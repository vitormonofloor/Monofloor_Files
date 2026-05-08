# ADR-004 · Timeline Obras · Universo D (222 vivas, exclui cancelado)

**Status:** Aceito
**Data:** 2026-05-07
**Quem decidiu:** Vitor + Claude (sessão escala Timeline)

## Contexto

Pra escalar Timeline de 10 obras-piloto pra rodada cheia, precisava definir o universo. Bloqueio descoberto: API `/api/projects?ativa=true` retornava 200 obras (paginação default · `ativa=true` ignorado), mas Painel UI mostrava 257.

Investigação revelou:
- **Universo total:** 1042 obras (com `?limit=5000`)
- **Critério UI "ativa":** todas exceto `finalizado` e `concluido` = 257 (inclui 35 canceladas)
- **Status "vivos" reais (Qualidade):** exclui também `cancelado` = 222 obras

Cancelado é flag administrativa que o Painel inclui em "ativa" por convenção interna · pra análise de Qualidade isso polui (obras canceladas não têm processo a auditar).

## Decisão

Universo padrão da Timeline = **222 obras vivas reais**:

```python
STATUS_VIVOS_QUALIDADE = {
    'planejamento', 'aguardando_execucao', 'em_execucao', 'reparo',
    'contrato', 'pausado', 'marcas_rolo_cera', 'aguardando_clima',
}
```

Chamada de API obrigatória com `?limit=5000` · filtragem local por status (nunca confiar em `?ativa=true`).

## Alternativas descartadas

- **Universo total 1042** · custo alto (~30-90min processamento), sem foco · finalizadas têm pouco valor pra dashboard de "está acontecendo agora"
- **257 (critério UI)** · inclui 35 canceladas que não acrescentam · poluição de dados
- **Vivas + finalizadas com retrabalho/marcas** (~245-250) · boa ideia, fica como upgrade futuro · Fase 2 do escalonamento
- **Filtrar por status na API** · API ignora · não dá

## Consequências · como saberemos se foi errado

- **Sintoma:** obra cancelada por engano (status mudou pra cancelado mas operação não fechou) → sumiu do nosso universo → revisar critério ou criar fluxo de "cancelamento questionável"
- **Sintoma:** Painel adicionar status novo (ex: `revisao_legal`) → não estamos no `STATUS_VIVOS_QUALIDADE` · vamos perder · adicionar
- **Sintoma:** finalizadas recentes com retrabalho aparecendo no Painel UI mas fora da nossa Timeline → usuários pedindo "cadê fulano que acabou de fechar com problema" → expandir universo

## Memórias relacionadas

- `reference_api_painel_obras.md` · vocabulário completo da API
- `project_timeline_obras_2026_05_06.md` · contexto pleno
