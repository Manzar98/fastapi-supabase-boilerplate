-- Create audit_logs table for tracking user actions
-- Run this migration in your Supabase SQL editor

-- Create the audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    resource_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id);

-- Enable Row Level Security (RLS)
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Policy 1: Users can view their own audit logs
CREATE POLICY "Users can view own audit logs" ON audit_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Policy 2: Service role can insert audit logs (for our application)
CREATE POLICY "Service role can insert audit logs" ON audit_logs
    FOR INSERT WITH CHECK (true);

-- Policy 3: Service role can view all audit logs (for admin purposes)
CREATE POLICY "Service role can view all audit logs" ON audit_logs
    FOR SELECT USING (true);

-- Policy 4: Service role can update audit logs (for corrections)
CREATE POLICY "Service role can update audit logs" ON audit_logs
    FOR UPDATE USING (true);

-- Add comments for documentation
COMMENT ON TABLE audit_logs IS 'Audit trail for tracking user actions and system events';
COMMENT ON COLUMN audit_logs.user_id IS 'ID of the user who performed the action (NULL for anonymous actions)';
COMMENT ON COLUMN audit_logs.action IS 'Type of action performed (e.g., LOGIN, LOGOUT, CREATE, UPDATE, DELETE)';
COMMENT ON COLUMN audit_logs.resource IS 'Resource type affected (e.g., user, auth, profile)';
COMMENT ON COLUMN audit_logs.resource_id IS 'ID of the specific resource affected (if applicable)';
COMMENT ON COLUMN audit_logs.ip_address IS 'IP address of the client making the request';
COMMENT ON COLUMN audit_logs.user_agent IS 'User agent string from the HTTP request';
COMMENT ON COLUMN audit_logs.metadata IS 'Additional context data (request body, response status, etc.)';
COMMENT ON COLUMN audit_logs.created_at IS 'Timestamp when the action was performed';
