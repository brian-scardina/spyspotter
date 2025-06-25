#!/usr/bin/env python3
"""
Configuration management for PixelTracker
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for PixelTracker"""
    
    DEFAULT_CONFIG = {
        'scanning': {
            'rate_limit_delay': 1.0,
            'request_timeout': 10,
            'max_retries': 3,
            'concurrent_requests': 10,
            'follow_redirects': True,
            'verify_ssl': True
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
            'viewport': {'width': 1920, 'height': 1080}
        },
        'detection': {
            'enable_ml_clustering': False,
            'enable_behavioral_analysis': False,
            'custom_patterns': [],
            'sensitivity': 'medium'  # low, medium, high
        },
        'privacy': {
            'scoring_weights': {
                'tracking_pixel': 5,
                'external_script': 8,
                'inline_script': 3,
                'high_risk_domain': 10
            },
            'risk_thresholds': {
                'low': 80,
                'medium': 50,
                'high': 0
            }
        },
        'output': {
            'formats': ['json', 'html', 'csv'],
            'include_raw_html': False,
            'include_screenshots': False,
            'compress_output': False
        },
        'database': {
            'enabled': True,
            'path': 'tracker_intelligence.db',
            'auto_backup': True,
            'retention_days': 30
        },
        'logging': {
            'level': 'INFO',
            'file': 'pixeltracker.log',
            'max_size_mb': 10,
            'backup_count': 5
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_path = config_path
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> None:
        """Load configuration from file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(f"Config file {config_path} not found, using defaults")
                return
            
            with open(config_file, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    user_config = yaml.safe_load(f)
                elif config_path.endswith('.json'):
                    user_config = json.load(f)
                else:
                    logger.error(f"Unsupported config format: {config_path}")
                    return
            
            # Deep merge user config with defaults
            self._deep_merge(self.config, user_config)
            logger.info(f"Configuration loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save_config(self, config_path: str) -> None:
        """Save current configuration to file"""
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
                elif config_path.endswith('.json'):
                    json.dump(self.config, f, indent=2)
                else:
                    logger.error(f"Unsupported config format: {config_path}")
                    return
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
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
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def validate(self) -> bool:
        """Validate configuration values"""
        errors = []
        
        # Validate scanning settings
        if self.get('scanning.rate_limit_delay', 0) < 0:
            errors.append("scanning.rate_limit_delay must be >= 0")
        
        if self.get('scanning.request_timeout', 0) <= 0:
            errors.append("scanning.request_timeout must be > 0")
        
        if self.get('scanning.concurrent_requests', 0) <= 0:
            errors.append("scanning.concurrent_requests must be > 0")
        
        # Validate privacy scoring weights
        weights = self.get('privacy.scoring_weights', {})
        for weight_name, weight_value in weights.items():
            if not isinstance(weight_value, (int, float)) or weight_value < 0:
                errors.append(f"privacy.scoring_weights.{weight_name} must be a non-negative number")
        
        # Validate risk thresholds
        thresholds = self.get('privacy.risk_thresholds', {})
        if 'low' in thresholds and 'medium' in thresholds and 'high' in thresholds:
            if not (thresholds['high'] <= thresholds['medium'] <= thresholds['low']):
                errors.append("privacy.risk_thresholds must be ordered: high <= medium <= low")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False
        
        return True
    
    def create_sample_config(self, config_path: str) -> None:
        """Create a sample configuration file"""
        sample_config = {
            'scanning': {
                'rate_limit_delay': 1.0,
                'request_timeout': 10,
                'concurrent_requests': 5,
                'follow_redirects': True
            },
            'javascript': {
                'enabled': False,
                'wait_time': 3
            },
            'detection': {
                'sensitivity': 'medium',
                'custom_patterns': [
                    # Add your custom tracking patterns here
                ]
            },
            'privacy': {
                'scoring_weights': {
                    'tracking_pixel': 5,
                    'external_script': 8,
                    'inline_script': 3,
                    'high_risk_domain': 10
                }
            },
            'output': {
                'formats': ['json', 'html'],
                'include_raw_html': False
            },
            'logging': {
                'level': 'INFO',
                'file': 'pixeltracker.log'
            }
        }
        
        try:
            with open(config_path, 'w') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(sample_config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(sample_config, f, indent=2)
            
            print(f"✅ Sample configuration created: {config_path}")
            print("Edit this file to customize your scanning preferences.")
            
        except Exception as e:
            logger.error(f"Failed to create sample config: {e}")

def load_config(config_path: Optional[str] = None) -> Config:
    """Convenience function to load configuration"""
    return Config(config_path)
