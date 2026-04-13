#!/bin/bash
# Atualiza data.json com dados ao vivo do painel Monofloor
API="https://cliente.monofloor.cloud/api"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Buscando dados do painel Monofloor..."
P=$(curl -s "$API/projects")
D=$(curl -s "$API/dashboard")
A=$(curl -s "$API/analise")
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "{\"projects\":$P,\"dashboard\":$D,\"analise\":$A,\"fetchedAt\":\"$TS\"}" > "$DIR/data.json"
echo "OK: data.json atualizado ($TS)"
echo "Tamanho: $(wc -c < "$DIR/data.json") bytes"
