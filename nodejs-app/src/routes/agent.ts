import { Router } from 'express';
import { RealtimeXSDK } from '@realtimex/sdk';

export const createAgentRoutes = (sdk: RealtimeXSDK) => {
    const router = Router();

    // 1. Simple Chat (One-liner)
    // POST /api/agent/chat
    router.post('/chat', async (req, res) => {
        try {
            const { message, agent_name, workspace_slug } = req.body;
            if (!message) {
                return res.status(400).json({ error: 'Message is required' });
            }

            // Start a chat session, send message, and get response in one go!
            const { response } = await sdk.agent.startChat(message, { agent_name, workspace_slug });

            res.json({
                response: response.text,
                fullResponse: response
            });
        } catch (error: any) {
            console.error('Agent chat error:', error);
            res.status(500).json({ error: error.message });
        }
    });

    // 2. Session-based Chat
    // POST /api/agent/session
    router.post('/session', async (req, res) => {
        try {
            const { agent_name, workspace_slug } = req.body;
            const session = await sdk.agent.createSession({ agent_name, workspace_slug });
            res.json(session);
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    // POST /api/agent/session/:id/chat
    router.post('/session/:id/chat', async (req, res) => {
        try {
            const { id } = req.params;
            const { message } = req.body;

            const response = await sdk.agent.chat(id, message);
            res.json(response);
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    // DELETE /api/agent/session/:id
    router.delete('/session/:id', async (req, res) => {
        try {
            const { id } = req.params;
            await sdk.agent.closeSession(id);
            res.json({ success: true });
        } catch (error: any) {
            res.status(500).json({ error: error.message });
        }
    });

    // Session Streaming Chat
    // GET /api/agent/session/:id/stream
    router.get('/session/:id/stream', async (req, res) => {
        const { id } = req.params;
        const { message } = req.query;

        if (!message || typeof message !== 'string') {
            return res.status(400).json({ error: 'Message is required' });
        }

        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');

        try {
            for await (const event of sdk.agent.streamChat(id, message)) {
                res.write(`data: ${JSON.stringify(event)}\n\n`);
            }
            res.write('data: [DONE]\n\n');
            res.end();
        } catch (error: any) {
            console.error('Streaming error:', error);
            res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
            res.end();
        }
    });

    // 3. Streaming Chat
    // GET /api/agent/stream
    router.get('/stream', async (req, res) => {
        const { message } = req.query;

        if (!message || typeof message !== 'string') {
            return res.status(400).json({ error: 'Message is required' });
        }

        // Set headers for SSE
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');

        try {
            // Create a temporary session for this stream
            const session = await sdk.agent.createSession();

            // Stream the chat
            for await (const event of sdk.agent.streamChat(session.session_id, message)) {
                res.write(`data: ${JSON.stringify(event)}\n\n`);
            }

            // Cleanup
            await sdk.agent.closeSession(session.session_id);
            res.write('data: [DONE]\n\n');
            res.end();
        } catch (error: any) {
            console.error('Streaming error:', error);
            res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
            res.end();
        }
    });

    return router;
};
