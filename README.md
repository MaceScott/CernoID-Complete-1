# CernoID Security System

A comprehensive security and surveillance system with facial recognition, real-time monitoring, and advanced analytics.

## Features
- Face Recognition and Identity Management
- Access Control and Zone Management
- Real-time Monitoring and Alerts
- Comprehensive Logging and Analytics
- Scalable Architecture with Kubernetes Support

## Project Structure

```
.
├── frontend/           # React frontend application
├── backend/           # Python backend API
├── deployment/        # Deployment configurations
│   ├── k8s/          # Kubernetes manifests
│   └── docker/       # Docker configurations
├── config/           # Application configurations
├── monitoring/       # Monitoring setup (Grafana, Prometheus)
├── scripts/         # Utility scripts
└── data/            # Application data
    ├── logs/        # Log files
    └── models/      # ML models
```

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- Docker 20.10 or higher
- Docker Compose 2.0 or higher

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cernoid.git
   cd cernoid
   ```

2. Run the setup script:
   ```bash
   python scripts/setup.py
   ```
   This will:
   - Check prerequisites
   - Set up Python virtual environment
   - Install Node.js dependencies
   - Build the frontend
   - Configure environment variables
   - Build Docker images

3. Start the application:
   ```bash
   docker-compose up
   ```

The application will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- Grafana: http://localhost:3001

## Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Backend Development

```bash
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
cd backend
python -m uvicorn main:app --reload
```

## Testing

### Frontend Tests

```bash
cd frontend
npm test
```

### Backend Tests

```bash
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pytest
```

## Deployment

### Docker Deployment

The application is containerized and can be deployed using Docker Compose:

```bash
docker-compose -f deployment/docker-compose.yml up -d
```

### Kubernetes Deployment

1. Apply base configuration:
   ```bash
   kubectl apply -k deployment/k8s/base
   ```

2. Apply environment-specific overlay:
   ```bash
   kubectl apply -k deployment/k8s/overlays/production
   ```

## Monitoring

The application includes comprehensive monitoring with Grafana and Prometheus:

- Grafana dashboards for system metrics
- Prometheus for metrics collection
- Alert manager for notifications
- Loki for log aggregation

Access Grafana at http://localhost:3001 (default credentials: admin/admin)

## Security

- All endpoints are secured with JWT authentication
- Environment variables for sensitive data
- Rate limiting on API endpoints
- Input validation and sanitization
- Regular security updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
