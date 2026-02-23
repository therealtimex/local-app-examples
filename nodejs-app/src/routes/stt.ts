
import { Router } from 'express';
import { RealtimeXSDK } from '@realtimex/sdk';

export const createSTTRoutes = (sdk: RealtimeXSDK) => {
    const router = Router();

    // POST /api/stt/listen
    // Listen to microphone and transcribe (frontend trigger via SDK)
    router.post('/listen', async (req, res) => {
        try {
            const { provider = 'native', language, timeout, model } = req.body;
            console.log(`[STT] Requesting transcription... Provider: ${provider}, Model: ${model || 'default'}`);

            const result = await sdk.stt.listen({
                provider,
                language,
                timeout,
                model
            });

            console.log('[STT] Result:', result);
            res.json(result);
        } catch (error: any) {
            console.error('[STT] Error:', error.message);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });

    // GET /api/stt/providers
    // List available providers and models via SDK
    router.get('/providers', async (req, res) => {
        try {
            const result = await sdk.stt.listProviders();
            res.json({ success: true, providers: result });
        } catch (error: any) {
            console.error('[STT] Providers Error:', error.message);
            res.status(500).json({ success: false, error: error.message });
        }
    });

    return router;
};
