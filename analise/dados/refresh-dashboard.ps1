$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Q1 — usa data atual (antes era '2026-04-24' chumbado)
$today = (Get-Date -Format 'yyyy-MM-dd')
$todayDate = [DateTime]::Parse($today)
$jsonPath = 'C:\Users\vitor\Monofloor_Files\analise\dados\dashboard-data.json'
$pipefyPath = 'C:\Users\vitor\Monofloor_Files\analise\dados\pipefy-dates.json'

Write-Host "=== REFRESH DASHBOARD DATA ==="
Write-Host "Date: $today"

# Helper: fetch URL as UTF-8 JSON
function Fetch-JsonUtf8($url) {
    $wc = New-Object System.Net.WebClient
    $wc.Encoding = [System.Text.Encoding]::UTF8
    $raw = $wc.DownloadString($url)
    return $raw | ConvertFrom-Json
}

# 1. Read existing JSON (remove BOM)
Write-Host "`n[1/7] Reading existing JSON..."
$rawBytes = [System.IO.File]::ReadAllBytes($jsonPath)
$rawText = [System.Text.Encoding]::UTF8.GetString($rawBytes)
if ($rawText[0] -eq [char]0xFEFF) { $rawText = $rawText.Substring(1) }
$existing = $rawText | ConvertFrom-Json
Write-Host "  Existing snapshot: $($existing.snapshot_date)"

# 2. Read Pipefy dates
Write-Host "`n[2/7] Reading Pipefy dates..."
$pipefyRaw = [System.IO.File]::ReadAllText($pipefyPath, [System.Text.Encoding]::UTF8)
$pipefyData = $pipefyRaw | ConvertFrom-Json
$pipefyMap = @{}
foreach ($prop in $pipefyData.PSObject.Properties) {
    $key = $prop.Name.ToUpper().Trim()
    if (-not $pipefyMap.ContainsKey($key)) {
        $pipefyMap[$key] = $prop.Value
    } else {
        if ($prop.Value -lt $pipefyMap[$key]) { $pipefyMap[$key] = $prop.Value }
    }
}
Write-Host "  Pipefy entries: $($pipefyMap.Count)"

function Get-PipefyDate($clienteName) {
    if (-not $clienteName) { return $null }
    $upper = $clienteName.ToUpper().Trim()
    if ($pipefyMap.ContainsKey($upper)) { return $pipefyMap[$upper] }
    foreach ($pKey in $pipefyMap.Keys) {
        if ($pKey.Length -gt 5 -and $upper.Length -gt 5) {
            if ($upper.Contains($pKey) -or $pKey.Contains($upper)) { return $pipefyMap[$pKey] }
        }
    }
    $words = $upper -split '\s+' | Where-Object { $_.Length -gt 2 } | Select-Object -First 2
    if ($words.Count -ge 2) {
        $pattern = "$($words[0]) $($words[1])"
        foreach ($pKey in $pipefyMap.Keys) {
            if ($pKey.StartsWith($pattern)) { return $pipefyMap[$pKey] }
        }
    }
    return $null
}

# 3. Fetch fresh API data (UTF-8)
Write-Host "`n[3/7] Fetching APIs (UTF-8)..."

try {
    $projects = Fetch-JsonUtf8 'https://cliente.monofloor.cloud/api/projects?limit=2000'
    Write-Host "  Projects: $($projects.Count)"
} catch {
    Write-Host "  ERROR: $_"; $projects = $null
}

try {
    $dashResp = Fetch-JsonUtf8 'https://cliente.monofloor.cloud/api/dashboard'
    Write-Host "  Dashboard: active=$($dashResp.totals.active)"
} catch {
    Write-Host "  ERROR: $_"; $dashResp = $null
}

try {
    $analiseResp = Fetch-JsonUtf8 'https://cliente.monofloor.cloud/api/analise'
    Write-Host "  Analise: atRisk=$($analiseResp.atRisk.Count)"
} catch {
    Write-Host "  ERROR: $_"; $analiseResp = $null
}

try {
    $equipesResp = Fetch-JsonUtf8 'https://cliente.monofloor.cloud/api/equipes'
    Write-Host "  Equipes: $($equipesResp.Count)"
} catch {
    Write-Host "  ERROR: $_"; $equipesResp = $null
}

try {
    $wc2 = New-Object System.Net.WebClient
    $wc2.Encoding = [System.Text.Encoding]::UTF8
    $escRaw = $wc2.DownloadString('https://cliente.monofloor.cloud/api/escalacao-diaria')
    $escalacaoResp = $escRaw | ConvertFrom-Json
    $escKeys = @()
    if ($escalacaoResp -is [PSCustomObject]) { $escKeys = @($escalacaoResp.PSObject.Properties.Name) }
    Write-Host "  Escalacao: keys=$($escKeys.Count)"
} catch {
    Write-Host "  ERROR: $_"; $escalacaoResp = $null
}

