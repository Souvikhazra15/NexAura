import EventTimeline from '@/components/EventTimeline';

export default function TimelinePage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">🕒 Event Timeline</h2>
        <p className="text-slate-400 mt-1">
          Operational audit trail of anomalies, recoveries, and maintenance events.
        </p>
      </div>

      <EventTimeline />
    </div>
  );
}
