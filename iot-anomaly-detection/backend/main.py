"""
FastAPI Backend - Anomaly Detection System
Production-ready server with CSV upload, ML pipeline, and results API
"""
import os
import logging
import asyncio
import random
import re
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from io import BytesIO
import pandas as pd
import numpy as np

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from fastapi import FastAPI, HTTPException, WebSocket, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import CORS_ORIGINS, DEBUG
from routes.anomaly import router as anomaly_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Anomaly Detection API",
    description="Production-grade ML pipeline for IoT anomaly detection",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(anomaly_router)

# Create upload directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)


# ============= Global State =============
signal_buffer: Dict[str, deque] = {}
anomaly_history = deque(maxlen=1000)
models = {}
scalers = {}
last_model_training = {}

# Uploaded dataset state (in-memory)
DATASET_STATE: Dict[str, object] = {
    "loaded": False,
    "filename": None,
    "loaded_at": None,
    "timestamp_col": None,
    "device_type_col": None,
    "device_id_col": None,
    "df": None,
    "numeric_cols": [],
    "stream_pos": 0,
}

# Initialize signal buffers
SIGNAL_CONFIGS = {
    'TEMP_ZONE_A': {'unit': '°C', 'min': 15, 'max': 35, 'critical_high': 40, 'critical_low': 5},
    'TEMP_ZONE_B': {'unit': '°C', 'min': 15, 'max': 35, 'critical_high': 40, 'critical_low': 5},
    'PRESSURE_PSI': {'unit': 'PSI', 'min': 50, 'max': 100, 'critical_high': 120, 'critical_low': 30},
    'VIBRATION_MM': {'unit': 'mm', 'min': 0, 'max': 5, 'critical_high': 10, 'critical_low': 0},
    'POWER_KW': {'unit': 'kW', 'min': 50, 'max': 200, 'critical_high': 250, 'critical_low': 20},
    'FLOW_RATE': {'unit': 'gpm', 'min': 100, 'max': 300, 'critical_high': 400, 'critical_low': 50},
    'HUMIDITY_PCT': {'unit': '%', 'min': 30, 'max': 60, 'critical_high': 80, 'critical_low': 10},
    'VOLTAGE_V': {'unit': 'V', 'min': 220, 'max': 240, 'critical_high': 250, 'critical_low': 210},
}

for signal_id in SIGNAL_CONFIGS:
    signal_buffer[signal_id] = deque(maxlen=3600)  # Keep 1 hour of data at 1-second intervals


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Internal server error"}
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Anomaly Detection API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# ============= Data Generator =============
class MockAnomalyDetectionSystem:
    def __init__(self):
        self.signal_ids = [
            "TEMP_ZONE_A", "TEMP_ZONE_B", "TEMP_ZONE_C",
            "PRESSURE_P1", "PRESSURE_P2", "PRESSURE_P3",
            "VIBRATION_M1", "VIBRATION_M2", "VIBRATION_M3",
            "POWER_LOAD_1", "POWER_LOAD_2", "POWER_LOAD_3",
            "FLOW_RATE_F1", "FLOW_RATE_F2",
            "HUMIDITY_H1", "HUMIDITY_H2",
            "CURRENT_AMP_A1", "CURRENT_AMP_A2", "CURRENT_AMP_A3",
        ]
        self.base_values = {
            "TEMP_ZONE_A": 22.0, "TEMP_ZONE_B": 22.5, "TEMP_ZONE_C": 23.0,
            "PRESSURE_P1": 1.0, "PRESSURE_P2": 1.05, "PRESSURE_P3": 0.98,
            "VIBRATION_M1": 0.5, "VIBRATION_M2": 0.52, "VIBRATION_M3": 0.48,
            "POWER_LOAD_1": 500, "POWER_LOAD_2": 520, "POWER_LOAD_3": 480,
            "FLOW_RATE_F1": 150, "FLOW_RATE_F2": 145,
            "HUMIDITY_H1": 45, "HUMIDITY_H2": 48,
            "CURRENT_AMP_A1": 25, "CURRENT_AMP_A2": 26, "CURRENT_AMP_A3": 24,
        }
        self.history = {}
        self.anomaly_count = 0
        
    def generate_signal_values(self):
        """Generate realistic sensor data with occasional anomalies"""
        values = {}
        current_time = datetime.now()
        
        for signal_id in self.signal_ids:
            base = self.base_values[signal_id]
            
            # Add normal variation (seasonal patterns, daily cycles)
            hour = current_time.hour
            seasonal_factor = 1 + 0.03 * np.sin(2 * np.pi * hour / 24)
            
            # Normal noise
            noise = np.random.normal(0, base * 0.02)
            
            # Occasional anomalies (5% chance)
            value = base * seasonal_factor + noise
            if np.random.random() < 0.05:
                if np.random.random() < 0.5:
                    value *= (1 + np.random.uniform(0.15, 0.35))  # Spike
                else:
                    value *= (1 - np.random.uniform(0.10, 0.25))  # Drop
            
            values[signal_id] = max(0, value)
        
        return values
    
    def detect_anomalies(self, values):
        """Detect anomalies using multiple methods"""
        anomalies = []
        
        # Method 1: Statistical threshold (univariate)
        for signal_id, value in values.items():
            base = self.base_values[signal_id]
            threshold = base * 0.3  # 30% deviation
            
            if abs(value - base) > threshold:
                anomalies.append({
                    "signal": signal_id,
                    "severity": "critical" if abs(value - base) > threshold * 1.5 else "warning",
                    "deviation": (value - base) / base,
                    "value": value,
                    "type": "point"
                })
        
        # Method 2: Correlation anomalies (collective)
        if "TEMP_ZONE_A" in values and "FLOW_RATE_F1" in values:
            temp_a = values["TEMP_ZONE_A"]
            flow_f1 = values["FLOW_RATE_F1"]
            
            # If temp rises AND flow drops (inverse relationship broken)
            if temp_a > self.base_values["TEMP_ZONE_A"] * 1.15 and flow_f1 < self.base_values["FLOW_RATE_F1"] * 0.85:
                anomalies.append({
                    "signal": "TEMP-FLOW_CORRELATION",
                    "severity": "critical",
                    "deviation": 0.3,
                    "value": temp_a,
                    "type": "collective",
                    "related_signals": ["TEMP_ZONE_A", "FLOW_RATE_F1"]
                })
        
        return anomalies

