-- Migration: create skills table for the Executive Brain's skill library.
-- Stores imported Hermes skills + auto-learned workflows as searchable rows.
-- Applied against the live Supabase project (port 5432 direct connection).

CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brain_id UUID,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    body TEXT,
    source TEXT NOT NULL DEFAULT 'hermes',  -- 'hermes' | 'auto-learn'
    learned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_skills_brain_id ON skills (brain_id);
CREATE INDEX IF NOT EXISTS idx_skills_source ON skills (source);

-- Reload PostgREST schema cache so the REST API sees the new table.
NOTIFY pgrst, 'reload schema';
