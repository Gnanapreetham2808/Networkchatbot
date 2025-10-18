# PostgreSQL Migration Guide

## Overview

This guide helps you migrate from SQLite (development) to PostgreSQL (production) for the Network Chatbot backend.

## Why PostgreSQL?

- ✅ **Production-ready**: Better concurrency, ACID compliance
- ✅ **Scalability**: Handles high loads and large datasets
- ✅ **Advanced features**: JSON fields, full-text search, connections pooling
- ✅ **Reliability**: Better crash recovery and data integrity
- ✅ **Multi-user**: Safe concurrent access from multiple workers

## Prerequisites

### Windows

**Option 1: Install PostgreSQL directly**
```powershell
# Download from https://www.postgresql.org/download/windows/
# Or use Chocolatey
choco install postgresql14

# Verify installation
psql --version
```

**Option 2: Use Docker** (Recommended)
```powershell
# Install Docker Desktop for Windows
# Then run PostgreSQL container
docker run --name netops-postgres -e POSTGRES_PASSWORD=yourpassword -e POSTGRES_DB=netops_db -p 5432:5432 -d postgres:15
```

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify
psql --version
```

### macOS

```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15

# Verify
psql --version
```

---

## Step-by-Step Migration

### 1. Install Python Dependencies

```powershell
# Activate your virtual environment
cd Backend
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install PostgreSQL support
pip install psycopg2-binary==2.9.9 dj-database-url==2.2.0

# Or update from requirements
pip install -r requirements.txt
```

### 2. Create PostgreSQL Database

**Option A: Using Docker** (Easiest for development)

```powershell
# Run PostgreSQL container
docker run --name netops-postgres `
  -e POSTGRES_USER=netops_user `
  -e POSTGRES_PASSWORD=netops_pass `
  -e POSTGRES_DB=netops_db `
  -p 5432:5432 `
  -d postgres:15

# Verify it's running
docker ps

# Connect to it (optional)
docker exec -it netops-postgres psql -U netops_user -d netops_db
```

**Option B: Using installed PostgreSQL**

Windows PowerShell:
```powershell
# Switch to postgres user (if on Linux/Mac)
# sudo -u postgres psql

# Or on Windows, open SQL Shell (psql) and run:
psql -U postgres

# In psql prompt:
CREATE DATABASE netops_db;
CREATE USER netops_user WITH PASSWORD 'secure_password_here';
ALTER ROLE netops_user SET client_encoding TO 'utf8';
ALTER ROLE netops_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE netops_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE netops_db TO netops_user;

# PostgreSQL 15+ requires additional permissions
\c netops_db
GRANT ALL ON SCHEMA public TO netops_user;

# Exit
\q
```

### 3. Update Environment Configuration

Edit `Backend/.env`:

```env
# Database Configuration
DATABASE_URL=postgresql://netops_user:netops_pass@localhost:5432/netops_db

# Optional: PostgreSQL tuning
DB_CONN_MAX_AGE=600
DB_CONNECT_TIMEOUT=10
DB_STATEMENT_TIMEOUT=30000
```

**Connection String Format:**
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

Examples:
```env
# Local development
DATABASE_URL=postgresql://netops_user:netops_pass@localhost:5432/netops_db

# Docker container
DATABASE_URL=postgresql://netops_user:netops_pass@localhost:5432/netops_db

# Remote server
DATABASE_URL=postgresql://user:pass@db.example.com:5432/netops_prod

# With special characters in password (URL-encode them)
DATABASE_URL=postgresql://user:p%40ssw0rd@localhost:5432/netops_db
```

### 4. Run Migrations

```powershell
cd Backend\netops_backend

# Verify database connection
python manage.py dbshell
# Type \q to exit

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 5. Export Data from SQLite (Optional)

If you have existing data in SQLite to preserve:

```powershell
# Export from SQLite
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > data_backup.json

# Switch to PostgreSQL (update .env)
# Run migrations
python manage.py migrate

# Import to PostgreSQL
python manage.py loaddata data_backup.json
```

### 6. Verify Migration

```powershell
# Test database connection
python manage.py check --database default

# Run development server
python manage.py runserver

# Check logs for any database errors
cat ..\logs\netops.log
```

---

## Configuration Details

### Environment Variables

```env
# Required
DATABASE_URL=postgresql://user:password@host:port/dbname

# Optional Performance Tuning
DB_CONN_MAX_AGE=600              # Keep connections alive (seconds)
DB_CONNECT_TIMEOUT=10            # Connection timeout (seconds)
DB_STATEMENT_TIMEOUT=30000       # Query timeout (milliseconds)
```

### Production Settings

For production deployments:

```env
# Production database
DATABASE_URL=postgresql://netops_prod:strong_password@db.internal:5432/netops_production

# Increase connection pool
DB_CONN_MAX_AGE=600

# Stricter timeouts
DB_CONNECT_TIMEOUT=5
DB_STATEMENT_TIMEOUT=10000

# Enable Django production settings
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

---

## Docker Compose Setup

For a complete development environment with PostgreSQL:

Create `Backend/docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: netops-postgres
    environment:
      POSTGRES_DB: netops_db
      POSTGRES_USER: netops_user
      POSTGRES_PASSWORD: netops_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U netops_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: netops-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Start services:
```powershell
cd Backend
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres

# Stop services
docker-compose down
```

---

## Database Management

### Backup Database

```powershell
# Using pg_dump
pg_dump -U netops_user -h localhost -d netops_db -F c -f backup_$(date +%Y%m%d).dump

