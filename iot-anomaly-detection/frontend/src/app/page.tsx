import DashboardOverview from '@/components/DashboardOverview';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="flex flex-col gap-6">
        <div>
          <h2 className="text-4xl font-bold mb-2">System Overview</h2>
          <p className="text-slate-400">
            Real-time multi-signal anomaly detection with correlation-aware insights and explainable alerts.
          </p>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[{
            href: '/alerts',
            title: 'Anomaly Alerts',
            desc: 'Investigate critical, warning, and info events',
            badge: 'Root cause + actions',
          }, {
            href: '/signals',
            title: 'Signal Monitoring',
            desc: 'Live sensor grid + historical drill-down',
            badge: '1s granularity',
          }, {
            href: '/correlation',
            title: 'Correlation Analysis',
            desc: 'Cross-signal dependencies and collective anomalies',
            badge: 'Correlation-aware',
          }, {
            href: '/models',
            title: 'Model Performance',
            desc: 'Precision/recall, latency, and health',
            badge: 'Production metrics',
          }, {
            href: '/timeline',
            title: 'Event Timeline',
            desc: 'Operational sequence and audit trail',
            badge: 'Ops-ready',
          }].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="card group hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/20 transition-all duration-300"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold">{item.title}</h3>
                  <p className="text-sm text-slate-400 mt-1">{item.desc}</p>
                </div>
                <span className="text-xs px-2 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-cyan-300 whitespace-nowrap">
                  {item.badge}
                </span>
              </div>
              <div className="mt-4 text-sm text-cyan-300 opacity-0 group-hover:opacity-100 transition-opacity">
                Open →
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* KPIs */}
      <section>
        <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">📊 Key Metrics</h3>
        <DashboardOverview />
      </section>

      {/* Advanced Features Section */}
      <section className="mt-12">
        <h3 className="text-2xl font-bold mb-6">✨ Advanced Capabilities</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              icon: '🤖',
              title: 'Multi-Model Ensemble',
              desc: 'Statistical, ML, and Deep Learning approaches',
              highlight: 'Isolation Forest + One-Class SVM',
            },
            {
              icon: '🔗',
              title: 'Correlation-Aware',
              desc: 'Detects inter-signal anomalies',
              highlight: 'Smart correlation matrices',
            },
            {
              icon: '📊',
              title: 'Explainable Alerts',
              desc: 'SHAP-based feature importance',
              highlight: 'Root cause identification',
            },
            {
              icon: '🧠',
              title: 'Adaptive Learning',
              desc: 'Learns from operator feedback',
              highlight: 'Dynamic threshold tuning',
            },
            {
              icon: '⚡',
              title: '50+ Signal Support',
              desc: '1-second granularity data ingestion',
              highlight: 'Real-time processing',
            },
            {
              icon: '🎯',
              title: 'Multi-Anomaly Detection',
              desc: 'Point, contextual, collective',
              highlight: '95%+ accuracy',
            },
            {
              icon: '📈',
              title: 'Seasonal Analysis',
              desc: 'Daily/weekly patterns detection',
              highlight: 'Context-aware thresholds',
            },
            {
              icon: '🚀',
              title: 'Production Ready',
              desc: 'Low-latency, scalable monitoring',
              highlight: '12.5ms latency',
            },
          ].map((feature, idx) => (
            <div
              key={idx}
              className="card group hover:border-cyan-500/50 hover:shadow-lg hover:shadow-cyan-500/20 transition-all duration-300"
            >
              <div className="text-4xl mb-3 group-hover:scale-110 transition-transform duration-300">
                {feature.icon}
              </div>
              <h4 className="font-semibold mb-2">{feature.title}</h4>
              <p className="text-sm text-slate-400 mb-3">{feature.desc}</p>
              <div className="text-xs px-2 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-cyan-300 inline-block">
                {feature.highlight}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-12 bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-purple-500/10 rounded-lg p-8 border border-cyan-500/20">
        <h3 className="text-2xl font-bold mb-6">🏗️ Enterprise Architecture</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h4 className="font-semibold text-cyan-300 mb-3">Backend ML Pipeline</h4>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>✓ FastAPI async framework</li>
              <li>✓ Scikit-learn ML models</li>
              <li>✓ TensorFlow ready</li>
              <li>✓ Real-time WebSocket</li>
              <li>✓ Horizontal scalability</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-cyan-300 mb-3">Frontend Dashboard</h4>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>✓ Next.js 14 with SSR</li>
              <li>✓ Recharts visualization</li>
              <li>✓ Real-time updates</li>
              <li>✓ Dark mode optimized</li>
              <li>✓ Mobile responsive</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-cyan-300 mb-3">DevOps & Monitoring</h4>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>✓ Local dev ready (Windows)</li>
              <li>✓ Health check endpoints</li>
              <li>✓ Performance metrics</li>
              <li>✓ CORS configured</li>
              <li>✓ Error tracking</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
