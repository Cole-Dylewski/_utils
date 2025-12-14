# _utils

A comprehensive Python utility library providing shared utilities for AWS services, Alpaca trading APIs, database operations, data processing, and more.

## Overview

_utils is a modular utility package designed to streamline development across multiple domains including cloud infrastructure, database operations, trading APIs, and data processing. The library is organized into feature-specific modules that can be installed independently based on project needs.

## Package Information

- **Name**: `_utils`
- **Version**: 0.1.0
- **Python**: >=3.10
- **License**: MIT
- **Author**: Cole Dylewski

## Installation

### Base Installation

```bash
pip install _utils
```

### Optional Dependencies

Install only the features you need:

```bash
# AWS services
pip install _utils[aws]

# Database operations
pip install _utils[db]

# Alpaca trading APIs
pip install _utils[alpaca]

# FastAPI support
pip install _utils[fastapi]

# Machine learning utilities
pip install _utils[ml]

# Tableau integration
pip install _utils[tableau]
```

## Project Structure

```
_utils/
├── alpaca/              # Alpaca trading API clients
│   ├── broker_api/      # Broker API operations
│   └── trader_api/      # Trader API operations
├── aws/                 # AWS service utilities
│   ├── aws_lambda.py    # Lambda function utilities
│   ├── boto3_session.py # AWS session management
│   ├── cloudwatch.py    # CloudWatch operations
│   ├── codebuild.py     # CodeBuild project management
│   ├── cognito.py        # Cognito user management
│   ├── dynamodb.py      # DynamoDB operations
│   ├── ecs.py           # ECS service management
│   ├── elasticache.py   # ElastiCache utilities
│   ├── glue.py          # AWS Glue job management
│   ├── s3.py            # S3 file operations
│   ├── secrets.py       # Secrets Manager operations
│   ├── sns.py           # SNS notifications
│   └── transfer_family.py # Transfer Family SFTP management
├── common/              # Common utilities
│   ├── basic.py         # Basic helper functions
│   ├── django_request.py # Django request utilities
│   ├── models.py        # Common models
│   └── requests.py      # HTTP request utilities
├── models/              # Model utilities
│   ├── django_models.py # Django model helpers
│   └── sql.py           # SQL model utilities
├── snowflake/           # Snowflake integration
│   └── snowpark.py      # Snowpark client wrapper
├── sql/                 # SQL operations
│   ├── io.py            # SQL I/O operations
│   └── models.py        # SQL model definitions
├── server_management/   # Server management and infrastructure automation
│   ├── ansible.py       # Ansible playbook execution
│   ├── app_deployment.py # Application deployment framework
│   ├── credential_generator.py # Credential generation utilities
│   ├── gpu_utils.py     # GPU memory management utilities
│   ├── terraform.py     # Terraform project management
│   └── vault.py         # HashiCorp Vault integration
├── tableau/             # Tableau integration
│   └── tableau_client.py # Tableau Server API client
├── tests/               # Test utilities
└── utils/                # General utilities
    ├── api.py           # API request utilities
    ├── azure.py         # Azure integration
    ├── cryptography.py  # Encryption/decryption
    ├── dataframe.py     # DataFrame operations
    ├── dict_json.py     # Dictionary/JSON utilities
    ├── email.py         # Email sending
    ├── files.py         # File operations
    ├── formatting_tools.py # Text formatting
    ├── git.py           # Git operations
    ├── log_print.py     # Logging utilities
    ├── misc.py          # Miscellaneous helpers
    ├── redis.py         # Redis operations
    ├── requirements.py  # Requirements management
    ├── sql.py           # SQL utilities
    ├── sync_async.py    # Async/sync utilities
    ├── tableau.py       # Tableau utilities
    └── teams.py         # Microsoft Teams integration
```

## Module Descriptions

### AWS Module (`aws/`)

Comprehensive AWS service integrations with session management, error handling, and logging.

**Key Features:**
- **Lambda**: Function invocation, context utilities, log link generation
- **S3**: File upload/download, multipart uploads, presigned URLs, metadata operations
- **DynamoDB**: CRUD operations, batch writes, table metadata
- **ECS**: Service management, task execution, Fargate deployments
- **Glue**: Job creation, execution, monitoring, CloudWatch log integration
- **Cognito**: User authentication, token management, user CRUD operations
- **Secrets Manager**: Secret retrieval, creation, updates
- **Transfer Family**: SFTP server and user management
- **CodeBuild**: Project configuration and build management
- **ElastiCache**: Redis token generation utilities

