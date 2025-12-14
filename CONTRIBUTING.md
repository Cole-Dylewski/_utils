# Contributing to _utils

Thank you for your interest in contributing to _utils! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/_utils.git
   cd _utils
   ```

2. **Set up Virtual Environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   
   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make Changes**
   - Write code following the project's style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Tests Locally**
   ```bash
   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=_utils --cov-report=html
   
   # Run specific test markers
   pytest -m unit
   ```

4. **Check Code Quality**
   ```bash
   # Lint code
   ruff check .
   
   # Format code
   ruff format .
   
   # Type check
   mypy python
   
   # Security scan
   bandit -r python
   safety check
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   ```
   
   Pre-commit hooks will run automatically. If they fail, fix the issues and commit again.

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a pull request on GitHub.

## Code Style

### Python Style Guide
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep line length to 100 characters (enforced by Ruff)

### Code Formatting
- Use Ruff for both linting and formatting
- Run `ruff format .` before committing
- The CI pipeline will check formatting automatically

### Type Hints
- Use type hints for all function parameters and return values
- Use `typing` module for complex types
- Use `Optional` for nullable types
- Use `Union` for multiple possible types

### Docstrings
- Use Google-style docstrings
- Include parameter descriptions
- Include return value descriptions
- Include example usage when helpful

Example:
```python
def process_data(data: list[str], threshold: int = 10) -> dict[str, int]:
    """
    Process a list of data items and return statistics.
    
    Args:
        data: List of data items to process
        threshold: Minimum count threshold for inclusion
        
    Returns:
        Dictionary mapping items to their counts
        
    Example:
        >>> process_data(['a', 'b', 'a'], threshold=1)
        {'a': 2, 'b': 1}
    """
    # Implementation
```

## Testing Guidelines

### Writing Tests
- Write tests for all new functionality
- Use descriptive test names
- Use pytest fixtures for common setup
- Mark tests appropriately (unit, integration, slow, etc.)

### Test Structure
- Place tests in `python/tests/`
- Mirror the source structure
- Use `test_` prefix for test files
- Use `Test` prefix for test classes

### Test Markers
Use appropriate markers for tests:
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.aws` - Tests requiring AWS
- `@pytest.mark.vault` - Tests requiring Vault
- etc.

### Running Tests
```bash
# All tests
pytest

# Specific markers
pytest -m unit
pytest -m "not slow"

# With coverage
pytest --cov=_utils --cov-report=html
```

## Pull Request Process

1. **Update Documentation**
   - Update README.md if adding new features
   - Update docstrings for new functions
   - Add examples if applicable

2. **Ensure Tests Pass**
   - All tests must pass
   - Code coverage should not decrease
   - Minimum 60% coverage required

3. **Check CI Status**
   - All CI checks must pass
   - Fix any linting or type checking errors
   - Address security scan warnings

4. **Create Pull Request**
   - Use descriptive title
   - Fill out PR template
   - Link related issues
   - Request review from maintainers

5. **Address Feedback**
   - Respond to review comments
   - Make requested changes
   - Update PR as needed

## Commit Messages

Write clear, descriptive commit messages:

```
feat: Add new S3 upload method with progress tracking

- Add upload_with_progress() method to S3Handler
- Include progress callback support
- Add tests for new functionality
- Update documentation

Closes #123
```

Use conventional commit prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

## Code Review Guidelines

### For Contributors
- Be open to feedback
- Respond to all review comments
- Make requested changes promptly
- Ask questions if unclear

### For Reviewers
- Be constructive and respectful
- Explain reasoning for suggestions
- Approve when satisfied
- Request changes when needed

## Questions?

If you have questions about contributing:
- Open an issue for discussion
- Check existing issues and PRs
- Review the codebase for examples

Thank you for contributing to _utils!

