import asyncio
import concurrent.futures


def run_async_function(async_func, *args, **kwargs):
    """
    Runs an async function inside a synchronous function, adapting to different environments.

    Works in:
    - Jupyter Notebooks
    - Local Python scripts
    - AWS Lambda
    - AWS Glue

    Args:
        async_func (function): The async function to execute.
        *args: Positional arguments to pass to the async function.
        **kwargs: Keyword arguments to pass to the async function.

    Returns:
        Any: The result of the async function.
    """

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    # If already inside an event loop (e.g., Jupyter Notebook, FastAPI)
    if loop and loop.is_running():
        print("Detected running event loop, using `nest_asyncio` for Jupyter.")
        import nest_asyncio

        nest_asyncio.apply()
        return asyncio.run(async_func(*args, **kwargs))

    # If no event loop exists (e.g., normal Python script or AWS Lambda)
    if not loop:
        return asyncio.run(async_func(*args, **kwargs))

    # If inside AWS Glue or other complex environments
    print("Using ThreadPoolExecutor for AWS Glue or other complex environments.")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_async_function, async_func, *args, **kwargs)
        return future.result()
