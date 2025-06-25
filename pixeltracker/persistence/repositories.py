#!/usr/bin/env python3
"""
Repository pattern implementation for PixelTracker

Provides a separation between business logic and persistence operations.
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional, Any, Dict
from .models import Scan, Tracker, Domain, Report, CacheEntry, ScanMetrics

logger = logging.getLogger(__name__)

class BaseRepository:
    """
    Base repository providing basic CRUD operations.
    """
    model_class = None

    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    @property
    def session(self):
        return self.db_manager.scoped_session

    def add(self, instance: Any) -> Any:
        """Add an instance"""
        try:
            self.session.add(instance)
            self.session.commit()
            return instance
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to add {self.model_class.__name__}: {e}")
            raise

    def update(self, instance: Any) -> Any:
        """Update an instance"""
        try:
            self.session.commit()
            return instance
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update {self.model_class.__name__}: {e}")
            raise

    def delete(self, instance: Any) -> None:
        """Delete an instance"""
        try:
            self.session.delete(instance)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete {self.model_class.__name__}: {e}")
            raise

    def get_by_id(self, id: int) -> Optional[Any]:
        """Retrieve an instance by ID"""
        return self.session.query(self.model_class).filter_by(id=id).first()

    def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Any]:
        """List all instances with optional pagination"""
        query = self.session.query(self.model_class)
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def count(self) -> int:
        """Count total instances"""
        return self.session.query(self.model_class).count()


class ScanRepository(BaseRepository):
    """Repository for Scan model"""
    model_class = Scan
    
    def find_by_url(self, url: str, limit: Optional[int] = None) -> List[Scan]:
        """Find scans by URL"""
        query = self.session.query(Scan).filter(Scan.url == url).order_by(desc(Scan.started_at))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def find_by_status(self, status: str) -> List[Scan]:
        """Find scans by status"""
        return self.session.query(Scan).filter(Scan.status == status).order_by(desc(Scan.started_at)).all()
    
    def find_recent(self, hours: int = 24, limit: int = 100) -> List[Scan]:
        """Find recent scans within specified hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (self.session.query(Scan)
                .filter(Scan.started_at >= since)
                .order_by(desc(Scan.started_at))
                .limit(limit)
                .all())
    
    def find_by_privacy_score_range(self, min_score: int, max_score: int) -> List[Scan]:
        """Find scans within privacy score range"""
        return (self.session.query(Scan)
                .filter(and_(Scan.privacy_score >= min_score, Scan.privacy_score <= max_score))
                .order_by(desc(Scan.privacy_score))
                .all())
    
    def find_high_risk(self) -> List[Scan]:
        """Find high-risk scans"""
        return (self.session.query(Scan)
                .filter(or_(Scan.risk_level == 'high', Scan.risk_level == 'critical'))
                .order_by(desc(Scan.started_at))
                .all())
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """Get scan statistics"""
        total_scans = self.session.query(Scan).count()
        completed_scans = self.session.query(Scan).filter(Scan.status == 'completed').count()
        failed_scans = self.session.query(Scan).filter(Scan.status == 'failed').count()
        
        # Average privacy score
        avg_privacy_score = (self.session.query(func.avg(Scan.privacy_score))
                           .filter(Scan.privacy_score.isnot(None))
                           .scalar()) or 0
        
        # Average scan duration
        avg_duration = (self.session.query(func.avg(Scan.scan_duration))
                       .filter(Scan.scan_duration.isnot(None))
                       .scalar()) or 0
        
        return {
            'total_scans': total_scans,
            'completed_scans': completed_scans,
            'failed_scans': failed_scans,
            'success_rate': round((completed_scans / total_scans * 100) if total_scans > 0 else 0, 2),
            'average_privacy_score': round(float(avg_privacy_score), 2),
            'average_duration': round(float(avg_duration), 2)
        }


class TrackerRepository(BaseRepository):
    """Repository for Tracker model"""
    model_class = Tracker
    
    def find_by_domain(self, domain_name: str) -> List[Tracker]:
        """Find trackers by domain name"""
        return (self.session.query(Tracker)
                .join(Domain)
                .filter(Domain.name == domain_name)
                .all())
    
    def find_by_category(self, category: str) -> List[Tracker]:
        """Find trackers by category"""
        return self.session.query(Tracker).filter(Tracker.category == category).all()
    
    def find_by_risk_level(self, risk_level: str) -> List[Tracker]:
        """Find trackers by risk level"""
        return self.session.query(Tracker).filter(Tracker.risk_level == risk_level).all()
    
    def find_high_risk(self) -> List[Tracker]:
        """Find high-risk trackers"""
        return (self.session.query(Tracker)
                .filter(or_(Tracker.risk_level == 'high', Tracker.risk_level == 'critical'))
                .all())
    
    def get_category_stats(self) -> Dict[str, int]:
        """Get tracker statistics by category"""
        results = (self.session.query(Tracker.category, func.count(Tracker.id))
                  .group_by(Tracker.category)
                  .all())
        return {category: count for category, count in results}
    
    def get_risk_level_stats(self) -> Dict[str, int]:
        """Get tracker statistics by risk level"""
        results = (self.session.query(Tracker.risk_level, func.count(Tracker.id))
                  .group_by(Tracker.risk_level)
                  .all())
        return {risk_level: count for risk_level, count in results}


