#!/usr/bin/env python3
"""
Storage service for PixelTracker

Handles persistence of scan results, tracker patterns, and other data.
"""

import sqlite3
import json
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from ..interfaces import Storage
from ..models import ScanResult, TrackerPattern
import logging

logger = logging.getLogger(__name__)


class StorageService(Storage):
    """SQLite-based storage service for scan results and tracker patterns"""
    
    def __init__(self, db_path: str = "pixeltracker.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Scan results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    scan_type TEXT NOT NULL,
                    tracker_count INTEGER NOT NULL,
                    privacy_score INTEGER,
                    scan_duration REAL,
                    javascript_enabled BOOLEAN,
                    error TEXT,
                    result_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tracker patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracker_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    patterns TEXT NOT NULL,
                    domains TEXT NOT NULL,
                    description TEXT,
                    data_types TEXT,
                    gdpr_relevant BOOLEAN,
                    ccpa_relevant BOOLEAN,
                    detection_method TEXT,
                    evasion_techniques TEXT,
                    first_seen TEXT,
                    last_updated TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_results_url ON scan_results(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_results_timestamp ON scan_results(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracker_patterns_category ON tracker_patterns(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracker_patterns_risk_level ON tracker_patterns(risk_level)')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    async def store_result(self, result: ScanResult) -> bool:
        """Store a scan result"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._store_result_sync, result)
        except Exception as e:
            logger.error(f"Failed to store result for {result.url}: {e}")
            return False
    
    def _store_result_sync(self, result: ScanResult) -> bool:
        """Synchronous implementation of store_result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Serialize the complete result data
                result_data = json.dumps(result.to_dict(), default=str)
                
                cursor.execute('''
                    INSERT INTO scan_results (
                        url, timestamp, scan_type, tracker_count, privacy_score,
                        scan_duration, javascript_enabled, error, result_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.url,
                    result.timestamp,
                    result.scan_type,
                    result.tracker_count,
                    result.privacy_analysis.privacy_score,
                    result.scan_duration,
                    result.javascript_enabled,
                    result.error,
                    result_data
                ))
                
                conn.commit()
                logger.debug(f"Stored scan result for {result.url}")
                return True
                
        except Exception as e:
            logger.error(f"Database error storing result: {e}")
            return False
    
    async def retrieve_results(
        self, 
        url: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ScanResult]:
        """Retrieve stored scan results"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._retrieve_results_sync, url, limit)
        except Exception as e:
            logger.error(f"Failed to retrieve results: {e}")
            return []
    
    def _retrieve_results_sync(
        self, 
        url: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ScanResult]:
        """Synchronous implementation of retrieve_results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT result_data FROM scan_results"
                params = []
                
                if url:
                    query += " WHERE url = ?"
                    params.append(url)
                
                query += " ORDER BY timestamp DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    try:
                        result_data = json.loads(row[0])
                        scan_result = ScanResult.from_dict(result_data)
                        results.append(scan_result)
                    except Exception as e:
                        logger.warning(f"Failed to deserialize scan result: {e}")
                        continue
                
                logger.debug(f"Retrieved {len(results)} scan results")
                return results
                
        except Exception as e:
            logger.error(f"Database error retrieving results: {e}")
            return []
    
    async def store_tracker_pattern(self, pattern: TrackerPattern) -> bool:
        """Store a tracker pattern"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._store_pattern_sync, pattern)
        except Exception as e:
            logger.error(f"Failed to store tracker pattern {pattern.name}: {e}")
            return False
    
    def _store_pattern_sync(self, pattern: TrackerPattern) -> bool:
        """Synchronous implementation of store_tracker_pattern"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO tracker_patterns (
                        name, category, risk_level, patterns, domains, description,
                        data_types, gdpr_relevant, ccpa_relevant, detection_method,
                        evasion_techniques, first_seen, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern.name,
                    pattern.category.value,
                    pattern.risk_level.value,
                    json.dumps(pattern.patterns),
                    json.dumps(pattern.domains),
                    pattern.description,
                    json.dumps(pattern.data_types),
                    pattern.gdpr_relevant,
                    pattern.ccpa_relevant,
                    pattern.detection_method.value,
                    json.dumps(pattern.evasion_techniques),
                    pattern.first_seen,
                    pattern.last_updated
                ))
                
                conn.commit()
                logger.debug(f"Stored tracker pattern: {pattern.name}")
                return True
                
        except Exception as e:
            logger.error(f"Database error storing tracker pattern: {e}")
            return False
    
    async def get_tracker_patterns(self) -> List[TrackerPattern]:
        """Get all tracker patterns"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_patterns_sync)
        except Exception as e:
            logger.error(f"Failed to retrieve tracker patterns: {e}")
            return []
    
    def _get_patterns_sync(self) -> List[TrackerPattern]:
        """Synchronous implementation of get_tracker_patterns"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT name, category, risk_level, patterns, domains, description,
                           data_types, gdpr_relevant, ccpa_relevant, detection_method,
                           evasion_techniques, first_seen, last_updated
                    FROM tracker_patterns
                    ORDER BY name
                ''')
                
                rows = cursor.fetchall()
                patterns = []
                
                for row in rows:
                    try:
                        pattern = TrackerPattern(
                            name=row[0],
                            category=row[1],
                            risk_level=row[2],
                            patterns=json.loads(row[3]),
                            domains=json.loads(row[4]),
                            description=row[5] or "",
                            data_types=json.loads(row[6]) if row[6] else [],
                            gdpr_relevant=bool(row[7]),
                            ccpa_relevant=bool(row[8]),
                            detection_method=row[9],
                            evasion_techniques=json.loads(row[10]) if row[10] else [],
                            first_seen=row[11] or "",
                            last_updated=row[12] or ""
                        )
                        patterns.append(pattern)
                    except Exception as e:
                        logger.warning(f"Failed to deserialize tracker pattern: {e}")
                        continue
                
                logger.debug(f"Retrieved {len(patterns)} tracker patterns")
                return patterns
                
        except Exception as e:
            logger.error(f"Database error retrieving tracker patterns: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Scan results statistics
                cursor.execute("SELECT COUNT(*) FROM scan_results")
                total_scans = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT url) FROM scan_results")
                unique_urls = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(privacy_score) FROM scan_results WHERE privacy_score IS NOT NULL")
                avg_privacy_score = cursor.fetchone()[0] or 0
                
                # Tracker patterns statistics
                cursor.execute("SELECT COUNT(*) FROM tracker_patterns")
                total_patterns = cursor.fetchone()[0]
                
                cursor.execute("SELECT category, COUNT(*) FROM tracker_patterns GROUP BY category")
                category_counts = dict(cursor.fetchall())
                
                cursor.execute("SELECT risk_level, COUNT(*) FROM tracker_patterns GROUP BY risk_level")
                risk_counts = dict(cursor.fetchall())
                
                return {
                    'total_scans': total_scans,
                    'unique_urls': unique_urls,
                    'average_privacy_score': round(avg_privacy_score, 2),
                    'total_tracker_patterns': total_patterns,
                    'patterns_by_category': category_counts,
                    'patterns_by_risk': risk_counts,
                    'database_path': str(self.db_path),
                    'database_size_mb': round(self.db_path.stat().st_size / (1024 * 1024), 2) if self.db_path.exists() else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {}
    
    def export_data(self, output_path: str, format: str = "json") -> bool:
        """Export all data to file"""
        try:
            if format.lower() == "json":
                return self._export_json(output_path)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False
    
    def _export_json(self, output_path: str) -> bool:
        """Export data to JSON format"""
        try:
            # Get all data
            results = self._retrieve_results_sync()
            patterns = self._get_patterns_sync()
            
            export_data = {
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'total_results': len(results),
                    'total_patterns': len(patterns)
                },
                'scan_results': [result.to_dict() for result in results],
                'tracker_patterns': [pattern.to_dict() for pattern in patterns],
                'statistics': self.get_statistics()
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Data exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            return False
