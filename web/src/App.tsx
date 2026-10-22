import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { CommitHero } from './components/CommitHero';
import { PreviousContextTimeline } from './components/PreviousContextTimeline';
import { TicketList } from './components/TicketList';
import { CliInstallModal } from './components/CliInstallModal';
import { CommitReview } from './types';
import { fetchReviewsDetailed } from './lib/supabase';
import { RefreshCw, ShieldAlert, Sparkles, AlertCircle, AlertTriangle } from 'lucide-react';

export const App: React.FC = () => {
  const [reviews, setReviews] = useState<CommitReview[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<string>('');
  const [activeReviewId, setActiveReviewId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [showCliModal, setShowCliModal] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [activeSupabaseUrl, setActiveSupabaseUrl] = useState<string>('');

  const loadData = async () => {
    setLoading(true);
    const res = await fetchReviewsDetailed();
    setReviews(res.reviews);
    setApiError(res.error);
    setActiveSupabaseUrl(res.supabaseUrl);
    if (res.reviews.length > 0) {
      setSelectedTicket((prev) => (prev && res.reviews.some(r => r.ticket_number === prev) ? prev : res.reviews[0].ticket_number));
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filter reviews for selected ticket
  const ticketReviews = reviews.filter((r) => r.ticket_number === selectedTicket);
  
  // The active review is either explicitly selected or the latest for that ticket
  const activeReview = activeReviewId
    ? reviews.find((r) => r.id === activeReviewId) || ticketReviews[0]
    : ticketReviews[0];

  const handleSelectTicket = (ticket: string) => {
    setSelectedTicket(ticket);
    setActiveReviewId(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar onOpenCliGuide={() => setShowCliModal(true)} />

      {/* Main Single Page Review Dashboard */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Intro banner */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
              <span>PR Review & Architectural Context</span>
              <span className="text-xs bg-slate-800 text-slate-300 font-normal px-2.5 py-1 rounded-full border border-slate-700">
                Anti-Rework Engine
              </span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Provides previous context for rejected pull requests and architectural justifications before merging.
            </p>
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center space-x-2 text-xs font-medium px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            <span>Refresh Reviews</span>
          </button>
        </div>

        {/* Prominent error alert if Supabase returned an error */}
        {apiError && (
          <div className="mb-6 p-5 rounded-2xl bg-rose-950/40 border border-rose-800 text-rose-200 text-xs">
            <div className="font-semibold text-sm flex items-center space-x-2 text-rose-400 mb-1.5">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>Supabase Query Notice</span>
            </div>
            <p className="leading-relaxed">
              Database responded with error: <code className="bg-rose-900/40 px-1.5 py-0.5 rounded text-white">{apiError}</code>
            </p>
            <p className="mt-2 text-rose-300/80">
              If this mentions permission denied or RLS, execute <code className="text-white">supabase/schema.sql</code> in your Supabase SQL Editor.
            </p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 text-blue-500 animate-spin" />
          </div>
        ) : reviews.length === 0 ? (
          <div className="p-12 text-center bg-slate-900 rounded-2xl border border-slate-800">
            <AlertCircle className="h-10 w-10 text-amber-400 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-white">No Commit Reviews Found in Database</h3>
            <p className="text-xs text-slate-400 mt-1 mb-2">
              Connected to <code className="text-blue-400 font-mono">{activeSupabaseUrl || 'Supabase'}</code>. The table <code className="text-emerald-400 font-mono">git_check_reviews</code> returned 0 rows.
            </p>
            <p className="text-xs text-slate-500 mb-4">
              Run <code className="text-blue-400 font-mono">git-check run</code> locally to commit your first verified review!
            </p>
            <button
              onClick={() => setShowCliModal(true)}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white"
            >
              Open CLI Setup Guide
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Ticket Selector / Filter (4 cols) */}
            <div className="lg:col-span-4 space-y-6">
              <TicketList
                reviews={reviews}
                selectedTicket={selectedTicket}
                onSelectTicket={handleSelectTicket}
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
              />

              {/* Previous Context Timeline for the selected ticket */}
              {activeReview && (
                <PreviousContextTimeline
                  currentReview={activeReview}
                  allTicketReviews={ticketReviews}
                  onSelectReview={(rev) => setActiveReviewId(rev.id)}
                />
              )}
            </div>

            {/* Right Column: Single Page Description of the Commit (8 cols) */}
            <div className="lg:col-span-8 space-y-6">
              {activeReview ? (
                <CommitHero review={activeReview} />
              ) : (
                <div className="p-8 text-center bg-slate-900 rounded-2xl border border-slate-800 text-slate-400 text-sm">
                  Select a ticket to review its architectural description.
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-600">
        GitCheck • Pre-Commit Verification Gate & Code Comprehension Harness • Deployed to Vercel
      </footer>

      {/* CLI Installation Modal */}
      <CliInstallModal
        isOpen={showCliModal}
        onClose={() => setShowCliModal(false)}
      />
    </div>
  );
};
