# PixelTracker REST API & Interactive Dashboard

This document describes the REST API and interactive web dashboard for PixelTracker - a comprehensive privacy tracking scanner.

## Features

### 🚀 REST API (FastAPI)
- **OpenAPI Documentation**: Auto-generated interactive docs at `/docs`
- **Four Core Endpoints**:
  - `POST /api/scan` - Start new privacy scans
  - `GET /api/results` - Retrieve scan results with pagination/filtering
  - `GET /api/reports/{scan_id}` - Generate reports (JSON/HTML/PDF)
  - `GET /api/stats` - Get analytics and statistics
- **WebSocket Support**: Real-time scan progress updates at `/ws/scan/{scan_id}`
- **CORS Enabled**: Ready for cross-origin requests
- **SQLite/PostgreSQL**: Flexible database backend support

### 📊 Interactive Dashboard (React + TypeScript)
- **Real-time Monitoring**: Live scan status and progress tracking
- **Rich Visualizations**: Charts powered by Recharts library
  - Historical tracker trends over time
  - Privacy score distributions
  - Domain activity heatmaps
  - Risk level breakdowns
- **Responsive Design**: Material-UI components for mobile/desktop
- **Data Grid**: Advanced filtering and sorting of scan results
- **Drill-down Pages**: Detailed view for individual URL scans

## Architecture

```
PixelTracker/
├── api/
│   ├── main.py              # FastAPI application
│   └── dashboard/           # React SPA
│       ├── src/
│       │   ├── pages/       # Dashboard, Scan, Results, Stats
│       │   ├── components/  # Reusable UI components
│       │   └── services/    # API client & WebSocket
│       └── build/           # Production build (served by FastAPI)
├── pixeltracker/           # Core scanning engine
│   ├── models.py           # Data models
│   ├── persistence/        # Database layer
│   └── scanners/           # Scanning implementations
└── requirements-api.txt    # API dependencies
```

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
# Install and start everything
python start_api.py

# Or with custom options
python start_api.py --host 127.0.0.1 --port 8080 --skip-install
```

### Option 2: Manual Setup

1. **Install API Dependencies**:
   ```bash
   pip install -r requirements-api.txt
   ```

2. **Build Dashboard** (requires Node.js):
   ```bash
   cd api/dashboard
   npm install
   npm run build
   cd ../..
   ```

3. **Start the API Server**:
   ```bash
   cd api
   python main.py
   # Or with uvicorn directly:
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the Application**:
   - Dashboard: http://localhost:8000/
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### 🔍 Scan Operations

#### Start New Scan
```http
POST /api/scan
Content-Type: application/json

{
  "url": "https://example.com",
  "scan_type": "enhanced",
  "enable_javascript": true,
  "enable_ml_analysis": false,
  "enable_advanced_fingerprinting": true
}
```

Response:
```json
{
  "scan_id": "uuid-4-here",
  "status": "started",
  "message": "Scan initiated successfully",
  "estimated_duration": 60
}
```

#### Get Scan Result
```http
GET /api/scan/{scan_id}
```

Response:
```json
{
  "scan_id": "uuid-4-here",
  "url": "https://example.com",
  "status": "completed",
  "timestamp": "2023-12-01T10:30:00Z",
  "tracker_count": 12,
  "privacy_score": 65,
  "risk_level": "medium",
  "scan_duration": 45.2,
  "trackers": [...],
  "performance_metrics": {...},
  "privacy_analysis": {...}
}
```

### 📊 Results & Analytics

#### Get Scan Results (Paginated)
```http
GET /api/results?limit=50&offset=0&risk_level=high
```

#### Get Statistics
```http
GET /api/stats?days=30
```

Response:
```json
{
  "total_scans": 1250,
  "total_trackers_found": 8432,
  "avg_privacy_score": 72.4,
  "most_common_trackers": [...],
  "risk_distribution": {"low": 45, "medium": 32, "high": 18, "critical": 5},
  "daily_scan_count": [...]
}
```

