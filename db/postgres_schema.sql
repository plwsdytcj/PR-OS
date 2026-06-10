CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS creator_profiles (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    enriched BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, creator_id)
);

CREATE TABLE IF NOT EXISTS creator_embeddings (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    creator_id TEXT NOT NULL,
    embedding VECTOR(1536),
    source TEXT NOT NULL DEFAULT 'profile',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, creator_id, source)
);

CREATE TABLE IF NOT EXISTS auth_users (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, user_id),
    UNIQUE (tenant_id, email)
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, session_id)
);

CREATE TABLE IF NOT EXISTS clients (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    client_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, client_id)
);

CREATE TABLE IF NOT EXISTS client_users (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    link_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, link_id)
);

CREATE TABLE IF NOT EXISTS project_access (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    access_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    client_id TEXT NOT NULL DEFAULT '',
    proposal_id TEXT NOT NULL DEFAULT '',
    campaign_id TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, access_id)
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    task_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, task_id)
);

CREATE TABLE IF NOT EXISTS agent_threads (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    thread_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, thread_id)
);

CREATE TABLE IF NOT EXISTS agent_messages (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    message_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL,
    run_id TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, message_id)
);

CREATE TABLE IF NOT EXISTS agent_runs (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, run_id)
);

CREATE TABLE IF NOT EXISTS agent_events (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    event_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, event_id)
);

CREATE TABLE IF NOT EXISTS agent_steps (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    step_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    tool_name TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, step_id)
);

CREATE TABLE IF NOT EXISTS agent_artifacts (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    artifact_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, artifact_id)
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    document_id TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    client_id TEXT NOT NULL DEFAULT '',
    project_id TEXT NOT NULL DEFAULT '',
    industry TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, document_id)
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    chunk_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    source_type TEXT NOT NULL DEFAULT 'manual',
    client_id TEXT NOT NULL DEFAULT '',
    project_id TEXT NOT NULL DEFAULT '',
    industry TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, chunk_id)
);

CREATE TABLE IF NOT EXISTS creator_symbolic_profiles (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, creator_id)
);

CREATE TABLE IF NOT EXISTS brand_symbolic_profiles (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    brand_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, brand_id)
);

CREATE TABLE IF NOT EXISTS simulation_reports (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    report_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, report_id)
);

CREATE TABLE IF NOT EXISTS social_symbolic_reports (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    report_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, report_id)
);

CREATE TABLE IF NOT EXISTS signifier_tags (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    tag_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, tag_id)
);

CREATE TABLE IF NOT EXISTS product_symbolic_profiles (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    product_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, product_id)
);

CREATE TABLE IF NOT EXISTS content_narrative_assets (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    narrative_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, narrative_id)
);

CREATE TABLE IF NOT EXISTS brand_creator_match_assets (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    match_id TEXT NOT NULL,
    brand_id TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, match_id)
);

CREATE TABLE IF NOT EXISTS feedback_corrections (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    correction_id TEXT NOT NULL,
    campaign_id TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, correction_id)
);

CREATE TABLE IF NOT EXISTS proposals (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    proposal_id TEXT NOT NULL,
    share_token TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, proposal_id),
    UNIQUE (tenant_id, share_token)
);

CREATE TABLE IF NOT EXISTS proposal_versions (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    version_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, version_id)
);

CREATE TABLE IF NOT EXISTS client_feedback (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    feedback_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    version_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, feedback_id)
);

CREATE TABLE IF NOT EXISTS brand_preferences (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    client_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, client_id)
);

CREATE TABLE IF NOT EXISTS creator_invitations (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    invitation_id TEXT NOT NULL,
    token TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, invitation_id),
    UNIQUE (tenant_id, token)
);

CREATE TABLE IF NOT EXISTS creator_submissions (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    submission_id TEXT NOT NULL,
    invitation_id TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, submission_id)
);

CREATE TABLE IF NOT EXISTS creator_commercial_profiles (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, creator_id)
);

CREATE TABLE IF NOT EXISTS distribution_briefs (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    brief_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, brief_id)
);

CREATE TABLE IF NOT EXISTS creator_brief_responses (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    response_id TEXT NOT NULL,
    brief_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, response_id)
);

CREATE TABLE IF NOT EXISTS campaign_projects (
    tenant_id TEXT NOT NULL DEFAULT 'default',
    campaign_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, campaign_id)
);

CREATE INDEX IF NOT EXISTS idx_creator_profiles_payload_gin ON creator_profiles USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_auth_users_payload_gin ON auth_users USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_clients_payload_gin ON clients USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_project_access_payload_gin ON project_access USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_campaign_projects_payload_gin ON campaign_projects USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_proposals_payload_gin ON proposals USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_distribution_briefs_payload_gin ON distribution_briefs USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_social_symbolic_reports_payload_gin ON social_symbolic_reports USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_signifier_tags_payload_gin ON signifier_tags USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_product_symbolic_profiles_payload_gin ON product_symbolic_profiles USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_content_narrative_assets_payload_gin ON content_narrative_assets USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_brand_creator_match_assets_payload_gin ON brand_creator_match_assets USING GIN (payload);
CREATE INDEX IF NOT EXISTS idx_feedback_corrections_payload_gin ON feedback_corrections USING GIN (payload);
