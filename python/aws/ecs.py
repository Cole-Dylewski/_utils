import asyncio
import json
import logging
import time
from typing import Any

from aws import boto3_session, s3, secrets
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class FargateDeploymentRollbackException(Exception):
    """Exception raised when a Fargate deployment fails and is rolled back."""

    def __init__(self, service_name, message="Deployment failed and was rolled back."):
        self.service_name = service_name
        self.message = f"Service {service_name}: {message}"
        super().__init__(self.message)


class ECSHandler:
    """
    Handles AWS ECS operations: run tasks, manage services, get task statuses, etc.
    """

    def __init__(
        self,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region_name="us-east-1",
        session=None,
    ):
        self.region = region_name or "us-east-1"

        # Initialize AWS session
        if session:
            self.session = session
        else:
            self.session = boto3_session.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=self.region,
            )

        logger.info(f"ECSHandler initialized in region: {self.region}")

        # Create ECS client
        self.ecs_client = self.session.client(
            "ecs", region_name=self.region, endpoint_url=f"https://ecs.{self.region}.amazonaws.com"
        )

        # Other handlers (optional)
        self.s3_handler = s3.S3Handler(session=self.session)
        self.secret_handler = secrets.SecretHandler(session=self.session)

    # -------------------------------------
    # ECS Service Management
    # -------------------------------------

    def create_service(
        self,
        cluster_name: str,
        service_name: str,
        task_definition: str,
        desired_count: int = 1,
        launch_type: str = "FARGATE",
        subnets: list[str] | None = None,
        security_groups: list[str] | None = None,
        assign_public_ip: str = "ENABLED",
    ):
        """
        Creates a new ECS service.
        """
        logger.info(f"Creating ECS service {service_name} in cluster {cluster_name}")

        try:
            response = self.ecs_client.create_service(
                cluster=cluster_name,
                serviceName=service_name,
                taskDefinition=task_definition,
                desiredCount=desired_count,
                launchType=launch_type,
                networkConfiguration={
                    "awsvpcConfiguration": {
                        "subnets": subnets or [],
                        "securityGroups": security_groups or [],
                        "assignPublicIp": assign_public_ip,
                    }
                },
            )
            logger.info(f"ECS Service {service_name} created successfully")
            return response
        except ClientError as e:
            logger.exception(f"Failed to create ECS service {service_name}: {e}")
            raise

    def delete_service(self, cluster_name: str, service_name: str, force: bool = True):
        """
        Deletes an ECS service.
        """
        logger.info(f"Deleting ECS service {service_name} from cluster {cluster_name}")

        try:
            response = self.ecs_client.delete_service(
                cluster=cluster_name, service=service_name, force=force
            )
            logger.info(f"ECS Service {service_name} deleted successfully")
            return response
        except ClientError as e:
            logger.exception(f"Failed to delete ECS service {service_name}: {e}")
            raise

    def update_service(
        self,
        cluster_name: str,
        service_name: str,
        desired_count: int | None = None,
        task_definition: str | None = None,
    ):
        """
        Updates an ECS service (e.g., to scale up/down or update the task definition).
        """
        logger.info(f"Updating ECS service {service_name} in cluster {cluster_name}")

        update_args = {"cluster": cluster_name, "service": service_name}

        if desired_count is not None:
            update_args["desiredCount"] = desired_count

        if task_definition is not None:
            update_args["taskDefinition"] = task_definition

        try:
            response = self.ecs_client.update_service(**update_args)
            logger.info(f"ECS Service {service_name} updated successfully")
            return response
        except ClientError as e:
            logger.exception(f"Failed to update ECS service {service_name}: {e}")
            raise

    # -------------------------------------
    # ECS Task Management
    # -------------------------------------

    def run_task(
        self,
        cluster_name: str,
        task_definition: str,
        subnets: list[str] | None = None,
        security_groups: list[str] | None = None,
        assign_public_ip: str = "ENABLED",
        launch_type: str = "FARGATE",
        overrides: dict[str, Any] | None = None,
    ) -> str:
        """
        Runs a one-off ECS task.
        """
        logger.info(f"Running ECS task {task_definition} in cluster {cluster_name}")

        try:
            response = self.ecs_client.run_task(
                cluster=cluster_name,
                launchType=launch_type,
                taskDefinition=task_definition,
                networkConfiguration={
                    "awsvpcConfiguration": {
                        "subnets": subnets or [],
                        "securityGroups": security_groups or [],
                        "assignPublicIp": assign_public_ip,
                    }
                },
                overrides=overrides or {},
            )

            tasks = response.get("tasks", [])
            if not tasks:
                logger.warning("No ECS task was started.")
                return None

            task_arn = tasks[0]["taskArn"]
            logger.info(f"Task started successfully: {task_arn}")
            return task_arn

        except ClientError as e:
            logger.exception(f"Failed to run ECS task: {e}")
            raise

    async def monitor_task(
        self, cluster_name: str, task_arn: str, interval: int = 15
    ) -> dict[str, Any]:
        """
        Asynchronously monitors an ECS task until completion.
        """
        logger.info(f"Monitoring ECS task {task_arn} in cluster {cluster_name}")

        while True:
            try:
                response = self.ecs_client.describe_tasks(cluster=cluster_name, tasks=[task_arn])

                tasks = response.get("tasks", [])
                if not tasks:
                    logger.warning(f"Task {task_arn} not found in cluster {cluster_name}")
                    return {"TaskArn": task_arn, "Status": "NOT_FOUND"}

                task_status = tasks[0]["lastStatus"]
                logger.info(f"Task {task_arn} status: {task_status}")

                if task_status in ["STOPPED"]:
                    logger.info(f"Task {task_arn} has stopped")
                    return tasks[0]

                await asyncio.sleep(interval)

            except ClientError as e:
                logger.exception(f"Error monitoring ECS task {task_arn}: {e}")
                raise

    def stop_task(self, cluster_name: str, task_arn: str, reason: str | None = None):
        """
        Stops an ECS task.
        """
        logger.info(f"Stopping ECS task {task_arn} in cluster {cluster_name}")

        try:
            response = self.ecs_client.stop_task(
                cluster=cluster_name, task=task_arn, reason=reason or "Stopped by ECSHandler"
            )
            logger.info(f"Task {task_arn} stopped successfully")
            return response
        except ClientError as e:
            logger.exception(f"Failed to stop ECS task {task_arn}: {e}")
            raise

    # -------------------------------------
    # Helper Methods
    # -------------------------------------

    def list_clusters(self) -> list[str]:
        """
        Lists all ECS clusters.
        """
        try:
            response = self.ecs_client.list_clusters()
            clusters = response.get("clusterArns", [])
            logger.info(f"Found {len(clusters)} clusters")
            return clusters
        except ClientError as e:
            logger.exception(f"Failed to list ECS clusters: {e}")
            raise

    def list_services(self, cluster_name: str) -> list[str]:
        """
        Lists all services in an ECS cluster.
        """
        try:
            response = self.ecs_client.list_services(cluster=cluster_name)
            services = response.get("serviceArns", [])
            logger.info(f"Found {len(services)} services in cluster {cluster_name}")
            return services
        except ClientError as e:
            logger.exception(f"Failed to list services in cluster {cluster_name}: {e}")
            raise

    def list_tasks(self, cluster_name: str, service_name: str | None = None) -> list[str]:
        """
        Lists tasks in an ECS cluster (optionally filtered by service).
        """
        try:
            kwargs = {"cluster": cluster_name}
            if service_name:
                kwargs["serviceName"] = service_name

            response = self.ecs_client.list_tasks(**kwargs)
            tasks = response.get("taskArns", [])
            logger.info(f"Found {len(tasks)} tasks in cluster {cluster_name}")
            return tasks
        except ClientError as e:
            logger.exception(f"Failed to list tasks in cluster {cluster_name}: {e}")
            raise

    def get_cluster_full_config(self, cluster_name: str) -> dict[str, Any]:
        """
        Retrieves a nested JSON structure representing the full configuration of a given ECS cluster.
        Includes:
          - cluster ARN & name
          - all services with configuration details
          - each service's current task definition details
        """
        logger.info(f"Fetching full configuration for ECS cluster: {cluster_name}")

        result = {"clusterName": cluster_name, "clusterArn": None, "services": []}

        try:
            # Get cluster metadata (optional but useful)
            cluster_response = self.ecs_client.describe_clusters(clusters=[cluster_name])
            if cluster_response.get("clusters"):
                cluster_meta = cluster_response["clusters"][0]
                result["clusterArn"] = cluster_meta["clusterArn"]
                result["status"] = cluster_meta.get("status")
                result["registeredContainerInstancesCount"] = cluster_meta.get(
                    "registeredContainerInstancesCount"
                )
                result["runningTasksCount"] = cluster_meta.get("runningTasksCount")
                result["pendingTasksCount"] = cluster_meta.get("pendingTasksCount")
                result["activeServicesCount"] = cluster_meta.get("activeServicesCount")

            # Get all services in the cluster
            service_arns = self.list_services(cluster_name)
            if not service_arns:
                logger.warning(f"No services found in cluster '{cluster_name}'")
                return result

            # Describe services in batches of 10
            for i in range(0, len(service_arns), 10):
                batch = service_arns[i : i + 10]
                service_resp = self.ecs_client.describe_services(
                    cluster=cluster_name, services=batch
                )

                for svc in service_resp.get("services", []):
                    service_info = {
                        "serviceName": svc["serviceName"],
                        "serviceArn": svc["serviceArn"],
                        "desiredCount": svc.get("desiredCount"),
                        "runningCount": svc.get("runningCount"),
                        "pendingCount": svc.get("pendingCount"),
                        "launchType": svc.get("launchType"),
                        "platformVersion": svc.get("platformVersion"),
                        "networkConfiguration": svc.get("networkConfiguration"),
                        "loadBalancers": svc.get("loadBalancers", []),
                        "deployments": svc.get("deployments", []),
                        "createdAt": str(svc.get("createdAt")),
                        "taskDefinitionArn": svc["taskDefinition"],
                        "taskDefinition": None,  # will be filled in below
                    }

                    # Fetch the task definition details
                    task_def_arn = svc["taskDefinition"]
                    task_def_resp = self.ecs_client.describe_task_definition(
                        taskDefinition=task_def_arn
                    )
                    task_def = task_def_resp.get("taskDefinition", {})
                    if task_def:
                        service_info["taskDefinition"] = {
                            "family": task_def.get("family"),
                            "revision": task_def.get("revision"),
                            "taskRoleArn": task_def.get("taskRoleArn"),
                            "executionRoleArn": task_def.get("executionRoleArn"),
                            "networkMode": task_def.get("networkMode"),
                            "containerDefinitions": task_def.get("containerDefinitions", []),
                            "volumes": task_def.get("volumes", []),
                            "requiresCompatibilities": task_def.get("requiresCompatibilities", []),
                            "cpu": task_def.get("cpu"),
                            "memory": task_def.get("memory"),
                        }

                    result["services"].append(service_info)

            logger.info(f"Completed fetching full config for cluster {cluster_name}")
            return result

        except ClientError as e:
            logger.exception(f"Failed to get full configuration for cluster {cluster_name}: {e}")
            raise

    # -------------------------------------
    # Force Update Fargate Services
    # -------------------------------------

    def update_fargate_services(self, cluster_name: str, wait_interval: int = 30):
        """
        Force an ECS cluster to update all its Fargate services to use the latest ECR images
        and wait for the updates to complete.

        Raises:
            FargateDeploymentRollbackException: If a deployment fails and is rolled back.
        """
        logger.info(f"Starting force update for all Fargate services in cluster: {cluster_name}")

        try:
            # Retrieve all services in the cluster
            services_response = self.ecs_client.list_services(cluster=cluster_name)
            services = services_response.get("serviceArns", [])

            if not services:
                logger.warning(f"No services found in cluster '{cluster_name}'. Exiting.")
                return None

            logger.info(f"Services to update ({len(services)}): {services}")

            # Trigger force new deployments on each service
            for service in services:
                logger.info(f"Forcing new deployment on service: {service}")
                self.ecs_client.update_service(
                    cluster=cluster_name, service=service, forceNewDeployment=True
                )

            logger.info("All services triggered for new deployment. Monitoring progress...")

            # Track statuses for final output
            service_statuses = {}

            # Monitor deployments until all services complete their rollout
            all_services_updated = False
            while not all_services_updated:
                all_services_updated = True  # Reset at each loop

                for service in services:
                    response = self.ecs_client.describe_services(
                        cluster=cluster_name, services=[service]
                    )

                    service_desc = response["services"][0]
                    running_count = service_desc.get("runningCount", 0)
                    pending_count = service_desc.get("pendingCount", 0)
                    desired_count = service_desc.get("desiredCount", 0)
                    service_status = {
                        "Running": running_count,
                        "Pending": pending_count,
                        "Desired": desired_count,
                        "Deployments": [],
                    }

                    # Analyze deployments for this service
                    for deployment in service_desc.get("deployments", []):
                        deployment_id = deployment.get("id")
                        status = deployment.get("status")
                        rollout_state = deployment.get("rolloutState")
                        rollout_reason = deployment.get("rolloutStateReason", "N/A")

                        deployment_status = {
                            "DeploymentID": deployment_id,
                            "Status": status,
                            "RolloutState": rollout_state,
                            "RolloutReason": rollout_reason,
                            "RunningCount": deployment.get("runningCount"),
                            "PendingCount": deployment.get("pendingCount"),
                            "DesiredCount": deployment.get("desiredCount"),
                            "CreatedAt": str(deployment.get("createdAt")),
                            "UpdatedAt": str(deployment.get("updatedAt")),
                        }

                        # Append deployment info to this service's status report
                        service_status["Deployments"].append(deployment_status)

                        # Detect rollback failure
                        if rollout_state == "FAILED":
                            logger.error(
                                f"Deployment rollback detected for service {service} - Reason: {rollout_reason}"
                            )
                            raise FargateDeploymentRollbackException(service_name=service)

                        # If PRIMARY deployment isn't complete, keep waiting
                        if status == "PRIMARY" and rollout_state != "COMPLETED":
                            all_services_updated = False

                    # Update the master status dictionary
                    service_statuses[service] = service_status

                if not all_services_updated:
                    logger.info(
                        f"Services are still updating. Waiting {wait_interval} seconds before checking again..."
                    )
                    time.sleep(wait_interval)

            logger.info("=" * 60)
            logger.info(f"All services in cluster '{cluster_name}' successfully updated.")
            logger.info("=" * 60)
            logger.info(f"\nFinal Deployment Status:\n{json.dumps(service_statuses, indent=2)}")
            return service_statuses
        except FargateDeploymentRollbackException as rollback_exception:
            logger.critical(f"Rollback detected: {rollback_exception.message}")
            raise

        except ClientError as e:
            logger.exception(f"AWS ClientError during service update: {e!s}")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error during service update: {e!s}")
            raise
