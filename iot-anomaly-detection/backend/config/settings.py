# Configuration settings for anomaly detection backend
import os

# File upload constraints
MAX_FILE_SIZE_MB = 50  # Maximum upload size: 50MB
ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')

# ML Model parameters
SEQUENCE_LENGTH = 30
LSTM_EPOCHS = 50
LSTM_BATCH_SIZE = 32
LSTM_DROPOUT = 0.2
LSTM_LEARNING_RATE = 0.001

# Anomaly detection thresholds
ZSCORE_THRESHOLD = 2.5
ISOLATION_FOREST_CONTAMINATION = 0.07

# Server configuration
DEBUG = True
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "*"]
