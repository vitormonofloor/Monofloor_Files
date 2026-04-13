# Mapeamento de Timeline Real — Monofloor
## Data: 13/04/2026 | Fontes: WhatsApp API + Projects API + Fluxograma OE

---

## FLUXO OE: 6 Fases, 52 Etapas

1. ONBOARDING (OE-001 a OE-010) — Introducao, manual, reuniao, cor, data
2. AFERICAO/PROJETO (OE-011 a OE-023) — VT afericao, relatorio, regularizacoes
3. PRE-OBRA (OE-022 a OE-036) — VT entrada, equipe, material, conferencia
4. EXECUCAO (OE-037 a OE-039) — Aplicacao, pausas, diario de obra
5. ENTREGA/VERNIZ (OE-040 a OE-046) — VT entrega, verniz, cura
6. COLETA/ENCERRAMENTO (OE-047 a OE-052) — Coleta material, encerramento

---

## TEMPOS REAIS MEDIDOS

### A. Via API Projects Individual (20 projetos com pipefyCreatedAt)

| Status | Projetos | Pipeline total | Ate VT | VT→Entrada | 
|--------|----------|---------------|--------|------------|
| Finalizado | 5 | **183 dias** | 67d | 131d |
| Em Execucao | 4 | **167 dias** | 25d | 42d |
| Aguardando Exec | 5 | **155 dias** | 79d | 103d |
| Concluido | 5 | **238 dias** | 51d | 39d |
| **MEDIA GERAL** | **20** | **186 dias** | **56d** | **79d** |

### Fluxo real mapeado (186 dias medio):

Pipefy criado --56d--> VT Afericao --79d--> Entrada Obra --17d--> Verniz --3d-- Coleta --5d
    ONBOARDING           PRE-OBRA (BURACO NEGRO 43%)         EM OBRA (9% do total)

| Fase | Dias | % do total |
|------|------|-----------|
| Onboarding → VT Afericao | 56d | 30% |
| VT Afericao → Entrada | **79d** | **43%** (BURACO NEGRO) |
| Execucao | 17d | 9% |
| Verniz + Cura | 3d | 2% (fixo) |
| Coleta/Encerramento | 5d | 3% |
| Pos-obra admin | ~26d | 14% |

### B. Via WhatsApp (3 obras concluidas)

| Projeto | Execucao | Verniz+Cura | Coleta | Total |
|---------|----------|-------------|--------|-------|
| Renato Eid Tucci | 22d (12d pausa) | 3d | 9d | 34d |
| Julia Paiva Heymann | 20d (12d pausa) | 3d | 3d | 40d |
| Mario Sabino Filho | 10d | 3d | 3d | 18d |
| **MEDIA** | **17d** | **3d** | **5d** | **31d** |

### C. Via WhatsApp (3 obras em execucao)

| Projeto | Pre-obra→Exec | Status | Gargalo principal |
|---------|---------------|--------|-------------------|
| Gurgel Dalfonso | 54d | Iniciou 13/04 | 17d gap do cliente |
| Michelle Gardenal | 46d+ | Nao iniciou | 18d sem resposta Monofloor |
| Tally Feldman | 38d+ banco | Em andamento | Clima + promessas quebradas |

### Obras Problematicas (5 analisadas)

| Projeto | Dias | Status | Ponto de quebra |
|---------|------|--------|-----------------|
| Petite Fleur | 35d+ | 80% | Verniz contaminado |
| Flavio Fava | 32d+ | 70% | Contrapiso fragil + trincas |
| Tally Feldman | 39d+ | 85% int | Banco externo 38d por clima |
| Fabio Federici | **59d+** | **0%** | **Cor errada — obra NAO comecou** |
| Manoela Latini | 48d+ | 75% | Interferencia terceiros + danos |

---

## PIPELINE TOTAL (Pipefy → Hoje)

### Dado detalhado: FLAVIO FAVA DITT
- pipefyCreatedAt: 29/07/2025
- Hoje: 13/04/2026
- **Total no pipeline: 259 dias** (meta: 150d)

Marcos Pipefy do FLAVIO (com intervalos):
- Envio manual: 29/05/2025
- pipefyCreatedAt: 29/07/2025 (dia 0)
- VT afericao: 07/08/2025 (+9 dias)
- Relatorio VT: 13/08/2025 (+6 dias)
- 1a visita: 26/08/2025 (+13 dias)
- Nova data: 15/09/2025 (+20 dias)
- VT entrada: 25/02/2026 (+163 dias!) ← GAP CRITICO
- Entrada obra: 09/03/2026 (+12 dias)
- Hoje (em execucao): 13/04/2026 (+35 dias)

