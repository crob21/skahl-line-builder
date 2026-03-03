# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app_simple.py
# App runs at http://127.0.0.1:5001
```

### Run in production mode
```bash
gunicorn app_simple:app
```

### Run with Discord bot
```bash
# Requires DISCORD_BOT_TOKEN set in environment or .env
python start_with_discord.py
```

### Tests
```bash
# Integration tests – requires the app running on port 5001
python tests/test_app.py

# Discord bot tests – requires DISCORD_BOT_TOKEN and app running
python test_discord_bot.py
```

### Data utilities
```bash
python migrate_to_db.py          # Migrate JSON team files into the database
python backup_teams.py           # Backup all DB teams to data/teams_backup.json
python backup_teams.py restore   # Restore teams from backup
```

## Architecture

Flask SPA — `templates/index.html` contains all CSS, HTML, and JavaScript inline. The backend exposes a JSON REST API consumed by the frontend via `fetch`. No npm, no build step.

### Module responsibilities

- `app_simple.py` — Flask app factory, session management, shared-lines view route (`/lines/<id>`)
- `routes.py` — All `/api/*` endpoints; registers via `init_routes(app)`
- `hockey_manager.py` — `HockeyTeamManager`: in-memory player/lines state with JSON file persistence per session
- `database.py` — `Database` class: dual SQLite/PostgreSQL backend; singleton `db` instance imported by routes
- `utils.py` — File I/O helpers, CSV parsing, session/line ID generation
- `config.py` — All constants (paths, colors, positions, line structure); runs `ensure_directories()` on import

### Data flow

Each HTTP request instantiates a `HockeyTeamManager` backed by a per-session JSON file at `data/sessions/<session_id>.json`. The `db` singleton is used separately for persistent team storage. Shared lines are stored as individual JSON files under `data/shared_lines/`.

### Database

- **Local**: SQLite at `data/line_walrus.db` (auto-selected when `DATABASE_URL` is absent)
- **Production**: PostgreSQL via `DATABASE_URL` env var (injected automatically by Render per `render.yaml`)
- Query syntax switches between `?` (SQLite) and `%s` (PostgreSQL) at module load time
- On startup, `_auto_restore_teams()` repopulates an empty database from `data/teams_backup.json`

### Hockey data model

```
Player: { id, name, jersey, roster_position (FORWARD/DEFENSE/GOALIE/SKATER), affiliate (bool), location (bench|spares) }
Lines:  { 1: { LW, C, RW, LD, RD, G }, 2: { LW, C, RW, LD, RD }, 3: { LW, C, RW, LD, RD } }
```

Line 1 is the only line with a goalie slot (`G`).

## Key Gotchas

**Line key type inconsistency**: `HockeyTeamManager.lines` stores line numbers as integers, but JSON serialization converts them to strings. Both `routes.py` and `hockey_manager.py` explicitly call `int(line)` on incoming values.

**Session isolation**: `HockeyTeamManager` is instantiated fresh on every request from the session file — no shared in-process state between users.

**Dual API methods**: `HockeyTeamManager` has legacy string-based methods (`add_player_legacy`, etc.) and new dict/id-based methods (`add_player`, etc.). The web API exclusively uses the new id-based methods.

**CSV format**: `parse_csv_data()` expects columns: `First Name`, `Last Name`, `Jersey Number`, `Position`, `Affiliate` (or `Affiliate Status`). Compatible with SportNinja CSV exports.

**Team filename convention**: Team names are converted via `team_name.lower().replace(' ', '_') + '.json'`. `save_team` upserts by `filename` — renaming a team creates a duplicate.

**Static frontend**: `static/index.html` exists but is unused. The live template is `templates/index.html`.

**Discord bot**: Optional companion requiring `DISCORD_BOT_TOKEN` and `LINE_WALRUS_URL`. `discord_requirements.txt` is redundant — `requirements.txt` already includes `discord.py` and `aiohttp`.

## Deployment

Render is the production host. `render.yaml` provisions a web service (`gunicorn app_simple:app`) and a PostgreSQL database (`line-walrus-db`). Pushes to `main` trigger auto-deploy. Run `python backup_teams.py` before destroying the Render database.
