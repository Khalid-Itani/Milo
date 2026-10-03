# Run in ordinary Windows PowerShell with Git/network access. Never resets or pushes.
param([string]$SourceRoot, [string]$Target = "prepared-checkout")
$ErrorActionPreference = "Stop"
if (-not $SourceRoot) {
    if (-not $PSScriptRoot) { throw "Pass -SourceRoot when running as a pasted script block." }
    $SourceRoot = Join-Path $PSScriptRoot "../.."
}
$sourcePath = (Resolve-Path -LiteralPath $SourceRoot).Path.TrimEnd('\', '/')
$targetPath = [IO.Path]::GetFullPath((Join-Path $sourcePath $Target))
if (-not $targetPath.StartsWith($sourcePath + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Target must be a new directory inside the source workspace."
}
if (Test-Path -LiteralPath $targetPath) { throw "Target already exists; nothing was overwritten. Choose another -Target." }
# Assemble the entire copy list before any Git operation. No partner-owned files.
$backendSource = Join-Path $sourcePath "backend"
$copies = @()
foreach ($file in Get-ChildItem -LiteralPath $backendSource -File -Recurse -Force) {
    $relative = $file.FullName.Substring($backendSource.Length + 1).Replace('\', '/')
    if ($relative -match '(^|/)(\.venv|__pycache__|\.pytest_cache|\.recovery-tests|verification-results)(/|$)' -or
        ($relative -match '(^|/)\.env($|\.)' -and $relative -ne '.env.example') -or
        $relative -match '\.(db|sqlite|sqlite3)(-wal|-shm|-journal)?$' -or
        ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
    $copies += [PSCustomObject]@{ Source = $file.FullName; Relative = "backend/$relative" }
}
foreach ($relative in @("README.md", "API_CONTRACT.md", "IOS_HANDOFF.md", "VERIFICATION.md", "TEAM_STATUS.md", "GIT_RECOVERY.md", "REMAINING_WORK_PROMPT.md", ".gitignore")) {
    $file = Join-Path $sourcePath $relative
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing handoff file: $relative" }
    $copies += [PSCustomObject]@{ Source = $file; Relative = $relative }
}
$baseline = Get-Content -LiteralPath (Join-Path $backendSource "scripts/upstream_baseline.json") -Raw | ConvertFrom-Json
Get-Command git -ErrorAction Stop | Out-Null
git clone --branch main --single-branch https://github.com/Khalid-Itani/Milo.git $targetPath
if ($LASTEXITCODE -ne 0) { throw "Clone failed. Original files are untouched; a partial target may remain." }
# Permit newer non-overlapping (e.g. iOS) commits, but never overwrite new backend work.
$conflicts = @()
foreach ($entry in $copies) {
    $expected = $baseline.files.PSObject.Properties[$entry.Relative]
    $actual = git -C $targetPath rev-parse --verify --quiet "HEAD:$($entry.Relative)"
    $existsUpstream = $LASTEXITCODE -eq 0
    if (($expected -and (-not $existsUpstream -or $actual -ne $expected.Value)) -or
        (-not $expected -and $existsUpstream)) { $conflicts += $entry.Relative }
}
if ($conflicts.Count) {
    throw ("Upstream changed overlapping files. Clone retained, but NO files copied. Review/merge these paths first: " + ($conflicts -join ', '))
}
git -C $targetPath switch -c backend/supabase-agent
if ($LASTEXITCODE -ne 0) { throw "Branch creation failed; no files copied." }
foreach ($entry in $copies) {
    $dest = Join-Path $targetPath $entry.Relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath $entry.Source -Destination $dest -Force
}
git -C $targetPath status --short
if ($LASTEXITCODE -ne 0) { throw "Status check failed; inspect the retained checkout." }
Write-Output "Prepared $targetPath on backend/supabase-agent. Original workspace/secrets untouched; no iOS/design edits, push or deployment."
