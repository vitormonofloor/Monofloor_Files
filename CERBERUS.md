# 🛡️ Recomendações de Segurança — Portal Monofloor

**Para:** Equipe técnica do `cliente.monofloor.cloud` e `planejamento.monofloor.cloud`
**Data:** 11 de Abril de 2026
**Severidade:** 🔴 **Alta** (exposição de PII sem autenticação)

---

## 📋 Resumo executivo

Durante uma análise técnica do portal `cliente.monofloor.cloud`, foram identificados **5 endpoints REST que retornam dados sensíveis sem nenhuma camada de autenticação**, incluindo informações pessoais identificáveis (PII) de clientes finais. O mesmo padrão ocorre em `planejamento.monofloor.cloud`.

Esses endpoints podem ser acessados por qualquer pessoa na internet sem login, sem token, sem cookie. Isso representa risco direto de:
- **Vazamento de PII** (LGPD — Lei Geral de Proteção de Dados)
- **Concorrentes obtendo a base de clientes**
- **Manipulação de dados via PATCH/POST**
- **Engenharia social baseada em listas reais**

Este documento traz **código pronto para colar** que corrige cada vulnerabilidade.

---

## 🚨 Vulnerabilidades identificadas

⚠️ **Atualização 11/04**: investigação adicional revelou **mais 7 endpoints expostos** sem autenticação, incluindo um vazamento crítico de **CPF e RG de prestadores**.

| # | Endpoint | Domínio | Método | Impacto |
|---|---|---|---|---|
| V1 | `/api/projects` | cliente.monofloor.cloud | GET | Lista 500 projetos com PII completa |
| V2 | `/api/projects/[id]` | cliente.monofloor.cloud | GET | **~90 campos** por projeto, incluindo `whatsappSummary` com resumo IA das mensagens |
| V3 | `/api/projects` | cliente.monofloor.cloud | POST/PATCH | Criação/edição sem auth |
| V4 | `/api/alerts` | cliente.monofloor.cloud | GET | Alertas internos |
| V5 | `/api/checklist` | cliente.monofloor.cloud | GET | Checklist interno |
| **V6** | **`/api/prestadores`** | cliente.monofloor.cloud | GET | 🔴 **CPF, RG e telefone de prestadores (43KB)** |
| **V7** | **`/api/contratos`** | cliente.monofloor.cloud | GET | 192KB de contratos completos |
| **V8** | **`/api/projects/[id]/messages`** | cliente.monofloor.cloud | GET | Mensagens Telegram + WhatsApp por projeto (até 1000+ por obra) |
| **V9** | **`/api/projects/[id]/fases`** | cliente.monofloor.cloud | GET | Materiais e ambientes por projeto |
| **V10** | **`/api/whatsapp/conversations`** | cliente.monofloor.cloud | GET | Lista de 299 grupos WhatsApp ativos |
| **V11** | **`/api/whatsapp/messages?phone=`** | cliente.monofloor.cloud | GET | Mensagens individuais de cada conversa |
| **V12** | **`/api/whatsapp/summary?projectId=`** | cliente.monofloor.cloud | GET | Resumo IA gerado das conversas |
| **V13** | **`/api/crm/typeform-responses`** | cliente.monofloor.cloud | GET | Respostas CRM do Typeform |
| V14 | `/api/obras` | planejamento.monofloor.cloud | GET | 228 obras com endereço residencial |

### Dados expostos confirmados (consolidado)

**De clientes finais:**
- Nome completo, email, telefone
- Endereço completo da obra (rua, número, apto, condomínio, cidade, CEP)
- Metragem, valor estimado, cores escolhidas, tipo de obra
- `portalToken` (token de acesso ao portal individual do cliente)
- Status interno e fases do pipeline
- **Histórico completo de mensagens WhatsApp e Telegram** (texto, áudio transcrito, foto, vídeo)
- Resumo IA das conversas (clima da relação, alertas, pendências, eventos)

**De prestadores Monofloor (CRÍTICO LGPD):**
- 🔴 **CPF**
- 🔴 **RG**
- Telefone, nome completo

**De equipe interna:**
- Nome de consultores, telefones internos
- Distribuição de carteira por consultor (exposição de performance individual)

### 🚨 Severidade extra: vazamento de PII de prestadores

A exposição de **CPF e RG de prestadores via `/api/prestadores`** é uma violação direta da LGPD (Art. 5º, II — dados pessoais) e pode caracterizar:

