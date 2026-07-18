-- Migration: add goal_id to tasks table (links Executive Brain tasks to goals)
-- Run this in the Supabase SQL Editor (or via psql with the service role).

-- 1. Add the column (nullable so existing rows are unaffected)
ALTER TABLE public.tasks
    ADD COLUMN IF NOT EXISTS goal_id uuid;

-- 2. Foreign key to goals (if the goals table exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'goals'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'tasks_goal_id_fkey'
        ) THEN
            ALTER TABLE public.tasks
                ADD CONSTRAINT tasks_goal_id_fkey
                FOREIGN KEY (goal_id) REFERENCES public.goals(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- 3. Index for fast goal→tasks lookups
CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON public.tasks(goal_id);

-- 4. Refresh PostgREST schema cache so the REST API sees the new column
NOTIFY pgrst, 'reload schema';
