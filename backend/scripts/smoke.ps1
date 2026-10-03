param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$DemoToken = $env:DEMO_API_TOKEN,
    [switch]$IncludeClaude
)
$ErrorActionPreference = "Stop"
if (-not $DemoToken) { throw "Set DEMO_API_TOKEN in this PowerShell session to the local backend/.env value." }
$headers = @{ Authorization = "Bearer $DemoToken" }
function Invoke-Milo([string]$Method, [string]$Path, $Body = $null, [string]$Key = "") {
    $requestHeaders = $headers.Clone()
    if ($Key) { $requestHeaders["Idempotency-Key"] = $Key }
    $params = @{ Method = $Method; Uri = "$BaseUrl$Path"; Headers = $requestHeaders; TimeoutSec = 300 }
    if ($null -ne $Body) { $params.ContentType = "application/json"; $params.Body = ($Body | ConvertTo-Json -Depth 12) }
    # Windows PowerShell does not enumerate Invoke-RestMethod's top-level JSON array.
    # Returning a captured value makes collection endpoints behave normally in callers.
    $response = Invoke-RestMethod @params
    return $response
}
Invoke-RestMethod "$BaseUrl/health"
Invoke-Milo GET "/profile"
Invoke-Milo GET "/today"
$foodKey = [guid]::NewGuid().ToString()
$food = @{ meal = "breakfast"; name = "Synthetic smoke: two eggs and toast"; quantity = "2 eggs, 2 slices"; kcal = 320; protein_g = 18; carbs_g = 30; fat_g = 14; source = "synthetic"; nutrition_provenance = "synthetic" }
$first = Invoke-Milo POST "/food" $food $foodKey
$replay = Invoke-Milo POST "/food" $food $foodKey
if ($first.id -ne $replay.id) { throw "Replay created a different food row" }
Invoke-Milo GET "/food"
Invoke-Milo GET "/today"
$workouts = @(Invoke-Milo GET "/workouts")
if ($workouts.Count) {
    $w = Invoke-Milo POST "/workouts/$($workouts[-1].id)/start" $null ([guid]::NewGuid().ToString())
    $set = $w.exercises[0].sets[0]
    Invoke-Milo PATCH "/sets/$($set.id)" @{ kg = $set.kg; reps = $set.reps; done = $true } ([guid]::NewGuid().ToString())
    Invoke-Milo POST "/workouts/$($w.id)/finish" $null ([guid]::NewGuid().ToString())
    Invoke-Milo GET "/sessions"
}
Invoke-Milo POST "/goals" @{ title = "Synthetic smoke: train three times weekly"; kind = "habit"; unit = "sessions"; target_value = 3 } ([guid]::NewGuid().ToString())
if ($IncludeClaude) {
    # Explicit switch: these calls can incur Anthropic charges.
    foreach ($prompt in @("Create a three-day dumbbell workout", "Create a vegetarian diet plan", "What should I eat for dinner?")) {
        Invoke-Milo POST "/chat" @{ message = $prompt } ([guid]::NewGuid().ToString())
    }
    $proposal = Invoke-Milo POST "/chat" @{ message = "Create a vegetarian diet plan"; plan_mode = "propose" } ([guid]::NewGuid().ToString())
    foreach ($card in $proposal.cards) {
        if ($card.status -eq "pending") { Invoke-Milo POST "/cards/$($card.id)/apply" $null ([guid]::NewGuid().ToString()) }
    }
}
Invoke-Milo GET "/goals"
Write-Output "Smoke requests completed. Synthetic writes were retained for inspection."
