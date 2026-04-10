import ModelPerformance from '@/components/ModelPerformance';

export default function ModelsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">🤖 Model Performance</h2>
        <p className="text-slate-400 mt-1">
          Track precision, recall, latency, and overall model health for real-time detection.
        </p>
      </div>

      <ModelPerformance />
    </div>
  );
}
