// Cloudflare Worker · proxy pra disparar workflow analisar-orion.yml
//
// Recebe POST do Lab Orion (https://orion-pub.vitor-monofloor.workers.dev) com
// { obra_ids: "id1,id2,...", recorte: "Em execução" } e dispara o workflow no
// GitHub via repository_dispatch (que aceita payload customizado).
//
// GH_TOKEN é Secret do Worker · não exposto no client.
//
// Rate limit: 1 dispatch a cada 60s por IP (análises são caras · evita spam).

const ALLOWED_ORIGINS = [
  'https://orion-pub.vitor-monofloor.workers.dev',
  'https://lab.monofloor.cloud',  // futuro custom domain
  'http://localhost:8000',
  'http://127.0.0.1:8000',
];

const REPO = 'vitormonofloor/Monofloor_Files';
const EVENT_TYPE = 'analisar-orion';

// Rate limit: 1 análise por minuto por IP (análise IA não é gratis cognitivamente)
const RATE_LIMIT_MS = 60 * 1000;
const recentDispatches = new Map();

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders(request) });
    }

    if (request.method === 'GET') {
      return jsonResponse({
        ok: true,
        service: 'orion-analise',
        uptime: Date.now(),
        usage: 'POST { obra_ids: "id1,id2,...", recorte: "label" }',
      }, 200, request);
    }

    if (request.method !== 'POST') {
      return jsonResponse({ ok: false, error: 'Method not allowed' }, 405, request);
    }

    const origin = request.headers.get('Origin');
    if (!ALLOWED_ORIGINS.includes(origin)) {
      return jsonResponse({ ok: false, error: 'Origem não autorizada', origin }, 403, request);
    }

    // Rate limit por IP
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const now = Date.now();
    const last = recentDispatches.get(ip);
    if (last && (now - last) < RATE_LIMIT_MS) {
      const waitSec = Math.ceil((RATE_LIMIT_MS - (now - last)) / 1000);
      return jsonResponse({
        ok: false,
        error: `Aguarde ${waitSec}s antes de outra análise.`,
        retry_after: waitSec,
      }, 429, request);
    }

    if (!env.GH_TOKEN) {
      return jsonResponse({ ok: false, error: 'GH_TOKEN não configurado no Worker' }, 500, request);
    }

    // Parse body
    let body;
    try {
      body = await request.json();
    } catch (e) {
      return jsonResponse({ ok: false, error: 'JSON inválido no body' }, 400, request);
    }

    const obraIds = String(body.obra_ids || '').trim();
    const recorte = String(body.recorte || 'manual').trim().slice(0, 80);

    if (!obraIds) {
      return jsonResponse({ ok: false, error: 'obra_ids obrigatório' }, 400, request);
    }

    // Limita pra não estourar custo (max 50 obras por chamada · alinha com analisar_recorte)
    const idsArr = obraIds.split(',').map(s => s.trim()).filter(Boolean);
    if (idsArr.length === 0) {
      return jsonResponse({ ok: false, error: 'Nenhum obra_id válido' }, 400, request);
    }
    if (idsArr.length > 50) {
      return jsonResponse({
        ok: false,
        error: `Máximo 50 obras por análise · você enviou ${idsArr.length}`,
      }, 400, request);
    }

    // Dispara repository_dispatch
    const apiUrl = `https://api.github.com/repos/${REPO}/dispatches`;
    let ghResp;
    try {
      ghResp = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.GH_TOKEN}`,
          'Accept': 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': 'orion-analise-worker',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: EVENT_TYPE,
          client_payload: {
            obra_ids: idsArr.join(','),
            recorte: recorte,
            triggered_by: ip,
            triggered_at: new Date().toISOString(),
          },
        }),
      });
    } catch (e) {
      return jsonResponse({
        ok: false,
        error: 'Falha ao contatar GitHub',
        detail: String(e),
      }, 502, request);
    }

    if (ghResp.status === 204) {
      recentDispatches.set(ip, now);
      // Cleanup map antigo
      if (recentDispatches.size > 500) {
        const cutoff = now - RATE_LIMIT_MS;
        for (const [k, v] of recentDispatches) {
          if (v < cutoff) recentDispatches.delete(k);
        }
      }
      return jsonResponse({
        ok: true,
        message: `Análise disparada · ${idsArr.length} obras · recorte "${recorte}"`,
        n_obras: idsArr.length,
        recorte,
        eta_seconds: 60 + idsArr.length * 3,  // estimativa: 1min base + 3s por obra
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
