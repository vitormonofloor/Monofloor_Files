[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'

$d = 'C:/Users/vitor/Monofloor_Files/analise/dados/'
$out = 'C:/Users/vitor/Monofloor_Files/analise/obras-mapa.html'

function Read-Json($f) {
  $raw = [System.IO.File]::ReadAllText($d + $f, [System.Text.Encoding]::UTF8)
  return $raw | ConvertFrom-Json
}

function Norm($s) {
  if ($null -eq $s) { return '' }
  $s = "$s".Trim()
  $s = $s.ToUpperInvariant()
  $s = $s -replace '[^A-Z0-9]', ''
  return $s
}

# --- carregar fontes ---
$painel       = Read-Json 'painel-temporal.json'
$plimit       = Read-Json 'p_limit.json'
$zumbi        = Read-Json 'cruz-zumbi.json'
$orfas        = Read-Json 'cruz-orfas.json'
$vt           = Read-Json 'cruz-agend-vt.json'
$silencio     = Read-Json 'cruz-silenciosas.json'
$cores        = Read-Json 'cruz-cores.json'
$fossil       = Read-Json 'cruz-cronograma-fossil.json'
$alertas      = Read-Json 'cruz-alertas.json'
$ocorrencias  = Read-Json 'cruz-ocorrencias.json'
$reparo       = Read-Json 'cruz-reparo.json'
$escalacao    = Read-Json 'cruz-escalacao.json'

# --- indexes ---
$ativas = $painel | Where-Object { $_.ativa -eq $true }
Write-Host "Total ativas: $($ativas.Count)"

# zumbi (id_curto)
$setZumbi = @{}
foreach ($x in $zumbi.zumbi_real_lista) { $setZumbi[$x.id_curto] = $true }
# todas candidatas zumbi (suspeitas)
$setSuspeitaZumbi = @{}
foreach ($x in $zumbi.todas_candidatas) { $setSuspeitaZumbi[$x.id_curto] = $x }

# órfãs (id full)
$setOrfa = @{}
foreach ($x in $orfas.obras) { $setOrfa[$x.id] = $true; $setOrfa[$x.id_curto] = $true }

# cauda VT (id_curto)
$setCaudaVt = @{}
foreach ($x in $vt.cauda_longa_detalhe) { $setCaudaVt[$x.id_curto] = $true }

# silenciosas (cliente+consultor) - top 20 detalhado
$setSilenciosa = @{}
$mapClima = @{}
foreach ($x in $silencio.top20_criticas) {
  $k = (Norm $x.cliente) + '|' + (Norm $x.consultor)
  $setSilenciosa[$k] = $true
  $mapClima[$k] = $x.climaGeral
}

# mapeamento extra: ler details das obras ativas para aferir tagKira (sinal de atividade WA)
# obras ativas SEM tagKira => silenciosas/sem WA real
$detailsDir = $d + 'details/'
$mapTagKira = @{}
foreach ($o in ($painel | Where-Object { $_.ativa -eq $true })) {
  $detPath = $detailsDir + $o.id + '.json'
  if (Test-Path $detPath) {
    try {
      $rawD = [System.IO.File]::ReadAllText($detPath, [System.Text.Encoding]::UTF8)
      $det = $rawD | ConvertFrom-Json
      $hasTag = ($null -ne $det.tagKira -and "$($det.tagKira)".Trim() -ne '')
      $hasSit = ($null -ne $det.situacaoAtual -and "$($det.situacaoAtual)".Trim() -ne '')
      $mapTagKira[$o.id] = [PSCustomObject]@{
        tagKira = $det.tagKira
        situacaoAtual = $det.situacaoAtual
        responsavelOperacoes = $det.responsavelOperacoes
        hasWaSignal = ($hasTag -or $hasSit)
      }
    } catch { }
  }
}

# cores top20 (id full) — para detail (lista de cores + categoria)
$setSemCor = @{}
foreach ($x in $cores.top20_criticas) { $setSemCor[$x.id] = $x }

# Map id -> projetoCores (de p_limit.json) — fonte real para flag SEM_COR
$mapCores = @{}
foreach ($p in $plimit) {
  $coresVal = $p.projetoCores
  $isSemCor = $false
  $coresArr = @()
  if ($null -eq $coresVal) { $isSemCor = $true }
  elseif ($coresVal -is [array]) {
    if ($coresVal.Count -eq 0) { $isSemCor = $true }
    else {
      $coresArr = @($coresVal | ForEach-Object { "$_" })
      $isPlaceholder = $true
      foreach ($c in $coresArr) {
        $cu = $c.ToUpperInvariant().Trim()
        if ($cu -ne 'À DEFINIR' -and $cu -ne 'A DEFINIR' -and $cu -ne '') { $isPlaceholder = $false; break }
      }
      if ($isPlaceholder) { $isSemCor = $true }
    }
  }
  else {
    $cs = "$coresVal".Trim().ToUpperInvariant()
    if ($cs -eq '' -or $cs -eq 'À DEFINIR' -or $cs -eq 'A DEFINIR') { $isSemCor = $true }
    else { $coresArr = @("$coresVal") }
  }
  $mapCores[$p.id] = [PSCustomObject]@{ semCor = $isSemCor; cores = $coresArr }
}

# cronograma fossil — atrasadas com painel ativa
$mapAtraso = @{}
foreach ($x in $fossil.detalhado) {
  if ($x.painel_ativa -eq $true -and $x.painel_id) {
    $mapAtraso[$x.painel_id] = $x
  }
}

# alertas (id full) — top20 por qtd
$mapAlertas = @{}
foreach ($x in $alertas.top20_mais_alertas_qtd) { $mapAlertas[$x.id] = $x }
foreach ($x in $alertas.top20_mais_criticas_risco_adiamento_idade_gt_180) {
  if (-not $mapAlertas.ContainsKey($x.id)) { $mapAlertas[$x.id] = $x }
}

# atRisk (id full)
$mapAtRisk = @{}
foreach ($x in $ocorrencias.atRisk_detalhe) { $mapAtRisk[$x.id] = $x }

# escalação anômala (id_curto)
$setEscalAnomala = @{}
foreach ($x in $escalacao.anomalas) { $setEscalAnomala[$x.id_curto] = $x }
$setEmExecSemEscal = @{}
foreach ($x in $escalacao.em_execucao_sem_escalacao) { $setEmExecSemEscal[$x.id_curto] = $true }

# reparo lista (cliente+consultor)
$setReparoCoerente = @{}
foreach ($x in $reparo.lista_completa) {
  $k = (Norm $x.cliente) + '|' + (Norm $x.consultor)
  $setReparoCoerente[$k] = $x
}

# --- montar consolidado ---
$obras = @()
foreach ($o in $ativas) {
  $idCurto = $o.id.Substring(0, 8)
  $kCC = (Norm $o.clienteNome) + '|' + (Norm $o.consultorNome)

  $flagZumbi      = [bool]$setZumbi[$idCurto]
  $flagOrfa       = [bool]$setOrfa[$o.id]
  $coresPL = $mapCores[$o.id]
  $flagSemCor     = if ($coresPL) { $coresPL.semCor } else { $false }
  $tagInfo        = $mapTagKira[$o.id]
  $flagSemWa      = [bool]$setSilenciosa[$kCC]
  $flagCaudaVt    = [bool]$setCaudaVt[$idCurto]
  $atraso         = $mapAtraso[$o.id]
  $flagAtraso     = ($null -ne $atraso)
  $flagAtrasoGrave= ($flagAtraso -and $atraso.diasAtraso -gt 90)
  $alt            = $mapAlertas[$o.id]
  $flagAlerta     = ($null -ne $alt)
  $atR            = $mapAtRisk[$o.id]
  $flagAtRisk     = ($null -ne $atR)
  $flagReparo     = ($o.status -eq 'reparo')
  $flagEscalAnom  = [bool]$setEscalAnomala[$idCurto]
  $flagSemEscal   = [bool]$setEmExecSemEscal[$idCurto]
  $reparoInfo     = $setReparoCoerente[$kCC]

  # cor first name
  $consultorFirst = ''
  if ($o.consultorNome) {
    $tmp = "$($o.consultorNome)".Trim()
    $consultorFirst = ($tmp -split '\s+')[0]
  }

  # UF
  $uf = ''
  if ($o.projetoCidade) {
    $m = [regex]::Match("$($o.projetoCidade)", '\b([A-Z]{2})\b')
    if ($m.Success) { $uf = $m.Groups[1].Value }
  }

  # listar alertas curtos
  $alertasArr = @()
  if ($alt -and $alt.alertas) { $alertasArr = $alt.alertas }
  $alertasCat = @()
  if ($alt -and $alt.categorias) { $alertasCat = $alt.categorias }

  # diagnostico head
  $diagHead = ''
  if ($atR -and $atR.diagnostico_head) { $diagHead = $atR.diagnostico_head }

  $criticalProb = $null
  $openProb = $null
  $diasAtrR = $null
  if ($atR) {
    $criticalProb = $atR.criticalProblems
    $openProb = $atR.openProblems
    $diasAtrR = $atR.diasAtraso
  }

  # responsavelOps: priorizar detail, fallback reparo
  $respOps = ''
  if ($tagInfo -and $tagInfo.responsavelOperacoes) { $respOps = "$($tagInfo.responsavelOperacoes)" }
  elseif ($reparoInfo) { $respOps = "$($reparoInfo.responsavelOperacoes)" }

  $metragem = $null
  if ($o.projetoMetragem) {
    try { $metragem = [double]"$($o.projetoMetragem)" } catch { $metragem = $null }
  }

  $obras += [PSCustomObject]@{
    id              = $o.id
    pipefyCardId    = $o.pipefyCardId
    cliente         = ("$($o.clienteNome)").Trim()
    cidade          = ("$($o.projetoCidade)").Trim()
    uf              = $uf
    status          = $o.status
    fase            = $o.faseAtual
    consultor       = $o.consultorNome
    consultorFirst  = $consultorFirst
    metragem        = $metragem
    idade           = $o.idade_dias
    dataRadar       = $o.data_radar
    radarFonte      = $o.data_radar_fonte
    flagZumbi       = $flagZumbi
    flagReparo      = $flagReparo
    flagOrfa        = $flagOrfa
    flagSemCor      = $flagSemCor
    flagSemWa       = $flagSemWa
    flagCaudaVt     = $flagCaudaVt
    flagAtraso      = $flagAtraso
    flagAtrasoGrave = $flagAtrasoGrave
    flagAlerta      = $flagAlerta
    flagAtRisk      = $flagAtRisk
    flagEscalAnom   = $flagEscalAnom
    flagSemEscal    = $flagSemEscal
    qtdAlertas      = if ($alt) { $alt.qtd_alertas } else { 0 }
    alertas         = $alertasArr
    alertasCat      = $alertasCat
    diagnostico     = $diagHead
    criticalProblems = $criticalProb
    openProblems     = $openProb
    diasAtrasoOcor   = $diasAtrR
    diasAtrasoCron   = if ($atraso) { $atraso.diasAtraso } else { $null }
    catAtraso        = if ($atraso) { $atraso.categoria } else { $null }
    responsavelOps   = $respOps
    climaGeral       = $mapClima[$kCC]
    tagKira          = if ($tagInfo) { $tagInfo.tagKira } else { $null }
    situacaoAtual    = if ($tagInfo) { $tagInfo.situacaoAtual } else { $null }
    coresList        = if ($coresPL -and $coresPL.cores -and $coresPL.cores.Count -gt 0) { $coresPL.cores } elseif ($setSemCor[$o.id]) { $setSemCor[$o.id].cores } else { @() }
    catCor           = if ($setSemCor[$o.id]) { $setSemCor[$o.id].categoria } elseif ($flagSemCor) { 'SEM_COR' } else { 'DEFINIDA' }
  }
}

# --- métricas ---
$total = $obras.Count
$comData = ($obras | Where-Object { $_.dataRadar }).Count
$idades = $obras | Where-Object { $_.idade -ne $null } | ForEach-Object { $_.idade }
$idadeMedia = if ($idades.Count -gt 0) { [Math]::Round(($idades | Measure-Object -Average).Average, 0) } else { 0 }
$idadeMax   = if ($idades.Count -gt 0) { ($idades | Measure-Object -Maximum).Maximum } else { 0 }
$n180 = ($obras | Where-Object { $_.idade -ge 180 }).Count
$n270 = ($obras | Where-Object { $_.idade -ge 270 }).Count

# resumo por flag
$rf = [PSCustomObject]@{
  zumbi       = ($obras | Where-Object { $_.flagZumbi }).Count
  reparo      = ($obras | Where-Object { $_.flagReparo }).Count
  orfa        = ($obras | Where-Object { $_.flagOrfa }).Count
  semCor      = ($obras | Where-Object { $_.flagSemCor }).Count
  semWa       = ($obras | Where-Object { $_.flagSemWa }).Count
  caudaVt     = ($obras | Where-Object { $_.flagCaudaVt }).Count
  atraso      = ($obras | Where-Object { $_.flagAtraso }).Count
  atrasoGrave = ($obras | Where-Object { $_.flagAtrasoGrave }).Count
  alerta      = ($obras | Where-Object { $_.flagAlerta }).Count
  atRisk      = ($obras | Where-Object { $_.flagAtRisk }).Count
  escalAnom   = ($obras | Where-Object { $_.flagEscalAnom }).Count
  semEscal    = ($obras | Where-Object { $_.flagSemEscal }).Count
}

Write-Host "Resumo flags:"
$rf.PSObject.Properties | ForEach-Object { Write-Host ("  $($_.Name): $($_.Value)") }

# --- métricas para header ---
$meta = [PSCustomObject]@{
  total       = $total
  comData     = $comData
  idadeMedia  = $idadeMedia
  idadeMax    = $idadeMax
  n180        = $n180
  n270        = $n270
  ultAtual    = '2026-04-15'
  resumo      = $rf
}

# --- gerar HTML ---
$obrasJson = $obras | ConvertTo-Json -Depth 8 -Compress
$metaJson  = $meta  | ConvertTo-Json -Depth 5 -Compress

# escapar </script para não fechar tag prematuramente
$obrasJson = $obrasJson.Replace('</script', '<\/script')
$metaJson  = $metaJson.Replace('</script', '<\/script')

# carregar template e substituir placeholders
$tplPath = 'C:/Users/vitor/Monofloor_Files/analise/mapa-template.html'
$html = [System.IO.File]::ReadAllText($tplPath, [System.Text.Encoding]::UTF8)
$html = $html.Replace('__META_JSON__', $metaJson)
$html = $html.Replace('__OBRAS_JSON__', $obrasJson)

$_DEAD_HEREDOC_START_ = @"
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mapa de Obras Ativas — Monofloor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0a;
    --card: #0d0d0d;
    --card-2: #111;
    --border: #1f1f1f;
    --border-2: #2a2a2a;
    --text: #e8e8e8;
    --muted: #888;
    --muted-2: #555;
    --accent: #c4a77d;
    --green: #7be8a8;
    --amber: #e8c87b;
    --red: #e87b7b;
    --scarlet: #ff5252;
    --blue: #7ba8e8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, sans-serif; font-size: 13px; line-height: 1.45; -webkit-font-smoothing: antialiased; }
  .mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* header */
  header.top {
    position: sticky; top: 0; z-index: 30;
    background: var(--card); border-bottom: 1px solid var(--border);
    padding: 16px 24px;
  }
  .top-row { display: flex; justify-content: space-between; align-items: baseline; gap: 24px; flex-wrap: wrap; }
  .top h1 { font-size: 16px; font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
  .top h1 span.acc { color: var(--accent); }
  .top .stamp { font-size: 11px; color: var(--muted); }
  .stamp .mono { color: var(--text); }

  .metrics { display: flex; gap: 20px; margin-top: 12px; flex-wrap: wrap; }
  .metric { display: flex; flex-direction: column; gap: 2px; }
  .metric .lbl { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
  .metric .val { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 600; color: var(--text); }
  .metric .val.warn { color: var(--amber); }
  .metric .val.crit { color: var(--red); }

  /* filters */
  .filters {
    position: sticky; top: 124px; z-index: 25;
    background: var(--card); border-bottom: 1px solid var(--border);
    padding: 12px 24px;
  }
  .filters-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .filters input, .filters select {
    background: var(--bg); border: 1px solid var(--border-2); color: var(--text);
    padding: 6px 10px; font-family: 'Inter', sans-serif; font-size: 12px; border-radius: 3px;
    outline: none; transition: border-color .15s;
  }
  .filters input:focus, .filters select:focus { border-color: var(--accent); }
  .filters input { min-width: 220px; }
  .filters select { min-width: 130px; }

  .toggles { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
  .toggle {
    background: transparent; border: 1px solid var(--border-2); color: var(--muted);
    padding: 4px 10px; font-size: 11px; font-family: 'Inter'; cursor: pointer;
    border-radius: 3px; letter-spacing: 0.04em; text-transform: uppercase;
    transition: all .15s;
  }
  .toggle:hover { color: var(--text); border-color: var(--border-2); }
  .toggle.active { background: var(--accent); color: #0a0a0a; border-color: var(--accent); }
  .clear-btn {
    background: transparent; border: 1px solid var(--border-2); color: var(--muted);
    padding: 4px 10px; font-size: 11px; cursor: pointer; border-radius: 3px;
    text-transform: uppercase; letter-spacing: 0.04em;
  }
  .clear-btn:hover { color: var(--red); border-color: var(--red); }
  .counter { margin-left: auto; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted); }
  .counter span.n { color: var(--accent); font-weight: 600; }

  /* table */
  .table-wrap { padding: 16px 24px 32px 24px; }
  table.obras {
    width: 100%; border-collapse: collapse; background: var(--card);
    border: 1px solid var(--border); border-radius: 4px; overflow: hidden;
  }
  table.obras thead th {
    background: var(--card-2); color: var(--muted);
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em;
    padding: 10px 12px; text-align: left; font-weight: 500;
    border-bottom: 1px solid var(--border-2); cursor: pointer; user-select: none;
    white-space: nowrap;
  }
  table.obras thead th:hover { color: var(--text); }
  table.obras thead th.sort-asc::after { content: ' ↑'; color: var(--accent); }
  table.obras thead th.sort-desc::after { content: ' ↓'; color: var(--accent); }
  table.obras tbody tr.row {
    border-bottom: 1px solid var(--border); cursor: pointer;
    transition: background .12s;
  }
  table.obras tbody tr.row:hover { background: #131313; }
  table.obras tbody tr.row.expanded { background: #131313; }
  table.obras tbody td { padding: 10px 12px; vertical-align: top; font-size: 12px; }
  td.cli { min-width: 220px; }
  td.cli .nome { color: var(--text); font-weight: 500; }
  td.cli .cidade { color: var(--muted); font-size: 11px; margin-top: 2px; }
  td.flags-cell { min-width: 280px; }

  .badge {
    display: inline-block; padding: 2px 7px; font-size: 10px;
    border-radius: 2px; letter-spacing: 0.04em; text-transform: uppercase; font-weight: 500;
    font-family: 'Inter', sans-serif; white-space: nowrap;
  }
  .badge-status-em_execucao { background: rgba(123,232,168,0.12); color: var(--green); border: 1px solid rgba(123,232,168,0.3); }
  .badge-status-aguardando_clima, .badge-status-aguardando_execucao { background: rgba(232,200,123,0.12); color: var(--amber); border: 1px solid rgba(232,200,123,0.3); }
  .badge-status-reparo { background: rgba(232,123,123,0.12); color: var(--red); border: 1px solid rgba(232,123,123,0.3); }
  .badge-status-planejamento, .badge-status-contrato, .badge-status-reserva { background: rgba(123,168,232,0.12); color: var(--blue); border: 1px solid rgba(123,168,232,0.3); }
  .badge-status-pausado, .badge-status-marcas_rolo_cera { background: rgba(136,136,136,0.12); color: var(--muted); border: 1px solid rgba(136,136,136,0.3); }

  .badge-idade-low    { color: var(--green); border: 1px solid rgba(123,232,168,0.3); background: rgba(123,232,168,0.06); }
  .badge-idade-mid    { color: var(--amber); border: 1px solid rgba(232,200,123,0.3); background: rgba(232,200,123,0.06); }
  .badge-idade-high   { color: var(--red);   border: 1px solid rgba(232,123,123,0.3); background: rgba(232,123,123,0.06); }
  .badge-idade-vhigh  { color: var(--scarlet); border: 1px solid rgba(255,82,82,0.4); background: rgba(255,82,82,0.1); }

  .chip {
    display: inline-block; padding: 1px 6px; font-size: 9px;
    border-radius: 2px; letter-spacing: 0.06em; text-transform: uppercase; font-weight: 600;
    font-family: 'Inter', sans-serif; margin: 1px 3px 1px 0;
  }
  .chip-red    { background: rgba(232,123,123,0.14); color: var(--red); border: 1px solid rgba(232,123,123,0.35); }
  .chip-amber  { background: rgba(232,200,123,0.12); color: var(--amber); border: 1px solid rgba(232,200,123,0.3); }
  .chip-blue   { background: rgba(123,168,232,0.12); color: var(--blue); border: 1px solid rgba(123,168,232,0.3); }
  .chip-scarlet{ background: rgba(255,82,82,0.16); color: var(--scarlet); border: 1px solid rgba(255,82,82,0.4); }

  td.consultor .first { color: var(--text); font-weight: 500; }
  td.consultor .empty { color: var(--muted-2); }
  td.metragem { font-family: 'JetBrains Mono', monospace; color: var(--text); text-align: right; min-width: 60px; }
  td.fase { color: var(--muted); font-size: 11px; max-width: 200px; }

  /* expanded */
  tr.detail-row td {
    background: #0a0a0a; padding: 16px 24px 20px 24px;
    border-bottom: 1px solid var(--border-2);
  }
  .detail-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 18px;
  }
  .detail-block { background: var(--card); border: 1px solid var(--border); padding: 12px; border-radius: 3px; }
  .detail-block h4 {
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent);
    font-weight: 500; margin-bottom: 8px;
  }
  .kv { display: flex; justify-content: space-between; gap: 12px; padding: 3px 0; font-size: 11px; }
  .kv .k { color: var(--muted); }
  .kv .v { color: var(--text); font-family: 'JetBrains Mono', monospace; text-align: right; }
  .alertas-list { list-style: none; padding: 0; margin: 0; }
  .alertas-list li { padding: 6px 0; border-top: 1px solid var(--border); font-size: 11px; color: var(--text); line-height: 1.5; }
  .alertas-list li:first-child { border-top: none; }
  .alertas-list li .cat-tag {
    display: inline-block; font-size: 9px; padding: 1px 5px; background: var(--card-2);
    color: var(--accent); border-radius: 2px; margin-right: 6px; letter-spacing: 0.05em;
    border: 1px solid var(--border-2);
  }
  .diag-text { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text); white-space: pre-wrap; line-height: 1.5; max-height: 240px; overflow-y: auto; }
  .portal-link { display: inline-block; margin-top: 8px; font-size: 11px; padding: 5px 10px; border: 1px solid var(--accent); color: var(--accent); border-radius: 3px; }
  .portal-link:hover { background: var(--accent); color: var(--bg); text-decoration: none; }

  footer { padding: 24px; text-align: center; border-top: 1px solid var(--border); color: var(--muted); font-size: 11px; }
  footer a { margin: 0 8px; }

  .empty-state { text-align: center; padding: 60px 20px; color: var(--muted); }

  /* mobile */
  @media (max-width: 900px) {
    table.obras thead { display: none; }
    table.obras tbody tr.row { display: block; padding: 12px; border: 1px solid var(--border); margin-bottom: 8px; border-radius: 4px; }
    table.obras tbody td { display: block; padding: 4px 0; }
    table.obras tbody td::before {
      content: attr(data-lbl); display: inline-block; width: 80px;
      color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .filters { top: 152px; }
    .filters-row { flex-direction: column; align-items: stretch; }
    .filters input, .filters select { min-width: 0; width: 100%; }
    .counter { margin-left: 0; margin-top: 8px; }
  }
</style>
</head>
<body>

<header class="top">
  <div class="top-row">
    <h1>Mapa de Obras Ativas <span class="acc">— 208 obras, 23 cruzamentos consolidados</span></h1>
    <div class="stamp">última atualização <span class="mono">2026-04-15</span></div>
  </div>
  <div class="metrics" id="metrics"></div>
</header>

<div class="filters">
  <div class="filters-row">
    <input type="text" id="f-busca" placeholder="buscar cliente, cidade ou consultor…" autocomplete="off">
    <select id="f-status"><option value="">todos status</option></select>
    <select id="f-fase"><option value="">todas fases</option></select>
    <select id="f-consultor"><option value="">todos consultores</option></select>
    <select id="f-uf"><option value="">todas UFs</option></select>
    <select id="f-idade">
      <option value="">qualquer idade</option>
      <option value="lt30">&lt; 30 dias</option>
      <option value="30-90">30–90 dias</option>
      <option value="90-180">90–180 dias</option>
      <option value="180-270">180–270 dias</option>
      <option value="270">&gt; 270 dias</option>
    </select>
    <button class="clear-btn" id="f-clear">limpar</button>
  </div>
  <div class="toggles" id="toggles"></div>
  <div class="filters-row" style="margin-top: 8px;">
    <span class="counter"><span class="n" id="n-vis">0</span> de <span id="n-tot">0</span> visíveis</span>
  </div>
</div>

<div class="table-wrap">
  <table class="obras" id="tbl">
    <thead>
      <tr>
        <th data-sort="cliente">Cliente</th>
        <th data-sort="status">Status</th>
        <th data-sort="fase">Fase</th>
        <th data-sort="consultorFirst">Consultor</th>
        <th data-sort="idade">Idade</th>
        <th data-sort="metragem">m²</th>
        <th data-sort="flagsCount">Flags</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="empty-state" id="empty" style="display:none">nenhuma obra corresponde aos filtros</div>
</div>

<footer>
  <a href="plano.html">plano.html</a> ·
  <a href="modelagem.html">modelagem.html</a> ·
  <a href="index.html">índice</a>
</footer>

<script>
const META = __META__;
const OBRAS = __OBRAS__;

// computar flagsCount p/ ordenação
OBRAS.forEach(o => {
  let n = 0;
  ['flagZumbi','flagReparo','flagOrfa','flagSemCor','flagSemWa','flagCaudaVt','flagAtraso','flagAtrasoGrave','flagAlerta','flagAtRisk','flagEscalAnom','flagSemEscal'].forEach(k => { if (o[k]) n++; });
  o.flagsCount = n;
});

// --- toggles definição ---
const TOGGLES = [
  { k: 'flagZumbi',       label: 'zumbi',         cls: 'red'    },
  { k: 'flagReparo',      label: 'reparo',        cls: 'red'    },
  { k: 'flagOrfa',        label: 'órfã',          cls: 'amber'  },
  { k: 'flagSemCor',      label: 'sem cor',       cls: 'amber'  },
  { k: 'flagSemWa',       label: 'sem WA',        cls: 'amber'  },
  { k: 'flagCaudaVt',     label: 'cauda VT',      cls: 'amber'  },
  { k: 'flagAtrasoGrave', label: 'atraso grave',  cls: 'red'    },
  { k: 'flagAlerta',      label: 'alertas',       cls: 'red'    },
  { k: 'flagAtRisk',      label: 'atRisk',        cls: 'amber'  },
  { k: 'flagEscalAnom',   label: 'escal. anômala',cls: 'red'    }
];

// --- métricas header ---
function renderMetrics() {
  const r = META.resumo;
  const items = [
    { lbl: 'total ativas',   val: META.total, cls: '' },
    { lbl: 'com data',       val: META.comData, cls: '' },
    { lbl: 'idade média',    val: META.idadeMedia + 'd', cls: '' },
    { lbl: 'idade max',      val: META.idadeMax + 'd', cls: 'crit' },
    { lbl: '180d+',          val: META.n180, cls: 'warn' },
    { lbl: '270d+',          val: META.n270, cls: 'crit' }
  ];
  const html = items.map(i => `<div class="metric"><span class="lbl">\${i.lbl}</span><span class="val \${i.cls}">\${i.val}</span></div>`).join('');
  document.getElementById('metrics').innerHTML = html;
}

// --- toggles render ---
function renderToggles() {
  const t = document.getElementById('toggles');
  t.innerHTML = TOGGLES.map(g => `<button class="toggle" data-flag="\${g.k}">\${g.label}</button>`).join('');
  t.querySelectorAll('.toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.classList.toggle('active');
      render();
    });
  });
}

// --- popular dropdowns ---
function popDropdowns() {
  const uniq = (arr) => [...new Set(arr)].filter(x => x !== null && x !== undefined && x !== '').sort();
  const fillSel = (id, vals) => {
    const sel = document.getElementById(id);
    vals.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v; opt.textContent = v;
      sel.appendChild(opt);
    });
    sel.addEventListener('change', render);
  };
  fillSel('f-status', uniq(OBRAS.map(o => o.status)));
  fillSel('f-fase',   uniq(OBRAS.map(o => o.fase)));
  fillSel('f-consultor', uniq(OBRAS.map(o => o.consultorFirst)));
  fillSel('f-uf',     uniq(OBRAS.map(o => o.uf)));
  document.getElementById('f-idade').addEventListener('change', render);
  document.getElementById('f-busca').addEventListener('input', render);
  document.getElementById('f-clear').addEventListener('click', () => {
    document.getElementById('f-busca').value = '';
    ['f-status','f-fase','f-consultor','f-uf','f-idade'].forEach(id => document.getElementById(id).value = '');
    document.querySelectorAll('.toggle.active').forEach(b => b.classList.remove('active'));
    render();
  });
}

