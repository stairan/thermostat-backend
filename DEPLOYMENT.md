can i# Thermostat Backend Deployment Guide

This guide explains how to deploy the Thermostat Backend API using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Home Assistant instance accessible from your home server

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository to your home server
git clone <your-repo-url> thermostat-backend
cd thermostat-backend

# Create environment file
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your settings:

```bash
HOME_ASSISTANT_URL=http://192.168.50.248:8123
HOME_ASSISTANT_TOKEN=your_long_lived_access_token_here
```

**Getting a Home Assistant Token:**
1. In Home Assistant: Profile → Long-Lived Access Tokens
2. Click "Create Token"
3. Copy the token to your `.env` file

### 3. Create Log Directory

```bash
mkdir -p logs
chmod 755 logs
```

**Note**: This setup uses your existing database at `/home/dietpi/Python/thermostat/data.db`

### 4. Deploy with Docker Compose

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

## Service Details

### Container Configuration
- **Image**: Built from local Dockerfile
- **Port**: 8000 (mapped to host:8000)
- **Restart Policy**: unless-stopped
- **Health Check**: Every 30 seconds

### Data Persistence
- **Database**: Uses existing SQLite at `/home/dietpi/Python/thermostat/data.db`
- **Logs**: Application logs in `./logs/` (if configured)

### API Endpoints
- **Health Check**: `http://your-server:8000/health`
- **Dashboard**: `http://your-server:8000/api/v1/dashboard`
- **API Docs**: `http://your-server:8000/docs`

## Management Commands

### Start/Stop Services
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

### View Logs
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs thermostat-backend
```

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Database Management
```bash
# Access SQLite database
docker-compose exec thermostat-backend sqlite3 /external/data.db

# Backup database (from host)
cp /home/dietpi/Python/thermostat/data.db /home/dietpi/Python/thermostat/data.db.backup.$(date +%Y%m%d)
```

## Monitoring

### Health Checks
The container includes built-in health checks:
```bash
# Check container health
docker-compose ps
docker inspect thermostat-backend | grep Health -A 10
```

### Application Metrics
- **Polling Status**: Check logs for "Updated X sensor readings"
- **API Response**: Test `curl http://localhost:8000/health`
- **Data Collection**: Monitor dashboard endpoint for fresh timestamps

## Troubleshooting

### Common Issues

**1. Container won't start**
```bash
# Check logs
docker-compose logs thermostat-backend

# Check if port is in use
sudo netstat -tlnp | grep :8000
```

**2. Home Assistant connection fails**
```bash
# Test Home Assistant connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://192.168.50.248:8123/api/states

# Check if token is set correctly
docker-compose exec thermostat-backend env | grep HOME_ASSISTANT
```

**3. Database permission issues**
```bash
# Fix permissions
sudo chown -R 1000:1000 data logs
chmod 755 data logs
```

### Log Levels
To increase logging, modify the Docker Compose environment:
```yaml
environment:
  - LOG_LEVEL=DEBUG
```

## Security Considerations

- **Network**: Container runs on bridge network for isolation
- **Secrets**: Store Home Assistant token in `.env` file (not in git)
- **Database**: SQLite file permissions set to container user only
- **Updates**: Regularly update base Python image for security patches

## Backup Strategy

```bash
#!/bin/bash
# backup.sh - Run this script daily via cron

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/path/to/backups"

# Backup database
cp data/thermostat.db "$BACKUP_DIR/thermostat_$DATE.db"

# Keep only last 30 days
find "$BACKUP_DIR" -name "thermostat_*.db" -mtime +30 -delete
```

## Production Recommendations

1. **Reverse Proxy**: Use nginx/traefik for SSL termination
2. **Monitoring**: Add Prometheus metrics endpoint
3. **Logging**: Configure log rotation and centralized logging
4. **Backup**: Automated daily database backups
5. **Updates**: Set up automated security updates

## Support

- **Logs**: Check `docker-compose logs -f` for real-time debugging
- **API Docs**: Visit `http://your-server:8000/docs` for interactive API documentation
- **Health Status**: Monitor `http://your-server:8000/health` endpoint