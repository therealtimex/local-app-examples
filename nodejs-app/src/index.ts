import express, { Request, Response } from 'express';
import path from 'path';
import { RealtimeXSDK, Activity, Agent, Workspace, Thread } from '@realtimex/sdk';

const app = express();
const PORT = process.env.PORT || 8080;

// Initialize SDK (Auto-detects RTX_APP_ID from environment)
const sdk = new RealtimeXSDK();

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// ========================
// API ROUTES
// ========================

// GET /api/activities - List activities
app.get('/api/activities', async (req: Request, res: Response) => {
    try {
        const activities = await sdk.activities.list({ limit: 20 });
        res.json({ success: true, activities });
    } catch (error: any) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// POST /api/activities - Create activity
app.post('/api/activities', async (req: Request, res: Response) => {
    try {
        const { raw_data } = req.body;
        const activity = await sdk.activities.insert(raw_data);
        res.json({ success: true, activity });
    } catch (error: any) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// PATCH /api/activities/:id - Update activity
app.patch('/api/activities/:id', async (req: Request, res: Response) => {
    try {
        const { id } = req.params;
        const updates = req.body;
        const activity = await sdk.activities.update(id, updates);
        res.json({ success: true, activity });
    } catch (error: any) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// DELETE /api/activities/:id - Delete activity
app.delete('/api/activities/:id', async (req: Request, res: Response) => {
    try {
        const { id } = req.params;
        await sdk.activities.delete(id);
        res.json({ success: true });
    } catch (error: any) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// GET /api/agents - List agents
app.get('/api/agents', async (req: Request, res: Response) => {
    try {
        const agents = await sdk.api.getAgents();
        res.json({ success: true, agents });
    } catch (error: any) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// GET /api/workspaces - List workspaces
app.get('/api/workspaces', async (req: Request, res: Response) => {
    try {
        const workspaces = await sdk.api.getWorkspaces();
        res.json({ success: true, workspaces });
    } catch (error: any) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// GET /api/workspaces/:slug/threads - List threads for workspace
app.get('/api/workspaces/:slug/threads', async (req: Request, res: Response) => {
    try {
        const { slug } = req.params;
        const threads = await sdk.api.getThreads(slug);
        res.json({ success: true, threads });
    } catch (error: any) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// POST /api/trigger - Trigger agent
app.post('/api/trigger', async (req: Request, res: Response) => {
    try {
        const { raw_data, agent_name, workspace_slug, thread_slug, prompt } = req.body;
        const result = await sdk.webhook.triggerAgent({
            raw_data,
            auto_run: true,
            agent_name,
            workspace_slug,
            thread_slug: thread_slug || 'create_new',
            prompt: prompt || 'Process this item',
        });
        res.json(result);
    } catch (error: any) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// GET /api/info - Get app info
app.get('/api/info', (req: Request, res: Response) => {
    res.json({
        app_name: process.env.RTX_APP_NAME || 'Node.js Demo',
        app_id: process.env.RTX_APP_ID || 'Not set',
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 RealtimeX Node.js Demo running at http://localhost:${PORT}`);
    console.log(`   App ID: ${process.env.RTX_APP_ID || 'Not set'}`);
});
