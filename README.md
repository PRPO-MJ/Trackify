# Trackify

**Trackify** is a microservices based open source goal and activity tracking application that helps users manage their personal goals, track daily entries, generate PDF reports, and receive email notifications.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development with Docker Compose](#local-development-with-docker-compose)
  - [Accessing the Application](#accessing-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Trackify is a full-stack web application designed to help users track their goals and daily activities. The application follows a microservices architecture, with each service responsible for a specific domain of functionality.

### Key Capabilities:
- **User Management**: Google OAuth authentication and user profile management
- **Goal Tracking**: Create, update, and monitor personal goals
- **Activity Entries**: Log daily activities and progress toward goals
- **PDF Reports**: Generate comprehensive PDF reports of user progress
- **Email Notifications**: Automated email notifications and report delivery

---

## 🏗️ Architecture

Trackify is built using a **microservices architecture** with the following services:

| Service | Port | Description |
|---------|------|-------------|
| **UI** | 3000 | React/TypeScript frontend with Vite |
| **User Service** | 8006 | User authentication and profile management |
| **Goals Service** | 8008 | Goal creation and management |
| **Entries Service** | 8009 | Activity entry tracking |
| **Mailer Service** | 8010 | Email notification handling |
| **PDF Service** | 8011 | PDF report generation |
| **Database** | 5432 | PostgreSQL database cluster |

All services communicate through a Docker network and are orchestrated using Docker Compose for local development.

---

## ✨ Features

- 🔐 **Google OAuth Integration** - Secure authentication using Google accounts
- 🎯 **Goal Management** - Create and track personal goals with deadlines
- 📝 **Activity Logging** - Record daily entries and progress
- 📊 **PDF Reports** - Generate detailed progress reports
- 📧 **Email Notifications** - Automated email delivery with AWS SES
- 🔄 **Real-time Updates** - Responsive UI with real-time data
- 🚀 **RESTful APIs** - Well-documented FastAPI services
- 🐳 **Containerized** - Fully containerized with Docker
- ☸️ **Kubernetes Ready** - Production deployment with Kubernetes

---

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **shadcn/ui** component library

### Backend
- **FastAPI** (Python 3.11+)
- **PostgreSQL** for data persistence
- **SQLAlchemy** ORM
- **Pydantic** for data validation
- **JWT** for authentication
- **PYTEST** for testing

### Infrastructure
- **Docker** & **Docker Compose**
- **Kubernetes** for production
- **AWS EKS** (optional cloud deployment)
- **Cloudflare** for UI hosting (optional)

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Git**

#### Verify Installation

```bash
docker --version
docker compose --version
```

### Local Development with Docker Compose

#### 1. Clone the Repository

```bash
# Clone from the main branch (production-ready)
git clone git@github.com:PRPO-MJ/Trackify.git
cd Trackify

# OR checkout the dev branch for latest features
git checkout dev
```

#### 2. Configure Google OAuth (Optional)

To use Google authentication, you need to set up OAuth credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Create OAuth 2.0 credentials
5. Add `http://localhost:3000` to authorized JavaScript origins
6. Add `http://localhost:3000/auth/callback` to authorized redirect URIs

Update the `VITE_GOOGLE_CLIENT_ID` in [docker-compose.yaml](docker-compose.yaml) with your client ID:

```yaml
VITE_GOOGLE_CLIENT_ID: "your-google-client-id-here"
```

> **Note**: The application will not work without Google OAuth as authentication features will be limited.

#### 3. Start the Application

Start all services using Docker Compose:

```bash
docker compose up --build
```

This command will:
- Build Docker images for all services
- Create a PostgreSQL database cluster
- Initialize the database schema
- Start all microservices
- Start the UI on port 3000

**First time startup** may take longer to build all images.

#### 4. Wait for Services to be Ready

Monitor the logs to ensure all services are healthy:

```bash
# In another terminal
docker compose ps
```

All services should show status as **healthy**. The UI will be available once you see:

```
trackify-ui | VITE ready in X ms
trackify-ui | Local: http://localhost:3000
```

### Accessing the Application

Once all services are running:

| Component | URL | Description |
|-----------|-----|-------------|
| **UI** | http://localhost:3000 | Main application interface |
| **User Service API** | http://localhost:8006/docs | Swagger documentation |
| **Goals Service API** | http://localhost:8008/docs | Swagger documentation |
| **Entries Service API** | http://localhost:8009/docs | Swagger documentation |
| **Mailer Service API** | http://localhost:8010/docs | Swagger documentation |
| **PDF Service API** | http://localhost:8011/docs | Swagger documentation |
| **Database** | localhost:5432 | PostgreSQL (user: postgres, password: postgres123!) |


### Stopping the Application

To stop all services:

```bash
# Stop and remove containers
docker compose down

# Stop and remove containers, volumes, and images
docker compose down -v --rmi all
```

---

## 📁 Project Structure

```
Trackify/
├── UI/                         # React frontend application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page components
│   │   ├── controllers/        # Business logic
│   │   └── types/              # TypeScript type definitions
│   └── Dockerfile
│
├── User-Service/               # User authentication service
│   ├── src/
│   │   ├── main.py             # FastAPI application
│   │   ├── auth.py             # Authentication logic
│   │   ├── database.py         # Database models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── config.py           # Configuration
│   │   ├── goals_client.py     # Module to communicate with Goals Service
│   │   ├── entries_client.py   # Module to communicate with Entries Service
│   │   ├── mailer_client.py    # Module to communicate with Mailer Service
│   │   └── pdf_client.py       # Module to communicate with PDF Service
│   ├── test/
│   ├── .env                    # Environment variables
│   ├── .gitignore              # Git ignore rules 
│   ├── Dockerfile              # Docker image build instructions 
│   ├── pyproject.toml          # Python project metadata and dependencies
│   └── requirements.txt        # Python dependencies
│
├── Goals-Service/              # Goal management service
│   ├── src/
│   └── test/
│
├── Entries-Service/            # Activity tracking service
│   ├── src/
│   └── test/
│
├── Mailer-Service/             # Email notification service
│   ├── src/
│   └── test/
│
├── PDF-Service/                # PDF generation service
│   ├── src/
│   └── test/
│
├── Database/
│   └── init.sql                # Database initialization script
│
├── .github/
│   └── workflows
│       └── ci-cd.yml           # FastAPI application
│
├── docker-compose.yaml         # Local development setup
├── k8s-msnifest.yaml           # Run k8s setup
├── README                      # Project overview and instructions
├── CODE_OF_CONDUCT             # Community standards and guidelines
└── SECURITY                    # Security policies and reporting

```

---


## 📚 API Documentation

Each microservice exposes interactive API documentation via Swagger UI:

- **User Service**: http://localhost:8006/api/docs
  - User registration and authentication
  - Profile management
  - Google OAuth integration

- **Goals Service**: http://localhost:8008/api/docs
  - Create, read, update, delete goals
  - Goal status tracking
  - Goal progress metrics

- **Entries Service**: http://localhost:8009/api/docs
  - Create and manage activity entries
  - Link entries to goals
  - Query entries by date range

- **Mailer Service**: http://localhost:8010/api/docs
  - Send email notifications
  - Email template management

- **PDF Service**: http://localhost:8011/api/docs
  - Generate progress reports
  - Export data to PDF

### Example API Requests

#### User Service - Health Check
```bash
curl http://localhost:8006/api/users/health/liveness
```

#### Goals Service - Get All Goals
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8008/api/goals/
```

---




## 🔄 Development Workflow

- Start from the `dev` branch.
- Create a feature branch for your changes.
- When ready, create a Pull Request to merge into `dev`.


### Viewing Logs

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f user-service
docker compose logs -f ui

# View last 100 lines
docker compose logs --tail=100 goals-service
```

### Rebuilding After Changes

```bash
# Rebuild specific service
docker compose up --build user-service

# Rebuild all services
docker compose up --build

# Force rebuild without cache
docker compose build --no-cache
docker compose up
```

### Accessing Service Containers

```bash
# Open a shell in a container
docker exec -it user-service bash
docker exec -it database psql -U postgres -d trackify

# Check container status
docker compose ps

# View resource usage
docker stats
```

---

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start

**Problem**: Services fail to start or crash immediately.

**Solution**:
```bash
# Check logs for errors
docker compose logs

# Remove old containers and volumes
docker compose down -v

# Rebuild and restart
docker compose up --build
```

#### Database Connection Issues

**Problem**: Services can't connect to the database.

**Solution**:
```bash
# Check if database is healthy
docker compose ps database

# Check database logs
docker compose logs database

# Restart database
docker compose restart database
```

#### Port Already in Use

**Problem**: `Error: port is already allocated`

**Solution**:
```bash
# Find process using the port (e.g., port 3000)
lsof -i :3000
# or
netstat -tulpn | grep 3000

# Kill the process
kill -9 <PID>

# Or change the port in docker-compose.yaml
```

#### Out of Disk Space

**Problem**: Docker runs out of space.

**Solution**:
```bash
# Remove unused Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune
```

#### UI Can't Connect to Backend

**Problem**: CORS errors or network errors in browser console.

**Solution**:
1. Ensure all services are running: `docker compose ps`
2. Check service health endpoints:
   ```bash
   curl http://localhost:8006/api/users/health/liveness
   ```
3. Verify environment variables in [docker-compose.yaml](docker-compose.yaml)
4. Clear browser cache and hard reload (Ctrl+Shift+R)

#### Google OAuth Not Working

**Problem**: Google sign-in fails.

**Solution**:
1. Verify `VITE_GOOGLE_CLIENT_ID` in [docker-compose.yaml](docker-compose.yaml)
2. Check Google Cloud Console OAuth settings
3. Ensure redirect URIs are correctly configured
4. Check browser console for specific error messages

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch from `dev`
3. Write tests for new features
4. Ensure all tests pass
5. Follow the existing code style
6. Submit a pull request to the `dev` branch

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community guidelines.

---

## 📄 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on the repository
- Review [SECURITY.md](SECURITY.md) for security-related concerns

---

**Happy Tracking! ⌛**