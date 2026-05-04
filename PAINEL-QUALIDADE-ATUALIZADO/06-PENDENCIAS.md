# 06 · Pendências e Roadmap

> Consolidação de tudo que está em aberto · 2026-05-04
> **Fonte viva:** `Monofloor_Files/analise/relatorios/MELHORIAS-PENDENTES.md`

---

## Por componente

### Dashboard Executivo
- 4 críticos · 5 médios · 5 refinamentos (lista detalhada em `project_pendencias_dashboard.md` na memória)
- 🔥 **Categoria dedicada de RETRABALHOS** (super-prioridade · task #70) — banner provisório no Q4 hoje, mas precisa seção dedicada com lista, top consultores, taxas, tempo médio
- Histórico Score (acumula desde 2026-05-01) · útil em ~7-10 dias
- Cidades com endereço apenas CEP · ~6 obras · banner clicável já avisa, Vitor arruma direto no Painel quando puder
- Funções JS órfãs (renderAchados etc) · código morto inerte · polish posterior

### Lab Orion
- Expansão piloto: 10 → 50 obras em 3 meses
- 🎨 Cores oficiais do catálogo (PENDENTE 2026-05-02) · extrair hex codes reais das 21 cores do PDF · 12 faltam
- Deep-link Dashboard ↔ Orion · modal de obra do Q4 aponta pra `?obra=ID` no Orion

### Hub
- ✅ Nada urgente · constelação fiel ao Lab funcionando

### Relatório Quinzenal · 18 fixes em 3 leituras (já aplicados)
**Pendentes:**
- 🟡 P1 nova (~45min)
  - Cortar Seção 1 (duplica Brief)
  - Consolidar 3 alertas com mesmo padrão em 1 alerta-padrão
  - Cortar 3 destaques que duplicam KPIs
  - Consolidar 32+ "Caminhos a explorar" espalhados
- ✏ P2 nova (~30min)
  - Seção 4 condensada
  - Equipe Michael (9 ativos · 0 lideradas) com nota
  - Resumo Orion em bullets
  - Lab Orion declarar amostra (10 de 260)
  - Anexo A com TOTAL
  - Caixa "Observação da Gerência" · voz humana
  - Tradução de gírias
- 🟢 P2 original (depende de coleta)
  - Comparativo histórico real (precisa 14+ dias)
  - Implicação financeira em R$
  - Top 3 obras de risco pessoal
  - Benchmark de setor
- 🎨 P3 visualização avançada
- 🚀 Fase B · botão no hub
- 🚀 Fase C · bot Telegram quinzenal

---

## Por categoria de tarefa

### 🔥 Super prioridades (Vitor sinalizou)
1. **Categoria de RETRABALHOS** dedicada no dashboard (task #70)
2. **Fuga de dados sensíveis em repo público** (task #43 · S2 ALAVANCA)

### ⭐ Alavancas (impacto alto)
- F1 · Ficha 360° por obra (task #46)
- M2 · Consumir 9 endpoints subutilizados (task #63 · 4 já consumidos pelo Relatório)
- I6 · Princípio "complementar, não duplicar Pipefy" (task #61 · ✅ feito)

### 🔬 Lab "Voz" e expansão Orion
- V6 · Lab "Voz" (filtro narrativo + busca textual · task #57)
- V7 · Lab Jornada enriquecida (relacionado a F1 · task #58)

### 📋 Outros
- Q6 · Amostragem fina cruz-relatorios e ocorrências
- Q7 · Cegueira KIRA: 43% sem WhatsApp
- Q8 · ATENA só lê 4 dos 29 cruz-* (ATENA descontinuado, mas refs podem persistir)
- Q9 · Auditar uso amplo de details/*.json
- I4 · Taxonomia permanente das 49 fases Pipefy
- M1 · Mapa vivo do painel-amigo (cliente.monofloor.cloud)
- M3 · Investigar payload de /api/alerts e /api/checklist
- S3 · cargo-assistente sem .gitignore
- S4 · Avisar amigo: API cliente.monofloor.cloud sem auth
- S5 · SCHEMA.md como contrato formal com amigo
- S6 · Validador de schema no refresh.sh

---

## Backlog vivo do Relatório Quinzenal

Lista detalhada em `Monofloor_Files/analise/relatorios/MELHORIAS-PENDENTES.md`. Hoje:
- ✅ P0 fechada (9 fixes)
- ✅ P0 nova fechada (5 fixes)
- ✅ P0 nova-2 fechada (4 fixes)
- ✅ P1 quase fechada (4 de 5)
- ⏳ P1 nova pendente
- ⏳ P2 nova pendente
- ⏳ P2 original aguardando dados
- ⏳ P3 visualização futuro

---

## Decisões fechadas que não vão mudar (provavelmente)

- **Pipefy descontinuado** · sempre "Painel de Obras"
- **ATENA descontinuado** · absorvido pelo Orion · não recriar
- **Tema claro aprovado** · Plus Jakarta + cream `#f0ebe3` + zero emojis (exceto Q2)
- **Retrabalho separado de atraso** · banner próprio
- **Score 0-100** · faixas 0-49 vermelho · 50-69 amarelo · 70-100 verde
- **Refresh 30min** · latência máxima
- **DNA da dupla** · Vitor + agente exercem Qualidade JUNTOS
