import json
import os

# --- KONFIGURATION ---
# Pfade zu deinen .json Dateien
SERVER_FILES = [
    r"D:\halloffame.json"
]

# Zielpfad für die generierte Webseite
OUTPUT_HTML = "Deer_Isle_Hall_of_Fame.html"

# --- HILFSFUNKTIONEN ---
def get_difficulty_name(diff_code):
    mapping = {0: "Easy", 1: "Normal", 2: "Hard", 3: "Nightmare"}
    return mapping.get(diff_code, f"Unknown ({diff_code})")

def get_difficulty_color(diff_code):
    mapping = {0: "#4CAF50", 1: "#FFEB3B", 2: "#FF9800", 3: "#F44336"}
    return mapping.get(diff_code, "#FFFFFF")

# --- GEMEINSAMES CSS FÜR ALLE SEITEN ---
COMMON_CSS = """
        :root {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --easy: #4ade80;
            --normal: #facc15;
            --hard: #fb923c;
            --nightmare: #f87171;
        }
        
        body {
            margin: 0; padding: 0;
            font-family: 'Montserrat', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
            color: var(--text-main);
            min-height: 100vh;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        header { text-align: center; margin-bottom: 50px; }
        
        h1 {
            font-size: 3rem; font-weight: 900; text-transform: uppercase;
            margin: 0; background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0px 4px 20px rgba(56, 189, 248, 0.3);
        }
        
        .subtitle { font-size: 1.2rem; color: var(--text-muted); margin-top: 10px; }
        
        /* Stats Dashboard */
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 50px;
        }
        
        .stat-card {
            background: var(--card-bg); backdrop-filter: blur(10px);
            border-radius: 15px; padding: 25px; text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); transition: transform 0.3s ease;
        }
        
        .stat-card:hover { transform: translateY(-5px); }
        .stat-title { font-size: 1.2rem; font-weight: 700; margin-bottom: 15px; text-transform: uppercase; }
        .stat-numbers { font-family: 'Roboto Mono', monospace; font-size: 2rem; font-weight: 700; }
        .stat-label { font-size: 0.9rem; color: var(--text-muted); margin-top: 5px; }
        
        .easy-text { color: var(--easy); } .normal-text { color: var(--normal); }
        .hard-text { color: var(--hard); } .nightmare-text { color: var(--nightmare); }
        
        /* Leaderboard & Tables */
        .content-section {
            background: var(--card-bg); backdrop-filter: blur(10px);
            border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.05);
            overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 20px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); }
        th { background: rgba(0,0,0,0.2); font-weight: 700; text-transform: uppercase; font-size: 0.9rem; color: var(--text-muted); }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: rgba(255,255,255,0.02); }
        
        .rank { font-size: 1.5rem; font-weight: 900; width: 60px; text-align: center; }
        .rank-1 { color: #ffd700; text-shadow: 0 0 10px rgba(255,215,0,0.5); }
        .rank-2 { color: #c0c0c0; text-shadow: 0 0 10px rgba(192,192,192,0.5); }
        .rank-3 { color: #cd7f32; text-shadow: 0 0 10px rgba(205,127,50,0.5); }
        
        .player-name { font-weight: 700; font-size: 1.2rem; }
        .mono-text { font-family: 'Roboto Mono', monospace; }
        
        .diff-badge {
            display: inline-block; padding: 5px 12px; border-radius: 20px;
            font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
            background: rgba(255,255,255,0.1);
        }
        
        .meta-info { font-size: 0.8rem; color: var(--text-muted); margin-top: 5px; }
        
        /* Links & Buttons */
        .id-link { color: var(--accent); text-decoration: none; font-weight: 700; transition: text-shadow 0.3s; }
        .id-link:hover { text-shadow: 0 0 10px var(--accent); text-decoration: underline; }
        
        .back-btn {
            display: inline-flex; align-items: center; gap: 8px;
            margin-bottom: 30px; padding: 12px 24px;
            background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3);
            color: var(--accent); text-decoration: none; font-weight: 700;
            border-radius: 8px; transition: all 0.3s ease;
        }
        .back-btn:hover { background: rgba(56, 189, 248, 0.2); box-shadow: 0 0 15px rgba(56, 189, 248, 0.4); transform: translateX(-5px); }
        
        @media (max-width: 768px) { th, td { padding: 10px; } .hide-mobile { display: none; } }
"""