# Or with Docker
docker exec -t netops-postgres pg_dump -U netops_user netops_db > backup.sql
```

### Restore Database

```powershell
# Using pg_restore
pg_restore -U netops_user -h localhost -d netops_db backup.dump

# Or with Docker
docker exec -i netops-postgres psql -U netops_user netops_db < backup.sql
```

### Database Console

```powershell
# Direct connection
psql -U netops_user -h localhost -d netops_db

# Via Django
python manage.py dbshell

# Via Docker
docker exec -it netops-postgres psql -U netops_user -d netops_db
```

### Useful SQL Commands

```sql
-- List all tables
\dt

-- Describe table
\d chatbot_conversation

-- Check database size
SELECT pg_size_pretty(pg_database_size('netops_db'));

-- List active connections
SELECT * FROM pg_stat_activity WHERE datname = 'netops_db';

-- Kill idle connections (if needed)
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE datname = 'netops_db' AND state = 'idle' AND state_change < now() - interval '5 minutes';

-- Vacuum database (optimize)
VACUUM ANALYZE;
```

---

## Troubleshooting

### Issue: "Connection refused"

**Solution:**
```powershell
# Check PostgreSQL is running
# Windows Service:
Get-Service postgresql*

# Docker:
docker ps | Select-String postgres

# Test connection
psql -U netops_user -h localhost -d netops_db
```

### Issue: "FATAL: password authentication failed"

**Solution:**
1. Verify username/password in DATABASE_URL
2. Check PostgreSQL user exists:
   ```sql
   psql -U postgres
   \du
   ```
3. Reset password if needed:
   ```sql
   ALTER USER netops_user WITH PASSWORD 'new_password';
   ```

### Issue: "database does not exist"

**Solution:**
```sql
# Connect as superuser
psql -U postgres

# Create database
CREATE DATABASE netops_db OWNER netops_user;
```

### Issue: "peer authentication failed"

**Solution (Linux):**
Edit `/etc/postgresql/15/main/pg_hba.conf`:
```
# Change from:
local   all   all   peer

# To:
local   all   all   md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Issue: Port 5432 already in use

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :5432

# Kill process or change port
# In docker-compose.yml:
ports:
  - "5433:5432"  # External:Internal

# Update DATABASE_URL
DATABASE_URL=postgresql://user:pass@localhost:5433/netops_db
```

---

## Performance Tuning

### PostgreSQL Configuration

For production, tune PostgreSQL settings in `postgresql.conf`:

```ini
# Memory
shared_buffers = 256MB          # 25% of RAM
effective_cache_size = 1GB      # 50-75% of RAM
work_mem = 4MB
maintenance_work_mem = 64MB

# Connections
max_connections = 100

# Checkpoints
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Query planner
random_page_cost = 1.1          # For SSD
effective_io_concurrency = 200  # For SSD

# Logging
log_min_duration_statement = 1000  # Log slow queries (ms)
```

### Django Connection Pooling

For high-traffic production, consider using `django-db-gevent` or `pgbouncer`:

```env
# Increase connection lifetime
DB_CONN_MAX_AGE=3600  # 1 hour
```

### Indexes

Django automatically creates indexes for:
- Primary keys
- Foreign keys
- Fields with `db_index=True`

Monitor slow queries and add indexes as needed.

---

## Security Best Practices

1. **Strong passwords**: Use 20+ character random passwords
2. **Limit access**: Firewall PostgreSQL port (5432) to trusted IPs only
3. **SSL connections**: Use `sslmode=require` for remote connections
   ```env
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```
4. **Separate user roles**: Don't use superuser for application
5. **Regular backups**: Automate daily backups
6. **Update regularly**: Keep PostgreSQL and dependencies updated

---

## Switching Between SQLite and PostgreSQL

The system automatically detects the database type:

**Use SQLite** (development):
```env
# Leave DATABASE_URL empty or commented
# DATABASE_URL=
```

**Use PostgreSQL** (production):
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

Django will automatically use the correct engine based on the `DATABASE_URL` value.

---

## Production Deployment Checklist

- [ ] PostgreSQL server installed and secured
- [ ] Strong passwords set
- [ ] Firewall rules configured
- [ ] SSL/TLS enabled for connections
- [ ] Regular backups scheduled (daily recommended)
- [ ] Database monitored (disk space, connections, slow queries)
- [ ] Connection pooling configured
- [ ] DATABASE_URL set in production environment
- [ ] DJANGO_DEBUG=0 in production
- [ ] Migrations run successfully
- [ ] Test database connection
- [ ] Monitor logs for database errors

---

## Additional Resources

- [PostgreSQL Official Docs](https://www.postgresql.org/docs/)
- [Django Database Documentation](https://docs.djangoproject.com/en/stable/ref/databases/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)

---

## Quick Reference Commands

```powershell
# Install dependencies
pip install psycopg2-binary dj-database-url

# Create database
psql -U postgres -c "CREATE DATABASE netops_db"

# Run migrations
python manage.py migrate

# Backup
pg_dump -U netops_user netops_db > backup.sql

# Restore
psql -U netops_user netops_db < backup.sql

# Database shell
python manage.py dbshell

# Check connection
python manage.py check --database default
```

---

**Ready to migrate? Follow the steps above, and you'll have PostgreSQL running in minutes!** 🚀
