'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface SignalData {
  id: string;
  current_value: number;
  baseline: number;
  deviation_percent: number;
  status: 'normal' | 'warning' | 'critical';
  unit: string;
  last_updated: string;
}

const STATUS_CONFIG = {
  normal: { color: '#10b981', bg: 'bg-green-500/10', border: 'border-green-500/30', badge: 'Normal' },
  warning: { color: '#f59e0b', bg: 'bg-amber-500/10', border: 'border-amber-500/30', badge: 'Warning' },
  critical: { color: '#dc2626', bg: 'bg-red-500/10', border: 'border-red-500/30', badge: 'Critical' },
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function computeHealthPercent(deviationPercent: number) {
  // Turn deviation into a stable 0-100 "health" gauge.
  // 0% = very anomalous, 100% = perfectly normal.
  const absDev = Math.abs(deviationPercent);
  return clamp(100 - absDev * 2.5, 0, 100);
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const angleRad = (Math.PI / 180) * angleDeg;
  return {
    x: cx + r * Math.cos(angleRad),
    // SVG y-axis is downward; invert sin to draw arcs on the top half.
    y: cy - r * Math.sin(angleRad),
  };
}

function describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, r, startAngle);
  const end = polarToCartesian(cx, cy, r, endAngle);
  const largeArcFlag = Math.abs(endAngle - startAngle) <= 180 ? '0' : '1';
  // sweep-flag 0 draws the counterclockwise arc (top half for 180→0)
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

function SignalGaugeTile({
  signal,
  selected,
  onSelect,
}: {
  signal: SignalData;
  selected: boolean;
  onSelect: () => void;
}) {
  const cfg = STATUS_CONFIG[signal.status];
  const health = computeHealthPercent(signal.deviation_percent);

  // Semi-circle gauge from 180° (left) to 0° (right)
  const cx = 52;
  const cy = 52;
  const r = 38;
  const start = 180;
  const end = 0;
  const sweep = start - end;
  const percentToAngle = (p: number) => start - (clamp(p, 0, 100) / 100) * sweep;
  const valueAngle = percentToAngle(health);

  // Tiny overlap (degrees) between bands to avoid anti-aliased seams
  const bandOverlap = 0.75;
  const a40 = percentToAngle(40);
  const a70 = percentToAngle(70);
  const startPt = polarToCartesian(cx, cy, r, start);
  const endPt = polarToCartesian(cx, cy, r, end);

  // Segmented gauge like the reference image
  const segmentCount = 8;
  const gapDeg = 2.2;
  const segments = Array.from({ length: segmentCount }, (_, i) => {
    const p0 = (i / segmentCount) * 100;
    const p1 = ((i + 1) / segmentCount) * 100;
    const segStart = percentToAngle(p0);
    const segEnd = percentToAngle(p1);

    // Red -> Yellow -> Green (left to right)
    let color = '#10b981';
    if (i < 3) color = '#ef4444';
    else if (i < 5) color = '#f59e0b';

    // Apply a small angular gap between segments
    const s = segStart - gapDeg / 2;
    const e = segEnd + gapDeg / 2;
    return { i, s, e, color };
  });

  const needleAngle = valueAngle;
  const needleOuter = polarToCartesian(cx, cy, r - 6, needleAngle);
  const needleInner = { x: cx, y: cy };

  return (
    <button
      onClick={onSelect}
      className={
        `card text-left p-3 border-2 transition-all ${
          selected ? 'border-cyan-500 bg-cyan-500/5' : 'border-slate-700 hover:border-slate-600'
        }`
      }
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[11px] font-mono text-slate-400 truncate">{signal.id}</div>
        </div>

        <span
          className="text-[11px] px-2 py-1 rounded-full font-semibold border"
          style={{
            color: cfg.color,
            backgroundColor: `${cfg.color}20`,
            borderColor: `${cfg.color}55`,
          }}
        >
          {cfg.badge}
        </span>
      </div>

      <div className="mt-3 flex items-end justify-between gap-3">
        <div className="w-[104px]">
          <svg width="104" height="62" viewBox="0 0 104 62" className="block">
            {/* Base track */}
            <path
              d={describeArc(cx, cy, r, start, end)}
              stroke="#1f2a37"
              strokeWidth="9"
              strokeLinecap="round"
              fill="none"
            />

            {/* Segments */}
            {segments.map((seg) => (
              <path
                key={seg.i}
                d={describeArc(cx, cy, r, seg.s, seg.e)}
                stroke={seg.color}
                strokeWidth="9"
                strokeLinecap="round"
                fill="none"
              />
            ))}

            {/* Needle */}
            <line x1={needleInner.x} y1={needleInner.y} x2={needleOuter.x} y2={needleOuter.y} stroke="#e2e8f0" strokeWidth="3" strokeLinecap="round" />

            {/* Center hub with value */}
            <circle cx={cx} cy={cy} r="9" fill="#0b1220" stroke="#e2e8f0" strokeWidth="1.2" />
            <text
              x={cx}
              y={cy + 3}
              textAnchor="middle"
              fontSize="9"
              fill="#e2e8f0"
              fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial"
              fontWeight="700"
            >
              {Math.round(health)}
            </text>
          </svg>
          <div className="-mt-1 text-center">
            <span className="text-sm font-bold" style={{ color: cfg.color }}>
              {health.toFixed(1)}%
            </span>
            <span className="text-[11px] text-slate-400 ml-2">health</span>
          </div>
        </div>

        <div className="text-right text-xs text-slate-400">
          <div className="text-base font-bold leading-none">
            {typeof signal.current_value === 'number' ? signal.current_value.toFixed(1) : 'N/A'}
          </div>
          <div className="mt-0.5">{signal.unit || '-'}</div>
          <div className="mt-2 flex items-center justify-end gap-1">
            {signal.deviation_percent > 0 ? (
              <TrendingUp size={12} className="text-red-500" />
            ) : (
              <TrendingDown size={12} className="text-blue-500" />
            )}
            <span style={{ color: signal.deviation_percent > 0 ? '#ef4444' : '#3b82f6' }} className="font-semibold">
              {signal.deviation_percent > 0 ? '+' : ''}
              {signal.deviation_percent.toFixed(1)}%
            </span>
          </div>
          <div className="mt-1">baseline {signal.baseline.toFixed(1)}</div>
        </div>
      </div>
    </button>
  );
}

