# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Unified `setup.py` script for cross-platform virtual environment setup
- Master `requirements.txt` consolidating all dependencies
- Production readiness plan and roadmap
- Security policy documentation
- Custom exception hierarchy (`_utils.exceptions`) with domain-specific exceptions
- Structured logging utilities (`_utils.utils.logger`) with JSON support
- CLI tool (`utils` command) for development and testing operations
- Resilience patterns (`_utils.utils.resilience`): retry, circuit breaker, rate limiting, timeout
- API documentation setup with MkDocs and auto-generation from docstrings
- GitHub Actions workflow for documentation deployment

### Changed
- Consolidated all requirements files into single `requirements.txt`
- Unified activation scripts into `setup.py`
- Consolidated documentation into README.md
- Updated setup instructions to use `setup.py`

### Fixed
- CodeQL false positives by excluding overly sensitive queries
- URL sanitization in git utilities
- File closure issues in basic utilities

## [0.1.0] - 2024-12-14

### Added
- Initial release of `_utils` package
- AWS service integrations (S3, DynamoDB, ECS, Glue, Cognito, Secrets Manager, etc.)
- Alpaca trading API clients (Broker and Trader APIs)
- Database utilities (PostgreSQL, Redshift, Snowflake)
- SQL operations and DataFrame utilities
- Tableau Server API integration
- Server management utilities (Terraform, Ansible, Vault)
- General utilities (cryptography, email, files, git, etc.)
- Comprehensive CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Test infrastructure with pytest
- Code quality tools (Ruff, MyPy, Bandit, Safety)

### Security
- CodeQL security scanning integration
- Dependency vulnerability scanning
- Secure credential handling patterns

---

## Version History

- **0.1.0** (2024-12-14): Initial release

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