- **Violação de dados** sob LGPD (Art. 48)
- **Notificação obrigatória** à ANPD se houver evidência de acesso indevido
- **Risco trabalhista** se prestadores souberem que tiveram dados pessoais expostos
- **Risco contratual** com clientes empresariais que têm cláusulas de proteção de dados

**Ação imediata recomendada**: além das correções de auth abaixo, **rotacionar tokens** e **auditar logs** dos últimos 90 dias para detectar possíveis acessos indevidos antes da correção.

---

## 🔧 Fix 1 — `cliente.monofloor.cloud` (Next.js 15 App Router)

### 1.1 Middleware global de autenticação

Crie ou atualize `middleware.ts` na raiz do projeto Next.js:

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';
import { verifySession } from '@/lib/auth';

// Rotas que NÃO precisam de autenticação
const PUBLIC_API_ROUTES = [
  '/api/auth',           // login
  '/api/auth/logout',
  '/api/health',         // se existir
];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Apenas protege rotas /api/*
  if (!pathname.startsWith('/api/')) {
    return NextResponse.next();
  }

  // Permite rotas públicas declaradas
  if (PUBLIC_API_ROUTES.some(route => pathname === route || pathname.startsWith(route + '/'))) {
    return NextResponse.next();
  }

  // Verifica sessão via cookie httpOnly
  const sessionCookie = request.cookies.get('mf_session')?.value;
  if (!sessionCookie) {
    return NextResponse.json(
      { error: 'unauthorized', message: 'Autenticação obrigatória' },
      { status: 401 }
    );
  }

  // Valida token de sessão
  try {
    const session = await verifySession(sessionCookie);
    if (!session || !session.userId) {
      return NextResponse.json(
        { error: 'invalid_session', message: 'Sessão inválida ou expirada' },
        { status: 401 }
      );
    }

    // Anexa o userId no header pra rota usar
    const headers = new Headers(request.headers);
    headers.set('x-user-id', session.userId);
    headers.set('x-user-role', session.role || 'user');

    return NextResponse.next({ request: { headers } });
  } catch (e) {
    return NextResponse.json(
      { error: 'unauthorized', message: 'Falha ao validar sessão' },
      { status: 401 }
    );
  }
}

export const config = {
  matcher: '/api/:path*',
};
```

### 1.2 Helper de sessão (lib/auth.ts)

```typescript
// lib/auth.ts
import { SignJWT, jwtVerify } from 'jose';

const JWT_SECRET = new TextEncoder().encode(
  process.env.SESSION_SECRET || ''
);

if (!process.env.SESSION_SECRET || process.env.SESSION_SECRET.length < 32) {
  throw new Error('SESSION_SECRET deve ter pelo menos 32 caracteres');
}

export interface Session {
  userId: string;
  email: string;
  role: 'admin' | 'operador' | 'cliente';
  exp: number;
}

// Cria token de sessão (chamado no /api/auth ao logar com sucesso)
export async function createSession(payload: Omit<Session, 'exp'>): Promise<string> {
  const token = await new SignJWT({ ...payload })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('8h')           // sessão expira em 8h
    .setIssuer('cliente.monofloor.cloud')
    .sign(JWT_SECRET);
  return token;
}

// Valida token de sessão (usado no middleware)
export async function verifySession(token: string): Promise<Session | null> {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET, {
      issuer: 'cliente.monofloor.cloud',
    });
    return payload as unknown as Session;
  } catch {
    return null;
  }
}
```

### 1.3 Atualizar `/api/auth/route.ts` para setar cookie httpOnly

```typescript
// app/api/auth/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { createSession } from '@/lib/auth';
import { verifyPassword, getUserByEmail } from '@/lib/users';
import { rateLimit } from '@/lib/rate-limit';

export async function POST(request: NextRequest) {
  // 1. Rate limit por IP (importante para login)
  const ip = request.headers.get('x-forwarded-for') || 'unknown';
  const limited = await rateLimit(`auth:${ip}`, 5, 60); // 5 tentativas por minuto
  if (limited) {
    return NextResponse.json(
      { error: 'rate_limited', message: 'Muitas tentativas. Aguarde 1 minuto.' },
      { status: 429 }
    );
  }

  // 2. Validação de input
  let body: { email?: string; password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'invalid_body' }, { status: 400 });
  }

  if (!body.email || !body.password || typeof body.email !== 'string') {
    return NextResponse.json({ error: 'missing_credentials' }, { status: 400 });
  }

  // 3. Busca usuário e verifica senha (use bcrypt/argon2, NUNCA texto puro)
  const user = await getUserByEmail(body.email.toLowerCase().trim());
  if (!user || !await verifyPassword(body.password, user.passwordHash)) {
    // Mesma mensagem de erro pra não expor se o email existe
    return NextResponse.json(
      { error: 'invalid_credentials', message: 'Email ou senha incorretos' },
      { status: 401 }
    );
  }

  // 4. Cria sessão e seta cookie httpOnly
  const token = await createSession({
    userId: user.id,
    email: user.email,
    role: user.role,
  });

  const response = NextResponse.json({ ok: true });
  response.cookies.set('mf_session', token, {
    httpOnly: true,                    // 🔒 não acessível via JS
    secure: true,                      // 🔒 só HTTPS
    sameSite: 'lax',                   // 🔒 protege contra CSRF básico
    path: '/',
    maxAge: 8 * 60 * 60,              // 8 horas
  });

  return response;
}

// Bloqueia outros métodos
export async function GET() {
  return NextResponse.json({ error: 'method_not_allowed' }, { status: 405 });
}
```

### 1.4 Endpoint de logout

```typescript
// app/api/auth/logout/route.ts
import { NextResponse } from 'next/server';

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete('mf_session');
  return response;
}
```

### 1.5 Exemplo: proteger `/api/projects/route.ts`

**Antes (vulnerável):**
```typescript
// app/api/projects/route.ts
export async function GET() {
  const projects = await db.project.findMany();
  return Response.json(projects);  // ❌ retorna tudo, sem auth
}
```

**Depois (seguro):**
```typescript
// app/api/projects/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET(request: NextRequest) {
  // Middleware já garantiu auth — pega userId do header
  const userId = request.headers.get('x-user-id');
  const role = request.headers.get('x-user-role');

  if (!userId) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  // Filtra dados pelo papel do usuário
  let projects;
  if (role === 'admin' || role === 'operador') {
    projects = await db.project.findMany({
      // Limite máximo pra evitar dump completo
      take: 200,
      orderBy: { updatedAt: 'desc' },
    });
  } else if (role === 'cliente') {
    // Cliente só vê os próprios projetos
    projects = await db.project.findMany({
      where: { ownerId: userId },
    });
  } else {
    return NextResponse.json({ error: 'forbidden' }, { status: 403 });
  }

  // Remove campos sensíveis antes de retornar
  const safe = projects.map(p => ({
    id: p.id,
    clienteNome: role === 'cliente' ? undefined : p.clienteNome,
    projetoCidade: p.projetoCidade,
    projetoMetragem: p.projetoMetragem,
    status: p.status,
    faseAtual: p.faseAtual,
    dataExecucaoPrevista: p.dataExecucaoPrevista,
    // ❌ NÃO retornar: portalToken, telefone, email, endereço completo
    // exceto para o próprio dono
  }));

  return NextResponse.json(safe);
}
```

### 1.6 Helper de rate limit (lib/rate-limit.ts)

```typescript
// lib/rate-limit.ts
// Use Upstash Redis ou similar em produção. Em dev, in-memory.
const buckets = new Map<string, { count: number; reset: number }>();

export async function rateLimit(
  key: string,
  max: number,
  windowSec: number
): Promise<boolean> {
  const now = Date.now();
  const bucket = buckets.get(key);

  if (!bucket || bucket.reset < now) {
    buckets.set(key, { count: 1, reset: now + windowSec * 1000 });
    return false;
  }

  if (bucket.count >= max) return true;

  bucket.count++;
  return false;
}

// Em produção: substitua por Upstash:
// import { Ratelimit } from '@upstash/ratelimit';
// import { Redis } from '@upstash/redis';
// const ratelimit = new Ratelimit({
//   redis: Redis.fromEnv(),
//   limiter: Ratelimit.slidingWindow(5, '1 m'),
// });
```

---

## 🔧 Fix 2 — `planejamento.monofloor.cloud` (Express)

### 2.1 Middleware de autenticação

```javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET || JWT_SECRET.length < 32) {
  throw new Error('JWT_SECRET deve ter pelo menos 32 caracteres');
}

function requireAuth(req, res, next) {
  // Tenta cookie primeiro, depois Authorization header
  const token = req.cookies?.mf_session ||
                req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({
      error: 'unauthorized',
      message: 'Autenticação obrigatória'
    });
  }

  try {
    const payload = jwt.verify(token, JWT_SECRET, {
      issuer: 'planejamento.monofloor.cloud',
    });
    req.user = payload;
    next();
  } catch (e) {
    return res.status(401).json({
      error: 'invalid_token',
      message: 'Token inválido ou expirado'
    });
  }
}

function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'forbidden' });
    }
    next();
  };
}

module.exports = { requireAuth, requireRole };
```

### 2.2 Aplicar nas rotas

```javascript
// routes/obras.js
const express = require('express');
const router = express.Router();
const { requireAuth, requireRole } = require('../middleware/auth');
const db = require('../lib/db');

// ❌ ANTES (vulnerável):
// router.get('/api/obras', async (req, res) => {
//   const obras = await db.obras.findAll();
//   res.json(obras);
// });

// ✅ DEPOIS (seguro):
router.get('/api/obras',
  requireAuth,
  requireRole('admin', 'operador'),
  async (req, res) => {
    try {
      const obras = await db.obras.findAll({
        limit: 100,                     // limite máximo
        order: [['updatedAt', 'DESC']],
      });

      // Remove PII desnecessária da resposta
      const safe = obras.map(o => ({
        id: o.id,
        projeto_nome: o.projeto_nome,
        cliente_iniciais: o.cliente?.split(' ').map(n => n[0]).join('.'),
        // ❌ NÃO retornar: cliente, projeto_endereco completo
        cidade: o.dados_json ? JSON.parse(o.dados_json).contexto?.cidadeProjeto : null,
        metragem: o.dados_json ? JSON.parse(o.dados_json).contexto?.metragemProjeto : null,
        status: o.status,
        tipo_projeto: o.tipo_projeto,
      }));

      res.json(safe);
    } catch (e) {
      console.error('Erro listar obras:', e);
      res.status(500).json({ error: 'internal_error' });
    }
  }
);

// Endpoint individual com verificação de ownership
router.get('/api/obras/:id',
  requireAuth,
  async (req, res) => {
    const obra = await db.obras.findByPk(req.params.id);
    if (!obra) return res.status(404).json({ error: 'not_found' });

    // Cliente só vê obras dele
    if (req.user.role === 'cliente' && obra.ownerId !== req.user.userId) {
      return res.status(403).json({ error: 'forbidden' });
    }

    res.json(obra);
  }
);

module.exports = router;
```

### 2.3 Login endpoint

```javascript
// routes/auth.js
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const { db } = require('../lib/db');
const router = express.Router();

const loginLimiter = rateLimit({
  windowMs: 60 * 1000,                  // 1 minuto
  max: 5,                               // 5 tentativas por IP
  message: { error: 'rate_limited' },
  standardHeaders: true,
});

router.post('/api/auth', loginLimiter, async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ error: 'missing_credentials' });
  }

  const user = await db.users.findOne({ where: { email: email.toLowerCase() } });
  if (!user || !await bcrypt.compare(password, user.passwordHash)) {
    return res.status(401).json({ error: 'invalid_credentials' });
  }

  const token = jwt.sign(
    { userId: user.id, email: user.email, role: user.role },
    process.env.JWT_SECRET,
    { expiresIn: '8h', issuer: 'planejamento.monofloor.cloud' }
  );

  res
    .cookie('mf_session', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 8 * 60 * 60 * 1000,
    })
    .json({ ok: true });
});

module.exports = router;
```

---

## 🌐 Fix 3 — CORS lockdown

### Para o Next.js

```typescript
// app/api/projects/route.ts (e todas as outras rotas)
export async function GET(request: NextRequest) {
  const origin = request.headers.get('origin');
  const allowedOrigins = [
    'https://cliente.monofloor.cloud',
    'https://www.monofloor.cloud',
    // adicione domínios aprovados aqui
  ];

  const headers = new Headers();
  if (origin && allowedOrigins.includes(origin)) {
    headers.set('Access-Control-Allow-Origin', origin);
    headers.set('Access-Control-Allow-Credentials', 'true');
    headers.set('Vary', 'Origin');
  }
  // Se origin não está na whitelist, NÃO adicione CORS headers (browser bloqueia)

  // ... resto do handler
}
```

### Para o Express

```javascript
// app.js
const cors = require('cors');

const allowedOrigins = [
  'https://planejamento.monofloor.cloud',
  'https://cliente.monofloor.cloud',
  'https://www.monofloor.cloud',
];

app.use(cors({
  origin: (origin, callback) => {
    if (!origin) return callback(null, true);     // mobile apps, curl
    if (allowedOrigins.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error('CORS bloqueado'));
  },
  credentials: true,
  methods: ['GET', 'POST', 'PATCH', 'DELETE'],
}));
```

---

## 🛡️ Fix 4 — Headers de segurança

### Next.js — `next.config.js`

```javascript
// next.config.js
const securityHeaders = [
  { key: 'X-DNS-Prefetch-Control', value: 'on' },
  { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline' fonts.googleapis.com",
      "font-src 'self' fonts.gstatic.com data:",
      "img-src 'self' data: blob:",
      "connect-src 'self'",
      "frame-ancestors 'self'",
    ].join('; '),
  },
];

module.exports = {
  async headers() {
    return [{ source: '/(.*)', headers: securityHeaders }];
  },
};
```

### Express — `app.js`

```javascript
const helmet = require('helmet');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'", 'fonts.googleapis.com'],
      fontSrc: ["'self'", 'fonts.gstatic.com'],
      imgSrc: ["'self'", 'data:'],
    },
  },
  hsts: { maxAge: 63072000, includeSubDomains: true, preload: true },
}));
```

---

## ✅ Checklist de implantação

### Antes de subir para produção
- [ ] `SESSION_SECRET` / `JWT_SECRET` gerados com `openssl rand -base64 64`
- [ ] Senhas no banco usando bcrypt (cost ≥12) ou argon2
- [ ] HTTPS forçado em todas as URLs
- [ ] Cookies `httpOnly` + `secure` + `sameSite=lax`
- [ ] Rate limit no `/api/auth` (5/min por IP)
- [ ] CORS restrito a domínios conhecidos
- [ ] Logs de auth (sucesso e falha) sem expor senha
- [ ] Migração: invalidar `portalToken` antigos e gerar novos

### Testes (curl)

```bash
# 1. Sem cookie → deve retornar 401
curl -i https://cliente.monofloor.cloud/api/projects
# Esperado: HTTP/2 401

# 2. Com cookie inválido → 401
curl -i -H "Cookie: mf_session=invalido" https://cliente.monofloor.cloud/api/projects
# Esperado: HTTP/2 401

# 3. Login válido → 200 + cookie
curl -i -X POST https://cliente.monofloor.cloud/api/auth \
  -H "Content-Type: application/json" \
  -d '{"email":"operador@monofloor.com","password":"senha"}'
# Esperado: HTTP/2 200 + Set-Cookie: mf_session=... HttpOnly Secure

# 4. Rate limit (chame 6 vezes seguidas)
for i in {1..6}; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST \
    https://cliente.monofloor.cloud/api/auth \
    -H "Content-Type: application/json" \
    -d '{"email":"x","password":"x"}'
done
# Esperado: 401 401 401 401 401 429 (último é rate limit)

# 5. CORS de origem não autorizada → bloqueado
curl -i -H "Origin: https://attacker.com" \
  https://cliente.monofloor.cloud/api/projects
# Esperado: sem Access-Control-Allow-Origin no response (browser bloqueia)
```

---

## 📦 Dependências necessárias

### Next.js
```bash
npm install jose bcryptjs
npm install --save-dev @types/bcryptjs
# Opcional para rate limit em prod:
npm install @upstash/ratelimit @upstash/redis
```

### Express
```bash
npm install jsonwebtoken bcryptjs cookie-parser cors helmet express-rate-limit
```

---

## 🎯 Prioridade de execução

| Prioridade | Ação | Tempo estimado |
|---|---|---|
| 🔴 P0 | Adicionar middleware de auth no `/api/projects` | 30 min |
| 🔴 P0 | Invalidar e regenerar todos os `portalToken` | 1 h |
| 🟡 P1 | Implementar rate limit no `/api/auth` | 30 min |
| 🟡 P1 | Aplicar headers de segurança (Helmet/next.config) | 15 min |
| 🟡 P1 | CORS lockdown | 15 min |
| 🟢 P2 | Auditoria de logs históricos (quem acessou o quê) | 4 h |
| 🟢 P2 | LGPD: notificar ANPD se houve acesso indevido confirmado | conforme jurídico |

**Tempo total para fix mínimo viável: ~3 horas**

---

## 📞 Próximos passos

1. **Aplicar fix P0 hoje** (middleware no `/api/projects`)
2. **Invalidar tokens** atuais e enviar novos aos clientes
3. **Auditoria** de logs do nginx/Vercel para detectar se houve acessos suspeitos antes do fix
4. **Comunicar** internamente que a vulnerabilidade foi corrigida

Estou disponível para apoiar a aplicação dessas correções se precisar.

---

*Documento gerado em 11/04/2026 — análise técnica defensiva.*
