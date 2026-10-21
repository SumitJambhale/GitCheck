export interface CommitReview {
  id: string;
  ticket_number: string;
  branch_name: string;
  commit_hash: string;
  author_name: string;
  author_email: string;
  summary: string; // 50-100 word concise summary
  detailed_analysis: {
    files_changed?: string[];
    lines_added?: number;
    lines_removed?: number;
    architectural_impact?: string;
  };
  agreed_with_changes: boolean;
  passed_verification: boolean;
  status: 'PASSED' | 'ACKNOWLEDGED' | 'ACKNOWLEDGED_WITH_EXPLANATION' | 'REJECTED_REVISION' | string;
  rejection_notes?: string;
  iteration_number?: number;
  created_at: string;
}
