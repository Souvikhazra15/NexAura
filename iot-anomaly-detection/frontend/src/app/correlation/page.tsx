import CorrelationAnalysis from '@/components/CorrelationAnalysis';

export default function CorrelationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">🔗 Correlation Analysis</h2>
        <p className="text-slate-400 mt-1">
          Identify inter-signal dependencies and detect collective anomalies.
        </p>
      </div>

      <CorrelationAnalysis />
    </div>
  );
}
