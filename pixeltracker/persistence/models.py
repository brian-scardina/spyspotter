#!/usr/bin/env python3
"""
SQLAlchemy ORM models for PixelTracker persistence layer
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import json
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Table, Index, JSON, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.sql import func
import uuid

# Base class for all models
Base = declarative_base()

# Association table for many-to-many relationship between scans and trackers
scan_tracker_association = Table(
    'scan_tracker_association',
    Base.metadata,
    Column('scan_id', Integer, ForeignKey('scans.id'), primary_key=True),
    Column('tracker_id', Integer, ForeignKey('trackers.id'), primary_key=True),
    Column('confidence', Float, default=1.0),
    Column('detected_at', DateTime, default=func.now())
)

class Domain(Base):
    """Domain model for tracking domain-related information"""
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(50))  # analytics, advertising, etc.
    risk_level = Column(String(20))  # low, medium, high, critical
    is_known_tracker = Column(Boolean, default=False)
    
    # Metadata
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    scan_count = Column(Integer, default=0)
    
    # Additional domain information
    whois_data = Column(Text)  # JSON string
    dns_records = Column(Text)  # JSON string
    ssl_info = Column(Text)  # JSON string
    
    # Privacy compliance
    gdpr_relevant = Column(Boolean, default=False)
    ccpa_relevant = Column(Boolean, default=False)
    
    # Relationships
    trackers = relationship("Tracker", back_populates="domain")
    
    def __repr__(self):
        return f"<Domain(name='{self.name}', category='{self.category}')>"
    
    @property
    def whois_dict(self) -> Dict[str, Any]:
        """Return whois data as dictionary"""
        return json.loads(self.whois_data) if self.whois_data else {}
    
    @whois_dict.setter
    def whois_dict(self, value: Dict[str, Any]):
        """Set whois data from dictionary"""
        self.whois_data = json.dumps(value) if value else None
    
    @property
    def dns_dict(self) -> Dict[str, Any]:
        """Return DNS records as dictionary"""
        return json.loads(self.dns_records) if self.dns_records else {}
    
    @dns_dict.setter
    def dns_dict(self, value: Dict[str, Any]):
        """Set DNS records from dictionary"""
        self.dns_records = json.dumps(value) if value else None

class Tracker(Base):
    """Tracker model for tracking pixel and script information"""
    __tablename__ = 'trackers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    tracker_type = Column(String(50), nullable=False)  # pixel, script, etc.
    category = Column(String(50), nullable=False)  # analytics, advertising, etc.
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Domain relationship
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False)
    domain = relationship("Domain", back_populates="trackers")
    
    # Pattern information
    url_patterns = Column(Text)  # JSON array of URL patterns
    detection_patterns = Column(Text)  # JSON array of detection patterns
    detection_method = Column(String(50))  # javascript, pixel, meta, css, network
    
    # Privacy and compliance
    purpose = Column(Text)
    data_types_collected = Column(Text)  # JSON array
    gdpr_relevant = Column(Boolean, default=False)
    ccpa_relevant = Column(Boolean, default=False)
    
    # Evasion techniques
    evasion_techniques = Column(Text)  # JSON array
    obfuscation_methods = Column(Text)  # JSON array
    
    # Metadata
    first_seen = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now())
    confidence_score = Column(Float, default=1.0)
    
    # Relationships
    scans = relationship("Scan", secondary=scan_tracker_association, back_populates="trackers")
    
    # Indexes
    __table_args__ = (
        Index('idx_tracker_category', 'category'),
        Index('idx_tracker_risk_level', 'risk_level'),
        Index('idx_tracker_type', 'tracker_type'),
    )
    
    def __repr__(self):
        return f"<Tracker(name='{self.name}', type='{self.tracker_type}')>"
    
    @property
    def url_patterns_list(self) -> List[str]:
        """Return URL patterns as list"""
        return json.loads(self.url_patterns) if self.url_patterns else []
    
    @url_patterns_list.setter
    def url_patterns_list(self, value: List[str]):
        """Set URL patterns from list"""
        self.url_patterns = json.dumps(value) if value else None
    
    @property
    def detection_patterns_list(self) -> List[str]:
        """Return detection patterns as list"""
        return json.loads(self.detection_patterns) if self.detection_patterns else []
    
    @detection_patterns_list.setter
    def detection_patterns_list(self, value: List[str]):
        """Set detection patterns from list"""
        self.detection_patterns = json.dumps(value) if value else None

class Scan(Base):
    """Scan model for storing scan results"""
    __tablename__ = 'scans'
    
    id = Column(Integer, primary_key=True)
    
    # Scan identification
    scan_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    url = Column(String(2048), nullable=False, index=True)
    
    # Scan configuration
    scan_type = Column(String(20), default='basic')  # basic, enhanced
    javascript_enabled = Column(Boolean, default=False)
    user_agent = Column(String(512))
    
    # Timing information
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    scan_duration = Column(Float)  # in seconds
    
    # Results summary
    status = Column(String(20), default='pending')  # pending, completed, failed
    tracker_count = Column(Integer, default=0)
    unique_domains_count = Column(Integer, default=0)
    privacy_score = Column(Integer)
    risk_level = Column(String(20))  # low, medium, high, critical
    
    # Performance metrics
    response_time = Column(Float)
    content_length = Column(Integer)
    status_code = Column(Integer)
    redirect_count = Column(Integer, default=0)
    
    # Network timing
    dns_lookup_time = Column(Float)
    connect_time = Column(Float)
    ssl_handshake_time = Column(Float)
    
    # Error information
    error_message = Column(Text)
    error_details = Column(Text)  # JSON string
    
    # Raw data storage
    raw_html = Column(LargeBinary)  # Compressed HTML content
    raw_network_data = Column(Text)  # JSON string of network requests
    screenshot_data = Column(LargeBinary)  # Screenshot if available
    
    # Analysis results
    analysis_results = Column(Text)  # JSON string of detailed analysis
    recommendations = Column(Text)  # JSON array of recommendations
    compliance_status = Column(Text)  # JSON dict of compliance checks
    
    # Caching support
    etag = Column(String(128))
    last_modified = Column(DateTime)
    cache_hit = Column(Boolean, default=False)
    
    # Relationships
    trackers = relationship("Tracker", secondary=scan_tracker_association, back_populates="scans")
    reports = relationship("Report", back_populates="scan")
    
    # Indexes
    __table_args__ = (
        Index('idx_scan_url', 'url'),
        Index('idx_scan_started_at', 'started_at'),
        Index('idx_scan_status', 'status'),
        Index('idx_scan_privacy_score', 'privacy_score'),
        Index('idx_scan_etag', 'etag'),
    )
    
    def __repr__(self):
        return f"<Scan(url='{self.url}', status='{self.status}')>"
    
    @validates('url')
    def validate_url(self, key, address):
        """Validate URL format"""
        if not address or len(address) < 1:
            raise ValueError("URL cannot be empty")
        return address
    
    @property
    def error_details_dict(self) -> Dict[str, Any]:
        """Return error details as dictionary"""
        return json.loads(self.error_details) if self.error_details else {}
    
    @error_details_dict.setter
    def error_details_dict(self, value: Dict[str, Any]):
        """Set error details from dictionary"""
        self.error_details = json.dumps(value) if value else None
    
    @property
    def analysis_results_dict(self) -> Dict[str, Any]:
        """Return analysis results as dictionary"""
        return json.loads(self.analysis_results) if self.analysis_results else {}
    
    @analysis_results_dict.setter
    def analysis_results_dict(self, value: Dict[str, Any]):
        """Set analysis results from dictionary"""
        self.analysis_results = json.dumps(value) if value else None
    
    @property
    def is_completed(self) -> bool:
        """Check if scan is completed"""
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """Check if scan failed"""
        return self.status == 'failed'

class Report(Base):
    """Report model for storing generated reports"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    
    # Report identification
    report_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # summary, detailed, compliance, etc.
    
    # Report relationship
    scan_id = Column(Integer, ForeignKey('scans.id'), nullable=False)
    scan = relationship("Scan", back_populates="reports")
    
    # Report content
    summary = Column(Text)
    content = Column(Text)  # Main report content (HTML, JSON, etc.)
    format = Column(String(20), default='html')  # html, json, pdf, csv
    
    # Metadata
    generated_at = Column(DateTime, default=func.now())
    generated_by = Column(String(100))  # User or system that generated report
    file_path = Column(String(512))  # Path to saved report file
    file_size = Column(Integer)  # Size in bytes
    
    # Report parameters
    parameters = Column(Text)  # JSON string of report generation parameters
    template_used = Column(String(100))
    
    # Access control
    is_public = Column(Boolean, default=False)
    access_token = Column(String(128))  # For shared reports
    expires_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_report_scan_id', 'scan_id'),
        Index('idx_report_type', 'report_type'),
        Index('idx_report_generated_at', 'generated_at'),
    )
    
    def __repr__(self):
        return f"<Report(title='{self.title}', type='{self.report_type}')>"
    
    @property
    def parameters_dict(self) -> Dict[str, Any]:
        """Return parameters as dictionary"""
        return json.loads(self.parameters) if self.parameters else {}
    
    @parameters_dict.setter
    def parameters_dict(self, value: Dict[str, Any]):
        """Set parameters from dictionary"""
        self.parameters = json.dumps(value) if value else None
    
    @property
    def is_expired(self) -> bool:
        """Check if report has expired"""
        return self.expires_at and datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)

