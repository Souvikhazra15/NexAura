'use client';

import { useState } from 'react';
import { AlertCircle, Clock, TrendingUp, Zap } from 'lucide-react';

interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'critical' | 'warning' | 'recovery' | 'maintenance';
  title: string;
  description: string;
}

export default function EventTimeline() {
  const [events] = useState<TimelineEvent[]>([
    {
      id: '1',
      timestamp: '14:35:22',
      type: 'critical',
      title: 'Temperature Spike Detected',
      description: 'Zone A exceeded 28°C threshold',
    },
    {
      id: '2',
      timestamp: '14:34:55',
      type: 'warning',
      title: 'Vibration Anomaly',
      description: 'Motor M2 vibration increased to 0.8mm/s',
    },
    {
      id: '3',
      timestamp: '14:33:10',
      type: 'recovery',
      title: 'System Normalized',
      description: 'Cooling flow restored, temperature stabilized',
    },
    {
      id: '4',
      timestamp: '14:30:45',
      type: 'maintenance',
      title: 'Scheduled Maintenance',
      description: 'Applied software patch v3.2.1',
    },
  ]);

  const typeConfig = {
    critical: { icon: AlertCircle, color: '#dc2626', bg: 'bg-red-500/10', border: 'border-red-500/30' },
    warning: { icon: TrendingUp, color: '#f59e0b', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
    recovery: { icon: Zap, color: '#10b981', bg: 'bg-green-500/10', border: 'border-green-500/30' },
    maintenance: { icon: Clock, color: '#3b82f6', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
  };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-6">Event Timeline</h3>

      <div className="space-y-4 max-h-96 overflow-y-auto">
        {events.map((event, idx) => {
          const config = typeConfig[event.type];
          const Icon = config.icon;

          return (
            <div key={event.id} className={`relative flex gap-4 ${idx !== events.length - 1 ? 'pb-4' : ''}`}>
              {/* Timeline Line */}
              {idx !== events.length - 1 && (
                <div className="absolute left-5 top-12 bottom-0 w-0.5 bg-gradient-to-b from-slate-700 to-transparent" />
              )}

              {/* Icon */}
              <div
                className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${config.bg} border-2`}
                style={{ borderColor: config.color }}
              >
                <Icon size={20} style={{ color: config.color }} />
              </div>

              {/* Content */}
              <div className={`flex-1 pt-1 ${config.bg} border-l-2 pl-4 py-3 rounded`} style={{ borderColor: config.color }}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-sm">{event.title}</p>
                    <p className="text-xs text-slate-400 mt-1">{event.description}</p>
                  </div>
                  <span className="text-xs text-slate-400 whitespace-nowrap">{event.timestamp}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
