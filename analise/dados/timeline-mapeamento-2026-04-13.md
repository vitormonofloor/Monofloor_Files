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

## TEMPOS REAIS MEDIDOS (Fase de Execucao em diante)

### Obras Concluidas (3 analisadas via WhatsApp)

| Projeto | Execucao | Verniz+Cura | Coleta | Total |
|---------|----------|-------------|--------|-------|
| Renato Eid Tucci | 22d (12d pausa) | 3d | 9d | 34d |
| Julia Paiva Heymann | 20d (12d pausa) | 3d | 3d | 40d |
| Mario Sabino Filho | 10d | 3d | 3d | 18d |
| **MEDIA** | **17d** | **3d** | **5d** | **31d** |

### Obras em Execucao (3 analisadas)

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

Dado de exemplo: FLAVIO FAVA DITT
- pipefyCreatedAt: 29/07/2025
- Hoje: 13/04/2026
- **Total no pipeline: 259 dias** (meta: 150d)

Marcos Pipefy do FLAVIO:
- Envio manual: 29/05/2025
- VT afericao: 07/08/2025 (70 dias apos criacao)
- Relatorio VT: 13/08/2025 (6 dias apos VT)
- 1a visita: 26/08/2025 (13 dias apos relatorio)
- Nova data: 15/09/2025 (20 dias apos visita)
- VT entrada: 25/02/2026 (163 dias apos nova data!)
- Entrada obra: 09/03/2026 (12 dias apos VT entrada)

**GAP CRITICO: 163 dias entre "nova data" e "VT entrada"**

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
