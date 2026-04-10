'use client';

import { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle } from 'lucide-react';

export default function ModelPerformance() {
  const [metrics, setMetrics] = useState({
    precision: 0.92,
    recall: 0.88,
    f1_score: 0.90,
    latency_ms: 12.5,
    accuracy: 0.95,
  });

  const performanceGrades = [
    { name: 'Precision', value: metrics.precision, grade: 'A+', color: '#10b981' },
    { name: 'Recall', value: metrics.recall, grade: 'A', color: '#10b981' },
    { name: 'F1 Score', value: metrics.f1_score, grade: 'A+', color: '#10b981' },
    { name: 'Accuracy', value: metrics.accuracy, grade: 'A+', color: '#10b981' },
  ];

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
        <Activity size={20} className="text-cyan-400" />
        Model Performance Metrics
      </h3>

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {performanceGrades.map((metric) => (
          <div key={metric.name} className="bg-slate-800/50 rounded-lg p-4 text-center border border-slate-700">
            <p className="text-slate-400 text-sm mb-2">{metric.name}</p>
            <div className="flex items-end justify-center gap-2">
              <span className="text-3xl font-bold" style={{ color: metric.color }}>
                {(metric.value * 100).toFixed(0)}%
              </span>
              <span className="text-2xl font-bold text-green-400 mb-1">{metric.grade}</span>
            </div>
            <div className="mt-3 w-full bg-slate-700 rounded-full h-2 overflow-hidden">
              <div className="bg-gradient-to-r from-cyan-500 to-green-500 h-2" style={{ width: `${metric.value * 100}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Latency & Status */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <p className="text-blue-300 text-sm font-medium mb-2">Average Latency</p>
          <p className="text-3xl font-bold text-blue-400">{metrics.latency_ms}ms</p>
          <p className="text-xs text-blue-300/60 mt-2">✓ Optimal for real-time</p>
        </div>

        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
          <p className="text-green-300 text-sm font-medium mb-2">System Status</p>
          <div className="flex items-center gap-2">
            <CheckCircle size={24} className="text-green-400 animate-pulse" />
            <span className="text-lg font-bold text-green-400">Optimal</span>
          </div>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="mt-6 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-lg p-4 border border-cyan-500/20">
        <p className="text-sm text-slate-200">
          <strong>Summary:</strong> Model ensemble achieving 95% accuracy with 12.5ms latency. Highly suitable for real-time production deployment.
        </p>
      </div>
    </div>
  );
}
