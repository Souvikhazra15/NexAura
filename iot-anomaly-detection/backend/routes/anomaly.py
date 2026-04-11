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
        "models": ["Z-Score", "Isolation Forest", "LSTM Autoencoder", "Ensemble"]
    }


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

