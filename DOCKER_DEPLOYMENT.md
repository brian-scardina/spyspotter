# SpySpotter Docker & Kubernetes Deployment Guide

This guide covers the complete deployment options for SpySpotter (formerly PixelTracker) using Docker and Kubernetes.

## 🐳 Docker Deployment

### Multi-Stage Docker Images

SpySpotter supports multiple deployment variants through a multi-stage Dockerfile:

- **Core**: Basic tracking pixel detection (`core`)
- **ML**: Core + Machine Learning capabilities (`ml`)
- **Enterprise**: Full feature set with enterprise capabilities (`enterprise`)
- **Development**: All features + development tools (`development`)

### Building Images

```bash
# Build core image
docker build --target core -t spyspotter:core .

# Build ML image
docker build --target ml -t spyspotter:ml .

# Build enterprise image
docker build --target enterprise -t spyspotter:enterprise .

# Build development image
docker build --target development -t spyspotter:dev .
```

### Docker Compose Deployment

#### Quick Start

```bash
# Start core services
docker-compose --profile core up -d

# Start ML services
docker-compose --profile ml up -d

# Start enterprise services (all features)
docker-compose --profile enterprise up -d

# Development environment
docker-compose --profile dev up -d
```

#### Service Profiles

The docker-compose.yml supports various service profiles:

- `core`: Basic SpySpotter functionality
- `ml`: Core + Machine Learning services
- `enterprise`: Full enterprise stack
- `dev`/`development`: Development environment
- `all`: All services (use with caution)

#### Optional Infrastructure Services

```bash
# Database services
docker-compose --profile postgres up -d
docker-compose --profile mongodb up -d

# Monitoring services
docker-compose --profile monitoring up -d

# Search services
docker-compose --profile elasticsearch up -d
```

### Environment Configuration

SpySpotter uses a hierarchical configuration system with environment variable overrides:

#### Environment Variables

Set environment variables with the `PIXELTRACKER__` prefix:

```bash
# Set scanning parameters
export PIXELTRACKER__SCANNING__RATE_LIMIT_DELAY=1.5
export PIXELTRACKER__SCANNING__CONCURRENT_REQUESTS=20

# Set logging level
export PIXELTRACKER__LOGGING__LEVEL=DEBUG

# Configure enterprise features
export PIXELTRACKER__ENTERPRISE__ENABLED=true
export PIXELTRACKER__REDIS__HOST=redis
export PIXELTRACKER__REDIS__PORT=6379
```

#### Configuration Directory Structure

```
config.d/
├── base/
│   └── default.yaml          # Base configuration
├── development/
│   └── development.yaml      # Development overrides
├── production/
│   └── production.yaml       # Production overrides
├── enterprise/
│   └── enterprise.yaml       # Enterprise overrides
└── env_overrides.yaml        # Generated from env vars
```

#### Environment-Specific Configurations

```bash
# Set environment
export PIXELTRACKER_ENV=production

# Available environments: development, testing, staging, production, enterprise
```

### Health Checks

All Docker images include comprehensive health checks:

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View health check logs
docker inspect --format='{{json .State.Health}}' spyspotter-enterprise
```

### Volume Management

```bash
# Create named volumes for persistence
docker volume create spyspotter-data
docker volume create spyspotter-logs
docker volume create spyspotter-config

# Backup volumes
docker run --rm -v spyspotter-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/spyspotter-data-backup.tar.gz -C /data .
```

### Security Features

- **Non-root user**: All containers run as user `pixeltracker` (UID 1000)
- **Read-only root filesystem**: Enhanced security posture
- **Health checks**: Automatic monitoring and restart capabilities
- **Secret management**: Secure handling of sensitive configuration

## ☸️ Kubernetes Deployment

### Helm Chart Deployment

#### Prerequisites

```bash
# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add elastic https://helm.elastic.co
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

#### Basic Deployment

```bash
# Install with default values (enterprise configuration)
helm install spyspotter ./helm/pixeltracker

# Install specific variant
helm install spyspotter ./helm/pixeltracker \
  --set image.variant=core \
  --set environment=production
```

#### Environment-Specific Deployments

```bash
# Development environment
helm install spyspotter-dev ./helm/pixeltracker \
  -f helm/pixeltracker/values.yaml \
  --set environment=development \
  --set replicaCount=1 \
  --set persistence.enabled=false

# Production environment
helm install spyspotter-prod ./helm/pixeltracker \
  -f helm/pixeltracker/values.yaml \
  --set environment=production \
  --set autoscaling.enabled=true \
  --set monitoring.prometheus.enabled=true

# Enterprise environment
helm install spyspotter-enterprise ./helm/pixeltracker \
  -f helm/pixeltracker/values.yaml \
  --set environment=enterprise \
  --set redis.enabled=true \
  --set postgresql.enabled=true \
  --set monitoring.prometheus.enabled=true \
  --set monitoring.grafana.enabled=true
```