**GAP CRITICO: 163 dias entre "nova data" e "VT entrada"**

### Descoberta sobre pipefyCreatedAt
- Campo existe na API individual (/api/projects/{id}) mas NAO na listagem (/api/projects)
- Diferenca entre pipefyCreatedAt e createdAt (portal): ~7,5 meses
- Para tempo real no pipeline: SEMPRE usar pipefyCreatedAt
- Outros marcos Pipefy disponiveis na API individual: envio_do_manuall, data_e_hora_da_visita, data_de_envio_do_relat_rio, 1_visita, visita_de_entrada, data_de_entrada

### Dados confirmados de 3 projetos (API individual)

| Projeto | pipefyCreatedAt | dataExecPrevista | Status | Dias pipeline |
|---------|-----------------|------------------|--------|---------------|
| Flavio Fava | 29/07/2025 | 09/03/2026 | em_execucao | 259d |
| Tally Feldman | 29/07/2025 | 13/11/2025 | aguardando_clima | 259d |
| Manoela Latini | (importado) | 10/02/2026 | em_execucao | 30d+ |

### Obras problematicas (WhatsApp timeline)

| Projeto | Msgs | Dias analise | Status | Ponto de quebra |
|---------|------|-------------|--------|-----------------|
| Petite Fleur | 431 | 35d+ | 80% | Verniz contaminado (cabelo) |
| Flavio Fava | 370 | 32d+ | 70% | Contrapiso fragil + trincas |
| Tally Feldman | 304 | 39d+ | 85% int | Banco externo 38d por clima |
| Fabio Federici | 280 | **59d+** | **0%** | **Cor errada — obra parada** |
| Manoela Latini | 273 | 48d+ | 75% | Terceiros danificam areas |

### 5 acoes corretivas da analise de timeline
1. Amostras no material real (nao MDF) — evita travamento de cor
2. VT com teste de contrapiso obrigatorio — evita retrabalho
3. Protocolo sala limpa para verniz — evita contaminacao
4. SLA 4h comunicacao + escalonamento auto — evita abandono
5. Coberturas provisorias para areas externas — evita parada por clima

---

## 5 PONTOS DE QUEBRA SISTEMICOS

### PQ1: AMOSTRAS DE COR (OEC)
- Amostra em MDF ≠ cor real no material (Stelion/Lilit)
- Fabio Federici: 59d+ travado por isso
- 267 amostras presas em coleta (260 dias avg)
- ACAO: Amostras no material real, nao MDF

### PQ2: VT DE AFERICAO INSUFICIENTE (OE-011)
- Nao detecta: contrapiso fragil, trincas, umidade
- Flavio Fava: trincas em TODA a area
- 46 obras represadas aguardando VT
- SLA: 3% no prazo (meta 90%)
- ACAO: Checklist tecnico obrigatorio com testes

### PQ3: VERNIZ/ACABAMENTO CONTAMINADO
- Impurezas (cabelo, poeira, agua) fixadas no verniz
- Petite Fleur: 23d na fase de acabamento
- Tally: agua contamina vestiario
- ACAO: Protocolo "sala limpa" durante verniz

### PQ4: COMUNICACAO REATIVA (WhatsApp)
- 78% conversas terminam com msg do cliente
- 100% sem responsavel atribuido
- Tempo de resposta: 19h a 7 DIAS em casos criticos
- Michelle: 18 dias de cobranças ate gestora intervir
- ACAO: SLA 4h uteis, escalonamento automatico

### PQ5: DEPENDENCIA CLIMATICA
- Areas externas: 38d+ de atraso (Tally banco)
- Monofloor nao trabalha fins de semana
- Nao aproveita janelas identificadas pelo CLIENTE
- ACAO: Coberturas provisorias + mobilizacao rapida

---

## FASE MAIS PREVISIVEL
Verniz + Cura: **3 dias** (consistente em 100% dos casos)

## FASE MAIS VARIAVEL
Pre-obra ate execucao: **18 a 259 dias**

## PADRAO DE COMUNICACAO
- Obras saudaveis: Monofloor inicia 45-55% das msgs
- Obras problematicas: Cliente inicia 70-75%
- Frequencia por fase: Onboarding 1-2/dia, Execucao 10-20/dia
- Aprovacao interna: 3-9 dias (maior gargalo de comunicacao)
