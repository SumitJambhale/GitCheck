import React, { useState } from 'react';
import { X, Terminal, Copy, Check, ExternalLink } from 'lucide-react';

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

  const macLinuxCmd = 'curl -fsSL https://raw.githubusercontent.com/SumitJambhale/GitCheck/main/install.sh | bash';
  const windowsCmd = 'irm https://raw.githubusercontent.com/SumitJambhale/GitCheck/main/install.ps1 | iex';
  const startCmd = 'git-check --help\ngit-check install-hook';

  const macScriptUrl = 'https://raw.githubusercontent.com/SumitJambhale/GitCheck/main/install.sh';
  const windowsScriptUrl = 'https://raw.githubusercontent.com/SumitJambhale/GitCheck/main/install.ps1';
  const releasesUrl = 'https://github.com/SumitJambhale/GitCheck/releases';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center space-x-3 mb-5">
          <div className="h-10 w-10 rounded-xl bg-blue-600/20 text-blue-400 flex items-center justify-center">
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">How the Client Installs It (The 1-Line Command)</h3>
            <p className="text-xs text-slate-400">Zero-dependency standalone binary installation</p>
          </div>
        </div>

        <div className="space-y-4">
          {/* macOS and Linux */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-slate-200">For macOS and Linux:</span>
              <a
                href={macScriptUrl}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center space-x-1"
              >
                <span>View install.sh</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <div className="relative">
              <pre className="bg-slate-900/90 border border-slate-800 p-2.5 pr-10 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto">
                {macLinuxCmd}
              </pre>
              <button
                onClick={() => copyCode(macLinuxCmd, 'mac')}
                className="absolute top-2 right-2 p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                title="Copy command"
              >
                {copiedSection === 'mac' ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>

          {/* Windows PowerShell */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-slate-200">For Windows (PowerShell):</span>
              <a
                href={windowsScriptUrl}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center space-x-1"
              >
                <span>View install.ps1</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <div className="relative">
              <pre className="bg-slate-900/90 border border-slate-800 p-2.5 pr-10 rounded-lg text-xs font-mono text-cyan-400 overflow-x-auto">
                {windowsCmd}
              </pre>
              <button
                onClick={() => copyCode(windowsCmd, 'win')}
                className="absolute top-2 right-2 p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                title="Copy command"
              >
                {copiedSection === 'win' ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>

          {/* Start Using GitCheck */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5">
            <div className="mb-1.5">
              <span className="text-xs font-semibold text-slate-200">Start using GitCheck:</span>
            </div>
            <div className="relative">
              <pre className="bg-slate-900/90 border border-slate-800 p-2.5 pr-10 rounded-lg text-xs font-mono text-slate-200 overflow-x-auto leading-relaxed">
                {startCmd}
              </pre>
              <button
                onClick={() => copyCode(startCmd, 'start')}
                className="absolute top-2 right-2 p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                title="Copy command"
              >
                {copiedSection === 'start' ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>

          {/* Direct URLs */}
          <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
            <span>Direct Releases & Binaries:</span>
            <a
              href={releasesUrl}
              target="_blank"
              rel="noreferrer"
              className="text-blue-400 hover:text-blue-300 flex items-center space-x-1 font-mono text-[11px]"
            >
              <span>{releasesUrl}</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
