# Offline recovery checks with mocked Git; does not touch actual .git or any network.
param([string]$SourceRoot)
$ErrorActionPreference = "Stop"
if (-not $SourceRoot) { $SourceRoot = Join-Path $PSScriptRoot "../.." }
$sourcePath = (Resolve-Path -LiteralPath $SourceRoot).Path
$scriptsPath = Join-Path $sourcePath 'backend/scripts'
$scriptPath = Join-Path $scriptsPath "prepare_checkout.ps1"
$scriptBody = [scriptblock]::Create((Get-Content -LiteralPath $scriptPath -Raw))
$baseline = Get-Content -LiteralPath (Join-Path $scriptsPath "upstream_baseline.json") -Raw | ConvertFrom-Json
$testRoot = Join-Path $sourcePath ("backend/.recovery-tests/" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
$gitCalls = [Collections.Generic.List[string]]::new()
$conflictMode = $false
function Assert-Recovery($Condition, $Message) {
    if (-not $Condition) { throw "FAIL: $Message" }
}
function git {
    $gitArgs = @($args)
    $gitCalls.Add(($gitArgs -join ' '))
    $global:LASTEXITCODE = 0
    if ($gitArgs[0] -eq 'clone') {
        $clonePath = $gitArgs[-1]
        foreach ($folder in @('ios', 'design', 'backend/app')) {
            New-Item -ItemType Directory -Path (Join-Path $clonePath $folder) -Force | Out-Null
        }
        foreach ($relative in @('ios/README.md', 'design/README.md', 'backend/app/main.py')) {
            Copy-Item -LiteralPath (Join-Path $sourcePath 'README.md') -Destination (Join-Path $clonePath $relative)
        }
    } elseif ($gitArgs[2] -eq 'rev-parse') {
        $relative = $gitArgs[-1].Substring(5)
        $expected = $baseline.files.PSObject.Properties[$relative]
        if ($conflictMode -and $relative -eq 'backend/app/main.py') {
            return '0000000000000000000000000000000000000000'
        }
        if ($expected) { return $expected.Value }
        $global:LASTEXITCODE = 1
    } elseif ($gitArgs[2] -notin @('switch', 'status')) {
        throw 'Unexpected mocked Git command'
    }
}

$successTarget = $testRoot.Substring($sourcePath.Length + 1) + '/success'
& $scriptBody -SourceRoot $sourcePath -Target $successTarget | Out-Null
$successPath = Join-Path $sourcePath $successTarget
$originalHash = (Get-FileHash -LiteralPath (Join-Path $sourcePath 'README.md')).Hash
foreach ($relative in @('ios/README.md', 'design/README.md')) {
    Assert-Recovery ((Get-FileHash -LiteralPath (Join-Path $successPath $relative)).Hash -eq $originalHash) "Partner files preserved: $relative"
}
Assert-Recovery (Test-Path -LiteralPath (Join-Path $successPath 'backend/app/services.py')) 'Backend implementation copied'
Assert-Recovery (Test-Path -LiteralPath (Join-Path $successPath 'TEAM_STATUS.md')) 'Handoff copied'
foreach ($relative in @('backend/.env', 'backend/.venv', 'backend/verification-results', 'backend/.recovery-tests')) {
    Assert-Recovery (-not (Test-Path -LiteralPath (Join-Path $successPath $relative))) "Private/generated files excluded: $relative"
}
$beforeCalls = $gitCalls.Count
foreach ($target in @($successTarget, '../outside-workspace')) {
    $failed = $false
    try { & $scriptBody -SourceRoot $sourcePath -Target $target | Out-Null } catch { $failed = $true }
    Assert-Recovery $failed 'Existing/outside target refused'
    Assert-Recovery ($gitCalls.Count -eq $beforeCalls) 'No Git invoked on unsafe target'
}

$conflictMode = $true
$conflictTarget = $testRoot.Substring($sourcePath.Length + 1) + '/conflict'
$failed = $false
try { & $scriptBody -SourceRoot $sourcePath -Target $conflictTarget | Out-Null } catch {
    $failed = $_.Exception.Message -like '*Upstream changed overlapping files*'
}
Assert-Recovery $failed 'Overlapping upstream change refused'
$conflictPath = Join-Path $sourcePath $conflictTarget
Assert-Recovery (-not (Test-Path -LiteralPath (Join-Path $conflictPath 'backend/app/services.py'))) 'No overlay copied after conflict'
Assert-Recovery ((Get-FileHash -LiteralPath (Join-Path $conflictPath 'backend/app/main.py')).Hash -eq $originalHash) 'Upstream file unchanged after conflict'
Assert-Recovery (-not ($gitCalls | Where-Object { $_ -match '(reset|push|clean|checkout --)' })) 'No destructive or remote-write command'
Write-Output 'PASS: mocked recovery copy, exclusions, partner preservation, unsafe-target rejection and upstream conflict guard. No actual clone/branch/push tested.'
Write-Output "Retained synthetic test files in ignored $testRoot; original workspace unchanged."
