/**
 * Activities Routes
 * 
 * CRUD operations for the activities table.
 * Requires: activities.read, activities.write permissions
 */

import { Router, Request, Response } from 'express';
import { RealtimeXSDK } from '@realtimex/sdk';

export function createActivitiesRoutes(sdk: RealtimeXSDK): Router {
    const router = Router();

    // GET /activities - List activities
    router.get('/', async (req: Request, res: Response) => {
        try {
            const limit = parseInt(req.query.limit as string) || 20;
            const status = req.query.status as string;
            const activities = await sdk.activities.list({ limit, status });
            res.json({ success: true, activities });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // GET /activities/:id - Get single activity
    router.get('/:id', async (req: Request, res: Response) => {
        try {
            const { id } = req.params;
            const activity = await sdk.activities.get(id);
            res.json({ success: true, activity });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // POST /activities - Create activity
    router.post('/', async (req: Request, res: Response) => {
        try {
            const { raw_data } = req.body;
            const activity = await sdk.activities.insert(raw_data);
            res.json({ success: true, activity });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // PATCH /activities/:id - Update activity
    router.patch('/:id', async (req: Request, res: Response) => {
        try {
            const { id } = req.params;
            const updates = req.body;
            const activity = await sdk.activities.update(id, updates);
            res.json({ success: true, activity });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    // DELETE /activities/:id - Delete activity
    router.delete('/:id', async (req: Request, res: Response) => {
        try {
            const { id } = req.params;
            await sdk.activities.delete(id);
            res.json({ success: true });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    return router;
}
