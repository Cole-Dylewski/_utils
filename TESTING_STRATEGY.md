# Comprehensive Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the `_utils` package to achieve 80%+ code coverage and robust, production-ready testing.

## Testing Goals

- **Coverage Target**: 80%+ overall, 90%+ for critical modules
- **Test Types**: Unit, Integration, Performance, CLI
- **Test Speed**: Fast unit tests (< 1s), slower integration tests marked appropriately
- **CI Integration**: All tests run on every PR and push

## Test Structure

```
python/tests/
├── conftest.py              # Shared fixtures and configuration
├── test_exceptions.py        # Exception hierarchy tests
├── test_logger.py           # Logging utility tests
├── test_resilience.py       # Resilience pattern tests
├── test_cache.py            # Caching utility tests
├── test_cli.py              # CLI tool tests
├── test_aws_s3.py           # S3 service tests
├── test_aws_secrets.py      # Secrets Manager tests
├── test_aws_boto3_session.py # Boto3 session tests
├── test_aws_dynamodb.py     # DynamoDB tests
├── test_utils_sql.py        # SQL utility tests
├── test_utils_dataframe.py  # DataFrame utility tests
├── test_utils_files.py      # File utility tests
├── test_utils_cryptography.py # Cryptography tests
├── test_utils_git.py        # Git utility tests
├── test_common_basic.py     # Common utilities tests
├── test_integration_aws.py  # AWS integration tests
├── test_performance.py      # Performance benchmarks
└── README.md                # Testing guide
```

## Testing Tools

### Core Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **pytest-timeout**: Test timeout management
- **pytest-xdist**: Parallel test execution
- **pytest-benchmark**: Performance testing

### Mocking & Integration
- **moto**: AWS service mocking (S3, DynamoDB, Secrets Manager, etc.)
- **responses**: HTTP request mocking
- **freezegun**: Time mocking
- **faker**: Test data generation

## Test Categories

### 1. Unit Tests (`@pytest.mark.unit`)

**Purpose**: Test individual functions and classes in isolation

**Characteristics**:
- Fast execution (< 1 second)
- No external dependencies
- Use mocks for external services
- Test edge cases and error conditions

**Examples**:
- Exception hierarchy
- Logger configuration
- Cache operations
- Resilience patterns
- Utility functions

### 2. Integration Tests (`@pytest.mark.integration`)

**Purpose**: Test module interactions with mocked services

**Characteristics**:
- Use moto for AWS services
- Test complete workflows
- Verify error handling
- Test with realistic data

**Examples**:
- S3 upload/download workflow
- Secrets Manager create/read/update
- SQL query execution with mocked DB
- Complete API workflows

### 3. Performance Tests (`@pytest.mark.slow`)

**Purpose**: Benchmark critical operations

**Characteristics**:
- Use pytest-benchmark
- Identify performance regressions
- Test with realistic data sizes
- Marked as slow to skip in fast runs

**Examples**:
- Cache performance
- Rate limiter throughput
- Logger performance
- DataFrame operations

## Coverage Strategy

### Critical Modules (90%+ coverage)
- `exceptions.py` - Error handling
- `logger.py` - Logging utilities
- `resilience.py` - Resilience patterns
- `cache.py` - Caching utilities
- `aws/s3.py` - S3 operations
- `aws/secrets.py` - Secrets Manager
- `utils/sql.py` - SQL operations

### High Priority (85%+ coverage)
- `aws/dynamodb.py` - DynamoDB operations
- `aws/boto3_session.py` - Session management
- `utils/dataframe.py` - DataFrame utilities
- `utils/files.py` - File operations
- `cli.py` - CLI tool

### Standard (80%+ coverage)
- All other modules

## Test Implementation Guidelines

### 1. Test Naming
```python
def test_function_name_scenario():
    """Test description explaining what is being tested."""
```

### 2. Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Set up test data and mocks
    data = {"key": "value"}

    # Act - Execute the function
    result = function_under_test(data)

    # Assert - Verify the result
    assert result == expected
```

### 3. Using Fixtures
```python
def test_with_fixtures(sample_dataframe, mock_boto3_client):
    """Use fixtures for common setup."""
    # Test implementation
```

### 4. Mocking External Services
```python
@patch("module.external_service")
def test_with_mock(mock_service):
    """Mock external dependencies."""
    mock_service.return_value = expected_value
    # Test implementation
```

### 5. Integration Tests with Moto
```python
@pytest.mark.integration
@pytest.mark.aws
def test_s3_workflow(moto_s3):
    """Test with moto S3 mock."""
    # Test implementation
```

## Running Tests

### All Tests
```bash
pytest python/tests
```

### Unit Tests Only
```bash
pytest -m unit python/tests
```

### Integration Tests
```bash
pytest -m integration python/tests
```

### With Coverage
```bash
pytest --cov=python --cov-report=html python/tests
```

### Parallel Execution
```bash
pytest -n auto python/tests
```

### Specific Test File
```bash
pytest python/tests/test_aws_s3.py
```

### Specific Test Function
```bash
pytest python/tests/test_aws_s3.py::TestS3Handler::test_s3_handler_initialization
```

## CI/CD Integration

### Coverage Requirements
- Minimum 80% overall coverage
- Coverage reports uploaded to Codecov
- HTML coverage reports as artifacts
- Coverage diff shown in PR comments

### Test Execution
- Run on every push and PR
- Matrix testing: Python 3.10, 3.11, 3.12
- OS testing: Ubuntu, Windows, macOS
- Fast-fail disabled for matrix builds

### Coverage Reports
- XML report for Codecov
- HTML report for local review
- Terminal report for quick feedback

## Test Data Management

### Fixtures for Common Data
- `sample_dataframe`: Test DataFrame
- `sample_dict_data`: Test dictionary
- `sample_json_string`: Test JSON
- `temp_file`: Temporary file
- `temp_dir`: Temporary directory

### Mock Services
- `mock_boto3_client`: Mock AWS client
- `moto_s3`: Moto S3 mock
- `moto_secretsmanager`: Moto Secrets Manager mock
- `moto_dynamodb`: Moto DynamoDB mock
- `mock_vault_client`: Mock Vault client
- `mock_redis`: Mock Redis client

## Best Practices

1. **Isolation**: Each test should be independent
2. **Deterministic**: Tests should produce consistent results
3. **Fast**: Unit tests should run quickly
4. **Clear**: Test names should describe what they test
5. **Comprehensive**: Test happy paths, edge cases, and errors
6. **Maintainable**: Use fixtures and helpers to reduce duplication
7. **Documented**: Add docstrings explaining test purpose

## Coverage Exclusions

The following are excluded from coverage:
- `__init__.py` files (unless they contain logic)
- Test files themselves
- CLI entry points (`if __name__ == "__main__"`)
- Type checking blocks (`if TYPE_CHECKING:`)
- Abstract methods
- Exception repr methods

## Next Steps

1. ✅ Set up test infrastructure
2. ✅ Create base test files
3. ⏳ Expand test coverage for all modules
4. ⏳ Add integration tests for all AWS services
5. ⏳ Add performance benchmarks
6. ⏳ Achieve 80%+ coverage
7. ⏳ Set up coverage reporting in CI

## Monitoring

- Track coverage trends over time
- Identify modules with low coverage
- Review coverage reports before merging PRs
- Set coverage goals for each module
- Use coverage to guide testing priorities