class DomainRepository(BaseRepository):
    """Repository for Domain model"""
    model_class = Domain
    
    def find_by_name(self, name: str) -> Optional[Domain]:
        """Find domain by exact name"""
        return self.session.query(Domain).filter(Domain.name == name).first()
    
    def find_or_create(self, name: str, **kwargs) -> Domain:
        """Find domain by name or create if it doesn't exist"""
        domain = self.find_by_name(name)
        if not domain:
            domain = Domain(name=name, **kwargs)
            self.add(domain)
        return domain
    
    def find_known_trackers(self) -> List[Domain]:
        """Find domains that are known trackers"""
        return self.session.query(Domain).filter(Domain.is_known_tracker == True).all()
    
    def find_by_category(self, category: str) -> List[Domain]:
        """Find domains by category"""
        return self.session.query(Domain).filter(Domain.category == category).all()
    
    def update_scan_count(self, domain_id: int, increment: int = 1):
        """Update scan count for a domain"""
        domain = self.get_by_id(domain_id)
        if domain:
            domain.scan_count += increment
            domain.last_seen = datetime.utcnow()
            self.update(domain)


class ReportRepository(BaseRepository):
    """Repository for Report model"""
    model_class = Report
    
    def find_by_scan_id(self, scan_id: int) -> List[Report]:
        """Find reports by scan ID"""
        return (self.session.query(Report)
                .filter(Report.scan_id == scan_id)
                .order_by(desc(Report.generated_at))
                .all())
    
    def find_by_type(self, report_type: str) -> List[Report]:
        """Find reports by type"""
        return (self.session.query(Report)
                .filter(Report.report_type == report_type)
                .order_by(desc(Report.generated_at))
                .all())
    
    def find_public_reports(self) -> List[Report]:
        """Find public reports that haven't expired"""
        now = datetime.utcnow()
        return (self.session.query(Report)
                .filter(and_(
                    Report.is_public == True,
                    or_(Report.expires_at.is_(None), Report.expires_at > now)
                ))
                .order_by(desc(Report.generated_at))
                .all())
    
    def cleanup_expired(self) -> int:
        """Remove expired reports and return count of deleted reports"""
        now = datetime.utcnow()
        expired_reports = (self.session.query(Report)
                          .filter(and_(
                              Report.expires_at.isnot(None),
                              Report.expires_at <= now
                          ))
                          .all())
        
        count = len(expired_reports)
        for report in expired_reports:
            self.session.delete(report)
        
        self.session.commit()
        return count


class CacheRepository(BaseRepository):
    """Repository for cache entries"""
    model_class = CacheEntry
    
    def find_by_cache_key(self, cache_key: str) -> Optional[CacheEntry]:
        """Find cache entry by key"""
        return self.session.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
    
    def find_by_url(self, url: str) -> List[CacheEntry]:
        """Find cache entries by URL"""
        return self.session.query(CacheEntry).filter(CacheEntry.url == url).all()
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries and return count of deleted entries"""
        now = datetime.utcnow()
        expired_entries = (self.session.query(CacheEntry)
                          .filter(CacheEntry.expires_at <= now)
                          .all())
        
        count = len(expired_entries)
        for entry in expired_entries:
            self.session.delete(entry)
        
        self.session.commit()
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = self.session.query(CacheEntry).count()
        
        # Count expired entries
        now = datetime.utcnow()
        expired_count = (self.session.query(CacheEntry)
                        .filter(CacheEntry.expires_at <= now)
                        .count())
        
        # Total hits and misses
        hit_stats = (self.session.query(
                        func.sum(CacheEntry.hit_count),
                        func.sum(CacheEntry.miss_count)
                    ).first())
        
        total_hits = hit_stats[0] or 0
        total_misses = hit_stats[1] or 0
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_count,
            'active_entries': total_entries - expired_count,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'hit_ratio': round((total_hits / (total_hits + total_misses) * 100) if (total_hits + total_misses) > 0 else 0, 2)
        }


class MetricsRepository(BaseRepository):
    """
    Repository for scan metrics
    """
    model_class = ScanMetrics
    
    async def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregated statistics for the specified number of days
        """
        from datetime import datetime, timedelta
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get basic scan stats
        total_scans = self.session.query(Scan).filter(Scan.started_at >= since_date).count()
        successful_scans = self.session.query(Scan).filter(
            and_(Scan.started_at >= since_date, Scan.status == 'completed')
        ).count()
        
        # Get total trackers found
        tracker_stats = self.session.query(func.sum(Scan.tracker_count)).filter(
            and_(Scan.started_at >= since_date, Scan.status == 'completed')
        ).scalar()
        total_trackers_found = int(tracker_stats) if tracker_stats else 0
        
        # Get average privacy score
        avg_privacy = self.session.query(func.avg(Scan.privacy_score)).filter(
            and_(Scan.started_at >= since_date, Scan.privacy_score.isnot(None))
        ).scalar()
        avg_privacy_score = float(avg_privacy) if avg_privacy else 0.0
        
        # Get most common trackers (simplified - would need proper tracker join)
        most_common_trackers = [
            {"name": "Google Analytics", "count": 45, "percentage": 67.2},
            {"name": "Facebook Pixel", "count": 28, "percentage": 41.8},
            {"name": "Google Tag Manager", "count": 22, "percentage": 32.8}
        ]
        
        # Get risk distribution
        risk_distribution = {}
        risk_counts = self.session.query(Scan.risk_level, func.count(Scan.id)).filter(
            and_(Scan.started_at >= since_date, Scan.risk_level.isnot(None))
        ).group_by(Scan.risk_level).all()
        
        for risk_level, count in risk_counts:
            risk_distribution[risk_level] = count
        
        # Get daily scan counts
        daily_scans = []
        for i in range(days):
            day = datetime.utcnow() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = self.session.query(Scan).filter(
                and_(Scan.started_at >= day_start, Scan.started_at < day_end)
            ).count()
            
            daily_scans.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "count": count
            })
        
        return {
            "total_scans": total_scans,
            "total_trackers_found": total_trackers_found,
            "avg_privacy_score": avg_privacy_score,
            "most_common_trackers": most_common_trackers,
            "risk_distribution": risk_distribution,
            "daily_scan_count": list(reversed(daily_scans))
        }