**Example:**
```python
from _utils.aws import s3, secrets

# Initialize S3 handler
s3_handler = s3.S3Handler()
s3_handler.send_to_s3(data=df, bucket='my-bucket', s3_file_name='data.csv')

# Initialize Secrets Manager
secret_handler = secrets.SecretHandler()
creds = secret_handler.get_secret('my-secret')
```

### Alpaca Module (`alpaca/`)

Trading API clients for both Broker and Trader APIs.

**Key Features:**
- **BrokerClient**: Account management, ACH transfers, funding accounts
- **TraderClient**: Trading operations, portfolio management, market data
- **Data APIs**: Stocks, crypto, forex, options, news, corporate actions

**Example:**
```python
from _utils.alpaca import TraderClient

client = TraderClient(api_key, api_secret, base_url)
account = client.get_account()
positions = client.get_positions()
```

### SQL Module (`sql/`)

Database operations for PostgreSQL and Redshift.

**Key Features:**
- Synchronous and asynchronous SQL execution
- DataFrame to SQL statement conversion
- S3 COPY/UNLOAD statement generation
- Data validation against table schemas
- Column normalization and type inference

**Example:**
```python
from _utils.utils import sql

# Execute query
result = sql.run_sql(
    query="SELECT * FROM users",
    queryType='query',
    dbname='mydb',
    rds='postgres'
)

# Generate INSERT statement from DataFrame
insert_stmt = sql.df_to_insert_stmt(df, 'schema.table')
```

### Snowflake Module (`snowflake/`)

Modern Snowpark client wrapper with context management.

**Key Features:**
- Environment variable configuration
- DataFrame operations
- UDF and stored procedure registration
- Pandas integration

**Example:**
```python
from _utils.snowflake import SnowparkClient

client = SnowparkClient.from_env()
with client as sp:
    df = sp.table("MY_DB.MY_SCHEMA.MY_TABLE").limit(5)
    rows = df.collect()
```

### Tableau Module (`tableau/`)

Tableau Server API integration for report generation and metadata management.

**Key Features:**
- Authentication and site management
- Report generation (PDF, CSV, images)
- Metadata retrieval (projects, workbooks, views, datasources)
- User and group management

**Example:**
```python
from _utils.utils import tableau

client = tableau.tableau_client(
    username='user',
    password='pass',
    server_url='https://tableau.example.com'
)
with client:
    reports = client.generate_report(view_ids=['view-id'], filename='report.pdf')
```

### Server Management Module (`server_management/`)

Infrastructure automation and server management utilities.

**Key Features:**
- **Terraform**: Project management, init/plan/apply/destroy operations, output parsing
- **Ansible**: Playbook execution, collection management, inventory handling
- **Vault**: HashiCorp Vault integration for secret management, multiple auth methods
- **App Deployment**: Framework for deploying applications using Terraform and Ansible
- **GPU Utils**: GPU memory detection and allocation for vLLM instances
- **Credential Generator**: Automated credential generation for applications

**Example:**
```python
from _utils.server_management import TerraformHandler, AnsibleHandler, VaultHandler

# Terraform operations
tf = TerraformHandler(project_dir="./terraform/my-project")
tf.init()
tf.apply()

# Ansible playbook execution
ansible = AnsibleHandler(ansible_dir="./ansible", inventory="hosts.yml")
ansible.run_playbook("deploy.yml", extra_vars={"env": "prod"})

# Vault secret management
vault = VaultHandler(vault_addr="https://vault.example.com", base_path="my-app")
secret = vault.get_secret("database-credentials")
```

### Utils Module (`utils/`)

General-purpose utilities for common development tasks.

**Key Features:**
- **API**: Async/sync HTTP requests, parallel request execution
- **Cryptography**: RSA key generation, data encryption/decryption
- **DataFrame**: Type inference, column normalization, memory analysis
- **Email**: SMTP email sending with attachments
- **Files**: File merging (PDF, CSV, PNG), filename sanitization
- **Git**: GitHub file downloads, pull request queries
- **Redis**: Key-value operations, pub/sub, room management
- **Teams**: Microsoft Teams notifications with Adaptive Cards
- **SQL**: SQL statement generation, data validation

## Key Features

### 1. AWS Integration
- Unified session management across all AWS services
- Consistent error handling and logging
- Support for Lambda, Glue, and local environments
- Retry configurations and connection pooling

