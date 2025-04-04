# CernoID Security System

A comprehensive security and surveillance system with facial recognition, real-time monitoring, and advanced analytics.

## Features
- Face Recognition and Identity Management
- Access Control and Zone Management
- Real-time Monitoring and Alerts
- Comprehensive Logging and Analytics
- Scalable Architecture with Kubernetes Support
- Secure Secrets Management with HashiCorp Vault
- Automated Testing and CI/CD Pipeline
- Resource-Optimized Docker Images

## Project Structure

```
.
├── frontend/           # React frontend application
├── backend/           # Python backend API
├── deployment/        # Deployment configurations
│   ├── k8s/          # Kubernetes manifests
│   ├── docker/       # Docker configurations
│   └── vault/        # Vault configurations
├── config/           # Application configurations
├── monitoring/       # Monitoring setup (Grafana, Prometheus)
├── scripts/         # Utility scripts
│   ├── setup_dev.sh    # Development environment setup
│   ├── setup_vault.sh  # Vault initialization
│   └── run_tests.sh    # Automated testing
└── data/            # Application data
    ├── logs/        # Log files
    └── models/      # ML models
```

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker 20.10 or higher
- Docker Compose 2.0 or higher
- Poetry 1.6.1 or higher
- Git

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cernoid.git
   cd cernoid
   ```

2. Run the setup script:
   ```bash
   ./scripts/setup_dev.sh
   ```
   This will:
   - Check prerequisites
   - Set up Python virtual environment with Poetry
   - Install Node.js dependencies
   - Configure Vault for secrets management
   - Set up pre-commit hooks
   - Create necessary directories

3. Start the application:
   ```bash
   docker-compose up -d
   ```

The application will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Documentation: http://localhost:8000/api/v1/docs
- Vault UI: http://localhost:8200

## Development

For detailed development instructions, see [Development Setup Guide](docs/development_setup.md).

### Code Quality

1. Run code formatting:
   ```bash
   # Backend
   cd backend
   poetry run black .
   poetry run isort .
   
   # Frontend
   cd frontend
   npm run format
   ```

2. Run linting:
   ```bash
   # Backend
   cd backend
   poetry run flake8
   poetry run mypy src
   
   # Frontend
   cd frontend
   npm run lint
   ```

### Testing

Run all tests:
```bash
./scripts/run_tests.sh --all
```

Or run specific test suites:
```bash
./scripts/run_tests.sh --backend    # Run backend tests
./scripts/run_tests.sh --frontend   # Run frontend tests
./scripts/run_tests.sh --integration # Run integration tests
./scripts/run_tests.sh --security   # Run security tests
```

## Security

1. Secrets Management:
   - All sensitive data is managed through HashiCorp Vault
   - No secrets are stored in version control
   - Service-specific access policies
   - Automated secret rotation

2. Container Security:
   - Non-root container execution
   - Resource limits and quotas
   - Regular security scanning
   - Minimal base images

3. Code Security:
   - Automated dependency scanning
   - OWASP compliance checks
   - Regular security audits
   - Input validation and sanitization

## Monitoring

1. Application Metrics:
   - CPU and memory usage
   - Request rates and latencies
   - Error rates and types
   - Custom business metrics

2. Infrastructure Metrics:
   - Container health
   - Resource utilization
   - Network traffic
   - Storage usage

3. Alerting:
   - Configurable thresholds
   - Multiple notification channels
   - Alert aggregation
   - Incident management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Environment Management

### Environment Variables

The project uses environment variables for configuration. See the following files for examples:
- `frontend/.env.example` - Frontend configuration
- `backend/.env.example` - Backend configuration
- `.env.example` - Root configuration

### Environment Management Script

A utility script is provided to manage environment variables:

```bash
# Initialize environment files
python scripts/manage_env.py --init

# Validate environment variables
python scripts/manage_env.py --validate

# Encrypt sensitive variables
python scripts/manage_env.py --encrypt

# Decrypt sensitive variables
python scripts/manage_env.py --decrypt

# Export environment variables
python scripts/manage_env.py --export --env production

# Import environment variables
python scripts/manage_env.py --import config/env/production_env.json
```

### Secrets Management

Sensitive environment variables are automatically encrypted using Fernet symmetric encryption:
- Database passwords
- Redis passwords
- JWT secrets
- API keys
- SMTP passwords
- Grafana admin password

The encryption key is stored in `.secrets.key` (do not commit this file).

### CI/CD Validation

Environment variables are validated in the CI/CD pipeline:
- Required variables are present
- Variables have correct types and formats
- No sensitive data is exposed in code
- Secrets management is working correctly

### Development vs Production

Use different environment files for development and production:
- Development: `.env`
- Production: `.env.production`

Never commit actual `.env` files to version control.

## Setup Instructions

1. Copy the example environment files:
   ```bash
   cp frontend/.env.example frontend/.env
   cp backend/.env.example backend/.env
   cp .env.example .env
   ```

2. Update the environment variables with your values

3. Start the application:
   ```bash
   docker-compose up -d
   ```

## Security Notes

- Never commit `.env` files to version control
- Use strong, unique passwords for all services
- In production, use secure secrets and enable SSL/TLS
- Regularly rotate secrets and passwords
- Use different credentials for development and production environments