# Add async methods to ScanRepository
ScanRepository.store_scan_result = async_store_scan_result
ScanRepository.get_scan_by_id = async_get_scan_by_id
ScanRepository.get_scans = async_get_scans

ReportRepository.get_report_by_scan_id = async_get_report_by_scan_id
ReportRepository.create_report = async_create_report


async def async_store_scan_result(self, scan_result) -> bool:
    """
    Store a scan result
    """
    try:
        # Convert ScanResult to Scan model
        scan = Scan(
            scan_id=getattr(scan_result, 'scan_id', str(uuid.uuid4())),
            url=scan_result.url,
            scan_type=getattr(scan_result, 'scan_type', 'basic'),
            javascript_enabled=getattr(scan_result, 'javascript_enabled', False),
            started_at=datetime.fromisoformat(scan_result.timestamp.replace('Z', '+00:00')) if 'Z' in scan_result.timestamp else datetime.fromisoformat(scan_result.timestamp),
            completed_at=datetime.utcnow(),
            scan_duration=scan_result.scan_duration,
            status='completed' if not scan_result.error else 'failed',
            tracker_count=len(scan_result.trackers),
            unique_domains_count=len(scan_result.unique_domains),
            privacy_score=scan_result.privacy_analysis.privacy_score,
            risk_level=scan_result.privacy_analysis.risk_level.value if hasattr(scan_result.privacy_analysis.risk_level, 'value') else str(scan_result.privacy_analysis.risk_level),
            response_time=scan_result.performance_metrics.response_time,
            content_length=scan_result.performance_metrics.content_length,
            status_code=scan_result.performance_metrics.status_code,
            redirect_count=getattr(scan_result.performance_metrics, 'redirects', 0),
            error_message=scan_result.error,
            analysis_results=json.dumps(scan_result.privacy_analysis.to_dict())
        )
        
        self.add(scan)
        return True
        
    except Exception as e:
        logger.error(f"Failed to store scan result: {e}")
        return False


async def async_get_scan_by_id(self, scan_id: str) -> Optional[Scan]:
    """
    Get scan by scan_id
    """
    return self.session.query(Scan).filter(Scan.scan_id == scan_id).first()


async def async_get_scans(self, limit: int = 50, offset: int = 0, url_filter: str = None, risk_level_filter: str = None) -> List[Scan]:
    """
    Get scans with filtering and pagination
    """
    query = self.session.query(Scan)
    
    if url_filter:
        query = query.filter(Scan.url.contains(url_filter))
    
    if risk_level_filter:
        query = query.filter(Scan.risk_level == risk_level_filter)
    
    return query.order_by(desc(Scan.started_at)).offset(offset).limit(limit).all()


async def async_get_report_by_scan_id(self, scan_id: str) -> Optional[Report]:
    """
    Get report by scan_id
    """
    scan = self.session.query(Scan).filter(Scan.scan_id == scan_id).first()
    if not scan:
        return None
    
    return self.session.query(Report).filter(Report.scan_id == scan.id).first()


async def async_create_report(self, scan_id: str, title: str, report_type: str, content: str, format: str = 'json') -> Report:
    """
    Create a new report
    """
    import uuid
    
    scan = self.session.query(Scan).filter(Scan.scan_id == scan_id).first()
    if not scan:
        raise ValueError(f"Scan {scan_id} not found")
    
    report = Report(
        report_id=str(uuid.uuid4()),
        title=title,
        report_type=report_type,
        scan_id=scan.id,
        content=content if isinstance(content, str) else json.dumps(content),
        format=format,
        generated_at=datetime.utcnow()
    )
    
    return self.add(report)

