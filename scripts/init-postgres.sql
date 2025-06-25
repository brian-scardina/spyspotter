-- PixelTracker PostgreSQL Database Initialization Script
-- Creates tables and initial data for the PixelTracker application

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database schema
CREATE SCHEMA IF NOT EXISTS pixeltracker;

-- Set default schema
SET search_path TO pixeltracker, public;

-- ==========================================
-- MAIN TABLES
-- ==========================================

-- Tracking scans table
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    scan_type VARCHAR(50) NOT NULL DEFAULT 'basic',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    privacy_score INTEGER,
    risk_level VARCHAR(20),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Detected trackers table
CREATE TABLE IF NOT EXISTS trackers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    tracker_type VARCHAR(50) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    url TEXT,
    method VARCHAR(20),
    risk_level VARCHAR(20),
    category VARCHAR(100),
    company VARCHAR(255),
    purpose TEXT,
    gdpr_relevant BOOLEAN DEFAULT FALSE,
    ccpa_relevant BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Known tracking domains table
CREATE TABLE IF NOT EXISTS known_domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) NOT NULL UNIQUE,
    company VARCHAR(255),
    category VARCHAR(100) NOT NULL,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    purpose TEXT,
    gdpr_relevant BOOLEAN DEFAULT FALSE,
    ccpa_relevant BOOLEAN DEFAULT FALSE,
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    scan_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Detection patterns table
CREATE TABLE IF NOT EXISTS detection_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type VARCHAR(50) NOT NULL,
    pattern TEXT NOT NULL,
    description TEXT,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Scan metadata table for additional information
CREATE TABLE IF NOT EXISTS scan_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ==========================================
-- INDEXES
-- ==========================================

-- Scans indexes
CREATE INDEX IF NOT EXISTS idx_scans_url ON scans(url);
CREATE INDEX IF NOT EXISTS idx_scans_started_at ON scans(started_at);
CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_scans_scan_type ON scans(scan_type);

-- Trackers indexes
CREATE INDEX IF NOT EXISTS idx_trackers_scan_id ON trackers(scan_id);
CREATE INDEX IF NOT EXISTS idx_trackers_domain ON trackers(domain);
CREATE INDEX IF NOT EXISTS idx_trackers_tracker_type ON trackers(tracker_type);
CREATE INDEX IF NOT EXISTS idx_trackers_risk_level ON trackers(risk_level);
CREATE INDEX IF NOT EXISTS idx_trackers_detected_at ON trackers(detected_at);

-- Known domains indexes
CREATE INDEX IF NOT EXISTS idx_known_domains_domain ON known_domains(domain);
CREATE INDEX IF NOT EXISTS idx_known_domains_category ON known_domains(category);
CREATE INDEX IF NOT EXISTS idx_known_domains_risk_level ON known_domains(risk_level);
CREATE INDEX IF NOT EXISTS idx_known_domains_company ON known_domains(company);
CREATE INDEX IF NOT EXISTS idx_known_domains_is_active ON known_domains(is_active);

-- Detection patterns indexes
CREATE INDEX IF NOT EXISTS idx_detection_patterns_type ON detection_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_detection_patterns_active ON detection_patterns(is_active);

