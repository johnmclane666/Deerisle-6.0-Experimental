# ==============================================================================
#                     ULTIMATE DEER ISLE HALL OF FAME BOT
# ==============================================================================

# --- KONFIGURATION ---

# 1. GAME SERVERS PATHS TO .JSON
$serverFiles = @(
    "D:\halloffame.json"    
)

# 2. DEINE WEBHOOK URL (Fest hinterlegt und global verfügbar gemacht)
$Global:MyDiscordUrl = "YOUR WEBHOOK LINK"
$Global:MyDiscordUrl = $Global:MyDiscordUrl.Trim()

# Pfad zur lokalen Speicherdatei
$scriptPath = $PSScriptRoot
if (-not $scriptPath) { $scriptPath = "." }
$botDataPath = "$scriptPath\bot_data.json"

# Emojis
$EmojiRocket   = [char]::ConvertFromUtf32(0x1F680)
$EmojiGold     = [char]::ConvertFromUtf32(0x1F947)
$EmojiSilver   = [char]::ConvertFromUtf32(0x1F948)
$EmojiBronze   = [char]::ConvertFromUtf32(0x1F949)
$EmojiMap      = [char]::ConvertFromUtf32(0x1F5FA)
$EmojiZap      = [char]::ConvertFromUtf32(0x26A1)
$EmojiSearch   = [char]::ConvertFromUtf32(0x1F50D)
$EmojiCalendar = [char]::ConvertFromUtf32(0x1F4C5)
$EmojiSkull    = [char]::ConvertFromUtf32(0x1F480)

# --- DEBUGGING VOR START ---
Write-Host "--- SYSTEM CHECK ---" -ForegroundColor Cyan
if ([string]::IsNullOrWhiteSpace($Global:MyDiscordUrl) -or $Global:MyDiscordUrl.Length -lt 20) {
    Write-Host "FEHLER: Webhook URL ist kaputt!" -ForegroundColor Red
    exit
}
Write-Host "Webhook URL geladen." -ForegroundColor DarkGray
Write-Host "--------------------" -ForegroundColor Cyan
# -----------------------

# --- HILFSFUNKTIONEN ---

# Übersetzt den Nummern-Code in lesbare Schwierigkeitsgrade
function Get-DifficultyName {
    param ([int]$diffCode)
    switch ($diffCode) {
        0 { return "Easy" }
        1 { return "Normal" }
        2 { return "Hard" }
        3 { return "Nightmare" }
        default { return "Unknown ($diffCode)" }
    }
}

# --- DISCORD FUNKTIONEN ---

function Send-DiscordMessage {
    param ($PayloadContent)
    try {
        $urlToUse = $Global:MyDiscordUrl
        if (-not $urlToUse) { return $null }

        $finalUrl = $urlToUse + "?wait=true"
        $jsonPayload = $PayloadContent | ConvertTo-Json -Depth 10
        $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonPayload)
        
        $response = Invoke-RestMethod -Uri $finalUrl -Method Post -ContentType 'application/json; charset=utf-8' -Body $utf8Bytes
        return $response.id
    }
    catch { 
        Write-Host "Fehler beim Senden: $($_.Exception.Message)" -ForegroundColor Red
        return $null 
    }
}

function Edit-DiscordMessage {
    param ($MessageId, $PayloadContent)
    try {
        $urlToUse = $Global:MyDiscordUrl
        if (-not $urlToUse) { return $false }

        $cleanUrl = $urlToUse.Split('?')[0]
        $editUrl = "$cleanUrl/messages/$MessageId"
        
        $jsonPayload = $PayloadContent | ConvertTo-Json -Depth 10
        $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonPayload)
        
        Invoke-RestMethod -Uri $editUrl -Method Patch -ContentType 'application/json; charset=utf-8' -Body $utf8Bytes
        return $true
    }
    catch { return $false }
}

function Delete-DiscordMessage {
    param ($MessageId)
    try {
        $urlToUse = $Global:MyDiscordUrl
        $cleanUrl = $urlToUse.Split('?')[0]
        $deleteUrl = "$cleanUrl/messages/$MessageId"
        Invoke-RestMethod -Uri $deleteUrl -Method Delete
        Write-Host "Nachricht $MessageId gelöscht." -ForegroundColor DarkGray
    }
    catch { Write-Host "Fehler beim Löschen: $($_.Exception.Message)" -ForegroundColor Red }
}

