# Environment Variables

## Overview
The application uses environment variables for configuration. All required variables are validated at startup to ensure the application runs correctly.

## Setup

### Development Setup
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the values in `.env` with your development settings:
   - Database credentials
   - Redis configuration
   - JWT secrets
   - API keys
   - Other sensitive information

3. Run the setup script to validate your configuration:
   ```bash
   python scripts/setup_env.py
   ```

### Production Setup
1. Use HashiCorp Vault for secure secret management:
   ```bash
   ./scripts/setup_vault.sh
   ```

2. Configure the application to use Vault:
   - Set `VAULT_ADDR` to your Vault server address
   - Set `VAULT_TOKEN` to your application token
   - Set `VAULT_PATH` to your secrets path

## Required Variables

### Core Settings
- `ENVIRONMENT`: Application environment (development/production)
- `DEBUG`: Enable debug mode
- `BACKEND_HOST`: Host to bind the server
- `BACKEND_PORT`: Port to bind the server
- `BACKEND_WORKERS`: Number of worker processes

### Database
- `DATABASE_URL`: PostgreSQL connection URL
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `ALEMBIC_CONFIG`: Alembic configuration file
- `MIGRATION_DIR`: Directory containing migrations

### Redis
- `REDIS_URL`: Redis connection URL
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `REDIS_DB`: Redis database number

### Security
- `JWT_SECRET`: Secret for JWT token generation
- `JWT_EXPIRES_IN`: JWT token expiration time
- `JWT_REFRESH_EXPIRES_IN`: Refresh token expiration time
- `CORS_ORIGIN`: Allowed CORS origin
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
- `RATE_LIMIT_WINDOW`: Rate limit window in seconds
- `RATE_LIMIT_MAX_REQUESTS`: Maximum requests per window

### Face Recognition
- `ENABLE_FACE_RECOGNITION`: Enable face recognition features
- `FACE_RECOGNITION_MODEL`: Model to use for face recognition
- `FACE_RECOGNITION_MODEL_PATH`: Path to the model file
- `FACE_DETECTION_CONFIDENCE`: Minimum confidence for face detection
- `FACE_DETECTION_CASCADE_PATH`: Path to the cascade classifier
- `FACE_DETECTION_TORCH_MODEL_PATH`: Path to the PyTorch model

### Monitoring
- `ENABLE_METRICS`: Enable Prometheus metrics
- `ENABLE_TRACING`: Enable distributed tracing
- `PROMETHEUS_MULTIPROC_DIR`: Directory for Prometheus metrics
- `LOG_LEVEL`: Application log level
- `LOG_FORMAT`: Log format (json/text)

## Optional Variables

### Email
- `SMTP_HOST`: SMTP server host
- `SMTP_PORT`: SMTP server port
- `SMTP_USER`: SMTP username
- `SMTP_PASSWORD`: SMTP password
- `SMTP_FROM`: Sender email address

### Vault
- `VAULT_ADDR`: Vault server address
- `VAULT_TOKEN`: Vault authentication token
- `VAULT_PATH`: Path to secrets in Vault

## Validation
The application validates all required environment variables at startup. If any required variables are missing or invalid, the application will fail to start with a clear error message.

To validate your environment configuration:
```bash
python scripts/setup_env.py
```

## Security Notes
1. Never commit `.env` files to version control
2. Use different values for development and production
3. Use Vault or similar tools for production secrets
4. Regularly rotate secrets and API keys
5. Use strong passwords and keys
6. Restrict access to sensitive configuration

## Troubleshooting
If you encounter environment-related issues:

1. Check the validation output:
   ```bash
   python scripts/setup_env.py
   ```

2. Verify all required variables are set:
   ```bash
   python -c "from src.core.config.validate import validate_env; print(validate_env())"
   ```

3. Check the application logs for specific errors

4. Ensure all paths and URLs are correct for your environment 