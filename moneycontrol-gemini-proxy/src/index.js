/**
 * Gemini API proxy for Cloudflare Workers.
 *
 * Secrets (set in Cloudflare dashboard):
 *   GEMINI_API_KEY      — Google AI Studio / Generative Language API key
 *   GEMINI_PROXY_KEY    — optional bearer token clients must send
 */
const GOOGLE_API_BASE = "https://generativelanguage.googleapis.com";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
};

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (request.method !== "GET" && request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405, headers: CORS_HEADERS });
    }

    if (env.GEMINI_PROXY_KEY) {
      const auth = request.headers.get("Authorization") ?? "";
      const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
      if (token !== env.GEMINI_PROXY_KEY) {
        return new Response("Unauthorized", { status: 401, headers: CORS_HEADERS });
      }
    }

    if (!env.GEMINI_API_KEY) {
      return new Response("Gemini API key not configured", {
        status: 503,
        headers: CORS_HEADERS,
      });
    }

    const url = new URL(request.url);
    const pathAndQuery = `${url.pathname}${url.search}`;
    const separator = url.search ? "&" : "?";
    const targetUrl = `${GOOGLE_API_BASE}${pathAndQuery}${separator}key=${env.GEMINI_API_KEY}`;

    const forwardHeaders = new Headers();
    const contentType = request.headers.get("Content-Type");
    if (contentType) {
      forwardHeaders.set("Content-Type", contentType);
    }

    const upstream = await fetch(targetUrl, {
      method: request.method,
      headers: forwardHeaders,
      body: request.method === "POST" ? request.body : undefined,
    });

    const responseHeaders = new Headers(upstream.headers);
    for (const [key, value] of Object.entries(CORS_HEADERS)) {
      responseHeaders.set(key, value);
    }

    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  },
};
