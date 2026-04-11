"""
Anomaly Detection Models
- Z-Score (Statistical)
- Isolation Forest (Ensemble)
- LSTM Autoencoder (Deep Learning)
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, RepeatVector, TimeDistributed
from tensorflow.keras.optimizers import Adam
from config.settings import LSTM_EPOCHS, LSTM_BATCH_SIZE, LSTM_DROPOUT, LSTM_LEARNING_RATE


class ZScoreDetector:
    """
    Statistical anomaly detection using Z-score.
    Flags samples where max Z-score exceeds threshold.
    """
    
    def __init__(self, threshold: float = 2.5):
        self.threshold = threshold
    
    def fit(self, X):
        """Fit not needed for Z-score (stateless)"""
        pass
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomalies using Z-score.
        
        Args:
            X: Scaled data (n_samples, n_features)
            
        Returns:
            np.ndarray: Binary predictions (0=normal, 1=anomaly)
        """
        z_scores = np.abs(X)
        composite = np.max(z_scores, axis=1)
        return (composite > self.threshold).astype(int)
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores"""
        return np.max(np.abs(X), axis=1)


class IsolationForestDetector:
    """
    Ensemble-based anomaly detection.
    Isolates anomalies by random feature selection and splitting.
    """
    
    def __init__(self, contamination: float = 0.07, random_state: int = 42):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        self.contamination = contamination
    
    def fit(self, X: np.ndarray):
        """Fit the Isolation Forest"""
        self.model.fit(X)
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomalies.
        
        Args:
            X: Data (n_samples, n_features)
            
        Returns:
            np.ndarray: Binary predictions (0=normal, 1=anomaly)
        """
        predictions = self.model.predict(X)
        return (predictions == -1).astype(int)  # -1 → anomaly, 1 → normal
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores"""
        return self.model.score_samples(X)


class LSTMAutoencoder:
    """
    Deep learning anomaly detection using LSTM Autoencoder.
    Trains on normal data only, flags high reconstruction errors as anomalies.
    """
    
    def __init__(self, seq_len: int, n_features: int):
        self.seq_len = seq_len
        self.n_features = n_features
        self.model = None
        self.threshold = None
        self._build_model()
    
    def _build_model(self):
        """Build LSTM Autoencoder architecture"""
        inputs = Input(shape=(self.seq_len, self.n_features))
        
        # Encoder: 3-layer LSTM compression
        encoded = LSTM(128, activation='relu', return_sequences=True)(inputs)
        encoded = Dropout(LSTM_DROPOUT)(encoded)
        encoded = LSTM(64, activation='relu', return_sequences=True)(encoded)
        encoded = Dropout(LSTM_DROPOUT)(encoded)
        encoded = LSTM(32, activation='relu', return_sequences=False)(encoded)
        
        # Decoder: 3-layer LSTM expansion
        decoded = RepeatVector(self.seq_len)(encoded)
        decoded = LSTM(32, activation='relu', return_sequences=True)(decoded)
        decoded = Dropout(LSTM_DROPOUT)(decoded)
        decoded = LSTM(64, activation='relu', return_sequences=True)(decoded)
        decoded = Dropout(LSTM_DROPOUT)(decoded)
        decoded = LSTM(128, activation='relu', return_sequences=True)(decoded)
        decoded = TimeDistributed(Dense(self.n_features))(decoded)
        
        self.model = Model(inputs,decoded)
        self.model.compile(optimizer=Adam(learning_rate=LSTM_LEARNING_RATE), loss='mse')
    
    def fit(self, X_normal: np.ndarray, validation_split: float = 0.2):
        """
        Train on normal data only.
        
        Args:
            X_normal: Normal samples only (n_samples, seq_len, n_features)
            validation_split: Fraction for validation
        """
        self.model.fit(
            X_normal, X_normal,
            epochs=LSTM_EPOCHS,
            batch_size=LSTM_BATCH_SIZE,
            validation_split=validation_split,
            verbose=0
        )
    
    def predict(self, X: np.ndarray, threshold_percentile: int = 95) -> np.ndarray:
        """
        Predict anomalies using reconstruction error.
        
        Args:
            X: Data (n_samples, seq_len, n_features)
            threshold_percentile: Percentile for threshold
            
        Returns:
            np.ndarray: Binary predictions
        """
        reconstructions = self.model.predict(X, verbose=0)
        mse = np.mean(np.power(X - reconstructions, 2), axis=(1, 2))
        
        threshold = np.percentile(mse, threshold_percentile)
        self.threshold = threshold
        
        return (mse > threshold).astype(int)
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Return reconstruction error scores"""
        reconstructions = self.model.predict(X, verbose=0)
        return np.mean(np.power(X - reconstructions, 2), axis=(1, 2))


class  MetricsComputer:
    """Compute evaluation metrics"""
    
    @staticmethod
    def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, model_name: str = "Model") -> dict:
        """
        Compute precision, recall, F1-score with edge case handling.
        
        Args:
            y_true: Ground truth labels
            y_pred: Predictions
            model_name: Model name for identification
            
        Returns:
            dict: Metrics dictionary
        """
        # Handle edge cases
        if len(np.unique(y_pred)) == 1:
            # All predictions are same class
            if y_pred[0] == 0:
                return {
                    'model': model_name,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1_score': 0.0,
                    'tp': 0, 'fp': 0, 'fn': np.sum(y_true), 'tn': np.sum(y_true == 0)
                }
            else:
                n_anom = np.sum(y_true)
                return {
                    'model': model_name,
                    'precision': n_anom / len(y_true) if len(y_true) > 0 else 0,
                    'recall': 1.0 if n_anom > 0 else 0,
                    'f1_score': (2 * n_anom / len(y_true) / (n_anom / len(y_true) + 1)) if n_anom > 0 else 0,
                    'tp': n_anom, 'fp': len(y_true) - n_anom, 'fn': 0, 'tn': 0
                }
        
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        try:
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        except:
            tn, tp = np.sum((y_true == 0) & (y_pred == 0)), np.sum((y_true == 1) & (y_pred == 1))
            fp, fn = np.sum((y_true == 0) & (y_pred == 1)), np.sum((y_true == 1) & (y_pred == 0))
        
        return {
            'model': model_name,
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'tp': int(tp), 'fp': int(fp), 'fn': int(fn), 'tn': int(tn)
        }
