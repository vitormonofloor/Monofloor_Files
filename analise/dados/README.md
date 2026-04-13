# Dados do Painel de Auditoria Monofloor

## Snapshots
- `snapshot-2026-04-13.json` — Primeiro snapshot com 200 projetos, dashboard e analise

## Como atualizar
```bash
bash analise/fetch-data.sh
cp analise/data.json analise/dados/snapshot-$(date +%Y-%m-%d).json
git add -A && git commit -m "📊 update dados" && git push
```

## Estrutura do JSON
```
{
  "projects": [...],      // Array de projetos (id, clienteNome, metragem, status, fase, datas)
  "dashboard": {...},     // KPIs, SLAs (8 etapas), fases, ocorrencias, NPS
  "analise": {...},       // atRisk (50 obras com diagnostico), problemCategories (11), recentEvents (30), teamPerformance (6), summary
  "fetchedAt": "ISO date" // Timestamp da coleta
}
```

## APIs fonte
- `GET https://cliente.monofloor.cloud/api/projects`
- `GET https://cliente.monofloor.cloud/api/dashboard`
- `GET https://cliente.monofloor.cloud/api/analise`