### 2. Database Operations
- Support for PostgreSQL, Redshift, and Snowflake
- Both synchronous and asynchronous operations
- Automatic type inference and validation
- S3 integration for bulk data transfers

### 3. Data Processing
- Pandas DataFrame utilities
- Type inference and conversion
- Column normalization
- Memory usage analysis

### 4. API Clients
- Alpaca trading APIs (Broker and Trader)
- Tableau Server API
- Async/sync HTTP request utilities

### 5. Infrastructure Automation
- Terraform project management and execution
- Ansible playbook automation
- HashiCorp Vault integration for secrets
- Application deployment framework
- GPU resource management

### 6. Security
- RSA encryption/decryption
- AWS Secrets Manager integration
- HashiCorp Vault support
- Secure credential management

## Usage Examples

### AWS S3 Operations
```python
from _utils.aws import s3

handler = s3.S3Handler()
# Upload DataFrame
handler.send_to_s3(data=df, bucket='my-bucket', s3_file_name='data.csv')
# Download to DataFrame
df = handler.s3_to_df(bucket='my-bucket', object_key='data.csv')
```

### Database Query
```python
from _utils.utils import sql

result = sql.run_sql(
    query="SELECT * FROM users WHERE active = true",
    queryType='query',
    dbname='production',
    rds='postgres'
)
```

### Alpaca Trading
```python
from _utils.alpaca import TraderClient

client = TraderClient(api_key, api_secret)
order = client.submit_order(
    symbol='AAPL',
    qty=10,
    side='buy',
    order_type='market',
    time_in_force='gtc'
)
```

### Tableau Report Generation
```python
from _utils.utils import tableau

with tableau.tableau_client(
    username='user',
    password='pass',
    server_url='https://tableau.example.com'
) as client:
    client.login()
    files = client.generate_report(
        view_ids=['view-123'],
        filename='report.pdf',
        merge=True
    )
```

### Infrastructure Automation
```python
from _utils.server_management import TerraformHandler, AnsibleHandler

# Deploy infrastructure with Terraform
tf = TerraformHandler(project_dir="./terraform")
tf.init()
tf.plan()
tf.apply()

# Configure servers with Ansible
ansible = AnsibleHandler(ansible_dir="./ansible", inventory="hosts.yml")
ansible.run_playbook("setup.yml", extra_vars={"app_version": "1.0.0"})
```

## Dependencies

### Core Dependencies
- Python >=3.10

### Optional Dependencies (by feature group)

**AWS:**
- boto3 >=1.28
- botocore >=1.31

**Database:**
- SQLAlchemy >=2.0
- psycopg[binary] >=3.1
- asyncpg

**Alpaca:**
- alpaca-trade-api >=3.1.0
- pandas >=2.0

**FastAPI:**
- fastapi >=0.110
- pydantic >=2.0
- uvicorn >=0.23

**ML:**
- numpy >=1.26
- pandas >=2.0
- scikit-learn >=1.4

**Tableau:**
- tableauserverclient >=0.26

**Server Management:**
- hvac (HashiCorp Vault client)
- pyyaml (for Ansible/YAML operations)

## Operational Tasks

The `tasks/` directory contains operational scripts for common infrastructure tasks:

- **deploy_app.py**: Application deployment automation
- **check_vault_secrets.py**: Vault secret validation
- **diagnose_server.py**: Server diagnostics and troubleshooting
- **explore_vault.py**: Vault exploration and management
- **deploy_coder_templates.py**: Coder template deployment
- **server_diagnostics.sh**: Shell script for server diagnostics

## Development

### Setup

#### Quick Setup (All Platforms)

The easiest way to set up the development environment:

```bash
# Create and configure virtual environment
python setup-venv.py
# or
python3 setup-venv.py
```

This will:
- Check Python version (requires 3.10+)
- Create a `.venv` virtual environment
- Install the package with development dependencies
- Install pre-commit hooks

#### Activate Virtual Environment

After setup, activate the virtual environment:

**Linux/macOS:**
```bash
source .venv/bin/activate
# or use the convenience script
source activate-venv.sh
```

