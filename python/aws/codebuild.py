import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Dict, Any, List, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Retry configuration for Codebuild operations
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})

class CodebuildHandler:
    """
    CodebuildHandler with AWS session management, error handling, and logging.
    """
    def __init__(
        self, 
        aws_access_key_id=None, 
        aws_secret_access_key=None, 
        region_name=None,
        session = None
    ):
        try:
            #get aws boto3 session   
            if session:
                self.session = session
            else:
                from _utils.aws import boto3_session
                self.session = boto3_session.Session(
                    aws_access_key_id=aws_access_key_id, 
                    aws_secret_access_key=aws_secret_access_key, 
                    region_name=region_name)

            self.codebuild_client = self.session.client('codebuild', config=retry_config)
            self.logs_client = self.session.client('logs')
            logger.info("Connected to AWS Codebuild")
        except ClientError as e:
            logger.error(f"Failed to initialize Codebuild client: {e}")
            raise
        
    async def get_project_config(self,project_name):
        
        """
    Updates an AWS CodeBuild project with detailed arguments for subfields.

    Args:
        project_name (str): The name of the CodeBuild project to update.

        kwargs: Key-value pairs representing the fields to update in the CodeBuild project.
            Supported keys include:
                - description (str): A description of the project.
                - source (dict): Configuration for the project's source repository.
                    Expected keys:
                        - type (str): Source type (e.g., "GITHUB", "S3").
                        - location (str): URL or location of the source.
                        - gitCloneDepth (int, optional): Depth of the Git clone.
                        - buildspec (str, optional): Buildspec file path or inline content.
                        - reportBuildStatus (bool, optional): Whether to report build status.
                        - insecureSsl (bool, optional): Allow insecure SSL connections.
                - artifacts (dict): Configuration for build artifacts.
                    Expected keys:
                        - type (str): Artifact type (e.g., "S3", "NO_ARTIFACTS").
                        - files (list, optional): List of file patterns to include.
                        - discardPaths (bool, optional): Discard path information in the artifact.
                - environment (dict): Build environment configuration.
                    Expected keys:
                        - type (str): Environment type (e.g., "LINUX_CONTAINER").
                        - image (str): Docker image for the build environment.
                        - computeType (str): Compute size (e.g., "BUILD_GENERAL1_SMALL").
                        - environmentVariables (list, optional): List of environment variables.
                            Each variable is a dict with:
                                - name (str): Variable name.
                                - value (str): Variable value.
                                - type (str, optional): Type ("PLAINTEXT" or "SECRETS_MANAGER").
                        - privilegedMode (bool, optional): Enable privileged mode.
                        - imagePullCredentialsType (str, optional): Credentials type for pulling images.
                - serviceRole (str): The IAM role ARN for CodeBuild to use.
                - timeoutInMinutes (int): The maximum build timeout, in minutes.
                - encryptionKey (str): KMS encryption key ARN for encryption.
                - tags (list): List of tags for the project, each as a key-value pair.
                    Example: [{"key": "Environment", "value": "Production"}].
                - vpcConfig (dict): VPC configuration for the build project.
                    Expected keys:
                        - vpcId (str): VPC ID.
                        - subnets (list): List of subnet IDs.
                        - securityGroupIds (list): List of security group IDs.
                - badgeEnabled (bool): Whether to enable the project badge.
                - logsConfig (dict): Configuration for logging.
                    Expected keys:
                        - cloudWatchLogs (dict): CloudWatch Logs configuration.
                            - status (str): "ENABLED" or "DISABLED".
                        - s3Logs (dict): S3 Logs configuration.
                            - status (str): "ENABLED" or "DISABLED".
                            - encryptionDisabled (bool, optional): Whether to disable encryption.
                - cache (dict): Caching configuration.
                    Expected keys:
                        - type (str): Cache type ("NO_CACHE" or "LOCAL").
                        - modes (list, optional): List of cache modes (e.g., "LOCAL_SOURCE_CACHE").
                - sourceVersion (str): The source version, such as a branch name or commit hash.
                - secondarySources (list): List of secondary sources.
                    Each source is a dict with fields like `type`, `location`, etc.
                - secondarySourceVersions (list): List of versions for secondary sources.
                    Each version is a dict with fields like `sourceIdentifier` and `sourceVersion`.
                - secondaryArtifacts (list): List of configurations for secondary artifacts.
                - fileSystemLocations (list): List of file system locations.
                    Each location is a dict with fields like `identifier` and `location`.
                - buildBatchConfig (dict): Configuration for batch builds.
                    Expected keys:
                        - serviceRole (str): The IAM role ARN for batch builds.
                        - combineArtifacts (bool): Whether to combine artifacts in batch builds.
                        - restrictions (dict, optional): Restrictions for batch builds.

    Returns:
        dict: Response from the CodeBuild `update_project` API.

    Raises:
        ClientError: If the update operation fails.
        ValueError: If the project is not found or accessible.
    """
        

        try:
            # Get the project details
            response = self.codebuild_client.batch_get_projects(names=[project_name])
            projects = response.get('projects', [])
            
            if not projects:
                raise ValueError(f"No project found with name: {project_name}")
            
            project = projects[0]
            # print_nested(project)
            # Map the project details to the update-project format
            update_project_format = {
                "name": project["name"],
                "description": project.get("description", ""),
                "source": project["source"],
                "artifacts": project["artifacts"],
                "environment": project["environment"],
                "serviceRole": project["serviceRole"],
                "timeoutInMinutes": project.get("timeoutInMinutes", 60),
                "encryptionKey": project.get("encryptionKey", ""),
                "tags": project.get("tags", []),
                "vpcConfig": project.get("vpcConfig", {}),
                "badgeEnabled": project.get("badgeEnabled", False),
                "logsConfig": project.get("logsConfig", {}),
                "cache": project.get("cache", {}),
                "sourceVersion": project.get("sourceVersion", ""),
                "secondarySources": project.get("secondarySources", []),
                "secondarySourceVersions": project.get("secondarySourceVersions", []),
                "secondaryArtifacts": project.get("secondaryArtifacts", []),
                "fileSystemLocations": project.get("fileSystemLocations", []),
                "buildBatchConfig": project.get("buildBatchConfig", {}),
            }

            return update_project_format

        except Exception as e:
            print(f"Error retrieving project: {e}")
            return None
    
    async def update_codebuild_project_json(
        self,
        project_name,
        **kwargs
    ):
        """
        Updates an AWS CodeBuild project with detailed arguments for subfields.

        Args:
            project_name (str): Name of the CodeBuild project.
            kwargs: Field updates as key-value pairs.
            

        Returns:
            dict: Response from the CodeBuild update project API.
        """
        try:
            # Fetch current project configuration
            current_config = await self.get_project_config(project_name)
            if not current_config:
                raise ValueError(f"Project {project_name} not found or inaccessible.")

            # Merge updates
            update_params = current_config.copy()
            for key, value in kwargs.items():
                if value is not None:
                    if isinstance(value, dict) and key in update_params:
                        update_params[key].update(value)  # Merge dictionaries
                    else:
                        update_params[key] = value

            # Make the update call
            response = self.codebuild_client.update_project(**update_params)
            logger.info(f"Project {project_name} updated successfully.")
            return response

        except ClientError as e:
            logger.error(f"Failed to update project {project_name}: {e}")
            raise
        
    async def update_codebuild_project(
        self,
        project_name,
        description=None,
        source_type=None,
        source_location=None,
        source_buildspec=None,
        source_report_build_status=None,
        source_insecure_ssl=None,
        artifacts_type=None,
        artifacts_files=None,
        artifacts_discard_paths=None,
        environment_type=None,
        environment_image=None,
        environment_compute_type=None,
        environment_variables=None,
        environment_privileged_mode=None,
        environment_image_pull_credentials_type=None,
        service_role=None,
        timeout_in_minutes=None,
        encryption_key=None,
        tags=None,
        vpc_config=None,
        badge_enabled=None,
        logs_cloudwatch_status=None,
        logs_s3_status=None,
        logs_s3_encryption_disabled=None,
        cache_type=None,
        source_version=None,
        secondary_sources=None,
        secondary_source_versions=None,
        secondary_artifacts=None,
        file_system_locations=None,
        build_batch_config=None,
    ):
        """
        Updates an AWS CodeBuild project with selective replacement of values.

        Args:
            project_name (str): Name of the CodeBuild project (required).
            description (str, optional): Project description.
            source_type (str, optional): Type of the source (e.g., 'GITHUB', 'CODECOMMIT').
            source_location (str, optional): Location of the source repository.
            source_buildspec (str, optional): Buildspec content or path.
            source_report_build_status (bool, optional): Whether to report build status.
            source_insecure_ssl (bool, optional): Allow insecure SSL connections.
            artifacts_type (str, optional): Type of artifacts (e.g., 'NO_ARTIFACTS', 'S3').
            artifacts_files (list, optional): List of files to include in artifacts.
            artifacts_discard_paths (bool, optional): Whether to discard paths in artifacts.
            environment_type (str, optional): Environment type (e.g., 'LINUX_CONTAINER').
            environment_image (str, optional): Docker image for the build environment.
            environment_compute_type (str, optional): Compute type (e.g., 'BUILD_GENERAL1_SMALL').
            environment_variables (list, optional): List of environment variables (dicts).
            environment_privileged_mode (bool, optional): Enable privileged mode.
            environment_image_pull_credentials_type (str, optional): Image pull credentials.
            service_role (str, optional): IAM service role.
            timeout_in_minutes (int, optional): Timeout in minutes.
            encryption_key (str, optional): KMS encryption key ARN.
            tags (list, optional): List of tags (dicts).
            vpc_config (dict, optional): VPC configuration.
            badge_enabled (bool, optional): Enable project badges.
            logs_cloudwatch_status (str, optional): CloudWatch logs status ('ENABLED', 'DISABLED').
            logs_s3_status (str, optional): S3 logs status ('ENABLED', 'DISABLED').
            logs_s3_encryption_disabled (bool, optional): Disable S3 log encryption.
            cache_type (str, optional): Cache type ('NO_CACHE', 'LOCAL', etc.).
            source_version (str, optional): Source version identifier.
            secondary_sources (list, optional): List of secondary sources (dicts).
            secondary_source_versions (list, optional): List of secondary source versions (dicts).
            secondary_artifacts (list, optional): List of secondary artifacts (dicts).
            file_system_locations (list, optional): List of file system locations (dicts).
            build_batch_config (dict, optional): Build batch configuration.

        Returns:
            dict: Response from the CodeBuild update project API.
        """
        try:
            # Fetch current project configuration
            current_config = await self.get_project_config(project_name)
            if not current_config:
                raise ValueError(f"Project {project_name} not found or inaccessible.")

            # Initialize the update parameters with the current configuration
            update_params = current_config.copy()

            # Selectively update only the provided fields
            if description is not None:
                update_params["description"] = description
            if source_type is not None:
                update_params["source"]["type"] = source_type
            if source_location is not None:
                update_params["source"]["location"] = source_location
            if source_buildspec is not None:
                update_params["source"]["buildspec"] = source_buildspec
            if source_report_build_status is not None:
                update_params["source"]["reportBuildStatus"] = source_report_build_status
            if source_insecure_ssl is not None:
                update_params["source"]["insecureSsl"] = source_insecure_ssl
            if artifacts_type is not None:
                update_params["artifacts"]["type"] = artifacts_type
            if artifacts_files is not None:
                update_params["artifacts"]["files"] = artifacts_files
            if artifacts_discard_paths is not None:
                update_params["artifacts"]["discardPaths"] = artifacts_discard_paths
            if environment_type is not None:
                update_params["environment"]["type"] = environment_type
            if environment_image is not None:
                update_params["environment"]["image"] = environment_image
            if environment_compute_type is not None:
                update_params["environment"]["computeType"] = environment_compute_type
            if environment_variables is not None:
                update_params["environment"]["environmentVariables"] = environment_variables
            if environment_privileged_mode is not None:
                update_params["environment"]["privilegedMode"] = environment_privileged_mode
            if environment_image_pull_credentials_type is not None:
                update_params["environment"]["imagePullCredentialsType"] = environment_image_pull_credentials_type
            if service_role is not None:
                update_params["serviceRole"] = service_role
            if timeout_in_minutes is not None:
                update_params["timeoutInMinutes"] = timeout_in_minutes
            if encryption_key is not None:
                update_params["encryptionKey"] = encryption_key
            if tags is not None:
                update_params["tags"] = tags
            if vpc_config is not None:
                update_params["vpcConfig"] = vpc_config
            if badge_enabled is not None:
                update_params["badgeEnabled"] = badge_enabled
            if logs_cloudwatch_status is not None:
                update_params["logsConfig"]["cloudWatchLogs"]["status"] = logs_cloudwatch_status
            if logs_s3_status is not None:
                update_params["logsConfig"]["s3Logs"]["status"] = logs_s3_status
            if logs_s3_encryption_disabled is not None:
                update_params["logsConfig"]["s3Logs"]["encryptionDisabled"] = logs_s3_encryption_disabled
            if cache_type is not None:
                update_params["cache"]["type"] = cache_type
            if source_version is not None:
                update_params["sourceVersion"] = source_version
            if secondary_sources is not None:
                update_params["secondarySources"] = secondary_sources
            if secondary_source_versions is not None:
                update_params["secondarySourceVersions"] = secondary_source_versions
            if secondary_artifacts is not None:
                update_params["secondaryArtifacts"] = secondary_artifacts
            if file_system_locations is not None:
                update_params["fileSystemLocations"] = file_system_locations
            if build_batch_config is not None:
                update_params["buildBatchConfig"] = build_batch_config

            # Make the update call
            response = self.codebuild_client.update_project(**update_params)
            logger.info(f"Project {project_name} updated successfully.")
            return response

        except Exception as e:
            logger.error(f"Failed to update project {project_name}: {e}")
            raise

    async def start_build(self, project_name):
        """
        Starts a build for the specified AWS CodeBuild project, retrieves the build logs,
        and provides a CloudWatch link to the logs.

        Args:
            project_name (str): The name of the CodeBuild project.

        Returns:
            dict: A dictionary containing the build status, logs, and a CloudWatch log link.

        Raises:
            ValueError: If the build cannot be started or logs cannot be retrieved.
            ClientError: If there is an issue communicating with AWS services.
        """
        try:
            # Start the build
            build_response = self.codebuild_client.start_build(projectName=project_name)
            build_id = build_response["build"]["id"]
            logger.info(f"Build started for project {project_name}. Build ID: {build_id}")

            # Wait for the build to complete and retrieve logs
            build_status = None
            logs_content = []
            cloudwatch_link = None

            while True:
                build_status_response = self.codebuild_client.batch_get_builds(ids=[build_id])
                build_details = build_status_response["builds"][0]
                build_status = build_details["buildStatus"]

                if build_status in ["SUCCEEDED", "FAILED", "STOPPED"]:
                    logger.info(f"Build completed with status: {build_status}")
                    break

            # Retrieve logs from CloudWatch
            logs_config = build_details.get("logs", {})
            if "groupName" in logs_config and "streamName" in logs_config:
                group_name = logs_config["groupName"]
                stream_name = logs_config["streamName"]
                region = self.codebuild_client.meta.region_name
                logger.info(f"Fetching logs from {group_name}/{stream_name}")

                log_events = self.logs_client.get_log_events(
                    logGroupName=group_name, logStreamName=stream_name
                )
                for event in log_events["events"]:
                    logs_content.append(event["message"])

                # Generate a CloudWatch link
                cloudwatch_link = (
                    f"https://{region}.console.aws.amazon.com/cloudwatch/home?"
                    f"region={region}#logEventViewer:group={group_name};stream={stream_name}"
                )
                logger.info(f"CloudWatch Logs Link: {cloudwatch_link}")
            else:
                logger.warning("No logs configuration found for this build.")

            return {
                "build_status": build_status,
                "logs": logs_content,
                "cloudwatch_link": cloudwatch_link,
            }

        except ClientError as e:
            logger.error(f"Failed to start or monitor build for project {project_name}: {e}")
            raise ValueError("Build could not be started or monitored.") from e
