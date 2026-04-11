#!/usr/bin/env python
"""Analyze critical and warning ranges from Production System Dataset"""

import pandas as pd
import numpy as np
import json

# Load the dataset
df = pd.read_csv(r'd:\NexAura\models\OmniAnamoly\Production System Dataset.csv')

print("Dataset shape:", df.shape)
print("Columns:", list(df.columns))

# Calculate statistics for numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns

ranges_data = {}

for col in numeric_cols:
    data = df[col].dropna()
    if len(data) == 0:
        continue
    
    mean = float(data.mean())
    std = float(data.std())
    min_val = float(data.min())
    max_val = float(data.max())
    
    # Calculate thresholds using 2 and 3 sigma rule
    warning_lower = mean - (2 * std)
    warning_upper = mean + (2 * std)
    critical_lower = mean - (3 * std)
    critical_upper = mean + (3 * std)
    
    ranges_data[col] = {
        'mean': round(mean, 2),
        'std': round(std, 2),
        'min': round(min_val, 2),
        'max': round(max_val, 2),
        'warning': {
            'min': round(warning_lower, 2),
            'max': round(warning_upper, 2)
        },
        'critical': {
            'min': round(critical_lower, 2),
            'max': round(critical_upper, 2)
        }
    }
    
    print("\n" + "="*70)
    print("COLUMN: " + col.upper())
    print("="*70)
    print("Actual Range: [" + str(round(min_val, 2)) + ", " + str(round(max_val, 2)) + "]")
    print("Mean: " + str(round(mean, 2)) + " | Std Dev: " + str(round(std, 2)))
    print("WARNING Range: [" + str(round(warning_lower, 2)) + ", " + str(round(warning_upper, 2)) + "]")
    print("CRITICAL Range: [" + str(round(critical_lower, 2)) + ", " + str(round(critical_upper, 2)) + "]")

# Save to file
with open('d:\\NexAura\\anomaly_ranges.json', 'w') as f:
    json.dump(ranges_data, f, indent=2)

print("\n\n" + "="*70)
print("Ranges saved to: d:\\NexAura\\anomaly_ranges.json")
print("="*70)