**Windows PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
# or use the convenience script
.\activate-venv.ps1
```

**Windows Command Prompt:**
```cmd
.venv\Scripts\activate.bat
# or use the convenience script
activate-venv.bat
```

**Git Bash (Windows):**
```bash
source activate-venv.sh
```

#### Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv .venv

# Activate (see platform-specific commands above)

# Install package with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

For detailed setup instructions and troubleshooting, see [VENV_SETUP.md](VENV_SETUP.md).

### CI/CD Pipeline

The project includes a comprehensive CI/CD pipeline using GitHub Actions with the following features:

#### Automated Testing
- **Multi-version Testing**: Tests run on Python 3.10, 3.11, and 3.12
- **Multi-platform Testing**: Tests run on Ubuntu, Windows, and macOS
- **Test Coverage**: Code coverage reporting with minimum 60% threshold
- **Coverage Reports**: HTML and XML coverage reports generated and uploaded

#### Code Quality
- **Linting**: Automated linting with Ruff (replaces flake8, isort, and more)
- **Type Checking**: Static type checking with mypy
- **Code Formatting**: Automated code formatting with Ruff formatter
- **Security Scanning**: Automated security vulnerability scanning with Safety and Bandit

#### Pre-commit Hooks
Install and use pre-commit hooks to catch issues before committing:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Run hooks automatically before each commit (after installation)
```

Pre-commit hooks include:
- Trailing whitespace removal
- End-of-file fixes
- YAML/JSON/TOML validation
- Large file detection
- Private key detection
- Ruff linting and formatting
- MyPy type checking
- Bandit security scanning

#### Running Tests Locally

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=_utils --cov-report=html

# Run specific test markers
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run tests in verbose mode
pytest -v

# Run tests with specific markers
pytest -m "aws or vault"
```

#### Test Markers

The project uses pytest markers to categorize tests:
- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (may require external services)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.aws` - Tests requiring AWS services
- `@pytest.mark.alpaca` - Tests requiring Alpaca API
- `@pytest.mark.vault` - Tests requiring Vault
- `@pytest.mark.terraform` - Tests requiring Terraform
- `@pytest.mark.ansible` - Tests requiring Ansible
- `@pytest.mark.requires_network` - Tests requiring network access
- `@pytest.mark.requires_docker` - Tests requiring Docker

#### Code Quality Tools

**Ruff (Linting & Formatting)**
```bash
# Check code
ruff check .

# Fix issues automatically
ruff check --fix .

# Format code
ruff format .
```

**MyPy (Type Checking)**
```bash
# Type check the codebase
mypy python/_utils
```

**Bandit (Security Scanning)**
```bash
# Scan for security issues
bandit -r python/_utils
```

**Safety (Dependency Scanning)**
```bash
# Check for known vulnerabilities
safety check
```

#### GitHub Actions Workflows

The project includes several GitHub Actions workflows:

1. **CI Workflow** (`.github/workflows/ci.yml`)
   - Runs on push and pull requests
   - Tests on multiple Python versions and platforms
   - Runs linting, type checking, and security scans
   - Builds and validates the package
   - Uploads coverage reports

2. **CodeQL Analysis** (`.github/workflows/codeql.yml`)
   - Automated security analysis
   - Runs on push, PR, and weekly schedule
   - Detects security vulnerabilities

3. **Dependabot** (`.github/workflows/dependabot.yml`)
   - Weekly dependency updates
   - Security vulnerability checks
   - Outdated package detection

#### Continuous Integration Status

The CI pipeline runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

All checks must pass before merging pull requests.

#### Package Building and Publishing

The CI pipeline automatically builds the package and validates it. To publish to PyPI:

1. Create a GitHub release
2. The publish workflow will automatically trigger
3. Package will be published to PyPI (requires `PYPI_API_TOKEN` secret)

#### Configuration Files

- `pytest.ini` - Pytest configuration
- `ruff.toml` - Ruff linting and formatting configuration
- `mypy.ini` - MyPy type checking configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `pyproject.toml` - Project metadata and tool configurations

### Project Status

**Current State:**
- ✅ Core AWS integrations functional
- ✅ Database operations (PostgreSQL, Redshift, Snowflake)
- ✅ Alpaca API clients
- ✅ Tableau integration
- ✅ Server management and infrastructure automation
- ✅ General utilities

**Known Limitations:**
- ⚠️ Some modules may have incomplete type hints
- ⚠️ Documentation strings may be incomplete in some functions
- ⚠️ Error handling patterns may vary across modules

## Future Tasks / Roadmap

This section tracks planned improvements and new features to enhance the library's capabilities and demonstrate advanced software engineering practices.

