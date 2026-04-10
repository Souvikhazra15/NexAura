import SignalMonitoring from '@/components/SignalMonitoring';

export default function SignalsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">📡 Signal Monitoring</h2>
        <p className="text-slate-400 mt-1">
          Live multi-signal monitoring with drill-down history and deviation tracking.
        </p>
      </div>

      <SignalMonitoring />
    </div>
  );
}
