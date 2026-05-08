# ADR-006 · Timeline Obras · Disparo híbrido (cron + botão)

**Status:** Aceito
**Data:** 2026-05-07
**Quem decidiu:** Vitor + Claude (sessão escala Timeline)

## Contexto

Com manifest incremental funcionando (ADR-005), precisava decidir COMO disparar a rodada · mantendo a ferramenta atualizada sem dependência de Vitor lembrar de rodar.

Restrições:
- Vitor **não gosta de GitHub Actions** (Lab Orion teve zebra com isso)
- Site é estático (Cloudflare Worker · sem backend)
- PC do Vitor pode ter modo suspensão · cron pode falhar

## Decisão

Disparo híbrido em duas camadas:

**1. Cron Windows (passivo · base)**
- Task Scheduler "Monofloor_Timeline_Obras"
- Roda diariamente 04:00 (zero tráfego API · nada conflita)
- Wrapper batch `agente/cron_timeline_obras.bat` faz: `cd` + `timeline_10obras.py --massa` + `gerar_html_timelines.py`
- Settings com `StartWhenAvailable + AllowStartIfOnBatteries + DontStopIfGoingOnBatteries` (resiliente a PC desligado · pega na primeira oportunidade)
- Log em `dados/cron_timeline_obras.log`

**2. Botão "↻ Atualizar agora" (ativo · sob demanda)**
- No header do HTML
- Click copia comando completo pro clipboard
- Vitor cola no terminal · roda imediato
- Mesmo padrão do "Atualizar dados Orion" já estabelecido

## Alternativas descartadas

- **Só cron (passivo)** · se PC ficar offline 1 semana, dado fica velho até voltar · sem refresh manual rápido
- **Só botão (ativo)** · depende de Vitor lembrar · dado fica velho se ele esquecer
- **GitHub Actions** · vetado por Vitor (incidente prévio)
- **Cloudflare Worker que roda script remoto** · Worker não roda Python · precisaria infraestrutura nova
- **Botão dispara via Worker → API local** · sem auth-flow · risco de exposição

## Consequências · como saberemos se foi errado

- **Sintoma:** PC do Vitor ficar offline 7+ dias sem refresh manual → dado defasado · monitorar log `cron_timeline_obras.log`
- **Sintoma:** Task Scheduler falhar silenciosamente → adicionar verificação no botão "data da última rodada · alerta se > 24h"
- **Sintoma:** Vitor parar de usar o botão por hábito · só esperar cron → tempo de update piora · medir no manifest "última atualização"
- **Sintoma:** outras pessoas (Rodrigo, Caroline) começarem a usar Lab Orion → necessidade de centralizar disparo · revisitar GitHub Actions ou Worker (com auth)

## Memórias relacionadas

- `reference_orion_atualizar_dados.md` · padrão "botão copia comando" estabelecido antes
- `project_orion_opcao_b_pausada.md` · automação click→IA dormente (mesma lógica de "esperar usuário externo aparecer")
- `ADR-005` · manifest que torna o cron eficiente
