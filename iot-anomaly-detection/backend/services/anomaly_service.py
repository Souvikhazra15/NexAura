"""
Main anomaly detection service orchestrating the full pipeline
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from config.settings import SEQUENCE_LENGTH, ISOLATION_FOREST_CONTAMINATION, ZSCORE_THRESHOLD
from services.preprocessing_service import PreprocessingService
from models.anomaly_models import (
    ZScoreDetector, IsolationForestDetector, LSTMAutoencoder, MetricsComputer
)


class AnomalyDetectionService:
    """
    Complete anomaly detection pipeline
    """
    
    def __init__(self):
        self.preprocessor = PreprocessingService()
        self.scaler = None
        self.df_clean = None
        self.data_scaled = None
        self.ground_truth = None
        
        # Models
        self.zscore_detector = ZScoreDetector(threshold=ZSCORE_THRESHOLD)
        self.isolation_forest = IsolationForestDetector(contamination=ISOLATION_FOREST_CONTAMINATION)
        self.lstm_autoencoder = None
        
        # Results storage
        self.predictions = {}
        self.metrics = {}
        self.anomaly_indices = {}
    
    def run_pipeline(self, df: pd.DataFrame) -> Dict:
        """
        Run complete anomaly detection pipeline.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dict: Complete results with predictions and metrics
        """
        print("[Pipeline] Starting anomaly detection...")
        
        # Step 1: Clean data
        print("[Step 1] Cleaning data...")
        self.df_clean = self. preprocessor.clean_data(df)
        
        # Step 2: Scale data
        print("[Step 2] Scaling data...")
        self.data_scaled, self.scaler = self.preprocessor.scale_data(self.df_clean.values)
        
        # Step 3: Create synthetic ground truth
        print("[Step 3] Creating ground truth...")
        self._create_ground_truth()
        
        # Step 4: Run Z-Score
        print("[Step 4] Running Z-Score detector...")
        self._run_zscore()
        
        # Step 5: Run Isolation Forest
        print("[Step 5] Running Isolation Forest...")
        self._run_isolation_forest()
        
        # Step 6: Run LSTM
        print("[Step 6] Running LSTM Autoencoder...")
        self._run_lstm()
        
        # Step 7: Recommend best model
        print("[Step 7] Ranking models...")
        best_model = self._rank_models()
        
        # Step 8: Compile results
        print("[Step 8] Compiling results...")
        return self._compile_results(best_model)
    
    def _create_ground_truth(self):
        """
        Create synthetic ground truth by combining Z-score and IF predictions.
        This represents "expected anomalies" for hybrid validation.
        """
        # Z-score initial detection
        z_scores = np.max(np.abs(self.data_scaled), axis=1)
        z_anomalies = (z_scores > ZSCORE_THRESHOLD).astype(int)
        
        # IF initial detection
        if_predictions = self.isolation_forest.fit(self.data_scaled).predict(self.data_scaled)
        
        # Consensus: flag as anomaly if BOTH detect or high z-score
        self.ground_truth = np.logical_or(z_anomalies, if_predictions).astype(int)
    
    def _run_zscore(self):
        """Run Z-score anomaly detection"""
        predictions_z = self.zscore_detector.predict(self.data_scaled)
        self.predictions['zscore'] = predictions_z
        
        metrics = MetricsComputer.compute_metrics(
            self.ground_truth, predictions_z, "Z-Score"
        )
        self.metrics['zscore'] = metrics
        self.anomaly_indices['zscore'] = np.where(predictions_z == 1)[0].tolist()
    
    def _run_isolation_forest(self):
        """Run Isolation Forest anomaly detection"""
        predictions_if = self.isolation_forest.predict(self.data_scaled)
        self.predictions['isolation_forest'] = predictions_if
        
        metrics = MetricsComputer.compute_metrics(
            self.ground_truth, predictions_if, "Isolation Forest"
        )
        self.metrics['isolation_forest'] = metrics
        self.anomaly_indices['isolation_forest'] = np.where(predictions_if == 1)[0].tolist()
    
    def _run_lstm(self):
        """Run LSTM Autoencoder"""
        try:
            # Build model
            self.lstm_autoencoder = LSTMAutoencoder(SEQUENCE_LENGTH, self.data_scaled.shape[1])
            
            # Create sequences
            X_sequences = self.preprocessor.create_sequences(self.data_scaled, SEQUENCE_LENGTH)
            
            # Create labels (ground truth) for sequences
            y_sequences = self.ground_truth[SEQUENCE_LENGTH - 1:]
            
            # Separate normal data for training
            X_normal = X_sequences[y_sequences == 0]
            
            if len(X_normal) < 10:
                print("  ⚠️  Insufficient normal samples for LSTM training")
                self.predictions['lstm'] = np.zeros(len(self.ground_truth))
                self.metrics['lstm'] = {
                    'model': 'LSTM',
                    'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0,
                    'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0
                }
                return
            
            # Train on normal data
            self.lstm_autoencoder.fit(X_normal)
            
            # Predict on sequences
            lstm_pred_seq = self.lstm_autoencoder.predict(X_sequences, threshold_percentile=95)
            
            # Align predictions with original ground truth
            predictions_lstm = np.zeros(len(self.ground_truth))
            predictions_lstm[SEQUENCE_LENGTH - 1:] = lstm_pred_seq
            
            self.predictions['lstm'] = predictions_lstm.astype(int)
            
            metrics = MetricsComputer.compute_metrics(
                self.ground_truth, predictions_lstm.astype(int), "LSTM"
            )
            self.metrics['lstm'] = metrics
            self.anomaly_indices['lstm'] = np.where(predictions_lstm == 1)[0].tolist()
        
        except Exception as e:
            print(f"  ❌ LSTM Error: {str(e)}")
            self.predictions['lstm'] = np.zeros(len(self.ground_truth))
            self.metrics['lstm'] = {
                'model': 'LSTM',
                'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0,
                'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0
            }
    
    def _rank_models(self) -> str:
        """
        Rank models by F1-score and return best model name.
        
        Returns:
            str: Name of best model
        """
        ranking = sorted(
            self.metrics.items(),
            key=lambda x: x[1]['f1_score'],
            reverse=True
        )
        
        best_model = ranking[0][0]
        print(f"  ✅ Best model: {ranking[0][1]['model']} (F1={ranking[0][1]['f1_score']:.3f})")
        
        return best_model
    
    def _compile_results(self, best_model: str) -> Dict:
        """
        Compile all results into single JSON response.
        
        Args:
            best_model: Name of best performing model
            
        Returns:
            Dict: Full results dictionary
        """
        # Use best model's predictions
        final_predictions = self.predictions[best_model]
        n_anomalies_detected = int(np.sum(final_predictions))
        
        # Prepare visualization data
        viz_data = []
        for i, row in self.df_clean.iterrows():
            viz_data.append({
                'index': i,
                'is_anomaly': int(final_predictions[i]),
                'values': row.to_dict()
            })
        
        return {
            'status': 'success',
            'summary': {
                'total_samples': len(self.df_clean),
                'anomalies_detected': n_anomalies_detected,
                'anomaly_rate': f"{(n_anomalies_detected / len(self.df_clean) * 100):.2f}%",
                'best_model': self.metrics[best_model]['model']
            },
            'metrics': {
                'best_model_metrics': self.metrics[best_model],
                'all_models': [self.metrics[m] for m in ['zscore', 'isolation_forest', 'lstm']]
            },
            'anomalies': {
                'predicted_indices': int(np.sum(final_predictions)),
                'anomaly_score': final_predictions.tolist(),
                'indices': self.anomaly_indices[best_model]
            },
            'visualization': {
                'data_points': viz_data,
                'anomaly_indices': self.anomaly_indices[best_model]
            }
        }
