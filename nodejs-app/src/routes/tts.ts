/**
 * TTS Routes
 * Demonstrates Text-to-Speech capabilities via SDK
 */

import { Router } from 'express';
import { RealtimeXSDK } from '@realtimex/sdk';

export function createTTSRoutes(sdk: RealtimeXSDK) {
    const router = Router();

    /**
     * GET /api/tts/providers
     * List available TTS providers
     */
    router.get('/providers', async (req, res) => {
        try {
            const providers = await sdk.tts.listProviders();
            res.json({ success: true, providers });
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    /**
     * POST /api/tts/speak
     * Generate speech from text (returns audio buffer)
     */
    router.post('/speak', async (req, res) => {
        try {
            const { text, voice, model, speed, provider } = req.body;

            if (!text) {
                return res.status(400).json({ success: false, error: 'Text is required' });
            }

            const audioBuffer = await sdk.tts.speak(text, { voice, model, speed, provider });

            // Set appropriate headers for audio
            res.setHeader('Content-Type', 'audio/mpeg');
            res.setHeader('Content-Length', audioBuffer.byteLength);
            res.send(Buffer.from(audioBuffer));
        } catch (error: any) {
            res.status(500).json({ success: false, error: error.message });
        }
    });

    /**
     * POST /api/tts/speak/stream
     * Generate speech from text (SSE streaming with decoded audio chunks)
     * Uses SDK speakStream which returns decoded ArrayBuffer chunks
     */
    router.post('/speak/stream', async (req, res) => {
        try {
            const { text, provider, voice, speed, language, num_inference_steps } = req.body;

            if (!text) {
                return res.status(400).json({ success: false, error: 'Text is required' });
            }

            // Set up SSE headers
            res.setHeader('Content-Type', 'text/event-stream');
            res.setHeader('Cache-Control', 'no-cache');
            res.setHeader('Connection', 'keep-alive');

            // SDK speakStream now yields decoded chunks with ArrayBuffer audio
            let chunksReceived = 0;
            for await (const chunk of sdk.tts.speakStream(text, {
                provider,
                voice,
                speed,
                language,
                num_inference_steps
            }) as AsyncGenerator<{ index: number; total: number; audio: ArrayBuffer; mimeType: string }>) {
                chunksReceived++;
                console.log(`[TTS Proxy] Received chunk ${chunk.index + 1}/${chunk.total}`);

                // Convert ArrayBuffer back to base64 for SSE transport
                const base64Audio = Buffer.from(chunk.audio).toString('base64');
                res.write(`event: chunk\ndata: ${JSON.stringify({
                    index: chunk.index,
                    total: chunk.total,
                    audio: base64Audio,
                    mimeType: chunk.mimeType,
                })}\n\n`);
            }
            console.log(`[TTS Proxy] Finished streaming, total chunks: ${chunksReceived}`);

            res.write(`event: done\ndata: ${JSON.stringify({ success: true, total: chunksReceived })}\n\n`);
            res.end();
        } catch (error: any) {
            console.error('[TTS Proxy] Stream error:', error);
            if (!res.headersSent) {
                return res.status(500).json({ success: false, error: error.message });
            }
            res.write(`event: error\ndata: ${JSON.stringify({ error: error.message })}\n\n`);
            res.end();
        }
    });

    /**
     * @deprecated Use /speak/stream instead - kept for backwards compatibility
     * Duplicates the /speak/stream logic for old clients
     */
    router.post('/speak/stream/chunked', async (req, res) => {
        const { text, provider, voice, speed, language, num_inference_steps } = req.body;
        if (!text) {
            return res.status(400).json({ success: false, error: 'Text is required' });
        }
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        try {
            let chunksReceived = 0;
            for await (const chunk of sdk.tts.speakStream(text, {
                provider, voice, speed, language, num_inference_steps
            }) as AsyncGenerator<{ index: number; total: number; audio: ArrayBuffer; mimeType: string }>) {
                chunksReceived++;
                const base64Audio = Buffer.from(chunk.audio).toString('base64');
                res.write(`event: chunk\ndata: ${JSON.stringify({
                    index: chunk.index, total: chunk.total, audio: base64Audio, mimeType: chunk.mimeType
                })}\n\n`);
            }
            res.write(`event: done\ndata: ${JSON.stringify({ success: true, total: chunksReceived })}\n\n`);
            res.end();
        } catch (error: any) {
            res.write(`event: error\ndata: ${JSON.stringify({ error: error.message })}\n\n`);
            res.end();
        }
    });


    return router;
}