#### Configuration Customization

Create a custom values file:

```yaml
# custom-values.yaml
environment: production
replicaCount: 3

image:
  variant: enterprise

resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"

redis:
  enabled: true
  auth:
    password: "your-secure-password"

postgresql:
  enabled: true
  auth:
    password: "your-db-password"

monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true

ingress:
  enabled: true
  hosts:
    - host: spyspotter.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: spyspotter-tls
      hosts:
        - spyspotter.yourdomain.com
```

Deploy with custom values:

```bash
helm install spyspotter ./helm/pixeltracker -f custom-values.yaml
```

### Kubernetes Resources

The Helm chart creates the following Kubernetes resources:

#### Core Resources
- **Deployment**: Main application pods
- **Service**: Internal service exposure
- **ConfigMap**: Application configuration
- **Secret**: Sensitive configuration data
- **ServiceAccount**: RBAC service account

#### Storage Resources
- **PersistentVolumeClaim**: Data persistence
  - `spyspotter-data`: Application data
  - `spyspotter-logs`: Application logs
  - `spyspotter-config`: Configuration files
  - `spyspotter-cache`: Cache data

#### Networking Resources
- **Ingress**: External access (optional)
- **NetworkPolicy**: Network security (optional)

#### Monitoring Resources
- **ServiceMonitor**: Prometheus scraping
- **PrometheusRule**: Alerting rules
- **ConfigMap**: Grafana dashboards

#### Autoscaling Resources
- **HorizontalPodAutoscaler**: Automatic scaling
- **PodDisruptionBudget**: Availability guarantees

### Database Integration

#### External Database Configuration

```yaml
# Use external Redis
redis:
  enabled: false
  external:
    enabled: true
    host: "redis.example.com"
    port: 6379
    password: "redis-password"

# Use external PostgreSQL
postgresql:
  enabled: false
  external:
    enabled: true
    host: "postgres.example.com"
    port: 5432
    database: "spyspotter"
    username: "spyspotter"
    password: "db-password"
```

#### Managed Database Services

```yaml
# Using cloud-managed services
redis:
  external:
    enabled: true
    host: "spyspotter-redis.abc123.cache.amazonaws.com"
    port: 6379

postgresql:
  external:
    enabled: true
    host: "spyspotter-db.cluster-abc123.us-west-2.rds.amazonaws.com"
    port: 5432
    database: "spyspotter"
    username: "spyspotter"
```

### Monitoring and Observability

#### Prometheus Integration

```yaml
monitoring:
  prometheus:
    enabled: true
    serviceMonitor:
      enabled: true
      interval: 30s
    prometheusRule:
      enabled: true
```

#### Grafana Dashboards

```yaml
monitoring:
  grafana:
    enabled: true
    dashboards:
      enabled: true
      configMapName: "spyspotter-dashboards"
```

#### Custom Metrics

SpySpotter exposes metrics at `/metrics` endpoint:

- `spyspotter_scans_total`: Total number of scans performed
- `spyspotter_trackers_detected_total`: Total trackers detected
- `spyspotter_scan_duration_seconds`: Scan duration histogram
- `spyspotter_privacy_score_histogram`: Privacy score distribution

### Security Configuration

#### RBAC

```yaml
rbac:
  create: true
  rules:
    - apiGroups: [""]
      resources: ["configmaps", "secrets"]
      verbs: ["get", "list", "watch"]
```

#### Pod Security

```yaml
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
  capabilities:
    drop:
      - ALL
```

#### Network Policies

```yaml
networkPolicy:
  enabled: true
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
```

### Scaling and High Availability

#### Horizontal Pod Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

#### Pod Disruption Budget

```yaml
podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

#### Multi-Zone Deployment

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/name
            operator: In
            values:
            - spyspotter
        topologyKey: topology.kubernetes.io/zone
```

### Backup and Disaster Recovery

#### Database Backups

```yaml
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention: "30d"
  storage:
    type: "s3"
    s3:
      bucket: "spyspotter-backups"
      region: "us-west-2"
```

#### Configuration Backups

```bash
# Backup Helm values
helm get values spyspotter > spyspotter-values-backup.yaml

# Backup Kubernetes manifests
kubectl get all,configmap,secret,pvc -l app.kubernetes.io/name=spyspotter -o yaml > spyspotter-k8s-backup.yaml
```

