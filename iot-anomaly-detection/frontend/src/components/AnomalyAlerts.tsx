'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, TrendingUp, TrendingDown, Pause, Play } from 'lucide-react';

interface Anomaly {
  id: string;
  timestamp: string;
  detected_at?: number; // Unix timestamp when first detected
  displayed_at?: number; // Unix timestamp when should be displayed
  alerted_at?: number; // Unix timestamp when bot should alert
  severity: 'critical' | 'warning' | 'info';
  anomaly_type: string;
  message: string;
  score: number;
  signal?: string;
  value?: number;
  contributing_signals: Array<{
    signal: string;
    importance: number;
  }>;
  suggested_action: string;
  status?: 'detected' | 'displayed' | 'alerted'; // Track processing stage
}

const SEVERITY_CONFIG = {
  critical: { color: '#dc2626', bg: 'bg-red-500/10', border: 'border-red-500/30' },
  warning: { color: '#f59e0b', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
  info: { color: '#3b82f6', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
};

export default function AnomalyAlerts() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [displayedAnomalies, setDisplayedAnomalies] = useState<Anomaly[]>([]);
  const [alertedAnomalies, setAlertedAnomalies] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [stats, setStats] = useState({ total: 0, critical: 0, warning: 0 });

  const fetchAnomalies = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/anomalies?limit=999');
      const result = await response.json();
      const now = Date.now();
      
      // Add timing metadata to new anomalies
      const enrichedAnomalies = (result.anomalies || []).map((a: Anomaly, idx: number) => {
        if (!a.detected_at) {
          return {
            ...a,
            detected_at: now,
            displayed_at: now + 3000, // Show after 3 seconds
            alerted_at: now + 6000, // Alert after 6 seconds
            status: 'detected'
          };
        }
        return a;
      }).sort((a: Anomaly, b: Anomaly) => {
        const severityOrder = { critical: 0, warning: 1, info: 2 };
        return (severityOrder[a.severity] || 3) - (severityOrder[b.severity] || 3);
      });
      
      setAnomalies(enrichedAnomalies);
      
      setStats({
        total: result.total || 0,
        critical: result.critical_count || 0,
        warning: result.warning_count || 0
      });
    } catch (error) {
      console.error('Failed to fetch anomalies:', error);
    } finally {
      setLoading(false);
    }
  };

  // Timer for showing anomalies after 3-second delay
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      
      // Filter anomalies that should be displayed (3 seconds after detection)
      const toDisplay = anomalies.filter(a => {
        const displayed = displayedAnomalies.find(d => d.id === a.id);
        return !displayed && a.displayed_at && now >= a.displayed_at;
      });
      
      if (toDisplay.length > 0) {
        setDisplayedAnomalies(prev => [...prev, ...toDisplay]);
      }
      
      // Track anomalies that should alert the bot (6 seconds after detection)
      const toAlert = anomalies.filter(a => {
        const notAlerted = !alertedAnomalies.has(a.id);
        return notAlerted && a.alerted_at && now >= a.alerted_at;
      });
      
      if (toAlert.length > 0) {
        // Send to bot immediately
        toAlert.forEach(anomaly => {
          sendToBotSequentially(anomaly);
        });
        
        // Mark as alerted
        setAlertedAnomalies(prev => new Set([...prev, ...toAlert.map(a => a.id)]));
      }
    }, 100); // Check every 100ms for precise timing
    
    return () => clearInterval(interval);
  }, [anomalies, displayedAnomalies, alertedAnomalies]);

  // Send alert to bot with parameter-by-parameter delays
  const sendToBotSequentially = async (anomaly: Anomaly) => {
    try {
      // Send initial alert message
      await fetch('http://localhost:3001/api/bot/send-alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: 'broadcast', // Will broadcast to all subscribed users
          message_type: 'main',
          data: {
            severity: anomaly.severity,
            message: anomaly.message,
            timestamp: new Date().toLocaleTimeString()
          }
        })
      });
      
      // Wait 3 seconds, then send signal details
      setTimeout(async () => {
        await fetch('http://localhost:3001/api/bot/send-alert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: 'broadcast',
            message_type: 'signal',
            data: {
              signal: anomaly.signal || 'Unknown',
              value: anomaly.value,
              type: anomaly.anomaly_type
            }
          })
        });
      }, 3000);
      
      // Wait 6 seconds, then send contributing signals
      setTimeout(async () => {
        await fetch('http://localhost:3001/api/bot/send-alert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: 'broadcast',
            message_type: 'signals',
            data: {
              contributing_signals: anomaly.contributing_signals
            }
          })
        });
      }, 6000);
      
      // Wait 9 seconds, then send suggested action
      setTimeout(async () => {
        await fetch('http://localhost:3001/api/bot/send-alert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: 'broadcast',
            message_type: 'action',
            data: {
              suggested_action: anomaly.suggested_action,
              score: anomaly.score
            }
          })
        });
      }, 9000);
    } catch (error) {
      console.error('Failed to send alert to bot:', error);
    }
  };

  useEffect(() => {
    fetchAnomalies();
    
    // Set up polling
    if (streaming) {
      const interval = setInterval(fetchAnomalies, 2000);
      return () => clearInterval(interval);
    }
  }, [streaming]);

  const handleStartStreaming = async () => {
    setStreaming(true);
    setDisplayedAnomalies([]);
    setAlertedAnomalies(new Set());
    try {
      await fetch('http://localhost:8000/api/signals/stream');
    } catch (error) {
      console.error('Failed to start stream:', error);
    }
  };

  const handleStopStreaming = async () => {
    setStreaming(false);
    try {
      await fetch('http://localhost:8000/api/signals/stop', { method: 'POST' });
    } catch (error) {
      console.error('Failed to stop stream:', error);
    }
  };

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
      {/* Control Panel */}
      <div className="card bg-gradient-to-r from-slate-800 to-slate-700 border border-slate-600 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            Alert Streaming Control
          </h3>
          <div className="flex gap-2">
            {!streaming ? (
              <button
                onClick={handleStartStreaming}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-all duration-200"
              >
                <Play className="w-4 h-4" />
                Start Stream
              </button>
            ) : (
              <button
                onClick={handleStopStreaming}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-semibold transition-all duration-200"
              >
                <Pause className="w-4 h-4" />
                Stop Stream
              </button>
            )}
          </div>
        </div>

        {/* Cascade Timeline Information */}
        {streaming && (
          <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded">
            <p className="text-xs font-semibold text-blue-300 mb-2">⏱️ Real-World Alert Cascade (3-Second Intervals):</p>
            <div className="flex items-center justify-between text-xs text-slate-300">
              <div className="text-center">
                <div className="text-green-400 font-bold">T+0s</div>
                <div>Signal Detected</div>
              </div>
              <div className="flex-1 mx-2 h-1 bg-gradient-to-r from-green-400 via-yellow-400 to-blue-400"></div>
              <div className="text-center">
                <div className="text-yellow-400 font-bold">T+3s</div>
                <div>Alert Shown</div>
              </div>
              <div className="flex-1 mx-2 h-1 bg-gradient-to-r from-yellow-400 via-yellow-400 to-blue-400"></div>
              <div className="text-center">
                <div className="text-blue-400 font-bold">T+6s</div>
                <div>Bot Notifies</div>
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-2 mt-2">Bot sends: Main Alert → Signal Details (3s) → Contributing Signals (3s) → Recommended Action (3s)</p>
          </div>
        )}

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-slate-900/50 rounded p-3 border border-slate-600/50">
            <p className="text-xs text-slate-400">Total Alerts</p>
            <p className="text-2xl font-bold text-cyan-400">{stats.total}</p>
          </div>
          <div className="bg-red-900/20 rounded p-3 border border-red-500/30">
            <p className="text-xs text-slate-400">Critical</p>
            <p className="text-2xl font-bold text-red-400">{stats.critical}</p>
          </div>
          <div className="bg-amber-900/20 rounded p-3 border border-amber-500/30">
            <p className="text-xs text-slate-400">Warnings</p>
            <p className="text-2xl font-bold text-amber-400">{stats.warning}</p>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
          <label className="flex items-center gap-2 cursor-pointer hover:text-slate-300">
            <input 
              type="checkbox" 
              checked={autoScroll} 
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="w-4 h-4"
            />
            Auto-scroll
          </label>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3 max-h-[70vh] overflow-y-auto scroll-smooth">
        {displayedAnomalies.length === 0 ? (
          <div className="card text-center py-8 text-slate-400">
            <p>No anomalies detected</p>
            <p className="text-xs mt-2">Click "Start Stream" to begin monitoring</p>
          </div>
        ) : (
          displayedAnomalies.map((anomaly) => {
            const config = SEVERITY_CONFIG[anomaly.severity];
            const now = Date.now();
            const isAlerted = alertedAnomalies.has(anomaly.id);
            const timeUntilAlert = anomaly.alerted_at ? Math.max(0, anomaly.alerted_at - now) : 0;
            
            return (
              <div
                key={anomaly.id}
                onClick={() => setSelectedAnomaly(anomaly)}
                className={`card cursor-pointer transition-all duration-200 border-l-4 ${config.bg} ${config.border} hover:shadow-lg hover:shadow-${anomaly.severity === 'critical' ? 'red' : 'amber'}-500/20 animate-in fade-in slide-in-from-bottom`}
                style={{ borderLeftColor: config.color }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <AlertCircle size={18} style={{ color: config.color }} className="animate-pulse" />
                      <span className="text-sm font-semibold">{anomaly.severity.toUpperCase()}</span>
                      <span className="text-xs px-2 py-1 bg-white/10 rounded">
                        {anomaly.anomaly_type}
                      </span>
                      {anomaly.signal && (
                        <span className="text-xs px-2 py-1 bg-white/5 rounded border border-slate-500/50">
                          {anomaly.signal}
                        </span>
                      )}
                      
                      {/* Status cascade indicators */}
                      <div className="flex items-center gap-1 ml-auto text-xs">
                        <span className="px-2 py-1 bg-green-500/20 border border-green-500/50 rounded text-green-300">
                          ✓ Detected
                        </span>
                        <span className={`px-2 py-1 rounded border ${isAlerted ? 'bg-blue-500/20 border-blue-500/50 text-blue-300' : 'bg-slate-700/50 border-slate-600/50 text-slate-400'}`}>
                          {isAlerted ? '✓ Alerted' : `Bot in ${Math.ceil(timeUntilAlert / 1000)}s`}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm mt-2 text-slate-100">{anomaly.message}</p>
                    {anomaly.value !== undefined && (
                      <div className="text-xs text-slate-400 mt-1">
                        Current Value: <strong className="text-white">{anomaly.value.toFixed(2)}</strong>
                      </div>
                    )}
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
              x
            </button>
          </div>

          <div className="space-y-4">
            {/* Main Message */}
            <div className="bg-slate-800/50 border border-slate-600 rounded p-3">
              <p className="text-sm text-slate-300">{selectedAnomaly.message}</p>
              {selectedAnomaly.value !== undefined && (
                <p className="text-xs text-slate-400 mt-2">
                  Value: <strong>{selectedAnomaly.value.toFixed(2)}</strong>
                </p>
              )}
            </div>

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
              <h4 className="text-sm font-semibold text-blue-300 mb-2">Suggested Investigation</h4>
              <p className="text-sm text-slate-300">{selectedAnomaly.suggested_action}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
