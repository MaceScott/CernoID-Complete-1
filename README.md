# CernoID Complete

A secure identity verification system with face recognition capabilities.

## System Requirements

- Docker and Docker Compose
- At least 4GB of RAM
- 20GB of free disk space

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cernoid-complete.git
cd cernoid-complete
```

2. Create a `.env` file with your configuration:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start the services:
```bash
docker compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin Dashboard: http://localhost:3000/dashboard

Default admin credentials:
- Email: admin@cernoid.com
- Password: admin123

## Update Procedures

### Automatic Updates

The system includes an automated update process that ensures zero downtime and data safety:

1. Create a backup before updating:
```bash
./backup.sh
```

2. Run the update script:
```bash
./update.sh
```

The update script will:
- Pull the latest images
- Update services one at a time
- Verify service health
- Clean up old images

### Manual Updates

If you need to update specific services:

1. Pull the latest images:
```bash
docker compose pull [service_name]
```

2. Update the service:
```bash
docker compose up -d --no-deps [service_name]
```

## Backup and Restore

### Creating Backups

To create a complete backup of the system:

```bash
./backup.sh
```

This will create a timestamped backup archive containing:
- Database dump
- Redis data
- Configuration files
- Initialization scripts

### Restoring from Backup

To restore from a backup:

```bash
./restore.sh path/to/backup.tar.gz
```

The restore process will:
1. Stop all services
2. Restore configuration files
3. Restore database and Redis data
4. Restart services

## Data Persistence

The system uses Docker volumes for data persistence:
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis data files
- `frontend_data`: Frontend build cache
- `backend_data`: Backend data files
- `backend_logs`: Backend log files

## Monitoring and Logs

View service logs:
```bash
docker compose logs -f [service_name]
```

Monitor service health:
```bash
docker compose ps
```

## Security Considerations

1. Change default passwords in `.env`
2. Enable HTTPS in production
3. Regularly update dependencies
4. Monitor audit logs
5. Implement rate limiting

## Troubleshooting

1. Check service logs:
```bash
docker compose logs [service_name]
```

2. Verify service health:
```bash
docker compose ps
```

3. Restart services:
```bash
docker compose restart [service_name]
```

4. Reset to clean state:
```bash
docker compose down -v
./restore.sh path/to/backup.tar.gz
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
