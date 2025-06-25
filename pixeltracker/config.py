#!/usr/bin/env python3
"""
Configuration manager for PixelTracker

Provides type-safe configuration management with validation.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScanningConfig:
    """Scanning-related configuration"""
    rate_limit_delay: float = 1.0
    request_timeout: float = 30.0
    max_retries: int = 3
    concurrent_requests: int = 10
    follow_redirects: bool = True
    verify_ssl: bool = True


@dataclass
class JavaScriptConfig:
    """JavaScript execution configuration"""
    enabled: bool = False
    browser: str = "chrome"
    headless: bool = True
    wait_time: float = 3.0
    viewport_width: int = 1920
    viewport_height: int = 1080


@dataclass
class DetectionConfig:
    """Detection engine configuration"""
    enable_ml_clustering: bool = False
    enable_behavioral_analysis: bool = False
    custom_patterns: List[str] = field(default_factory=list)
    sensitivity: str = "medium"  # low, medium, high


@dataclass
class PrivacyConfig:
    """Privacy scoring configuration"""
    scoring_weights: Dict[str, int] = field(default_factory=lambda: {
        'tracking_pixel': 5,
        'external_script': 8,
        'inline_script': 3,
        'high_risk_domain': 10
    })
    risk_thresholds: Dict[str, int] = field(default_factory=lambda: {
        'low': 80,
        'medium': 50,
        'high': 20
    })


@dataclass
class OutputConfig:
    """Output and reporting configuration"""
    formats: List[str] = field(default_factory=lambda: ['json', 'html'])
    include_raw_html: bool = False
    include_screenshots: bool = False
    compress_output: bool = False


@dataclass
class DatabaseConfig:
    """Database configuration"""
    enabled: bool = True
    path: str = "pixeltracker.db"
    auto_backup: bool = True
    retention_days: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file: Optional[str] = "pixeltracker.log"
    max_size_mb: int = 10
    backup_count: int = 5


@dataclass
class NetworkConfig:
    """Network-related configuration"""
    user_agents: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ])
    headers: Dict[str, str] = field(default_factory=lambda: {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })


class ConfigManager:
    """Configuration manager with type safety and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        
        # Initialize with defaults
        self.scanning = ScanningConfig()
        self.javascript = JavaScriptConfig()
        self.detection = DetectionConfig()
        self.privacy = PrivacyConfig()
        self.output = OutputConfig()
        self.database = DatabaseConfig()
        self.logging = LoggingConfig()
        self.network = NetworkConfig()
        
        # Load user configuration if provided
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
            
            # Update configuration sections
            self._update_config_section('scanning', user_config.get('scanning', {}))
            self._update_config_section('javascript', user_config.get('javascript', {}))
            self._update_config_section('detection', user_config.get('detection', {}))
            self._update_config_section('privacy', user_config.get('privacy', {}))
            self._update_config_section('output', user_config.get('output', {}))
            self._update_config_section('database', user_config.get('database', {}))
            self._update_config_section('logging', user_config.get('logging', {}))
            self._update_config_section('network', user_config.get('network', {}))
            
            logger.info(f"Configuration loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
    
    def _update_config_section(self, section_name: str, config_data: Dict[str, Any]) -> None:
        """Update a specific configuration section"""
        if not config_data:
            return
        
        section = getattr(self, section_name)
        for key, value in config_data.items():
            if hasattr(section, key):
                setattr(section, key, value)
            else:
                logger.warning(f"Unknown config key: {section_name}.{key}")
    
    def save_config(self, config_path: str) -> None:
        """Save current configuration to file"""
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'scanning': asdict(self.scanning),
                'javascript': asdict(self.javascript),
                'detection': asdict(self.detection),
                'privacy': asdict(self.privacy),
                'output': asdict(self.output),
                'database': asdict(self.database),
                'logging': asdict(self.logging),
                'network': asdict(self.network)
            }
            
            with open(config_file, 'w') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
                elif config_path.endswith('.json'):
                    json.dump(config_data, f, indent=2)
                else:
                    logger.error(f"Unsupported config format: {config_path}")
                    return
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        
        if len(keys) < 2:
            logger.error(f"Invalid config key format: {key}")
            return default
        
        section_name, *attr_path = keys
        
        if not hasattr(self, section_name):
            logger.error(f"Unknown config section: {section_name}")
            return default
        
        value = getattr(self, section_name)
        
        for attr in attr_path:
            if hasattr(value, attr):
                value = getattr(value, attr)
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        
        if len(keys) < 2:
            logger.error(f"Invalid config key format: {key}")
            return
        
        section_name, *attr_path = keys
        
        if not hasattr(self, section_name):
            logger.error(f"Unknown config section: {section_name}")
            return
        
        section = getattr(self, section_name)
        
        # Navigate to the parent of the target attribute
        for attr in attr_path[:-1]:
            if hasattr(section, attr):
                section = getattr(section, attr)
            else:
                logger.error(f"Unknown config attribute: {key}")
                return
        
        # Set the final attribute
        final_attr = attr_path[-1]
        if hasattr(section, final_attr):
            setattr(section, final_attr, value)
        else:
            logger.error(f"Unknown config attribute: {key}")
    
    def validate(self) -> bool:
        """Validate configuration values"""
        errors = []
        
        # Validate scanning settings
        if self.scanning.rate_limit_delay < 0:
            errors.append("scanning.rate_limit_delay must be >= 0")
        
        if self.scanning.request_timeout <= 0:
            errors.append("scanning.request_timeout must be > 0")
        
        if self.scanning.concurrent_requests <= 0:
            errors.append("scanning.concurrent_requests must be > 0")
        
        # Validate privacy scoring weights
        for weight_name, weight_value in self.privacy.scoring_weights.items():
            if not isinstance(weight_value, (int, float)) or weight_value < 0:
                errors.append(f"privacy.scoring_weights.{weight_name} must be a non-negative number")
        
        # Validate risk thresholds
        thresholds = self.privacy.risk_thresholds
        if 'low' in thresholds and 'medium' in thresholds and 'high' in thresholds:
            if not (thresholds['high'] <= thresholds['medium'] <= thresholds['low']):
                errors.append("privacy.risk_thresholds must be ordered: high <= medium <= low")
        
        # Validate JavaScript config
        if self.javascript.wait_time < 0:
            errors.append("javascript.wait_time must be >= 0")
        
        if self.javascript.viewport_width <= 0 or self.javascript.viewport_height <= 0:
            errors.append("javascript viewport dimensions must be > 0")
        
        # Validate detection sensitivity
        if self.detection.sensitivity not in ['low', 'medium', 'high']:
            errors.append("detection.sensitivity must be 'low', 'medium', or 'high'")
        
        # Log errors
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
                'request_timeout': 30.0,
                'concurrent_requests': 5,
                'follow_redirects': True
            },
            'javascript': {
                'enabled': False,
                'wait_time': 3.0
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'scanning': asdict(self.scanning),
            'javascript': asdict(self.javascript),
            'detection': asdict(self.detection),
            'privacy': asdict(self.privacy),
            'output': asdict(self.output),
            'database': asdict(self.database),
            'logging': asdict(self.logging),
            'network': asdict(self.network)
        }
    
    def get_scan_configuration(self) -> 'ScanConfiguration':
        """Get scan configuration in the format expected by services"""
        from .models import ScanConfiguration
        
        return ScanConfiguration(
            enable_javascript=self.javascript.enabled,
            enable_ml_analysis=self.detection.enable_ml_clustering,
            enable_advanced_fingerprinting=self.detection.enable_behavioral_analysis,
            rate_limit_delay=self.scanning.rate_limit_delay,
            request_timeout=self.scanning.request_timeout,
            max_retries=self.scanning.max_retries,
            concurrent_requests=self.scanning.concurrent_requests,
            custom_headers=self.network.headers,
            follow_redirects=self.scanning.follow_redirects,
            verify_ssl=self.scanning.verify_ssl
        )
