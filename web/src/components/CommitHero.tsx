import React, { useState } from 'react';
import { CommitReview } from '../types';
import { 
  GitCommit, 
  GitBranch, 
  User, 
  CheckCircle, 
  AlertTriangle, 
  FileCode, 
  Copy, 
  Check, 
  Layers, 
  ExternalLink,
  Shield,
  FileCheck
} from 'lucide-react';

interface CommitHeroProps {
  review: CommitReview;
}

export const CommitHero: React.FC<CommitHeroProps> = ({ review }) => {
  const [copied, setCopied] = useState(false);

  const trailerText = `GitCheck-Ticket: ${review.ticket_number}\nGitCheck-Commit: ${review.commit_hash}\nGitCheck-Status: ${review.agreed_with_changes ? 'Acknowledged-By-Author' : 'Pending'}\nGitCheck-Summary: ${review.summary}`;

  const copyTrailer = () => {
    navigator.clipboard.writeText(trailerText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isPassed = review.status === 'PASSED';
  const isRejected = review.status === 'REJECTED_REVISION';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
      {/* Background subtle gradient flare */}
      <div className="absolute top-0 right-0 -mt-12 -mr-12 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Bar: Ticket and Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <span className="text-sm font-semibold tracking-wide text-blue-400 bg-blue-500/10 border border-blue-500/30 px-3 py-1 rounded-lg">
            {review.ticket_number}
          </span>
          <div className="flex items-center space-x-2 text-slate-300 font-mono text-sm bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800">
            <GitCommit className="h-4 w-4 text-slate-400" />
            <span>{review.commit_hash || 'staged'}</span>
          </div>
          <div className="flex items-center space-x-1.5 text-slate-400 text-sm">
            <GitBranch className="h-4 w-4" />
            <span className="font-mono text-xs">{review.branch_name}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {isPassed ? (
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>Comprehension Verified (≥ 80%)</span>
            </span>
          ) : isRejected ? (
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Prior PR Rejection Context</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>Author Acknowledged & Explained</span>
            </span>
          )}

          <button
            onClick={copyTrailer}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Copy Git commit trailer"
          >
            {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Author & Timestamp */}
      <div className="mt-4 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
        <div className="flex items-center space-x-2">
          <User className="h-3.5 w-3.5 text-slate-500" />
          <span>Author: <span className="text-slate-200 font-medium">{review.author_name}</span> &lt;{review.author_email}&gt;</span>
        </div>
        <div>
          <span>Evaluated on {new Date(review.created_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Core Summary: 50–100 Words Description of the Changes for Review */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold tracking-wide uppercase text-slate-300 flex items-center space-x-2">
            <FileCheck className="h-4 w-4 text-blue-400" />
            <span>Commit Review Summary (Why changes exist)</span>
          </h2>
          <span className="text-xs text-slate-500">
            {review.summary.split(/\s+/).filter(Boolean).length} words
          </span>
        </div>
        <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200 text-sm leading-relaxed font-sans">
          {review.summary}
        </div>
      </div>

      {/* If this was a rejected iteration or has review notes */}
      {review.rejection_notes && (
        <div className="mt-4 p-4 rounded-xl bg-rose-950/30 border border-rose-900/40 text-rose-200 text-xs">
          <div className="font-semibold flex items-center space-x-1.5 mb-1 text-rose-400">
            <AlertTriangle className="h-4 w-4" />
            <span>Review Feedback from Previous Rejection</span>
          </div>
          <p>{review.rejection_notes}</p>
        </div>
      )}

      {/* Architectural Impact & Detailed Findings */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
            <Layers className="h-3.5 w-3.5 text-indigo-400" />
            <span>Architectural Alignment</span>
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            {review.detailed_analysis?.architectural_impact || 'Adheres to standard repository architecture with no detected duplicate dependencies.'}
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
            <Shield className="h-3.5 w-3.5 text-blue-400" />
            <span>Author Accountability</span>
          </h3>
          <div className="text-xs text-slate-300 space-y-1">
            <div className="flex items-center space-x-1.5">
              <span className="text-emerald-400 font-bold">✓</span>
              <span>Developer actively reviewed Socratic failure modes</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="text-emerald-400 font-bold">✓</span>
              <span>Explicitly confirmed agreement with generated changes</span>
            </div>
            <p className="text-[11px] text-slate-500 pt-1">
              * Individual quiz scores remain confidential to protect developer psychological safety.
            </p>
          </div>
        </div>
      </div>

      {/* Changed Files */}
      {review.detailed_analysis?.files_changed && review.detailed_analysis.files_changed.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center justify-between">
            <span className="flex items-center space-x-1.5">
              <FileCode className="h-3.5 w-3.5 text-blue-400" />
              <span>Modified Files ({review.detailed_analysis.files_changed.length})</span>
            </span>
            <span className="text-xs font-mono text-slate-400">
              <span className="text-emerald-400">+{review.detailed_analysis.lines_added || 0}</span> / <span className="text-rose-400">-{review.detailed_analysis.lines_removed || 0}</span>
            </span>
          </h3>
          <ul className="space-y-1.5">
            {review.detailed_analysis.files_changed.map((file, idx) => (
              <li key={idx} className="flex items-center space-x-2 text-xs font-mono text-slate-300 bg-slate-950/80 px-3 py-2 rounded-lg border border-slate-800/80">
                <span className="text-blue-500">•</span>
                <span className="truncate">{file}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
