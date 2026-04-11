'use client';

import { useState, useEffect } from 'react';
import { ZoomIn, AlertCircle, RefreshCw } from 'lucide-react';

interface CorrelationMatrix {
  [key: string]: { [key: string]: number };
}

interface CorrelationResponse {
  status: string;
  signals: string[];
  matrix: CorrelationMatrix;
  filename: string;
  shape: {
    rows: number;
    columns: number;
  };
}

export default function CorrelationAnalysis() {
  const [correlationMatrix, setCorrelationMatrix] = useState<CorrelationMatrix | null>(null);
  const [signals, setSignals] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>('');
  const [shape, setShape] = useState<{ rows: number; columns: number } | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUploadTime, setLastUploadTime] = useState<number>(0);

  useEffect(() => {
    // Initial fetch
    fetchCorrelationMatrix();
    
    // Listen for upload completion via localStorage
    const handleStorageChange = () => {
      const uploadTime = localStorage.getItem('lastUploadTime');
      if (uploadTime) {
        const newUploadTime = parseInt(uploadTime, 10);
        if (newUploadTime > lastUploadTime) {
          setLastUploadTime(newUploadTime);
          // Delay slightly to ensure file is written to disk
          setTimeout(() => fetchCorrelationMatrix(), 500);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    // Poll for updates every 3 seconds (in case upload happens on same tab)
    const interval = setInterval(() => {
      const uploadTime = localStorage.getItem('lastUploadTime');
      if (uploadTime) {
        const newUploadTime = parseInt(uploadTime, 10);
        if (newUploadTime > lastUploadTime) {
          setLastUploadTime(newUploadTime);
          setTimeout(() => fetchCorrelationMatrix(), 500);
        }
      }
    }, 3000);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, [lastUploadTime]);

  const fetchCorrelationMatrix = async () => {
    try {
      if (!isRefreshing) setLoading(true);
      setIsRefreshing(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/api/correlation');
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('No CSV file uploaded yet. Upload a file to see correlations.');
        } else {
          const errorData = await response.json();
          setError(errorData.detail || 'Failed to fetch correlation data');
        }
        setCorrelationMatrix(null);
        setSignals([]);
        setLoading(false);
        setIsRefreshing(false);
        return;
      }
      
      const data: CorrelationResponse = await response.json();
      
      setCorrelationMatrix(data.matrix);
      setSignals(data.signals);
      setFilename(data.filename);
      setShape(data.shape);
      setError(null);
    } catch (err) {
      console.error('Error fetching correlation matrix:', err);
      setError('Unable to connect to backend. Make sure the server is running on http://localhost:8000');
      setCorrelationMatrix(null);
      setSignals([]);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const getCorrelationColor = (value: number): string => {
    // Color scale: dark blue (negative) -> white (zero) -> dark red (positive)
    if (value < 0) {
      const intensity = Math.abs(value);
      return `rgb(${Math.round(30 + 195 * (1 - intensity))}, ${Math.round(58 + 167 * (1 - intensity))}, ${Math.round(138 + 117 * (1 - intensity))})`;
    } else if (value > 0) {
      const intensity = value;
      return `rgb(${Math.round(139 + 116 * intensity)}, ${Math.round(69 + 33 * intensity)}, ${Math.round(19 + 36 * intensity)})`;
    }
    return 'rgb(200, 200, 200)';
  };

  const getTopCorrelations = (limit: number = 3) => {
    if (!correlationMatrix || signals.length === 0) return [];
    
    const correlations: Array<{ pair: string; value: number }> = [];
    
    for (let i = 0; i < signals.length; i++) {
      for (let j = i + 1; j < signals.length; j++) {
        const sig1 = signals[i];
        const sig2 = signals[j];
        const value = correlationMatrix[sig1]?.[sig2] ?? 0;
        correlations.push({ pair: `${sig1} ↔ ${sig2}`, value });
      }
    }
    
    return correlations.sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, limit);
  };

  if (loading && !correlationMatrix) {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <ZoomIn size={20} className="text-cyan-400" />
            Correlation Matrix - Signal Dependencies
          </h3>
        </div>
        <div className="h-96 bg-slate-800/50 animate-pulse rounded flex items-center justify-center">
          <p className="text-slate-400">Loading correlation data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <ZoomIn size={20} className="text-cyan-400" />
            Correlation Matrix - Signal Dependencies
          </h3>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded p-4 flex items-start gap-3">
          <AlertCircle size={20} className="text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-amber-300 font-semibold">No Data Available</p>
            <p className="text-amber-200 text-sm mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!correlationMatrix || signals.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <ZoomIn size={20} className="text-cyan-400" />
            Correlation Matrix - Signal Dependencies
          </h3>
        </div>
        <div className="bg-slate-800/50 rounded p-8 text-center">
          <p className="text-slate-400">No correlation data available. Upload a CSV file to generate correlation analysis.</p>
        </div>
      </div>
    );
  }

  const topCorrelations = getTopCorrelations(3);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <ZoomIn size={20} className="text-cyan-400" />
          Correlation Matrix - Signal Dependencies
        </h3>
        <span className="text-xs px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-cyan-300">
          {signals.length} signals analyzed
        </span>
      </div>
      
      {filename && shape && (
        <p className="text-xs text-slate-500 mb-4">
          File: <span className="text-slate-300">{filename}</span> • 
          Rows: <span className="text-slate-300">{shape.rows}</span> • 
          Columns: <span className="text-slate-300">{shape.columns}</span>
        </p>
      )}

      {/* Heatmap Container */}
      <div className="overflow-x-auto mb-6">
        <div className="inline-block min-w-full">
          {/* Column Headers */}
          <div className="flex">
            <div className="w-32 flex-shrink-0" />
            {signals.map((signal) => (
              <div
                key={`header-${signal}`}
                className="w-20 flex-shrink-0 flex items-center justify-center text-xs font-medium text-slate-300 overflow-hidden"
                style={{ minHeight: '40px', writingMode: 'vertical-lr', transform: 'rotate(180deg)' }}
              >
                {signal.replace(/_/g, ' ')}
              </div>
            ))}
          </div>

          {/* Heatmap Rows */}
          {signals.map((rowSignal) => (
            <div key={`row-${rowSignal}`} className="flex">
              {/* Row Label */}
              <div className="w-32 flex-shrink-0 flex items-center justify-end pr-2 text-xs font-medium text-slate-300 bg-slate-900/30">
                {rowSignal.replace(/_/g, ' ')}
              </div>

              {/* Correlation Cells */}
              {signals.map((colSignal) => {
                const value = correlationMatrix?.[rowSignal]?.[colSignal] ?? 0;
                return (
                  <div
                    key={`cell-${rowSignal}-${colSignal}`}
                    className="w-20 h-20 flex-shrink-0 flex items-center justify-center text-sm font-semibold border border-slate-700/30 cursor-pointer hover:border-cyan-500/50 transition-colors"
                    style={{ backgroundColor: getCorrelationColor(value) }}
                    title={`${rowSignal} - ${colSignal}: ${value.toFixed(4)}`}
                  >
                    <span className="text-slate-100 drop-shadow" style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}>
                      {value.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center gap-8 mb-6">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded" style={{ backgroundColor: 'rgb(30, 58, 138)' }} />
          <span className="text-xs text-slate-400">-1.0 (Negative)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded" style={{ backgroundColor: 'rgb(200, 200, 200)' }} />
          <span className="text-xs text-slate-400">0.0 (No Correlation)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded" style={{ backgroundColor: 'rgb(139, 69, 19)' }} />
          <span className="text-xs text-slate-400">+1.0 (Positive)</span>
        </div>
      </div>

      {/* Key Insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {topCorrelations.map((corr, idx) => (
          <div key={idx} className="bg-slate-800/50 rounded p-3 border border-slate-700">
            <p className="text-xs text-slate-400 mb-1">
              {Math.abs(corr.value) > 0.7 ? 'Strong' : Math.abs(corr.value) > 0.4 ? 'Moderate' : 'Weak'} Correlation
            </p>
            <p className="text-sm font-bold text-orange-400">{corr.pair}</p>
            <p className="text-xs text-slate-500">{corr.value.toFixed(4)}</p>
          </div>
        ))}
      </div>

      <button
        onClick={fetchCorrelationMatrix}
        disabled={isRefreshing}
        className="mt-6 w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:bg-cyan-600/50 text-white text-sm font-medium rounded transition-colors flex items-center justify-center gap-2"
      >
        <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
        {isRefreshing ? 'Refreshing...' : 'Refresh Correlation Data'}
      </button>
    </div>
  );
}
