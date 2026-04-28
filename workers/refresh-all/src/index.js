// Cloudflare Worker — proxy para disparar o workflow refresh-all.yml.
// O dashboard (https://vitormonofloor.github.io/Monofloor_Files/) chama POST aqui.
// O Worker guarda o GH_TOKEN como secret (não exposto no client) e dispara via API GitHub.

const ALLOWED_ORIGINS = [
  'https://vitormonofloor.github.io',
  'http://localhost:8000',
  'http://127.0.0.1:8000',
];

const REPO = 'vitormonofloor/Monofloor_Files';
const WORKFLOW_FILE = 'refresh-all.yml';
const REF = 'main';

// Rate limit: 1 dispatch a cada 5 min por IP (best-effort, in-memory por isolate).
// Não é criptograficamente perfeito, mas evita spam casual.
const RATE_LIMIT_MS = 5 * 60 * 1000;
const recentDispatches = new Map(); // ip -> timestamp

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders(request) });
    }

    if (request.method === 'GET') {
      // Health check público (não dispara nada)
      return jsonResponse({ ok: true, service: 'monofloor-refresh', uptime: Date.now() }, 200, request);
    }

    if (request.method !== 'POST') {
      return jsonResponse({ ok: false, error: 'Method not allowed' }, 405, request);
    }

    const origin = request.headers.get('Origin');
    if (!ALLOWED_ORIGINS.includes(origin)) {
      return jsonResponse({ ok: false, error: 'Origem não autorizada' }, 403, request);
    }

    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const now = Date.now();
    const last = recentDispatches.get(ip);
    if (last && (now - last) < RATE_LIMIT_MS) {
      const waitSec = Math.ceil((RATE_LIMIT_MS - (now - last)) / 1000);
      return jsonResponse({
        ok: false,
        error: `Aguarde ${waitSec}s antes de disparar de novo.`,
        retry_after: waitSec,
      }, 429, request);
    }

    if (!env.GH_TOKEN) {
      return jsonResponse({ ok: false, error: 'GH_TOKEN não configurado no Worker' }, 500, request);
    }

    const apiUrl = `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;
    let ghResp;
    try {
      ghResp = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.GH_TOKEN}`,
          'Accept': 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': 'monofloor-refresh-worker',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ref: REF }),
      });
    } catch (e) {
      return jsonResponse({ ok: false, error: 'Falha ao contatar GitHub', detail: String(e) }, 502, request);
    }

    if (ghResp.status === 204) {
      recentDispatches.set(ip, now);
      // limpa entradas antigas pra não vazar memória
      if (recentDispatches.size > 1000) {
        const cutoff = now - RATE_LIMIT_MS;
        for (const [k, v] of recentDispatches) {
          if (v < cutoff) recentDispatches.delete(k);
        }
      }
      return jsonResponse({
        ok: true,
        message: 'Refresh disparado — aguarde 2-3 min para os 3 agentes completarem.',
        triggered_at: new Date().toISOString(),
      }, 200, request);
    }

    const errText = await ghResp.text().catch(() => '');
    return jsonResponse({
      ok: false,
      error: `GitHub API retornou ${ghResp.status}`,
      detail: errText.slice(0, 500),
    }, ghResp.status === 401 || ghResp.status === 403 ? 502 : ghResp.status, request);
  },
};

function corsHeaders(request) {
  const origin = request.headers.get('Origin');
  const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
}

function jsonResponse(data, status, request) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...corsHeaders(request),
    },
  });
}
