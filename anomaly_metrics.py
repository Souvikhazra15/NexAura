"""
Anomaly Detection Metrics Module
=================================
Clean, production-ready implementation for evaluating anomaly detection models.

Usage:
    from anomaly_metrics import safe_metrics, create_ground_truth
    
    # Create ground truth
    y_true = create_ground_truth(data_scaled, method='hybrid')
    
    # Compute metrics
    metrics = safe_metrics(y_true, predictions, 'ModelName')
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    confusion_matrix, roc_curve, auc
)
from sklearn.ensemble import IsolationForest


def create_ground_truth(data_scaled, method='hybrid', contamination=0.07):
    """
    Create ground truth labels using statistical methods when labels unavailable.
    
    Parameters
    ----------
    data_scaled : ndarray, shape (n_samples, n_features)
        Standardized feature matrix
    method : str, default='hybrid'
        'zscore_ensemble': Max Z-score across features
        'isolation_forest': Isolation Forest algorithm
        'hybrid': Union of Z-Score and Isolation Forest
    contamination : float, default=0.07
        Expected fraction of anomalies (0-1)
    
    Returns
    -------
    labels : ndarray, shape (n_samples,)
        Binary labels (0=normal, 1=anomaly)
    threshold : float or tuple
        Threshold value(s) used
    method_name : str
        Description of method used
    
    Examples
    --------
    >>> y_true, _, _ = create_ground_truth(X_scaled, method='hybrid')
    >>> y_true
    array([0, 0, 1, 0, 1, ...])
    """
    
    if method == 'zscore_ensemble':
        # Composite Z-score: max deviation from mean
        z_scores = np.abs(data_scaled)
        composite_z = np.max(z_scores, axis=1)
        threshold = np.percentile(composite_z, 100 * (1 - contamination))
        labels = (composite_z > threshold).astype(int)
        return labels, threshold, 'Z-Score (Composite)'
    
    elif method == 'isolation_forest':
        # Unsupervised ensemble method
        iso = IsolationForest(contamination=contamination, random_state=42)
        labels = (iso.fit_predict(data_scaled) == -1).astype(int)
        return labels, contamination, 'Isolation Forest'
    
    elif method == 'hybrid':
        # Combine both methods: union approach (higher recall)
        z_scores = np.abs(data_scaled)
        composite_z = np.max(z_scores, axis=1)
        threshold_z = np.percentile(composite_z, 100 * (1 - contamination))
        labels_z = (composite_z > threshold_z).astype(int)
        
        iso = IsolationForest(contamination=contamination, random_state=42)
        labels_iso = (iso.fit_predict(data_scaled) == -1).astype(int)
        
        # Union: flag as anomaly if either method agrees
        labels_hybrid = np.maximum(labels_z, labels_iso)
        return labels_hybrid, (threshold_z, contamination), 'Hybrid (Z + IF)'
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'zscore_ensemble', 'isolation_forest', or 'hybrid'")


def safe_metrics(y_true, y_pred, model_name='Model'):
    """
    Compute metrics with comprehensive edge case handling.
    
    Handles:
    - Division by zero (precision/recall when no positives)
    - Class imbalance (returns valid scores)
    - Constant predictions (all 0s or all 1s)
    - Confusion matrix extraction (safe unpacking)
    
    Parameters
    ----------
    y_true : array-like, shape (n_samples,)
        Ground truth binary labels (0 or 1)
    y_pred : array-like, shape (n_samples,)
        Predicted binary labels (0 or 1)
    model_name : str, default='Model'
        Name of the model for identification
    
    Returns
    -------
    dict
        Dictionary containing:
        - Model: Model name
        - Precision: TP / (TP + FP)
        - Recall: TP / (TP + FN)
        - F1-Score: 2 * (Precision * Recall) / (Precision + Recall)
        - TP, FP, FN, TN: Confusion matrix elements
        - Anomalies_Detected: Total positive predictions
    
    Examples
    --------
    >>> y_true = np.array([0, 0, 1, 0, 1, 0])
    >>> y_pred = np.array([0, 0, 1, 0, 0, 0])
    >>> metrics = safe_metrics(y_true, y_pred, 'MyModel')
    >>> metrics['F1-Score']
    0.6666666666666666
    """
    
    # Validate inputs
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    
    # --- EDGE CASE 1: Model predicts only normal (all 0s) ---
    if len(np.unique(y_pred)) == 1 and np.unique(y_pred)[0] == 0:
        precision = 1.0 if np.sum(y_true) == 0 else 0.0
        recall = 0.0
        f1 = 0.0
    
    # --- EDGE CASE 2: Model predicts everything as anomaly (all 1s) ---
    elif len(np.unique(y_pred)) == 1 and np.unique(y_pred)[0] == 1:
        n_true_anomalies = np.sum(y_true)
        precision = n_true_anomalies / len(y_true) if len(y_true) > 0 else 0.0
        recall = 1.0 if n_true_anomalies > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # --- NORMAL CASE: Mixed predictions ---
    else:
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # --- Confusion Matrix Extraction (Safe Unpacking) ---
    if len(np.unique(y_true)) > 1 and len(np.unique(y_pred)) > 1:
        try:
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        except:
            tn, fp, fn, tp = 0, 0, 0, 0
    else:
        tn, fp, fn, tp = 0, 0, 0, 0
    
    return {
        'Model': model_name,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1,
        'TP': int(tp),
        'FP': int(fp),
        'FN': int(fn),
        'TN': int(tn),
        'Anomalies_Detected': int(np.sum(y_pred))
    }


def evaluate_models(y_true, predictions_dict, print_results=True):
    """
    Evaluate multiple models and return comparison DataFrame.
    
    Parameters
    ----------
    y_true : array-like
        Ground truth labels
    predictions_dict : dict
        Dictionary of {model_name: predictions_array}
    print_results : bool, default=True
        Whether to print formatted results
    
    Returns
    -------
    metrics_df : pd.DataFrame
        Metrics for all models
    
    Examples
    --------
    >>> predictions = {
    ...     'Z-Score': z_pred,
    ...     'Isolation Forest': iso_pred,
    ...     'LSTM': lstm_pred
    ... }
    >>> df = evaluate_models(y_true, predictions)
    """
    
    metrics_list = []
    for model_name, predictions in predictions_dict.items():
        metrics = safe_metrics(y_true, predictions, model_name)
        metrics_list.append(metrics)
    
    metrics_df = pd.DataFrame(metrics_list)
    
    if print_results:
        print('\n' + '='*100)
        print('MODEL EVALUATION METRICS')
        print('='*100)
        
        # Display main metrics
        print('\n' + metrics_df[['Model', 'Precision', 'Recall', 'F1-Score', 'TP', 'FP', 'FN']].to_string(index=False))
        
        # Summary statistics
        print('\n' + '='*100)
        print('SUMMARY STATISTICS')
        print('='*100)
        best_f1_idx = metrics_df['F1-Score'].idxmax()
        best_prec_idx = metrics_df['Precision'].idxmax()
        best_rec_idx = metrics_df['Recall'].idxmax()
        
        print(f'\nBest F1-Score:   {metrics_df.loc[best_f1_idx, "F1-Score"]:.4f} ({metrics_df.loc[best_f1_idx, "Model"]})')
        print(f'Best Precision:  {metrics_df.loc[best_prec_idx, "Precision"]:.4f} ({metrics_df.loc[best_prec_idx, "Model"]})')
        print(f'Best Recall:     {metrics_df.loc[best_rec_idx, "Recall"]:.4f} ({metrics_df.loc[best_rec_idx, "Model"]})')
        print(f'Avg F1-Score:    {metrics_df["F1-Score"].mean():.4f}')
        print(f'Avg Precision:   {metrics_df["Precision"].mean():.4f}')
        print(f'Avg Recall:      {metrics_df["Recall"].mean():.4f}')
        print('\n' + '='*100)
    
    return metrics_df


if __name__ == '__main__':
    # Example usage
    print("Anomaly Detection Metrics Module - Quick Start Guide")
    print("="*60)
    
    # Simulate data
    from sklearn.preprocessing import StandardScaler
    
    # Random data
    X = np.random.randn(1000, 10)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Create ground truth
    y_true, _, method = create_ground_truth(X_scaled, method='hybrid', contamination=0.08)
    print(f"\nGround Truth Method: {method}")
    print(f"Anomalies detected: {np.sum(y_true)} ({100*np.sum(y_true)/len(y_true):.1f}%)")
    
    # Simulate predictions from 3 models
    predictions = {
        'Z-Score': (np.random.randn(1000) > 1.5).astype(int),
        'Isolation Forest': (np.random.randn(1000) > 1.8).astype(int),
        'LSTM Autoencoder': (np.random.randn(1000) > 1.2).astype(int),
    }
    
    # Evaluate
    metrics_df = evaluate_models(y_true, predictions, print_results=True)
    
    print("\nDataFrame output:")
    print(metrics_df)