// --- filtros aplicados ---
function applyFilters() {
  const q = document.getElementById('f-busca').value.toLowerCase().trim();
  const fs = document.getElementById('f-status').value;
  const ff = document.getElementById('f-fase').value;
  const fc = document.getElementById('f-consultor').value;
  const fu = document.getElementById('f-uf').value;
  const fi = document.getElementById('f-idade').value;
  const activeFlags = [...document.querySelectorAll('.toggle.active')].map(b => b.dataset.flag);

  return OBRAS.filter(o => {
    if (q) {
      const hay = (o.cliente + ' ' + o.cidade + ' ' + (o.consultor||'')).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    if (fs && o.status !== fs) return false;
    if (ff && o.fase !== ff) return false;
    if (fc && o.consultorFirst !== fc) return false;
    if (fu && o.uf !== fu) return false;
    if (fi) {
      const i = o.idade || 0;
      if (fi === 'lt30' && i >= 30) return false;
      if (fi === '30-90' && (i < 30 || i >= 90)) return false;
      if (fi === '90-180' && (i < 90 || i >= 180)) return false;
      if (fi === '180-270' && (i < 180 || i >= 270)) return false;
      if (fi === '270' && i < 270) return false;
    }
    for (const f of activeFlags) {
      if (!o[f]) return false;
    }
    return true;
  });
}

// --- ordenação ---
let sortKey = 'idade';
let sortDir = -1;
function applySort(rows) {
  return rows.slice().sort((a, b) => {
    let va = a[sortKey], vb = b[sortKey];
    if (va === null || va === undefined) va = (typeof vb === 'number') ? -1 : '';
    if (vb === null || vb === undefined) vb = (typeof va === 'number') ? -1 : '';
    if (typeof va === 'string') va = va.toLowerCase();
    if (typeof vb === 'string') vb = vb.toLowerCase();
    if (va < vb) return -1 * sortDir;
    if (va > vb) return 1 * sortDir;
    return 0;
  });
}
function bindSort() {
  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.dataset.sort;
      if (sortKey === k) sortDir = -sortDir;
      else { sortKey = k; sortDir = 1; }
      document.querySelectorAll('th[data-sort]').forEach(t => t.classList.remove('sort-asc','sort-desc'));
      th.classList.add(sortDir === 1 ? 'sort-asc' : 'sort-desc');
      render();
    });
  });
}

