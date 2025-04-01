# Development Setup Guide

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker 20.10 or higher
- Docker Compose 2.0 or higher
- Poetry 1.6.1 or higher
- Git

## Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cernoid.git
   cd cernoid
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Set up backend development environment:
   ```bash
   cd backend
   poetry install
   poetry shell
   ```

4. Set up frontend development environment:
   ```bash
   cd frontend
   npm install
   ```

5. Set up HashiCorp Vault for secrets management:
   ```bash
   # Start Vault in development mode
   docker-compose up -d vault
   
   # Initialize Vault and save the root token
   docker-compose exec vault vault operator init
   
   # Unseal Vault (run this 3 times with different unseal keys)
   docker-compose exec vault vault operator unseal
   
   # Login to Vault
   docker-compose exec vault vault login
   
   # Enable secrets engine
   docker-compose exec vault vault secrets enable -path=cernoid kv-v2
   
   # Store secrets
   docker-compose exec vault vault kv put cernoid/database \
     url="postgresql://postgres:postgres@db:5432/cernoid" \
     username="postgres" \
     password="postgres"
   
   docker-compose exec vault vault kv put cernoid/redis \
     url="redis://redis:6379" \
     host="redis" \
     port="6379"
   
   docker-compose exec vault vault kv put cernoid/jwt \
     secret="your-secure-jwt-secret"
   ```

## Development Workflow

### Running Services Locally

1. Start the development environment:
   ```bash
   docker-compose up -d db redis vault
   ```

2. Run backend development server:
   ```bash
   cd backend
   poetry run uvicorn src.main:app --reload
   ```

3. Run frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

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

3. Run tests:
   ```bash
   # Backend
   cd backend
   poetry run pytest
   
   # Frontend
   cd frontend
   npm test
   ```

### Working with Docker

1. Build images:
   ```bash
   docker-compose build
   ```

2. Run all services:
   ```bash
   docker-compose up -d
   ```

3. View logs:
   ```bash
   docker-compose logs -f [service_name]
   ```

### Database Management

1. Create a new migration:
   ```bash
   cd backend
   poetry run alembic revision -m "description"
   ```

2. Apply migrations:
   ```bash
   poetry run alembic upgrade head
   ```

3. Rollback migration:
   ```bash
   poetry run alembic downgrade -1
   ```

## Monitoring and Debugging

1. Access services:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/v1/docs
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001
   - Vault UI: http://localhost:8200

2. View metrics:
   - Application metrics: http://localhost:8000/metrics
   - Node metrics: http://localhost:9100/metrics

3. Check service health:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:3000/api/health
   ```

## Troubleshooting

### Common Issues

1. Database connection issues:
   - Check if PostgreSQL is running: `docker-compose ps db`
   - Verify connection settings in Vault
   - Check database logs: `docker-compose logs db`

2. Redis connection issues:
   - Check if Redis is running: `docker-compose ps redis`
   - Verify connection settings in Vault
   - Check Redis logs: `docker-compose logs redis`

3. Vault issues:
   - Ensure Vault is unsealed: `docker-compose exec vault vault status`
   - Check if secrets are accessible: `docker-compose exec vault vault kv get cernoid/database`
   - Verify service token permissions

### Performance Optimization

1. Docker volume performance:
   - Use tmpfs for temporary data
   - Configure volume driver options for better I/O
   - Monitor volume usage with `docker system df -v`

2. Resource monitoring:
   - Use `docker stats` to monitor container resource usage
   - Check Grafana dashboards for detailed metrics
   - Monitor system resources with `top` or `htop`

## Security Best Practices

1. Secrets management:
   - Never commit secrets to version control
   - Use Vault for all sensitive data
   - Rotate secrets regularly
   - Use least privilege access

2. Container security:
   - Keep base images updated
   - Run containers as non-root
   - Use security scanning tools
   - Follow Docker security best practices

3. Code security:
   - Use dependency scanning
   - Follow OWASP guidelines
   - Implement proper input validation
   - Use secure coding practices 