# Additional utility models

class CacheEntry(Base):
    """Cache entry model for storing cached scan results"""
    __tablename__ = 'cache_entries'
    
    id = Column(Integer, primary_key=True)
    cache_key = Column(String(128), unique=True, nullable=False, index=True)
    url = Column(String(2048), nullable=False, index=True)
    
    # Cache metadata
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False, index=True)
    last_accessed = Column(DateTime, default=func.now())
    access_count = Column(Integer, default=0)
    
    # HTTP caching support
    etag = Column(String(128))
    last_modified = Column(DateTime)
    
    # Cached data
    scan_result = Column(Text)  # JSON serialized scan result
    compressed_data = Column(LargeBinary)  # Compressed scan data
    
    # Cache statistics
    hit_count = Column(Integer, default=0)
    miss_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<CacheEntry(key='{self.cache_key}', url='{self.url}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)
    
    def touch(self):
        """Update last accessed time and increment access count"""
        self.last_accessed = func.now()
        self.access_count += 1

class ScanMetrics(Base):
    """Model for storing scan performance metrics and statistics"""
    __tablename__ = 'scan_metrics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now(), index=True)
    
    # Daily aggregated metrics
    total_scans = Column(Integer, default=0)
    successful_scans = Column(Integer, default=0)
    failed_scans = Column(Integer, default=0)
    avg_scan_duration = Column(Float)
    avg_privacy_score = Column(Float)
    
    # Tracker statistics
    total_trackers_found = Column(Integer, default=0)
    unique_domains_found = Column(Integer, default=0)
    high_risk_trackers = Column(Integer, default=0)
    
    # Cache statistics
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    cache_hit_ratio = Column(Float)
    
    # Performance metrics
    avg_response_time = Column(Float)
    avg_content_size = Column(Integer)
    
    def __repr__(self):
        return f"<ScanMetrics(date='{self.date}', total_scans={self.total_scans})>"
