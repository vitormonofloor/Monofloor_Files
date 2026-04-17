# ATENA Pilot Scan — PowerShell version for local execution
# Generates the same JSON output as atena-scan.sh but uses PowerShell
$ErrorActionPreference = "Stop"

$DIR = "C:\Users\vitor\Monofloor_Files\analise"
$DADOS = "C:\Users\vitor\Monofloor_Files\analise\dados"
$ATENA = "C:\Users\vitor\Monofloor_Files\analise\dados\atena"
$DASHBOARD = "C:\Users\vitor\Monofloor_Files\analise\dashboard.html"
$PAINEL = "C:\Users\vitor\Monofloor_Files\analise\dados\painel-temporal.json"
$HISTFILE = "C:\Users\vitor\Monofloor_Files\analise\dados\backlog-historico.json"

$TODAY = (Get-Date).ToString("yyyy-MM-dd")
$NOW_UTC = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

if (!(Test-Path $ATENA)) { New-Item -ItemType Directory -Path $ATENA -Force | Out-Null }

Write-Host "=== ATENA Pilot Scan $TODAY ==="

# Load data
$dashHtml = Get-Content $DASHBOARD -Raw -Encoding UTF8
$painel = Get-Content $PAINEL -Raw -Encoding UTF8 | ConvertFrom-Json
$hist = @()
if (Test-Path $HISTFILE) {
    $hist = Get-Content $HISTFILE -Raw -Encoding UTF8 | ConvertFrom-Json
}

