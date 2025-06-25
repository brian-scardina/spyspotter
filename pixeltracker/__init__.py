#!/usr/bin/env python3
"""
PixelTracker - Advanced tracking pixel detection library

A comprehensive toolkit for detecting and analyzing tracking technologies
across websites and web applications.
"""

__version__ = "2.0.0"
__author__ = "PixelTracker Team"
__license__ = "MIT"

# Core interfaces
from .interfaces import Fetcher, Parser, Storage, Analyzer, Reporter

# Core services
from .services.network import NetworkService
from .services.parser import HTMLParserService
from .services.storage import StorageService
from .services.analyzer import AnalyzerService
from .services.reporter import ReporterService

# Scanner implementations
from .scanners.basic import BasicTrackingScanner
from .scanners.enhanced import EnhancedTrackingScanner

# Configuration and utilities
from .config import ConfigManager
from .models import TrackerInfo, ScanResult, TrackerPattern

__all__ = [
    # Interfaces
    'Fetcher', 'Parser', 'Storage', 'Analyzer', 'Reporter',
    
    # Services
    'NetworkService', 'HTMLParserService', 'StorageService', 
    'AnalyzerService', 'ReporterService',
    
    # Scanners
    'BasicTrackingScanner', 'EnhancedTrackingScanner',
    
    # Configuration and models
    'ConfigManager', 'TrackerInfo', 'ScanResult', 'TrackerPattern',
    
    # Metadata
    '__version__', '__author__', '__license__'
]