export default function SignalMonitoring() {
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSignal, setSelectedSignal] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [tempZonesHistory, setTempZonesHistory] = useState<any[]>([]);

  const [datasetStatus, setDatasetStatus] = useState<any>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDatasetStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dataset/status');
        const result = await response.json();
        setDatasetStatus(result);
      } catch {
        setDatasetStatus(null);
      }
    };

    fetchDatasetStatus();
  }, []);

  useEffect(() => {
    const fetchSignals = async () => {
      const useLive = Boolean(datasetStatus?.loaded);
      const url = useLive ? 'http://localhost:8000/api/signals?live=1' : 'http://localhost:8000/api/signals';
      try {
        const response = await fetch(url);
        const result = await response.json();
        setSignals(result.signals || []);
        setSelectedSignal((prev) => {
          if (prev && (result.signals || []).some((s: any) => s.id === prev)) return prev;
          return result.signals && result.signals.length > 0 ? result.signals[0].id : null;
        });
      } catch (error) {
        console.error('Failed to fetch signals:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSignals();
    const interval = setInterval(fetchSignals, 1000);
    return () => clearInterval(interval);
  }, [datasetStatus?.loaded]);

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploading(true);
    setUploadError(null);
    try {
      const form = new FormData();
      form.append('file', uploadFile);
      const res = await fetch('http://localhost:8000/api/dataset/upload', {
        method: 'POST',
        body: form,
      });
      const payload = await res.json();
      if (!res.ok) {
        throw new Error(payload?.detail || 'Upload failed');
      }
      setDatasetStatus(payload);

      // Refresh signals immediately after upload
      const signalsRes = await fetch('http://localhost:8000/api/signals?live=1');
      const signalsPayload = await signalsRes.json();
      setSignals(signalsPayload.signals || []);
      setSelectedSignal((prev) => {
        if (prev && (signalsPayload.signals || []).some((s: any) => s.id === prev)) return prev;
        return signalsPayload.signals && signalsPayload.signals.length > 0 ? signalsPayload.signals[0].id : null;
      });
    } catch (e: any) {
      setUploadError(e?.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    if (!selectedSignal) return;

    const isTempZone = /^TEMP_ZONE_[ABC]$/.test(selectedSignal);
    const tempZoneIds = ['TEMP_ZONE_A', 'TEMP_ZONE_B', 'TEMP_ZONE_C'];

    const fetchHistory = async () => {
      try {
        const liveParam = datasetStatus?.loaded ? '&live=1' : '';
        if (isTempZone) {
          const results = await Promise.all(
            tempZoneIds.map(async (id) => {
              const response = await fetch(`http://localhost:8000/api/signals/${id}/history?minutes=30${liveParam}`);
              const result = await response.json();
              return { id, history: result.history || [] };
            })
          );

          const byTs = new Map<number, any>();
          for (const r of results) {
            for (const h of r.history) {
              // Round timestamps to the nearest minute to align series
              const raw = new Date(h.timestamp);
              const ts = Math.floor(raw.getTime() / 60000) * 60000;
              const existing = byTs.get(ts) || { _ts: ts, time: new Date(ts).toLocaleTimeString() };
              existing[r.id] = h.value;
              byTs.set(ts, existing);
            }
          }

          const merged = Array.from(byTs.values()).sort((a, b) => a._ts - b._ts).map(({ _ts, ...rest }) => rest);
          setTempZonesHistory(merged);
          setHistoryData([]);
        } else {
          const response = await fetch(`http://localhost:8000/api/signals/${selectedSignal}/history?minutes=30${liveParam}`);
          const result = await response.json();
          const formatted = (result.history || []).map((h: any) => ({
            time: new Date(h.timestamp).toLocaleTimeString(),
            value: h.value,
          }));
          setHistoryData(formatted);
          setTempZonesHistory([]);
        }
      } catch (error) {
        console.error('Failed to fetch history:', error);
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, datasetStatus?.loaded ? 1000 : 5000);
    return () => clearInterval(interval);
  }, [selectedSignal, datasetStatus?.loaded]);

  if (loading) {
    return <div className="text-slate-400">Loading signals...</div>;
  }

  const selected = signals.find((s) => s.id === selectedSignal);
  const config = selected ? STATUS_CONFIG[selected.status] : STATUS_CONFIG.normal;
  const isTempZoneSelected = selectedSignal ? /^TEMP_ZONE_[ABC]$/.test(selectedSignal) : false;

  return (
    <div className="space-y-6">
      {/* Dataset upload */}
      <div className="card p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold">Machine Data File</h3>
            <p className="text-sm text-slate-400 mt-1">Upload CSV / TXT / XLSX to drive the whole dashboard.</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
            <input
              type="file"
              accept=".csv,.txt,.xlsx,.xls"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-slate-700 file:px-3 file:py-2 file:text-slate-100 hover:file:bg-slate-600"
            />
            <button
              onClick={handleUpload}
              disabled={!uploadFile || uploading}
              className="px-4 py-2 rounded-md bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-400 text-white text-sm font-semibold"
            >
              {uploading ? 'Uploading…' : 'Use This File'}
            </button>
          </div>
        </div>

        <div className="mt-3 text-sm text-slate-300">
          {datasetStatus?.loaded ? (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <span className="text-slate-400">Active dataset:</span>{' '}
                <span className="font-semibold">{datasetStatus.filename}</span>{' '}
                <span className="text-slate-500">({datasetStatus.rows} rows)</span>
              </div>
              <div className="text-slate-500">timestamp: {datasetStatus.timestamp_col || 'auto'}</div>
            </div>
          ) : (
            <div className="text-slate-500">No dataset uploaded yet — showing mock data.</div>
          )}
          {uploadError && (
            <div className="mt-2 text-red-400 flex items-center gap-2">
              <AlertCircle size={16} />
              <span>{uploadError}</span>
            </div>
          )}
        </div>
      </div>

      {/* Signal Grid */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Active Signals</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3 max-h-[520px] overflow-y-auto">
          {signals.map((signal) => (
            <SignalGaugeTile
              key={signal.id}
              signal={signal}
              selected={signal.id === selectedSignal}
              onSelect={() => setSelectedSignal(signal.id)}
            />
          ))}
        </div>
      </div>

      {/* Detail Chart */}
      {selected && (
        <div className={`card ${config.bg} border-l-4`} style={{ borderLeftColor: config.color }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold">{selected.id}</h3>
              <p className="text-sm text-slate-400 mt-1">Last updated: {selected.last_updated}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold">{selected.current_value.toFixed(2)}</div>
              <div className="text-sm text-slate-400">{selected.unit}</div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
            <div className="bg-slate-800/50 rounded p-2">
              <p className="text-slate-400">Baseline</p>
              <p className="font-semibold">{selected.baseline.toFixed(2)}</p>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <p className="text-slate-400">Deviation</p>
              <p className="font-semibold">{selected.deviation_percent.toFixed(2)}%</p>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <p className="text-slate-400">Status</p>
              <p className="font-semibold" style={{ color: config.color }}>
                {selected.status.toUpperCase()}
              </p>
            </div>
          </div>

          {/* History Chart */}
          {(historyData.length > 0 || tempZonesHistory.length > 0) && (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={isTempZoneSelected ? tempZonesHistory : historyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                />
                <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />

                {isTempZoneSelected ? (
                  <>
                    <Line type="monotone" dataKey="TEMP_ZONE_A" name="TEMP_ZONE_A" stroke="#22c55e" dot={false} strokeWidth={2} isAnimationActive={true} />
                    <Line type="monotone" dataKey="TEMP_ZONE_B" name="TEMP_ZONE_B" stroke="#38bdf8" dot={false} strokeWidth={2} isAnimationActive={true} />
                    <Line type="monotone" dataKey="TEMP_ZONE_C" name="TEMP_ZONE_C" stroke="#f59e0b" dot={false} strokeWidth={2} isAnimationActive={true} />
                  </>
                ) : (
                  <>
                    <ReferenceLine
                      y={selected.baseline}
                      stroke="#64748b"
                      strokeDasharray="5 5"
                      label={{ value: 'Baseline', position: 'right', fill: '#94a3b8', fontSize: 12 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={config.color}
                      dot={false}
                      strokeWidth={2}
                      isAnimationActive={true}
                    />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      )}
    </div>
  );
}