detector = MockAnomalyDetectionSystem()

# ============= Dataset Helpers =============
def _detect_timestamp_column(df: pd.DataFrame) -> Optional[str]:
    candidates = []
    for col in df.columns:
        name = str(col).lower()
        if any(k in name for k in ["timestamp", "time", "datetime", "date"]):
            candidates.append(col)
    # Try explicit candidates first
    for col in candidates:
        parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True, utc=False)
        if parsed.notna().sum() > max(10, int(0.5 * len(df))):
            return str(col)
    # Fallback: any column that parses reasonably well
    for col in df.columns[: min(len(df.columns), 5)]:
        # Avoid auto-selecting numeric signal columns as timestamps.
        # pandas will happily interpret numbers as ns since epoch (1970...), which is rarely desired.
        try:
            if pd.api.types.is_numeric_dtype(df[col]):
                continue
        except Exception:
            pass
        parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True, utc=False)
        if parsed.notna().sum() > max(10, int(0.6 * len(df))):
            return str(col)
    return None


def _normalize_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, Optional[str], list[str]]:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Detect common categorical columns (keep names as they appear in df)
    lower_to_col = {str(c).strip().lower(): str(c).strip() for c in df.columns}
    device_type_col = lower_to_col.get("device_type") or lower_to_col.get("machine_type") or lower_to_col.get("device")
    device_id_col = lower_to_col.get("device_id") or lower_to_col.get("machine_id") or lower_to_col.get("asset_id")

    ts_col = _detect_timestamp_column(df)
    if ts_col and ts_col in df.columns:
        df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce", infer_datetime_format=True)
        df = df.dropna(subset=[ts_col])
        df = df.sort_values(ts_col)
    else:
        # No timestamp present; create a synthetic time axis ending "now"
        now = datetime.now()
        df.insert(0, "timestamp", [now - timedelta(seconds=(len(df) - 1 - i)) for i in range(len(df))])
        ts_col = "timestamp"

    # Coerce numeric columns
    numeric_cols: list[str] = []
    for col in df.columns:
        if col == ts_col:
            continue
        if device_type_col and col == device_type_col:
            continue
        if device_id_col and col == device_id_col:
            continue
        coerced = pd.to_numeric(df[col], errors="coerce")
        if coerced.notna().sum() >= max(5, int(0.3 * len(df))):
            df[col] = coerced
            numeric_cols.append(col)

    # Persist detected categorical columns into global state (best effort)
    DATASET_STATE["device_type_col"] = device_type_col
    DATASET_STATE["device_id_col"] = device_id_col

    df = df.dropna(subset=[ts_col])
    return df, ts_col, numeric_cols


