'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, TrendingUp, TrendingDown } from 'lucide-react';

interface Anomaly {
  id: string;
  timestamp: string;
  severity: 'critical' | 'warning' | 'info';
  anomaly_type: string;
  message: string;
  score: number;
  contributing_signals: Array<{
    signal: string;
    importance: number;
  }>;
  suggested_action: string;
}

const SEVERITY_CONFIG = {
  critical: { color: '#dc2626', bg: 'bg-red-500/10', border: 'border-red-500/30' },
  warning: { color: '#f59e0b', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
  info: { color: '#3b82f6', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
};

export default function AnomalyAlerts() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/anomalies?limit=20');
        const result = await response.json();
        setAnomalies(result.anomalies || []);
      } catch (error) {
        console.error('Failed to fetch anomalies:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading)
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="card h-24 bg-slate-800/50 animate-pulse" />
        ))}
      </div>
    );

  return (
    <div className="space-y-4">
      {/* Alerts List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {anomalies.length === 0 ? (
          <div className="card text-center py-8 text-slate-400">
            <p>No anomalies detected</p>
          </div>
        ) : (
          anomalies.map((anomaly) => {
            const config = SEVERITY_CONFIG[anomaly.severity];
            return (
              <div
                key={anomaly.id}
                onClick={() => setSelectedAnomaly(anomaly)}
                className={`card cursor-pointer transition-all border-l-4 ${config.bg} ${config.border}`}
                style={{ borderLeftColor: config.color }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <AlertCircle size={18} style={{ color: config.color }} />
                      <span className="text-sm font-semibold">{anomaly.severity.toUpperCase()}</span>
                      <span className="text-xs px-2 py-1 bg-white/10 rounded">
                        {anomaly.anomaly_type}
                      </span>
                    </div>
                    <p className="text-sm mt-2 text-slate-100">{anomaly.message}</p>
                    <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
                      <span>
                        Score:{' '}
                        <strong style={{ color: config.color }}>
                          {(anomaly.score * 100).toFixed(0)}%
                        </strong>
                      </span>
                      <span>{new Date(anomaly.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="font-semibold text-cyan-400">
                      {anomaly.contributing_signals.length} signals
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Detailed View */}
      {selectedAnomaly && (
        <div className="card border-2 border-cyan-500/50 bg-cyan-500/5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Anomaly Details</h3>
            <button
              onClick={() => setSelectedAnomaly(null)}
              className="text-slate-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            {/* Contributing Signals */}
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Contributing Signals</h4>
              <div className="space-y-2">
                {selectedAnomaly.contributing_signals.map((signal, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-slate-800/50 px-3 py-2 rounded">
                    <span className="text-sm">{signal.signal}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-slate-700 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-cyan-500 h-full"
                          style={{ width: `${signal.importance * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-400 w-8 text-right">
                        {(signal.importance * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Suggested Action */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded p-3">
              <h4 className="text-sm font-semibold text-blue-300 mb-2">🔍 Suggested Investigation</h4>
              <p className="text-sm text-slate-300">{selectedAnomaly.suggested_action}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
