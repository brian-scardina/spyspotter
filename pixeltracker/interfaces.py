#!/usr/bin/env python3
"""
Core interfaces and abstract base classes for PixelTracker

These interfaces define the contracts for all major components,
enabling dependency injection, testing, and modularity.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Protocol, runtime_checkable
from .models import ScanResult, TrackerInfo, TrackerPattern


@runtime_checkable
class Fetcher(Protocol):
    """Interface for fetching web content"""
    
    async def fetch(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch content from a URL
        
        Args:
            url: The URL to fetch
            **kwargs: Additional fetch options
            
        Returns:
            Dict containing content and metadata
        """
        ...
    
    def set_headers(self, headers: Dict[str, str]) -> None:
        """Set default headers for requests"""
        ...
    
    def set_timeout(self, timeout: float) -> None:
        """Set request timeout"""
        ...


@runtime_checkable
class Parser(Protocol):
    """Interface for parsing HTML content"""
    
    def parse(self, content: str, url: str = "") -> Dict[str, Any]:
        """
        Parse HTML content for tracking elements
        
        Args:
            content: HTML content to parse
            url: Source URL for context
            
        Returns:
            Dict containing parsed tracking data
        """
        ...
    
    def find_tracking_pixels(self, content: str) -> List[Dict[str, Any]]:
        """Find tracking pixels in content"""
        ...
    
    def find_javascript_trackers(self, content: str) -> List[Dict[str, Any]]:
        """Find JavaScript tracking code"""
        ...
    
    def find_meta_trackers(self, content: str) -> List[Dict[str, Any]]:
        """Find tracking meta tags"""
        ...


@runtime_checkable
class Storage(Protocol):
    """Interface for data storage operations"""
    
    async def store_result(self, result: ScanResult) -> bool:
        """Store scan result"""
        ...
    
    async def retrieve_results(
        self, 
        url: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ScanResult]:
        """Retrieve stored results"""
        ...
    
    async def store_tracker_pattern(self, pattern: TrackerPattern) -> bool:
        """Store tracker pattern"""
        ...
    
    async def get_tracker_patterns(self) -> List[TrackerPattern]:
        """Get all tracker patterns"""
        ...


@runtime_checkable
class Analyzer(Protocol):
    """Interface for analyzing tracking data"""
    
    def analyze_privacy_impact(
        self, 
        trackers: List[TrackerInfo], 
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze privacy impact of detected trackers"""
        ...
    
    def calculate_privacy_score(
        self, 
        trackers: List[TrackerInfo], 
        **kwargs
    ) -> int:
        """Calculate privacy score (0-100)"""
        ...
    
    def assess_risks(
        self, 
        trackers: List[TrackerInfo], 
        url: str
    ) -> Dict[str, Any]:
        """Assess privacy and security risks"""
        ...


@runtime_checkable
class Reporter(Protocol):
    """Interface for generating reports"""
    
    def generate_report(
        self, 
        results: List[ScanResult], 
        format: str = "json"
    ) -> str:
        """Generate report in specified format"""
        ...
    
    def generate_summary(self, results: List[ScanResult]) -> Dict[str, Any]:
        """Generate summary statistics"""
        ...
    
    def export_data(
        self, 
        results: List[ScanResult], 
        format: str,
        output_path: str
    ) -> bool:
        """Export data to file"""
        ...


# Abstract base classes for concrete implementations

class AbstractFetcher(ABC):
    """Abstract base class for content fetchers"""
    
    def __init__(self):
        self._headers: Dict[str, str] = {}
        self._timeout: float = 30.0
    
    @abstractmethod
    async def fetch(self, url: str, **kwargs) -> Dict[str, Any]:
        """Fetch content from URL"""
        pass
    
    def set_headers(self, headers: Dict[str, str]) -> None:
        """Set default headers"""
        self._headers.update(headers)
    
    def set_timeout(self, timeout: float) -> None:
        """Set request timeout"""
        self._timeout = timeout


class AbstractParser(ABC):
    """Abstract base class for content parsers"""
    
    @abstractmethod
    def parse(self, content: str, url: str = "") -> Dict[str, Any]:
        """Parse content for tracking elements"""
        pass
    
    @abstractmethod
    def find_tracking_pixels(self, content: str) -> List[Dict[str, Any]]:
        """Find tracking pixels"""
        pass
    
    @abstractmethod
    def find_javascript_trackers(self, content: str) -> List[Dict[str, Any]]:
        """Find JavaScript trackers"""
        pass
    
    @abstractmethod
    def find_meta_trackers(self, content: str) -> List[Dict[str, Any]]:
        """Find meta tag trackers"""
        pass


class AbstractStorage(ABC):
    """Abstract base class for storage implementations"""
    
    @abstractmethod
    async def store_result(self, result: ScanResult) -> bool:
        """Store scan result"""
        pass
    
    @abstractmethod
    async def retrieve_results(
        self, 
        url: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ScanResult]:
        """Retrieve results"""
        pass
    
    @abstractmethod
    async def store_tracker_pattern(self, pattern: TrackerPattern) -> bool:
        """Store tracker pattern"""
        pass
    
    @abstractmethod
    async def get_tracker_patterns(self) -> List[TrackerPattern]:
        """Get tracker patterns"""
        pass


class AbstractAnalyzer(ABC):
    """Abstract base class for analyzers"""
    
    @abstractmethod
    def analyze_privacy_impact(
        self, 
        trackers: List[TrackerInfo], 
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze privacy impact"""
        pass
    
    @abstractmethod
    def calculate_privacy_score(
        self, 
        trackers: List[TrackerInfo], 
        **kwargs
    ) -> int:
        """Calculate privacy score"""
        pass
    
    @abstractmethod
    def assess_risks(
        self, 
        trackers: List[TrackerInfo], 
        url: str
    ) -> Dict[str, Any]:
        """Assess risks"""
        pass


class AbstractReporter(ABC):
    """Abstract base class for reporters"""
    
    @abstractmethod
    def generate_report(
        self, 
        results: List[ScanResult], 
        format: str = "json"
    ) -> str:
        """Generate report"""
        pass
    
    @abstractmethod
    def generate_summary(self, results: List[ScanResult]) -> Dict[str, Any]:
        """Generate summary"""
        pass
    
    @abstractmethod
    def export_data(
        self, 
        results: List[ScanResult], 
        format: str,
        output_path: str
    ) -> bool:
        """Export data"""
        pass


# Factory interface for creating service instances
class ServiceFactory(ABC):
    """Factory for creating service instances"""
    
    @abstractmethod
    def create_fetcher(self, **kwargs) -> Fetcher:
        """Create fetcher instance"""
        pass
    
    @abstractmethod
    def create_parser(self, **kwargs) -> Parser:
        """Create parser instance"""
        pass
    
    @abstractmethod
    def create_storage(self, **kwargs) -> Storage:
        """Create storage instance"""
        pass
    
    @abstractmethod
    def create_analyzer(self, **kwargs) -> Analyzer:
        """Create analyzer instance"""
        pass
    
    @abstractmethod
    def create_reporter(self, **kwargs) -> Reporter:
        """Create reporter instance"""
        pass
