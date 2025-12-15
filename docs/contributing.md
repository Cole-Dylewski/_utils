# Contributing to _utils

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

See [Installation Guide](installation.md) for detailed setup instructions.

## Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest`
5. Check code quality: `ruff check . && mypy python`
6. Commit your changes: `git commit -m "feat: Add new feature"`
7. Push to your fork: `git push origin feature/your-feature`
8. Create a pull request

## Code Style

- Follow PEP 8
- Use type hints for all functions
- Write docstrings (Google style)
- Keep line length to 100 characters
- Run `ruff format .` before committing

## Testing

- Write tests for all new functionality
- Aim for 80%+ test coverage
- Use appropriate pytest markers
- Run tests: `pytest --cov=python/_utils`

## Documentation

- Update docstrings for new functions
- Add examples to this documentation
- Update CHANGELOG.md for user-facing changes

## Questions?

Open an issue on GitHub for questions or discussions.
