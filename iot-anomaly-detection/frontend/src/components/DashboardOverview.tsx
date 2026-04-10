'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertCircle, TrendingUp, Zap, Activity, Gauge, Wind } from 'lucide-react';

interface DashboardData {
  health_score: number;
  total_signals: number;
  anomalies_detected: number;
  severity_breakdown: {
    critical: number;
    warning: number;
    info: number;
  };
  uptime: string;
  avg_latency_ms: number;
}

const SEVERITY_COLORS = {
  critical: '#dc2626',
  warning: '#f59e0b',
  info: '#3b82f6',
};

export default function DashboardOverview() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/summary');
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card h-32 bg-slate-800/50 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data) {
    return <div className="text-center text-red-500">Failed to load dashboard data</div>;
  }

  const pieData = [
    { name: 'Critical', value: data.severity_breakdown.critical, color: SEVERITY_COLORS.critical },
    { name: 'Warning', value: data.severity_breakdown.warning, color: SEVERITY_COLORS.warning },
    { name: 'Info', value: data.severity_breakdown.info, color: SEVERITY_COLORS.info },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Health Score */}
        <div className="card border-l-4 border-cyan-500">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">System Health</p>
              <p className="text-3xl font-bold text-gradient mt-2">{data.health_score.toFixed(1)}%</p>
            </div>
            <Activity className="w-8 h-8 text-cyan-500" />
          </div>
          <div className="mt-4 bg-cyan-500/10 rounded px-2 py-1 text-xs text-cyan-300 w-fit">
            ↑ Optimal
          </div>
        </div>

        {/* Active Signals */}
        <div className="card border-l-4 border-green-500">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Active Signals</p>
              <p className="text-3xl font-bold text-green-400 mt-2">{data.total_signals}</p>
            </div>
            <Gauge className="w-8 h-8 text-green-500" />
          </div>
          <div className="mt-4 text-xs text-slate-400">
            All sensors operational
          </div>
        </div>

        {/* Critical Alerts */}
        <div className="card border-l-4 border-red-500">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Critical Alerts</p>
              <p className="text-3xl font-bold text-red-500 mt-2">{data.severity_breakdown.critical}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-500 animate-pulse" />
          </div>
          <div className="mt-4 text-xs text-amber-300">
            Requires attention
          </div>
        </div>

        {/* Uptime */}
        <div className="card border-l-4 border-blue-500">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Uptime</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">{data.uptime}</p>
            </div>
            <Zap className="w-8 h-8 text-blue-500" />
          </div>
          <div className="mt-4 text-xs text-slate-400">
            Latency: {data.avg_latency_ms}ms
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Anomaly Distribution */}
        <div className="card lg:col-span-1">
          <h3 className="text-lg font-semibold mb-4">Anomaly Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #475569',
                  borderRadius: '8px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2 text-sm">
            {pieData.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <span className="text-slate-400">{item.name}</span>
                <span className="font-semibold" style={{ color: item.color }}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Trend Chart */}
        <div className="card lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4">Anomalies Over Time</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart
              data={[
                { time: '00:00', anomalies: 2 },
                { time: '04:00', anomalies: 3 },
                { time: '08:00', anomalies: 5 },
                { time: '12:00', anomalies: 4 },
                { time: '16:00', anomalies: 6 },
                { time: '20:00', anomalies: 3 },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="anomalies" fill="#0ea5e9" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
