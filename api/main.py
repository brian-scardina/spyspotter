#!/usr/bin/env python3
"""
FastAPI REST API for PixelTracker

Provides REST endpoints for scanning, results, reports, and statistics.
Includes WebSocket support for real-time scan progress updates.
"""

import os
import sys
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks, Query, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl, validator
import uvicorn

# Add parent directory to path to import pixeltracker modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pixeltracker.models import ScanResult, TrackerInfo, RiskLevel, TrackerCategory, ScanConfiguration
from pixeltracker.scanners import BasicTrackingScanner, EnhancedTrackingScanner
from pixeltracker.persistence.database import DatabaseManager
from pixeltracker.persistence.repositories import ScanRepository, ReportRepository, MetricsRepository

# Pydantic models for API
class ScanRequest(BaseModel):
    url: HttpUrl
    scan_type: str = "basic"
    enable_javascript: bool = False
    enable_ml_analysis: bool = False
    enable_advanced_fingerprinting: bool = False
    
    @validator('scan_type')
    def validate_scan_type(cls, v):
        if v not in ['basic', 'enhanced']:
            raise ValueError('scan_type must be "basic" or "enhanced"')
        return v

class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str
    estimated_duration: Optional[int] = None

class ScanResultResponse(BaseModel):
    scan_id: str
    url: str
    status: str
    timestamp: str
    tracker_count: int
    privacy_score: Optional[int]
    risk_level: Optional[str]
    scan_duration: Optional[float]
    trackers: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    privacy_analysis: Dict[str, Any]
    error: Optional[str] = None

class StatsResponse(BaseModel):
    total_scans: int
    total_trackers_found: int
    avg_privacy_score: float
    most_common_trackers: List[Dict[str, Any]]
    risk_distribution: Dict[str, int]
    daily_scan_count: List[Dict[str, Any]]

# WebSocket connection manager
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, scan_id: str):
        await websocket.accept()
        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = []
        self.active_connections[scan_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, scan_id: str):
        if scan_id in self.active_connections:
            self.active_connections[scan_id].remove(websocket)
            if not self.active_connections[scan_id]:
                del self.active_connections[scan_id]
    
    async def send_progress(self, scan_id: str, data: dict):
        if scan_id in self.active_connections:
            for connection in self.active_connections[scan_id][:]:  # Create copy to avoid modification during iteration
                try:
                    await connection.send_text(json.dumps(data))
                except:
                    # Remove disconnected clients
                    self.active_connections[scan_id].remove(connection)

