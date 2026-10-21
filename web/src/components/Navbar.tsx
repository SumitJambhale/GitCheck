import React from 'react';
import { GitBranch, ShieldCheck, Database, Terminal, CheckCircle2 } from 'lucide-react';
import { isSupabaseConfigured } from '../lib/supabase';

interface NavbarProps {
  onOpenCliGuide: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenCliGuide }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">GitCheck</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full">
                Pre-Commit Gate
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">AI Code Comprehension & PR Defense Harness</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300">
            <Database className="h-3.5 w-3.5 text-emerald-400" />
            <span>Supabase:</span>
            <span className={isSupabaseConfigured ? 'text-emerald-400 font-medium' : 'text-amber-400 font-medium'}>
              {isSupabaseConfigured ? 'Connected' : 'Demo Mode'}
            </span>
          </div>

          <button
            onClick={onOpenCliGuide}
            className="flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-sm transition-colors"
          >
            <Terminal className="h-3.5 w-3.5" />
            <span>CLI Setup</span>
          </button>
        </div>
      </div>
    </header>
  );
};
