export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const SEVERITY_COLORS = {
  critical: '#dc2626',
  warning: '#f59e0b',
  info: '#3b82f6',
};

export const SIGNAL_UNITS = {
  TEMP: '°C',
  PRESSURE: 'bar',
  VIBRATION: 'mm/s',
  POWER: 'W',
  FLOW: 'L/min',
  HUMIDITY: '%',
  CURRENT: 'A',
};

export const ANOMALY_TYPES = {
  point: 'Sudden Spike/Drop',
  contextual: 'Abnormal Pattern',
  collective: 'Multi-Signal Correlation',
};
