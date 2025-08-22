# Jarvistrade Production Deployment Guide

This guide covers the complete production deployment setup for the Jarvistrade application, including database migration from SQLite to PostgreSQL, security enhancements, monitoring, and deployment automation.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL database (or use the provided Docker setup)
- Redis for caching and rate limiting
- SSL certificates for HTTPS
- Domain name configured

### 1. Environment Setup

Copy the environment template and configure it:

```bash
cp env.example .env
```

Edit `.env` with your production values:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/jarvistrade_prod
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_secure_redis_password

# Security Configuration
SECRET_KEY=your-super-secure-secret-key-at-least-32-characters
ENVIRONMENT=production
DEBUG=False

# Email Configuration
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@yourdomain.com

# Payment Configuration
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_PUBLIC_KEY=your-paystack-public-key
```

### 2. Database Migration

If migrating from SQLite to PostgreSQL:

```bash
# Create PostgreSQL database
createdb jarvistrade_prod

# Run the migration script
./scripts/migrate.sh
```

### 3. Deploy with Docker Compose

```bash
# Deploy all services
./scripts/deploy.sh

# Or manually
docker-compose up -d
```

## 🏗️ Architecture Overview

### Services

- **PostgreSQL**: Primary database (replaces SQLite)
- **Redis**: Caching and rate limiting
- **FastAPI App**: Main application with Gunicorn
- **Nginx**: Reverse proxy with SSL termination
- **Celery**: Background task processing
- **Celery Beat**: Scheduled task management

### Security Features

- Rate limiting (per IP and per endpoint)
- Security headers (HSTS, XSS protection, etc.)
- Trusted host validation
- Request logging and monitoring
- File upload validation
- SSL/TLS encryption

## 📊 Monitoring & Health Checks

### Health Endpoints

- `/health` - Basic health status
- `/health/detailed` - Comprehensive service health
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Kubernetes liveness probe
- `/metrics` - System and application metrics

### Logging

Logs are stored in the `./logs/` directory:

- `app.log` - Application logs
- `access.log` - HTTP access logs
- `error.log` - Error logs
- `deploy.log` - Deployment logs
- `backup.log` - Backup logs

## 🔧 Configuration

### Database Configuration

The application automatically detects the database type and configures connection pooling:

- **PostgreSQL**: 20 workers, SSL in production
- **MySQL**: 20 workers, UTF8MB4 charset
- **SQLite**: 10 workers (development only)

### Rate Limiting

- **API endpoints**: 100 requests per minute
- **Login endpoint**: 5 requests per minute
- **Burst allowance**: 20 requests for API, 5 for login

### File Upload Limits

- **Maximum file size**: 10MB
- **Allowed extensions**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.pdf`, `.txt`, `.zip`, `.ex5`
- **Upload directory**: `./uploads/`

## 🚀 Deployment

### Automated Deployment

```bash
# Full deployment with health checks
./scripts/deploy.sh

# Deploy specific environment
./scripts/deploy.sh staging
```

### Manual Deployment

```bash
# Build and start services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

## 💾 Backup & Recovery

### Automated Backups

```bash
# Create backup
./scripts/backup.sh

# Set up cron job for daily backups
0 2 * * * /path/to/jarvistrade/backend/scripts/backup.sh
```

### Backup Contents

- Database dump (PostgreSQL)
- Upload files
- Digital products
- Licenses
- Configuration files
- Logs

### Recovery

```bash
# Restore from backup
docker-compose exec postgres psql -U jarvistrade_user -d jarvistrade_prod < backup_file.sql

# Restore files
tar -xzf backup_file.tar.gz
```

## 🔄 Database Migrations

### Running Migrations

```bash
# Safe migration with backup
./scripts/migrate.sh

# Manual migration
docker-compose exec app alembic upgrade head
```

### Migration Safety

- Automatic backups before migration
- Health checks after migration
- Rollback capability
- Verification of all endpoints

## 🛡️ Security

### SSL/TLS Configuration

1. Place your SSL certificates in `./nginx/ssl/`
2. Update `nginx.conf` with your domain
3. Ensure certificates are valid and not expired

### Security Headers

- `Strict-Transport-Security`: HTTPS enforcement
- `X-Frame-Options`: Clickjacking protection
- `X-Content-Type-Options`: MIME type sniffing protection
- `X-XSS-Protection`: XSS protection
- `Referrer-Policy`: Referrer information control

### Rate Limiting

- Per-IP rate limiting
- Endpoint-specific limits
- Burst allowance for legitimate traffic
- Redis-based storage for scalability

## 📈 Performance

### Optimization Features

- Connection pooling
- Gzip compression
- Static file caching
- Database query optimization
- Worker process management

### Scaling

- Horizontal scaling with multiple app instances
- Load balancing with Nginx
- Database connection pooling
- Redis for session storage

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check PostgreSQL status
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U jarvistrade_user
```

#### Application Not Starting

```bash
# Check application logs
docker-compose logs app

# Check health endpoint
curl http://localhost:8000/health

# Verify environment variables
docker-compose exec app env | grep DATABASE_URL
```

#### Rate Limiting Issues

```bash
# Check Redis status
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Check rate limit counters
docker-compose exec redis redis-cli keys "rate_limit:*"
```

### Log Analysis

```bash
# View real-time logs
docker-compose logs -f

# Search for errors
docker-compose logs app | grep ERROR

# Check access logs
tail -f logs/access.log
```

## 🔧 Maintenance

### Regular Tasks

1. **Daily**: Check health endpoints
2. **Weekly**: Review logs and metrics
3. **Monthly**: Update dependencies
4. **Quarterly**: Security audit and SSL renewal

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Run migrations if needed
./scripts/migrate.sh
```

### Monitoring

- Application health checks
- Database performance monitoring
- System resource monitoring
- Error rate tracking
- Response time monitoring

## 🌐 Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrated and tested
- [ ] Health checks passing
- [ ] Rate limiting configured
- [ ] Backup system tested
- [ ] Monitoring configured
- [ ] Security headers verified
- [ ] File permissions set correctly
- [ ] Log rotation configured
- [ ] Error handling tested
- [ ] Performance benchmarks completed

## 📞 Support

For production deployment issues:

1. Check the logs in `./logs/`
2. Verify environment configuration
3. Test health endpoints
4. Review Docker container status
5. Check system resources

## 🔗 Additional Resources

- [FastAPI Production Documentation](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/current/admin.html)
- [Docker Production Guidelines](https://docs.docker.com/engine/security/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [Redis Production Setup](https://redis.io/topics/admin)
