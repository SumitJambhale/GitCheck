import React, { useState } from 'react';
import { X, Terminal, Copy, Check, Shield } from 'lucide-react';

interface CliInstallModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CliInstallModal: React.FC<CliInstallModalProps> = ({ isOpen, onClose }) => {
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  if (!isOpen) return null;

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedSection(id);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const installCode = `# 1. Install GitCheck CLI harness
cd GitCheck/cli
pip install -e .

# 2. Configure AI Provider (Optional: supports Gemini, OpenAI, Claude)
export GEMINI_API_KEY="your-gemini-key"

# 3. Configure Supabase (Optional)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"

# 4. Install Git Pre-Commit Hook into your repository
git-check install-hook`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="h-9 w-9 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center">
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Install GitCheck on Developer Machine</h3>
            <p className="text-xs text-slate-400">Run verification harness on git commit or push</p>
          </div>
        </div>

        <p className="text-xs text-slate-300 mb-4 leading-relaxed">
          GitCheck runs locally in your terminal before commits are pushed to remote. It asks 3–4 Socratic questions to catch comprehension debt and overengineering, then stores the review context for the team dashboard.
        </p>

        <div className="relative mb-4">
          <pre className="bg-slate-950 border border-slate-800 p-4 rounded-xl text-xs font-mono text-slate-200 overflow-x-auto leading-relaxed">
            {installCode}
          </pre>
          <button
            onClick={() => copyCode(installCode, 'install')}
            className="absolute top-3 right-3 p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300"
            title="Copy command"
          >
            {copiedSection === 'install' ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
          </button>
        </div>

        <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-900/40 text-xs text-blue-200 flex items-center space-x-2">
          <Shield className="h-4 w-4 text-blue-400 shrink-0" />
          <span>
            <strong>Developer Privacy First:</strong> Quiz comprehension scores are kept 100% confidential. Only the architectural summary and agreement are recorded.
          </span>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
