#!/usr/bin/env python3
"""
Enhanced Configuration Management for PixelTracker
Supports environment-specific configuration merging and environment variable overrides
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from copy import deepcopy
import re

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """Enhanced configuration manager with environment support and variable interpolation"""
    
    def __init__(self, 
                 config_dir: Optional[str] = None,
                 environment: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
            environment: Environment name (development, production, etc.)
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config.d"
        self.environment = environment or os.getenv("PIXELTRACKER_ENV", "production")
        self.config: Dict[str, Any] = {}
        self.config_loaded = False
        
        # Environment variable prefix for overrides
        self.env_prefix = "PIXELTRACKER__"
        
        # Default configuration structure
        self.default_config = {
            'scanning': {
                'rate_limit_delay': 1.0,
                'request_timeout': 10,
                'max_retries': 3,
                'concurrent_requests': 10,
                'follow_redirects': True,
                'verify_ssl': True,
                'user_agent_rotation': True
            },
            'user_agents': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ],
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'javascript': {
                'enabled': False,
                'browser': 'chrome',
                'headless': True,
                'wait_time': 3,
                'viewport': {'width': 1920, 'height': 1080},
                'page_timeout': 30
            },
            'detection': {
                'enable_ml_clustering': False,
                'enable_behavioral_analysis': False,
                'custom_patterns': [],
                'sensitivity': 'medium',
                'min_confidence': 0.7
            },
            'privacy': {
                'scoring_weights': {
                    'tracking_pixel': 5,
                    'external_script': 8,
                    'inline_script': 3,
                    'high_risk_domain': 10,
                    'social_media': 7,
                    'advertising': 9
                },
                'risk_thresholds': {
                    'low': 80,
                    'medium': 50,
                    'high': 20,
                    'critical': 0
                }
            },
            'output': {
                'formats': ['json', 'html'],
                'include_raw_html': False,
                'include_screenshots': False,
                'compress_output': False,
                'pretty_print': True
            },
            'database': {
                'enabled': True,
                'type': 'sqlite',
                'path': '${PIXELTRACKER_DATA_DIR}/tracker_intelligence.db',
                'auto_backup': True,
                'retention_days': 30,
                'connection_pool_size': 10
            },
            'logging': {
                'level': 'INFO',
                'file': '${PIXELTRACKER_LOG_DIR}/pixeltracker.log',
                'max_size_mb': 10,
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'json_format': False
            },
            'enterprise': {
                'enabled': False,
                'redis': {
                    'enabled': False,
                    'host': 'localhost',
                    'port': 6379,
                    'password': '',
                    'db': 0,
                    'connection_pool_size': 10
                },
                'monitoring': {
                    'enabled': False,
                    'prometheus_port': 9090,
                    'metrics_endpoint': '/metrics',
                    'health_check_endpoint': '/health'
                },
                'task_queue': {
                    'enabled': False,
                    'broker_url': 'redis://localhost:6379/1',
                    'result_backend': 'redis://localhost:6379/2',
                    'worker_concurrency': 4
                },
                'api': {
                    'enabled': False,
                    'host': '0.0.0.0',
                    'port': 8080,
                    'cors_enabled': True,
                    'rate_limiting': True
                }
            },
            'ml': {
                'enabled': False,
                'model_cache_dir': '${PIXELTRACKER_DATA_DIR}/models',
                'training_data_dir': '${PIXELTRACKER_DATA_DIR}/training',
                'auto_retrain': False,
                'model_update_interval': 86400  # 24 hours
            }
        }
    
    def load_configuration(self) -> None:
        """Load and merge configurations from various sources"""
        if self.config_loaded:
            return
        
        logger.info(f"Loading configuration for environment: {self.environment}")
        logger.info(f"Configuration directory: {self.config_dir}")
        
        # Start with default configuration
        self.config = deepcopy(self.default_config)
        
        # 1. Load base configuration
        self._load_base_config()
        
        # 2. Load environment-specific configuration
        self._load_environment_config()
        
        # 3. Apply environment variable overrides
        self._apply_env_var_overrides()
        
        # 4. Interpolate variables
        self._interpolate_variables()
        
        # 5. Validate configuration
        self._validate_configuration()
        
        self.config_loaded = True
        logger.info("Configuration loaded successfully")
    
    def _load_base_config(self) -> None:
        """Load base configuration files"""
        base_dir = self.config_dir / "base"
        if base_dir.exists():
            for config_file in base_dir.glob("*.yaml"):
                logger.debug(f"Loading base config: {config_file}")
                try:
                    with open(config_file, 'r') as f:
                        base_config = yaml.safe_load(f) or {}
                    self._deep_merge(self.config, base_config)
                except Exception as e:
                    logger.warning(f"Failed to load base config {config_file}: {e}")
    
    def _load_environment_config(self) -> None:
        """Load environment-specific configuration"""
        env_dir = self.config_dir / self.environment
        if env_dir.exists():
            # Load environment config file
            env_config_file = env_dir / f"{self.environment}.yaml"
            if env_config_file.exists():
                logger.debug(f"Loading environment config: {env_config_file}")
                try:
                    with open(env_config_file, 'r') as f:
                        env_config = yaml.safe_load(f) or {}
                    self._deep_merge(self.config, env_config)
                except Exception as e:
                    logger.warning(f"Failed to load environment config {env_config_file}: {e}")
            
            # Load additional environment files
            for config_file in env_dir.glob("*.yaml"):
                if config_file.name != f"{self.environment}.yaml":
                    logger.debug(f"Loading additional environment config: {config_file}")
                    try:
                        with open(config_file, 'r') as f:
                            additional_config = yaml.safe_load(f) or {}
                        self._deep_merge(self.config, additional_config)
                    except Exception as e:
                        logger.warning(f"Failed to load additional config {config_file}: {e}")
    
    def _apply_env_var_overrides(self) -> None:
        """Apply environment variable overrides using PIXELTRACKER__ prefix"""
        logger.debug("Applying environment variable overrides")
        
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Remove prefix and convert to config path
                config_key = key[len(self.env_prefix):].lower().replace('_', '.')
                
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value)
                
                # Set the configuration value
                self._set_nested_value(self.config, config_key, converted_value)
                logger.debug(f"Environment override: {config_key} = {converted_value}")
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool, List[str]]:
        """Convert environment variable string to appropriate type"""
        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Handle numeric values
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        # Handle lists (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set a nested configuration value using dot notation"""
        keys = key_path.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # Convert to dict if it's not already
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _interpolate_variables(self) -> None:
        """Interpolate variables in configuration values"""
        logger.debug("Interpolating configuration variables")
        self.config = self._interpolate_recursive(self.config)
    
    def _interpolate_recursive(self, obj: Any) -> Any:
        """Recursively interpolate variables in configuration"""
        if isinstance(obj, dict):
            return {key: self._interpolate_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._interpolate_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._interpolate_string(obj)
        else:
            return obj
    
    def _interpolate_string(self, value: str) -> str:
        """Interpolate variables in a string value"""
        # Pattern to match ${VAR_NAME} or ${VAR_NAME:-default}
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_expr = match.group(1)
            
            # Check for default value syntax: VAR_NAME:-default
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
            else:
                var_name = var_expr
                default_value = ''
            
            # Get value from environment
            env_value = os.getenv(var_name, default_value)
            return env_value
        
        return re.sub(pattern, replace_var, value)
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _validate_configuration(self) -> None:
        """Validate the merged configuration"""
        errors = []
        
        # Validate scanning settings
        scanning = self.config.get('scanning', {})
        if scanning.get('rate_limit_delay', 0) < 0:
            errors.append("scanning.rate_limit_delay must be >= 0")
        
        if scanning.get('request_timeout', 0) <= 0:
            errors.append("scanning.request_timeout must be > 0")
        
        if scanning.get('concurrent_requests', 0) <= 0:
            errors.append("scanning.concurrent_requests must be > 0")
        
        # Validate privacy settings
        privacy = self.config.get('privacy', {})
        weights = privacy.get('scoring_weights', {})
        for weight_name, weight_value in weights.items():
            if not isinstance(weight_value, (int, float)) or weight_value < 0:
                errors.append(f"privacy.scoring_weights.{weight_name} must be a non-negative number")
        
        thresholds = privacy.get('risk_thresholds', {})
        if all(k in thresholds for k in ['low', 'medium', 'high']):
            if not (thresholds['high'] <= thresholds['medium'] <= thresholds['low']):
                errors.append("privacy.risk_thresholds must be ordered: high <= medium <= low")
        
        # Validate enterprise settings if enabled
        enterprise = self.config.get('enterprise', {})
        if enterprise.get('enabled', False):
            redis_config = enterprise.get('redis', {})
            if redis_config.get('enabled', False):
                if not redis_config.get('host'):
                    errors.append("enterprise.redis.host is required when Redis is enabled")
                if not isinstance(redis_config.get('port'), int) or redis_config.get('port') <= 0:
                    errors.append("enterprise.redis.port must be a positive integer")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        if not self.config_loaded:
            self.load_configuration()
        
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        if not self.config_loaded:
            self.load_configuration()
        
        self._set_nested_value(self.config, key, value)
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration dictionary"""
        if not self.config_loaded:
            self.load_configuration()
        
        return deepcopy(self.config)
    
    def save_config(self, file_path: str) -> None:
        """Save current configuration to file"""
        if not self.config_loaded:
            self.load_configuration()
        
        config_file = Path(file_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {file_path}: {e}")
            raise
    
    def create_sample_configs(self) -> None:
        """Create sample configuration files for different environments"""
        environments = {
            'development': {
                'logging': {'level': 'DEBUG'},
                'scanning': {
                    'concurrent_requests': 5,
                    'rate_limit_delay': 0.5
                },
                'javascript': {'enabled': True},
                'detection': {
                    'enable_ml_clustering': True,
                    'enable_behavioral_analysis': True,
                    'sensitivity': 'high'
                },
                'output': {
                    'include_raw_html': True,
                    'include_screenshots': True
                }
            },
            'testing': {
                'logging': {'level': 'DEBUG'},
                'scanning': {
                    'concurrent_requests': 2,
                    'rate_limit_delay': 0.1
                },
                'database': {
                    'path': '${PIXELTRACKER_DATA_DIR}/test_tracker.db'
                }
            },
            'staging': {
                'logging': {'level': 'INFO'},
                'scanning': {
                    'concurrent_requests': 15,
                    'rate_limit_delay': 1.0
                },
                'enterprise': {
                    'enabled': True,
                    'redis': {'enabled': True}
                }
            },
            'production': {
                'logging': {
                    'level': 'INFO',
                    'json_format': True
                },
                'scanning': {
                    'concurrent_requests': 20,
                    'rate_limit_delay': 1.5,
                    'request_timeout': 15
                },
                'privacy': {
                    'scoring_weights': {
                        'tracking_pixel': 7,
                        'external_script': 10,
                        'inline_script': 4,
                        'high_risk_domain': 15
                    }
                },
                'database': {'retention_days': 90},
                'output': {'compress_output': True}
            },
            'enterprise': {
                'javascript': {'enabled': True},
                'detection': {
                    'enable_ml_clustering': True,
                    'enable_behavioral_analysis': True,
                    'sensitivity': 'high'
                },
                'enterprise': {
                    'enabled': True,
                    'redis': {
                        'enabled': True,
                        'host': '${PIXELTRACKER_REDIS_HOST:-redis}',
                        'port': '${PIXELTRACKER_REDIS_PORT:-6379}',
                        'password': '${PIXELTRACKER_REDIS_PASSWORD:-}'
                    },
                    'monitoring': {
                        'enabled': True,
                        'prometheus_port': 9090
                    },
                    'task_queue': {
                        'enabled': True,
                        'broker_url': 'redis://${PIXELTRACKER_REDIS_HOST:-redis}:${PIXELTRACKER_REDIS_PORT:-6379}/1',
                        'result_backend': 'redis://${PIXELTRACKER_REDIS_HOST:-redis}:${PIXELTRACKER_REDIS_PORT:-6379}/2'
                    },
                    'api': {
                        'enabled': True,
                        'host': '0.0.0.0',
                        'port': 8080
                    }
                },
                'ml': {
                    'enabled': True,
                    'auto_retrain': True
                },
                'scanning': {
                    'concurrent_requests': 50,
                    'rate_limit_delay': 0.5
                },
                'output': {
                    'formats': ['json', 'html', 'csv'],
                    'include_raw_html': True,
                    'compress_output': True
                }
            }
        }
        
        # Create base configuration
        base_dir = self.config_dir / "base"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        base_config_file = base_dir / "default.yaml"
        if not base_config_file.exists():
            with open(base_config_file, 'w') as f:
                yaml.dump(self.default_config, f, default_flow_style=False, indent=2)
            logger.info(f"Created base configuration: {base_config_file}")
        
        # Create environment-specific configurations
        for env_name, env_config in environments.items():
            env_dir = self.config_dir / env_name
            env_dir.mkdir(parents=True, exist_ok=True)
            
            env_config_file = env_dir / f"{env_name}.yaml"
            if not env_config_file.exists():
                with open(env_config_file, 'w') as f:
                    f.write(f"# {env_name.title()} Environment Configuration\n")
                    f.write(f"# Overrides for {env_name} environment\n\n")
                    yaml.dump(env_config, f, default_flow_style=False, indent=2)
                logger.info(f"Created {env_name} configuration: {env_config_file}")
    
    def reload(self) -> None:
        """Reload configuration from files"""
        self.config_loaded = False
        self.load_configuration()
        logger.info("Configuration reloaded")
    
    def __str__(self) -> str:
        """String representation of configuration"""
        if not self.config_loaded:
            self.load_configuration()
        
        return f"ConfigurationManager(environment={self.environment}, config_dir={self.config_dir})"
    
    def __repr__(self) -> str:
        return self.__str__()


# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager(
    config_dir: Optional[str] = None,
    environment: Optional[str] = None,
    force_reload: bool = False
) -> ConfigurationManager:
    """
    Get global configuration manager instance
    
    Args:
        config_dir: Configuration directory path
        environment: Environment name
        force_reload: Force recreation of config manager
    
    Returns:
        ConfigurationManager instance
    """
    global _config_manager
    
    if _config_manager is None or force_reload:
        _config_manager = ConfigurationManager(config_dir, environment)
    
    return _config_manager

def get_config(key: str, default: Any = None) -> Any:
    """Convenience function to get configuration value"""
    return get_config_manager().get(key, default)

def set_config(key: str, value: Any) -> None:
    """Convenience function to set configuration value"""
    get_config_manager().set(key, value)
