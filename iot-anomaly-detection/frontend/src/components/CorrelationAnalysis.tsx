'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ZoomIn } from 'lucide-react';

interface CorrelationItem {
  signal1: string;
  correlation: number;
  type: string;
}

export default function CorrelationAnalysis() {
  const [correlationData, setCorrelationData] = useState<CorrelationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock correlation matrix data
    const mockData = [
      { signal1: 'TEMP-PRESSURE', correlation: 0.87, type: 'Strong Positive' },
      { signal1: 'TEMP-VIBRATION', correlation: 0.42, type: 'Moderate' },
      { signal1: 'PRESSURE-FLOW', correlation: 0.91, type: 'Strong Positive' },
      { signal1: 'VIBRATION-POWER', correlation: 0.65, type: 'Moderate' },
      { signal1: 'HUMIDITY-TEMP', correlation: -0.23, type: 'Weak Negative' },
      { signal1: 'POWER-CURRENT', correlation: 0.95, type: 'Very Strong' },
    ];
    setCorrelationData(mockData);
    setLoading(false);
  }, []);

  if (loading) return <div className="card h-96 bg-slate-800/50 animate-pulse" />;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <ZoomIn size={20} className="text-cyan-400" />
          Signal Correlation Analysis
        </h3>
        <span className="text-xs px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-cyan-300">
          6 strong correlations
        </span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={correlationData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="signal1" stroke="#94a3b8" angle={-45} textAnchor="end" height={100} fontSize={12} />
          <YAxis stroke="#94a3b8" label={{ value: 'Correlation', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
            }}
            formatter={(value) => {
              const n = typeof value === 'number' ? value : Number(value);
              if (!Number.isFinite(n)) return String(value);
              return `${(n * 100).toFixed(0)}%`;
            }}
          />
          <Bar dataKey="correlation" fill="#0ea5e9" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-3">
        {correlationData.map((item, idx) => (
          <div key={idx} className="bg-slate-800/50 rounded p-3 text-sm border border-slate-700">
            <p className="text-slate-400">{item.signal1}</p>
            <div className="flex items-end justify-between mt-2">
              <span className="font-bold text-cyan-400">{(item.correlation * 100).toFixed(0)}%</span>
              <span className="text-xs text-slate-500">{item.type}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
