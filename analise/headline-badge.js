/**
 * headline-badge.js — componente reutilizável
 *
 * Lê dados/headline.json e renderiza badge "atualizado há X min" no canto da página.
 * Cores: verde (<60min) / âmbar (60min-12h) / vermelho (>12h ou erro de fetch).
 *
 * Uso em qualquer painel:
 *   <script src="analise/headline-badge.js" data-src="analise/dados/headline.json" defer></script>
 *
 * O atributo data-src é opcional — default 'dados/headline.json' (relativo à página).
 *
 * Se um <div id="headline-badge"> existir, preenche ele. Senão, cria fixed top-right.
 */
(function () {
  const script = document.currentScript;
  const SRC = script?.dataset?.src || 'dados/headline.json';

  function fmtAge(updatedIso) {
    const t = new Date(updatedIso).getTime();
    if (Number.isNaN(t)) return { txt: 'horário inválido', level: 'red' };
    const diffMin = Math.max(0, Math.floor((Date.now() - t) / 60000));
    let level = 'green';
    if (diffMin >= 60) level = 'amber';
    if (diffMin >= 720) level = 'red';

    let txt;
    if (diffMin < 1) txt = 'agora há pouco';
    else if (diffMin < 60) txt = `há ${diffMin} min`;
    else if (diffMin < 1440) {
      const h = Math.floor(diffMin / 60);
      txt = `há ${h} h`;
    } else {
      const d = Math.floor(diffMin / 1440);
      txt = `há ${d} dia${d > 1 ? 's' : ''}`;
    }
    return { txt, level, diffMin };
  }

  function injectStyle() {
    if (document.getElementById('hb-style')) return;
    const s = document.createElement('style');
    s.id = 'hb-style';
    s.textContent = `
      .hb-pill {
        display: inline-flex; align-items: center; gap: 6px;
        font: 500 11px/1 'JetBrains Mono', ui-monospace, monospace;
        letter-spacing: .5px; text-transform: uppercase;
        padding: 6px 10px; border-radius: 99px;
        border: 1px solid; user-select: none;
      }
      .hb-fixed { position: fixed; top: 14px; right: 14px; z-index: 9999; }
      .hb-pill .hb-dot {
        width: 6px; height: 6px; border-radius: 50%;
      }
      .hb-green { background: #e8f2ec; border-color: #c4e0cf; color: #2d5a3a; }
      .hb-green .hb-dot { background: #3d8a5a; box-shadow: 0 0 6px #3d8a5a55; }
      .hb-amber { background: #f4f0e6; border-color: #e0d2b4; color: #5a4a2a; }
      .hb-amber .hb-dot { background: #b89a4a; box-shadow: 0 0 6px #b89a4a55; }
      .hb-red   { background: #f6eaea; border-color: #e8c8c8; color: #6a2a2a; }
      .hb-red .hb-dot { background: #c45a5a; box-shadow: 0 0 8px #c45a5a88;
        animation: hb-blink 1.4s ease-in-out infinite; }
      @keyframes hb-blink { 0%,100%{opacity:1} 50%{opacity:.45} }
    `;
    document.head.appendChild(s);
  }

  function ensureContainer() {
    let el = document.getElementById('headline-badge');
    if (el) return { el, fixed: false };
    el = document.createElement('div');
    el.id = 'headline-badge';
    el.className = 'hb-fixed';
    document.body.appendChild(el);
    return { el, fixed: true };
  }

  function render(state, data) {
    injectStyle();
    const { el } = ensureContainer();
    if (state === 'error') {
      el.innerHTML = `<span class="hb-pill hb-red"><span class="hb-dot"></span>fonte indisponível</span>`;
      el.title = 'Falha ao carregar dados/headline.json — dado pode estar desatualizado';
      return;
    }
    const age = fmtAge(data.atualizado_em);
    const cor = `hb-${age.level}`;
    el.innerHTML = `<span class="hb-pill ${cor}"><span class="hb-dot"></span>atualizado ${age.txt}</span>`;
    el.title = [
      `Snapshot: ${data.snapshot_date}`,
      `Score: ${data.score}`,
      `Ativas: ${data.ativas}`,
      `Alertas hoje: ${data.alertas?.novos_hoje ?? 0}`,
      `Fonte: ${data.fonte || 'headline.json'}`
    ].join(' · ');
  }

  function load() {
    fetch(SRC, { cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(data => render('ok', data))
      .catch(err => { console.warn('[headline-badge]', err); render('error'); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();
