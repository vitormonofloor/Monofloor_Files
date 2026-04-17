/**
 * Monofloor Auth Gate
 * Proteção LGPD — gate de autenticação client-side
 * 
 * Uso: inclua no <head> de qualquer página protegida:
 * <script src="auth.js"></script>  (ou ../auth.js pra subpastas)
 * 
 * Para trocar a senha:
 * 1. Gere o SHA-256 da nova senha: echo -n "novasenha" | sha256sum
 * 2. Substitua o valor de HASH abaixo
 */

(function() {
  // SHA-256 hash da senha (senha atual: monofloor2026)
  var HASH = '5a62c2138bf2ca64fee65573cebd7e1f4dbb4de09882cdfbc70531583f913b39';
  var SESSION_KEY = 'mono_auth_token';
  var TOKEN_VALUE = 'mono_' + HASH.substring(0, 16);

  // Já autenticado nesta sessão?
  if (sessionStorage.getItem(SESSION_KEY) === TOKEN_VALUE) return;

  // Bloquear scroll enquanto não autenticado
  document.documentElement.style.overflow = 'hidden';

  // SHA-256 async
  async function sha256(str) {
    var buf = new TextEncoder().encode(str);
    var hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash)).map(function(b) { return b.toString(16).padStart(2, '0'); }).join('');
  }

  // Criar overlay de login
  function createGate() {
    var overlay = document.createElement('div');
    overlay.id = 'auth-gate';
    overlay.innerHTML = [
      '<style>',
      '#auth-gate{position:fixed;inset:0;z-index:99999;background:#f0ebe3;display:flex;align-items:center;justify-content:center;font-family:"Plus Jakarta Sans",system-ui,sans-serif}',
      '#auth-gate *{box-sizing:border-box;margin:0;padding:0}',
      '.auth-box{text-align:center;width:100%;max-width:360px;padding:0 24px}',
      '.auth-logo{height:36px;filter:brightness(0) sepia(1) saturate(0.3) hue-rotate(350deg) brightness(0.25);margin-bottom:8px}',
      '.auth-tag{font-size:9px;letter-spacing:4px;text-transform:uppercase;color:#a89e92;margin-bottom:40px}',
      '.auth-label{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#a89e92;margin-bottom:12px;font-weight:500}',
      '.auth-input{width:100%;padding:12px 16px;border:1px solid #e0d8cc;border-radius:12px;background:#f8f5f0;font-size:14px;font-family:"Plus Jakarta Sans",sans-serif;color:#2a2520;outline:none;text-align:center;letter-spacing:2px;transition:border-color 0.3s}',
      '.auth-input:focus{border-color:#b8976a}',
      '.auth-input.error{border-color:#c44b4b;animation:shake 0.4s ease}',
      '.auth-btn{width:100%;margin-top:16px;padding:12px;border:1px solid #d4c4a8;border-radius:12px;background:transparent;color:#8b6d44;font-size:11px;font-weight:500;letter-spacing:2px;text-transform:uppercase;cursor:pointer;font-family:"Plus Jakarta Sans",sans-serif;transition:all 0.3s}',
      '.auth-btn:hover{background:#2a2520;border-color:#2a2520;color:#f0ebe3}',
      '.auth-error{font-size:11px;color:#c44b4b;margin-top:12px;min-height:16px;transition:opacity 0.3s}',
      '.auth-footer{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#c8bfb4}',
      '@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-8px)}50%{transform:translateX(8px)}75%{transform:translateX(-4px)}}',
      '</style>',
      '<div class="auth-box">',
      '  <img src="https://static.wixstatic.com/media/2bc4fe_d7fd788ceb094e96b86315e020950bda~mv2.png/v1/fill/w_506,h_156,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Artboard%201.png" alt="monofloor" class="auth-logo">',
      '  <div class="auth-tag">Área restrita</div>',
      '  <div class="auth-label">Senha de acesso</div>',
      '  <input type="password" class="auth-input" id="auth-pwd" placeholder="••••••••" autocomplete="off">',
      '  <button class="auth-btn" id="auth-submit">Entrar</button>',
      '  <div class="auth-error" id="auth-msg"></div>',
      '</div>',
      '<div class="auth-footer">Acesso protegido · LGPD</div>',
    ].join('\n');

    document.body.appendChild(overlay);

    var pwd = document.getElementById('auth-pwd');
    var btn = document.getElementById('auth-submit');
    var msg = document.getElementById('auth-msg');

    async function tryAuth() {
      var value = pwd.value.trim();
      if (!value) { pwd.classList.add('error'); setTimeout(function() { pwd.classList.remove('error'); }, 500); return; }
      var h = await sha256(value);
      if (h === HASH) {
        sessionStorage.setItem(SESSION_KEY, TOKEN_VALUE);
        overlay.style.transition = 'opacity 0.4s';
        overlay.style.opacity = '0';
        setTimeout(function() {
          overlay.remove();
          document.documentElement.style.overflow = '';
        }, 400);
      } else {
        pwd.classList.add('error');
        msg.textContent = 'Senha incorreta';
        msg.style.opacity = '1';
        setTimeout(function() { pwd.classList.remove('error'); msg.style.opacity = '0'; }, 2000);
        pwd.value = '';
        pwd.focus();
      }
    }

    btn.addEventListener('click', tryAuth);
    pwd.addEventListener('keydown', function(e) { if (e.key === 'Enter') tryAuth(); });
    setTimeout(function() { pwd.focus(); }, 100);
  }

  // Esperar DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createGate);
  } else {
    createGate();
  }
})();
