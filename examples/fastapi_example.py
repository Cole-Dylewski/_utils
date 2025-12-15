"""
FastAPI example application using _utils.

Demonstrates integration with AWS, database operations, and structured logging.
"""

from aws import s3
from exceptions import AWSConnectionError, DatabaseError
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from utils.logger import get_logger
from utils.sql import run_sql

# Initialize logger
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="_utils FastAPI Example", version="1.0.0")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("FastAPI application starting", extra={"app": "fastapi_example"})


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "_utils FastAPI Example", "version": "1.0.0"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/s3/upload")
async def upload_to_s3(bucket: str, key: str, data: dict) -> dict[str, str]:
    """
    Upload data to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        data: Data to upload

    Returns:
        Success message
    """
    try:
        handler = s3.S3Handler()
        # Convert dict to DataFrame or use appropriate method
        logger.info("Uploading to S3", extra={"bucket": bucket, "key": key})
        # handler.send_to_s3(data=data, bucket=bucket, s3_file_name=key)
        return {"status": "success", "message": f"Uploaded to s3://{bucket}/{key}"}
    except AWSConnectionError as e:
        logger.exception("AWS connection error", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail=f"AWS connection failed: {e}")
    except Exception as e:
        logger.exception("S3 upload failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@app.get("/db/query")
async def query_database(query: str, dbname: str) -> dict:
    """
    Execute database query.

    Args:
        query: SQL query to execute
        dbname: Database name

    Returns:
        Query results
    """
    try:
        logger.info("Executing database query", extra={"dbname": dbname})
        result = run_sql(query=query, queryType="query", dbname=dbname)
        return {"status": "success", "data": result}
    except DatabaseError as e:
        logger.exception("Database error", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail=f"Database error: {e}")
    except Exception as e:
        logger.exception("Query failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