-- Scan metadata indexes
CREATE INDEX IF NOT EXISTS idx_scan_metadata_scan_id ON scan_metadata(scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_metadata_key ON scan_metadata(key);

-- ==========================================
-- FUNCTIONS AND TRIGGERS
-- ==========================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_scans_updated_at BEFORE UPDATE ON scans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_known_domains_updated_at BEFORE UPDATE ON known_domains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_detection_patterns_updated_at BEFORE UPDATE ON detection_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- INITIAL DATA
-- ==========================================

-- Insert some common tracking domains
INSERT INTO known_domains (domain, company, category, risk_level, purpose, gdpr_relevant, ccpa_relevant) VALUES 
    ('google-analytics.com', 'Google', 'Analytics', 'medium', 'Web analytics and user behavior tracking', TRUE, TRUE),
    ('googletagmanager.com', 'Google', 'Tag Management', 'medium', 'Tag management and tracking', TRUE, TRUE),
    ('facebook.com', 'Meta', 'Social Media', 'high', 'Social media tracking and advertising', TRUE, TRUE),
    ('doubleclick.net', 'Google', 'Advertising', 'high', 'Online advertising and tracking', TRUE, TRUE),
    ('amazon-adsystem.com', 'Amazon', 'Advertising', 'high', 'Amazon advertising network', TRUE, TRUE),
    ('googleadservices.com', 'Google', 'Advertising', 'high', 'Google Ads tracking', TRUE, TRUE),
    ('googlesyndication.com', 'Google', 'Advertising', 'high', 'Google AdSense', TRUE, TRUE),
    ('youtube.com', 'Google', 'Video', 'medium', 'Video tracking and analytics', TRUE, TRUE),
    ('twitter.com', 'Twitter', 'Social Media', 'medium', 'Social media widgets and tracking', TRUE, TRUE),
    ('linkedin.com', 'LinkedIn', 'Social Media', 'medium', 'Professional networking tracking', TRUE, TRUE),
    ('hotjar.com', 'Hotjar', 'Analytics', 'high', 'Heatmaps and session recording', TRUE, TRUE),
    ('mixpanel.com', 'Mixpanel', 'Analytics', 'medium', 'Product analytics', TRUE, TRUE),
    ('segment.com', 'Segment', 'Analytics', 'medium', 'Customer data platform', TRUE, TRUE),
    ('amplitude.com', 'Amplitude', 'Analytics', 'medium', 'Product analytics', TRUE, TRUE),
    ('fullstory.com', 'FullStory', 'Analytics', 'high', 'Digital experience analytics', TRUE, TRUE)
ON CONFLICT (domain) DO NOTHING;

-- Insert common detection patterns
INSERT INTO detection_patterns (pattern_type, pattern, description, risk_level, category) VALUES 
    ('pixel', '1x1', '1x1 pixel tracking images', 'medium', 'Tracking Pixel'),
    ('pixel', 'tracking', 'Generic tracking pixel patterns', 'medium', 'Tracking Pixel'),
    ('script', 'analytics', 'Analytics script detection', 'medium', 'Analytics'),
    ('script', 'gtag', 'Google Analytics gtag detection', 'medium', 'Analytics'),
    ('script', 'fbq', 'Facebook Pixel detection', 'high', 'Social Media'),
    ('script', '_gaq', 'Google Analytics classic detection', 'medium', 'Analytics'),
    ('url', 'collect', 'Data collection endpoint', 'medium', 'Data Collection'),
    ('url', 'track', 'Tracking endpoint', 'medium', 'Tracking'),
    ('url', 'event', 'Event tracking endpoint', 'medium', 'Event Tracking'),
    ('header', 'doubleclick', 'DoubleClick advertising', 'high', 'Advertising')
ON CONFLICT DO NOTHING;

-- ==========================================
-- VIEWS
-- ==========================================

-- View for scan summaries
CREATE OR REPLACE VIEW scan_summaries AS
SELECT 
    s.id,
    s.url,
    s.scan_type,
    s.status,
    s.started_at,
    s.completed_at,
    s.duration_ms,
    s.privacy_score,
    s.risk_level,
    COUNT(t.id) as tracker_count,
    COUNT(DISTINCT t.domain) as unique_domains,
    COUNT(CASE WHEN t.risk_level = 'high' THEN 1 END) as high_risk_trackers,
    COUNT(CASE WHEN t.gdpr_relevant = TRUE THEN 1 END) as gdpr_relevant_trackers,
    COUNT(CASE WHEN t.ccpa_relevant = TRUE THEN 1 END) as ccpa_relevant_trackers
FROM scans s
LEFT JOIN trackers t ON s.id = t.scan_id
GROUP BY s.id, s.url, s.scan_type, s.status, s.started_at, s.completed_at, 
         s.duration_ms, s.privacy_score, s.risk_level;

-- View for domain statistics
CREATE OR REPLACE VIEW domain_statistics AS
SELECT 
    kd.domain,
    kd.company,
    kd.category,
    kd.risk_level,
    kd.scan_count,
    COUNT(t.id) as detection_count,
    MAX(t.detected_at) as last_detected,
    COUNT(DISTINCT t.scan_id) as scans_found_in
FROM known_domains kd
LEFT JOIN trackers t ON kd.domain = t.domain
WHERE kd.is_active = TRUE
GROUP BY kd.domain, kd.company, kd.category, kd.risk_level, kd.scan_count
ORDER BY detection_count DESC;

-- ==========================================
-- PERMISSIONS
-- ==========================================

-- Grant permissions to the pixeltracker user
GRANT USAGE ON SCHEMA pixeltracker TO pixeltracker;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pixeltracker TO pixeltracker;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA pixeltracker TO pixeltracker;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA pixeltracker TO pixeltracker;

-- Grant permissions on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA pixeltracker GRANT ALL ON TABLES TO pixeltracker;
ALTER DEFAULT PRIVILEGES IN SCHEMA pixeltracker GRANT ALL ON SEQUENCES TO pixeltracker;
ALTER DEFAULT PRIVILEGES IN SCHEMA pixeltracker GRANT ALL ON FUNCTIONS TO pixeltracker;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'PixelTracker PostgreSQL database initialized successfully!';
    RAISE NOTICE 'Schema: pixeltracker';
    RAISE NOTICE 'Tables created: scans, trackers, known_domains, detection_patterns, scan_metadata';
    RAISE NOTICE 'Views created: scan_summaries, domain_statistics';
END $$;
