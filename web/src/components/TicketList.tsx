import React from 'react';
import { CommitReview } from '../types';
import { Search, Filter, Clock, CheckCircle2, AlertCircle } from 'lucide-react';

interface TicketListProps {
  reviews: CommitReview[];
  selectedTicket: string;
  onSelectTicket: (ticket: string) => void;
  searchTerm: string;
  onSearchChange: (val: string) => void;
}

export const TicketList: React.FC<TicketListProps> = ({
  reviews,
  selectedTicket,
  onSelectTicket,
  searchTerm,
  onSearchChange,
}) => {
  // Group reviews by ticket
  const ticketGroups = reviews.reduce((acc, r) => {
    if (!acc[r.ticket_number]) {
      acc[r.ticket_number] = [];
    }
    acc[r.ticket_number].push(r);
    return acc;
  }, {} as Record<string, CommitReview[]>);

  const filteredTickets = Object.keys(ticketGroups).filter(
    (ticket) =>
      ticket.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticketGroups[ticket].some((r) =>
        r.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.branch_name.toLowerCase().includes(searchTerm.toLowerCase())
      )
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
      <div className="mb-4">
        <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
          Find Ticket / PR
        </label>
        <div className="relative">
          <Search className="h-4 w-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search PROJ-402, author, keywords..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Active Tickets ({filteredTickets.length})
        </span>

        {filteredTickets.map((ticket) => {
          const group = ticketGroups[ticket];
          const latest = group[0];
          const isSelected = ticket === selectedTicket;
          const hasRejection = group.some((r) => r.status === 'REJECTED_REVISION');

          return (
            <div
              key={ticket}
              onClick={() => onSelectTicket(ticket)}
              className={`p-3 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-blue-600/10 border-blue-500 text-white shadow-sm'
                  : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-800/50 hover:border-slate-700 text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-xs tracking-tight text-blue-400">
                  {ticket}
                </span>
                <span className="text-[10px] text-slate-500 flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>{new Date(latest.created_at).toLocaleDateString()}</span>
                </span>
              </div>

              <p className="text-xs text-slate-300 line-clamp-1">{latest.summary}</p>

              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 pt-1.5 border-t border-slate-800/50">
                <span className="truncate max-w-[140px] font-mono text-[10px]">{latest.branch_name}</span>
                <span className="flex items-center space-x-1">
                  {hasRejection ? (
                    <span className="text-rose-400 text-[10px] bg-rose-500/10 px-1.5 py-0.5 rounded">
                      {group.length} Iterations
                    </span>
                  ) : (
                    <span className="text-emerald-400 text-[10px] bg-emerald-500/10 px-1.5 py-0.5 rounded flex items-center space-x-0.5">
                      <CheckCircle2 className="h-2.5 w-2.5" />
                      <span>{group.length} commit</span>
                    </span>
                  )}
                </span>
              </div>
            </div>
          );
        })}

        {filteredTickets.length === 0 && (
          <div className="text-center py-6 text-xs text-slate-500">
            No tickets matching search query.
          </div>
        )}
      </div>
    </div>
  );
};
