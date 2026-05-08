# 📋 ADR · Architecture Decision Records

> Captura formal das decisões grandes tomadas no Lab Orion e periféricos · padrão consagrado em engenharia.
> Cada ADR vive até ser **superado** por outro ADR · histórico permanece pra auditoria.

## Por quê

Sem ADR, decisões grandes ficam dispersas em memórias e conversas. Quem chega depois (outro Claude, outro humano, eu mesmo daqui a 6 meses) não sabe:
- O que **descartamos** e por quê (e portanto não retoma à toa)
- **Como saberemos** se a decisão foi errada (critério de revisão)
- Em que **contexto** a decisão fez sentido (contexto muda, decisão pode ficar obsoleta)

## Template

Cada ADR é 1 arquivo `ADR-NNN-titulo-curto.md` · 30-40 linhas no máximo.

```markdown
# ADR-NNN · Título da decisão

**Status:** Aceito · Superado por ADR-XXX · Descartado
**Data:** 2026-MM-DD
**Quem decidiu:** Vitor + Claude (sessão XYZ)

## Contexto
2-4 linhas · o problema que motivou a decisão

## Decisão
1-2 linhas · o que decidimos fazer

## Alternativas descartadas
- **Opção A** · por que descartamos
- **Opção B** · por que descartamos

## Consequências · como saberemos se foi errado
- Sintoma X aparece → revisar
- Sintoma Y aparece → revisar

## Memórias relacionadas
- ponteiro
```

## Índice

| ID | Título | Status | Data |
|---|---|---|---|
| [ADR-001](ADR-001-kira-driven-vs-ia-externa.md) | Lab Orion · Kira-driven em vez de IA externa | Aceito | 2026-05-05 |
| [ADR-002](ADR-002-tratativas-vs-retrabalho.md) | Tratativas × Retrabalho · classificação operacional | Aceito | 2026-05-06 |
| [ADR-003](ADR-003-macro-etapas-5-categorias.md) | Lab Orion · Macro-etapas em 5 categorias | Aceito | 2026-05-06 |
| [ADR-004](ADR-004-universo-qualidade-222-vivas.md) | Timeline Obras · Universo D (222 vivas, exclui cancelado) | Aceito | 2026-05-07 |
| [ADR-005](ADR-005-manifest-incremental.md) | Timeline Obras · Manifest incremental | Aceito | 2026-05-07 |
| [ADR-006](ADR-006-disparo-hibrido-cron-botao.md) | Timeline Obras · Disparo híbrido (cron + botão) | Aceito | 2026-05-07 |
| [ADR-007](ADR-007-atena-descontinuado.md) | ATENA descontinuado · absorvido pelo Lab Orion | Aceito | 2026-05-01 |

## Quando criar ADR novo

Disparar criação quando uma decisão satisfaz 2+ critérios:
- **Reversível com alto custo** · voltar atrás vai exigir refactor não-trivial
- **Tem alternativa real** · houve outra opção razoável que descartamos
- **Afeta arquitetura** · mexe em pipeline, schema, contrato de dados, fluxo de processamento
- **Decisão filosófica** · separação conceitual (ex: Tratativas vs Retrabalho), corte temporal, escolha de fonte canônica

NÃO criar ADR pra:
- Escolha de cor/CSS
- Detalhe de implementação que não generaliza
- Bug fix
- Refator de função

## Como superar ADR

Se uma decisão é revisitada e mudada:
1. Cria ADR novo · explica contexto novo + por que mudou
2. Atualiza ADR antigo: `Status: Superado por ADR-NNN`
3. NÃO deleta o antigo · histórico permanece auditável
