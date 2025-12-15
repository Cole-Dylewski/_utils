# _utils Example Applications

This directory contains example applications demonstrating how to use `_utils` in real-world scenarios.

## Examples

### FastAPI Example (`fastapi_example.py`)

Demonstrates:
- FastAPI integration with _utils
- AWS S3 operations
- Database queries
- Structured logging
- Error handling with custom exceptions

**Run:**
```bash
uvicorn examples.fastapi_example:app --reload
```

### AWS Lambda Example (`lambda_example.py`)

Demonstrates:
- Lambda function handler
- AWS Secrets Manager integration
- S3 operations
- JSON-structured logging
- Error handling

**Deploy:**
```bash
# Package and deploy to AWS Lambda
zip -r lambda_function.zip lambda_example.py
# Upload to Lambda via AWS Console or CLI
```

### Django Example (`django_example.py`)

Demonstrates:
- Django views with _utils
- Database operations
- Logging integration
- Error handling

**Usage:**
Add to your Django project's `urls.py`:
```python
from examples.django_example import DatabaseQueryView

urlpatterns = [
    path('api/query/', DatabaseQueryView.as_view(), name='query'),
]
```

## Running Examples

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. **Run the example:**
   ```bash
   python examples/fastapi_example.py
   ```

## Best Practices

- Always use structured logging for production applications
- Handle exceptions using custom exception hierarchy
- Use resilience patterns (retry, circuit breaker) for external services
- Implement proper error responses for API endpoints
- Use environment variables for configuration
