# _utils Documentation

Welcome to the `_utils` library documentation!

## Overview

`_utils` is a comprehensive Python utility library providing shared utilities for AWS services, Alpaca trading APIs, database operations, data processing, and more. The library is designed to be modular, allowing you to install only the features you need.

## Quick Start

### Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install package in editable mode
pip install -e .
```

### Basic Usage

```python
from aws import s3
from alpaca import TraderClient
from utils import sql

# AWS S3 operations
s3_handler = s3.S3Handler()
s3_handler.send_to_s3(data=df, bucket='my-bucket', s3_file_name='data.csv')

# Alpaca trading
client = TraderClient(api_key, api_secret)
account = client.get_account()

# SQL operations
result = sql.run_sql(query="SELECT * FROM users", queryType='query', dbname='mydb')
```

## Features

- **AWS Integration**: S3, DynamoDB, ECS, Glue, Cognito, Secrets Manager, and more
- **Alpaca Trading**: Complete Broker and Trader API clients
- **Database Operations**: PostgreSQL, Redshift, Snowflake support
- **Data Processing**: DataFrame utilities, SQL generation, type inference
- **Tableau Integration**: Report generation and metadata management
- **Infrastructure Automation**: Terraform, Ansible, Vault integration
- **General Utilities**: Cryptography, email, files, git, and more

## Documentation Structure

- **[Installation Guide](installation.md)** - Setup and installation instructions
- **[API Reference](api/)** - Complete API documentation for all modules
- **[Examples](examples.md)** - Real-world usage examples
- **[Contributing](contributing.md)** - How to contribute to the project

## Key Modules

### AWS Module
Comprehensive AWS service integrations with session management and error handling.

### Alpaca Module
Trading API clients for both Broker and Trader APIs with market data access.

### Database Module
Database operations for PostgreSQL, Redshift, and Snowflake with async support.

### Utils Module
General-purpose utilities for common development tasks.

## Support

- **GitHub**: [https://github.com/Cole-Dylewski/_utils](https://github.com/Cole-Dylewski/_utils)
- **Issues**: [GitHub Issues](https://github.com/Cole-Dylewski/_utils/issues)
- **Security**: See [SECURITY.md](https://github.com/Cole-Dylewski/_utils/blob/main/SECURITY.md) for security concerns

## License

MIT License - See LICENSE file for details
