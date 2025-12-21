-- ============================================================
-- MONEY MACHINE - DATABASE SCHEMA
-- Telemetry + Self-Improvement Data Layer
-- ============================================================
-- This schema enables the SelfImprover to learn from real data
-- instead of guessing. Every engine run, content piece, and
-- financial event is tracked for optimization.
-- ============================================================

-- ============================================================
-- CORE TRACKING TABLES
-- ============================================================

-- Track every engine execution
CREATE TABLE IF NOT EXISTS engine_runs (
    id SERIAL PRIMARY KEY,
    run_id UUID DEFAULT gen_random_uuid(),
    engine TEXT NOT NULL,
    action TEXT,
    status TEXT NOT NULL CHECK (status IN ('started', 'success', 'failed', 'timeout', 'healed')),
    duration_ms INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for performance queries
CREATE INDEX IF NOT EXISTS idx_engine_runs_engine ON engine_runs(engine);
CREATE INDEX IF NOT EXISTS idx_engine_runs_status ON engine_runs(status);
CREATE INDEX IF NOT EXISTS idx_engine_runs_created ON engine_runs(created_at);

-- Track content performance across platforms
CREATE TABLE IF NOT EXISTS content_metrics (
    id SERIAL PRIMARY KEY,
    content_id TEXT UNIQUE,
    niche TEXT NOT NULL,
    platform TEXT NOT NULL,
    title TEXT,
    
    -- Performance metrics
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    watch_time_seconds INTEGER DEFAULT 0,
    
    -- Revenue metrics
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue NUMERIC(10,2) DEFAULT 0,
    rpm NUMERIC(10,4) DEFAULT 0,
    
    -- Calculated fields
    engagement_rate NUMERIC(5,4) DEFAULT 0,
    ctr NUMERIC(5,4) DEFAULT 0,
    
    -- Status
    status TEXT DEFAULT 'published',
    is_winner BOOLEAN DEFAULT false,
    
    -- Timestamps
    published_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_content_niche ON content_metrics(niche);
CREATE INDEX IF NOT EXISTS idx_content_platform ON content_metrics(platform);
CREATE INDEX IF NOT EXISTS idx_content_rpm ON content_metrics(rpm DESC);

-- Track all financial events
CREATE TABLE IF NOT EXISTS financial_events (
    id SERIAL PRIMARY KEY,
    event_id UUID DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'sale', 'refund', 'payout', 'sweep', 'allocation',
        'ad_spend', 'subscription', 'tip', 'affiliate_commission'
    )),
    amount NUMERIC(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    description TEXT,
    reference_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_financial_source ON financial_events(source);
CREATE INDEX IF NOT EXISTS idx_financial_type ON financial_events(event_type);
CREATE INDEX IF NOT EXISTS idx_financial_created ON financial_events(created_at);

-- ============================================================
-- PROFIT-FIRST ALLOCATION TABLES
-- ============================================================

-- Track balance allocations
CREATE TABLE IF NOT EXISTS profit_allocations (
    id SERIAL PRIMARY KEY,
    allocation_id UUID DEFAULT gen_random_uuid(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Source amounts
    total_revenue NUMERIC(10,2) DEFAULT 0,
    total_expenses NUMERIC(10,2) DEFAULT 0,
    net_profit NUMERIC(10,2) DEFAULT 0,
    
    -- Allocated amounts (30/40/30)
    tax_reserve NUMERIC(10,2) DEFAULT 0,
    reinvest_fund NUMERIC(10,2) DEFAULT 0,
    owner_profit NUMERIC(10,2) DEFAULT 0,
    
    -- Reinvest breakdown
    ads_budget NUMERIC(10,2) DEFAULT 0,
    tools_budget NUMERIC(10,2) DEFAULT 0,
    content_budget NUMERIC(10,2) DEFAULT 0,
    
    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'transferred')),
    processed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SELF-HEALING TABLES
-- ============================================================

-- Track healing actions
CREATE TABLE IF NOT EXISTS healing_events (
    id SERIAL PRIMARY KEY,
    event_id UUID DEFAULT gen_random_uuid(),
    component TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT,
    
    -- Healing details
    strategy_used TEXT,
    healing_action TEXT,
    success BOOLEAN,
    retry_count INTEGER DEFAULT 0,
    
    -- Learning data
    context JSONB DEFAULT '{}',
    outcome JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_healing_component ON healing_events(component);
CREATE INDEX IF NOT EXISTS idx_healing_error ON healing_events(error_type);

-- Track system health snapshots
CREATE TABLE IF NOT EXISTS health_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_id UUID DEFAULT gen_random_uuid(),
    
    -- Overall health
    health_score INTEGER CHECK (health_score >= 0 AND health_score <= 100),
    status TEXT CHECK (status IN ('healthy', 'degraded', 'critical', 'offline')),
    
    -- Component health
    components JSONB DEFAULT '{}',
    
    -- Resource usage
    cpu_percent NUMERIC(5,2),
    memory_percent NUMERIC(5,2),
    disk_percent NUMERIC(5,2),
    
    -- API health
    api_status JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SELF-IMPROVEMENT TABLES
-- ============================================================

-- Track learning outcomes
CREATE TABLE IF NOT EXISTS learning_outcomes (
    id SERIAL PRIMARY KEY,
    outcome_id UUID DEFAULT gen_random_uuid(),
    category TEXT NOT NULL,
    action TEXT NOT NULL,
    
    -- Context
    context JSONB DEFAULT '{}',
    
    -- Result
    success BOOLEAN,
    impact_score NUMERIC(5,2),
    
    -- What we learned
    lesson TEXT,
    recommendation TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learning_category ON learning_outcomes(category);

-- Track optimization decisions
CREATE TABLE IF NOT EXISTS optimization_decisions (
    id SERIAL PRIMARY KEY,
    decision_id UUID DEFAULT gen_random_uuid(),
    
    -- What was optimized
    target TEXT NOT NULL,
    metric TEXT NOT NULL,
    
    -- Before/after
    before_value NUMERIC(10,4),
    after_value NUMERIC(10,4),
    improvement_percent NUMERIC(5,2),
    
    -- Decision details
    reason TEXT,
    action_taken TEXT,
    
    -- Validation
    validated BOOLEAN DEFAULT false,
    validated_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- NICHE PERFORMANCE TABLES
-- ============================================================

-- Track niche-level performance
CREATE TABLE IF NOT EXISTS niche_performance (
    id SERIAL PRIMARY KEY,
    niche TEXT NOT NULL,
    date DATE NOT NULL,
    
    -- Content metrics
    videos_published INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    avg_watch_time INTEGER DEFAULT 0,
    
    -- Revenue metrics
    revenue NUMERIC(10,2) DEFAULT 0,
    rpm NUMERIC(10,4) DEFAULT 0,
    
    -- Engagement
    total_clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    email_optins INTEGER DEFAULT 0,
    
    -- Score (calculated)
    performance_score NUMERIC(5,2) DEFAULT 0,
    
    UNIQUE(niche, date)
);

CREATE INDEX IF NOT EXISTS idx_niche_perf_date ON niche_performance(date);

-- ============================================================
-- AD REINVESTMENT TABLES
-- ============================================================

-- Track ad campaigns
CREATE TABLE IF NOT EXISTS ad_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id UUID DEFAULT gen_random_uuid(),
    
    -- Target
    content_id TEXT REFERENCES content_metrics(content_id),
    platform TEXT NOT NULL,
    niche TEXT,
    
    -- Budget
    daily_budget NUMERIC(10,2),
    total_spend NUMERIC(10,2) DEFAULT 0,
    
    -- Performance
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue_generated NUMERIC(10,2) DEFAULT 0,
    
    -- ROI
    roi NUMERIC(10,4) DEFAULT 0,
    
    -- Status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'stopped', 'completed')),
    
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- VIEWS FOR ANALYTICS
-- ============================================================

-- Daily revenue summary
CREATE OR REPLACE VIEW daily_revenue AS
SELECT 
    DATE(created_at) as date,
    source,
    event_type,
    SUM(amount) as total_amount,
    COUNT(*) as event_count
FROM financial_events
WHERE event_type IN ('sale', 'affiliate_commission', 'tip')
GROUP BY DATE(created_at), source, event_type
ORDER BY date DESC;

-- Niche leaderboard
CREATE OR REPLACE VIEW niche_leaderboard AS
SELECT 
    niche,
    COUNT(*) as content_count,
    SUM(views) as total_views,
    SUM(revenue) as total_revenue,
    AVG(rpm) as avg_rpm,
    AVG(engagement_rate) as avg_engagement
FROM content_metrics
WHERE published_at > CURRENT_DATE - INTERVAL '30 days'
GROUP BY niche
ORDER BY total_revenue DESC;

-- Winner content (top 10%)
CREATE OR REPLACE VIEW winner_content AS
SELECT *
FROM content_metrics
WHERE rpm > (SELECT PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY rpm) FROM content_metrics)
ORDER BY rpm DESC;

-- Healing effectiveness
CREATE OR REPLACE VIEW healing_effectiveness AS
SELECT 
    component,
    error_type,
    strategy_used,
    COUNT(*) as attempts,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
    ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM healing_events
GROUP BY component, error_type, strategy_used
ORDER BY attempts DESC;

-- ============================================================
-- FUNCTIONS FOR AUTOMATION
-- ============================================================

-- Function to calculate content RPM
CREATE OR REPLACE FUNCTION calculate_rpm(p_content_id TEXT)
RETURNS NUMERIC AS $$
DECLARE
    v_views INTEGER;
    v_revenue NUMERIC;
BEGIN
    SELECT views, revenue INTO v_views, v_revenue
    FROM content_metrics WHERE content_id = p_content_id;
    
    IF v_views > 0 THEN
        RETURN ROUND((v_revenue / v_views) * 1000, 4);
    ELSE
        RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to get niche performance score
CREATE OR REPLACE FUNCTION get_niche_score(p_niche TEXT)
RETURNS NUMERIC AS $$
DECLARE
    v_rpm_score NUMERIC;
    v_volume_score NUMERIC;
    v_engagement_score NUMERIC;
BEGIN
    SELECT 
        COALESCE(AVG(rpm), 0),
        COALESCE(COUNT(*), 0),
        COALESCE(AVG(engagement_rate), 0)
    INTO v_rpm_score, v_volume_score, v_engagement_score
    FROM content_metrics 
    WHERE niche = p_niche 
    AND published_at > CURRENT_DATE - INTERVAL '7 days';
    
    -- Weighted score: RPM 50%, Volume 30%, Engagement 20%
    RETURN ROUND((v_rpm_score * 0.5) + (v_volume_score * 0.3) + (v_engagement_score * 100 * 0.2), 2);
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- TRIGGERS FOR AUTOMATION
-- ============================================================

-- Auto-update RPM when views/revenue change
CREATE OR REPLACE FUNCTION update_content_rpm()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.views > 0 THEN
        NEW.rpm := ROUND((NEW.revenue / NEW.views) * 1000, 4);
    END IF;
    
    IF NEW.views > 0 THEN
        NEW.engagement_rate := ROUND((NEW.likes + NEW.comments + NEW.shares)::NUMERIC / NEW.views, 4);
    END IF;
    
    IF NEW.views > 0 THEN
        NEW.ctr := ROUND(NEW.clicks::NUMERIC / NEW.views, 4);
    END IF;
    
    NEW.last_updated := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_content_rpm
    BEFORE UPDATE ON content_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_content_rpm();

-- Mark winners automatically
CREATE OR REPLACE FUNCTION mark_winners()
RETURNS TRIGGER AS $$
DECLARE
    v_threshold NUMERIC;
BEGIN
    SELECT PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY rpm) 
    INTO v_threshold FROM content_metrics;
    
    IF NEW.rpm >= v_threshold THEN
        NEW.is_winner := true;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mark_winners
    BEFORE INSERT OR UPDATE ON content_metrics
    FOR EACH ROW
    EXECUTE FUNCTION mark_winners();