# Initialize FastAPI app
app = FastAPI(
    title="PixelTracker API",
    description="REST API for privacy tracker scanning and analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
websocket_manager = WebSocketManager()
db_manager = DatabaseManager()
scan_repository = ScanRepository(db_manager)
report_repository = ReportRepository(db_manager)
metrics_repository = MetricsRepository(db_manager)

# Security
security = HTTPBearer(auto_error=False)

# Active scans tracking
active_scans: Dict[str, Dict[str, Any]] = {}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple authentication - replace with proper implementation"""
    # For demo purposes, we'll allow all requests
    # In production, implement proper JWT validation
    return {"user": "demo"}

@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables"""
    db_manager.create_tables()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the dashboard"""
    dashboard_path = Path(__file__).parent / "dashboard" / "index.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    else:
        return HTMLResponse("""
        <html>
            <head><title>PixelTracker API</title></head>
            <body>
                <h1>PixelTracker API</h1>
                <p>API is running! Visit <a href="/docs">/docs</a> for interactive documentation.</p>
                <p>Dashboard will be available once built.</p>
            </body>
        </html>
        """)

@app.post("/api/scan", response_model=ScanResponse)
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new privacy tracking scan
    """
    scan_id = str(uuid.uuid4())
    
    # Create scan configuration
    config = ScanConfiguration(
        enable_javascript=request.enable_javascript,
        enable_ml_analysis=request.enable_ml_analysis,
        enable_advanced_fingerprinting=request.enable_advanced_fingerprinting
    )
    
    # Store scan status
    active_scans[scan_id] = {
        "url": str(request.url),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "scan_type": request.scan_type,
        "config": config.to_dict()
    }
    
    # Start background scan
    background_tasks.add_task(perform_scan, scan_id, str(request.url), request.scan_type, config)
    
    return ScanResponse(
        scan_id=scan_id,
        status="started",
        message="Scan initiated successfully",
        estimated_duration=30 if request.scan_type == "basic" else 60
    )

async def perform_scan(scan_id: str, url: str, scan_type: str, config: ScanConfiguration):
    """Perform the actual scanning in background"""
    try:
        # Update status
        active_scans[scan_id]["status"] = "scanning"
        await websocket_manager.send_progress(scan_id, {
            "scan_id": scan_id,
            "status": "scanning",
            "progress": 10,
            "message": "Starting scan..."
        })
        
        # Initialize appropriate scanner
        if scan_type == "enhanced":
            scanner = EnhancedTrackingScanner()
        else:
            scanner = BasicTrackingScanner()
        
        # Progress callback
        async def progress_callback(progress: int, message: str):
            await websocket_manager.send_progress(scan_id, {
                "scan_id": scan_id,
                "status": "scanning",
                "progress": progress,
                "message": message
            })
        
        # Perform scan with progress updates
        await websocket_manager.send_progress(scan_id, {
            "scan_id": scan_id,
            "status": "scanning",
            "progress": 30,
            "message": "Fetching page content..."
        })
        
        # For now, use sync method and run in thread pool
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, scanner.scan_url_sync, url)
        result.scan_type = scan_type
        
        # Store result in database
        await scan_repository.store_scan_result(result)
        
        # Update status
        active_scans[scan_id]["status"] = "completed"
        active_scans[scan_id]["result"] = result.to_dict()
        
        await websocket_manager.send_progress(scan_id, {
            "scan_id": scan_id,
            "status": "completed",
            "progress": 100,
            "message": "Scan completed successfully",
            "result": result.to_dict()
        })
        
    except Exception as e:
        # Handle scan error
        active_scans[scan_id]["status"] = "failed"
        active_scans[scan_id]["error"] = str(e)
        
        await websocket_manager.send_progress(scan_id, {
            "scan_id": scan_id,
            "status": "failed",
            "progress": 0,
            "message": f"Scan failed: {str(e)}",
            "error": str(e)
        })

