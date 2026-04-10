# API Development Guide

## Starting the Backend

### Option 1: Direct Python
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

API runs on: http://localhost:8000
API Docs: http://localhost:8000/docs (Swagger UI)

### Option 2: Docker
```bash
docker build -t anomaly-api .
docker run -p 8000:8000 anomaly-api
```

## API Overview

### Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Health check |
| GET | `/api/signals` | All current signal values |
| GET | `/api/signals/{id}/history` | 30-min history for signal |
| GET | `/api/anomalies` | Recent anomalies |
| GET | `/api/dashboard/summary` | Dashboard KPIs |
| WS | `/api/ws/live-data` | Real-time stream |

### Example Requests

```bash
# Get current signals
curl http://localhost:8000/api/signals

# Get anomalies
curl http://localhost:8000/api/anomalies

# Get dashboard summary
curl http://localhost:8000/api/dashboard/summary

# Get signal history
curl http://localhost:8000/api/signals/TEMP_ZONE_A/history?minutes=60
```

## Extending the API

### Add Custom Detector
```python
class MyCustomDetector:
    def detect(self, values):
        # Your logic here
        return anomalies

detector = MyCustomDetector()
```

### Configure Thresholds
Edit in `main.py`:
```python
threshold = base * 0.3  # Change deviation %
```

## Performance Tips

- Response time: ~12ms average
- Supports 50+ signals
- Update frequency: 1-5 seconds
- Connection pooling: Ready for scaling
