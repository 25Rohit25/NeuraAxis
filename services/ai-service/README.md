# NEURAXIS AI Service

> FastAPI Backend for AI-Powered Medical Diagnosis

## Overview

This service provides the AI/ML backend for NEURAXIS, handling medical image analysis, symptom assessment, and diagnosis generation.

## Features

- 🧠 **AI Diagnosis** - ML-powered medical diagnosis assistance
- 🖼️ **Image Analysis** - Medical image processing (X-ray, CT, MRI)
- 📊 **Analytics** - Patient data analytics and insights
- 🔐 **Secure API** - JWT authentication and HIPAA compliance
- ⚡ **High Performance** - Async processing with Redis caching

## Project Structure

```
ai-service/
├── app/
│   ├── api/              # API routes
│   │   ├── v1/           # API version 1
│   │   │   ├── auth.py
│   │   │   ├── diagnosis.py
│   │   │   ├── patients.py
│   │   │   └── images.py
│   │   └── deps.py       # Shared dependencies
│   ├── core/             # Core configuration
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── ai/           # AI/ML services
│   │   └── diagnosis/    # Diagnosis services
│   ├── db/               # Database
│   │   ├── base.py
│   │   └── session.py
│   └── main.py           # Application entry
├── tests/                # Test files
├── alembic/              # Database migrations
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

See `.env.example` in the project root.

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Scripts

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload` | Start dev server |
| `pytest` | Run tests |
| `alembic upgrade head` | Run migrations |
| `alembic revision --autogenerate -m "message"` | Create migration |

## Models

The service uses several ML models:
- **Symptom Analyzer** - NLP model for symptom extraction
- **Image Classifier** - CNN for medical image classification
- **Diagnosis Generator** - Ensemble model for diagnosis prediction

## License

Proprietary - All rights reserved.
