'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { CheckCircle, TrendingUp, AlertTriangle } from 'lucide-react';

interface AnomalyResultsProps {
  data: {
    status: string;
    summary: {
      total_samples: number;
      anomalies_detected: number;
      anomaly_rate: string;
      best_model: string;
    };
    metrics: {
      best_model_metrics: Record<string, any>;
      all_models: Array<Record<string, any>>;
    };
    anomalies: {
      predicted_indices: number;
      anomaly_score: number[];
      indices: number[];
    };
    visualization: {
      data_points: Array<any>;
      anomaly_indices: number[];
    };
  };
  onReset?: () => void;
}

const AnomalyResults: React.FC<AnomalyResultsProps> = ({ data, onReset }) => {
  const { summary, metrics, visualization } = data;
  const { best_model_metrics, all_models } = metrics;

  // Prepare chart data
  const modelComparisonData = all_models?.map((model) => ({
    name: model?.model_name || model?.name || 'Unknown Model',
    f1: parseFloat(((model?.f1_score || 0) * 100).toFixed(2)) / 100,
    precision: parseFloat(((model?.precision || 0) * 100).toFixed(2)) / 100,
    recall: parseFloat(((model?.recall || 0) * 100).toFixed(2)) / 100,
  })) || [];

  // Confusion matrix data
  const cmData = [
    {
      name: 'True Negative',
      value: best_model_metrics?.tn || 0,
      color: '#10b981',
    },
    {
      name: 'False Positive',
      value: best_model_metrics?.fp || 0,
      color: '#ef4444',
    },
    {
      name: 'False Negative',
      value: best_model_metrics?.fn || 0,
      color: '#f97316',
    },
    {
      name: 'True Positive',
      value: best_model_metrics?.tp || 0,
      color: '#3b82f6',
    },
  ];

  // Scatter plot data (with RED anomalies)
  const scatterData = visualization?.data_points?.map((point, idx) => ({
    x: point?.x !== undefined ? point.x : idx,
    y: point?.y !== undefined ? point.y : (point?.value || 0),
    isAnomaly: visualization?.anomaly_indices?.includes(idx) || false,
  })) || [];

  return (
    <div className="w-full bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b-2 border-slate-200 pb-6">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-8 h-8 text-green-500" />
          <h2 className="text-3xl font-bold text-slate-800">
            Anomaly Detection Results
          </h2>
        </div>
        <span className="px-4 py-2 bg-green-100 text-green-700 rounded-lg font-semibold">
          ✓ Success
        </span>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
          <p className="text-sm text-slate-600 font-medium">Total Samples</p>
          <p className="text-3xl font-bold text-blue-600">
            {(summary?.total_samples || 0).toLocaleString()}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
          <p className="text-sm text-slate-600 font-medium">Anomalies Detected</p>
          <p className="text-3xl font-bold text-red-600">
            {summary?.anomalies_detected || 0}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-500">
          <p className="text-sm text-slate-600 font-medium">Anomaly Rate</p>
          <p className="text-3xl font-bold text-orange-600">
            {summary?.anomaly_rate || '0%'}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
          <p className="text-sm text-slate-600 font-medium">Best Model</p>
          <p className="text-2xl font-bold text-purple-600">
            {summary?.best_model || 'N/A'}
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-500" />
          Performance Metrics ({summary?.best_model || 'Best'})
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <p className="text-sm text-slate-600">Precision</p>
            <p className="text-2xl font-bold text-blue-600">
              {((best_model_metrics?.precision || 0) * 100).toFixed(2)}%
            </p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <p className="text-sm text-slate-600">Recall</p>
            <p className="text-2xl font-bold text-green-600">
              {((best_model_metrics?.recall || 0) * 100).toFixed(2)}%
            </p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <p className="text-sm text-slate-600">F1-Score</p>
            <p className="text-2xl font-bold text-purple-600">
              {((best_model_metrics?.f1_score || 0) * 100).toFixed(2)}%
            </p>
          </div>

          <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-4">
            <p className="text-sm text-slate-600">Accuracy</p>
            <p className="text-2xl font-bold text-amber-600">
              {(
                (((best_model_metrics?.tp || 0) + (best_model_metrics?.tn || 0)) /
                  ((best_model_metrics?.tp || 0) +
                    (best_model_metrics?.tn || 0) +
                    (best_model_metrics?.fp || 0) +
                    (best_model_metrics?.fn || 0)) || 0) *
                100
              ).toFixed(2)}%
            </p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Comparison Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-slate-800 mb-4">
            Model Performance Comparison
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={modelComparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                formatter={(value) => {
                  if (typeof value === 'number') {
                    return value > 1 ? value.toFixed(2) + '%' : (value * 100).toFixed(2) + '%';
                  }
                  return value;
                }}
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend />
              <Bar dataKey="f1" fill="#3b82f6" name="F1-Score" />
              <Bar dataKey="precision" fill="#10b981" name="Precision" />
              <Bar dataKey="recall" fill="#f59e0b" name="Recall" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Confusion Matrix */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-slate-800 mb-4">
            Confusion Matrix
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={cmData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Bar dataKey="value" fill="#3b82f6">
                {cmData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Scatter Plot with RED Anomalies */}
        <div className="bg-white rounded-lg shadow-md p-6 lg:col-span-2">
          <h3 className="text-lg font-bold text-slate-800 mb-4">
            Anomaly Detection Visualization (RED = Anomalies)
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" name="Sample Index" />
              <YAxis dataKey="y" name="Value" />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend />

              {/* Normal points - BLUE */}
              <Scatter
                name="Normal"
                data={scatterData.filter((p) => !p.isAnomaly)}
                fill="#3b82f6"
                opacity={0.6}
              />

              {/* Anomaly points - RED */}
              <Scatter
                name="Anomaly"
                data={scatterData.filter((p) => p.isAnomaly)}
                fill="#ef4444"
                opacity={0.9}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Confusion Matrix Details */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-slate-800 mb-4">
          Detailed Metrics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
            <p className="text-sm text-slate-600 font-semibold">True Positive</p>
            <p className="text-3xl font-bold text-blue-600">
              {best_model_metrics?.tp || 0}
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Correctly detected anomalies
            </p>
          </div>

          <div className="bg-red-50 rounded-lg p-4 border-2 border-red-200">
            <p className="text-sm text-slate-600 font-semibold">
              False Positive
            </p>
            <p className="text-3xl font-bold text-red-600">
              {best_model_metrics?.fp || 0}
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Normal flagged as anomaly
            </p>
          </div>

          <div className="bg-orange-50 rounded-lg p-4 border-2 border-orange-200">
            <p className="text-sm text-slate-600 font-semibold">
              False Negative
            </p>
            <p className="text-3xl font-bold text-orange-600">
              {best_model_metrics?.fn || 0}
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Anomalies missed</p>
          </div>

          <div className="bg-green-50 rounded-lg p-4 border-2 border-green-200">
            <p className="text-sm text-slate-600 font-semibold">
              True Negative
            </p>
            <p className="text-3xl font-bold text-green-600">
              {best_model_metrics?.tn || 0}
            </p>
            <p className="text-xs text-slate-500 mt-2">
              Correctly identified normal
            </p>
          </div>
        </div>
      </div>

      {/* Status Message */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-lg p-4 flex items-center gap-3">
        <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
        <div>
          <p className="font-semibold text-green-800">Analysis Complete</p>
          <p className="text-sm text-green-700">
            {summary?.best_model || 'Best'} model selected as the best performer with
            F1-Score of{' '}
            {((best_model_metrics?.f1_score || 0) * 100).toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Reset Button */}
      {onReset && (
        <div className="flex justify-center pt-6">
          <button
            onClick={onReset}
            className="px-8 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
          >
            Upload New File
          </button>
        </div>
      )}
    </div>
  );
};

export default AnomalyResults;
