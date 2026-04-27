# Fórmula do Score de Saúde

> Documenta como o número que aparece no hub e ATENA é calculado.
> Fonte única: `dados/headline.json` (regenerado pelo `refresh.sh`).
> Última revisão: 2026-04-27.

## Filosofia

Score é uma **subtração de penalidades**, não uma soma de méritos. Começa em 100 e perde pontos conforme problemas crescem em proporção à carteira ativa. Os pesos refletem o que **dói mais para a diretoria**.

## Fórmula

```
score = max(0, 100
              - peso_zumbi      × pct_zumbi
              - peso_orfas      × pct_orfas
              - peso_180        × pct_ciclo_180
              - peso_ciclo      × excesso_ciclo
              - peso_lote_vt    × pct_lote_vt)
```

Arredondado para inteiro.

## Componentes

| Componente | Como calcular | Peso atual |
|---|---|---|
| `pct_zumbi` | `n_zumbi / total_ativas × 100` (obras em CLIENTE FINALIZADO sem fechar status) | **0.8** |
| `pct_orfas` | `n_orfas / total_ativas × 100` (obras sem consultor) | **0.5** |
| `pct_ciclo_180` | `n_180_plus / total_ativas × 100` (obras com idade ≥ 180 dias) | **0.2** |
| `excesso_ciclo` | `max(0, (idade_mediana − meta_150) / meta_150) × 100` (% acima da meta de 150 dias) | **0.3** |
| `pct_lote_vt` | `n_lote_vt_270d / total_ativas × 100` (obras presas em AGEND. VT por 258-262 dias) | **0.6** |

## Exemplo (snapshot 27/04/2026)

| Componente | Valor cru | × peso | = penalidade |
|---|---|---|---|
| zumbi | 26/227 = 11.5% | × 0.8 | 9.16 |
| órfãs | 30/227 = 13.2% | × 0.5 | 6.61 |
| ciclo 180+ | 121/227 = 53.3% | × 0.2 | 10.66 |
| ciclo mediano | (206−150)/150 = 37.3% | × 0.3 | 11.20 |
| lote VT | 3/227 = 1.3% | × 0.6 | 0.79 |
| **Total penalidades** | | | **38.42** |
| **Score = 100 − 38.42** | | | **≈ 62** |

## Faixas de cor (uso visual)

| Score | Faixa | Cor |
|---|---|---|
| < 50 | crítico | vermelho `#c45a5a` |
| 50 – 69 | atenção | âmbar `#b89a4a` |
| 70 – 84 | bom | verde claro `#3d8a5a` |
| ≥ 85 | excelente | verde escuro `#2d7a4a` |

## Por que esses pesos

- **Zumbi (0.8)** — obra que aparece como "ativa" mas o cliente já assinou conclusão. Mente o status. Pesa muito porque corrompe TODO outro indicador.
- **Órfãs (0.5)** — obra sem consultor. Tática (atribuir resolve). Peso médio.
- **Ciclo 180+ (0.2)** — pesado em volume mas crônico, não cirúrgico. Peso baixo pra não dominar o score.
- **Excesso ciclo mediano (0.3)** — diretoria olha "quanto tempo realmente leva". Peso médio para refletir.
- **Lote VT (0.6)** — gargalo conhecido (G2). Peso alto porque é nominal, finito e atacável.

## Como ajustar

Editar este arquivo + o bloco `# headline.json` em `refresh.sh`. Sem coordenação dos dois → JSON e doc divergem.

Se quiser componente novo:
1. Calcule a métrica no Python do refresh.sh
2. Adicione em `score_componentes` no `headline.json`
3. Some na fórmula com peso explícito
4. Atualize esta doc
