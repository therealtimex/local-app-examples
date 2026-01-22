/**
 * Webhook Routes
 * 
 * Trigger AI agents for automated or manual processing.
 * Requires: webhook.trigger permission
 */

import { Router, Request, Response } from 'express';
import { RealtimeXSDK } from '@realtimex/sdk';

export function createWebhookRoutes(sdk: RealtimeXSDK): Router {
    const router = Router();

    // POST /trigger - Trigger agent with auto_run
    router.post('/trigger', async (req: Request, res: Response) => {
        try {
            const {
                raw_data,
                agent_name,
                workspace_slug,
                thread_slug,
                prompt,
                auto_run = true
            } = req.body;

            const result = await sdk.webhook.triggerAgent({
                raw_data,
                auto_run,
                agent_name: auto_run ? agent_name : undefined,
                workspace_slug: auto_run ? workspace_slug : undefined,
                thread_slug: auto_run && thread_slug ? thread_slug : undefined,
                prompt: prompt || 'Process this item',
            });

            res.json(result);
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // POST /schedule - Create calendar event for manual review
    router.post('/schedule', async (req: Request, res: Response) => {
        try {
            const { raw_data, prompt } = req.body;

            const result = await sdk.webhook.triggerAgent({
                raw_data,
                auto_run: false,
                prompt: prompt || 'Review this item',
            });

            res.json(result);
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    return router;
}
