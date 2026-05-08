# ADR-002 · Tratativas × Retrabalho · classificação operacional

**Status:** Aceito
**Data:** 2026-05-06
**Quem decidiu:** Vitor (definição operacional Monofloor)

## Contexto

Em obras com retrabalho (KRYSTAL exemplo · Ciclo 2 com 143d), a página da Jornada estava categorizando **todo o ciclo 2 como RETRABALHO**. Vitor questionou: dos 143d, só 7d foram trabalho físico real (prestadores aplicando). Os 136d restantes foram visita técnica de qualidade, relatórios, definições, agendamento, acompanhamento.

Misturar tudo como "retrabalho" mente sobre o gargalo real. Operacionalmente, a obra pode ter **demorado** por causa de tratativas administrativas (cliente que não responde, agendamento difícil) e não por dificuldade de execução. Dashboards confundindo isso geram decisão errada.

## Decisão

Separar em duas categorias distintas dentro do ciclo de retrabalho:

- **RETRABALHO** = só dias de fase "Execução" pura (prestadores em obra · mão na massa)
- **TRATATIVAS** = todo o resto do ciclo de retrabalho (Despertar/pré-execução, Pós-execução, Atividade retomada, Hibernação interna)

Implementação no `classificarMacroEtapa()` (jornada.html · backend e frontend) · comparação **igualdade exata** com `n === 'execução'`, não `n.includes('execu')` (porque "pré-execução" e "pós-execução" também contêm "execu" e cairiam por engano).

## Alternativas descartadas

- **Tudo como Retrabalho** · simples mas mente · perdemos o sinal do gargalo administrativo
- **Tudo como Tratativas** · simétrico mas inverte: zera a sinalização de aplicação física nova
- **Categorizar por verbo no texto** · regex sobre msgs · frágil · vocabulário do time muda
- **Coluna binária só "tem retrabalho?"** · perde granularidade temporal · impossível medir gargalo

## Consequências · como saberemos se foi errado

- **Sintoma:** obra com 2 ciclos onde Ciclo 2 não tem fase "Execução" detectada (cluster perdeu a janela) → RETRABALHO=0d engana → revisar detector de cluster
- **Sintoma:** time começar a usar "execução" pra significar reunião/decisão → comparação igualdade quebra · revisar regra
- **Sintoma:** dashboards que somam Tratativas+Retrabalho como "tempo do ciclo de retrabalho" deveriam continuar funcionando (soma é estável)

## Memórias relacionadas

- `reference_tratativas_vs_retrabalho.md` · definição canônica detalhada
- `feedback_retrabalho_separado.md` · status reparo/marcas pós-entrega não conta como atraso