#### Generate Report
```http
GET /api/reports/{scan_id}?format=html
```

### 🔄 Real-time Updates

Connect to WebSocket for live scan progress:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scan/your-scan-id');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}% - ${data.message}`);
};
```

## Dashboard Pages

### 🏠 Dashboard (`/`)
- Overview cards with key metrics
- Real-time charts showing trends
- Recent scan activity
- Quick stats and risk distribution

### 🔍 New Scan (`/scan`)
- URL input form
- Scan configuration options
- Real-time progress tracking
- Automatic redirect to results

### 📋 Results (`/results`)
- Sortable/filterable data grid
- Export capabilities
- Click-through to detailed views
- Bulk operations

### 📈 Statistics (`/stats`)
- Advanced analytics charts
- Time range selectors
- Domain heatmaps
- Privacy trend analysis

### 🔎 Scan Detail (`/scan/{id}`)
- Comprehensive scan results
- Real-time progress (for active scans)
- Tracker breakdown table
- Performance metrics
- Report generation

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///pixeltracker.db
# or
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# CORS (for production)
ALLOWED_ORIGINS=["https://your-domain.com"]
```

### Database Setup

The API automatically creates tables on startup. For production:

```python
from pixeltracker.persistence.database import DatabaseManager

# Initialize with PostgreSQL
db_manager = DatabaseManager(
    database_url="postgresql://user:pass@host:5432/pixeltracker"
)
db_manager.create_tables()
```

## Deployment

### Development
```bash
python start_api.py --host 127.0.0.1 --port 8000
```

### Production

1. **Docker** (recommended):
   ```dockerfile
   FROM python:3.9
   COPY . /app
   WORKDIR /app
   RUN pip install -r requirements-api.txt
   RUN cd api/dashboard && npm install && npm run build
   EXPOSE 8000
   CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Gunicorn**:
   ```bash
   pip install gunicorn
   gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

3. **Nginx Reverse Proxy**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /ws/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

## Development

### Adding New API Endpoints

1. Add route to `api/main.py`:
   ```python
   @app.get("/api/custom-endpoint")
   async def custom_endpoint():
       return {"message": "Hello World"}
   ```

2. Update API service in dashboard:
   ```typescript
   // api/dashboard/src/services/api.ts
   export const apiService = {
     // ... existing methods
     customEndpoint: async (): Promise<any> => {
       const response = await api.get('/custom-endpoint');
       return response.data;
     }
   };
   ```

### Adding Dashboard Components

```typescript
// api/dashboard/src/components/NewComponent.tsx
import React from 'react';
import { useQuery } from 'react-query';
import apiService from '../services/api';

const NewComponent: React.FC = () => {
  const { data, isLoading } = useQuery('custom-data', apiService.customEndpoint);
  
  return <div>{/* Your component JSX */}</div>;
};

export default NewComponent;
```

## Security Considerations

- **Authentication**: Currently demo mode - implement JWT tokens for production
- **Rate Limiting**: Add rate limiting middleware
- **Input Validation**: Pydantic models validate all inputs
- **CORS**: Configure `allow_origins` appropriately
- **HTTPS**: Use TLS in production
- **Database**: Use connection pooling and prepared statements

## Performance

- **Caching**: Redis integration available in persistence layer
- **Database**: Optimized indexes on frequently queried columns
- **WebSockets**: Efficient real-time updates
- **Async**: Non-blocking I/O throughout the stack
- **Compression**: Gzip enabled for API responses

## Monitoring

The API includes built-in metrics endpoints suitable for Prometheus:
- Response times
- Request counts
- Error rates
- Database performance

## Support

For issues or questions:
1. Check the interactive API docs at `/docs`
2. Review the database schema in `pixeltracker/persistence/models.py`
3. Examine the React components for UI customization

The system is designed to be modular and extensible - you can easily add new scanning methods, chart types, or analytical features!
