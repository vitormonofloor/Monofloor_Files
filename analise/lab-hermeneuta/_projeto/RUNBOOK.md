# 5 · RUNBOOK · Receitas operacionais

## Verificar saúde rápido (sentinela · ~1s)

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python agente/sentinela.py
```

Saída: 9 checks · `ok` / `warn` / `crit` · cada um com sugestão de ação. Gera `dados/status.json`.

## Rodar varredura completa manual (~47s)

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python agente/varredura.py
```

Roda os 13 passos · com lock anti-concorrência (se outra rodando, sai sem fazer nada).

Pipeline:
1. Backup rolling
2. Selecionar piloto (227 ativas)
3. Coletar Painel API (Telegram + WhatsApp)
4. Extrair timeline + bloco telegram
5. Aplicar régua SLA
6. Equipe / cores / KIRA / consultor
7. Sanitizar + KPIs + refresh
8. Sentinela
9. Publicar (git push pub repo + wrangler deploy)

## Rodar IA cirurgicamente em 1 obra (~2-3min · custo zero)

```powershell
$env:GITHUB_TOKEN = "<PAT com escopo repo>"
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python agente/analisar_recorte.py --obra-ids "<obra_id>" --recorte "manual"
python agente/publicar.py
```

GitHub Models gpt-4o-mini · 8k req/dia gratuito · failover gracioso se sem token.

Aceita múltiplos IDs separados por vírgula:
```powershell
python agente/analisar_recorte.py --obra-ids "id1,id2,id3" --recorte "Em execução"
```

## Publicar manualmente (sem rodar pipeline)

```powershell
python agente/publicar.py
```

Faz: atomic write · git push pub repo · wrangler deploy. Detecta sync fail e flag em `pipeline-errors.json`.

## Subir tela local (debug)

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python -m http.server 8765
```

Abrir `http://localhost:8765/` · usa o `index.html` local + `dados/*.json` direto sem auth.

## Backup pré-IA (antes de mexer em obra específica)

```powershell
python agente/arquivar_versao.py --evolucao <obra_id>
```

Salva snapshot pré-mudança da obra X em `dados/historico/`.

## Forçar refresh de detail (quando snapshot defasado)

(detail-snapshot é gerado em outro lugar · cargo-assistente provavelmente)

Workaround manual: deletar `dados/details-snapshot/{id}.json` e rodar coletor antes da varredura.

---

## Debug · receitas comuns

### Card mostra dados incorretos
1. `python agente/sentinela.py` · verifica saúde geral
2. Abrir `dados/discordancias-v3.json` · busca `obra_id` · valida campos
3. Se `telegram.ultima_msg = null` mas devia ter corpus: rodar `python agente/extrair_timeline.py` standalone
4. Se `regua.bucket = null`: rodar `python agente/aplicar_regua.py`

### Varredura quebrou no meio
1. Ler `dados/pipeline-errors.json` · sentinela marca step que falhou
2. Rodar step individual: `python agente/<script>.py`
3. Investigar erro · fix · rodar varredura completa de novo

### Lab Orion não atualiza no browser
1. Confirmar varredura fez `publicar.py` · `git log` no `lab-hermeneuta-pub`
2. Confirmar wrangler deploy: `cd lab-hermeneuta-pub && wrangler deployments list`
3. Se browser cache: Ctrl+F5 (CF retorna `Cache-Control: no-cache` pro index.html mas browser pode segurar)

### Lock travado
- Ver `agente/.varredura.lock` · contém PID
- TTL 30min · expira sozinho
- Se PID morto: varredura próxima reusa
- Se realmente travado: `rm .varredura.lock` (cuidado · só se confirmar sem outra rodando)

### Sentinela cuspindo CRIT falso (drift)
- Drift directional · só CRIT em REGRESSÃO
- Crescimento (mais obras coletadas) = OK
- Se ainda cuspir: ler `sentinela.py:check_drift()` e revisar lógica

---

## Secrets e tokens necessários

| Secret | Onde mora | Pra que serve |
|---|---|---|
| `GITHUB_TOKEN` | Env var local (Vitor) | analisar_recorte.py · GitHub Models API |
| `LAB_USER` + `LAB_PASS` | CF Worker env (lab-hermeneuta-pub) | Basic Auth do `lab.monofloor.cloud` |
| `GH_TOKEN` | CF Worker env (orion-analise · DORMENTE) | Opção B click→IA · pendente reativação |
| `PAT_LAB_PUB` | GitHub Secrets (DORMENTE) | Action analisar-orion · push pub repo |
| `CLOUDFLARE_API_TOKEN` | GitHub Secrets (DORMENTE) | Action wrangler deploy |
| `CLOUDFLARE_ACCOUNT_ID` | GitHub Secrets (DORMENTE) | Action wrangler deploy |

PAT GitHub do Vitor: escopo `repo` · gerar em github.com → Settings → Developer settings → PAT.

---

## Atalhos pessoais

```powershell
# Status quick
python agente/sentinela.py

# Varredura completa
python agente/varredura.py

# Só publica (sem refazer pipeline)
python agente/publicar.py

# IA em 1 obra · storytelling
$env:GITHUB_TOKEN = "$env:GITHUB_TOKEN"  # se já setado
python agente/analisar_recorte.py --obra-ids "<id>" --recorte "manual"
python agente/publicar.py
```

---

## Task Scheduler · varredura automática 12h e 18h

(setup feito previamente · Vitor sabe)

Executa `python agente/varredura.py` em background · log em `agente/varredura.log` · resultado publicado automaticamente em `lab.monofloor.cloud`.
