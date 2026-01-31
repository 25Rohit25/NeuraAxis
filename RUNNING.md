# How to Run NEURAXIS

This guide explains how to spin up the entire NEURAXIS platform locally using Docker.

## Prerequisites

- **Docker** and **Docker Compose** installed.
- **Node.js** (optional, for local script running).

## Quick Start

1. **Start the Environment**:

   ```bash
   # From the project root
   npm run docker:up
   # OR directly
   docker-compose up -d --build
   ```

2. **Wait for Services**:
   - It may take a few minutes for the initial build of Frontend (`neuraxis-frontend`) and Backend (`neuraxis-backend`).
   - Monitor logs using:
     ```bash
     npm run docker:logs
     ```

## Access Points

| Service                 | URL                                                      | Credentials (Default)            |
| :---------------------- | :------------------------------------------------------- | :------------------------------- |
| **Frontend Web App**    | [http://localhost:3000](http://localhost:3000)           | N/A                              |
| **AI Service API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | N/A                              |
| **Realtime Service**    | ws://localhost:4000                                      | N/A                              |
| **MinIO Console** (S3)  | [http://localhost:9001](http://localhost:9001)           | `neuraxis` / `neuraxis123`       |
| **pgAdmin** (DB UI)     | [http://localhost:5050](http://localhost:5050)           | `admin@neuraxis.local` / `admin` |
| **Redis Commander**     | [http://localhost:8081](http://localhost:8081)           | N/A                              |

## Default Environment Variables

The setup uses default values suitable for local development.

- **Database**: `postgres://neuraxis_user:neuraxis_dev_password@postgres:5432/neuraxis`
- **Redis**: `redis://redis:6379`
- **JWT Secret**: `neuraxis_secret_key`

## Troubleshooting

- **Port Conflicts**: Ensure ports `3000`, `8000`, `4000`, `5432`, `6379` are free.
- **Database Connection**: If the backend fails to connect, wait a moment; Docker Compose handles retry, but initial DBinit takes time.
- **Build Failures**: Run `docker-compose build --no-cache` to force a rebuild.

## Stopping

```bash
npm run docker:down
```
