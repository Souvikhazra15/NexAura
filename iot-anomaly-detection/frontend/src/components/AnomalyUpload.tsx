'use client';

import React, { useState } from 'react';
import axios from 'axios';
import { Upload, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import AnomalyDashboard from './AnomalyDashboard';

interface UploadResponse {
  status: string;
  error?: string;
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
}

const FileUploadComponent: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<UploadResponse | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  // Handle drag and drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  };

  // Validate file before setting
  const validateAndSetFile = (selectedFile: File) => {
    // Check file type
    if (!selectedFile.name.endsWith('.csv')) {
      setError('❌ Only CSV files are allowed. Got: ' + selectedFile.name.split('.').pop());
      return;
    }

    // Check file size (max 50MB)
    const fileSizeMB = selectedFile.size / (1024 * 1024);
    if (fileSizeMB > 50) {
      setError(`❌ File too large: ${fileSizeMB.toFixed(2)}MB (max 50MB)`);
      return;
    }

    // Check minimum file size (at least 100 bytes for valid CSV)
    if (selectedFile.size < 100) {
      setError('❌ File too small. Must contain actual data.');
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  // Upload and process file
  const handleUpload = async () => {
    if (!file) {
      setError('❌ Please select a file');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<UploadResponse>(
        `${API_BASE_URL}/api/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minute timeout for large files
        }
      );

      if (response?.data?.status === 'success') {
        setResults(response.data);
        // Notify CorrelationAnalysis component that a new file was uploaded
        localStorage.setItem('lastUploadTime', Date.now().toString());
      } else if (response?.data?.error) {
        setError(`❌ Error: ${response?.data?.error}`);
      } else {
        setError('❌ Processing failed. Please try again.');
      }
    } catch (err: any) {
      console.error('Upload error:', err);
      
      // Handle different error types
      if (err.code === 'ECONNABORTED') {
        setError('❌ Request timeout. File may be too large or server is slow.');
      } else if (err.response?.status === 413) {
        setError('❌ File too large. Maximum size is 50MB.');
      } else if (err.response?.status === 422) {
        setError('❌ Invalid CSV format. Check file structure.');
      } else if (err.response?.status === 500) {
        setError('❌ Server error. Please try again later.');
      } else if (err.code === 'ERR_NETWORK') {
        setError(`❌ Cannot connect to server at ${API_BASE_URL}. Is the backend running?`);
      } else {
        const errorMsg = err.response?.data?.detail || err.message || 'Unknown error occurred';
        setError(`❌ Error: ${errorMsg}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // Reset for new upload
  const handleReset = () => {
    setFile(null);
    setResults(null);
    setError(null);
  };

  // Show results if available
  if (results) {
    return (
      <div className="space-y-4">
        <AnomalyDashboard data={results} onReset={handleReset} />
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🚀 Anomaly Detection System
          </h1>
          <p className="text-gray-600">
            Upload a CSV file to detect anomalies using ML models
          </p>
          <p className="text-sm text-blue-600 mt-2">
            💡 Your data will also be processed in the Comprehensive Analysis notebook for advanced insights
          </p>
        </div>

        {/* Upload Area */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-gray-50 hover:border-blue-400'
          }`}
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-lg font-semibold text-gray-700 mb-2">
            Drag & drop your CSV file here
          </p>
          <p className="text-sm text-gray-600 mb-4">or</p>

          <label className="inline-block">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <span className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors">
              Browse Files
            </span>
          </label>

          {file && (
            <p className="mt-4 text-sm text-green-600 font-semibold">
              ✅ Selected: {file.name}
            </p>
          )}
        </div>

        {/* File Info */}
        {file && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-700">
              <strong>File:</strong> {file.name}
            </p>
            <p className="text-sm text-gray-700">
              <strong>Size:</strong> {(file.size / 1024).toFixed(2)} KB
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Upload Button */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className={`flex-1 py-3 px-4 text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${
              !file || loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
            }`}
            title={!file ? 'Please select a CSV file first' : 'Click to analyze your data'}
          >
            {loading ? (
              <>
                <Loader className="h-5 w-5 animate-spin" />
                <span>Processing CSV...</span>
              </>
            ) : (
              <>
                <Upload className="h-5 w-5" />
                <span>Analyze Now</span>
              </>
            )}
          </button>

          {file && (
            <button
              onClick={() => setFile(null)}
              disabled={loading}
              className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 disabled:opacity-50 font-semibold transition-colors"
            >
              Clear Selection
            </button>
          )}
        </div>

        {/* Processing Info */}
        {loading && (
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <Loader className="h-5 w-5 text-blue-600 animate-spin" />
              <span className="font-semibold text-blue-900">Processing your CSV file...</span>
            </div>
            <div className="text-sm text-blue-800 space-y-2">
              <p>📊 Analyzing data patterns</p>
              <p>🤖 Running anomaly detection models</p>
              <p>📈 Generating metrics and visualizations</p>
            </div>
          </div>
        )}

        {/* Requirements */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-3">📋 Requirements:</h3>
          <ul className="text-sm text-gray-600 space-y-2">
            <li>✓ CSV format only</li>
            <li>✓ Maximum 50MB file size</li>
            <li>✓ At least 2 numeric columns</li>
            <li>✓ Minimum 10 rows of data</li>
          </ul>

          {/* Notebook Integration Info */}
          <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
            <h4 className="font-semibold text-purple-900 mb-2">📊 Advanced Analysis</h4>
            <p className="text-sm text-purple-800 mb-3">
              After uploading, your CSV file is automatically saved and can be processed in the comprehensive analysis notebook at:
            </p>
            <code className="text-xs bg-white px-3 py-2 rounded text-purple-700 block overflow-x-auto">
              models/OmniAnamoly/Comprehensive_Anomaly_Detection_Pipeline.ipynb
            </code>
            <p className="text-xs text-purple-700 mt-2">
              📝 The notebook will automatically detect and use your latest uploaded CSV file.
            </p>
          </div>

          {/* API Configuration Info */}
          <div className="mt-4 p-3 bg-gray-100 rounded text-xs text-gray-700 font-mono">
            <p>
              <strong>API Endpoint:</strong> {API_BASE_URL}
            </p>
            <p className="text-gray-600 mt-1">
              (If connection fails, ensure backend is running: <code className="bg-white px-1 py-0.5 rounded">python main.py</code>)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUploadComponent;
