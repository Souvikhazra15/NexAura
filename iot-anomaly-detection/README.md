# 🚀 Production-Ready Anomaly Detection System

A complete full-stack machine learning pipeline for detecting anomalies in time-series sensor data. Features three complementary models (Z-Score, Isolation Forest, GRU Autoencoder) with a professional React frontend and FastAPI backend.

---

## 📂 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (Next.js)                 │
│  - CSV Upload UI (Drag & Drop)                              │
│  - Real-time Progress Display                               │
│  - Interactive Dashboards (Recharts)                        │
│  - Metrics & Confusion Matrix Visualization                 │
└────────────────────┬────────────────────────────────────────┘
                     │ (Axios HTTP POST)
                     │ /api/upload (multipart/form-data)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND (Python)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Routes (routes/anomaly.py)                           │   │
│  │  - POST /api/upload (main endpoint)                  │   │
│  │  - GET /api/health                                   │   │
│  │  - POST /api/test                                    │   │
│  └─────────────────┬──────────────────────────────────┘   │
│                    │                                        │
│  ┌─────────────────▼──────────────────────────────────┐   │
│  │ Services (services/)                               │   │
│  │  - AnomalyDetectionService (orchestrator)          │   │
│  │  - PreprocessingService (scaling, normalization)   │   │
│  └─────────────────┬──────────────────────────────────┘   │
│                    │                                        │
│  ┌─────────────────▼──────────────────────────────────┐   │
│  │ ML Models (models/anomaly_models.py)               │   │
│  │  • ZScoreDetector                                  │   │
│  │  • IsolationForestDetector                         │   │
│  │  • GRUAutoencoder                                  │   │
│  │  • MetricsComputer                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Utilities (utils/)                                 │   │
│  │  - File validation                                 │   │
│  │  - Error handling                                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Folder Structure

### Backend
```
backend/
├── main.py                      # FastAPI app entry point
├── requirements.txt             # Python dependencies
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration (model params, limits, etc)
├── models/
│   ├── __init__.py
│   └── anomaly_models.py       # Z-Score, IF, GRU, Metrics
├── services/
│   ├── __init__.py
│   ├── anomaly_service.py      # Core pipeline orchestrator
│   └── preprocessing_service.py # Data cleaning & scaling
├── routes/
│   ├── __init__.py
│   └── anomaly.py              # API endpoints
├── utils/
│   ├── __init__.py
│   └── validators.py           # File validation
└── uploads/                     # Temporary file storage
```

### Frontend
```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx            # Home/dashboard
│   │   ├── upload/
│   │   │   └── page.tsx        # Upload page
│   │   ├── layout.tsx          # Root layout
│   │   └── ...
│   ├── components/
│   │   ├── AnomalyUpload.tsx   # File upload UI
│   │   ├── AnomalyResults.tsx  # Results dashboard
│   │   └── ...
│   └── ...
├── .env.local                   # Environment variables
├── package.json                 # Dependencies
├── tsconfig.json               # TypeScript config
└── tailwind.config.js          # Tailwind CSS
```

---

## 🔧 Setup & Installation

### Prerequisites
- **Python 3.9+** (Backend)
- **Node.js 18+** (Frontend)
- **Git**

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
# OR with uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ Server will start at `http://localhost:8000`
📚 API docs at `http://localhost:8000/docs` (Swagger UI)

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local if not exists
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

#Run development server
npm run dev
```

✅ Frontend will start at `http://localhost:3000`

---

## 📊 ML Models Explained

### 1. **Z-Score Detector** 📈
- **Type**: Statistical
- **How it works**: Flags samples where max Z-score exceeds threshold (2.5σ)
- **Pros**: Fast, interpretable, peak-based detection
- **Cons**: Univariate (ignores correlations)
- **Use case**: Quick outlier detection

### 2. **Isolation Forest** 🌲
- **Type**: Ensemble (Random Forest variant)
- **How it works**: Randomly isolates anomalies; anomalies isolated faster = higher scores
- **Pros**: No distribution assumptions, handles multivariate, fast
- **Cons**: Less explainable, parameter tuning needed
- **Use case**: General-purpose, production-grade
- **Status**: ✅ **RECOMMENDED** (F1~0.92)

### 3. **GRU Autoencoder** 🧠
- **Type**: Deep Learning (RNN)
- **How it works**: 
  - Trains ONLY on normal data
  - Reconstructs sequences
  - High reconstruction error = anomaly
  - 3-layer compression: 128→64→32 dimensions
- **Pros**: Learns temporal patterns, handles complex sequences
- **Cons**: Requires more data, training time, expensive inference
- **Use case**: Complex temporal patterns, if data abundant
- **Note**: May need tuning for specific datasets

### Model Selection Logic
```python
1. Get predictions from all 3 models
2. Compute metrics (Precision, Recall, F1) using hybrid ground truth
3. Select model with highest F1-score
4. Return predictions + rankings
```

---

## 🔌 API Reference

### POST /api/upload
**Upload CSV and run anomaly detection**

