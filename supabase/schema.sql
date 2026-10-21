-- GitCheck: Supabase PostgreSQL Schema
-- Stores commit comprehension findings, architectural summaries, and previous context.

CREATE TABLE IF NOT EXISTS git_check_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(100) NOT NULL,
    branch_name VARCHAR(255),
    commit_hash VARCHAR(64),
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    summary TEXT NOT NULL,                     -- 50-100 word summary of why the changes exist
    detailed_analysis JSONB DEFAULT '{}'::jsonb, -- Files modified, architectural impact, dependencies
    agreed_with_changes BOOLEAN DEFAULT true, -- Whether engineer confirmed agreement
    passed_verification BOOLEAN DEFAULT false, -- Internal validation result (kept confidential)
    status VARCHAR(50) DEFAULT 'COMPLETED',   -- 'PASSED', 'ACKNOWLEDGED', 'REJECTED_REVISION'
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for lightning-fast lookup by ticket number and recency
CREATE INDEX IF NOT EXISTS idx_git_check_ticket ON git_check_reviews (ticket_number);
CREATE INDEX IF NOT EXISTS idx_git_check_commit ON git_check_reviews (commit_hash);
CREATE INDEX IF NOT EXISTS idx_git_check_created ON git_check_reviews (created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE git_check_reviews ENABLE ROW LEVEL SECURITY;

-- Allow public read access for the single-page web dashboard
CREATE POLICY "Allow public read access for dashboard"
    ON git_check_reviews
    FOR SELECT
    USING (true);

-- Allow authenticated or anon clients to insert reviews via CLI
CREATE POLICY "Allow anon insert from GitCheck CLI"
    ON git_check_reviews
    FOR INSERT
    WITH CHECK (true);

-- Allow updating review record
CREATE POLICY "Allow update for existing reviews"
    ON git_check_reviews
    FOR UPDATE
    USING (true);

-- Sample starter record for demonstration and testing
INSERT INTO git_check_reviews (
    ticket_number,
    branch_name,
    commit_hash,
    author_name,
    author_email,
    summary,
    detailed_analysis,
    agreed_with_changes,
    passed_verification,
    status
) VALUES (
    'PROJ-402',
    'feat/PROJ-402-payment-webhook-retry',
    '8f3b12a',
    'Milind Mane',
    'milind.mane@company.internal',
    'Introduced exponential backoff retry mechanism for failed payment gateway webhooks. Centralized retry state in distributed Redis cache to prevent redundant transaction processing under high network latency, avoiding race conditions during peak checkout volumes.',
    '{
        "files_changed": [
            "src/services/payment_webhook.py",
            "src/infrastructure/redis_cache.py",
            "tests/test_webhook_retry.py"
        ],
        "lines_added": 84,
        "lines_removed": 12,
        "architectural_impact": "Uses shared Redis connection pool rather than instantiating isolated connections; complies with core microservice resiliency guidelines."
    }'::jsonb,
    true,
    true,
    'PASSED'
) ON CONFLICT DO NOTHING;