# --- NEUE FUNKTION: DETAILSEITEN GENERIEREN ---
def generate_detail_pages(survivors, base_filename):
    # Gruppiere Spieler nach Endgame ID
    runs = {}
    for s in survivors:
        eid = s.get("EndgameID", "N/A")
        if eid == "N/A": 
            continue # Überspringe Einträge ohne ID (optional)
            
        if eid not in runs:
            runs[eid] = []
        runs[eid].append(s)
        
    # Erstelle für jede ID eine eigene HTML Datei
    for eid, players in runs.items():
        page_filename = f"run_{eid}.html"
        
        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Run Details - {eid}</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Roboto+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>{COMMON_CSS}</style>
</head>
<body>
    <div class="container">
        <a href="{base_filename}" class="back-btn">⬅ Zurück zur Hall of Fame</a>
        
        <header>
            <h1>Run Details</h1>
            <div class="subtitle">Endgame ID: <span class="mono-text" style="color: var(--text-main);">{eid}</span></div>
        </header>
        
        <div class="content-section">
            <table>
                <thead>
                    <tr>
                        <th>Player</th>
                        <th>Difficulty</th>
                        <th>Survival Time</th>
                        <th class="hide-mobile">Date / Time</th>
                    </tr>
                </thead>
                <tbody>
