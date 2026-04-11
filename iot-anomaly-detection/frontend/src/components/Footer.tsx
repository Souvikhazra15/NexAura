'use client';

export default function Footer() {
  return (
    <footer className="border-t border-slate-700 bg-slate-900/50 py-8 mt-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Bottom */}
        <div className="border-t border-slate-700 pt-6 flex flex-col md:flex-row items-center justify-between text-sm text-slate-400">
          <p>&copy; 2026 AnomalySync. All rights reserved.</p>
          <div className="flex gap-6 mt-4 md:mt-0">
            <a href="#" className="hover:text-cyan-400 transition-colors">
              Privacy
            </a>
            <a href="#" className="hover:text-cyan-400 transition-colors">
              Terms
            </a>
            <a href="#" className="hover:text-cyan-400 transition-colors">
              Status
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
