# RETOMAR — Analise de Execucao por Faixa

Ultima atualizacao: 2026-05-21

## SESSAO 2026-05-21 · O QUE FECHAMOS HOJE

**O que foi fechado:**
- Analise de execucao por faixa de metragem completa (analise_execucao.py)
- Corte temporal >= 2026-01-01 (100 obras, era 169)
- 3 abas: Finalizadas / Em execucao / Retrabalho
- Proporcao retorno dentro dos totais (limpas vs com retorno) em KPIs e cards por faixa
- Tabelas separadas: "Obras com retorno" (borda vermelha) + "Entregas limpas" (borda verde)
- Auditoria das 20 "limpas": 2 falsos negativos corrigidos (Ariane Ribeiro, Dona Corina)
- Novo criterio de deteccao: n_blocos >= 2 (gap > 14d entre camadas = retorno)

**Numeros auditados (2026+):**
- 100 obras com dados | 25 finalizadas (18 limpas + 7 com retorno = 28%)
- Mediana total: 19d | Limpa: 13d | Com retorno: 33d | Impacto: +9.7d
- Em campo: 22 (16 exec + 6 retrab)

**Arquivos:**
- Script: `analise/dados/analise_execucao.py` (fonte canonica)
- JSON: `analise/dados/execucao-por-faixa.json` (output, 83 KB)
- HTML: `analise/execucao.html` (output, 67 KB)
- Servir: `python -m http.server 8080 --directory analise`

**Memorias novas:**
- feedback_corte_temporal_obras_historico.md (atualizado: agora inclui corte execucao >= jan/2026)
- reference_deteccao_retorno_blocos.md (novo: n_blocos >= 2)

**Pendencias proxima sessao:**
- Investigar macrodados consultor vs sem consultor (~2h)
- Limpar _tmp_*.py em analise/dados/ e analise/lab-hermeneuta/ (~5min)
- Considerar integrar execucao.html na Central de Qualidade como painel adicional (~1h)

**Comando pra retomar:**
```
Retomar analise de execucao por faixa. Ler analise/dados/RETOMAR_EXECUCAO.md. Script em analise/dados/analise_execucao.py, output em analise/execucao.html. Corte 2026+, 100 obras, auditadas. Servir com python -m http.server 8080 --directory analise.
```