// --- render row ---
function badgeStatus(s) {
  if (!s) return '<span class="badge" style="color:var(--muted-2)">—</span>';
  return `<span class="badge badge-status-\${s}">\${s.replace(/_/g,' ')}</span>`;
}
function badgeIdade(i) {
  if (i === null || i === undefined) return '<span class="badge" style="color:var(--muted-2)">—</span>';
  let cls = 'low';
  if (i >= 270) cls = 'vhigh';
  else if (i >= 180) cls = 'high';
  else if (i >= 90) cls = 'mid';
  return `<span class="badge mono badge-idade-\${cls}">\${i}d</span>`;
}
function chips(o) {
  const out = [];
  if (o.flagZumbi)       out.push('<span class="chip chip-red">zumbi</span>');
  if (o.flagReparo)      out.push('<span class="chip chip-red">reparo</span>');
  if (o.flagOrfa)        out.push('<span class="chip chip-amber">órfã</span>');
  if (o.flagSemCor)      out.push('<span class="chip chip-amber">sem cor</span>');
  if (o.flagSemWa)       out.push('<span class="chip chip-amber">sem WA</span>');
  if (o.flagCaudaVt)     out.push('<span class="chip chip-amber">cauda VT</span>');
  if (o.flagAtrasoGrave) out.push('<span class="chip chip-scarlet">atraso grave</span>');
  else if (o.flagAtraso) out.push('<span class="chip chip-amber">atraso</span>');
  if (o.flagAlerta)      out.push(`<span class="chip chip-red">alertas \${o.qtdAlertas}</span>`);
  if (o.flagAtRisk)      out.push('<span class="chip chip-amber">atRisk</span>');
  if (o.flagEscalAnom)   out.push('<span class="chip chip-red">escal. anômala</span>');
  if (o.flagSemEscal)    out.push('<span class="chip chip-blue">sem escal.</span>');
  return out.join('');
}