"""
        # Spieler für diesen Run auflisten
        for p in players:
            diff_code = p.get("MaxDifficulty", 0)
            diff_name = get_difficulty_name(diff_code)
            diff_color = get_difficulty_color(diff_code)
            
            html += f"""
                    <tr>
                        <td>
                            <div class="player-name">{p.get('Name', 'Unknown')}</div>
                        </td>
                        <td>
                            <span class="diff-badge" style="color: {diff_color}; border: 1px solid {diff_color}40;">
                                {diff_name}
                            </span>
                        </td>
                        <td class="mono-text" style="color: var(--accent); font-weight:700; font-size:1.1rem;">
                            ⚡ {p.get('SurvivalTime', '00:00:00')}
                        </td>
                        <td class="hide-mobile meta-info" style="font-size: 0.9rem;">
                            {p.get('Date', '')} at {p.get('Time', '')}
                        </td>
                    </tr>"""
                    
        html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
        # Detailseite speichern
        with open(page_filename, "w", encoding="utf-8") as f:
            f.write(html)


# --- HAUPTPROGRAMM ---
def generate_html(json_paths, output_file):
    # Globale Statistiken sammeln
    global_stats = {
        "Attempts_Easy": 0, "Success_Easy": 0,
        "Attempts_Normal": 0, "Success_Normal": 0,
        "Attempts_Hard": 0, "Success_Hard": 0,
        "Attempts_Nightmare": 0, "Success_Nightmare": 0,
    }
    
    survivors = []
    
    # JSON Dateien einlesen
    for path in json_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Statistiken addieren
                    for key in global_stats.keys():
                        global_stats[key] += data.get(key, 0)
                        
                    # Survivors sammeln
                    if "Survivors" in data:
                        survivors.extend(data["Survivors"])
            except Exception as e:
                print(f"Fehler beim Lesen von {path}: {e}")

    # Daten sortieren (MaxDifficulty Absteigend, Zeit Aufsteigend, Discovery Absteigend)
    survivors.sort(key=lambda x: (
        x.get("MaxDifficulty", 0), 
        -x.get("SurvivalTimeSeconds", 999999), 
        x.get("DiscoveryProgress", 0)
    ), reverse=True)
    
    # NEU: Generiere Detailseiten für die Endgame IDs
    generate_detail_pages(survivors, output_file)
    
    # HTML Aufbau für die Hauptseite
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Deer Isle Hall of Fame</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&family=Roboto+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>{COMMON_CSS}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Deer Isle Hall of Fame</h1>
            <div class="subtitle">Global Speedrun & Survival Leaderboard</div>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title easy-text">Easy</div>
                <div class="stat-numbers">{global_stats['Success_Easy']} / {global_stats['Attempts_Easy']}</div>
                <div class="stat-label">Wins / Attempts</div>
            </div>
            <div class="stat-card">
                <div class="stat-title normal-text">Normal</div>
                <div class="stat-numbers">{global_stats['Success_Normal']} / {global_stats['Attempts_Normal']}</div>
                <div class="stat-label">Wins / Attempts</div>
            </div>
            <div class="stat-card">
                <div class="stat-title hard-text">Hard</div>
                <div class="stat-numbers">{global_stats['Success_Hard']} / {global_stats['Attempts_Hard']}</div>
                <div class="stat-label">Wins / Attempts</div>
            </div>
            <div class="stat-card">
                <div class="stat-title nightmare-text">Nightmare</div>
                <div class="stat-numbers">{global_stats['Success_Nightmare']} / {global_stats['Attempts_Nightmare']}</div>
                <div class="stat-label">Wins / Attempts</div>
            </div>
        </div>
        
        <div class="content-section">
            <table>
                <thead>
                    <tr>
                        <th class="rank">#</th>
                        <th>Player</th>
                        <th>Difficulty</th>
                        <th>Survival Time</th>
                        <th class="hide-mobile">Discovery</th>
                        <th class="hide-mobile">Endgame ID</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Dynamische Tabellenzeilen für Survivor
    if not survivors:
        html += """<tr><td colspan="6" style="text-align:center; padding: 40px; color: #94a3b8;">Niemand hat den Run bis jetzt geschafft! Starte jetzt!</td></tr>"""
    else:
        for i, s in enumerate(survivors):
            rank = i + 1
            rank_class = f"rank-{rank}" if rank <= 3 else ""
            rank_display = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else f"{rank}"
            
            diff_code = s.get("MaxDifficulty", 0)
            diff_name = get_difficulty_name(diff_code)
            diff_color = get_difficulty_color(diff_code)
            eid = s.get('EndgameID', 'N/A')
            
            # Mache ID zum klickbaren Link (falls ID vorhanden ist)
            if eid != "N/A":
                eid_html = f'<a href="run_{eid}.html" class="id-link">{eid}</a>'
            else:
                eid_html = f'<span style="color: var(--text-muted);">{eid}</span>'
            
            html += f"""
                    <tr>
                        <td class="rank {rank_class}">{rank_display}</td>
                        <td>
                            <div class="player-name">{s.get('Name', 'Unknown')}</div>
                            <div class="meta-info hide-mobile">{s.get('Date', '')} at {s.get('Time', '')}</div>
                        </td>
                        <td>
                            <span class="diff-badge" style="color: {diff_color}; border: 1px solid {diff_color}40;">
                                {diff_name}
                            </span>
                        </td>
                        <td class="mono-text" style="color: var(--accent); font-weight:700; font-size:1.1rem;">
                            ⚡ {s.get('SurvivalTime', '00:00:00')}
                        </td>
                        <td class="hide-mobile">
                            🗺️ {round(s.get('DiscoveryProgress', 0), 1)}%
                        </td>
                        <td class="hide-mobile mono-text" style="font-size: 0.9rem;">
                            {eid_html}
                        </td>
                    </tr>"""
            
    html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    
    # HTML-Hauptdatei abspeichern
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Erfolg! Hauptwebseite in '{output_file}' sowie die dazugehörigen Detailseiten wurden erstellt.")

if __name__ == "__main__":
    generate_html(SERVER_FILES, OUTPUT_HTML)