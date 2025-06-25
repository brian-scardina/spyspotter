#!/bin/bash

# PixelTracker Docker Entrypoint Script
# Handles environment-specific configuration merging and startup

set -e

# Default values
PIXELTRACKER_ENV=${PIXELTRACKER_ENV:-production}
PIXELTRACKER_CONFIG_DIR=${PIXELTRACKER_CONFIG_DIR:-/app/config.d}
PIXELTRACKER_DATA_DIR=${PIXELTRACKER_DATA_DIR:-/app/data}
PIXELTRACKER_LOG_DIR=${PIXELTRACKER_LOG_DIR:-/app/logs}
PIXELTRACKER_STAGE=${PIXELTRACKER_STAGE:-core}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ENTRYPOINT:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Create directories if they don't exist
create_directories() {
    log "Creating necessary directories..."
    mkdir -p "$PIXELTRACKER_CONFIG_DIR" "$PIXELTRACKER_DATA_DIR" "$PIXELTRACKER_LOG_DIR"
    
    # Create cache directory
    mkdir -p /app/cache
    
    # Create config.d subdirectories for different environments
    mkdir -p "$PIXELTRACKER_CONFIG_DIR/base"
    mkdir -p "$PIXELTRACKER_CONFIG_DIR/development"
    mkdir -p "$PIXELTRACKER_CONFIG_DIR/testing"
    mkdir -p "$PIXELTRACKER_CONFIG_DIR/staging"
    mkdir -p "$PIXELTRACKER_CONFIG_DIR/production"
    mkdir -p "$PIXELTRACKER_CONFIG_DIR/enterprise"
}

# Generate default configuration
generate_default_config() {
    local config_file="$PIXELTRACKER_CONFIG_DIR/base/default.yaml"
    
    if [ ! -f "$config_file" ]; then
        log "Generating default configuration: $config_file"
        cat > "$config_file" << 'EOF'
# PixelTracker Default Configuration
# This is the base configuration that gets merged with environment-specific configs

scanning:
  rate_limit_delay: 1.0
  request_timeout: 10
  max_retries: 3
  concurrent_requests: 10
  follow_redirects: true
  verify_ssl: true

user_agents:
  - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
  - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
  - "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

headers:
  Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
  Accept-Language: "en-US,en;q=0.5"
  Accept-Encoding: "gzip, deflate"
  Connection: "keep-alive"
  Upgrade-Insecure-Requests: "1"

javascript:
  enabled: false
  browser: "chrome"
  headless: true
  wait_time: 3
  viewport:
    width: 1920
    height: 1080

detection:
  enable_ml_clustering: false
  enable_behavioral_analysis: false
  custom_patterns: []
  sensitivity: "medium"

privacy:
  scoring_weights:
    tracking_pixel: 5
    external_script: 8
    inline_script: 3
    high_risk_domain: 10
  risk_thresholds:
    low: 80
    medium: 50
    high: 0

output:
  formats: ["json", "html"]
  include_raw_html: false
  include_screenshots: false
  compress_output: false

database:
  enabled: true
  path: "${PIXELTRACKER_DATA_DIR}/tracker_intelligence.db"
  auto_backup: true
  retention_days: 30

logging:
  level: "INFO"
  file: "${PIXELTRACKER_LOG_DIR}/pixeltracker.log"
  max_size_mb: 10
  backup_count: 5

enterprise:
  enabled: false
  redis:
    enabled: false
    host: "localhost"
    port: 6379
    password: ""
    db: 0
  monitoring:
    enabled: false
    prometheus_port: 9090
    metrics_endpoint: "/metrics"
  task_queue:
    enabled: false
    broker_url: "redis://localhost:6379/1"
    result_backend: "redis://localhost:6379/2"
EOF
    fi
}

# Generate environment-specific configuration
generate_env_config() {
    local env="$1"
    local config_file="$PIXELTRACKER_CONFIG_DIR/$env/$env.yaml"
    
    case "$env" in
        "development")
            if [ ! -f "$config_file" ]; then
                log "Generating development configuration: $config_file"
                cat > "$config_file" << 'EOF'
# Development Environment Configuration
logging:
  level: "DEBUG"
  