def _read_uploaded_file_to_df(filename: str, content: bytes) -> pd.DataFrame:
    name = (filename or "").lower()
    buf = BytesIO(content)

    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(buf)

    # CSV / TXT
    try:
        # Try delimiter inference
        return pd.read_csv(buf, sep=None, engine="python")
    except Exception:
        buf.seek(0)
        # Try whitespace-delimited
        return pd.read_csv(buf, delim_whitespace=True)


def _dataset_loaded() -> bool:
    return bool(DATASET_STATE.get("loaded")) and isinstance(DATASET_STATE.get("df"), pd.DataFrame)


def _get_dataset_df() -> pd.DataFrame:
    df = DATASET_STATE.get("df")
    if not isinstance(df, pd.DataFrame):
        raise HTTPException(status_code=400, detail="No dataset loaded")
    return df


def _sanitize_token(token: str) -> str:
    # Keep ids URL-safe and consistent.
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(token).strip()).strip("_")


def _split_device_metric_signal_id(signal_id: str) -> Optional[tuple[str, str]]:
    # Composite ids are emitted as: <device_type>__<metric>
    if "__" not in signal_id:
        return None
    left, right = signal_id.split("__", 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        return None
    return left, right


def _correlation_label(value: float) -> str:
    try:
        r = float(value)
    except Exception:
        return "Unknown"

    a = abs(r)
    if a >= 0.90:
        strength = "Very Strong"
    elif a >= 0.70:
        strength = "Strong"
    elif a >= 0.40:
        strength = "Moderate"
    elif a >= 0.20:
        strength = "Weak"
    else:
        strength = "Very Weak"

    direction = "Positive" if r >= 0 else "Negative"
    return f"{strength} {direction}"


def _top_correlation_pairs(
    corr: pd.DataFrame,
    top_n: int,
    prefix: Optional[str] = None,
    min_abs: float = 0.2,
) -> list[dict]:
    if not isinstance(corr, pd.DataFrame) or corr.empty:
        return []

    cols = [str(c) for c in corr.columns]
    items: list[dict] = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            a = cols[i]
            b = cols[j]
            try:
                r = float(corr.loc[a, b])
            except Exception:
                continue
            if not np.isfinite(r):
                continue
            if abs(r) < float(min_abs):
                continue
            left = f"{prefix}__{a}" if prefix else a
            right = f"{prefix}__{b}" if prefix else b
            items.append({
                "signal1": f"{left} - {right}",
                "correlation": round(float(r), 4),
                "type": _correlation_label(r),
            })

    items.sort(key=lambda x: abs(float(x.get("correlation") or 0.0)), reverse=True)
    return items[: max(0, int(top_n))]


def _compute_signal_snapshot(
    df: pd.DataFrame,
    ts_col: str,
    numeric_cols: list[str],
    device_type_col: Optional[str] = None,
) -> list[dict]:
    if len(df) == 0:
        return []

    # If a device_type column exists, compute snapshot per device_type.
    if device_type_col and device_type_col in df.columns:
        # Interpret "current" as: take the latest 1-second bucket, then aggregate all rows
        # in that second by device_type (mean across device_ids).
        ts = pd.to_datetime(df[ts_col], errors="coerce")
        work = df.assign(_ts=ts).dropna(subset=["_ts"])
        if len(work) == 0:
            return []

        signals: list[dict] = []
        latest_sec = work["_ts"].dt.floor("1s").max()
        last_updated = pd.to_datetime(latest_sec).to_pydatetime().isoformat()

        # For each device type, compute per-second aggregates and carry-forward to latest_sec
        for device_type_val in sorted(work[device_type_col].dropna().unique().tolist(), key=lambda x: str(x)):
            if pd.isna(device_type_val):
                continue

            view = work.loc[work[device_type_col] == device_type_val, ["_ts", *numeric_cols]]
            if len(view) == 0:
                continue

            per_sec_all = (
                view.set_index("_ts")[numeric_cols]
                .resample("1s")
                .mean(numeric_only=True)
                .sort_index()
            )
            if len(per_sec_all) == 0:
                continue

            # Extend to global latest second and carry-forward.
            full_index = pd.date_range(per_sec_all.index.min().floor("1s"), latest_sec, freq="1s")
            per_sec_all = per_sec_all.reindex(full_index).ffill()

            current_row = per_sec_all.iloc[-1]
            per_sec_tail = per_sec_all.tail(60)
            baselines = per_sec_tail.mean(numeric_only=True)
            stds = per_sec_tail.std(numeric_only=True).replace(0, np.nan)

            device_type_raw = str(device_type_val)
            device_type = _sanitize_token(device_type_raw)

            for col in numeric_cols:
                value = float(current_row[col]) if pd.notna(current_row[col]) else float("nan")
                baseline = float(baselines.get(col, np.nan))
                std = float(stds.get(col, np.nan))

                if np.isfinite(baseline) and abs(baseline) > 1e-9:
                    deviation = ((value - baseline) / baseline) * 100.0
                else:
                    deviation = 0.0

                abs_dev = abs(deviation)
                if abs_dev < 10:
                    status = "normal"
                elif abs_dev < 20:
                    status = "warning"
                else:
                    status = "critical"

                signal_id = f"{device_type}__{col}"
                signals.append({
                    "id": signal_id,
                    "current_value": round(value, 2) if np.isfinite(value) else None,
                    "baseline": round(baseline, 2) if np.isfinite(baseline) else 0,
                    "deviation_percent": round(deviation, 2) if np.isfinite(deviation) else 0,
                    "status": status,
                    "unit": get_unit(col),
                    "last_updated": last_updated,
                    "_std": std,
                })

        return signals

    # Default behavior: treat numeric columns as independent signals
    last_row = df.iloc[-1]
    window = min(60, len(df))
    tail = df[numeric_cols].tail(window)
    baselines = tail.mean(numeric_only=True)
    stds = tail.std(numeric_only=True).replace(0, np.nan)

    signals: list[dict] = []
    for col in numeric_cols:
        value = float(last_row[col]) if pd.notna(last_row[col]) else float("nan")
        baseline = float(baselines.get(col, np.nan))
        std = float(stds.get(col, np.nan))

        if np.isfinite(baseline) and abs(baseline) > 1e-9:
            deviation = ((value - baseline) / baseline) * 100.0
        else:
            deviation = 0.0

        abs_dev = abs(deviation)
        if abs_dev < 10:
            status = "normal"
        elif abs_dev < 20:
            status = "warning"
        else:
            status = "critical"

        signals.append({
            "id": col,
            "current_value": round(value, 2) if np.isfinite(value) else None,
            "baseline": round(baseline, 2) if np.isfinite(baseline) else 0,
            "deviation_percent": round(deviation, 2) if np.isfinite(deviation) else 0,
            "status": status,
            "unit": get_unit(col),
            "last_updated": pd.to_datetime(last_row[ts_col]).to_pydatetime().isoformat() if ts_col in df.columns else datetime.now().isoformat(),
            "_std": std,
        })
    return signals


def _detect_anomalies_from_snapshot(signals: list[dict], limit: int = 50) -> list[dict]:
    # Simple anomaly logic based on deviation and optional z-score from rolling std
    alerts: list[dict] = []
    now = datetime.now()
    idx = 0
    for s in sorted(signals, key=lambda x: abs(x.get("deviation_percent", 0) or 0), reverse=True):
        dev = float(s.get("deviation_percent") or 0)
        if abs(dev) < 20:
            continue
        severity = "critical" if abs(dev) >= 35 else "warning"
        score = min(0.99, 0.6 + abs(dev) / 100.0)
        alerts.append({
            "id": f"ANOM-{now.strftime('%H%M%S')}-{idx}",
            "timestamp": now.isoformat(),
            "severity": severity,
            "anomaly_type": "point",
            "contributing_signals": [{"signal": s["id"], "importance": min(1.0, abs(dev) / 50.0)}],
            "score": round(score, 2),
            "message": f"{s['id']} deviation of {abs(dev):.1f}%",
            "suggested_action": get_suggested_action({"signal": s["id"]}),
            "similar_past_patterns": random.randint(0, 3),
        })
        idx += 1
        if len(alerts) >= limit:
            break
    return alerts

# ============= API Endpoints =============
@app.get("/")
async def root():
    return {
        "message": "IoT Anomaly Detection API",
        "version": "1.0",
        "status": "operational"
    }

@app.get("/api/signals")
async def get_signals(live: bool = False):
    """Get list of all monitored signals with current values"""
    if _dataset_loaded():
        df = _get_dataset_df()
        ts_col = str(DATASET_STATE.get("timestamp_col"))
        numeric_cols = list(DATASET_STATE.get("numeric_cols") or [])
        device_type_col = DATASET_STATE.get("device_type_col")

        view_df = df
        response_ts = datetime.now().isoformat()
        source = "dataset"

        # Optional live playback mode: advance through the dataset so UI updates each second.
        if live and len(df) > 0:
            try:
                pos = int(DATASET_STATE.get("stream_pos") or 0) % len(df)
            except Exception:
                pos = 0
            view_df = df.iloc[: pos + 1]
            DATASET_STATE["stream_pos"] = (pos + 1) % len(df)
            try:
                ts_val = view_df.iloc[-1][ts_col]
                parsed = pd.to_datetime(ts_val, errors="coerce")
                if pd.notna(parsed):
                    response_ts = parsed.to_pydatetime().isoformat()
            except Exception:
                pass
            source = "dataset-live"

        signals = _compute_signal_snapshot(view_df, ts_col, numeric_cols, device_type_col=str(device_type_col) if device_type_col else None)
        # Strip internal fields
        for s in signals:
            s.pop("_std", None)
        return {"signals": signals, "timestamp": response_ts, "source": source}

    values = detector.generate_signal_values()
    signals = []
    for signal_id, value in values.items():
        base = detector.base_values[signal_id]
        deviation = ((value - base) / base) * 100 if base != 0 else 0
        if abs(deviation) < 10:
            status = "normal"
        elif abs(deviation) < 20:
            status = "warning"
        else:
            status = "critical"
        signals.append({
            "id": signal_id,
            "current_value": round(value, 2),
            "baseline": round(base, 2),
            "deviation_percent": round(deviation, 2),
            "status": status,
            "unit": get_unit(signal_id),
            "last_updated": datetime.now().isoformat()
        })
    return {"signals": signals, "timestamp": datetime.now().isoformat(), "source": "mock"}

@app.get("/api/signals/{signal_id}/history")
async def get_signal_history(signal_id: str, minutes: int = 60, live: bool = False):
    """Get historical data for a specific signal"""
    if _dataset_loaded():
        df = _get_dataset_df()
        if live and len(df) > 0:
            # Use the current playback cursor (stream_pos) without advancing it.
            try:
                pos = int(DATASET_STATE.get("stream_pos") or 0) - 1
            except Exception:
                pos = 0
            pos = max(0, min(pos, len(df) - 1))
            df = df.iloc[: pos + 1]
        ts_col = str(DATASET_STATE.get("timestamp_col"))
        numeric_cols = list(DATASET_STATE.get("numeric_cols") or [])
        device_type_col = DATASET_STATE.get("device_type_col")

        # Support composite ids: <device_type>__<metric>
        composite = _split_device_metric_signal_id(signal_id)
        if composite and device_type_col and str(device_type_col) in df.columns:
            device_type, metric = composite
            if metric not in numeric_cols:
                raise HTTPException(status_code=404, detail=f"Metric '{metric}' not found in dataset")
            # device_type was sanitized in id; map by sanitized comparison
            match_mask = df[str(device_type_col)].apply(
                lambda x: _sanitize_token(str(x)) == device_type if pd.notna(x) else False
            )
            view_df = df.loc[match_mask, [ts_col, metric]]
            if len(view_df) == 0:
                raise HTTPException(status_code=404, detail=f"Device type '{device_type}' not found")

            ts = pd.to_datetime(view_df[ts_col], errors="coerce")
            view_df = view_df.assign(_ts=ts).dropna(subset=["_ts"]).sort_values("_ts")
            last_ts = view_df["_ts"].iloc[-1]
            cutoff = last_ts - pd.Timedelta(minutes=minutes)
            view_df = view_df.loc[view_df["_ts"] >= cutoff]

            # Resample to 1-second interval; forward-fill so the chart is stable.
            s = view_df.set_index("_ts")[metric].astype(float)
            s1 = s.resample("1s").mean().ffill()
            # Limit to requested window in seconds
            s1 = s1.tail(max(1, int(minutes * 60)))

            history = [
                {"timestamp": t.to_pydatetime().isoformat(), "value": round(float(v), 2)}
                for t, v in s1.items()
                if pd.notna(v)
            ]
            return {"signal_id": signal_id, "history": history, "source": "dataset", "interval": "1s"}

        # Non-composite: treat as raw numeric column
        if signal_id not in numeric_cols:
            raise HTTPException(status_code=404, detail=f"Signal '{signal_id}' not found in dataset")

        ts = pd.to_datetime(df[ts_col], errors="coerce")
        last_ts = ts.iloc[-1]
        if pd.notna(last_ts):
            cutoff = last_ts - pd.Timedelta(minutes=minutes)
            view = df.loc[ts >= cutoff, [ts_col, signal_id]]
        else:
            view = df[[ts_col, signal_id]].tail(minutes)

        view_ts = pd.to_datetime(view[ts_col], errors="coerce")
        s = pd.Series(view[signal_id].values, index=view_ts).dropna().astype(float)
        s1 = s.resample("1s").mean().ffill().tail(max(1, int(minutes * 60)))
        history = [{"timestamp": t.to_pydatetime().isoformat(), "value": round(float(v), 2)} for t, v in s1.items()]
        return {"signal_id": signal_id, "history": history, "source": "dataset", "interval": "1s"}

    history = []
    now = datetime.now()
    
    for i in range(minutes):
        timestamp = now - timedelta(minutes=i)
        base = detector.base_values.get(signal_id, 100)
        
        # Generate historical data with some variation
        hour = timestamp.hour
        seasonal = base * (1 + 0.03 * np.sin(2 * np.pi * hour / 24))
        noise = np.random.normal(0, base * 0.02)
        value = seasonal + noise
        
        history.append({
            "timestamp": timestamp.isoformat(),
            "value": round(max(0, value), 2)
        })
    
    return {
        "signal_id": signal_id,
        "history": sorted(history, key=lambda x: x["timestamp"])
    }


@app.get("/api/correlation")
async def get_correlation(top_n: int = 12, window: int = 2000, min_abs: float = 0.2):
    """Return top correlated signal pairs from the currently uploaded dataset.

    - If a device_type column exists, correlations are computed per device_type and the
      results are merged and sorted by absolute correlation.
    - If no dataset is loaded, this endpoint returns a 400 so the UI can fall back to mock.
    """
    if not _dataset_loaded():
        raise HTTPException(status_code=400, detail="No dataset loaded")

    df = _get_dataset_df()
    numeric_cols = list(DATASET_STATE.get("numeric_cols") or [])
    if len(numeric_cols) < 2:
        raise HTTPException(status_code=400, detail="Dataset has insufficient numeric columns for correlation")

    win = max(0, int(window))
    top = max(1, int(top_n))
    min_abs_val = float(min_abs)

    device_type_col = DATASET_STATE.get("device_type_col")
    items: list[dict] = []

    # If device types exist, compute correlations per device_type for better signal meaning.
    if device_type_col and str(device_type_col) in df.columns:
        try:
            device_types = df[str(device_type_col)].dropna().unique().tolist()
        except Exception:
            device_types = []

        for device_type_val in device_types:
            if pd.isna(device_type_val):
                continue
            view = df.loc[df[str(device_type_col)] == device_type_val, numeric_cols]
            if win and len(view) > win:
                view = view.tail(win)
            if len(view) < 10:
                continue

            corr = view.corr(method="pearson", numeric_only=True)
            prefix = _sanitize_token(str(device_type_val))
            items.extend(_top_correlation_pairs(corr, top_n=top, prefix=prefix, min_abs=min_abs_val))
    else:
        view = df[numeric_cols]
        if win and len(view) > win:
            view = view.tail(win)
        corr = view.corr(method="pearson", numeric_only=True)
        items = _top_correlation_pairs(corr, top_n=top, prefix=None, min_abs=min_abs_val)

    items.sort(key=lambda x: abs(float(x.get("correlation") or 0.0)), reverse=True)
    items = items[:top]

    return {
        "items": items,
        "source": "dataset",
        "filename": DATASET_STATE.get("filename"),
        "window": win,
        "min_abs": min_abs_val,
        "device_type_col": device_type_col,
    }

@app.get("/api/anomalies")
async def get_anomalies(limit: int = 50):
    """Get recent anomalies with explanations"""
    if _dataset_loaded():
        df = _get_dataset_df()
        ts_col = str(DATASET_STATE.get("timestamp_col"))
        numeric_cols = list(DATASET_STATE.get("numeric_cols") or [])
        device_type_col = DATASET_STATE.get("device_type_col")
        signals = _compute_signal_snapshot(df, ts_col, numeric_cols, device_type_col=str(device_type_col) if device_type_col else None)
        alerts = _detect_anomalies_from_snapshot(signals, limit=limit)
        return {"anomalies": alerts, "total": len(alerts), "timestamp": datetime.now().isoformat(), "source": "dataset"}

    values = detector.generate_signal_values()
    anomalies_detected = detector.detect_anomalies(values)
    
    alerts = []
    current_time = datetime.now()
    
    for idx, anomaly in enumerate(anomalies_detected[:limit]):
        if anomaly["type"] == "collective":
            severity = "critical"
            contributing = [
                {"signal": sig, "importance": 0.8 if idx == 0 else 0.4}
                for sig in anomaly.get("related_signals", [])
            ]
            message = f"Correlation anomaly detected: {', '.join(anomaly.get('related_signals', []))}"
        else:
            severity = anomaly["severity"]
            contributing = [{"signal": anomaly["signal"], "importance": abs(anomaly["deviation"])}]
            message = f"{anomaly['signal']} deviation of {abs(anomaly['deviation'])*100:.1f}%"
        
        alerts.append({
            "id": f"ANOM-{current_time.strftime('%H%M%S')}-{idx}",
            "timestamp": (current_time - timedelta(minutes=idx*2)).isoformat(),
            "severity": severity,
            "anomaly_type": anomaly["type"],
            "contributing_signals": contributing,
            "score": round(0.7 + abs(anomaly["deviation"]) * 0.3, 2),
            "message": message,
            "suggested_action": get_suggested_action(anomaly),
            "similar_past_patterns": 2
        })
    
    return {"anomalies": alerts, "total": len(alerts), "timestamp": datetime.now().isoformat()}

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get comprehensive dashboard summary"""
    if _dataset_loaded():
        df = _get_dataset_df()
        ts_col = str(DATASET_STATE.get("timestamp_col"))
        numeric_cols = list(DATASET_STATE.get("numeric_cols") or [])
        device_type_col = DATASET_STATE.get("device_type_col")
        signals = _compute_signal_snapshot(df, ts_col, numeric_cols, device_type_col=str(device_type_col) if device_type_col else None)
        alerts = _detect_anomalies_from_snapshot(signals, limit=1000)
        severity_counts = {"critical": 0, "warning": 0, "info": 0}
        for a in alerts:
            severity_counts[a["severity"]] = severity_counts.get(a["severity"], 0) + 1

        total_signals = max(1, len(numeric_cols))
        anomalous_signals = len({c["signal"] for a in alerts for c in (a.get("contributing_signals") or [])})
        health_score = 100 - (anomalous_signals / total_signals) * 100

        return {
            "health_score": round(health_score, 1),
            "total_signals": len(numeric_cols),
            "anomalies_detected": anomalous_signals,
            "severity_breakdown": severity_counts,
            "uptime": "99.8%",
            "avg_latency_ms": 12.5,
            "last_sync": datetime.now().isoformat(),
            "source": "dataset",
            "dataset": {
                "filename": DATASET_STATE.get("filename"),
                "loaded_at": DATASET_STATE.get("loaded_at"),
                "rows": int(len(df)),
            },
        }

    values = detector.generate_signal_values()
    anomalies_detected = detector.detect_anomalies(values)
    
    # Count by severity
    severity_counts = {"critical": 0, "warning": 0, "info": 0}
    for anomaly in anomalies_detected:
        severity = anomaly.get("severity", "info")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Calculate system health
    total_signals = len(values)
    anomalous_signals = len(anomalies_detected)
    health_score = 100 - (anomalous_signals / total_signals) * 100
    
    return {
        "health_score": round(health_score, 1),
        "total_signals": total_signals,
        "anomalies_detected": anomalous_signals,
        "severity_breakdown": severity_counts,
        "uptime": "99.8%",
        "avg_latency_ms": 12.5,
        "last_sync": datetime.now().isoformat()
    }

@app.websocket("/api/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    """WebSocket for live streaming sensor data"""
    await websocket.accept()
    try:
        while True:
            if _dataset_loaded():
                df = _get_dataset_df()
                ts_col = str(DATASET_STATE.get("timestamp_col"))
                numeric_cols = list(DATASET_STATE.get("numeric_cols") or [])
                device_type_col = DATASET_STATE.get("device_type_col")
                if len(df) == 0 or len(numeric_cols) == 0:
                    await asyncio.sleep(1)
                    continue

                pos = int(DATASET_STATE.get("stream_pos") or 0) % len(df)
                row = df.iloc[pos]
                DATASET_STATE["stream_pos"] = (pos + 1) % len(df)
                values = {c: float(row[c]) if pd.notna(row[c]) else 0.0 for c in numeric_cols}
                # lightweight anomalies count based on deviation from rolling baseline
                signals = _compute_signal_snapshot(df.iloc[: pos + 1], ts_col, numeric_cols, device_type_col=str(device_type_col) if device_type_col else None)
                alerts = _detect_anomalies_from_snapshot(signals, limit=10)
                anomalies_count = len(alerts)
                data = {
                    "timestamp": pd.to_datetime(row[ts_col]).to_pydatetime().isoformat(),
                    "signals": {k: round(v, 2) for k, v in values.items()},
                    "anomalies": anomalies_count,
                    "anomaly_alerts": [
                        {"signal": (a.get("contributing_signals") or [{}])[0].get("signal", "UNKNOWN"), "severity": a.get("severity", "info"), "type": a.get("anomaly_type", "point")}
                        for a in alerts[:5]
                    ],
                    "source": "dataset",
                }
                await websocket.send_json(data)
                await asyncio.sleep(1)
                continue

            values = detector.generate_signal_values()
            anomalies = detector.detect_anomalies(values)
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "signals": {k: round(v, 2) for k, v in values.items()},
                "anomalies": len(anomalies),
                "anomaly_alerts": [
                    {
                        "signal": a.get("signal", "UNKNOWN"),
                        "severity": a.get("severity", "info"),
                        "type": a.get("type", "unknown")
                    }
                    for a in anomalies[:5]
                ]
            }
            
            await websocket.send_json(data)
            await asyncio.sleep(1)  # Send update every second
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.get("/api/dataset/status")
async def get_dataset_status():
    if not _dataset_loaded():
        return {"loaded": False}
    df = _get_dataset_df()
    device_type_col = DATASET_STATE.get("device_type_col")
    device_types = []
    if device_type_col and str(device_type_col) in df.columns:
        try:
            device_types = sorted(df[str(device_type_col)].dropna().astype(str).unique().tolist())
        except Exception:
            device_types = []
    return {
        "loaded": True,
        "filename": DATASET_STATE.get("filename"),
        "loaded_at": DATASET_STATE.get("loaded_at"),
        "timestamp_col": DATASET_STATE.get("timestamp_col"),
        "device_type_col": device_type_col,
        "device_id_col": DATASET_STATE.get("device_id_col"),
        "device_types": device_types,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "numeric_columns": list(DATASET_STATE.get("numeric_cols") or []),
    }


@app.post("/api/dataset/upload")
async def upload_dataset(file: UploadFile = File(...)):
    filename = file.filename or "dataset"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        df = _read_uploaded_file_to_df(filename, content)
        df, ts_col, numeric_cols = _normalize_dataset(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse dataset: {e}")

    if len(df) == 0 or len(numeric_cols) == 0:
        raise HTTPException(status_code=400, detail="Dataset has no usable numeric signal columns")

    DATASET_STATE["loaded"] = True
    DATASET_STATE["filename"] = filename
    DATASET_STATE["loaded_at"] = datetime.now().isoformat()
    DATASET_STATE["timestamp_col"] = ts_col
    DATASET_STATE["df"] = df
    DATASET_STATE["numeric_cols"] = numeric_cols
    DATASET_STATE["stream_pos"] = 0

    return {
        "loaded": True,
        "filename": filename,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "timestamp_col": ts_col,
        "device_type_col": DATASET_STATE.get("device_type_col"),
        "device_id_col": DATASET_STATE.get("device_id_col"),
        "numeric_columns": numeric_cols,
        "sample": df.head(3).to_dict(orient="records"),
    }

# ============= Utility Functions =============
def get_unit(signal_id: str) -> str:
    """Get unit for each signal type"""
    units = {
        "CPU": "%",
        "MEMORY": "%",
        "NETWORK_IN": "KB",
        "NETWORK_OUT": "KB",
        "PACKET_RATE": "pps",
        "AVG_RESPONSE_TIME": "ms",
        "SERVICE_ACCESS_COUNT": "count",
        "FAILED_AUTH_ATTEMPTS": "count",
        "IS_ENCRYPTED": "bool",
        "GEO_LOCATION_VARIATION": "score",
        "TEMP": "°C",
        "PRESSURE": "bar",
        "VIBRATION": "mm/s",
        "POWER": "W",
        "FLOW": "L/min",
        "HUMIDITY": "%",
        "CURRENT": "A"
    }
    for key, unit in units.items():
        if key in signal_id.upper():
            return unit
    return "unit"

def get_suggested_action(anomaly: dict) -> str:
    """Get suggested investigation path based on anomaly"""
    signal = anomaly.get("signal", "")
    if "TEMP" in signal:
        return "Check cooling system, verify radiator/fan operation"
    elif "PRESSURE" in signal:
        return "Inspect pressure relief valve and pump operation"
    elif "VIBRATION" in signal:
        return "Check bearing conditions and motor alignment"
    elif "POWER" in signal:
        return "Review load distribution and circuit breaker status"
    elif "FLOW" in signal:
        return "Check for clogs in flow path, inspect pump"
    else:
        return "Manual inspection recommended for potential failure"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
