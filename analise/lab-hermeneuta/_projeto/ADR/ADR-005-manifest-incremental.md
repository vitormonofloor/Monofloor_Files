# ADR-005 · Timeline Obras · Manifest incremental

**Status:** Aceito
**Data:** 2026-05-07
**Quem decidiu:** Vitor + Claude (sessão escala Timeline)

## Contexto

Rodada cheia da Timeline em 222 obras leva ~2:25min com paralelização. Rodar tudo a cada disparo (cron diário + botão manual) é desperdício porque a maioria das obras não muda dia-a-dia · só algumas dezenas têm `updatedAt` novo.

Painel expõe `updatedAt` ISO no listing · campo perfeito pra detectar "essa obra mudou desde a última rodada".

## Decisão

Persistir `dados/manifest_obras.json`:

```json
{
  "obra_id": {
    "cliente": "...",
    "status": "...",
    "ultimo_updatedAt": "...",
    "processada_em": "..."
  }
}
```

A cada rodada:
1. Fetch lista atual (`?limit=5000`)
2. Filtra universo Qualidade (ADR-004)
3. Compara IDs com manifest:
   - **ID novo** → processa (entrou)
   - **ID sumiu** → marca `arquivada_em` no manifest (status mudou pra final · não processa mais)
   - **ID existente** → compara `updatedAt` · igual = pula · diferente = reprocessa
4. Mescla timelines do output anterior pras inalteradas
5. Atualiza manifest

Resultado validado: primeira rodada 144.7s · subsequente ~5-30s (27× mais rápido).

## Alternativas descartadas

- **Reprocessar tudo sempre** · simples mas desperdício · 144.7s × 24 disparos/dia = inviável pra cron horário
- **Hash de conteúdo das msgs** · bom mas precisa fetch das msgs antes de saber · custa mesmo que reprocessar
- **Cache TTL** · arbitrário · não respeita atividade real da obra
- **Webhook do Painel** · ideal mas Painel não expõe · dependência externa que não controlamos

## Consequências · como saberemos se foi errado

- **Sintoma:** Painel mudar `updatedAt` por motivo bobo (editaram nota) → reprocessamos sem ganho real · custo aceitável (5-10s)
- **Sintoma:** Painel não atualizar `updatedAt` em mudança real (bug deles) → não detectamos · mitigação: rodada de force-refresh manual periódica
- **Sintoma:** manifest crescer indefinidamente com obras arquivadas → adicionar limpeza de arquivadas > 90d sem mudança
- **Sintoma:** corrupção do manifest (JSON inválido) → atual fallback é reprocessar tudo · pode adicionar versionamento

## Memórias relacionadas

- `reference_api_painel_obras.md` · vocabulário do Painel
- `ADR-004` · universo Qualidade 222
