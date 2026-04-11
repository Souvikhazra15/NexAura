# ⚡ QUICK START - Get Running in 5 Minutes

## 🚀 Fastest Way to Run

### Option 1: Windows (Recommended for You)

```bash
# 1. Navigate to project root
cd d:\NexAura\iot-anomaly-detection

# 2. Run startup script
start.bat

# That's it! System will start automatically
# Window 1: Backend server (port 8000)
# Window 2: Frontend (port 3000)
```

### Option 2: macOS/Linux

```bash
cd iot-anomaly-detection
chmod +x start.sh
./start.sh
```

### Option 3: Manual Start (All Platforms)

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# OR source venv/bin/activate # macOS/Linux
pip install -r requirements.txt
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📱 Access the System

Once running:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Upload and visualize |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI (test API) |

---

## 📥 Test It Out

### Option A: Use Sample Data
```bash
# Copy sample CSV and upload via frontend
cp sample_data.csv your_data.csv
# Then go to http://localhost:3000/upload and upload
```

### Option B: Test API Directly
```bash
# In PowerShell:
$file = "sample_data.csv"
$url = "http://localhost:8000/api/upload"
$form = @{
    file = Get-Item -Path $file
}
Invoke-WebRequest -Uri $url -Form $form -Method Post -OutFile results.json

# View results
Get-Content results.json | ConvertFrom-Json | ConvertTo-Json
```

### Option C: Quick Test Endpoint
```bash
curl -X POST http://localhost:8000/api/test
```

---

## 📊 What You'll Get

After uploading CSV, you'll see:

✅ **Summary**
- Total samples analyzed
- Anomalies detected
- Best performing ML model

✅ **Metrics**
- Precision, Recall, F1-Score
- All 3 models compared
- Confusion matrix

✅ **Visualizations**
- Red dots showing anomalies on your data
- Model comparison bar chart
- Detailed metrics table

✅ **Download**
- Full results as JSON
- All predictions and metrics included

---

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
uvicorn main:app --port 8001
```

### Frontend won't connect
```bash
# Make sure backend is running first
# Check .env.local has:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Out of memory
```bash
# Reduce file size or:
# Windows: Settings → App memory limit
# Linux: ulimit -v 4000000
```

### Module not found errors
```bash
# Backend
pip install --upgrade -r requirements.txt

# Frontend
npm install
npm cache clean --force
npm install
```

---

## 📂 Key Files to Know

| File | Purpose |
|------|---------|
| `frontend/src/components/AnomalyUpload.tsx` | File upload UI |
| `frontend/src/components/AnomalyResults.tsx` | Results dashboard |
| `backend/routes/anomaly.py` | API endpoints |
| `backend/services/anomaly_service.py` | ML pipeline |
| `backend/models/anomaly_models.py` | Z-Score, IF, LSTM |
| `backend/config/settings.py` | Configuration |

---

## 🎯 Next Steps

1. ✅ Run the system (`start.bat` or scripts)
2. ✅ Upload sample CSV
3. ✅ View results dashboard
4. ✅ Download results JSON
5. ✅ Read `IMPLEMENTATION_GUIDE.md` for deep dive
6. ✅ Customize models (edit `config/settings.py`)
7. ✅ Deploy to production (`docker-compose up`)

---

## 💎 Features at a Glance

| Feature | Implementation |
|---------|-----------------|
| **3 ML Models** | Z-Score + Isolation Forest + LSTM |
| **Upload UI** | Drag & drop, validation, progress |
| **Real-time Processing** | Instant results (minutes) |
| **Rich Dashboard** | Charts, metrics, confusion matrix |
| **Model Ranking** | Auto-select best model by F1 |
| **Download Results** | JSON export with all data |
| **Responsive Design** | Mobile-friendly UI |
| **Production Ready** | Error handling, logging, validation |

---

## 🚀 Production Deployment

```bash
# Using Docker (if installed)
docker-compose up --build

# This will:
# - Build backend Docker image
# - Build frontend Docker image
# - Start both services
# - Expose frontend on :3000
# - Expose API on :8000
```

---

## 📞 Quick Reference

**Python Required:** 3.9+  
**Node Required:** 18+  
**Dependencies:** Automatically installed  
**Time to run:** < 5 minutes  
**Processing time:** Seconds to minutes depending on dataset size  

---

## ✅ Verification Checklist

After startup:
- [ ] Backend console shows "Uvicorn running"
- [ ] Frontend console shows "Ready in X.Xs"
- [ ] Browser opens http://localhost:3000
- [ ] Can upload CSV without errors
- [ ] Results display successfully
- [ ] All charts render correctly
- [ ] Download button works

---

**You're all set! 🎉 Enjoy the system!**

For detailed documentation, see: `README.md` and `IMPLEMENTATION_GUIDE.md`
