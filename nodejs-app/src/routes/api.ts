/**
 * API Routes
 * 
 * Access to RealtimeX platform data (agents, workspaces, threads, tasks).
 * Requires: api.agents, api.workspaces, api.threads, api.task permissions
 */

import { Router, Request, Response } from 'express';
import { RealtimeXSDK } from '@realtimex/sdk';

export function createApiRoutes(sdk: RealtimeXSDK): Router {
    const router = Router();

    // GET /agents - List agents
    router.get('/agents', async (req: Request, res: Response) => {
        try {
            const agents = await sdk.api.getAgents();
            res.json({ success: true, agents });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // GET /workspaces - List workspaces
    router.get('/workspaces', async (req: Request, res: Response) => {
        try {
            const workspaces = await sdk.api.getWorkspaces();
            res.json({ success: true, workspaces });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // GET /workspaces/:slug/threads - List threads for workspace
    router.get('/workspaces/:slug/threads', async (req: Request, res: Response) => {
        try {
            const { slug } = req.params;
            const threads = await sdk.api.getThreads(slug);
            res.json({ success: true, threads });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // GET /tasks/:uuid - Get task status
    router.get('/tasks/:uuid', async (req: Request, res: Response) => {
        try {
            const { uuid } = req.params;
            const task = await sdk.api.getTask(uuid);
            res.json({ success: true, task });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // GET /info - App information
    router.get('/info', (req: Request, res: Response) => {
        res.json({
            app_name: process.env.RTX_APP_NAME || 'Node.js Demo',
            app_id: process.env.RTX_APP_ID || 'Not set',
            sdk_version: '1.1.0',
        });
    });

    return router;
}
