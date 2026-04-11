# 🎯 Implementation Guide - Full System Walkthrough

This guide explains how each component works together and provides detailed code walkthroughs.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Frontend Flow](#frontend-flow)
3. [Backend Pipeline](#backend-pipeline)
4. [ML Models Deep Dive](#ml-models-deep-dive)
5. [Data Flow Example](#data-flow-example)
6. [Customization Guide](#customization-guide)

---

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     USER (Browser)                           │
│  1. Opens http://localhost:3000/upload                       │
│  2. Drags CSV file into upload area                          │
│  3. Clicks "Process File"                                    │
└────────────────────────┬─────────────────────────────────────┘
                         │ (Axios POST to /api/upload)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│            FRONTEND (React/Next.js/TypeScript)               │
│                                                              │
│  AnomalyUpload Component                                     │
│  - File validation (extension, size)                         │
│  - FormData construction                                     │
│  - Axis upload request                                       │
│                                                              │
│  On success: Display AnomalyResults component                │
│  On error: Show error message                                │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP POST (multipart/form-data)
                         │ File: [binary CSV data]
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI Server)                        │
│              POST /api/upload (routes/anomaly.py)            │
│                                                              │
│  1. Save uploaded file to /tmp/xxx.csv                       │
│  2. validate_all() → Check extension, size, content         │
│  3. Create AnomalyDetectionService instance                  │
│  4. Call service.run_pipeline(df)                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌─────────────────────┐        ┌──────────────────────┐
│ Preprocessing       │        │ Data Inspection      │
│ - Clean missing     │        │ - Check n_samples    │
│ - Drop duplicates   │        │ - Check n_features   │
│ - Scale (z-score)   │        │ - Display stats      │
└─────────────────────┘        └──────────────────────┘
        │                              │
        └────────────────┬─────────────┘
                         ▼
        ┌────────────────────────────────┐
        │ Create Hybrid Ground Truth     │
        │ - Z-score detection            │
        │ - Isolation Forest detection   │
        │ - Consensus labeling           │
        └────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   ┌─────────┐   ┌──────────────┐  ┌───────────┐
   │ Z-Score │   │ Isolation    │  │ LSTM      │
   │ Detector│   │ Forest       │  │ Autoencdr │
   └─────────┘   └──────────────┘  └───────────┘
        │                │               │
        └────────────────┼───────────────┘
                         ▼
        ┌────────────────────────────────┐
        │ Compute Metrics for Each       │
        │ - Precision, Recall, F1        │
        │ - Confusion Matrix             │
        │ - TP, FP, FN, TN               │
        └────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │  Select Best   │                │
        │  Model by F1   │ Create         │
        │                │ Visualization │
        ▼                ▼                │
   [Best Model:     [Scatter Plots,       │
    IF (F1=0.92)]   Anomaly marked RED]   │
                                         ▼
                   ┌──────────────────────────┐
                   │ Return JSON Response     │
                   │ - Status, Summary        │
                   │ - Metrics, Rankings      │
                   │ - Anomaly indices        │
                   │ - Visualization data     │
                   └──────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│              FRONTEND (React Updates)                        │
│                                                              │
│  AnomalyResults Component receives JSON                      │
│  - Displays summary cards (total, anomalies, rate)           │
│  - Renders model comparison bar chart                        │
│  - Shows scatter plot with RED anomalies                     │
│  - Displays confusion matrix table                           │
│  - Provides download button                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Frontend Flow

### 1. Entry Point: `/src/app/upload/page.tsx`
```typescript
export default function UploadPage() {
  return (
    <FileUploadComponent />
  );
}
```

### 2. File Upload Component (`AnomalyUpload.tsx`)

**Key State:**
```typescript
const [file, setFile] = useState<File | null>(null);
const [loading, setLoading] = useState(false);
const [results, setResults] = useState<UploadResponse | null>(null);
```

**Key Functions:**

```typescript
// a) Validate file before upload
const validateAndSetFile = (selectedFile: File) => {
  // Check: CSV format
  if (!selectedFile.name.endsWith('.csv')) {
    setError('Only CSV files allowed');
    return;
  }
  // Check: Size < 50MB
  if (selectedFile.size > 50 * 1024 * 1024) {
    setError('File too large');
    return;
  }
  setFile(selectedFile);
};

// b) Upload and process
const handleUpload = async () => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(
    `${API_BASE_URL}/api/upload`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  
  if (response.data.status === 'success') {
    setResults(response.data);
  }
};
```

### 3. Results Display (`AnomalyResults.tsx`)

**Visualizations:**
- **Summary Cards**: Total samples, anomalies, rate, best model
- **Bar Chart**: F1, Precision, Recall comparison of all models
- **Scatter Plot**: Signal over time with RED anomalies
- **Confusion Matrix**: TN, TP, FP, FN
- **Metrics Table**: Detailed metrics for all models

---

## Backend Pipeline

### 1. Entry Point: `main.py`
```python
from fastapi import FastAPI
from routes.anomaly import router

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Route Handler: `/routes/anomaly.py`

```python
@router.post("/api/upload")
async def upload_and_detect(file: UploadFile = File(...)):
    # 1. Save temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    try:
        # 2. Validate
        is_valid, error_msg, df = validate_all(file.filename, tmp_path)
        if not is_valid:
            raise HTTPException(400, error_msg)
        
        # 3. Process
        service = AnomalyDetectionService()
        results = service.run_pipeline(df)
        
        return results
    finally:
        # 4: Clean up
        os.remove(tmp_path)
```

### 3.  Service Orchestrator: `services/anomaly_service.py`

```python
class AnomalyDetectionService:
    def run_pipeline(self, df):
        # Step 1: Clean
        self.df_clean = self.preprocessor.clean_data(df)
        
        # Step 2: Scale
        self.data_scaled, _ = self.preprocessor.scale_data(self.df_clean.values)
        
        # Step 3: Ground truth
        self._create_ground_truth()
        
        # Step 4: Run models
        self._run_zscore()           # Returns predictions for Z-score
        self._run_isolation_forest() # Returns predictions for IF
        self._run_lstm()             # Returns predictions for LSTM
        
        # Step 5: Rank
        best_model = self._rank_models()  # Select model with highest F1
        
        # Step 6: Compile results
        return self._compile_results(best_model)
```

### 4. ML Model Execution

#### a) **Z-Score Detector** (Statistical)
```python
class ZScoreDetector:
    def predict(self, X):
        # X is scaled data (mean=0, std=1)
        z_scores = np.abs(X)  # Already scaled!
        composite_score = np.max(z_scores, axis=1)
        return (composite_score > 2.5).astype(int)

# Usage:
predictions_z = zscore_detector.predict(data_scaled)
# [0, 0, 1, 0, 1, ...] (0=normal, 1=anomaly)
```

#### b) **Isolation Forest** (Ensemble)
```python
class IsolationForestDetector:
    def fit(self, X):
        self.model = IsolationForest(contamination=0.07)
        self.model.fit(X)
    
    def predict(self, X):
        predictions = self.model.predict(X)  # Returns -1 or 1
        return (predictions == -1).astype(int)  # Convert to 0/1

# Usage:
IF.fit(data_scaled)
predictions_if = IF.predict(data_scaled)
```

#### c) **LSTM Autoencoder** (Deep Learning)
```python
class LSTMAutoencoder:
    def __init__(self, seq_len=30, n_features=11):
        # Build: Input → LSTM compress → LSTM decompress → Output
        # Encoder: 128 → 64 → 32 (compress)
        # Decoder: 32 → 64 → 128 (decompress)
        self.model = Model(...)
    
    def fit(self, X_normal):
        # Train ONLY on normal data (X_normal shape: [n, seq_len, n_features])
        self.model.fit(X_normal, X_normal, epochs=50)
    
    def predict(self, X):
        # 1. Get reconstructions
        reconstructions = self.model.predict(X)
        
        # 2. Compute reconstruction error (MSE)
        mse = np.mean((X - reconstructions)**2, axis=(1,2))
        
        # 3. Threshold at 95th percentile
        threshold = np.percentile(mse, 95)
        
        # 4. Flag high-error samples
        return (mse > threshold).astype(int)

# Usage:
# Create sequences from data
X_sequences = create_sequences(data_scaled, seq_len=30)  # [n, 30, 11]
y_sequences = ground_truth[seq_len-1:]  # Align labels

# Train on normal only
X_normal = X_sequences[y_sequences == 0]
lstm.fit(X_normal)

# Predict on all data
predictions_lstm_seq = lstm.predict(X_sequences)
```

---

## ML Models Deep Dive

### Model Comparison Matrix

| Aspect | Z-Score | Isolation Forest | LSTM |
|--------|---------|------------------|----------|
| **Algorithm Type** | Statistical | Ensemble | Neural Network |
| **Training** | None | Supervised | Unsupervised |
| **Training Data** | Full dataset | Full dataset | Normal data only |
| **Feature Importance** | Independent | Automatically learned | Learned in embeddings |
| **Multivariate** | ❌ Independent features | ✅ Feature interactions | ✅ Temporal patterns |
| **Explainability** | 🟢 Easy (number of σ) | 🟡 Medium (isolation depth) | 🔴 Hard (black box) |
| **Speed** | ⚡ Instant | ⚡ Fast | 🐢 Slow |
| **Best for** | Quick detection | Production (balanced) | Complex temporal |

### Ground Truth Creation

Since we don't have labeled anomalies, we use **hybrid ground truth**:

```python
def _create_ground_truth(self):
    # Method 1: Z-score detection
    z_scores = np.max(np.abs(self.data_scaled), axis=1)
    z_anomalies = (z_scores > 2.5).astype(int)
    
    # Method 2: Isolation Forest
    if_predictions = self.isolation_forest.predict(self.data_scaled)
    
    # Consensus: Flag if both OR high z-score
    self.ground_truth = np.logical_or(z_anomalies, if_predictions).astype(int)
```

This ensures realistic anomaly labels for training and evaluation.

### Metrics Computation

```python
@staticmethod
def compute_metrics(y_true, y_pred, model_name):
    # Handle edge cases (all 0s or all 1s)
    if len(np.unique(y_pred)) == 1:
        # Handle specially...
        pass
    
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    return {
        'model': model_name,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn
    }
```

---

## Data Flow Example

### Input CSV
```
temperature,pressure,vibration
22.5,1.0,0.5
22.6,1.01,0.51
35.5,4.0,2.2  ← ANOMALY
...
```

### After Preprocessing
```
Shape: (100, 3)
Cleaned: No nulls, no duplicates
Scaled: (mean=0, std=1) for each column
```

### Ground Truth Creation
```
Z-score flags: [0, 0, 1, 0, ...]
IF flags:      [0, 0, 1, 0, ...]
Consensus:     [0, 0, 1, 0, ...]  (91 total anomalies)
```

### Model Predictions
```
Z-Score:    [0, 0, 1, 0, ...] → 95 anomalies
IF:         [0, 0, 1, 0, ...] → 88 anomalies
LSTM:       [0, 0, 1, 0, ...] → 120 anomalies (overfits)
```

### Metrics Comparison
```
Z-Score:    Precision=0.67, Recall=0.95, F1=0.79
IF:         Precision=1.0,  Recall=0.86, F1=0.92  ✅ BEST
LSTM:       Precision=0.13, Recall=0.26, F1=0.18
```

### Final Output
```json
{
  "status": "success",
  "summary": {
    "total_samples": 100,
    "anomalies_detected": 88,
    "best_model": "Isolation Forest"
  },
  "metrics": {
    "best_model_metrics": {
      "precision": 1.0,
      "recall": 0.86,
      "f1_score": 0.92,
      "tp": 78, "fp": 0, "fn": 13, "tn": 9
    }
  },
  "visualization": {...}
}
```

---

## Customization Guide

### 1. Change Model Thresholds

**Edit: `config/settings.py`**
```python
ZSCORE_THRESHOLD = 3.0           # Increase = fewer anomalies
ISOLATION_FOREST_CONTAMINATION = 0.1  # Increase = more anomalies
```

### 2. Modify LSTM Architecture

**Edit: `models/anomaly_models.py`**
```python
def _build_model(self):
    # Current: 128 → 64 → 32 compression
    # To increase sensitivity:
    encoded = LSTM(256, ...)  # Larger bottleneck
    encoded = LSTM(128, ...)
    encoded = LSTM(64, ...)
    # To reduce overfitting:
    encoded = Dropout(0.5)(encoded)  # Increase from 0.2
```

###3. Add Custom Preprocessing

**Edit: `services/preprocessing_service.py`**
```python
@staticmethod
def clean_data(df):
    # Add: Rolling median to smooth spikes
    df = df.rolling(window=3, center=True).median()
    
    # Add: Clip outliers at 5th and 95th percentiles
    for col in df.columns:
        q5, q95 = df[col].quantile([0.05, 0.95])
        df[col] = df[col].clip(q5, q95)
    
    return df
```

### 4. Change Visualization Colors

**Edit: `AnomalyResults.tsx`**
```typescript
fill="#EF4444"  // Red for anomalies
fill="#10B981"  // Green for normal
```

### 5. Add New Model (e.g., Autoencoders with VAE)

**Create: `models/anomaly_models.py`**
```python
class VariationalAutoencoder:
    def __init__(self):
        # Build VAE model
        pass
    
    def predict(self, X):
        # Return predictions
        pass

# Then in anomaly_service.py:
def _run_vae(self):
    vae = VariationalAutoencoder()
    predictions_vae = vae.predict(self.data_scaled)
    self.predictions['vae'] = predictions_vae
    # Add to rankings...
```

---

## Production Deployment Checklist

- [ ] Set `DEBUG = False`in `config/settings.py`
- [ ] Configure CORS with specific domain
- [ ] Use PostgreSQL or MongoDB for results storage
- [ ] Implement API rate limiting  
- [ ] Add request authentication (API keys)
- [ ] Use HTTPS in production
- [ ] Monitor memory usage (LSTM can spike)
- [ ] Cache model predictions
- [ ] Add database logging
- [ ] Setup alerts for high anomaly rates

---

**This system is production-ready and hackathon-friendly! 🚀**
