# Contributing to ai-search-engine

Thank you for your interest in contributing to ai-search-engine! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Bugs

1. Check existing [issues](https://github.com/LiuChenICBC/ai-search-engine/issues) to avoid duplicates
2. Create a new issue with the **Bug Report** template
3. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, etc.)
   - Relevant logs or error messages

### Suggesting Features

1. Check existing [issues](https://github.com/LiuChenICBC/ai-search-engine/issues) for similar suggestions
2. Create a new issue with the **Feature Request** template
3. Include:
   - Clear description of the feature
   - Use case and benefits
   - Implementation ideas (if any)

### Submitting Changes

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes
4. Run tests:
   ```bash
   python3 -m pytest test_*.py -v
   ```
5. Run linting:
   ```bash
   ruff check .
   ruff format .
   ```
6. Commit with a clear message:
   ```bash
   git commit -m "Add: feature description"
   ```
7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
8. Create a Pull Request

## Development Setup

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ai-search-engine.git
cd ai-search-engine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install ruff pytest mypy

# Copy environment file
cp .env.example .env
```

### Running Tests

```bash
# Run all tests
python3 -m pytest test_*.py -v

# Run with coverage
python3 -m pytest test_*.py --cov=. --cov-report=term-missing
```

### Code Style

- We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Line length: 88 characters
- Follow PEP 8 style guide

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking

```bash
mypy .
```

## Code Guidelines

### Commit Messages

Use the format: `Type: description`

Types:
- `Add`: New feature or file
- `Fix`: Bug fix
- `Update`: Improvement to existing feature
- `Refactor`: Code refactoring without behavior change
- `Docs`: Documentation changes
- `Test`: Adding or updating tests
- `Chore`: Maintenance tasks

Examples:
```
Add: user rate limiting
Fix: CSRF token validation
Update: improve error messages
Docs: add API documentation
```

### Python Code

- Use type hints
- Keep functions focused and small
- Write docstrings for public functions
- Handle errors gracefully
- Use async/await when appropriate

### Testing

- Write tests for new features
- Maintain test coverage
- Test both success and error paths
- Mock external services

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for project structure and design decisions.

## Questions?

If you have questions about contributing, feel free to:
- Open an issue
- Start a discussion on GitHub

Thank you for contributing!