# --- HAUPTPROGRAMM ---

try {
    # 1. Bot-Daten laden
    $storedMessageIds = @()
    if (Test-Path $botDataPath) {
        try {
            $storedData = Get-Content $botDataPath | ConvertFrom-Json
            if ($storedData.messageIds) { $storedMessageIds = $storedData.messageIds }
        } catch {
            Write-Host "Warnung: Konnte bot_data.json nicht lesen. Starte frisch." -ForegroundColor Yellow
        }
    }
    
    # 2. Server-Daten laden & Globale Statistiken sammeln
    $globalSurvivors = @()
    
    $globalStats = @{
        Attempts_Easy = 0; Success_Easy = 0;
        Attempts_Normal = 0; Success_Normal = 0;
        Attempts_Hard = 0; Success_Hard = 0;
        Attempts_Nightmare = 0; Success_Nightmare = 0;
    }

    foreach ($path in $serverFiles) {
        if (Test-Path $path) {
            try {
                $jsonData = Get-Content -Raw -Path $path | ConvertFrom-Json
                
                # Globale Statistiken addieren (falls vorhanden)
                if ($null -ne $jsonData.Attempts_Easy) { $globalStats.Attempts_Easy += $jsonData.Attempts_Easy }
                if ($null -ne $jsonData.Success_Easy) { $globalStats.Success_Easy += $jsonData.Success_Easy }
                if ($null -ne $jsonData.Attempts_Normal) { $globalStats.Attempts_Normal += $jsonData.Attempts_Normal }
                if ($null -ne $jsonData.Success_Normal) { $globalStats.Success_Normal += $jsonData.Success_Normal }
                if ($null -ne $jsonData.Attempts_Hard) { $globalStats.Attempts_Hard += $jsonData.Attempts_Hard }
                if ($null -ne $jsonData.Success_Hard) { $globalStats.Success_Hard += $jsonData.Success_Hard }
                if ($null -ne $jsonData.Attempts_Nightmare) { $globalStats.Attempts_Nightmare += $jsonData.Attempts_Nightmare }
                if ($null -ne $jsonData.Success_Nightmare) { $globalStats.Success_Nightmare += $jsonData.Success_Nightmare }

                # Survivors sammeln
                if ($null -ne $jsonData.Survivors -and $jsonData.Survivors.Count -gt 0) {
                    $globalSurvivors += $jsonData.Survivors
                }
            } catch { Write-Host "Fehler beim Lesen von $path" -ForegroundColor Red }
        }
    }

    # 3. Daten sortieren
    $hasSurvivors = $globalSurvivors.Count -gt 0
    if ($hasSurvivors) {
        # NEUE SORTIERUNG: 
        # 1. MaxDifficulty (Absteigend - Schwerste zuerst)
        # 2. SurvivalTimeSeconds (Aufsteigend - Schnellste Zeit zuerst)
        # 3. DiscoveryProgress (Absteigend - Höchste Rate zuerst bei Zeitgleichstand)
        $sortedSurvivors = $globalSurvivors | Sort-Object -Property `
            @{Expression="MaxDifficulty"; Descending=$true}, `
            @{Expression="SurvivalTimeSeconds"; Descending=$false}, `
            @{Expression="DiscoveryProgress"; Descending=$true}
    } else {
        $sortedSurvivors = @()
    }

    # Pagination Berechnung
    $itemsPerPage = 10
    $neededPages = if ($hasSurvivors) { [math]::Ceiling($sortedSurvivors.Count / $itemsPerPage) } else { 1 }

    $newMessageIds = @()

    # 4. Loop durch Seiten
    for ($pageIndex = 0; $pageIndex -lt $neededPages; $pageIndex++) {
        
        $desc = ""

        # Global Stats Header auf Seite 1 hinzufügen
        if ($pageIndex -eq 0) {
            $desc += "📊 **GLOBAL SERVER STATS**`n"
            $desc += "🟢 **Easy:** $($globalStats.Success_Easy) / $($globalStats.Attempts_Easy) Wins`n"
            $desc += "🟡 **Normal:** $($globalStats.Success_Normal) / $($globalStats.Attempts_Normal) Wins`n"
            $desc += "🔴 **Hard:** $($globalStats.Success_Hard) / $($globalStats.Attempts_Hard) Wins`n"
            $desc += "☠️ **Nightmare:** $($globalStats.Success_Nightmare) / $($globalStats.Attempts_Nightmare) Wins`n"
            $desc += "━━━━━━━━━━━━━━━━━━━━━━`n`n"
        }

        # --- PAYLOAD BAUEN ---
        if (-not $hasSurvivors) {
            $title = "$EmojiRocket Global Server Speedrun"
            $desc += "$EmojiSearch **No entries found yet!**`n`n**Login and start the run!**"
            $color = 9807270
            $footerText = "Status: Waiting..."
        } else {
            $startIndex = $pageIndex * $itemsPerPage
            $chunk = $sortedSurvivors | Select-Object -Skip $startIndex -First $itemsPerPage
            
            $rank = $startIndex + 1
            
            foreach ($survivor in $chunk) {
                $rankText = switch ($rank) { 1 {$EmojiGold} 2 {$EmojiSilver} 3 {$EmojiBronze} Default {"**#$rank**"} }
                
                # Schwierigkeit ermitteln
                $diffName = Get-DifficultyName -diffCode $survivor.MaxDifficulty
                
                # NEUES LAYOUT:
                # 1. Zeile: Name und Schwierigkeit
                # 2. Zeile: Zeit (Fokus) und Discovery
                # 3. Zeile: Info (Datum, Uhrzeit, ID)
                $desc += "$rankText **$($survivor.Name)** | $EmojiSkull **$diffName**`n"
                $desc += "$EmojiZap **$($survivor.SurvivalTime)** | $EmojiMap $([math]::Round($survivor.DiscoveryProgress, 1))%`n"
                $desc += "*( $($survivor.Date), $($survivor.Time), ID: $($survivor.EndgameID) )*`n`n"
                
                $rank++
            }
            
            $endRank = $rank - 1
            $title = "$EmojiRocket Global Speedrun (Rank $($startIndex + 1) - $endRank)"
            $color = 16711680 
            $footerText = "Page $($pageIndex + 1) | Total: $($sortedSurvivors.Count) Players"
        }

        $payload = @{
            username = "Deer Isle Bot"
            embeds = @(@{ 
                title = $title; 
                description = $desc; 
                color = $color; 
                footer = @{ text = $footerText } 
            })
        }

        # --- SENDEN / EDITIEREN ---
        $currentMsgId = $null
        if ($pageIndex -lt $storedMessageIds.Count) {
            $currentMsgId = $storedMessageIds[$pageIndex]
        }

        if ($currentMsgId) {
            Write-Host "Aktualisiere Seite $($pageIndex + 1)..." -ForegroundColor Cyan
            $success = Edit-DiscordMessage -MessageId $currentMsgId -PayloadContent $payload
            
            if ($success) {
                $newMessageIds += $currentMsgId
            } else {
                Write-Host "Nachricht war weg, sende neu..." -ForegroundColor Yellow
                $newId = Send-DiscordMessage -PayloadContent $payload
                if ($newId) { $newMessageIds += $newId }
            }
        } else {
            Write-Host "Erstelle neue Seite $($pageIndex + 1)..." -ForegroundColor Green
            $newId = Send-DiscordMessage -PayloadContent $payload
            if ($newId) { $newMessageIds += $newId }
        }

        Start-Sleep -Seconds 1
    }

    # 5. Cleanup (Löscht überschüssige alte Seiten, falls Spieler aus der Liste fallen)
    if ($storedMessageIds.Count -gt $neededPages) {
        for ($i = $neededPages; $i -lt $storedMessageIds.Count; $i++) {
            $idToDelete = $storedMessageIds[$i]
            Delete-DiscordMessage -MessageId $idToDelete
        }
    }

    # 6. Speichern
    $saveData = @{ messageIds = $newMessageIds; lastUpdate = (Get-Date).ToString() }
    $saveData | ConvertTo-Json | Set-Content -Path $botDataPath -Force
    Write-Host "Fertig! Datenbank aktualisiert." -ForegroundColor Green

} catch {
    Write-Host "CRITICAL ERROR: $($_.Exception.Message)" -ForegroundColor Red
}