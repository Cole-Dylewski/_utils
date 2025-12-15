# Testing Guide

## Test Structure

Tests are organized by module in the `python/tests/` directory:

- `test_aws.py` - AWS service tests
- `test_aws_s3.py` - S3-specific tests
- `test_aws_secrets.py` - Secrets Manager tests
- `test_aws_boto3_session.py` - Boto3 session tests
- `test_utils.py` - General utils tests
- `test_utils_sql.py` - SQL utility tests
- `test_logger.py` - Logging utility tests
- `test_resilience.py` - Resilience pattern tests
- `test_cache.py` - Caching utility tests
- `test_exceptions.py` - Exception hierarchy tests
- `test_cli.py` - CLI tool tests
- `test_common.py` - Common utilities tests
- `conftest.py` - Shared fixtures and configuration

## Running Tests

### Run all tests
```bash
pytest python/tests
```

### Run with coverage
```bash
pytest python/tests --cov=python --cov-report=html
```

### Run specific test file
```bash
pytest python/tests/test_aws_s3.py
```

### Run by marker
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# AWS tests
pytest -m aws
```

### Run in parallel
```bash
pytest python/tests -n auto
```

## Test Markers

- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (may use mocks)
- `@pytest.mark.aws` - Tests requiring AWS services/mocks
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_network` - Tests requiring network access

## Coverage Goals

- **Target**: 80%+ coverage
- **Critical modules**: 90%+ coverage
- Run `pytest --cov=python --cov-report=term-missing` to see coverage details

## Writing Tests

### Unit Test Example
```python
@pytest.mark.unit
def test_function_name():
    """Test description."""
    result = function_under_test(input)
    assert result == expected_output
```

### Integration Test with Mocks
```python
@pytest.mark.integration
@pytest.mark.aws
def test_s3_operation(moto_s3):
    """Test S3 operation with moto."""
    handler = S3Handler()
    # Test implementation
```

### Using Fixtures
```python
def test_with_fixture(sample_dataframe, mock_boto3_client):
    """Test using fixtures."""
    # Use sample_dataframe and mock_boto3_client
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Naming**: Use descriptive test names
3. **Fixtures**: Use fixtures for common setup
4. **Mocks**: Use mocks for external dependencies
5. **Coverage**: Aim for high coverage of critical paths
6. **Documentation**: Add docstrings to test functions
