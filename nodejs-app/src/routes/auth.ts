/**
 * Auth Routes — Supabase Authentication & SDK Token Sync
 * 
 * Demonstrates the full auth flow:
 * 1. GET  /api/auth/config      — Fetch Supabase config from Main App via SDK
 * 2. POST /api/auth/login       — Sign in to Supabase and sync token to Main App
 * 3. POST /api/auth/sync-token  — Manually sync existing Supabase token
 * 4. GET  /api/auth/status       — Check current auth status
 * 
 * Requires: database.config permission
 */

import { Router, Request, Response } from 'express';
import { RealtimeXSDK, DatabaseConfig } from '@realtimex/sdk';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Module-level state
let supabaseClient: SupabaseClient | null = null;
let currentConfig: DatabaseConfig | null = null;
let currentUser: any = null;

export function createAuthRoutes(sdk: RealtimeXSDK): Router {
    const router = Router();

    /**
     * GET /api/auth/config
     * Fetch Supabase database configuration from Main App.
     */
    router.get('/config', async (req: Request, res: Response) => {
        try {
            const config = await sdk.database.getConfig();
            currentConfig = config;

            // Create Supabase client with fetched config
            supabaseClient = createClient(config.url, config.anonKey, {
                auth: { persistSession: false, autoRefreshToken: false },
            });

            res.json({
                success: true,
                config: {
                    url: config.url,
                    anonKey: config.anonKey ? `${config.anonKey.substring(0, 20)}...` : null,
                    mode: config.mode,
                    tables: config.tables,
                },
                message: 'Supabase config loaded. Client created.',
            });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    /**
     * POST /api/auth/signup
     * Create a new Supabase user account.
     * Body: { email: string, password: string }
     */
    router.post('/signup', async (req: Request, res: Response) => {
        try {
            // Ensure config is loaded
            if (!supabaseClient || !currentConfig) {
                const config = await sdk.database.getConfig();
                currentConfig = config;
                supabaseClient = createClient(config.url, config.anonKey, {
                    auth: { persistSession: false, autoRefreshToken: false },
                });
            }

            const { email, password } = req.body;
            if (!email || !password) {
                return res.status(400).json({ success: false, error: 'email and password are required' });
            }
            if (password.length < 6) {
                return res.status(400).json({ success: false, error: 'password must be at least 6 characters' });
            }

            const { data, error } = await supabaseClient.auth.signUp({ email, password });

            if (error) {
                return res.status(400).json({ success: false, error: error.message });
            }

            res.json({
                success: true,
                user: { id: data.user?.id, email: data.user?.email },
                message: '✅ Account created! You can now login.',
            });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    /**
     * POST /api/auth/login
     * Sign in to Supabase with email/password, then sync token to Main App.
     * Body: { email: string, password: string }
     */
    router.post('/login', async (req: Request, res: Response) => {
        try {
            // Step 1: Ensure config is loaded
            if (!supabaseClient || !currentConfig) {
                // Auto-load config
                const config = await sdk.database.getConfig();
                currentConfig = config;
                supabaseClient = createClient(config.url, config.anonKey, {
                    auth: { persistSession: false, autoRefreshToken: false },
                });
            }

            const { email, password } = req.body;
            if (!email || !password) {
                return res.status(400).json({
                    success: false,
                    error: 'email and password are required',
                });
            }

            // Step 2: Sign in to Supabase
            const { data, error } = await supabaseClient.auth.signInWithPassword({
                email,
                password,
            });

            if (error) {
                return res.status(401).json({
                    success: false,
                    error: `Supabase auth failed: ${error.message}`,
                });
            }

            const accessToken = data.session?.access_token;
            if (!accessToken) {
                return res.status(500).json({
                    success: false,
                    error: 'No access token received from Supabase',
                });
            }

            currentUser = data.user;

            // Step 3: Sync Supabase token to Main App (for RLS bypass)
            const syncResult = await sdk.auth.syncSupabaseToken(accessToken);

            res.json({
                success: true,
                user: {
                    id: data.user?.id,
                    email: data.user?.email,
                },
                tokenSynced: syncResult.success,
                message: syncResult.success
                    ? '✅ Logged in & token synced. Activities will now bypass RLS.'
                    : '⚠️ Logged in but token sync failed.',
            });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    /**
     * POST /api/auth/sync-token
     * Manually sync an existing Supabase token.
     * Body: { token: string }
     */
    router.post('/sync-token', async (req: Request, res: Response) => {
        try {
            const { token } = req.body;
            if (!token) {
                return res.status(400).json({
                    success: false,
                    error: 'token is required',
                });
            }

            const result = await sdk.auth.syncSupabaseToken(token);
            res.json({
                ...result,
                message: '✅ Supabase token synced to Main App.',
            });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    /**
     * GET /api/auth/status
     * Check current auth state.
     */
    router.get('/status', async (req: Request, res: Response) => {
        try {
            const keycloakToken = await sdk.auth.getAccessToken();

            res.json({
                success: true,
                supabase: {
                    configLoaded: !!currentConfig,
                    clientReady: !!supabaseClient,
                    userLoggedIn: !!currentUser,
                    userEmail: currentUser?.email || null,
                },
                keycloak: {
                    hasToken: keycloakToken?.hasToken || false,
                    syncedAt: keycloakToken?.syncedAt || null,
                },
            });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    return router;
}