@app.get("/api/scan/{scan_id}", response_model=ScanResultResponse)
async def get_scan_result(
    scan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get scan result by ID
    """
    # Check active scans first
    if scan_id in active_scans:
        scan_data = active_scans[scan_id]
        
        if scan_data["status"] == "completed" and "result" in scan_data:
            result_data = scan_data["result"]
            return ScanResultResponse(
                scan_id=scan_id,
                url=result_data["url"],
                status="completed",
                timestamp=result_data["timestamp"],
                tracker_count=result_data.get("tracker_count", 0),
                privacy_score=result_data.get("privacy_analysis", {}).get("privacy_score"),
                risk_level=result_data.get("privacy_analysis", {}).get("risk_level"),
                scan_duration=result_data.get("scan_duration"),
                trackers=[t for t in result_data.get("trackers", [])],
                performance_metrics=result_data.get("performance_metrics", {}),
                privacy_analysis=result_data.get("privacy_analysis", {}),
                error=scan_data.get("error")
            )
        elif scan_data["status"] == "failed":
            return ScanResultResponse(
                scan_id=scan_id,
                url=scan_data["url"],
                status="failed",
                timestamp=scan_data["created_at"],
                tracker_count=0,
                trackers=[],
                performance_metrics={},
                privacy_analysis={},
                error=scan_data.get("error", "Scan failed")
            )
        else:
            return ScanResultResponse(
                scan_id=scan_id,
                url=scan_data["url"],
                status=scan_data["status"],
                timestamp=scan_data["created_at"],
                tracker_count=0,
                trackers=[],
                performance_metrics={},
                privacy_analysis={}
            )
    
    # Check database for historical results
    result = await scan_repository.get_scan_by_id(scan_id)
    if result:
        return ScanResultResponse(
            scan_id=scan_id,
            url=result.url,
            status=result.status,
            timestamp=result.started_at.isoformat(),
            tracker_count=result.tracker_count,
            privacy_score=result.privacy_score,
            risk_level=result.risk_level,
            scan_duration=result.scan_duration,
            trackers=[t.to_dict() for t in result.trackers],
            performance_metrics={
                "response_time": result.response_time,
                "content_length": result.content_length,
                "status_code": result.status_code
            },
            privacy_analysis=result.analysis_results_dict
        )
    
    raise HTTPException(status_code=404, detail="Scan not found")

@app.get("/api/results", response_model=List[ScanResultResponse])
async def get_scan_results(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    url: Optional[str] = None,
    risk_level: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get scan results with pagination and filtering
    """
    # Get results from database
    results = await scan_repository.get_scans(
        limit=limit,
        offset=offset,
        url_filter=url,
        risk_level_filter=risk_level
    )
    
    response_results = []
    for result in results:
        response_results.append(ScanResultResponse(
            scan_id=result.scan_id,
            url=result.url,
            status=result.status,
            timestamp=result.started_at.isoformat(),
            tracker_count=result.tracker_count,
            privacy_score=result.privacy_score,
            risk_level=result.risk_level,
            scan_duration=result.scan_duration,
            trackers=[t.to_dict() for t in result.trackers] if result.trackers else [],
            performance_metrics={
                "response_time": result.response_time,
                "content_length": result.content_length,
                "status_code": result.status_code
            },
            privacy_analysis=result.analysis_results_dict
        ))
    
    return response_results

@app.get("/api/reports/{scan_id}")
async def get_scan_report(
    scan_id: str,
    format: str = Query("json", regex="^(json|html|pdf)$"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get or generate scan report in specified format
    """
    # Check if report already exists
    report = await report_repository.get_report_by_scan_id(scan_id)
    
    if not report:
        # Generate new report
        scan_result = await scan_repository.get_scan_by_id(scan_id)
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Generate report content based on format
        if format == "json":
            report_content = scan_result.analysis_results_dict
        elif format == "html":
            report_content = generate_html_report(scan_result)
        else:  # pdf
            report_content = "PDF generation not implemented yet"
        
        # Store report
        await report_repository.create_report(
            scan_id=scan_id,
            title=f"Privacy Scan Report - {scan_result.url}",
            report_type="scan_report",
            content=report_content,
            format=format
        )
    
    return report.content if report else report_content

@app.get("/api/stats", response_model=StatsResponse)
async def get_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Get scanning statistics and analytics
    """
    # Get metrics from repository
    stats = await metrics_repository.get_statistics(days=days)
    
    return StatsResponse(
        total_scans=stats.get("total_scans", 0),
        total_trackers_found=stats.get("total_trackers_found", 0),
        avg_privacy_score=stats.get("avg_privacy_score", 0.0),
        most_common_trackers=stats.get("most_common_trackers", []),
        risk_distribution=stats.get("risk_distribution", {}),
        daily_scan_count=stats.get("daily_scan_count", [])
    )

@app.websocket("/ws/scan/{scan_id}")
async def websocket_endpoint(websocket: WebSocket, scan_id: str):
    """
    WebSocket endpoint for real-time scan progress updates
    """
    await websocket_manager.connect(websocket, scan_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, scan_id)

def generate_html_report(scan_result) -> str:
    """Generate HTML report from scan result"""
    return f"""
    <html>
    <head>
        <title>Privacy Scan Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .tracker {{ margin: 10px 0; padding: 10px; border-left: 3px solid #007cba; }}
            .risk-high {{ border-left-color: #d32f2f; }}
            .risk-medium {{ border-left-color: #f57c00; }}
            .risk-low {{ border-left-color: #388e3c; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Privacy Scan Report</h1>
            <p><strong>URL:</strong> {scan_result.url}</p>
            <p><strong>Scan Date:</strong> {scan_result.started_at}</p>
            <p><strong>Privacy Score:</strong> {scan_result.privacy_score}/100</p>
            <p><strong>Risk Level:</strong> {scan_result.risk_level}</p>
        </div>
        
        <h2>Detected Trackers ({scan_result.tracker_count})</h2>
        {''.join([f'<div class="tracker risk-{t.risk_level.lower()}"><strong>{t.name}</strong> - {t.category} ({t.risk_level})</div>' for t in scan_result.trackers])}
        
        <h2>Performance Metrics</h2>
        <p>Response Time: {scan_result.response_time}ms</p>
        <p>Content Size: {scan_result.content_length} bytes</p>
        <p>Status Code: {scan_result.status_code}</p>
    </body>
    </html>
    """

# Mount static files for dashboard
dashboard_path = Path(__file__).parent / "dashboard" / "build"
if dashboard_path.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_path / "static")), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
