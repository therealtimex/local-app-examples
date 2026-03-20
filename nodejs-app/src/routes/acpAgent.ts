/**
 * ACP Agent Routes — CLI-based agent sessions via SDK
 *
 * Endpoints:
 *   GET    /api/acp-agent/agents              - List installed CLI agents
 *   POST   /api/acp-agent/session             - Create session
 *   POST   /api/acp-agent/session/close       - Close session
 *   POST   /api/acp-agent/chat                - Sync chat
 *   POST   /api/acp-agent/chat/stream         - Streaming chat (SSE)
 *   POST   /api/acp-agent/permission          - Resolve permission request
 */

import { Router } from "express";
import { RealtimeXSDK } from "@realtimex/sdk";

export const createAcpAgentRoutes = (sdk: RealtimeXSDK) => {
  const router = Router();

  // List installed CLI agents (with models when requested)
  router.get("/agents", async (req, res) => {
    try {
      const includeModels = req.query.includeModels === "true";
      const agents = await sdk.acpAgent.listAgents({ includeModels });
      res.json({ agents: agents.filter((a) => a.installed) });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Create session
  router.post("/session", async (req, res) => {
    try {
      const { agent_id, cwd, model, approvalPolicy } = req.body;
      if (!agent_id) return res.status(400).json({ error: "agent_id required" });
      const session = await sdk.acpAgent.createSession({
        agent_id,
        cwd: cwd || process.cwd(),
        model: model || undefined,
        approvalPolicy: approvalPolicy || undefined,
      });
      res.json({ session });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Close session
  router.post("/session/close", async (req, res) => {
    try {
      const { session_key } = req.body;
      if (!session_key) return res.status(400).json({ error: "session_key required" });
      await sdk.acpAgent.closeSession(session_key);
      res.json({ success: true });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Sync chat
  router.post("/chat", async (req, res) => {
    try {
      const { session_key, message, attachments } = req.body;
      if (!session_key || !message)
        return res.status(400).json({ error: "session_key and message required" });
      const response = await sdk.acpAgent.chat(session_key, message, attachments);
      res.json({ response });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Streaming chat (SSE proxy — re-streams SDK events to browser)
  router.post("/chat/stream", async (req, res) => {
    const { session_key, message, attachments } = req.body;
    if (!session_key || !message) {
      return res.status(400).json({ error: "session_key and message required" });
    }

    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.flushHeaders();

    try {
      for await (const event of sdk.acpAgent.streamChat(session_key, message, attachments)) {
        res.write(`data: ${JSON.stringify(event)}\n\n`);
      }
      res.write(`data: ${JSON.stringify({ type: "stream_end" })}\n\n`);
    } catch (err: any) {
      res.write(`data: ${JSON.stringify({ type: "error", data: { message: err.message } })}\n\n`);
    } finally {
      res.end();
    }
  });

  // Resolve a permission request
  router.post("/permission", async (req, res) => {
    try {
      const { session_key, requestId, optionId } = req.body;
      if (!session_key || !requestId || !optionId)
        return res.status(400).json({ error: "session_key, requestId, and optionId required" });
      const result = await sdk.acpAgent.resolvePermission(session_key, {
        requestId,
        optionId,
      });
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  return router;
};
