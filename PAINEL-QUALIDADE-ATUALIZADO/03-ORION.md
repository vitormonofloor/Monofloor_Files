# 03 · Lab Orion

> **URL:** https://orion-pub.vitor-monofloor.workers.dev (Basic Auth)
> **Hospedagem:** Cloudflare Worker
> **Status:** piloto · 10 obras · varredura 12h e 18h

---

## Visão · pra que serve

Lab Orion é o **diferencial qualitativo da Qualidade**. Cruza:

```
   Painel de Obras                Grupos Telegram/WhatsApp
   "diz que a obra está em       "contam que aplicador
    INFORMAÇÕES LOGÍSTICAS"       sumiu há 4 dias"
            └────────────┬────────────┘
                         ▼
                    LAB ORION
                detecta divergência
```

Onde os dois lados divergem, **nasce o problema**. Antes do problema virar caso jurídico ou retrabalho, o Orion sinaliza.

---

## Arquitetura · 2 repositórios sincronizados

```
┌────────────────────────────────────┐
│ Monofloor_Files                    │
│ (canônico · público GitHub)        │
│                                    │
│ analise/lab-hermeneuta/            │
│ ├── index.html ◄── EDITAR AQUI     │
│ ├── dados/                         │
│ │   ├── discordancias-v3.json     │
│ │   ├── historico-kpis.json       │
│ │   └── status.json               │
│ └── agente/                        │
│     ├── varredura.py               │
│     ├── publicar.py ──┐            │
│     └── sentinela.py  │            │
└──────────────────────│─────────────┘
                       │ copia a cada varredura
                       ▼
┌────────────────────────────────────┐
│ lab-hermeneuta-pub                 │
│ (publicado · Cloudflare Worker)    │
│                                    │
│ src/index.js (Worker · Basic Auth) │
│ public/                            │
│ ├── index.html ◄── NÃO editar aqui │
│ ├── dados/...                      │
│ └── login.html (área restrita)     │
│ wrangler.toml                      │
└────────────────────────────────────┘
              │
              ▼
   orion-pub.vitor-monofloor.workers.dev
```

**Princípio firmado:** sempre editar o canônico (`Monofloor_Files`), nunca o pub. Varredura sobrescreve.

---

## O que Orion entrega

### `discordancias-v3.json`
Pra cada uma das 10 obras analisadas:
- **Painel diz:** status atual + fase atual + idade
- **Telegram conta:** última mensagem + dias de silêncio + tom do grupo
- **Veredicto:** coerente · status_desatualizado · em_abandono
- **Tipo de demanda:** retrabalho_acabamento · execução_normal · etc
- **Flags:** detrator_latente · risco_tecnico · cor_personalizada
- **Ação sugerida:** texto narrativo do que consultoria deve fazer

### `resumo_executivo`
Texto narrativo de 5-10 linhas resumindo padrões transversais. Usado direto no Relatório Quinzenal Seção 9.

### `historico-kpis.json`
Acumula KPIs do Orion ao longo do tempo (% coerentes · flags abertas).

### `status.json`
Saúde do sistema · timestamp da última varredura · alertas internos.

---

## Hub do Vitor · ponto de entrada

- **Hub** (`hub.html`) tem card animado com a constelação fiel ao Lab
- **Constelação real do Orion:** viewBox 1280×280 · 18 twinkles + 4 âncoras (Betelgeuse/Bellatrix/Rigel/Saiph) + cinturão de 3 spots (Mintaka/Alnilam/Alnitak) + 6 flare-diag + 3 cores + espada inferior
- **Keyframes:** spotBreathe 7s · flarePulse 6s · coreBreathe 6s · twinklePulse 4s · ancoraPulse 9s · shimmerLine 12-14s · drift 90s
- Ao clicar, transição de 3.5s com a constelação ampliada antes de abrir o login do Orion

---

## Dock cross-tool

Orion, Dashboard e Hub têm **dock vertical na esquerda** com 3 ícones (Central · Dashboard · Orion). Navegação cruzada · 1 clique entre as 3 ferramentas.

---

## Sentinela · varredura automática

Roda 2x/dia (12h e 18h) via Task Scheduler:

1. **`varredura.py`** — coleta dados frescos do Painel (1.038 obras)
2. **`agente/extrair_*.py`** — extrai cores, equipe, KIRA, timeline, consultor
3. **`agente/sanitizar_json.py`** — valida output
4. **`agente/aplicar_regua.py`** — calcula KPIs do Orion
5. **`agente/registrar_kpis.py`** — acumula histórico
6. **`agente/publicar.py`** — copia canônico → pub + git push

Falha silenciosa. Se publicação falhar (rede, conflito), loga aviso mas não aborta a varredura.

---

## Roadmap

- ✅ Piloto 10 obras funcionando
- ⏳ Expansão pra 50 obras em 3 meses
- ⏳ Cores oficiais do catálogo (PENDENTE 2026-05-02 · 12 hex codes faltam)
- ⏳ A/B com Painel · quando divergir, qual fonte está certa?