# 4. Build Q2_OBRAS and AGG
Write-Host "`n[4/7] Building Q2_OBRAS and AGG..."

if (-not $projects -or $projects.Count -eq 0) { Write-Host "FATAL: No projects"; exit 1 }

$finalizados = @('finalizado','concluido','cancelado')
$ativas = @($projects | Where-Object { $_.status -notin $finalizados })
$total_obras = $projects.Count
$total_ativas = $ativas.Count
Write-Host "  Total: $total_obras, Ativas: $total_ativas"

# Status dist
$statusDist = [ordered]@{}
foreach ($g in ($ativas | Group-Object -Property status | Sort-Object Count -Descending)) {
    $statusDist[$g.Name] = $g.Count
}

# Top consultores
$consultorCount = [ordered]@{}
$valid = $ativas | Where-Object { $_.consultorNome -and $_.consultorNome -ne '' -and $_.consultorNome -ne '[]' }
foreach ($g in ($valid | Group-Object -Property consultorNome | Sort-Object Count -Descending | Select-Object -First 10)) {
    $consultorCount[$g.Name] = $g.Count
}
$semConsultorAtivas = @($ativas | Where-Object { -not $_.consultorNome -or $_.consultorNome -eq '' -or $_.consultorNome -eq '[]' -or $_.consultorNome -eq $null }).Count

# Metragem
$metragens = @()
foreach ($p in $ativas) {
    $m = 0
    if ($p.projetoMetragem -and $p.projetoMetragem -ne '' -and $p.projetoMetragem -ne $null) {
        try { $m = [double]($p.projetoMetragem.ToString() -replace ',','.') } catch { $m = 0 }
    }
    if ($m -gt 0) { $metragens += $m }
}
$metTotal = ($metragens | Measure-Object -Sum).Sum
$metSorted = $metragens | Sort-Object
$metMediana = if ($metSorted.Count -gt 0) { $metSorted[[math]::Floor($metSorted.Count/2)] } else { 0 }

# Q2_OBRAS with Pipefy ages
$q2Obras = @()
$idades = @()
$matchedPipefy = 0

foreach ($p in $ativas) {
    $age = 0
    $pipefyDate = Get-PipefyDate $p.clienteNome
    if ($pipefyDate) {
        $dt = [DateTime]::Parse($pipefyDate)
        $age = ($todayDate - $dt).Days
        $matchedPipefy++
    } else {
        if ($p.createdAt) {
            try { $dt = [DateTime]::Parse($p.createdAt); $age = ($todayDate - $dt).Days } catch { $age = 0 }
        }
    }
    $idades += $age

    $m2val = $null
    if ($p.projetoMetragem -and $p.projetoMetragem -ne '' -and $p.projetoMetragem -ne $null) {
        try { $m2val = [double]($p.projetoMetragem.ToString() -replace ',','.') } catch { $m2val = $null }
    }

    $q2Obras += [PSCustomObject]@{
        id = $p.id; cliente = $p.clienteNome; cidade = $p.projetoCidade
        fase = $p.faseAtual; consultor = $p.consultorNome; status = $p.status
        m2 = $m2val; idade = $age
    }
}

Write-Host "  Pipefy match: $matchedPipefy / $total_ativas"

$idadesSorted = $idades | Sort-Object
$idadeMedia = if ($idades.Count -gt 0) { [math]::Round(($idades | Measure-Object -Average).Average, 0) } else { 0 }
$idadeMediana = if ($idadesSorted.Count -gt 0) { $idadesSorted[[math]::Floor($idadesSorted.Count/2)] } else { 0 }
$n_lt90 = @($idades | Where-Object { $_ -lt 90 }).Count
$n_90_180 = @($idades | Where-Object { $_ -ge 90 -and $_ -lt 180 }).Count
$n_180_plus = @($idades | Where-Object { $_ -ge 180 }).Count
$n_270_plus = @($idades | Where-Object { $_ -ge 270 }).Count

Write-Host "  Ages: media=$idadeMedia, mediana=$idadeMediana"
Write-Host "  <90=$n_lt90, 90-180=$n_90_180, 180+=$n_180_plus, 270+=$n_270_plus"

