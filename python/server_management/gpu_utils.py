"""
GPU Utility Functions

Utilities for detecting GPU information and allocating memory limits.
"""

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


def detect_gpu_memory_via_ssh(
    host: str,
    user: str,
    gpu_device_id: str = "0",
    port: int = 22,
    ssh_key_path: str | None = None,
) -> float | None:
    """
    Detect GPU memory capacity via SSH using nvidia-smi.

    :param host: Server hostname or IP
    :param user: SSH user
    :param gpu_device_id: GPU device ID to check
    :param port: SSH port
    :param ssh_key_path: Path to SSH private key
    :return: GPU memory in GB, or None if detection fails
    """
    ssh_cmd = [
        "ssh",
        "-p",
        str(port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ConnectTimeout=10",
    ]

    if ssh_key_path:
        ssh_cmd.extend(["-i", ssh_key_path])

    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.append(
        f"nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits --id={gpu_device_id} 2>/dev/null || echo ''"
    )

    try:
        result = subprocess.run(
            ssh_cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip():
            # Output is in MB, convert to GB
            memory_mb = float(result.stdout.strip())
            memory_gb = memory_mb / 1024.0
            logger.info(
                f"Detected GPU {gpu_device_id} memory: {memory_gb:.2f} GB ({memory_mb:.0f} MB)"
            )
            return memory_gb
        logger.warning(
            f"Failed to detect GPU memory: {result.stderr or 'nvidia-smi not available'}"
        )
        return None

    except subprocess.TimeoutExpired:
        logger.warning("GPU memory detection timed out")
        return None
    except Exception as e:
        logger.warning(f"GPU memory detection failed: {e}")
        return None


def allocate_gpu_memory_for_vllm_instances(
    total_memory_gb: float,
    vllm_llm_memory_gb: float,
    vllm_embedding_memory_gb: float,
    vllm_ocr_memory_gb: float,
) -> dict[str, Any]:
    """
    Allocate GPU memory for vLLM instances using vLLM's GPU memory percentage setting.

    For unified RAM systems with multiple vLLM instances:
    - Calculates GPU memory percentage for each vLLM instance
    - Remaining memory goes to other services (backend, ingest)

    :param total_memory_gb: Total GPU memory in GB
    :param vllm_llm_memory_gb: Memory required for LLM vLLM instance
    :param vllm_embedding_memory_gb: Memory required for embedding vLLM instance
    :param vllm_ocr_memory_gb: Memory required for OCR vLLM instance
    :return: Dictionary with vLLM percentages and remaining memory allocations
    """
    allocations = {}

    # Calculate total vLLM memory requirements
    total_vllm_memory = vllm_llm_memory_gb + vllm_embedding_memory_gb + vllm_ocr_memory_gb

    # Calculate GPU memory percentage for each vLLM instance
    # vLLM uses --gpu-memory-utilization or similar percentage setting
    vllm_llm_percentage = (vllm_llm_memory_gb / total_memory_gb) * 100.0
    vllm_embedding_percentage = (vllm_embedding_memory_gb / total_memory_gb) * 100.0
    vllm_ocr_percentage = (vllm_ocr_memory_gb / total_memory_gb) * 100.0

    allocations["vllm_llm_gpu_percentage"] = round(vllm_llm_percentage, 2)
    allocations["vllm_embedding_gpu_percentage"] = round(vllm_embedding_percentage, 2)
    allocations["vllm_ocr_gpu_percentage"] = round(vllm_ocr_percentage, 2)

    # Calculate remaining memory for other services
    remaining_memory_gb = total_memory_gb - total_vllm_memory

    if remaining_memory_gb < 0:
        logger.warning(
            f"vLLM memory requirements ({total_vllm_memory:.2f}GB) exceed total GPU memory "
            f"({total_memory_gb:.2f}GB). Remaining services will have no GPU memory allocated."
        )
        remaining_memory_gb = 0

    # Allocate remaining memory to backend and ingest (equally)
    if remaining_memory_gb > 0:
        allocations["backend_gpu_memory_gb"] = round(remaining_memory_gb / 2.0, 2)
        allocations["ingest_gpu_memory_gb"] = round(remaining_memory_gb / 2.0, 2)
    else:
        allocations["backend_gpu_memory_gb"] = 0.0
        allocations["ingest_gpu_memory_gb"] = 0.0

    logger.info(
        f"GPU memory allocation for unified RAM system: "
        f"Total={total_memory_gb:.2f}GB, "
        f"vLLM instances={total_vllm_memory:.2f}GB, "
        f"Remaining={remaining_memory_gb:.2f}GB"
    )
    logger.info(
        f"vLLM percentages: LLM={vllm_llm_percentage:.2f}%, "
        f"Embedding={vllm_embedding_percentage:.2f}%, "
        f"OCR={vllm_ocr_percentage:.2f}%"
    )
    logger.info(
        f"Other services: Backend={allocations['backend_gpu_memory_gb']:.2f}GB, "
        f"Ingest={allocations['ingest_gpu_memory_gb']:.2f}GB"
    )

    return allocations


def allocate_gpu_memory(
    total_memory_gb: float,
    enable_vllm: bool = False,
    ai_services_ratio: float = 0.8,
    non_ai_services_ratio: float = 0.2,
) -> dict[str, float]:
    """
    Allocate GPU memory to services based on hierarchy.

    Legacy allocation method for non-unified RAM systems.
    For unified RAM with vLLM instances, use allocate_gpu_memory_for_vllm_instances instead.

    AI services (backend, ingest, vLLM) get 80% of total memory.
    Other services get 20% of total memory.

    :param total_memory_gb: Total GPU memory in GB
    :param enable_vllm: Whether vLLM is enabled
    :param ai_services_ratio: Ratio for AI services (default: 0.8 = 80%)
    :param non_ai_services_ratio: Ratio for non-AI services (default: 0.2 = 20%)
    :return: Dictionary mapping service names to memory limits in GB
    """
    ai_memory_total = total_memory_gb * ai_services_ratio
    non_ai_memory_total = total_memory_gb * non_ai_services_ratio

    allocations = {}

    # AI services: backend, ingest, vLLM (if enabled)
    ai_services = ["backend", "ingest"]
    if enable_vllm:
        ai_services.append("vllm")

    # Distribute AI memory equally among AI services
    if ai_services:
        ai_memory_per_service = ai_memory_total / len(ai_services)
        for service in ai_services:
            allocations[f"{service}_gpu_memory_gb"] = round(ai_memory_per_service, 2)

    # Non-AI services (currently none, but reserved for future)
    # If there are non-AI services that need GPU, distribute non_ai_memory_total among them
    # For now, this is reserved for future use

    logger.info(
        f"GPU memory allocation: AI services={ai_memory_total:.2f}GB "
        f"({ai_services_ratio * 100:.0f}%), "
        f"Non-AI services={non_ai_memory_total:.2f}GB ({non_ai_services_ratio * 100:.0f}%)"
    )
    logger.info(
        f"Per-service allocation: {', '.join([f'{k}={v:.2f}GB' for k, v in allocations.items()])}"
    )

    return allocations