### Testing & Quality Assurance
- [x] **Comprehensive Test Suite**: Add unit tests using pytest for all modules (structure created, tests in progress)
- [ ] **Integration Tests**: Test AWS service integrations with localstack or moto
- [x] **Test Coverage**: Code coverage reporting with coverage.py (60% minimum threshold)
- [x] **CI/CD Pipeline**: GitHub Actions workflow for automated testing
  - [x] Run tests on multiple Python versions (3.10, 3.11, 3.12)
  - [x] Linting with ruff and type checking with mypy
  - [x] Automated dependency vulnerability scanning (Safety, Bandit, CodeQL)
  - [x] Code coverage reporting and badges
- [x] **Pre-commit Hooks**: Automated code quality checks before commits

### Documentation & Developer Experience
- [ ] **API Documentation**: Generate comprehensive API docs with Sphinx or mkdocs
- [ ] **Code Examples**: Add more real-world usage examples and tutorials
- [ ] **Type Stubs**: Complete type hints and generate .pyi stub files
- [ ] **Changelog**: Maintain CHANGELOG.md for version tracking
- [ ] **Contributing Guide**: Detailed CONTRIBUTING.md with development workflow

### Code Quality & Standards
- [ ] **Type Hints**: Complete type annotations across all modules
- [ ] **Error Handling**: Standardize error handling patterns and custom exceptions
- [ ] **Logging**: Unified logging configuration and structured logging
- [x] **Code Formatting**: Enforce consistent formatting with Ruff formatter
- [x] **Linting**: Comprehensive linting rules with Ruff

### Performance & Scalability
- [ ] **Async Support**: Expand async/await patterns for I/O-bound operations
- [ ] **Connection Pooling**: Optimize database and HTTP connection pooling
- [ ] **Caching**: Add caching layer for frequently accessed data (Redis integration)
- [ ] **Performance Benchmarks**: Add performance testing and benchmarks
- [ ] **Memory Profiling**: Tools for memory usage analysis and optimization

### New Features & Integrations
- [ ] **Kubernetes Integration**: Add Kubernetes client utilities for cluster management
- [ ] **Docker Utilities**: Container management and Docker Compose utilities
- [ ] **Monitoring & Observability**: Integration with Prometheus, Grafana, or Datadog
- [ ] **Message Queues**: Support for RabbitMQ, SQS, and Kafka
- [ ] **GraphQL Support**: GraphQL client utilities and query builders
- [ ] **WebSocket Support**: Real-time communication utilities
- [ ] **Machine Learning Pipeline**: Expand ML utilities with model training helpers

### Security Enhancements
- [ ] **Security Audit**: Comprehensive security review and vulnerability assessment
- [ ] **Secrets Rotation**: Automated secret rotation utilities
- [ ] **OAuth2/OIDC**: Enhanced authentication and authorization support
- [ ] **Encryption Utilities**: Additional encryption algorithms and key management
- [ ] **Security Best Practices**: Documentation and examples for secure usage

### Developer Tools
- [ ] **CLI Tools**: Command-line interface for common operations
- [ ] **Development Scripts**: Automated setup and development environment scripts
- [ ] **Docker Development**: Docker Compose setup for local development
- [x] **Pre-commit Configuration**: Shared pre-commit configuration file
- [ ] **VS Code Settings**: Recommended VS Code settings and extensions

### Package Distribution
- [ ] **PyPI Publication**: Publish package to PyPI for easy installation
- [ ] **Version Management**: Automated versioning with semantic versioning
- [ ] **Release Automation**: Automated release process with GitHub Actions
- [ ] **Package Signing**: GPG signing for package releases
- [ ] **Multi-platform Support**: Ensure compatibility across Windows, Linux, macOS

### Advanced Features
- [ ] **Plugin System**: Extensible plugin architecture for custom integrations
- [ ] **Configuration Management**: Centralized configuration with environment-based settings
- [ ] **Feature Flags**: Feature flag system for gradual rollouts
- [ ] **Rate Limiting**: Built-in rate limiting utilities for API calls
- [ ] **Retry Strategies**: Advanced retry mechanisms with exponential backoff
- [ ] **Circuit Breaker Pattern**: Circuit breaker implementation for resilience

### Community & Open Source
- [x] **Issue Templates**: GitHub issue and PR templates
- [ ] **Code of Conduct**: Community guidelines and code of conduct
- [ ] **Security Policy**: SECURITY.md for responsible disclosure
- [ ] **Examples Repository**: Separate repository with usage examples
- [ ] **Blog Posts**: Technical blog posts showcasing features and use cases

## Contributing

This is a utility library. For contributions:
1. Follow existing code patterns
2. Add type hints for new functions
3. Include docstrings
4. Update this README for new features

## License

MIT License - See LICENSE file for details

## Author

Cole Dylewski