# Load cruz files
$cruzFiles = Get-ChildItem (Join-Path $DADOS "cruz-*.json") -ErrorAction SilentlyContinue
$cruzData = @{}
foreach ($cf in $cruzFiles) {
    $nome = $cf.Name -replace "^cruz-","" -replace "\.json$",""
    try {
        $cruzData[$nome] = Get-Content $cf.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {}
}

$INATIVAS = @("finalizado","concluido","cancelado")
$ativas = @($painel | Where-Object { $_.status -notin $INATIVAS })

Write-Host "  Obras total: $($painel.Count), ativas: $($ativas.Count)"
Write-Host "  Cruzamentos: $($cruzData.Count)"

function New-Achado($sev, $titulo, $desc, $evidencia) {
    return @{
        severidade = $sev
        titulo = $titulo
        descricao = $desc
        evidencia = $evidencia
    }
}

# ============================================================
# OLHO 1: UX
# ============================================================
Write-Host "  [ux] executando..."
$ux_achados = @()
$ux_metricas = @{}

# TODOs
$todos = [regex]::Matches($dashHtml, "(?:TODO|FIXME|HACK|XXX)[:\s].*", "IgnoreCase")
if ($todos.Count -gt 0) {
    $ev = ($todos | Select-Object -First 5 | ForEach-Object { $_.Value.Trim().Substring(0, [Math]::Min(80, $_.Value.Trim().Length)) }) -join "; "
    $ux_achados += New-Achado "baixa" "$($todos.Count) marcadores TODO/FIXME no HTML" "Comentarios de desenvolvimento pendentes." $ev
}

# Duplicate IDs
$ids = [regex]::Matches($dashHtml, '\bid=["\x27]([^"\x27]+)["\x27]') | ForEach-Object { $_.Groups[1].Value }
$idCounts = $ids | Group-Object | Where-Object { $_.Count -gt 1 }
if ($idCounts) {
    $ev = ($idCounts | Sort-Object Count -Descending | Select-Object -First 10 | ForEach-Object { "$($_.Name) ($($_.Count)x)" }) -join ", "
    $ux_achados += New-Achado "media" "$($idCounts.Count) IDs duplicados no HTML" "IDs HTML devem ser unicos." $ev
}

# File size
$sizeKB = [Math]::Round((Get-Item $DASHBOARD).Length / 1024, 1)
$lines = (Get-Content $DASHBOARD).Count
if ($sizeKB -gt 250) {
    $sev = if ($sizeKB -gt 500) { "alta" } else { "media" }
    $ux_achados += New-Achado $sev "Dashboard com $([Math]::Round($sizeKB))KB" "Arquivo monolitico. Paginas acima de 250KB impactam carregamento." "dashboard.html = ${sizeKB}KB, $lines linhas"
}

# Inline scripts
$scripts = [regex]::Matches($dashHtml, '<script(?:\s[^>]*)?>[^<]{100,}')
$ux_achados += New-Achado $(if ($scripts.Count -le 3) {"baixa"} else {"media"}) "$($scripts.Count) blocos script inline com >100 chars" "Scripts inline extensos dificultam cache e manutencao." "$($scripts.Count) blocos encontrados"

# Console.log
$consoleLogs = [regex]::Matches($dashHtml, 'console\.\w+\s*\(')
if ($consoleLogs.Count -gt 0) {
    $ux_achados += New-Achado "baixa" "$($consoleLogs.Count) chamadas console.* no codigo" "Console.log residuais devem ser removidos em producao." "$($consoleLogs.Count) ocorrencias"
}

$ux_metricas = @{
    tamanho_kb = $sizeKB
    linhas = $lines
    ids_unicos = ($ids | Sort-Object -Unique).Count
    ids_duplicados = $idCounts.Count
    scripts_inline = $scripts.Count
    todos_fixme = $todos.Count
    console_logs = $consoleLogs.Count
}

# ============================================================
# OLHO 2: INSIGHTS
# ============================================================
Write-Host "  [insights] executando..."
$ins_achados = @()

# Concentracao por consultor
$consultores = @{}
foreach ($o in $ativas) {
    $c = if ($o.consultorNome) { $o.consultorNome.Trim() } else { "" }
    if ($c -and $c -ne "[]") {
        if (!$consultores.ContainsKey($c)) { $consultores[$c] = 0 }
        $consultores[$c]++
    }
}
$topConsultores = $consultores.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 3
$topTotal = ($topConsultores | Measure-Object -Property Value -Sum).Sum
$nAtivas = $ativas.Count
if ($nAtivas -gt 0 -and $topTotal / $nAtivas -gt 0.4) {
    $ev = ($topConsultores | ForEach-Object { "$($_.Key) ($($_.Value))" }) -join ", "
    $pct = [Math]::Floor($topTotal * 100 / $nAtivas)
    $ins_achados += New-Achado "media" "Concentracao: $topTotal obras (${pct}%) em 3 consultores" "Os 3 consultores com mais obras concentram ${pct}% do total ativo." $ev
}

# Idade media
$idades = @($ativas | Where-Object { $_.idade_dias -and $_.idade_dias -gt 0 } | ForEach-Object { [int]$_.idade_dias } | Sort-Object)
if ($idades.Count -gt 0) {
    $media = [Math]::Round(($idades | Measure-Object -Average).Average)
    $mediana = $idades[[Math]::Floor($idades.Count / 2)]
    $p90 = $idades[[Math]::Floor($idades.Count * 0.9)]
    $sev = if ($media -gt 150) { "media" } else { "baixa" }
    $ins_achados += New-Achado $sev "Idade media das obras ativas: ${media}d (mediana ${mediana}d, P90 ${p90}d)" "De $($idades.Count) obras com data." "media=${media}d, mediana=${mediana}d, P90=${p90}d, max=$($idades[-1])d"
}

# Fases top
$fases = $ativas | Group-Object faseAtual | Sort-Object Count -Descending | Select-Object -First 5
$ev = ($fases | ForEach-Object { "$($_.Name): $($_.Count)" }) -join "; "
$ins_achados += New-Achado "baixa" "Top 5 fases com mais obras ativas" "Distribuicao das obras ativas por fase atual." $ev

# Cruzamentos info
if ($cruzData.Count -gt 0) {
    $cruzSizes = @{}
    foreach ($k in $cruzData.Keys) {
        $cruzSizes[$k] = [Math]::Round((Get-Item (Join-Path $DADOS "cruz-$k.json")).Length / 1024)
    }
    $biggest = ($cruzSizes.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1).Key
    $ev = ($cruzSizes.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 5 | ForEach-Object { "$($_.Key): $($_.Value)KB" }) -join "; "
    $ins_achados += New-Achado "baixa" "$($cruzData.Count) cruzamentos ativos, maior: $biggest" "Mapa dos cruzamentos disponíveis." $ev
}

$ins_metricas = @{
    obras_ativas = $nAtivas
    obras_total = $painel.Count
    consultores_distintos = $consultores.Count
    fases_distintas = ($ativas | Select-Object -ExpandProperty faseAtual -Unique).Count
    cruzamentos_ativos = $cruzData.Count
    idade_media = if ($idades.Count -gt 0) { [Math]::Round(($idades | Measure-Object -Average).Average, 1) } else { $null }
    idade_mediana = if ($idades.Count -gt 0) { $idades[[Math]::Floor($idades.Count / 2)] } else { $null }
    idade_p90 = if ($idades.Count -gt 0) { $idades[[Math]::Floor($idades.Count * 0.9)] } else { $null }
}

# ============================================================
# OLHO 3: LACUNAS
# ============================================================
Write-Host "  [lacunas] executando..."
$lac_achados = @()

# Campos do painel
$camposPainel = if ($painel.Count -gt 0) { $painel[0].PSObject.Properties.Name } else { @() }

# Campos usados no HTML (heuristica simples)
$camposHtml = @()
$camposHtml += [regex]::Matches($dashHtml, '\.(\w+)') | ForEach-Object { $_.Groups[1].Value }
$camposHtml += [regex]::Matches($dashHtml, '\["(\w+)"\]') | ForEach-Object { $_.Groups[1].Value }
$camposHtml = $camposHtml | Sort-Object -Unique

$naoUsados = @($camposPainel | Where-Object { $_ -notin $camposHtml -and $_ -ne "ativa" })
if ($naoUsados.Count -gt 0) {
    $sev = if ($naoUsados.Count -gt 3) { "media" } else { "baixa" }
    $lac_achados += New-Achado $sev "$($naoUsados.Count) campos do painel-temporal nao usados no dashboard" "Campos disponiveis nos dados mas nao referenciados no HTML." ($naoUsados -join ", ")
}

# Cruzamentos ausentes no dashboard
$cruzNomes = @($cruzData.Keys)
$cruzNoDash = @($cruzNomes | Where-Object { $dashHtml.Contains("cruz-$_") -or $dashHtml.Contains($_) })
$cruzAusentes = @($cruzNomes | Where-Object { $_ -notin $cruzNoDash })
if ($cruzAusentes.Count -gt 0) {
    $sev = if ($cruzAusentes.Count -gt 5) { "media" } else { "baixa" }
    $lac_achados += New-Achado $sev "$($cruzAusentes.Count) cruzamentos sem referencia no dashboard" "Cruzamentos que existem nos dados mas nao sao carregados pelo dashboard." ($cruzAusentes -join ", ")
}

$lac_metricas = @{
    campos_painel = $camposPainel.Count
    campos_referenciados_html = $camposHtml.Count
    campos_nao_usados = $naoUsados.Count
    cruzamentos_total = $cruzNomes.Count
    cruzamentos_no_dashboard = $cruzNoDash.Count
    cruzamentos_ausentes = $cruzAusentes.Count
}

# ============================================================
# OLHO 4: BUGS
# ============================================================
Write-Host "  [bugs] executando..."
$bugs_achados = @()

# Datas estranhas
$datasEstranhas = @()
foreach ($o in $painel) {
    if ($o.data_radar) {
        try {
            $ano = [int]$o.data_radar.Substring(0, 4)
            if ($ano -lt 2020 -or $ano -gt 2030) {
                $datasEstranhas += @{ id = $o.id.Substring(0,8); cliente = $o.clienteNome; data = $o.data_radar }
            }
        } catch {}
    }
}
if ($datasEstranhas.Count -gt 0) {
    $ev = ($datasEstranhas | Select-Object -First 5 | ForEach-Object { "$($_.id) ($($_.cliente.Substring(0, [Math]::Min(30, $_.cliente.Length)))): $($_.data)" }) -join "; "
    $bugs_achados += New-Achado "alta" "$($datasEstranhas.Count) obras com data_radar fora do range 2020-2030" "Datas de radar com ano improvavel." $ev
}

# Idades extremas (>500d)
$extremas = @($ativas | Where-Object { $_.idade_dias -and [int]$_.idade_dias -gt 500 } | Sort-Object { -[int]$_.idade_dias })
if ($extremas.Count -gt 0) {
    $ev = ($extremas | Select-Object -First 5 | ForEach-Object { "$($_.id.Substring(0,8)) ($($_.clienteNome.Substring(0, [Math]::Min(25, $_.clienteNome.Length)))): $($_.idade_dias)d" }) -join "; "
    $bugs_achados += New-Achado "alta" "$($extremas.Count) obras ativas com idade > 500 dias" "Obras anormalmente antigas. Verificar se deviam estar finalizadas." $ev
}

# Zumbis
$zumbis = @($ativas | Where-Object { $_.faseAtual -and $_.faseAtual.Trim().ToUpper() -eq "CLIENTE FINALIZADO" })
if ($zumbis.Count -gt 0) {
    $ev = ($zumbis | Select-Object -First 5 | ForEach-Object { "$($_.id.Substring(0,8)) ($($_.clienteNome.Substring(0, [Math]::Min(25, $_.clienteNome.Length))))" }) -join "; "
    $bugs_achados += New-Achado "alta" "$($zumbis.Count) obras zumbi (ativas + CLIENTE FINALIZADO)" "Obras com status ativo mas fase terminal." $ev
}

# Orfas
$orfas = @($ativas | Where-Object { -not $_.consultorNome -or $_.consultorNome.Trim() -eq "" -or $_.consultorNome.Trim() -eq "[]" })
if ($orfas.Count -gt 0) {
    $ev = ($orfas | Select-Object -First 8 | ForEach-Object { $_.id.Substring(0,8) }) -join "; "
    $bugs_achados += New-Achado "media" "$($orfas.Count) obras orfas (sem consultor atribuido)" "Obras ativas sem consultor responsavel." $ev
}

# Strings hardcoded
$hardcodedDates = [regex]::Matches($dashHtml, "2026-04-\d\d")
if ($hardcodedDates.Count -gt 0) {
    $uniq = ($hardcodedDates | ForEach-Object { $_.Value } | Sort-Object -Unique) -join ", "
    $bugs_achados += New-Achado "media" "Strings hardcoded no HTML: datas fixas 2026-04-xx" "$($hardcodedDates.Count) ocorrencias de datas fixas no HTML." $uniq
}

$hardcodedCounts = [regex]::Matches($dashHtml, "de 1[\.,]028|de 228|de 208")
if ($hardcodedCounts.Count -gt 0) {
    $uniq = ($hardcodedCounts | ForEach-Object { $_.Value } | Sort-Object -Unique) -join ", "
    $bugs_achados += New-Achado "media" "Strings hardcoded no HTML: contagens fixas" "$($hardcodedCounts.Count) ocorrencias de contagens hardcoded." $uniq
}

# Idades negativas
$negativas = @($ativas | Where-Object { $_.idade_dias -and [int]$_.idade_dias -lt 0 })
if ($negativas.Count -gt 0) {
    $ev = ($negativas | Select-Object -First 5 | ForEach-Object { "$($_.id.Substring(0,8)): $($_.idade_dias)d" }) -join "; "
    $bugs_achados += New-Achado "media" "$($negativas.Count) obras ativas com idade negativa" "Idade negativa indica data_radar no futuro." $ev
}

# Saude
$nCriticos = $zumbis.Count + $orfas.Count + $extremas.Count
$saude = [Math]::Max(0, [Math]::Min(100, [Math]::Round(100 - ($nCriticos / [Math]::Max($nAtivas, 1)) * 100)))

$bugs_metricas = @{
    indice_saude = $saude
    obras_ativas = $nAtivas
    zumbis = $zumbis.Count
    orfas = $orfas.Count
    idades_extremas_500 = $extremas.Count
    datas_estranhas = $datasEstranhas.Count
    idades_negativas = $negativas.Count
}

# ============================================================
# OLHO 5: OPORTUNIDADES
# ============================================================
Write-Host "  [oportunidades] executando..."
$op_achados = @()

# Cruzamentos nao explorados
$dimensoes = @("idade","fase","consultor","geo","metragem","tipo","status")
$paresNaoExplorados = @()
for ($i=0; $i -lt $dimensoes.Count; $i++) {
    for ($j=$i+1; $j -lt $dimensoes.Count; $j++) {
        $d1 = $dimensoes[$i]; $d2 = $dimensoes[$j]
        $par = "$d1-$d2"
        $coberto = $false
        foreach ($c in $cruzData.Keys) {
            if ($c.Contains($d1) -and $c.Contains($d2)) { $coberto = $true; break }
        }
        if (!$coberto) { $paresNaoExplorados += $par }
    }
}
if ($paresNaoExplorados.Count -gt 0) {
    $op_achados += New-Achado "baixa" "$($paresNaoExplorados.Count) cruzamentos bidimensionais nao explorados" "Combinacoes de dimensoes que poderiam revelar padroes." (($paresNaoExplorados | Select-Object -First 8) -join ", ")
}

# Consultores com acumulo >180d
$consultorVelhas = @{}
foreach ($o in $ativas) {
    $c = if ($o.consultorNome) { $o.consultorNome.Trim() } else { "" }
    $idade = if ($o.idade_dias) { [int]$o.idade_dias } else { 0 }
    if ($c -and $c -ne "[]" -and $idade -gt 180) {
        if (!$consultorVelhas.ContainsKey($c)) { $consultorVelhas[$c] = @() }
        $consultorVelhas[$c] += $idade
    }
}
$topVelhas = $consultorVelhas.GetEnumerator() | Sort-Object { -$_.Value.Count } | Select-Object -First 3
if ($topVelhas -and $topVelhas[0].Value.Count -ge 3) {
    $ev = ($topVelhas | ForEach-Object { "$($_.Key): $($_.Value.Count) obras (media $([Math]::Floor(($_.Value | Measure-Object -Average).Average))d)" }) -join "; "
    $op_achados += New-Achado "media" "Consultores com acumulo de obras antigas (>180d)" "Oportunidade de redistribuicao." $ev
}

# Fases gargalo
$faseStats = @{}
foreach ($o in $ativas) {
    $f = if ($o.faseAtual) { $o.faseAtual } else { "?" }
    if (!$faseStats.ContainsKey($f)) { $faseStats[$f] = @{ n=0; idades=@() } }
    $faseStats[$f].n++
    if ($o.idade_dias -and [int]$o.idade_dias -gt 0) { $faseStats[$f].idades += [int]$o.idade_dias }
}
$gargalos = @()
foreach ($kv in $faseStats.GetEnumerator()) {
    if ($kv.Value.n -ge 5 -and $kv.Value.idades.Count -gt 0) {
        $m = [Math]::Round(($kv.Value.idades | Measure-Object -Average).Average)
        if ($m -gt 150) { $gargalos += @{ fase=$kv.Key; n=$kv.Value.n; media=$m } }
    }
}
$gargalos = $gargalos | Sort-Object { -$_.media }
if ($gargalos.Count -gt 0) {
    $sev = if ($gargalos.Count -ge 3) { "alta" } else { "media" }
    $ev = ($gargalos | Select-Object -First 5 | ForEach-Object { "$($_.fase): $($_.n) obras, media $($_.media)d" }) -join "; "
    $op_achados += New-Achado $sev "$($gargalos.Count) fases com gargalo (>=5 obras + media >150d)" "Fases onde obras acumulam com idade elevada." $ev
}

# Obras sem data_radar
$semRadar = @($ativas | Where-Object { -not $_.data_radar })
if ($semRadar.Count -gt 0) {
    $ev = ($semRadar | Select-Object -First 8 | ForEach-Object { $_.id.Substring(0,8) }) -join "; "
    $op_achados += New-Achado "media" "$($semRadar.Count) obras ativas sem data_radar" "Sem data, nao eh possivel calcular SLAs." $ev
}

# Distribuicao regional
$cidades = @{}
foreach ($o in $ativas) {
    $c = if ($o.projetoCidade) { $o.projetoCidade.Trim() } else { "" }
    if ($c) { if (!$cidades.ContainsKey($c)) { $cidades[$c]=0 }; $cidades[$c]++ }
}
$topCidades = $cidades.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 5
$ev = ($topCidades | ForEach-Object { "$($_.Key): $($_.Value)" }) -join "; "
$op_achados += New-Achado "baixa" "Concentracao regional: $($cidades.Count) cidades" "Distribuicao geografica das obras ativas." $ev

$op_metricas = @{
    cruzamentos_nao_explorados = $paresNaoExplorados.Count
    fases_gargalo = $gargalos.Count
    obras_sem_radar = $semRadar.Count
    cidades_distintas = $cidades.Count
}

# ============================================================
# SALVAR JSONs
# ============================================================
$olhos = @{
    ux = @{ achados = $ux_achados; metricas = $ux_metricas }
    insights = @{ achados = $ins_achados; metricas = $ins_metricas }
    lacunas = @{ achados = $lac_achados; metricas = $lac_metricas }
    bugs = @{ achados = $bugs_achados; metricas = $bugs_metricas }
    oportunidades = @{ achados = $op_achados; metricas = $op_metricas }
}

$totalAchados = 0; $totalAlta = 0; $totalMedia = 0; $totalBaixa = 0
$sumarioHoje = @{}

foreach ($nome in $olhos.Keys) {
    $o = $olhos[$nome]
    $resultado = @{
        olho = $nome
        executado_em = $NOW_UTC
        achados = $o.achados
        metricas = $o.metricas
        comparativo_vs_anterior = $null
    }
    $outPath = Join-Path $ATENA "$TODAY-$nome.json"
    $resultado | ConvertTo-Json -Depth 10 | Set-Content $outPath -Encoding UTF8

    $nAlta = @($o.achados | Where-Object { $_.severidade -eq "alta" }).Count
    $nMedia = @($o.achados | Where-Object { $_.severidade -eq "media" }).Count
    $nBaixa = @($o.achados | Where-Object { $_.severidade -eq "baixa" }).Count
    $totalAchados += $o.achados.Count
    $totalAlta += $nAlta; $totalMedia += $nMedia; $totalBaixa += $nBaixa

    $sumarioHoje[$nome] = @{ achados = $o.achados.Count; alta = $nAlta; media = $nMedia; baixa = $nBaixa }

    Write-Host "    [$nome] $($o.achados.Count) achados ($nAlta alta, $nMedia media, $nBaixa baixa)"
}

# INDEX.JSON
$varreduras = @(@{ date = $TODAY; olhos = @("ux","insights","lacunas","bugs","oportunidades"); completa = $true })
$index = @{
    ultima_varredura = $NOW_UTC
    proxima_varredura = "${TODAY}T10:00:00Z"
    total_achados = $totalAchados
    achados_alta = $totalAlta
    achados_media = $totalMedia
    achados_baixa = $totalBaixa
    indice_saude = $saude
    varreduras = $varreduras
    sumario_hoje = $sumarioHoje
}
$indexPath = Join-Path $ATENA "index.json"
$index | ConvertTo-Json -Depth 10 | Set-Content $indexPath -Encoding UTF8

Write-Host ""
Write-Host "=== ATENA completa ==="
Write-Host "  $totalAchados achados ($totalAlta alta, $totalMedia media, $totalBaixa baixa)"
Write-Host "  indice de saude: $saude"
Write-Host "  Arquivos gerados em: $ATENA"
