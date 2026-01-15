# Event Dispatcher Microservice

The Event Dispatcher is a microservice designed to handle notification dispatching for the ecosystem. Currently, it focuses on dispatching health alerts when services fail, with plans to expand to handle all notification types in the future.

## Features

- **Health Alert Dispatch**: Sends email notifications when service health checks fail.
- **Extensible Architecture**: Built with FastAPI to easily add more notification channels and event types.
- **Asynchronous Processing**: Uses background tasks for non-blocking email sending.
- **Kubernetes Ready**: Includes full deployment manifests and scripts for Kubernetes environments.

## Tech Stack

- **Python 3.12**
- **FastAPI**: High-performance web framework for APIs.
- **Uvicorn**: ASGI server.
- **Docker**: Containerization.
- **Kubernetes**: Orchestration.

## Prerequisites

- Python 3.12+
- Docker
- Kubernetes cluster (for deployment)
- SMTP Server credentials (e.g., Gmail App Password)
- StockFlow

## Project Structure

```
event-dispatcher/
├── deploy_project.sh           # Deployment script for Kubernetes
├── dockerfiles/                # Docker build files
├── kubernetes/                 # Kubernetes manifests (deployments, services)
├── src/
│   ├── api/
│   │   └── main.py            # FastAPI application entry point
│   └── core/
│       └── event_dispatch_functions.py # Core logic for email dispatching
├── templates/                  # Email templates
└── README.md
```

## Configuration

The service is configured using environment variables. You must set these in your environment or Kubernetes secrets.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMTP_HOST` | SMTP Server Hostname | None | **Yes** |
| `SMTP_PASSWORD` | SMTP Authentication Password | None | **Yes** |
| `SMTP_PORT` | SMTP Server Port | `587` | No |
| `SMTP_USER` | SMTP Username | `noreply.avinash.s@gmail.com` | No |
| `SENDER_ADDR` | Email Sender Address | `noreply.avinash.s@gmail.com` | No |
| `HEALTH_ALERT_RECEIVER` | Recipient for health alerts | `kingaiva@icloud.com` | No |

## Deployment

This service is designed to be deployed to a Kubernetes cluster using the provided helper script.

### Using `deploy_project.sh`

The `deploy_project.sh` script automates the deployment process, including applying manifests and verifying service health.

**Requirement:** The target Kubernetes namespace must exist with StockFlow before running the script.

**Usage:**

```bash
chmod +x deploy_project.sh
./deploy_project.sh [namespace]
```

- **`namespace`**: (Optional) The Kubernetes namespace to deploy into. Defaults to `default`.

**What the script does:**
1. validates that the specified namespace exists.
2. Removes existing deployments of `event-dispatcher` to ensure a clean state.
3. Deploys the application using the manifests in `kubernetes/`.
4. Waits for the deployment to become available.
5. Exposes the application via the configured Service.

## API Documentation

### Health Check

- **Endpoint:** `GET /health`
- **Description:** Checks if the service is running.
- **Response:**
  ```json
  {
    "status": "OK",
    "timestamp": "2024-01-15 12:00:00.000000"
  }
  ```

### Send Health Alert

- **Endpoint:** `POST /api/v1/health-alert`
- **Description:** Triggers a health alert email for failed services.
- **Body:**
  ```json
  {
    "issues": [
      "service-a-failure",
      "database-connection-error"
    ]
  }
  ```
- **Response:**
  ```json
  {
    "status": "Health alert email sent"
  }
  ```

## Future Plans

- Add support for generic notification events.
- Integrate Slack/Discord webhooks.
- Implement specialized email templates for different event types.
