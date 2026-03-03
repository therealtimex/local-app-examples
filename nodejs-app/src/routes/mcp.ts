import { Router } from 'express';
import { RealtimeXSDK } from '@realtimex/sdk';

export const createMCPRoutes = (sdk: RealtimeXSDK) => {
    const router = Router();

    /**
     * GET /api/mcp/servers
     * List available MCP servers
     */
    router.get('/servers', async (req, res) => {
        try {
            const provider = (req.query.provider as string) || 'all';
            const servers = await sdk.mcp.getServers(provider as any);
            res.json({ success: true, servers });
        } catch (error: any) {
            console.error('Failed to fetch MCP servers:', error.message);
            res.status(500).json({ success: false, error: error.message });
        }
    });

    /**
     * GET /api/mcp/servers/:serverName/tools
     * List tools for a specific MCP server
     */
    router.get('/servers/:serverName/tools', async (req, res) => {
        try {
            const { serverName } = req.params;
            const provider = (req.query.provider as 'local' | 'remote') || 'local';
            const tools = await sdk.mcp.getTools(serverName, provider);
            res.json({ success: true, tools });
        } catch (error: any) {
            console.error(`Failed to fetch tools for ${req.params.serverName}:`, error.message);
            res.status(500).json({ success: false, error: error.message });
        }
    });

    /**
     * POST /api/mcp/servers/:serverName/tools/:toolName/execute
     * Execute a tool on an MCP server
     */
    router.post('/servers/:serverName/tools/:toolName/execute', async (req, res) => {
        try {
            const { serverName, toolName } = req.params;
            const provider = (req.query.provider as 'local' | 'remote') || 'local';
            const { arguments: toolArgs, ...rest } = req.body || {};

            const result = await sdk.mcp.executeTool(serverName, toolName, toolArgs || rest, provider);
            res.json({ success: true, result });
        } catch (error: any) {
            console.error(`Failed to execute MCP tool ${req.params.toolName}:`, error.message);
            res.status(500).json({ success: false, error: error.message });
        }
    });

    return router;
};
