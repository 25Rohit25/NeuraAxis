# NEURAXIS 🧠

> **AI-Powered Medical Diagnosis Platform**

[![Built with Turborepo](https://img.shields.io/badge/Built%20with-Turborepo-FF4154?style=for-the-badge&logo=turborepo)](https://turbo.build/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)

---

## 📋 Overview

NEURAXIS is a cutting-edge medical diagnosis platform that leverages artificial intelligence to assist healthcare professionals in making accurate, timely diagnoses. Built as a modern monorepo, it combines the power of Next.js for a responsive frontend with FastAPI-powered AI services on the backend.

### Key Features

- 🔬 **AI-Powered Diagnostics** - Advanced ML models for medical image analysis and symptom assessment
- 🏥 **HIPAA Compliant** - Enterprise-grade security and audit logging
- ⚡ **Real-time Updates** - WebSocket-based live notifications and updates
- 📊 **Analytics Dashboard** - Comprehensive insights and reporting
- 🔐 **Multi-tenant Architecture** - Support for multiple healthcare organizations

---

## 🏗️ Architecture

```
neuraxis/
├── apps/
│   ├── web/                 # Next.js 15 Frontend
│   └── docs/                # Documentation site
├── packages/
│   ├── ui/                  # Shared React components
│   ├── shared-types/        # TypeScript type definitions
│   ├── utils/               # Common utilities
│   └── config/              # Shared configurations
├── services/
│   └── ai-service/          # FastAPI AI/ML service
├── docker/                  # Docker configurations
└── infrastructure/          # IaC and deployment configs
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** >= 18.0.0
- **Python** >= 3.11
- **Docker** & **Docker Compose**
- **pnpm** or **npm** >= 9.0.0

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/neuraxis.git
   cd neuraxis
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start infrastructure services**
   ```bash
   npm run docker:up
   ```

5. **Run development servers**
   ```bash
   npm run dev
   ```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |
| Redis Commander | http://localhost:8081 |

---

## 📦 Workspaces

### Apps

| Package | Description |
|---------|-------------|
| `@neuraxis/web` | Main Next.js 15 frontend application |
| `@neuraxis/docs` | Documentation and API reference site |

### Packages

| Package | Description |
|---------|-------------|
| `@neuraxis/ui` | Shared React component library |
| `@neuraxis/shared-types` | TypeScript types and interfaces |
| `@neuraxis/utils` | Common utility functions |
| `@neuraxis/config` | Shared ESLint, TypeScript, Tailwind configs |

### Services

| Package | Description |
|---------|-------------|
| `ai-service` | FastAPI backend for AI/ML processing |

---

## 🛠️ Development

### Available Scripts

```bash
# Development
npm run dev          # Start all services in development mode
npm run build        # Build all packages
npm run lint         # Lint all packages
npm run test         # Run all tests
npm run type-check   # TypeScript type checking

# Docker
npm run docker:up    # Start infrastructure services
npm run docker:down  # Stop infrastructure services
npm run docker:logs  # View service logs

# Database
npm run db:migrate   # Run database migrations
npm run db:seed      # Seed database with sample data

# Formatting
npm run format       # Format all files with Prettier
npm run format:check # Check formatting without changes
```

### Turborepo Commands

```bash
# Run a specific task
npx turbo run build --filter=@neuraxis/web

# Run with verbose output
npx turbo run dev --verbosity=2

# Generate dependency graph
npx turbo run build --graph
```

---

## 🐳 Docker

### Development Environment

```bash
# Start all services
docker-compose up -d

# Start with optional tools (pgAdmin, Redis Commander)
docker-compose --profile tools up -d

# Start with S3-compatible storage (MinIO)
docker-compose --profile storage up -d

# View logs
docker-compose logs -f backend
```

### Service Profiles

| Profile | Services Included |
|---------|------------------|
| (default) | postgres, redis, frontend, backend |
| tools | + pgAdmin, Redis Commander |
| storage | + MinIO |

---

## 🔒 Security & Compliance

NEURAXIS is designed with healthcare compliance in mind:

- **HIPAA Compliance** - Audit logging, data encryption, access controls
- **SOC 2 Ready** - Security best practices implemented
- **Data Encryption** - At-rest and in-transit encryption
- **Role-Based Access Control** - Fine-grained permissions

---

## 📚 Documentation

- [Architecture Overview](./docs/architecture.md)
- [API Reference](./docs/api.md)
- [Deployment Guide](./docs/deployment.md)
- [Contributing Guidelines](./CONTRIBUTING.md)

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](./CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 👥 Team

Built with ❤️ by the NEURAXIS Team

---

<p align="center">
  <strong>Transforming Healthcare with AI</strong>
</p>
