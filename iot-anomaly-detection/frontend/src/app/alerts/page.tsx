import AnomalyAlerts from '@/components/AnomalyAlerts';

export default function AlertsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">🚨 Anomaly Alerts</h2>
        <p className="text-slate-400 mt-1">
          Explainable alerts with severity scoring, contributing signals, and suggested investigation paths.
        </p>
      </div>

      <AnomalyAlerts />
    </div>
  );
}
