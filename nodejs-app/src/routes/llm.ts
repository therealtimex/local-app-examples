/**
 * LLM & Vector Store Routes
 * 
 * AI capabilities: chat, embeddings, and vector storage for RAG patterns.
 * Requires: llm.chat, llm.embed, llm.providers, vectors.read, vectors.write permissions
 */

import { Router, Request, Response } from 'express';
import { RealtimeXSDK, LLMPermissionError, LLMProviderError } from '@realtimex/sdk';

export function createLLMRoutes(sdk: RealtimeXSDK): Router {
    const router = Router();

    // ========================
    // LLM Endpoints
    // ========================

    // GET /providers - List available LLM and embedding providers
    router.get('/providers', async (req: Request, res: Response) => {
        try {
            const providers = await sdk.llm.getProviders();
            res.json(providers);
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // POST /chat - Sync chat completion
    router.post('/chat', async (req: Request, res: Response) => {
        try {
            const { messages, model, provider, temperature, max_tokens } = req.body;

            if (!messages || !Array.isArray(messages)) {
                return res.status(400).json({
                    success: false,
                    error: 'messages array is required'
                });
            }

            const response = await sdk.llm.chat(messages, {
                model,
                provider,
                temperature,
                max_tokens,
            });

            res.json(response);
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // POST /chat/stream - Streaming chat completion (SSE)
    router.post('/chat/stream', async (req: Request, res: Response) => {
        try {
            const { messages, model, provider, temperature, max_tokens } = req.body;

            if (!messages || !Array.isArray(messages)) {
                return res.status(400).json({
                    success: false,
                    error: 'messages array is required'
                });
            }

            // Set up SSE headers
            res.setHeader('Content-Type', 'text/event-stream');
            res.setHeader('Cache-Control', 'no-cache');
            res.setHeader('Connection', 'keep-alive');

            // Stream chunks to client
            for await (const chunk of sdk.llm.chatStream(messages, {
                model,
                provider,
                temperature,
                max_tokens,
            })) {
                res.write(`data: ${JSON.stringify(chunk)}\n\n`);
            }

            res.write('data: [DONE]\n\n');
            res.end();
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // POST /embed - Generate embeddings
    router.post('/embed', async (req: Request, res: Response) => {
        try {
            const { input, provider, model } = req.body;

            if (!input) {
                return res.status(400).json({
                    success: false,
                    error: 'input text is required'
                });
            }

            const response = await sdk.llm.embed(input, { provider, model });
            res.json(response);
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // ========================
    // Vector Store Endpoints
    // ========================

    // POST /vectors/upsert - Store vectors
    router.post('/vectors/upsert', async (req: Request, res: Response) => {
        try {
            const { vectors, workspaceId } = req.body;

            if (!vectors || !Array.isArray(vectors)) {
                return res.status(400).json({
                    success: false,
                    error: 'vectors array is required'
                });
            }

            const response = await sdk.llm.vectors.upsert(vectors, { workspaceId });
            res.json(response);
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // POST /vectors/query - Query similar vectors
    router.post('/vectors/query', async (req: Request, res: Response) => {
        try {
            const { vector, topK, filter, workspaceId } = req.body;

            if (!vector || !Array.isArray(vector)) {
                return res.status(400).json({
                    success: false,
                    error: 'vector array is required'
                });
            }

            const response = await sdk.llm.vectors.query(vector, {
                topK: topK || 5,
                filter,
                workspaceId,
            });
            res.json(response);
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // POST /vectors/delete - Delete vectors
    router.post('/vectors/delete', async (req: Request, res: Response) => {
        try {
            const { deleteAll, workspaceId } = req.body;

            if (!deleteAll) {
                return res.status(400).json({
                    success: false,
                    error: 'deleteAll: true is required (granular delete not yet supported)'
                });
            }

            const response = await sdk.llm.vectors.delete({ deleteAll, workspaceId });
            res.json(response);
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // GET /vectors/workspaces - List all unique workspaces (namespaces)
    router.get('/vectors/workspaces', async (req: Request, res: Response) => {
        try {
            const response = await sdk.llm.vectors.listWorkspaces();
            res.json(response);
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // ========================
    // RAG Helper Endpoints
    // ========================

    // POST /embed-and-store - Embed texts and store as vectors in one call
    router.post('/embed-and-store', async (req: Request, res: Response) => {
        try {
            const { texts, documentId, document_id, workspaceId, idPrefix, provider, model } = req.body;

            if (!texts || !Array.isArray(texts)) {
                return res.status(400).json({
                    success: false,
                    error: 'texts array is required'
                });
            }

            const response = await sdk.llm.embedAndStore({
                texts,
                documentId: documentId || document_id,
                workspaceId,
                idPrefix,
                provider,
                model
            });
            res.json(response);
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    // POST /search - Semantic search by text query
    router.post('/search', async (req: Request, res: Response) => {
        try {
            const { query, topK, workspaceId, documentId, document_id, provider, model } = req.body;

            if (!query) {
                return res.status(400).json({
                    success: false,
                    error: 'query text is required'
                });
            }

            const results = await sdk.llm.search(query, {
                topK: topK || 5,
                filter: (documentId || document_id) ? { documentId: documentId || document_id } : undefined,
                workspaceId,
                provider,
                model
            });

            res.json({ success: true, results });
        } catch (error: any) {
            handleLLMError(error, res);
        }
    });

    return router;
}

// Error handler for LLM-specific errors
function handleLLMError(error: any, res: Response) {
    if (error instanceof LLMPermissionError) {
        return res.status(403).json({
            success: false,
            error: `Permission required: ${error.permission}`,
            code: error.code,
        });
    }

    if (error instanceof LLMProviderError) {
        return res.status(502).json({
            success: false,
            error: error.message,
            code: error.code,
        });
    }

    return res.status(500).json({
        success: false,
        error: error.message,
    });
}