function renderDetail(o) {
  const portalUrl = `https://cliente.monofloor.cloud/app/projetos/\${o.id}`;
  const alertasHtml = (o.alertas && o.alertas.length)
    ? '<ul class="alertas-list">' + o.alertas.map((a, i) => `<li><span class="cat-tag">\${(o.alertasCat && o.alertasCat[i]) ? o.alertasCat[i] : 'OUTROS'}</span>\${escapeHtml(a)}</li>`).join('') + '</ul>'
    : '<div style="color:var(--muted-2); font-size:11px;">sem alertas</div>';
  const diagHtml = o.diagnostico ? `<div class="diag-text">\${escapeHtml(o.diagnostico)}</div>` : '<div style="color:var(--muted-2); font-size:11px;">sem diagnóstico atRisk</div>';
  const coresHtml = (o.coresList && o.coresList.length) ? o.coresList.map(c => `<span class="chip chip-amber">\${escapeHtml(c)}</span>`).join('') : '—';

  return `
    <td colspan="7">
      <div class="detail-grid">
        <div class="detail-block">
          <h4>Identificação</h4>
          <div class="kv"><span class="k">id</span><span class="v">\${o.id.substring(0,8)}</span></div>
          <div class="kv"><span class="k">pipefyCardId</span><span class="v">\${o.pipefyCardId || '—'}</span></div>
          <div class="kv"><span class="k">data radar</span><span class="v">\${o.dataRadar || '—'}</span></div>
          <div class="kv"><span class="k">fonte radar</span><span class="v">\${o.radarFonte || '—'}</span></div>
          <div class="kv"><span class="k">consultor</span><span class="v">\${o.consultor || '—'}</span></div>
          <div class="kv"><span class="k">resp. operações</span><span class="v">\${escapeHtml(o.responsavelOps) || '—'}</span></div>
          <div class="kv"><span class="k">tagKira</span><span class="v">\${escapeHtml(o.tagKira) || '—'}</span></div>
          <div class="kv"><span class="k">situaçãoAtual</span><span class="v">\${escapeHtml(o.situacaoAtual) || '—'}</span></div>
          <div class="kv"><span class="k">climaGeral</span><span class="v">\${escapeHtml(o.climaGeral) || '—'}</span></div>
          <a class="portal-link" href="\${portalUrl}" target="_blank" rel="noopener">abrir no portal →</a>
        </div>
        <div class="detail-block">
          <h4>Cruzamentos</h4>
          <div class="kv"><span class="k">cat. cor</span><span class="v">\${o.catCor || '—'}</span></div>
          <div class="kv"><span class="k">cores</span><span class="v">\${coresHtml}</span></div>
          <div class="kv"><span class="k">atraso cron.</span><span class="v">\${o.diasAtrasoCron !== null ? (o.diasAtrasoCron + 'd ' + (o.catAtraso||'')) : '—'}</span></div>
          <div class="kv"><span class="k">atRisk dias</span><span class="v">\${o.diasAtrasoOcor !== null ? (o.diasAtrasoOcor + 'd') : '—'}</span></div>
          <div class="kv"><span class="k">openProblems</span><span class="v">\${o.openProblems !== null ? o.openProblems : '—'}</span></div>
          <div class="kv"><span class="k">criticalProblems</span><span class="v">\${o.criticalProblems !== null ? o.criticalProblems : '—'}</span></div>
        </div>
        <div class="detail-block" style="grid-column: span 2;">
          <h4>Alertas (\${o.qtdAlertas || 0})</h4>
          \${alertasHtml}
        </div>
        <div class="detail-block" style="grid-column: 1 / -1;">
          <h4>Diagnóstico Operacional (atRisk)</h4>
          \${diagHtml}
        </div>
      </div>
    </td>`;
}

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

