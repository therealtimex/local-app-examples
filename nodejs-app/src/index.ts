/**
 * RealtimeX Local App Example - Node.js
 * 
 * Demonstrates all SDK capabilities organized into clear modules:
 * - Activities: CRUD operations on activities table
 * - API: Access to agents, workspaces, threads, tasks
 * - Webhook: Trigger AI agents
 * - LLM & Vectors: Chat, embeddings, and RAG patterns
 */

import express from 'express';
import path from 'path';
import { RealtimeXSDK } from '@realtimex/sdk';

// Import route modules
import { createActivitiesRoutes } from './routes/activities';
import { createApiRoutes } from './routes/api';
import { createWebhookRoutes } from './routes/webhook';
import { createLLMRoutes } from './routes/llm';

const app = express();

// Initialize SDK with all permissions
const sdk = new RealtimeXSDK({
    realtimex: {
        apiKey: process.env.RTX_API_KEY, // Added for Dev Mode testing
    },
    permissions: [
        // Activities
        'activities.read',
        'activities.write',
        // API
        'api.agents',
        'api.workspaces',
        'api.threads',
        'api.task',
        // Webhook
        'webhook.trigger',
        // LLM
        'llm.chat',
        'llm.embed',
        'llm.providers',
        // Vectors
        'vectors.read',
        'vectors.write',
    ],
});

const startServer = async () => {
    const PORT = await sdk.port.getPort();

    // Middleware
    app.use(express.json());
    app.use(express.static(path.join(__dirname, '../public')));

    // ========================
    // Mount Route Modules
    // ========================

    // Activities CRUD: /api/activities/*
    app.use('/api/activities', createActivitiesRoutes(sdk));

    // Platform API: /api/agents, /api/workspaces, /api/tasks, /api/info
    app.use('/api', createApiRoutes(sdk));

    // Webhook triggers: /api/webhook/trigger, /api/webhook/schedule
    app.use('/api/webhook', createWebhookRoutes(sdk));

    // LLM & Vectors: /api/llm/*
    app.use('/api/llm', createLLMRoutes(sdk));

    // ========================
    // Health Check
    app.get('/health', (req, res) => {
        res.json({ status: 'ok', timestamp: new Date().toISOString() });
    });

    // SDK Ping Test
    // app.get('/api/ping', async (req, res) => {
    //     try {
    //         const result = await sdk.ping();
    //         res.json(result);
    //     } catch (error: any) {
    //         res.status(500).json({ success: false, error: error.message });
    //     }
    // });
    const result = await sdk.ping();
    console.log(result);
    // Start server
    app.listen(PORT, () => {
        console.log(`\n🚀 RealtimeX Node.js Demo running at http://localhost:${PORT}`);
        console.log(`   App ID: ${process.env.RTX_APP_ID || 'Not set'}`);
        console.log(`   App Name: ${process.env.RTX_APP_NAME || 'Not set'}\n`);
        console.log('📚 Available endpoints:');
        console.log('   Activities:  GET/POST/PATCH/DELETE /api/activities');
        console.log('   Agents:      GET /api/agents');
        console.log('   Workspaces:  GET /api/workspaces');
        console.log('   Threads:     GET /api/workspaces/:slug/threads');
        console.log('   Tasks:       GET /api/tasks/:uuid');
        console.log('   Webhook:     POST /api/webhook/trigger');
        console.log('   Webhook:     POST /api/webhook/schedule');
        console.log('   LLM Chat:    POST /api/llm/chat');
        console.log('   LLM Stream:  POST /api/llm/chat/stream');
        console.log('   Embeddings:  POST /api/llm/embed');
        console.log('   Vectors:     POST /api/llm/vectors/*');
        console.log('   RAG Search:  POST /api/llm/search');
    });
};

// Run
startServer().catch(console.error);
