# AUTH — Autenticação LGPD dos Painéis Monofloor

> Gate de autenticação client-side para proteção de dados pessoais (LGPD).

---

## Dados Técnicos

| Campo | Valor |
|---|---|
| **Arquivo** | `auth.js` (raiz do repo Monofloor_Files) |
| **Tipo** | Client-side, SHA-256, sessionStorage |
| **Senha atual** | `monofloor2026` |
| **Hash SHA-256** | `5a62c2138bf2ca64fee65573cebd7e1f4dbb4de09882cdfbc70531583f913b39` |

## Páginas Protegidas

| Página | Inclui | Dados sensíveis |
|---|---|---|
| `hub.html` | `<script src="auth.js">` | Links para painéis |
| `indicadores-v2.html` | `<script src="auth.js">` | Nomes clientes, consultores, ocorrências |
| `analise/dashboard.html` | `<script src="../auth.js">` | Nomes completos, cidades, UUIDs, equipes |

## Página Pública (sem auth)

| Página | Motivo |
|---|---|
| `splash.html` | Apenas branding, zero dados pessoais |

## Como Trocar a Senha

```bash
# 1. Gerar hash da nova senha
echo -n "suanovasenha" | sha256sum

# 2. Copiar o hash gerado (64 caracteres hex)
# 3. Abrir auth.js no repo Monofloor_Files
# 4. Substituir o valor de HASH na linha 14:
var HASH = 'cole_o_novo_hash_aqui';

# 5. Commit e push
git add auth.js
git commit -m "security: atualiza senha auth"
git push origin main
```

## Como Funciona

1. Página carrega → `auth.js` verifica `sessionStorage`
2. Se não autenticado → overlay cobre tudo (fundo sólido, z-index 99999)
3. Usuário digita senha → JS calcula SHA-256 → compara com HASH
4. Se correto → salva token em `sessionStorage` → overlay faz fade-out
5. Navegação entre páginas protegidas → já autenticado (mesma sessão)
6. Fechar aba/navegador → sessão perdida → precisa autenticar de novo

## Limitações (importante saber)

- **Não é autenticação real de servidor** — quem inspecionar o código-fonte vê o hash
- **Repositório público** — quem acessar o repo raw no GitHub vê os HTMLs com dados
- **Não protege contra** — força bruta, acesso direto ao repo, developer tools

## Próximos Passos (segurança real)

1. **Tornar o repositório privado** no GitHub
2. **Cloudflare Access** — auth real na frente do GitHub Pages (gratuito até 50 usuários)
3. **Mover pra `cliente.monofloor.cloud`** — que já tem autenticação NestJS
4. **Anonimizar dados** — versão pública com dados fictícios

## Conexões

- **Protege**: [[ARGOS]] indicadores-v2, Dashboard Executivo, Hub
- **Skill relacionada**: seguranca-monofloor (checklists detalhados)
- **LGPD**: Art. 6, 7, 46 — finalidade, base legal, segurança

---

*Criado em: 17/04/2026*
*Tags: #seguranca #lgpd #auth #monofloor*
