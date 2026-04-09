# CLAUDE.md — Contexto Monofloor

## Idioma
Sempre responda em português brasileiro. Todos os comentários, commits, mensagens e explicações devem ser em PT-BR.

## Quem é o Vitor
**Vitor Gomes** — Gerente de Qualidade da Monofloor. GitHub: `vitormonofloor`. Trabalha com otimização de processos e análise de dados. Está construindo um sistema de gestão operacional completo com assistência do Claude.

## O que é a Monofloor
Empresa de piso de concreto polido (STELION™, LILIT™). Opera em todo o Brasil (SP, RJ, Curitiba). Produtos premium: STELION Piso R$637/m², LILIT Piso R$560/m². Ticket médio 2026: R$150.885. 228 obras ativas.

## Arquitetura de Repositórios

| Repo | Conteúdo | GitHub Pages |
|------|----------|-------------|
| `Monofloor_Files` | POPs, fluxogramas, painel de projeto | vitormonofloor.github.io/Monofloor_Files/ |
| `cargo-assistente` | Portal v10, régua de saúde, relatório financeiro, cérebro | vitormonofloor.github.io/cargo-assistente/ |
| `teleagente` | Bot Telegram @monofloor_op_bot — Railway | teleagente-production.up.railway.app |

## Operação — 5 Fluxos Interdependentes

| Código | Nome | Escopo |
|--------|------|--------|
| OE | Ordem de Execução | Fluxo principal: introdução ao cliente → coleta final (52 etapas) |
| OEC | Ordem de Execução de Cor | Escolha de cores e gestão de amostras (14 etapas) |
| OEI | Ordem de Execução Indústria | Produção, NF, despacho, rastreamento |
| OEL | Ordem de Execução Logística | Ocorrências de entrega e impacto no cronograma |
| OECT | Ordem de Execução Contratos | Proposta aceita → assinatura → finalização (17 etapas) |

**Regra crítica**: OE só inicia após OECT-017 (contrato assinado).

## SLAs — PP:001 (base: Data de Início X)
- VT Aferição: X − 60 dias
- Escolha da Cor: X − 35 dias
- VT Entrada: X − 10 dias
- Definir Equipe: X − 7 dias
- Execução: X + dias definidos pela gerência

## Gargalos Críticos Ativos
- **G1**: 267 amostras presas em "Solicitar Coleta" no pipe CORES — 260 dias avg
- **G2**: 41 cards em AGEND. VT AFERIÇÃO — 163 dias avg — 97% acima do SLA (3% no prazo vs meta 90%)
- **G3**: 28 cards em Aguardando Liberação (depende de G1)
- **G4**: 10 obras pausadas sem motivo registrado (taxa de pausa: 47,6%)
- Ciclo médio end-to-end: 238 dias (meta: ≤150 dias)

## Sistemas
- **Pipefy**: Sistema central. Pipes: OE (306410007), OEC (306446640), OEI (306446401), OECT (306431675)
- **Telegram**: Grupos técnicos de obra + Teleagente @monofloor_op_bot
- **WhatsApp Business**: Grupos de alinhamento com cliente ("Alinhamento obra [NOME]")
- **Omie**: ERP financeiro (⚠ ACESSO PENDENTE — 5/8 indicadores travados)
- **D4Sign**: Assinatura digital de contratos (115 finalizados)
- **planejamento.monofloor.cloud**: API com 228 obras ativas

## Pipefy Token
Token de acesso salvo nas variáveis do projeto. Peça ao Vitor se necessário.

## Teleagente
- Bot: @monofloor_op_bot (ID: 8685770674)
- Railway: projeto `upbeat-wholeness`, URL: teleagente-production.up.railway.app
- VITOR_CHAT_ID: 8151246424
- Comandos: /obras /gargalos /atrasadas /aproveitamento /alerta /status /semana

## GitHub Token
Use a variável de ambiente `GITHUB_TOKEN` ou peça ao Vitor o token atual.

## Bloqueadores Ativos
1. **ANTHROPIC_API_KEY** — trava Cérebro + Teleagente /semana. Criar em console.anthropic.com
2. **Acesso Omie** — trava 5/8 indicadores financeiros
3. **G1 coleta amostras** — 267 cards, 260 dias avg

## Painel de Projeto
Arquivo central: `painel-projeto.html` — 4 abas (Mapa Cerebral, Tarefas, Fluxograma, Hub)
- 8 pilares: Base Conhecimento, Documentação, Infra Digital, Integrações, Automação, Dashboards, Brainstorm, Melhorias
- 62 tarefas com status e dependências

## Arquivos Principais neste Repo (Monofloor_Files)
- `index.html` — Site de POPs (5 POPs + 1 DC publicados)
- `painel-projeto.html` — Painel de projeto completo (4 abas)
- `fluxograma-monofloor.html` — Diagnóstico operacional
- `fluxograma-geral.html` — Fluxo resumido (5 abas: SLAs, Sync, Sistemas, Escalação)
- `fluxograma-macro.html` — Todos os passos do PDF (10 sub-abas)
- `monofloor-dashboard_2.html` — Central operacional Pipefy

## Pessoas-chave
- Vitor Gomes — Qualidade (você está falando com ele)
- Júlio César Bielenki Taporosky — Coordenador Financeiro
- Karine — Assistente Financeiro (DC-FIN-001)
- Kassandra Martinho de Oliveira — Diretoria Operacional
- Nathan, Braiam — VT/Agendamentos
- Cauã Matheus Bezerra da Silva — Auxiliar de Operação
- Maria Eduarda de Oliveira Gomulski — Assistente de RH

## Como trabalhar com o Vitor
- Sempre use códigos OE/OEC/OEI/OEL/OECT para etapas
- Calcule prazos a partir de X (Data de Início da Obra)
- Preferir análise com dados concretos antes de sugerir melhorias
- Classificar melhorias por esforço (baixo/médio/alto)
- Branding: fundo escuro (#0a0a0a), accent dourado (#c4a77d), fonte Inter
- GitHub Pages é a plataforma de publicação
- Publicar outputs no GitHub para compartilhamento
