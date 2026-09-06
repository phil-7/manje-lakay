# Manje Lakay 🍽️

A personal recipe manager and meal planner. Add recipes by pasting a URL (auto-scraped) or typing them in by hand, plan what you're going to cook, and get a combined grocery list for everything on your plan.

Built with FastAPI, SQLAlchemy, SQLite, and server-rendered Jinja2 templates.

---

## 🚀 Features

- **Add recipes two ways:**
  - Paste a URL — pulls ingredients from the page's embedded JSON-LD (schema.org `Recipe` markup), then cleans each line down to just the core ingredient name using a local NLP model (`ingredient_parser_nlp`) — no external API calls, no cost.
  - Enter manually — title, ingredients, and instructions.
  - Instructions are **only ever typed in by hand**, never scraped, on purpose.
- **Planner** — manage an editable calendar with breakfast, lunch, and dinner slots for each day. Choose a saved recipe for any slot, replace it, or clear it. Start a new 1-, 2-, or 4-week calendar when needed.
- **All Recipes** — browse everything you've saved, with full edit and delete support.
- **Recipe search and sorting** — search by title or ingredient as you type, then sort by alphabetical order, ingredient count, or date added. Mark recipes as **staples** to keep them pinned at the top without automatically adding them to the Plan.
- **Recipe detail view** — click any recipe (Planner or All Recipes) to see its ingredients and instructions. Editing/deleting is only available from All Recipes.
- **Grocery List** — automatically built from whatever's currently on your Plan (no manual re-selecting), with a shopping checklist so you can check off what you've already got. Recipe names and quantities are hidden by default for a simpler shopping view; enable the checkbox to show them.
- **Responsive layout** — all tabs share a wider desktop layout and adapt to phones and other smaller screens.
- **Database backups** — a script to safely back up the SQLite database using SQLite's own backup API (safe to run while the app is live).

---

## 🧱 Project Structure

```
manje-lakay/
├── app/
│   ├── main.py            # FastAPI app setup, routers, static files
│   ├── database.py        # SQLAlchemy engine/session setup
│   ├── models.py          # Recipe, Ingredient (SQLAlchemy models)
│   ├── schemas.py         # Pydantic request/response models
│   ├── recipes.py         # Business logic: create/update/delete/toggle-plan
│   ├── grocery.py         # Grocery list building logic
│   ├── calendar.py        # Calendar settings and meal scheduling logic
│   ├── scraper.py         # URL -> JSON-LD -> cleaned ingredients pipeline
│   ├── routers/
│   │   ├── recipes.py     # /recipes API endpoints
│   │   ├── grocery.py     # /grocery-list API endpoint
│   │   ├── calendar.py     # /calendar API endpoints
│   │   └── pages.py       # HTML page routes (/, /add, /grocery, /all-recipes)
│   ├── templates/         # Jinja2 templates
│   │   ├── base.html      # Shared layout (nav, head) -- other pages extend this
│   │   ├── index.html     # Planner page
│   │   ├── add.html       # Add Recipe page
│   │   ├── grocery.html   # Grocery List page
│   │   └── recipes.html   # All Recipes page
│   └── static/             # CSS/JS served directly
│       ├── style.css
│       ├── planner.js
│       ├── add.js
│       ├── all-recipes.js
│       ├── grocery.js
│       ├── ingredient-fields.js # Shared fraction-aware ingredient inputs
│       └── recipe-modal.js # Shared recipe detail/edit popup
├── scripts/
│   └── backup_db.py       # Database backup utility
├── data/
│   ├── manje_lakay.db     # SQLite database (created automatically)
│   └── backups/            # Timestamped backups (created by backup_db.py)
├── tests/                  # (empty for now)
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Uvicorn, SQLAlchemy, SQLite
- **Frontend:** Jinja2 templates, vanilla JavaScript, plain CSS -- no frontend framework or build step
- **Scraping/parsing:** `requests`, `beautifulsoup4` (JSON-LD extraction), `ingredient_parser_nlp` (local ingredient-name cleanup)

---

## 📦 Setup

### 1. Clone the repository and create a virtual environment
```powershell
git clone https://github.com/<your-username>/manje-lakay.git
cd manje-lakay
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run the app
```powershell
uvicorn app.main:app --reload
```
Then open **http://127.0.0.1:8000/** -- that's the Planner page, your app's home screen.

### 4. (Optional) Access it from another device on your network
```powershell
uvicorn app.main:app --reload --host 0.0.0.0
```
Then find your PC's local IP (`ipconfig`) and visit `http://<your-ip>:8000/` from another device on the same network. Requires allowing the port through Windows Firewall (Inbound Rule, TCP, your port, Private profile) and your PC's network profile set to "Private."

### 5. Back up the database
```powershell
python scripts\backup_db.py
```
Creates a timestamped copy in `data/backups/`, keeping the 14 most recent. Automate it with Windows Task Scheduler for daily backups (set "Start in" to the project root, since the script uses relative paths).

### 6. Run with Docker (manual updates)

This repository includes a Docker Compose setup for running the app. The compose stack does not perform automatic image updates — updates are applied manually by the operator. The database remains in `./data`, and the container runs `alembic upgrade head` before starting the app.

Start the stack:

```bash
docker compose up -d
```

Manual update workflow (recommended):

```bash
# Backup the database first
cp -v ./data/manje_lakay.db ./data/manje_lakay.db.bak.$(date +%Y%m%d%H%M)

# Pull the latest image published to the registry, then recreate containers
docker compose pull
docker compose up -d
```

If you build and deploy from local source instead of pulling from the registry, build with:

```bash
docker build -t ghcr.io/phil-7/manje-lakay:latest .
docker compose up -d
```

Notes:
- Always back up `./data` before applying updates that include migrations. `alembic upgrade head` runs at container start.
- If you later decide to re-enable automatic updates, add a Watchtower (or similar) service and a label on the app service; this repo previously used Watchtower but it is not required.

---

## 🗺️ Pages

| Page | Route | Purpose |
|---|---|---|
| Planner | `/` | Editable meal calendar, planned recipes, and saved recipes available to add |
| Add Recipe | `/add` | Add a new recipe, by URL or manually |
| Grocery List | `/grocery` | Combined ingredient list and shopping checklist for everything on your plan |
| All Recipes | `/all-recipes` | Every saved recipe, with edit/delete |

The underlying JSON API lives at `/recipes`, `/calendar`, and `/grocery-list` (interactive docs at `/docs`).