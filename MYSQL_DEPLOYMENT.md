# MySQL Deployment Guide for JarvisTrade

This guide provides comprehensive instructions for deploying JarvisTrade with MySQL in production.

## 🚀 Quick Start

### 1. Prerequisites

- **Server**: Ubuntu 20.04+ or CentOS 8+ (recommended)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 50GB, SSD recommended
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd jarvistrade/backend

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.mysql.production .env

# Edit environment variables
nano .env
```

### 3. Environment Configuration

Update your `.env` file with production values:

```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://jarvistrade_user:your_secure_password@localhost:3306/jarvistrade_prod

# MySQL Configuration
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_DATABASE=jarvistrade_prod
MYSQL_USER=jarvistrade_user
MYSQL_PASSWORD=your_secure_password

# Security
SECRET_KEY=your-super-secret-key-here
PAYSTACK_SECRET_KEY=your-paystack-secret-key
```

## 🐳 Docker Deployment

### 1. Start MySQL Services

```bash
# Start MySQL and Redis
docker-compose -f docker-compose.mysql.yml up -d mysql redis

# Wait for services to be healthy
docker-compose -f docker-compose.mysql.yml ps
```

### 2. Run Migration

```bash
# Create tables
python migrate_to_mysql.py --create-tables

# Migrate data (if migrating from SQLite)
python migrate_to_mysql.py --migrate-data

# Verify migration
python migrate_to_mysql.py --verify
```

### 3. Start Application

```bash
# Start all services
docker-compose -f docker-compose.mysql.yml up -d

# Check status
docker-compose -f docker-compose.mysql.yml ps
```

## 🗄️ Manual MySQL Setup

### 1. Install MySQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server mysql-client

# CentOS/RHEL
sudo yum install mysql-server mysql-client
```

### 2. Secure MySQL

```bash
# Run security script
sudo mysql_secure_installation

# Access MySQL
sudo mysql -u root -p
```

### 3. Create Database and User

```sql
-- Create database
CREATE DATABASE jarvistrade_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'jarvistrade_user'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON jarvistrade_prod.* TO 'jarvistrade_user'@'localhost';
GRANT ALL PRIVILEGES ON jarvistrade_test.* TO 'jarvistrade_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;
```

### 4. Configure MySQL

Edit `/etc/mysql/mysql.conf.d/mysqld.cnf`:

```ini
[mysqld]
# Character set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# SQL mode
sql_mode = STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO

# InnoDB settings
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# Connection settings
max_connections = 200
query_cache_size = 64M
query_cache_type = 1

# Performance settings
tmp_table_size = 64M
max_heap_table_size = 64M
table_open_cache = 2000
thread_cache_size = 16

# Binary logging
log-bin = /var/log/mysql/mysql-bin
binlog_format = ROW
expire_logs_days = 7
max_binlog_size = 100M
```

### 5. Restart MySQL

```bash
sudo systemctl restart mysql
sudo systemctl enable mysql
```

## 🔧 Application Configuration

### 1. Update Database URL

Ensure your application uses the MySQL connection:

```python
# In database.py or environment
DATABASE_URL = "mysql+pymysql://jarvistrade_user:password@localhost:3306/jarvistrade_prod"
```

### 2. Test Connection

```bash
# Test database connection
python -c "
from database import check_database_health
print('Database healthy:', check_database_health())
"
```

### 3. Initialize Tables

```bash
# Create tables
python -c "
from database import init_database
init_database()
"
```

## 📊 Performance Optimization

### 1. MySQL Configuration

```ini
# Buffer pool (adjust based on available RAM)
innodb_buffer_pool_size = 2G  # 70-80% of available RAM

# Log files
innodb_log_file_size = 512M
innodb_log_files_in_group = 2

# I/O settings
innodb_io_capacity = 200
innodb_io_capacity_max = 400
innodb_read_io_threads = 4
innodb_write_io_threads = 4

# Connection pooling
max_connections = 300
thread_cache_size = 32
```

### 2. Application-Level Optimization

```python
# Connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Query optimization
session = SessionLocal()
session.execute(text("SET SESSION sql_mode = 'STRICT_TRANS_TABLES'"))
```

### 3. Indexing Strategy

```sql
-- Add composite indexes for common queries
CREATE INDEX idx_transaction_user_status ON transactions(user_id, status);
CREATE INDEX idx_product_category_active ON products(category, is_active);
CREATE INDEX idx_order_transaction_product ON order_items(transaction_id, product_id);

-- Add covering indexes for frequently accessed columns
CREATE INDEX idx_user_email_name ON users(email, name);
CREATE INDEX idx_product_name_category ON products(name, category);
```

## 🔒 Security Configuration

### 1. MySQL Security

```sql
-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';

-- Remove test database
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';

-- Restrict root access
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

-- Apply changes
FLUSH PRIVILEGES;
```

### 2. Network Security

```bash
# Configure firewall
sudo ufw allow 3306/tcp
sudo ufw allow 6379/tcp
sudo ufw allow 8000/tcp

# Bind MySQL to localhost only
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# Add: bind-address = 127.0.0.1
```

### 3. SSL Configuration

```sql
-- Enable SSL
ALTER USER 'jarvistrade_user'@'localhost' REQUIRE SSL;

-- Verify SSL status
SHOW VARIABLES LIKE 'have_ssl';
SHOW VARIABLES LIKE 'ssl_version';
```

## 📈 Monitoring and Maintenance

### 1. Health Checks

```bash
# Database health
mysql -u jarvistrade_user -p -e "SELECT 1"

# Application health
curl http://localhost:8000/health

# Redis health
redis-cli ping
```

### 2. Performance Monitoring

```sql
-- Check slow queries
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- Monitor connections
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- Check buffer pool usage
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_%';
```

### 3. Backup Strategy

```bash
# Create backup script
cat > backup_mysql.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mysql"
DB_NAME="jarvistrade_prod"

mkdir -p $BACKUP_DIR
mysqldump -u jarvistrade_user -p $DB_NAME > $BACKUP_DIR/${DB_NAME}_${DATE}.sql
gzip $BACKUP_DIR/${DB_NAME}_${DATE}.sql

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_mysql.sh

# Add to crontab
echo "0 2 * * * /path/to/backup_mysql.sh" | crontab -
```

## 🚨 Troubleshooting

### 1. Connection Issues

```bash
# Check MySQL status
sudo systemctl status mysql

# Check MySQL logs
sudo tail -f /var/log/mysql/error.log

# Test connection
mysql -u jarvistrade_user -p -h localhost
```

### 2. Performance Issues

```sql
-- Check slow queries
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- Check process list
SHOW PROCESSLIST;

-- Check table status
SHOW TABLE STATUS;
```

### 3. Common Errors

```bash
# "Access denied" error
sudo mysql -u root -p
GRANT ALL PRIVILEGES ON jarvistrade_prod.* TO 'jarvistrade_user'@'localhost';

# "Can't connect to MySQL server"
sudo systemctl restart mysql
sudo netstat -tlnp | grep 3306

# "Table doesn't exist"
python migrate_to_mysql.py --create-tables
```

## 📚 Additional Resources

- [MySQL 8.0 Reference Manual](https://dev.mysql.com/doc/refman/8.0/en/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs mysql`
2. Verify environment variables
3. Test database connectivity
4. Check MySQL error logs
5. Review this documentation

For production deployments, consider:

- Setting up monitoring (Prometheus, Grafana)
- Implementing automated backups
- Configuring alerting
- Setting up replication for high availability
- Regular security updates and patches