## 🔧 Maintenance and Operations

### Updating Deployments

#### Docker Compose Updates

```bash
# Pull latest images
docker-compose pull

# Recreate containers with new images
docker-compose up -d --force-recreate
```

#### Helm Updates

```bash
# Update dependencies
helm dependency update ./helm/pixeltracker

# Upgrade deployment
helm upgrade spyspotter ./helm/pixeltracker -f custom-values.yaml

# Rollback if needed
helm rollback spyspotter 1
```

### Logs and Debugging

#### Docker Logs

```bash
# View application logs
docker-compose logs -f spyspotter-enterprise

# View specific service logs
docker-compose logs redis postgres
```

#### Kubernetes Logs

```bash
# View pod logs
kubectl logs -f deployment/spyspotter

# View logs from all pods
kubectl logs -f -l app.kubernetes.io/name=spyspotter

# Debug pod issues
kubectl describe pod spyspotter-xxx
```

### Health Monitoring

#### Health Check Endpoints

- `GET /health` - Overall health status
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

#### Monitoring Commands

```bash
# Check Docker container health
docker inspect --format='{{json .State.Health}}' spyspotter-enterprise

# Check Kubernetes pod health
kubectl get pods -l app.kubernetes.io/name=spyspotter
kubectl describe pods -l app.kubernetes.io/name=spyspotter
```

## 📊 Performance Tuning

### Resource Optimization

#### Memory Settings

```yaml
resources:
  requests:
    memory: "1Gi"      # Minimum memory
  limits:
    memory: "4Gi"      # Maximum memory

# For ML workloads, increase memory
resources:
  requests:
    memory: "2Gi"
  limits:
    memory: "8Gi"
```

#### CPU Settings

```yaml
resources:
  requests:
    cpu: "500m"        # 0.5 CPU cores
  limits:
    cpu: "2000m"       # 2 CPU cores
```

#### Concurrent Scanning

```bash
# Increase concurrent requests for better throughput
export PIXELTRACKER__SCANNING__CONCURRENT_REQUESTS=50
export PIXELTRACKER__SCANNING__RATE_LIMIT_DELAY=0.5
```

### Database Performance

#### Redis Configuration

```yaml
redis:
  master:
    persistence:
      enabled: true
      size: 8Gi
    resources:
      requests:
        memory: 256Mi
        cpu: 250m
```

#### PostgreSQL Configuration

```yaml
postgresql:
  primary:
    persistence:
      enabled: true
      size: 20Gi
    resources:
      requests:
        memory: 512Mi
        cpu: 500m
```

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs for errors
docker-compose logs spyspotter-enterprise

# Verify configuration
docker-compose config

# Check resource limits
docker stats
```

#### Database Connection Issues

```bash
# Test Redis connectivity
docker-compose exec spyspotter-enterprise redis-cli -h redis ping

# Test PostgreSQL connectivity
docker-compose exec spyspotter-enterprise psql -h postgres -U spyspotter -d spyspotter -c "SELECT 1;"
```

#### Kubernetes Pod CrashLoopBackOff

```bash
# Check pod events
kubectl describe pod spyspotter-xxx

# Check logs
kubectl logs spyspotter-xxx --previous

# Check resource limits
kubectl top pod spyspotter-xxx
```

#### Configuration Issues

```bash
# Validate configuration syntax
python -c "
import yaml
with open('config.yaml') as f:
    yaml.safe_load(f)
print('Configuration is valid')
"

# Test environment variable expansion
docker-compose exec spyspotter-enterprise env | grep PIXELTRACKER
```

### Performance Issues

#### Slow Scanning

1. Increase concurrent requests:
   ```bash
   export PIXELTRACKER__SCANNING__CONCURRENT_REQUESTS=20
   ```

2. Reduce rate limiting:
   ```bash
   export PIXELTRACKER__SCANNING__RATE_LIMIT_DELAY=0.5
   ```

3. Scale horizontally:
   ```bash
   kubectl scale deployment spyspotter --replicas=5
   ```

#### Memory Issues

1. Increase memory limits:
   ```yaml
   resources:
     limits:
       memory: "8Gi"
   ```

2. Enable swap accounting (Docker):
   ```bash
   # Add to /etc/default/grub
   GRUB_CMDLINE_LINUX="cgroup_enable=memory swapaccount=1"
   ```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [GitHub Repository](https://github.com/brian-scardina/spyspotter)

For support and questions, please open an issue on the [GitHub repository](https://github.com/brian-scardina/spyspotter/issues).
