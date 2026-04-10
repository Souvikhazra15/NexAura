'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, Database, Wifi } from 'lucide-react';

type ServerStatus = 'checking' | 'operational' | 'error' | 'offline';

export default function Header() {
  const pathname = usePathname();
  const [serverStatus, setServerStatus] = useState<ServerStatus>('checking');

  const navItems = useMemo(
    () => [
      { href: '/', label: 'Overview' },
      { href: '/alerts', label: 'Alerts' },
      { href: '/signals', label: 'Signals' },
      { href: '/correlation', label: 'Correlation' },
      { href: '/models', label: 'Models' },
      { href: '/timeline', label: 'Timeline' },
    ],
    []
  );

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/summary');
        setServerStatus(response.ok ? 'operational' : 'error');
      } catch {
        setServerStatus('offline');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const statusColor =
    serverStatus === 'operational'
      ? '#10b981'
      : serverStatus === 'checking'
        ? '#f59e0b'
        : '#ef4444';

  return (
    <header className="glass sticky top-0 z-50 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between gap-6">
          <div className="flex items-center gap-3 min-w-[220px]">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gradient">AnomalySync</h1>
              <p className="text-xs text-slate-400">Multi-Signal IoT Anomaly Detection</p>
            </div>
          </div>

          <nav className="hidden lg:flex items-center gap-2 flex-1 justify-center">
            {navItems.map((item) => {
              const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={
                    active
                      ? 'px-4 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-semibold'
                      : 'px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-300'
                  }
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-6">
            <div className="hidden md:flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <Database className="w-4 h-4 text-slate-400" />
                <span className="text-slate-400">IoT Hub</span>
              </div>

              <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg border border-slate-700">
                <Wifi className="w-4 h-4 animate-pulse" style={{ color: statusColor }} />
                <span className="text-sm font-medium">
                  {serverStatus === 'operational'
                    ? 'API Connected'
                    : serverStatus === 'checking'
                      ? 'Checking...'
                      : 'API Offline'}
                </span>
              </div>
            </div>

            <button className="hidden sm:inline-block px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors font-medium text-sm">
              Live View
            </button>
          </div>
        </div>

        <div className="lg:hidden mt-4 -mx-2 px-2 overflow-x-auto">
          <div className="flex items-center gap-2 min-w-max">
            {navItems.map((item) => {
              const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={
                    active
                      ? 'px-3 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-semibold text-sm'
                      : 'px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-300 text-sm'
                  }
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </header>
  );
}
