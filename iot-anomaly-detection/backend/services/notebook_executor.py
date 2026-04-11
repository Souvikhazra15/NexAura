"""
Jupyter Notebook Execution Service
Handles running the anomaly detection pipeline notebook programmatically
"""
import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class NotebookExecutor:
    """Execute Jupyter notebooks programmatically"""
    
    def __init__(self):
        self.notebook_path = Path(__file__).parent.parent.parent / "models" / "OmniAnamoly" / "Comprehensive_Anomaly_Detection_Pipeline.ipynb"
        self.output_dir = Path(__file__).parent.parent.parent / "models" / "OmniAnamoly"
        self.report_path = self.output_dir / "report.json"
        
    def execute_anomaly_detection(self, input_csv_path: str, timeout: int = 600) -> Dict:
        """
        Execute anomaly detection notebook on uploaded CSV
        
        Args:
            input_csv_path: Path to uploaded CSV file
            timeout: Execution timeout in seconds (default 10 minutes)
            
        Returns:
            Dict with metrics and results
            
        Raises:
            RuntimeError: If notebook execution fails
        """
        try:
            logger.info(f"Starting notebook execution for: {input_csv_path}")
            
            # Ensure paths exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Set environment variables for the notebook
            env = os.environ.copy()
            env['INPUT_CSV_PATH'] = str(input_csv_path)
            env['OUTPUT_DIR'] = str(self.output_dir)
            env['PYTHONUNBUFFERED'] = '1'
            
            # Execute notebook using papermill
            self._execute_with_papermill(str(self.notebook_path), str(input_csv_path), env, timeout)
            
            # Read and return results
            results = self._read_report()
            
            logger.info(f"✅ Notebook execution completed successfully")
            return results
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Notebook execution timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Notebook execution failed: {str(e)}")
            raise RuntimeError(f"Notebook execution error: {str(e)}")
    
    def _execute_with_papermill(self, notebook_path: str, input_csv: str, env: Dict, timeout: int):
        """Execute notebook using papermill library"""
        try:
            import papermill as pm
        except ImportError:
            logger.warning("Papermill not installed, trying nbconvert...")
            return self._execute_with_nbconvert(notebook_path, input_csv, env, timeout)
        
        # Create temporary output notebook
        with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False) as tmp:
            output_notebook = tmp.name
        
        try:
            # Execute notebook with papermill
            cmd = [
                'papermill',
                notebook_path,
                output_notebook,
                '-p', 'INPUT_CSV_PATH', input_csv,
                '-p', 'OUTPUT_DIR', str(self.output_dir)
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(
                cmd,
                env=env,
                timeout=timeout,
                check=True,
                capture_output=True,
                text=True
            )
        finally:
            # Clean up temporary notebook
            if os.path.exists(output_notebook):
                os.remove(output_notebook)
    
    def _execute_with_nbconvert(self, notebook_path: str, input_csv: str, env: Dict, timeout: int):
        """Fallback: Execute notebook using nbconvert"""
        cmd = [
            'jupyter', 'nbconvert',
            '--to', 'notebook',
            '--execute',
            '--ExecutePreprocessor.timeout=' + str(timeout),
            '--output-dir=' + str(self.output_dir),
            notebook_path
        ]
        
        logger.info(f"Executing with nbconvert: {' '.join(cmd)}")
        subprocess.run(
            cmd,
            env=env,
            timeout=timeout,
            check=True,
            capture_output=True,
            text=True
        )
    
    def _read_report(self) -> Dict:
        """Read the generated JSON report"""
        if not self.report_path.exists():
            raise FileNotFoundError(f"Report not found at {self.report_path}")
        
        with open(self.report_path, 'r') as f:
            report = json.load(f)
        
        return {
            "status": "success",
            "summary": {
                "total_samples": report.get("data_shape", {}).get("total_samples", 0),
                "anomalies_detected": report.get("data_shape", {}).get("anomalies_detected", 0),
                "anomaly_rate": f"{(report.get('data_shape', {}).get('anomalies_detected', 0) / max(report.get('data_shape', {}).get('total_samples', 1), 1) * 100):.2f}%",
                "best_model": "Ensemble",
            },
            "metrics": {
                "best_model_metrics": report.get("ensemble_metrics", {}),
                "all_models": [
                    {"model": "Z-Score", **report.get("zscore_metrics", {})},
                    {"model": "Isolation Forest", **report.get("isolation_forest_metrics", {})},
                    {"model": "LSTM Autoencoder", **report.get("lstm_metrics", {})},
                    {"model": "Ensemble", **report.get("ensemble_metrics", {})}
                ]
            },
            "report": report
        }


# Create singleton instance
notebook_executor = NotebookExecutor()
