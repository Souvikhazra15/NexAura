"""
Data preprocessing service
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


class PreprocessingService:
    """Handle data cleaning and scaling"""
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean dataset: remove nulls and duplicates.
        
        Args:
            df: Raw dataframe
            
        Returns:
            pd.DataFrame: Cleaned dataframe
        """
        # Keep only numeric columns
        df_numeric = df.select_dtypes(include=[np.number]).copy()
        
        # Drop rows with NaN values
        df_numeric = df_numeric.dropna()
        
        # Drop complete duplicates
        df_numeric = df_numeric.drop_duplicates()
        
        # Reset index
        df_numeric.reset_index(drop=True, inplace=True)
        
        return df_numeric
    
    @staticmethod
    def scale_data(data: np.ndarray) -> tuple[np.ndarray, StandardScaler]:
        """
        Standardize features using z-score normalization.
        
        Args:
            data: Input array (n_samples, n_features)
            
        Returns:
            tuple: (scaled_data, scaler_object)
        """
        scaler = StandardScaler()
        scaled = scaler.fit_transform(data)
        return scaled, scaler
    
    @staticmethod
    def create_sequences(data: np.ndarray, seq_len: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Create sliding window sequences for LSTM.
        
        Args:
            data: Input array (n_samples, n_features)
            seq_len: Sequence length
            
        Returns:
            tuple: (sequences, labels for alignment)
        """
        sequences = []
        for i in range(len(data) - seq_len + 1):
            sequences.append(data[i:i + seq_len])
        
        return np.array(sequences)
    
    @staticmethod
    def get_stats(data: np.ndarray) -> dict:
        """
        Get data statistics.
        
        Args:
            data: Input array
            
        Returns:
            dict: Statistics summary
        """
        return {
            'n_samples': len(data),
            'n_features': data.shape[1] if len(data.shape) > 1 else 1,
            'mean': np.mean(data, axis=0).tolist() if len(data.shape) > 1 else float(np.mean(data)),
            'std': np.std(data, axis=0).tolist() if len(data.shape) > 1 else float(np.std(data)),
            'min': np.min(data, axis=0).tolist() if len(data.shape) > 1 else float(np.min(data)),
            'max': np.max(data, axis=0).tolist() if len(data.shape) > 1 else float(np.max(data)),
        }
