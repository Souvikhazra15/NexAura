# 📐 Mathematical Formulas & Equations Used in NexAura Models

This document outlines all the mathematical formulas, algorithms, and equations used in the anomaly detection models.

---

## 🔍 Table of Contents

1. [Data Preprocessing](#-data-preprocessing)
2. [Z-Score Detection](#-z-score-detection)
3. [Isolation Forest](#-isolation-forest)
4. [LSTM Autoencoder](#-lstm-autoencoder)
5. [Performance Metrics](#-performance-metrics)
6. [Threshold Determination](#-threshold-determination)

---

## 1️⃣ Data Preprocessing

### StandardScaler Normalization

**Formula:**
$$X_{scaled} = \frac{X - \mu}{\sigma}$$

**Where:**
- $X$ = Original feature value
- $\mu$ = Mean of the feature
- $\sigma$ = Standard deviation of the feature
- $X_{scaled}$ = Normalized value (zero-mean, unit-variance)

**Implementation:**
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
data_scaled = scaler.fit_transform(df_clean)

# Properties:
# - Mean = 0
# - Standard Deviation = 1
# - Preserves relative distances
```

**Why Used:**
- Puts all features on same scale
- Prevents feature dominance by magnitude
- Required for anomaly detection algorithms
- Improves model convergence

**Applied to:**
- ✓ Z-Score calculations
- ✓ Isolation Forest training
- ✓ LSTM Autoencoder input

---

## 2️⃣ Z-Score Detection

### Model 1: Z-Score Anomaly Detection

**Step 1: Calculate Z-Scores**

$$z = \frac{|x - \mu|}{\sigma}$$

**Where:**
- $x$ = Individual feature value (after standardization, this is already scaled)
- $|·|$ = Absolute value

**Implementation:**
```python
z_scores = np.abs(data_scaled)  # Already standardized, so μ=0, σ=1
# Result: z_scores of each feature for each sample
```

**Step 2: Composite Z-Score (Max Across Features)**

$$z_{composite} = \max_{j}(|z_j|)$$

**Where:**
- $z_j$ = Z-score of feature $j$
- The maximum across all features for a single sample

**Implementation:**
```python
composite_zscore = np.max(z_scores, axis=1)  # Max Z-score per sample
# axis=1 means across columns (features)
```

**Why Maximum?**
- Any extreme value in any feature indicates anomaly
- Univariate anomalies are detected per feature
- Taking max catches the most extreme deviation

**Step 3: Threshold Selection**

$$threshold = \text{percentile}(z_{composite}, 93)$$

**Implementation:**
```python
threshold_zscore_93 = np.percentile(composite_zscore, 93)
# 93rd percentile captures top ~7% as anomalies
```

**Why 93rd percentile?**
- Typical contamination in real data: 5-10%
- 93rd percentile ≈ 7% anomalies
- Balances detection rate vs. false alarms

**Step 4: Anomaly Classification**

$$\text{anomaly} = \begin{cases} 1 & \text{if } z_{composite} > threshold \\ 0 & \text{otherwise} \end{cases}$$

**Implementation:**
```python
labels_zscore_93 = (composite_zscore > threshold_zscore_93).astype(int)
# Returns 1 for anomalies, 0 for normal
```

### Complete Z-Score Algorithm

```python
# Algorithm pseudocode
1. Input: data of shape (n_samples, n_features)
2. Scale data: X = StandardScaler().fit_transform(X)
3. For each sample i:
   a. Calculate z_scores: z_i = |X_i|  (absolute value)
   b. Compute composite: z_composite_i = max(z_i)
4. Calculate threshold: T = percentile(z_composite, 93)
5. For each sample i:
   prediction_i = 1 if z_composite_i > T else 0
6. Output: Binary predictions (1 = anomaly, 0 = normal)
```

**Time Complexity:** $O(n \times m)$
- $n$ = number of samples
- $m$ = number of features

**Space Complexity:** $O(n \times m)$

---

## 3️⃣ Isolation Forest

### Model 2: Isolation Forest Ensemble

**Algorithm Overview:**

Isolation Forest is an ensemble method that isolates anomalies by randomly selecting features and split values.

**Key Principle:**
- Normal points require many splits to isolate
- Anomalies require few splits to isolate
- Measured by average path length in isolation trees

**Implementation:**
```python
from sklearn.ensemble import IsolationForest

iso_forest = IsolationForest(
    contamination=0.07,  # Expect 7% anomalies
    random_state=42      # For reproducibility
)

# Training and prediction
labels_iforest = iso_forest.fit_predict(data_scaled)
# Returns: -1 (anomaly), +1 (normal)

# Convert to binary (1 = anomaly, 0 = normal)
labels_iforest = (labels_iforest == -1).astype(int)
```

**Contamination Parameter:**

$$contamination = \frac{\text{expected anomalies}}{\text{total samples}}$$

**In our case:**
$$contamination = \frac{0.07 \times 5432}{5432} = 0.07$$

**Anomaly Score Calculation (Internal):**

$$s(x) = 2^{-\frac{E(h(x))}{c(n)}}$$

**Where:**
- $E(h(x))$ = Average path length from root to leaf (where $x$ is isolated)
- $c(n)$ = Average path length of unsuccessful search in BST of size $n$
- $s(\cdot)$ = Anomaly score in range $[0, 1]$

**Decision Rule:**

$$\text{anomaly} = \begin{cases} 1 & \text{if } s(x) > threshold \\ 0 & \text{otherwise} \end{cases}$$

The threshold is automatically set based on contamination parameter.

**Why Isolation Forest?**

✅ Handles multivariate data  
✅ Works in high dimensions  
✅ Linear time complexity  
✅ No distance calculation needed  
✅ Robust to different data distributions  

**Algorithm Steps:**
```
1. For each tree in ensemble (default 100 trees):
   a. Randomly select a feature
   b. Randomly select a split value within feature range
   c. Recursively split data until isolation achieved
   d. Compute path lengths
2. Average path lengths across all trees
3. Convert to anomaly scores
4. Apply threshold based on contamination
```

**Time Complexity:** $O(n \log n)$ for building, $O(m \log n)$ for predicting
- $n$ = number of samples
- $m$ = number of samples to predict

**Space Complexity:** $O(n \times t)$
- $t$ = number of trees

---

## 4️⃣ LSTM Autoencoder

### Model 3: Deep Learning LSTM Autoencoder

**Architecture:**

```
INPUT SEQUENCE
    ↓ (seq_len=40, n_features=8)
┌─────────────────────────────────┐
│        ENCODER STAGE            │
├─────────────────────────────────┤
│ LSTM Layer 1: 128 units         │
│ Activation: ReLU                │
│ Dropout: 0.2                    │
├─────────────────────────────────┤
│ LSTM Layer 2: 64 units          │
│ Activation: ReLU                │
│ Dropout: 0.15                   │
├─────────────────────────────────┤
│ LSTM Layer 3: 32 units          │
│ Activation: ReLU                │
│ (Output shape: 32)              │
└──────────┬──────────────────────┘
           ↓ (bottleneck)
┌──────────────────────────────────┐
│      DECODER STAGE               │
├──────────────────────────────────┤
│ RepeatVector: 40 repetitions     │
│ (Expand 32 → 40×32)              │
├──────────────────────────────────┤
│ LSTM Layer 1: 32 units           │
│ Activation: ReLU                 │
│ Dropout: 0.15                    │
├──────────────────────────────────┤
│ LSTM Layer 2: 64 units           │
│ Activation: ReLU                 │
│ Dropout: 0.2                     │
├──────────────────────────────────┤
│ LSTM Layer 3: 128 units          │
│ Activation: ReLU                 │
├──────────────────────────────────┤
│ TimeDistributed Dense: n_features│
│ (Output shape: 40×8)             │
└──────────┬──────────────────────┘
           ↓
OUTPUT RECONSTRUCTED SEQUENCE
```

### LSTM Cell Equations

**LSTM Forward Pass:**

$$f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f)$$

$$i_t = \sigma(W_i \cdot [h_{t-1}, x_t] + b_i)$$

$$\tilde{C}_t = \tanh(W_C \cdot [h_{t-1}, x_t] + b_C)$$

$$C_t = f_t \odot C_{t-1} + i_t \odot \tilde{C}_t$$

$$o_t = \sigma(W_o \cdot [h_{t-1}, x_t] + b_o)$$

$$h_t = o_t \odot \tanh(C_t)$$

**Where:**
- $f_t$ = Forget gate (decides which info to discard)
- $i_t$ = Input gate (decides which new info to add)
- $\tilde{C}_t$ = Cell state candidate (new information)
- $C_t$ = Cell state (memory)
- $o_t$ = Output gate (decides what to output)
- $h_t$ = Hidden state output
- $\sigma$ = Sigmoid activation function
- $\tanh$ = Hyperbolic tangent activation function
- $\odot$ = Element-wise multiplication (Hadamard product)
- $W$ = Weight matrices
- $b$ = Bias vectors
- $[h_{t-1}, x_t]$ = Concatenation of previous hidden state and current input

### ReLU Activation

$$\text{ReLU}(x) = \max(0, x)$$

**Properties:**
- Non-linear activation
- Introduces non-linearity
- Mitigates vanishing gradient problem

### Dropout Regularization

$$\text{Dropout}(x, p) = \begin{cases} \frac{x}{1-p} & \text{with probability } 1-p \\ 0 & \text{with probability } p \end{cases}$$

**Where:**
- $p$ = Dropout probability (0.2 = 20% of neurons dropped)
- Used to prevent overfitting

**In architecture:**
- Encoder dropout: 0.2, 0.15
- Decoder dropout: 0.15, 0.2
- Ensures model generalizes to new data

### Reconstruction Loss (MSE)

$$\text{Loss} = \frac{1}{n} \sum_{i=1}^{n} (X_i - \hat{X}_i)^2$$

**Where:**
- $X_i$ = Original input sequence
- $\hat{X}_i$ = Reconstructed sequence from autoencoder
- $n$ = Number of samples in batch

**Expanded form for sequences:**
$$\text{MSE} = \frac{1}{n \times T} \sum_{i=1}^{n} \sum_{t=1}^{T} \sum_{j=1}^{m} (x_{i,t,j} - \hat{x}_{i,t,j})^2$$

**Where:**
- $T$ = Sequence length (40)
- $m$ = Number of features (8)
- $x_{i,t,j}$ = Feature $j$ at time $t$ of sample $i$

### Training Configuration

**Optimizer: Adam**

$$m_t = \beta_1 m_{t-1} + (1 - \beta_1) g_t$$

$$v_t = \beta_2 v_{t-1} + (1 - \beta_2) g_t^2$$

$$\theta_t = \theta_{t-1} - \alpha \frac{m_t}{\sqrt{v_t} + \epsilon}$$

**Parameters:**
- Learning rate ($\alpha$) = 0.0003
- $\beta_1$ = 0.9 (moment estimate decay)
- $\beta_2$ = 0.999 (2nd moment estimate decay)
- $\epsilon$ = 1e-8 (numerical stability)

**Training Details:**
```python
Epochs: 50 maximum (with early stopping)
Batch Size: 32
Validation Split: 20-30%
Early Stopping: patience=10 epochs
Learning Rate Reduction: factor=0.5, patience=5
Min Learning Rate: 1e-5
```

### Mean Squared Error (MSE) Calculation for Anomaly Scores

**For each sequence:**
$$\text{MSE}_i = \frac{1}{T \times m} \sum_{t=1}^{T} \sum_{j=1}^{m} (x_{i,t,j} - \hat{x}_{i,t,j})^2$$

**Implementation:**
```python
predictions_lstm_full = lstm_model.predict(X_sequences)  # Shape: (n_seq, 40, 8)
mse = np.mean(np.power(X_sequences - predictions_lstm_full, 2), axis=(1, 2))
# Reduces dimensions to (n_seq,) - one MSE per sequence
```

**Why MSE for Anomalies?**
- Normal data: Learned by model → Low reconstruction error
- Anomalies: Unseen patterns → High reconstruction error
- Natural separation between normal and anomalous

### Time Series Sequence Creation

**Sliding Window:**
$$\text{Sequence}_i = [x_i, x_{i+1}, \ldots, x_{i+L-1}]$$

**Where:**
- $L$ = Sequence length (40)
- Total sequences = $n - L + 1$

**Implementation:**
```python
def create_sequences(data, seq_len):
    X = []
    for i in range(len(data) - seq_len + 1):
        X.append(data[i:i + seq_len])
    return np.array(X)

X_sequences = create_sequences(data_scaled, seq_len=40)
# Shape: (n_samples - 39, 40, 8)
```

**Properties:**
- 40 timesteps per sequence
- 8 features per timestep
- Captures temporal dependencies

---

## 5️⃣ Performance Metrics

### Confusion Matrix Elements

**Definitions:**

| Metric | Definition |
|--------|-----------|
| **TP (True Positive)** | Predicted anomaly, actually anomaly ✓ |
| **FP (False Positive)** | Predicted anomaly, actually normal ✗ |
| **FN (False Negative)** | Predicted normal, actually anomaly ✗ |
| **TN (True Negative)** | Predicted normal, actually normal ✓ |

**Calculation:**
```python
tp = np.sum((predictions == 1) & (ground_truth == 1))
fp = np.sum((predictions == 1) & (ground_truth == 0))
fn = np.sum((predictions == 0) & (ground_truth == 1))
tn = np.sum((predictions == 0) & (ground_truth == 0))
```

### Precision (False Alarm Rate)

$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$

**Interpretation:**
- What fraction of predicted anomalies are correct?
- Range: 0 to 1 (higher is better)
- 1.0 = No false alarms

**Implementation:**
```python
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
```

**When to optimize:**
- Minimize false alarms in production systems
- Reduce noise in alert systems

### Recall (Detection Rate / True Positive Rate)

$$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$

**Interpretation:**
- What fraction of actual anomalies are detected?
- Range: 0 to 1 (higher is better)
- 1.0 = Catches all anomalies

**Implementation:**
```python
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
```

**When to optimize:**
- Catch all critical failures
- Mission-critical anomaly detection

### F1-Score (Harmonic Mean)

$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

**Interpretation:**
- Balanced metric between precision and recall
- Range: 0 to 1 (higher is better)
- 1.0 = Perfect balance

**Implementation:**
```python
f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
```

**Why F1?**
- Single metric for overall performance
- Balances false alarms vs. missed detections
- Standard in ML community

### Accuracy

$$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$$

**Interpretation:**
- Fraction of all predictions that are correct
- Range: 0 to 1 (higher is better)
- Can be misleading with imbalanced data

**Implementation:**
```python
accuracy = np.mean(predictions == ground_truth)
```

**Note:**
- In imbalanced datasets (many normal, few anomalies)
- High accuracy is easy but F1 is more informative

### Metrics in Our System

**Performance Formulas Used:**
```python
# Z-Score
tp_z = np.sum((pred_z == 1) & (ground_truth == 1))
fp_z = np.sum((pred_z == 1) & (ground_truth == 0))
fn_z = np.sum((pred_z == 0) & (ground_truth == 1))
tn_z = np.sum((pred_z == 0) & (ground_truth == 0))

precision_z = tp_z / (tp_z + fp_z) if (tp_z + fp_z) > 0 else 0
recall_z = tp_z / (tp_z + fn_z) if (tp_z + fn_z) > 0 else 0
f1_z = 2 * (precision_z * recall_z) / (precision_z + recall_z) if (precision_z + recall_z) > 0 else 0
accuracy_z = np.mean(pred_z == ground_truth)

# Same for Isolation Forest and LSTM
```

---

## 6️⃣ Threshold Determination

### Z-Score Threshold

$$T_{z} = \text{percentile}(z_{composite}, p)$$

**In our implementation:**
$$T_{z} = \text{percentile}(z_{composite}, 93)$$

**Interpretation:**
- 93rd percentile means top 7% are flagged as anomalies
- Empirically chosen for IoT sensor data

### Isolation Forest Contamination

$$\text{contamination} = \frac{\# \text{ expected anomalies}}{\# \text{ total samples}}$$

**In our implementation:**
$$\text{contamination} = 0.07 \text{ (target 7% anomaly rate)}$$

### LSTM Threshold (Percentile-Based)

$$T_{\text{LSTM}} = \text{percentile}(\text{MSE}, 95)$$

**Default if not optimized:**
- 95th percentile of MSE values
- Captures extreme reconstruction errors

**Optimized via F1-Score Search:**
```python
# Pseudocode for threshold optimization
best_f1 = 0
best_threshold = 0

for threshold_candidate in range(min_mse, max_mse, step):
    predictions = (mse > threshold_candidate).astype(int)
    f1 = compute_f1(predictions, ground_truth)
    
    if f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold_candidate
```

**This finds the threshold that maximizes F1-score.**

---

## 📊 Ground Truth Generation

### Majority Voting Ensemble

**Formula:**

$$\text{ground\_truth} = z_{pred} \land \text{iso}_{pred}$$

**Where:**
- $z_{pred}$ = Z-Score prediction (1 or 0)
- $\text{iso}_{pred}$ = Isolation Forest prediction (1 or 0)
- $\land$ = Boolean AND operation

**Interpretation:**
- Only flag as anomaly if BOTH models agree
- Conservative approach
- Reduces false positives

**Implementation:**
```python
ground_truth = (labels_zscore_93 & labels_iforest).astype(int)
# Both must be 1 for result to be 1
```

**Decision Matrix:**
| Z-Score | IForest | Result | Confidence |
|---------|---------|--------|------------|
| 1 | 1 | 1 (Anomaly) | HIGH ✓✓ |
| 1 | 0 | 0 (Normal) | LOW |
| 0 | 1 | 0 (Normal) | LOW |
| 0 | 0 | 0 (Normal) | HIGH ✓✓ |

---

## 🔗 Data Flow and Formulas Integration

```
Raw CSV Data
    ↓
┌─────────────────────────────────────────────────────────┐
│ StandardScaler Normalization                            │
│ X_scaled = (X - μ) / σ                                  │
└─────────────────────┬───────────────────────────────────┘
                      ↓ (Split into Train/Val/Test)
        ┌─────────────────────────────┐
        │ Sequence Creation (LSTM)    │
        │ Seq_i = [x_i, ..., x_{i+39}]│
        └──────────────┬──────────────┘
                       ↓
    ┌──────────────────────────────────────────────┐
    │         THREE MODELS IN PARALLEL             │
    ├──────────────────────────────────────────────┤
    │ MODEL 1: Z-Score                             │
    │ z = |X|; T = percentile(max(z), 93)          │
    │                                              │
    │ MODEL 2: Isolation Forest                    │
    │ Anomaly Score based on path length           │
    │ contamination = 0.07                         │
    │                                              │
    │ MODEL 3: LSTM Autoencoder                    │
    │ MSE = mean((X - X_reconstructed)²)           │
    │ T = percentile(MSE, 95)                      │
    └────────┬──────────────────┬───────────────────┘
             ↓                  ↓
    ┌──────────────────────────────────────┐
    │ Majority Vote Ground Truth           │
    │ GT = z_pred AND iso_pred             │
    │ (LSTM used separately)               │
    └──────────────┬───────────────────────┘
                   ↓
    ┌──────────────────────────────────────┐
    │ Metrics Computation                  │
    │ TP, FP, FN, TN                       │
    │ Precision, Recall, F1, Accuracy      │
    └──────────────┬───────────────────────┘
                   ↓
    ┌──────────────────────────────────────┐
    │ Final Report Generation              │
    │ JSON with all metrics                │
    └──────────────────────────────────────┘
```

---

## 📈 Example Calculation Walkthrough

### Sample Data: 3 Features, 5 Samples

**Original Data:**
```
Temp  Pressure  Humidity
20.1  101.2     45.2
20.2  101.3     45.1
20.0  101.1     45.3
25.5  105.8     62.1  ← Anomaly
20.3  101.4     45.0
```

### Step 1: Normalization

**After StandardScaler:**
```
        Temp    Pressure  Humidity
-0.100  -0.085  -0.042
 0.050   0.090   0.015
-0.200  -0.120   0.060
 2.150   2.200   2.180  ← Extreme
 0.100   0.115  -0.033
```

### Step 2: Z-Score Model

```
composite_zscore = max(|features|, axis=1):
[-0.100, -0.085, -0.042] → max = 0.100
[ 0.050,  0.090,  0.015] → max = 0.090
[-0.200, -0.120,  0.060] → max = 0.200
[ 2.150,  2.200,  2.180] → max = 2.200 ← Very high!
[ 0.100,  0.115, -0.033] → max = 0.115

composite_zscore = [0.100, 0.090, 0.200, 2.200, 0.115]
threshold_93 = percentile([0.100, 0.090, 0.200, 2.200, 0.115], 93) ≈ 2.0

Predictions: [0, 0, 0, 1, 0]
```

### Step 3: Isolation Forest

```
contamination = 0.07
Predicts based on isolation path lengths...

Predictions: [0, 0, 0, 1, 0]
```

### Step 4: Ground Truth

```
GT = Z_pred AND IForest_pred
   = [0, 0, 0, 1, 0] AND [0, 0, 0, 1, 0]
   = [0, 0, 0, 1, 0]
```

### Step 5: LSTM Anomaly Scores

```
MSE for each sequence:
[0.012, 0.015, 0.014, 0.450, 0.013]
threshold_95 = percentile(..., 95) ≈ 0.40

Predictions: [0, 0, 0, 1, 0]
```

### Step 6: Metrics Computation

```
TP = 1 (sample 4 correctly detected)
FP = 0 (no false alarms)
FN = 0 (no missed anomalies)
TN = 4 (4 normal correctly classified)

Precision = 1 / (1 + 0) = 1.0 (Perfect!)
Recall = 1 / (1 + 0) = 1.0 (Perfect!)
F1 = 2 × (1.0 × 1.0) / (1.0 + 1.0) = 1.0 (Perfect!)
Accuracy = (1 + 4) / 5 = 1.0 (Perfect!)
```

---

## 🎯 Summary Table

| Model | Key Formula | Complexity | Use Case |
|-------|------------|-----------|----------|
| **Z-Score** | $z = \frac\|x - \mu\|\sigma$ | $O(n \times m)$ | Real-time |
| **IForest** | $s(x) = 2^{-E(h(x))/c(n)}$ | $O(n \log n)$ | Multivariate |
| **LSTM** | $MSE = \frac{1}{n} \sum (X - \hat{X})^2$ | $O(n \times T \times m)$ | Temporal patterns |
| **Metrics** | $F1 = 2 \times \frac{P \times R}{P + R}$ | $O(1)$ | Evaluation |

---

## 📚 Mathematical Notation Reference

| Symbol | Meaning |
|--------|---------|
| $\mu$ | Mean |
| $\sigma$ | Standard deviation |
| $x_i$ | Individual sample |
| $X$ | Data matrix |
| $\hat{X}$ | Reconstructed data |
| $T$ | Threshold value |
| $n$ | Number of samples |
| $m$ | Number of features |
| $T$ | Time steps / Sequence length |
| $\max$ | Maximum value |
| $\text{percentile}$ | Percentile function |
| $\odot$ | Element-wise multiplication |
| $\land$ | Logical AND |

---

## 🔗 External References

- [Z-Score (Standard Score)](https://en.wikipedia.org/wiki/Standard_score)
- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08.pdf)
- [LSTM Paper](https://www.bioinf.jku.at/publications/older/2604.pdf)
- [Autoencoder Theory](https://en.wikipedia.org/wiki/Autoencoder)
- [Confusion Matrix](https://en.wikipedia.org/wiki/Confusion_matrix)
- [F1-Score](https://en.wikipedia.org/wiki/F-score)

---

**Last Updated:** April 11, 2026  
**Version:** 1.0.0
