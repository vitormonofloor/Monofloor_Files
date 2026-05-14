# E5 — Propostas de melhoria no fluxo operacional

> Baseado na analise de 189 obras iniciadas em 2026.
> Cada proposta tem: evidencia dos dados, hipotese de causa, intervencao sugerida.
> Gerado em 2026-05-14.

---

## Resumo executivo

De 189 obras de 2026, so 8 (4%) seguiram o caminho feliz. 80% das que finalizaram tiveram reprovacao. 44% da carteira esta presa no pre-obra sem nenhuma execucao. A execucao em si e rapida (13-16d) — o problema esta antes e depois dela.

**3 intervencoes de maior impacto:**
1. Destravar pre-obra (44% da carteira parada)
2. Garantir VT antes da execucao (70% das reprovadas nao tiveram VT)
3. Sincronizar material com cronograma (67% recebe material depois da equipe)

---

## Proposta 1 — Destravar pre-obra

**Evidencia:** 83 obras (44%) em pre-obra pura. 19 pararam no contrato, 19 na revisao de escopo, 11 na VT agendada. Mediana 80 dias paradas. 15 obras ha mais de 6 meses sem movimento.

**Hipotese de causa:** Nao ha gatilho que force a transicao de uma etapa pra outra no pre-obra. Contrato assina, card avanca, e ninguem cobra o proximo passo (revisao de escopo, agendamento de VT). O consultor cuida de muitas obras simultaneamente e as que nao tem urgencia do cliente ficam dormindo.

**Intervencao sugerida:**
- Criar alerta operacional simples: obra com contrato assinado ha mais de 30 dias sem proximo marco = flag pro consultor
- Reuniao semanal de desbloqueio: consultor apresenta as 5 obras mais antigas em pre-obra e diz o que falta
- Meta: reduzir mediana de contrato→equipe de 139d pra <90d

---

## Proposta 2 — VT obrigatoria antes da execucao

**Evidencia:** 70% das obras com reprovacao NAO tiveram VT realizada registrada. 47% nem tiveram VT agendada. No caminho feliz (perfil D), 50% tiveram VT — ja e mais que o dobro dos perfis E/F.

**Hipotese de causa:** VT e vista como formalidade, nao como etapa de prevencao. Quando o cronograma aperta, pula a VT pra nao atrasar a execucao. Resultado: problemas que a VT pegaria aparecem como reprovacao 73 dias depois.

**Intervencao sugerida:**
- Tornar VT bloqueante: equipe nao agenda execucao sem VT realizada registrada no Painel
- Se a VT for dispensada (metragem pequena, cliente recorrente), registrar como "VT dispensada" com justificativa — nao simplesmente nao fazer
- Meta: VT registrada em 90%+ das obras que entram em execucao

---

## Proposta 3 — Sincronizar material com cronograma

**Evidencia:** Material produzido/entregue DEPOIS da equipe chegar em 67% das obras. Em 51% das obras com reprovacao, material_produzido esta ausente.

**Hipotese de causa:** Producao de material e disparada pelo contrato (OEI), mas equipe e disparada pelo cronograma (OE). Os dois fluxos correm em paralelo sem ponto de sincronizacao. Equipe chega e material nao esta la — ou material errado, cor errada, quantidade errada.

**Intervencao sugerida:**
- Ponto de checagem: material confirmado em obra ANTES de agendar data de execucao
- OEI deveria ter flag "material entregue" que desbloqueia agendamento de equipe no OE
- Meta: material_entregue registrado antes de equipe_chegou em 80%+ das obras

---

## Proposta 4 — Velocidade equipe→camada como preditor

**Evidencia:** No caminho feliz, equipe→1a camada = 4 dias. Nas obras com reprovacao sem finalizacao (perfil F) = 55 dias. Diferenca de 14x.

**Hipotese de causa:** Quando a equipe chega e comeca rapido, e porque tudo estava pronto (material, escopo, superficie). Quando demora 55 dias entre chegar e aplicar, e porque faltou algo (material, definicao de cor, autorizacao do cliente, superficie nao preparada). Essa demora gera retrabalho — equipe improvisa, aplica sem condicao ideal.

**Intervencao sugerida:**
- Monitorar tempo equipe→1a camada como indicador de saude: >7d = alerta amarelo, >15d = alerta vermelho
- Investigar as 9 obras do perfil F com >30d entre equipe e camada: o que faltou?
- Meta: equipe→camada <7d em 80% das obras

---

## Proposta 5 — Registro de finalizacao e aprovacao

**Evidencia:** Finalizacao ausente em 45% das obras. Aprovacao do cliente ausente em 62%. Em 12 obras, a finalizacao foi registrada DEPOIS da reprovacao (inversao de fluxo).

**Hipotese de causa:** O registro no Painel depende de alguem atualizar o card manualmente. Quando a obra termina no campo, o aplicador avisa no Telegram mas ninguem atualiza o card. O card so muda quando alguem precisa dele (cobranca, relatorio).

**Intervencao sugerida:**
- Aplicador ou lider registra finalizacao no mesmo dia (msg padrao no Telegram tipo "obra finalizada [DATA]" que o bot pode capturar)
- Aprovacao formal do cliente: vistoria final com registro fotografico obrigatorio antes de mudar status pra CLIENTE FINALIZADO
- Meta: finalizacao registrada em <3 dias apos ultima camada

---

## Proposta 6 — Reduzir taxa de reprovacao

**Evidencia:** 80% das obras finalizadas em 2026 tiveram reprovacao. Reprovacao aparece com mediana de 73 dias apos finalizacao.

**Hipotese de causa:** Multiplas causas provaveis (precisaria destrinchar por tipo de reprovacao):
- Defeito de aplicacao que so aparece com uso (marcas, bolhas, desgaste)
- Expectativa do cliente diferente do escopo contratado
- Acabamento que deteriora na cura
- Cliente que demora pra inspecionar e so reclama meses depois

**Intervencao sugerida:**
- Vistoria de qualidade Monofloor 30 dias apos finalizacao (janela critica: 65% das reprovacoes acontecem em fase "concluida")
- Classificar reprovacoes por subtipo (defeito tecnico vs expectativa vs desgaste) pra tratar cada causa separadamente
- Meta: taxa de reprovacao <50% em obras novas (vs 80% atual)

---

## Priorizacao

| # | Proposta | Impacto | Esforco | Prioridade |
|---|---|---|---|---|
| 1 | Destravar pre-obra | Alto (44% da carteira) | Baixo (reuniao + alerta) | **P0** |
| 2 | VT obrigatoria | Alto (correlacao direta com reprovacao) | Medio (mudar processo) | **P0** |
| 3 | Sincronizar material | Medio (67% invertido) | Medio (OEI x OE) | **P1** |
| 4 | Velocidade equipe→camada | Medio (preditor forte) | Baixo (monitorar) | **P1** |
| 5 | Registro finalizacao | Medio (45% ausente) | Baixo (disciplina) | **P2** |
| 6 | Reduzir reprovacao | Alto (80%) | Alto (multiplas causas) | **P2** |
