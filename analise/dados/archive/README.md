# Cruzamentos arquivados

Esta pasta contém **8 cruz-*.json** que foram retirados do diretório principal `dados/` na FASE 7.1 do overhaul (2026-04-27).

## Critério de arquivamento

JSONs **não consumidos por nenhum painel HTML** — apenas mencionados em `plano.html` como referência narrativa de cruzamentos já produzidos.

## Arquivos aqui

| Arquivo | Tamanho | Última atualização | Conteúdo |
|---|---|---|---|
| `cruz-receita-risco.json` | 268 KB | 16/04 | obras × receita estimada vs risco operacional · sem consumidor |
| `cruz-equipes-fantasma.json` | 118 KB | 16/04 | aplicadores escalados sem cadastro em /api/equipes |
| `cruz-aplicadores-carga.json` | 73 KB | 16/04 | distribuição de carga entre aplicadores |
| `cruz-idade-fase.json` | 32 KB | 15/04 | idade média/p90 por fase do Pipefy |
| `cruz-limbo.json` | 27 KB | 15/04 | obras em fase de transição há > 60 dias |
| `cruz-luana-vs-wesley.json` | 14 KB | 15/04 | comparativo entre os 2 consultores top |
| `cruz-idade-geo.json` | 10 KB | 15/04 | idade média por cidade/UF |
| `cruz-idade-metragem.json` | 7 KB | 15/04 | correlação m² vs idade da obra |

**Total: ~565 KB** liberados do diretório principal.

## Como restaurar

Se precisar reativar algum:

```bash
git mv analise/dados/archive/cruz-X.json analise/dados/cruz-X.json
```

E adicionar o consumidor (HTML/JS) que vai usar.

## Por que arquivar e não deletar?

Arquivar (mover para `archive/`) preserva o histórico e permite restauração imediata. Deletar perderia o trabalho de extração que pode ser útil em análises futuras.
