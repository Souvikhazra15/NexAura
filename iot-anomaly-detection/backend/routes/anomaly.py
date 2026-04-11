"""
FastAPI routes for anomaly detection
Integrates Jupyter notebook execution for ML pipeline
"""
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import pandas as pd
import logging

from utils.validators import validate_all
from services.notebook_executor import notebook_executor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["anomaly"])

# Response models
class MetricsResponse(BaseModel):
    model: str
    precision: float
    recall: float
    f1_score: float
    accuracy: float


class AnomalyResponse(BaseModel):
    status: str
    summary: dict
    metrics: dict


@router.post("/upload")
async def upload_and_detect(file: UploadFile = File(...), background_tasks: BackgroundTasks = None) -> dict:
    """
    Upload CSV and run anomaly detection via Jupyter notebook.
    
    Workflow:
    1. Receive CSV file
    2. Validate file format and content
    3. Save file to uploads folder
    4. Execute Comprehensive_Anomaly_Detection_Pipeline.ipynb
    5. Notebook runs: preprocessing, model inference, metrics computation
    6. Notebook saves results to OmniAnamoly/report.json
    7. Return metrics and summary to frontend
    
    Args:
        file: CSV file upload
        background_tasks: Background task manager for cleanup
        
    Returns:
        {
            "status": "success",
            "summary": {"total_samples": ..., "anomalies_detected": ..., "anomaly_rate": ..., "best_model": "Ensemble"},
            "metrics": {
                "best_model_metrics": {"precision": ..., "recall": ..., "f1_score": ..., "accuracy": ...},
                "all_models": [...]
            }
        }
        
    Raises:
        HTTPException: Validation or processing errors
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Ensure uploads directory exists
    os.makedirs('uploads', exist_ok=True)
    
    # Save uploaded file permanently for notebook access
    permanent_path = os.path.join('uploads', file.filename)
    tmp_path = None
    
    try:
        # Read file contents
        contents = await file.read()
        
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Save to permanent location for notebook
        with open(permanent_path, 'wb') as perm_file:
            perm_file.write(contents)
        
        # Create temporary copy for validation
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        # Validate file
        is_valid, error_msg, df = validate_all(file.filename, tmp_path)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        logger.info(f"📊 Starting anomaly detection for: {file.filename} ({len(df)} rows, {len(df.columns)} cols)")
        
        # Execute notebook on uploaded CSV
        results = notebook_executor.execute_anomaly_detection(permanent_path)
        
        logger.info(f"✅ Successfully processed {file.filename}")
        
        # Schedule cleanup of temporary file
        if background_tasks:
            background_tasks.add_task(lambda: os.remove(tmp_path) if os.path.exists(tmp_path) else None)
        
        return results
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"🔴 Processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Anomaly Detection API",
        "execution": "Jupyter Notebook Pipeline",
        "models": ["Z-Score", "Isolation Forest"],
        "cwd": os.getcwd(),
        "uploads_dir": os.path.abspath('uploads'),
        "uploads_exists": os.path.exists('uploads'),
        "uploads_files": os.listdir('uploads') if os.path.exists('uploads') else []
    }


@router.get("/correlation")
async def get_correlation_matrix() -> dict:
    """
    Get correlation matrix from the most recently uploaded CSV file.
    
    Returns:
        {
            "signals": ["col1", "col2", ...],
            "matrix": {
                "col1": {"col1": 1.0, "col2": 0.85, ...},
                "col2": {"col1": 0.85, "col2": 1.0, ...},
                ...
            },
            "filename": "uploaded_file.csv"
        }
        
    Raises:
        HTTPException: If no CSV file found or calculation fails
    """
    try:
        # Find the most recently uploaded CSV file
        # Try both relative and absolute paths
        uploads_dirs = [
            'uploads',  # Relative path
            os.path.join(os.getcwd(), 'uploads'),  # Absolute path from cwd
            os.path.abspath('uploads'),  # Absolute relative path
        ]
        
        uploads_dir = None
        for dir_path in uploads_dirs:
            if os.path.exists(dir_path):
                uploads_dir = dir_path
                logger.info(f"Found uploads directory: {uploads_dir}")
                break
        
        if not uploads_dir:
            error_msg = f"Uploads directory not found. Searched: {uploads_dirs}. CWD: {os.getcwd()}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail="No uploads directory found. Upload a CSV file first.")
        
        csv_files = [f for f in os.listdir(uploads_dir) if f.endswith('.csv')]
        if not csv_files:
            logger.warning(f"No CSV files found in {uploads_dir}")
            raise HTTPException(status_code=404, detail="No CSV files found. Upload a CSV file first.")
        
        # Get the latest CSV file
        latest_file = max([os.path.join(uploads_dir, f) for f in csv_files], 
                         key=os.path.getctime)
        filename = os.path.basename(latest_file)
        
        logger.info(f"Processing correlation for: {latest_file}")
        
        # Read and process CSV
        df = pd.read_csv(latest_file)
        
        # Convert mixed types to numeric (fill non-numeric with NaN)
        df_numeric = df.select_dtypes(include=['number']).copy()
        
        if df_numeric.empty:
            raise HTTPException(status_code=400, detail="No numeric columns found in CSV")
        
        # Calculate correlation matrix (Pearson)
        corr_matrix = df_numeric.corr().round(4)
        
        # Convert to dictionary format
        signals = corr_matrix.columns.tolist()
        matrix_dict = {}
        
        for signal in signals:
            matrix_dict[signal] = corr_matrix[signal].to_dict()
        
        logger.info(f"✓ Calculated correlation matrix for {filename}: {len(signals)} signals")
        
        return {
            "status": "success",
            "signals": signals,
            "matrix": matrix_dict,
            "filename": filename,
            "shape": {
                "rows": len(df),
                "columns": len(signals)
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Correlation calculation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Correlation error: {str(e)}")


@router.get("/models")
async def get_available_models() -> dict:
    """Get available anomaly detection models"""
    return {
        "models": [
            {
                "name": "Z-Score",
                "type": "Statistical",
                "description": "Univariate outlier detection based on standard deviation"
            },
            {
                "name": "Isolation Forest",
                "type": "Ensemble",
                "description": "Tree-based anomaly detection algorithm"
            },
            {
                "name": "LSTM Autoencoder",
                "type": "Deep Learning",
                "description": "Sequence-based anomaly detection using neural networks"
            },
            {
                "name": "Ensemble",
                "type": "Hybrid",
                "description": "Majority voting from all three models"
            }
        ]
    }


# Global signal monitoring state
signal_stream_active = False
current_alerts = []


@router.get("/signals/stream")
async def start_signal_stream() -> dict:
    """Start streaming signal data and monitoring for anomalies"""
    global signal_stream_active
    signal_stream_active = True
    
    try:
        # Find the most recently uploaded CSV file
        uploads_dir = 'uploads'
        if not os.path.exists(uploads_dir):
            raise HTTPException(status_code=404, detail="No data available")
        
        csv_files = [f for f in os.listdir(uploads_dir) if f.endswith('.csv')]
        if not csv_files:
            raise HTTPException(status_code=404, detail="No CSV files found")
        
        latest_file = max([os.path.join(uploads_dir, f) for f in csv_files], 
                         key=os.path.getctime)
        
        df = pd.read_csv(latest_file)
        
        from services.alert_service import alert_service
        
        alerts = []
        
        # Generate alerts from each row
        for idx, row in df.iterrows():
            if not signal_stream_active:
                break
            
            # Extract numeric values from row
            signals_dict = {}
            for col in df.columns:
                if col not in ['timestamp', 'machine_id', 'machine_type', 'production_status']:
                    val = row[col]
                    if pd.notna(val):
                        signals_dict[col] = float(val)
            
            # Check for anomalies
            row_alerts = alert_service.check_multiple_signals(signals_dict)
            if row_alerts:
                alerts.extend(row_alerts)
        
        return {
            "status": "success",
            "total_alerts": len(alerts),
            "critical_count": len([a for a in alerts if a['severity'] == 'critical']),
            "warning_count": len([a for a in alerts if a['severity'] == 'warning']),
            "alerts": alerts[:100]  # Limit to 100 for response
        }
    
    except HTTPException as e:
        signal_stream_active = False
        raise e
    except Exception as e:
        signal_stream_active = False
        logger.error(f"Signal stream error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")


@router.post("/signals/stop")
async def stop_signal_stream() -> dict:
    """Stop streaming signal data"""
    global signal_stream_active
    signal_stream_active = False
    return {"status": "success", "message": "Signal stream stopped"}


@router.post("/signals/disconnect")
async def disconnect_backend() -> dict:
    """Disconnect backend - stop streaming and clear active connections"""
    global signal_stream_active
    signal_stream_active = False
    logger.info("Backend disconnected - signal streaming disabled")
    return {"status": "success", "message": "Backend disconnected"}


@router.post("/signals/reconnect")
async def reconnect_backend() -> dict:
    """Reconnect backend - re-establish connection"""
    global signal_stream_active
    signal_stream_active = True
    logger.info("Backend reconnected - signal streaming enabled")
    return {"status": "success", "message": "Backend reconnected"}


@router.get("/anomalies")
async def get_anomalies(limit: int = 20) -> dict:
    """
    Get critical and warning anomalies from the current dataset
    
    Args:
        limit: Maximum number of anomalies to return
        
    Returns:
        List of anomalies with severity, contributing signals, and suggested actions
    """
    try:
        # Find the most recently uploaded CSV file
        uploads_dir = 'uploads'
        if not os.path.exists(uploads_dir):
            return {"anomalies": [], "total": 0}
        
        csv_files = [f for f in os.listdir(uploads_dir) if f.endswith('.csv')]
        if not csv_files:
            return {"anomalies": [], "total": 0}
        
        latest_file = max([os.path.join(uploads_dir, f) for f in csv_files], 
                         key=os.path.getctime)
        
        df = pd.read_csv(latest_file)
        
        from services.alert_service import alert_service
        
        all_alerts = []
        
        # Generate alerts from all rows
        for idx, row in df.iterrows():
            # Extract numeric values from row
            signals_dict = {}
            for col in df.columns:
                if col not in ['timestamp', 'machine_id', 'machine_type', 'production_status']:
                    val = row[col]
                    if pd.notna(val):
                        signals_dict[col] = float(val)
            
            # Check for anomalies
            row_alerts = alert_service.check_multiple_signals(signals_dict)
            if row_alerts:
                # Add timestamp if available
                if 'timestamp' in row and pd.notna(row['timestamp']):
                    for alert in row_alerts:
                        alert['timestamp'] = str(row['timestamp'])
                all_alerts.extend(row_alerts)
        
        # Sort by severity (critical first) and take limit
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        sorted_alerts = sorted(all_alerts, 
                             key=lambda x: (severity_order.get(x['severity'], 3), -x['score']))
        
        return {
            "anomalies": sorted_alerts[:limit],
            "total": len(sorted_alerts),
            "critical_count": len([a for a in sorted_alerts if a['severity'] == 'critical']),
            "warning_count": len([a for a in sorted_alerts if a['severity'] == 'warning'])
        }
    
    except Exception as e:
        logger.error(f"Anomalies retrieval error: {str(e)}", exc_info=True)
        return {"anomalies": [], "total": 0, "error": str(e)}

