# AI Service Tests

This directory contains tests for the NEURAXIS AI Service.

## Structure

```
tests/
├── api/              # API endpoint tests
│   ├── test_auth.py
│   ├── test_patients.py
│   └── test_diagnosis.py
├── services/         # Service layer tests
├── unit/             # Unit tests
├── integration/      # Integration tests
└── conftest.py       # Pytest fixtures
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/api/test_auth.py

# Run with verbose output
pytest -v
```