scanning:
  concurrent_requests: 5
  rate_limit_delay: 0.5

javascript:
  enabled: true
  
detection:
  enable_ml_clustering: true
  enable_behavioral_analysis: true
  sensitivity: "high"

output:
  include_raw_html: true
  include_screenshots: true
EOF
            fi
            ;;
        "production")
            if [ ! -f "$config_file" ]; then
                log "Generating production configuration: $config_file"
                cat > "$config_file" << 'EOF'
# Production Environment Configuration
logging:
  level: "INFO"
  
scanning:
  concurrent_requests: 20
  rate_limit_delay: 1.5
  request_timeout: 15

privacy:
  scoring_weights:
    tracking_pixel: 7
    external_script: 10
    inline_script: 4
    high_risk_domain: 15

database:
  retention_days: 90
  auto_backup: true

output:
  compress_output: true
EOF
            fi
            ;;
        "enterprise")
            if [ ! -f "$config_file" ]; then
                log "Generating enterprise configuration: $config_file"
                cat > "$config_file" << 'EOF'
# Enterprise Environment Configuration
javascript:
  enabled: true

detection:
  enable_ml_clustering: true
  enable_behavioral_analysis: true
  sensitivity: "high"

enterprise:
  enabled: true
  redis:
    enabled: true
    host: "${PIXELTRACKER_REDIS_HOST:-redis}"
    port: "${PIXELTRACKER_REDIS_PORT:-6379}"
    password: "${PIXELTRACKER_REDIS_PASSWORD:-}"
    db: 0
  monitoring:
    enabled: true
    prometheus_port: 9090
    metrics_endpoint: "/metrics"
  task_queue:
    enabled: true
    broker_url: "redis://${PIXELTRACKER_REDIS_HOST:-redis}:${PIXELTRACKER_REDIS_PORT:-6379}/1"
    result_backend: "redis://${PIXELTRACKER_REDIS_HOST:-redis}:${PIXELTRACKER_REDIS_PORT:-6379}/2"

scanning:
  concurrent_requests: 50
  rate_limit_delay: 0.5

output:
  formats: ["json", "html", "csv"]
  include_raw_html: true
  compress_output: true
EOF
            fi
            ;;
    esac
}

# Process environment variables into configuration overrides
process_env_vars() {
    local override_file="$PIXELTRACKER_CONFIG_DIR/env_overrides.yaml"
    
    log "Processing environment variable overrides..."
    
    # Create empty override file
    echo "# Environment variable overrides" > "$override_file"
    echo "# Generated at $(date)" >> "$override_file"
    
    # Process PIXELTRACKER__ prefixed environment variables
    env | grep '^PIXELTRACKER__' | while IFS='=' read -r key value; do
        # Remove PIXELTRACKER__ prefix and convert to lowercase
        config_key=$(echo "${key#PIXELTRACKER__}" | tr '[:upper:]' '[:lower:]' | tr '_' '.')
        
        # Convert boolean strings
        case "$value" in
            "true"|"True"|"TRUE") yaml_value="true" ;;
            "false"|"False"|"FALSE") yaml_value="false" ;;
            *) yaml_value="\"$value\"" ;;
        esac
        
        # Write to override file (simple format, may need enhancement for nested values)
        log "Override: $config_key = $yaml_value"
        echo "$config_key: $yaml_value" >> "$override_file"
    done
}

# Merge configuration files
merge_configurations() {
    log "Merging configuration files for environment: $PIXELTRACKER_ENV"
    
    local merged_config="/tmp/merged_config.yaml"
    local base_config="$PIXELTRACKER_CONFIG_DIR/base/default.yaml"
    local env_config="$PIXELTRACKER_CONFIG_DIR/$PIXELTRACKER_ENV/$PIXELTRACKER_ENV.yaml"
    local override_config="$PIXELTRACKER_CONFIG_DIR/env_overrides.yaml"
    
    # Start with base configuration
    cp "$base_config" "$merged_config"
    
    # Merge environment-specific config if it exists
    if [ -f "$env_config" ]; then
        log "Merging environment config: $env_config"
        # Note: This is a simple approach. For complex merging, consider using yq or python
        python3 << EOF
import yaml
import sys

try:
    # Load base config
    with open('$merged_config', 'r') as f:
        base = yaml.safe_load(f) or {}
    
    # Load environment config
    with open('$env_config', 'r') as f:
        env_conf = yaml.safe_load(f) or {}
    
    # Simple deep merge function
    def deep_merge(base_dict, update_dict):
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    # Merge configurations
    deep_merge(base, env_conf)
    
    # Write merged config
    with open('$merged_config', 'w') as f:
        yaml.dump(base, f, default_flow_style=False, indent=2)
        
    print("Configuration merge successful")
    
except Exception as e:
    print(f"Configuration merge failed: {e}")
    sys.exit(1)
EOF
    fi
    
    # Set the merged config as the default config file
    export PIXELTRACKER_CONFIG="$merged_config"
    log "Using merged configuration: $PIXELTRACKER_CONFIG"
}

