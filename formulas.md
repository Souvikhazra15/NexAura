# Z-scores:

z = |x - μ| / σ
composite_zscore = max(z) [across all features]
threshold = percentile(composite_zscore, 93)
prediction = 1 if composite_zscore > threshold else 0

# Isolation Forest:

s(x) = 2^(-E(h(x)) / c(n))
contamination = 0.07 (target 7%)
prediction based on isolation path length

# LSTM Autoencoder:

MSE = (1/(n×T)) × Σ(X_i - Ŷ_i)²
threshold = percentile(MSE, 95)
prediction = 1 if MSE > threshold else 0

# F1 Scores: 2*(Precision * Recall) / (Precision + Recall)

# Precision = TP / (TP + FP)


# Recall = TP / (TP + FN)