# 🦭 Line Walrus

**"Because Even a Walrus Can Manage Lines Better"**

A professional hockey line management web application for coaches and team managers. Build, organize, and print hockey lines with drag-and-drop functionality and mobile-friendly touch controls.

**Live App**: [https://www.linewalrus.com](https://www.linewalrus.com)  
**Repository**: [crob21/skahl-line-builder](https://github.com/crob21/skahl-line-builder)

## ✨ Features

- **Drag & Drop Interface**: Intuitive player positioning (desktop)
- **Mobile Touch Controls**: Click-to-select player placement (mobile)
- **Real-time Updates**: No page refreshes needed
- **Team Management**: Upload/Download CSV files, save/load teams
- **Smart Print**: Professional line sheets with current date
- **Position Indicators**: Visual badges for positions
- **Goalie Styling**: Special gold styling for goalies
- **Red Spare Players**: Distinct red styling for affiliate/spare players
- **SportNinja Integration**: Compatible with SportNinja CSV exports
- **Shared Line URLs**: Save and share specific line combinations
- **Team CRUD Operations**: Create, read, update, and delete saved teams

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/crob21/skahl-line-builder.git
   cd skahl-line-builder
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app_simple.py
   ```

5. **Access the app**
   - Open your browser to `http://127.0.0.1:5001`
   - The app will automatically load with a default Seattle Kraken roster

## 📁 Project Structure

```
line-walrus/
├── app_simple.py         # Main Flask application (modular)
├── config.py             # Configuration settings
├── routes.py             # Flask routes and API endpoints
├── utils.py              # Utility functions
├── hockey_manager.py     # Team management logic
├── requirements.txt      # Python dependencies
├── Procfile              # Render deployment configuration
├── render.yaml           # Render service configuration
├── README.md             # This file
├── .gitignore           # Git ignore rules
│
├── data/                 # Data storage
│   ├── teams/           # Team JSON files
│   │   └── seattle_kraken.json
│   ├── sessions/        # User session data
│   ├── shared_lines/    # Shared line combinations
│   └── samples/         # Sample CSV files
│
├── templates/           # HTML templates
│   └── index.html       # Main application template
│
├── static/              # Static assets (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
│       ├── line-walrus-logo.png
│       └── favicon.png
│
└── docs/                # Documentation
    ├── DEPLOYMENT.md
    └── LOGO_GUIDE.md
```

## 🎯 Usage

### Loading Teams
1. **Default Teams**: Use "Load Saved Team" to access Seattle Kraken or Jackalopes
2. **Upload CSV**: Click "📁 Upload CSV" and select your file
3. **Manual Entry**: Add players one by one

#### CSV Upload Privacy Information
When you upload a CSV file, only the following columns are stored in our database:
- **First Name** - Player's first name
- **Last Name** - Player's last name  
- **Jersey Number** - Player's jersey number
- **Position** - Player's position (Forward, Defense, Goalie, etc.)
- **Affiliate** or **Affiliate Status** - Whether player is an affiliate (YES/NO)

**We do NOT store**: Email addresses, phone numbers, addresses, birth dates, or any other personal information. Only basic roster information needed for line management is retained.

### Building Lines
1. **Desktop**: Drag players from bench/spares to line positions
2. **Mobile**: Tap to select a player, then tap a position to place them
3. **Position Flexibility**: Players can be placed in any position regardless of roster position
4. **Real-time Updates**: Changes save automatically
5. **Print Lines**: Generate professional line sheets
6. **Share Lines**: Save and share specific line combinations via URL

### CSV Format
Upload CSV files with the following format:
```csv
last_name,first_name,jersey_number,position,affiliate
Beniers,Matty,10,FORWARD,NO
McCann,Jared,16,FORWARD,NO
Dunn,Vince,29,DEFENSE,NO
Grubauer,Philipp,31,GOALIE,NO
```

**Position Options**: `FORWARD`, `DEFENSE`, `GOALIE`
**Affiliate Options**: `YES` or `NO`

## 🛠 Development

### Local Development
```bash
# Activate virtual environment
source .venv/bin/activate

# Run in development mode
export FLASK_ENV=development
python app_simple.py
```

### Code Structure
- **app_simple.py**: Main Flask application entry point
- **routes.py**: API endpoints and web request handlers
- **hockey_manager.py**: Core team management logic
- **utils.py**: Utility functions for file handling and data parsing
- **config.py**: Application configuration settings
- **templates/index.html**: Single-page application with drag-and-drop and mobile touch
- **Data Storage**: JSON files for team persistence and session management

## 🚀 Deployment

### Render Deployment (Current)
The app is currently deployed on Render at [https://www.linewalrus.com](https://www.linewalrus.com)

1. **Automatic Deployment**: Pushes to `main` branch trigger automatic deployments
2. **Configuration**: Uses `render.yaml` and `Procfile` for deployment settings
3. **Environment**: Python 3.11 with Gunicorn WSGI server

### Other Platforms
- **Heroku**: Use the provided `Procfile`
- **Railway**: Automatic Python detection
- **DigitalOcean App Platform**: Deploy from Git repository
- **Vercel**: Python runtime support

## 📊 API Endpoints

### Team Management
- `GET /api/players` - Get all players
- `POST /api/players/add` - Add new player
- `DELETE /api/players/remove/<id>` - Remove player
- `POST /api/teams/upload` - Upload CSV team
- `GET /api/teams/download` - Download current team as CSV
- `POST /api/teams/save` - Save team with custom name
- `POST /api/teams/load` - Load saved team
- `GET /api/teams/list` - List all saved teams
- `POST /api/teams/update` - Update existing saved team
- `POST /api/teams/delete` - Delete saved team

### Line Management
- `POST /api/lines/set-player` - Place player in line position
- `DELETE /api/lines/remove-player/<id>` - Remove player from lines
- `DELETE /api/lines/clear/<line>` - Clear entire line
- `GET /api/lines` - Get current lines
- `GET /api/print-lines` - Generate printable line sheet

### Shared Lines
- `POST /api/shared-lines/save` - Save current lines as shareable URL
- `GET /api/shared-lines/<id>` - Get shared line combination
- `GET /api/shared-lines/<id>/print` - Print shared line combination

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏆 Acknowledgments

- **SportNinja**: CSV export compatibility
- **Seattle Kraken**: Default team roster
- **Flask Community**: Web framework
- **Hockey Community**: Feature inspiration
- **Render**: Hosting platform

---

**Built with ❤️ for hockey coaches and team managers**

*Line Walrus - Because Even a Walrus Can Manage Lines Better*