# Validate configuration
validate_configuration() {
    log "Validating configuration..."
    
    if [ -f "$PIXELTRACKER_CONFIG" ]; then
        python3 << EOF
import yaml
import sys
import os

config_file = os.environ.get('PIXELTRACKER_CONFIG')
try:
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Basic validation
    required_sections = ['scanning', 'logging', 'privacy']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    
    print("Configuration validation successful")
    
except Exception as e:
    print(f"Configuration validation failed: {e}")
    sys.exit(1)
EOF
    else
        error "No configuration file found at: $PIXELTRACKER_CONFIG"
        exit 1
    fi
}

# Display startup information
display_startup_info() {
    log "PixelTracker Container Starting..."
    log "Environment: $PIXELTRACKER_ENV"
    log "Stage: $PIXELTRACKER_STAGE"
    log "Config Directory: $PIXELTRACKER_CONFIG_DIR"
    log "Data Directory: $PIXELTRACKER_DATA_DIR"
    log "Log Directory: $PIXELTRACKER_LOG_DIR"
    log "Configuration File: $PIXELTRACKER_CONFIG"
    
    # Display environment variables with PIXELTRACKER prefix
    log "Environment Variables:"
    env | grep '^PIXELTRACKER' | while IFS='=' read -r key value; do
        # Mask sensitive values
        case "$key" in
            *PASSWORD*|*SECRET*|*TOKEN*|*KEY*)
                masked_value="***MASKED***"
                log "  $key=$masked_value"
                ;;
            *)
                log "  $key=$value"
                ;;
        esac
    done
}

# Wait for dependencies
wait_for_dependencies() {
    # Wait for Redis if enabled
    if [ "$PIXELTRACKER_REDIS_ENABLED" = "true" ]; then
        local redis_host="${PIXELTRACKER_REDIS_HOST:-redis}"
        local redis_port="${PIXELTRACKER_REDIS_PORT:-6379}"
        
        log "Waiting for Redis at $redis_host:$redis_port..."
        
        for i in {1..30}; do
            if nc -z "$redis_host" "$redis_port" 2>/dev/null; then
                log "Redis is available"
                break
            fi
            
            if [ $i -eq 30 ]; then
                warn "Redis is not available after 30 attempts, continuing anyway..."
            else
                sleep 1
            fi
        done
    fi
    
    # Wait for PostgreSQL if configured
    if [ -n "$PIXELTRACKER_POSTGRES_HOST" ]; then
        local pg_host="$PIXELTRACKER_POSTGRES_HOST"
        local pg_port="${PIXELTRACKER_POSTGRES_PORT:-5432}"
        
        log "Waiting for PostgreSQL at $pg_host:$pg_port..."
        
        for i in {1..30}; do
            if nc -z "$pg_host" "$pg_port" 2>/dev/null; then
                log "PostgreSQL is available"
                break
            fi
            
            if [ $i -eq 30 ]; then
                warn "PostgreSQL is not available after 30 attempts, continuing anyway..."
            else
                sleep 1
            fi
        done
    fi
}

# Main execution
main() {
    display_startup_info
    create_directories
    generate_default_config
    generate_env_config "$PIXELTRACKER_ENV"
    process_env_vars
    merge_configurations
    validate_configuration
    wait_for_dependencies
    
    log "Initialization complete. Starting application..."
    
    # Execute the passed command
    exec "$@"
}

# Run main function
main "$@"
