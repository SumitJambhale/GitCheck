import React from 'react';
import { CommitReview } from '../types';
import { History, AlertCircle, CheckCircle, ArrowRight, CornerDownRight } from 'lucide-react';

interface PreviousContextTimelineProps {
  currentReview: CommitReview;
  allTicketReviews: CommitReview[];
  onSelectReview: (rev: CommitReview) => void;
}

export const PreviousContextTimeline: React.FC<PreviousContextTimelineProps> = ({
  currentReview,
  allTicketReviews,
  onSelectReview,
}) => {
  // Sort oldest to newest for chronological story
  const history = [...allTicketReviews].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <History className="h-5 w-5 text-indigo-400" />
          <h3 className="font-semibold text-slate-200 text-sm">
            Previous Context & Iteration History
          </h3>
        </div>
        <span className="text-xs text-slate-400">
          Ticket: <strong className="text-blue-400">{currentReview.ticket_number}</strong>
        </span>
      </div>

      <p className="text-xs text-slate-400 mt-2 mb-4">
        When PRs get rejected during code review, tracking previous architectural rationale prevents repeated rework and helps authors defend improvements.
      </p>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
        {history.map((item, idx) => {
          const isSelected = item.id === currentReview.id;
          const isRejected = item.status === 'REJECTED_REVISION';
          const isLatest = idx === history.length - 1;

          return (
            <div key={item.id} className="relative group">
              {/* Dot on timeline */}
              <div
                className={`absolute -left-6 top-1.5 h-5 w-5 rounded-full border-2 flex items-center justify-center transition-all ${
                  isRejected
                    ? 'border-rose-500 bg-rose-950 text-rose-400'
                    : 'border-emerald-500 bg-emerald-950 text-emerald-400'
                } ${isSelected ? 'ring-4 ring-blue-500/30' : ''}`}
              >
                {isRejected ? (
                  <AlertCircle className="h-3 w-3" />
                ) : (
                  <CheckCircle className="h-3 w-3" />
                )}
              </div>

              {/* Card */}
              <div
                onClick={() => onSelectReview(item)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-slate-800/90 border-blue-500/50 shadow-md ring-1 ring-blue-500/20'
                    : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-800/50 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-slate-300">
                    Iteration {idx + 1} {isLatest && <span className="ml-1 text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded">Current</span>}
                  </span>
                  <span className="font-mono text-slate-400">{item.commit_hash}</span>
                </div>

                <div className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                  {item.summary}
                </div>

                {item.rejection_notes && (
                  <div className="mt-2.5 pt-2 border-t border-slate-800/80 text-[11px] text-rose-300 flex items-start space-x-1.5">
                    <CornerDownRight className="h-3.5 w-3.5 mt-0.5 text-rose-400 shrink-0" />
                    <span><strong>Previous Rejection Reason:</strong> {item.rejection_notes}</span>
                  </div>
                )}

                <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  <span className="text-blue-400 group-hover:underline flex items-center space-x-1">
                    <span>Inspect</span>
                    <ArrowRight className="h-3 w-3" />
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