# Top fases
$topFases = [ordered]@{}
foreach ($g in ($ativas | Group-Object -Property { if ($_.faseAtual) { $_.faseAtual } else { 'SEM FASE' } } | Sort-Object Count -Descending | Select-Object -First 15)) {
    $topFases[$g.Name] = $g.Count
}

# Top UFs
$ufLookup = @{
    'SÃO PAULO'='SP';'SAO PAULO'='SP';'CAMPINAS'='SP';'SANTOS'='SP';'BERTIOGA'='SP';'ATIBAIA'='SP';'PIRACICABA'='SP';'ITU'='SP';'MOGI DAS CRUZES'='SP';'BRAGANÇA PAULISTA'='SP';'SÃO CAETANO DO SUL'='SP';'SÃO BERNARDO DO CAMPO'='SP';'CARAPICUÍBA'='SP'
    'RIO DE JANEIRO'='RJ';'CABO FRIO'='RJ'
    'CURITIBA'='PR';'CASCAVEL'='PR';'GUARATUBA'='PR';'JAGUARIAÍVA'='PR'
    'BELO HORIZONTE'='MG';'NOVA LIMA'='MG'
    'BRASILIA'='DF';'BRASÍLIA'='DF'
    'FLORIANÓPOLIS'='SC';'PORTO BELO'='SC'
    'PORTO ALEGRE'='RS';'PELOTAS'='RS'
    'PORTO SEGURO'='BA'
}
$ufDist = @{}
foreach ($p in $ativas) {
    $c = if ($p.projetoCidade) { $p.projetoCidade.ToUpper().Trim() } else { '' }
    $uf = 'OUTROS'
    if ($ufLookup.ContainsKey($c)) { $uf = $ufLookup[$c] }
    elseif ($c -match 'SÃO PAULO|SAO PAULO' -or $c -match '/\s*SP') { $uf = 'SP' }
    elseif ($c -match 'RIO DE JANEIRO' -or $c -match '/\s*RJ') { $uf = 'RJ' }
    elseif ($c -match 'CURIT' -or $c -match '/\s*PR') { $uf = 'PR' }
    elseif ($c -match '/\s*RS') { $uf = 'RS' }
    elseif ($c -match '/\s*SC' -or $c -match '-\s*SC') { $uf = 'SC' }
    elseif ($c -match 'PORTO FELIZ|ITAIM|CEP\s*0') { $uf = 'SP' }
    if ($ufDist.ContainsKey($uf)) { $ufDist[$uf]++ } else { $ufDist[$uf] = 1 }
}
$topUfs = [ordered]@{}
foreach ($kv in ($ufDist.GetEnumerator() | Sort-Object Value -Descending)) { $topUfs[$kv.Key] = $kv.Value }

# Top cidades
$topCidades = [ordered]@{}
foreach ($g in ($ativas | Group-Object -Property { if ($_.projetoCidade) { $_.projetoCidade.ToUpper().Trim() } else { 'NAO INFORMADA' } } | Sort-Object Count -Descending | Select-Object -First 10)) {
    $topCidades[$g.Name] = $g.Count
}

# Top antigas
$sortedByAge = $q2Obras | Sort-Object -Property idade -Descending
$top30Antigas = @($sortedByAge | Select-Object -First 30 | ForEach-Object {
    [PSCustomObject]@{
        fase = $_.fase; id_curto = $_.id.Substring(0, 8); consultor = $_.consultor
        cliente = $_.cliente; idade = $_.idade
        metragem = if ($_.m2) { $_.m2.ToString("F2", [System.Globalization.CultureInfo]::InvariantCulture) } else { "0.00" }
        status = $_.status; cidade = $_.cidade
    }
})
$top10Antigas = @($top30Antigas | Select-Object -First 10)
Write-Host "  Top antiga: $($top30Antigas[0].cliente) idade=$($top30Antigas[0].idade)"

$agg = [ordered]@{
    n_270_plus=$n_270_plus; status_dist=$statusDist; top30_antigas=$top30Antigas; top10_antigas=$top10Antigas
    top_consultores=$consultorCount; top_fases=$topFases; top_ufs=$topUfs; top_cidades=$topCidades
    total_ativas=$total_ativas; total_obras=$total_obras
    metragem_total=[math]::Round($metTotal,2); metragem_mediana=[math]::Round($metMediana,2)
    idade_media=$idadeMedia; idade_mediana=$idadeMediana
    n_180_plus=$n_180_plus; n_lt90=$n_lt90; n_90_180=$n_90_180
    sem_consultor_ativas=$semConsultorAtivas
}