**Request:**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@data.csv"
```

**Response:**
```json
{
  "status": "success",
  "summary": {
    "total_samples": 2303,
    "anomalies_detected": 44,
    "anomaly_rate": "1.91%",
    "best_model": "Isolation Forest"
  },
  "metrics": {
    "best_model_metrics": {
      "model": "Isolation Forest",
      "precision": 1.0,
      "recall": 0.855,
      "f1_score": 0.922,
      "tp": 44, "fp": 0, "fn": 7, "tn": 2252
    },
    "all_models": [...]
  },
  "anomalies": {
    "predicted_indices": 44,
    "anomaly_score": [...],
    "indices": [5, 12, 48, ...]
  },
  "visualization": {
    "data_points": [...],
    "anomaly_indices": [...]
  }
}
```

### GET /api/health
**Health check**
```bash
curl http://localhost:8000/api/health
```

### POST /api/test
**Test with sample data**
```bash
curl -X POST http://localhost:8000/api/test
```

---

## 📥 CSV Format Requirements

**Required:**
- ✅ CSV format only
- ✅ At least 2 numeric columns
- ✅ Minimum 10 rows
- ✅ Maximum 50MB

**Example CSV:**
```csv
temperature,pressure,vibration,humidity,power
22.5,1.0,0.5,45,500
22.6,1.01,0.51,46,502
22.4,0.99,0.49,44,498
...
```

---

## ⚙️ Configuration

Edit `backend/config/settings.py`:

```python
# File constraints
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = {'csv'}

# GRU parameters
SEQUENCE_LENGTH = 30        # Sliding window size
GRU_EPOCHS = 50           # Training iterations
GRU_BATCH_SIZE = 32       # Batch size
GRU_DROPOUT = 0.2         # Dropout for regularization
GRU_LEARNING_RATE = 0.001 # Adam optimizer LR

# Model thresholds
ZSCORE_THRESHOLD = 2.5                      # Standard deviations
ISOLATION_FOREST_CONTAMINATION = 0.07       # Expected anomaly rate

# CORS
CORS_ORIGINS = ["http://localhost:3000", "*"]
```

---

## 🚀 Running the System

### Option 1: Local Development
```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit: `http://localhost:3000`

### Option 2: Docker (Production)
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Option 3: Production Server
```bash
# Backend (with gunicorn)
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# Frontend (next build)
cd frontend
npm run build
npm run start
```

---

## 📈 Example Workflow

1. **Upload CSV** → Drag & drop your sensor data
2. **Validate** → Check file format, size, columns
3. **Preprocess** → Clean missing values, scale data
4. **Run Models** → Execute Z-Score, IF, GRU in parallel
5. **Generate Metrics** → Compute precision, recall, F1
6. **Recommend** → Select best model
7. **Visualize** → Show results with charts
8. **Download** → Get JSON with predictions & metrics

---

## 🎯 Key Features

✅ **Easy File Upload**
- Drag & drop UI
- Real-time validation
- Progress indicators

✅ **Three ML Models**
- Statistical (Z-Score)
- Ensemble (Isolation Forest) 
- Deep Learning (GRU)

✅ **Rich Dashboards**
- Metrics comparison charts
- Confusion matrices
- Anomaly visualizations
- Model rankings

✅ **Production Ready**
- Error handling
- Input validation
- Modular architecture
- Logging & monitoring

✅ **Fast Processing**
- Optimized NumPy/scikit-learn
- Batch inference
- Caching where possible

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # macOS/Linux

# Kill process & restart
# OR use different port:
uvicorn main:app --port 8001
```

### Frontend can't connect to backend
- Check `.env.local` has correct API URL
- Verify backend is running on port 8000
- Check CORS middleware is configured

### Out of memory with large files
- Reduce file size (split dataset)
- Or increase RAM allocation
- Process in batches

### GRU training too slow
- Reduce `GRU_EPOCHS` in settings.py
- Reduce `SEQUENCE_LENGTH` 
- Use GPU (install `tensorflow[and-cuda]`)

---

## 📚 Model Performance Benchmarks

(Based on IoT sensor dataset - 2,303 samples, 11 features)

| Model | Precision | Recall | F1-Score | Speed |
|-------|-----------|--------|----------|-------|
| Z-Score | 0.67 | 0.95 | 0.79 | ⚡ 1ms |
| Isolation Forest | **1.0** | **0.86** | **0.92** | ⚡ 5ms |
| GRU Autoencoder | 0.13 | 0.26 | 0.18 | 🐢 500ms |

**Recommendation**: Use **Isolation Forest** for production. GRU may need dataset-specific tuning.

---

## 🔐 Security Considerations

- Validate all file inputs (extension, size, content)
- Sanitize file paths to prevent directory traversal
- Use HTTPS in production
- Keep dependencies updated
- Implement rate limiting for API endpoints
- Store sensitive config in environment variables

---

## 📦 Deployment Checklist

- [ ] Configure `settings.py` for production
- [ ] Set `DEBUG = False` in main.py
- [ ] Use `CORS_ORIGINS = ["yourdomain.com"]` (not `*`)
- [ ] Deploy backend on production server
- [ ] Build frontend (`npm run build`)
- [ ] Use CDN for static assets
- [ ] Monitor API response times & memory usage
- [ ] Set up logging & alerting

---

## 📞 Support & Contributing

For issues, feature requests, or improvements:
- Check existing issues on GitHub
- Create detailed bug reports with CSV samples
- Contribute improvements via pull requests

---

## 📄 License

MIT License - Free for production use

---

**Built with ❤️ for production-grade anomaly detection**