const expanded = new Set();

function render() {
  let rows = applyFilters();
  rows = applySort(rows);
  const tbody = document.getElementById('tbody');
  const html = rows.map(o => {
    const isExp = expanded.has(o.id);
    const consHtml = o.consultorFirst
      ? `<span class="first">\${escapeHtml(o.consultorFirst)}</span>`
      : '<span class="empty">—</span>';
    const metr = o.metragem !== null ? Number(o.metragem).toFixed(1) : '—';
    const main = `
      <tr class="row \${isExp ? 'expanded' : ''}" data-id="\${o.id}">
        <td class="cli" data-lbl="Cliente">
          <div class="nome">\${escapeHtml(o.cliente)}</div>
          <div class="cidade">\${escapeHtml(o.cidade)}</div>
        </td>
        <td data-lbl="Status">\${badgeStatus(o.status)}</td>
        <td class="fase" data-lbl="Fase">\${escapeHtml(o.fase || '—')}</td>
        <td class="consultor" data-lbl="Consultor">\${consHtml}</td>
        <td data-lbl="Idade">\${badgeIdade(o.idade)}</td>
        <td class="metragem" data-lbl="m²">\${metr}</td>
        <td class="flags-cell" data-lbl="Flags">\${chips(o) || '<span style="color:var(--muted-2)">—</span>'}</td>
      </tr>`;
    const detail = isExp ? `<tr class="detail-row" data-detail="\${o.id}">\${renderDetail(o)}</tr>` : '';
    return main + detail;
  }).join('');
  tbody.innerHTML = html;

  document.getElementById('empty').style.display = rows.length === 0 ? 'block' : 'none';
  document.getElementById('n-vis').textContent = rows.length;
  document.getElementById('n-tot').textContent = OBRAS.length;

  tbody.querySelectorAll('tr.row').forEach(tr => {
    tr.addEventListener('click', () => {
      const id = tr.dataset.id;
      if (expanded.has(id)) expanded.delete(id);
      else expanded.add(id);
      render();
    });
  });
}

// init
renderMetrics();
renderToggles();
popDropdowns();
bindSort();
document.querySelector('th[data-sort="idade"]').classList.add('sort-desc');
render();
</script>
</body>
</html>
"@
$null = $_DEAD_HEREDOC_START_

[System.IO.File]::WriteAllText($out, $html, [System.Text.UTF8Encoding]::new($false))
Write-Host "OK: arquivo gerado em $out"
$sz = (Get-Item $out).Length
Write-Host "Tamanho: $([Math]::Round($sz/1024,1)) KB"
