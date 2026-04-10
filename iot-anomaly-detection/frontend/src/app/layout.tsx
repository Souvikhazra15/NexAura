import type { Metadata } from 'next';
import '../globals.css';

import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'AnomalySync - IoT Anomaly Detection',
  description: 'Enterprise-grade multi-signal time-series anomaly detection for industrial IoT',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
        <div className="min-h-screen flex flex-col">
          <Header />

          <main className="flex-1 p-6 md:p-8">
            <div className="max-w-7xl mx-auto">{children}</div>
          </main>

          <Footer />
        </div>
      </body>
    </html>
  );
}
