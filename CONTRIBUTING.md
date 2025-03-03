# Contributing to Lastify

Thank you for considering contributing to Lastify! This document provides guidelines and instructions for contributing to the project.

## Development Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lastify.git
   cd lastify
   ```

2. Install development dependencies with Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Code Style

This project follows standard Python coding practices:

- We use [Black](https://black.readthedocs.io/en/stable/) for code formatting
- We use [isort](https://pycqa.github.io/isort/) for import sorting
- Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines

To format your code automatically:

```bash
# Format code with Black
poetry run black lastify tests

# Sort imports
poetry run isort lastify tests
```

## Testing

All contributions should include appropriate tests:

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=lastify
```

Ensure that:
- All tests pass
- Code coverage doesn't decrease
- New features have corresponding tests

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and formatting tools
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Commit Messages

Follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Documentation

- Update the README.md if necessary
- Add or update docstrings for public methods
- Consider adding examples if implementing a new feature

## Version Control Practices

- Make small, focused commits
- Rebase your branch against the latest main before submitting a PR
- Squash multiple commits if they represent a single logical change

## Release Process

For maintainers:

1. Update version in `pyproject.toml` using semantic versioning
2. Update CHANGELOG.md (if present)
3. Create a new GitHub release with appropriate tag
4. Build and publish the package to PyPI (if applicable):
   ```bash
   poetry build
   poetry publish
   ```

## Questions?

If you have questions about contributing, feel free to open an issue for discussion.

Thank you for contributing to Lastify!
