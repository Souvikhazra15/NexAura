import FileUploadComponent from '@/components/AnomalyUpload';

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Navigation */}
        <div className="mb-8">
          <a href="/" className="text-blue-600 hover:text-blue-700 font-semibold">
            ← Back to Dashboard
          </a>
        </div>

        {/* Main Content */}
        <FileUploadComponent />

        {/* Info Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-2">🤖 AI Models</h3>
            <p className="text-sm text-gray-600">
              State-of-the-art anomaly detection using Z-score, Isolation Forest, and LSTM Autoencoder.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-2">⚡ Fast Processing</h3>
            <p className="text-sm text-gray-600">
              Processes medium-sized datasets in seconds. Optimized for production use.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-2">📊 Rich Analytics</h3>
            <p className="text-sm text-gray-600">
              Get metrics, confusion matrices, model comparisons, and visual dashboards.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
