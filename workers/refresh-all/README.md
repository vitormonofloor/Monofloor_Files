# Worker: monofloor-refresh

Proxy Cloudflare Worker que dispara o workflow `refresh-all.yml` (Refresh + ARGOS + ATENA) a partir de um clique no dashboard, sem expor token GitHub no client.

## Fluxo

```
Dashboard (GitHub Pages)  →  POST  →  Worker  →  GitHub API  →  GH Actions
                            (sem token)        (com token)     (3 workflows)
```

## Por que Worker e não chamada direta?

O dashboard é HTML estático em repo público. Qualquer token embutido no JS vaza via DevTools. O Worker mantém o token como secret server-side e responde só a origens permitidas (GitHub Pages do Vitor + localhost).

## Deploy — passo-a-passo (uma vez só)

### 1. Criar PAT no GitHub
- Vá em https://github.com/settings/tokens/new
- Nome: `Monofloor Refresh Worker`
- Expiração: 1 ano (ou "No expiration" — vai precisar lembrar de renovar)
- Escopo (apenas 1): **`workflow`** (em "Repository access" — `Read and write` em Actions)
  - Se for fine-grained PAT: Resource owner = `vitormonofloor`, Repositories = `Monofloor_Files`, Permissions → Repository → **Actions: Read and write**
- **Copie o token**. Você vai colar no Cloudflare.

### 2. Deploy via dashboard Cloudflare (mais fácil)
1. Vá em https://dash.cloudflare.com → Workers & Pages → **Create application** → **Create Worker**
2. Nome: `monofloor-refresh`
3. **Deploy** (com o "Hello World" default)
4. Após criado: **Edit code**
5. Apague tudo e cole o conteúdo de `src/index.js` deste diretório
6. **Save and deploy**
7. Vá em **Settings → Variables and Secrets → Add variable**
   - Type: **Secret**
   - Name: `GH_TOKEN`
   - Value: (cole o PAT do passo 1)
   - **Save**
8. Copie a URL final (algo como `https://monofloor-refresh.SEU-USUARIO.workers.dev`) e me passe — eu integro no dashboard.

### 2-alt. Deploy via wrangler CLI (se preferir)
```bash
npm install -g wrangler
cd workers/refresh-all
wrangler login
wrangler secret put GH_TOKEN     # cole o PAT quando pedir
wrangler deploy
```

## Teste manual

Health check (sem disparar nada):
```bash
curl https://monofloor-refresh.SEU-USUARIO.workers.dev
# {"ok":true,"service":"monofloor-refresh","uptime":...}
```

Dispatch real (precisa Origin permitido — então só funciona via dashboard, não curl direto a menos que adicione `-H "Origin: https://vitormonofloor.github.io"`):
```bash
curl -X POST https://monofloor-refresh.SEU-USUARIO.workers.dev \
  -H "Origin: https://vitormonofloor.github.io"
# {"ok":true,"message":"Refresh disparado — aguarde 2-3 min..."}
```

## Limites e custos

- Free tier Cloudflare Workers: **100.000 requisições/dia**. Vamos usar ~30/dia (1 click ≈ 1 req). R$ 0/mês.
- Rate limit no Worker: **1 dispatch a cada 5 min por IP** (best-effort, in-memory). Se virar problema, troca por KV ou Durable Objects.
- GitHub Actions free: **2.000 minutos/mês** em repo público (ilimitado). Sem custo.

## Renovar token

Quando o PAT expirar:
1. Crie novo PAT (passo 1)
2. Cloudflare → Worker `monofloor-refresh` → Settings → Variables → `GH_TOKEN` → **Edit** → cole o novo → Save

Nada do dashboard ou do código do Worker precisa mudar.