# 5. Q2_DIAG
Write-Host "`n[5/7] Building Q2_DIAG..."
$q2Diag = [ordered]@{}
if ($existing.Q2_DIAG -is [PSCustomObject]) {
    foreach ($prop in $existing.Q2_DIAG.PSObject.Properties) { $q2Diag[$prop.Name] = $prop.Value }
}
if ($analiseResp -and $analiseResp.atRisk) {
    foreach ($ar in $analiseResp.atRisk) {
        $diagId = if ($ar.id) { $ar.id } elseif ($ar.projectId) { $ar.projectId } else { $null }
        $diagText = if ($ar.diagnostico) { $ar.diagnostico } elseif ($ar.description) { $ar.description } else { $null }
        $clientName = if ($ar.clienteNome) { $ar.clienteNome } else { '' }
        if ($diagId -and $diagText) { $q2Diag[$diagId] = "PROJETO: $clientName | $diagText" }
    }
}
Write-Host "  Q2_DIAG: $($q2Diag.Count) entries"

# 6. Q3
Write-Host "`n[6/7] Building Q3..."
$q3Equipes = if ($equipesResp) { $equipesResp } else { $existing.Q3_EQUIPES }
Write-Host "  Q3_EQUIPES: $(if ($equipesResp) { 'fresh' } else { 'reused' })"

$q3ObrasHoje = $existing.Q3_OBRAS_HOJE
if ($escalacaoResp -is [PSCustomObject]) {
    $ek = @($escalacaoResp.PSObject.Properties.Name)
    if ($ek.Count -gt 0) { $q3ObrasHoje = $escalacaoResp; Write-Host "  Q3_OBRAS_HOJE: fresh ($($ek.Count) keys)" }
    else { Write-Host "  Q3_OBRAS_HOJE: reused (empty)" }
} else { Write-Host "  Q3_OBRAS_HOJE: reused" }

# 7. Write
Write-Host "`n[7/7] Writing JSON..."

$result = [ordered]@{
    snapshot_date = $today
    AGG = $agg
    EXT = $existing.EXT
    Q2_OBRAS = $q2Obras
    Q2_DIAG = $q2Diag
    Q4_RESP_OPS = $existing.Q4_RESP_OPS
    Q4_ESCALACAO = $existing.Q4_ESCALACAO
    Q4_DATAS = $existing.Q4_DATAS
    Q1_PLAN_OBRAS = $existing.Q1_PLAN_OBRAS
    SYNC_LIMBO = $existing.SYNC_LIMBO
    SYNC_ESCALACAO_INV = $existing.SYNC_ESCALACAO_INV
    SYNC_BUGARRAY = $existing.SYNC_BUGARRAY
    Q1_TOTAIS = $existing.Q1_TOTAIS
    Q3_EQUIPES = $q3Equipes
    Q3_OBRAS_HOJE = $q3ObrasHoje
}

$json = $result | ConvertTo-Json -Depth 20 -Compress

# Fix PowerShell's unicode escaping: convert \uXXXX back to actual chars
$json = [System.Text.RegularExpressions.Regex]::Replace($json, '\\u([0-9a-fA-F]{4})', {
    param($m)
    [char][int]('0x' + $m.Groups[1].Value)
})

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($jsonPath, $json, $utf8NoBom)

$fi = Get-Item $jsonPath
Write-Host "`n=== DONE ==="
Write-Host "File: $jsonPath"
Write-Host "Size: $($fi.Length) bytes ($([math]::Round($fi.Length/1024,1)) KB)"
Write-Host "snapshot_date: $today"
Write-Host "Q2_OBRAS: $total_ativas"
Write-Host "AGG.total_ativas: $total_ativas"
Write-Host "AGG.total_obras: $total_obras"
Write-Host "AGG.idade_media: $idadeMedia"
Write-Host "AGG.n_270_plus: $n_270_plus"
Write-Host "AGG.n_180_plus: $n_180_plus"
Write-Host "Pipefy matched: $matchedPipefy / $total_ativas"

# Validate
$testRaw = [System.IO.File]::ReadAllText($jsonPath, [System.Text.Encoding]::UTF8)
try {
    $test = $testRaw | ConvertFrom-Json
    Write-Host "Valid JSON: YES (keys=$($test.PSObject.Properties.Name.Count))"
} catch {
    Write-Host "INVALID JSON: $_"
}

# Check encoding - look for SÃO PAULO
if ($json.Contains('SÃO PAULO')) { Write-Host "UTF-8 encoding: CORRECT (accents preserved)" }
elseif ($json.Contains('S\u00c3O')) { Write-Host "UTF-8 encoding: ESCAPED (unicode escapes - OK)" }
else { Write-Host "UTF-8 encoding: CHECK MANUALLY" }
