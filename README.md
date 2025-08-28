# 🏒 SKAHL Line Builder

A professional hockey line management web application for coaches and team managers. Build, organize, and print hockey lines with drag-and-drop functionality.

## ✨ Features

- **Drag & Drop Interface**: Intuitive player positioning
- **Real-time Updates**: No page refreshes needed
- **Team Management**: Upload/Download CSV files, save/load teams
- **Smart Print**: Professional line sheets with current date
- **Position Indicators**: Visual badges for positions
- **Goalie Styling**: Special gold styling for goalies
- **Affiliate Players**: Separate "Spares" section
- **SportNinja Integration**: Compatible with SportNinja CSV exports

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
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
   python app.py
   ```

5. **Access the app**
   - Open your browser to `http://127.0.0.1:5001`
   - The app will automatically load with a default Seattle Kraken roster

## 📁 Project Structure

```
skahl-line-builder/
├── app.py                 # Main Flask application
├── hockey_manager.py      # Team management logic
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku deployment configuration
├── README.md             # This file
├── DEPLOYMENT.md         # Deployment instructions
├── .gitignore           # Git ignore rules
│
├── data/                 # Data storage
│   ├── teams/           # Team JSON files
│   │   ├── seattle_kraken.json
│   │   └── jackalopes.json
│   └── samples/         # Sample CSV files
│       ├── kraken_roster.csv
│       └── sample_team.csv
│
└── static/              # Static assets (CSS, JS, images)
    ├── css/
    ├── js/
    └── images/
```

## 🎯 Usage

### Loading Teams
1. **Default Teams**: Use "Load Saved Team" to access Seattle Kraken or Jackalopes
2. **CSV Upload**: Upload your own team CSV file
3. **Manual Entry**: Add players one by one

### Building Lines
1. **Drag Players**: Drag from bench/spares to line positions
2. **Position Flexibility**: Players can be placed in any position regardless of roster position
3. **Real-time Updates**: Changes save automatically
4. **Print Lines**: Generate professional line sheets

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
python app.py
```

### Code Structure
- **Flask Routes**: Handle API endpoints and web requests
- **HockeyTeamManager**: Core team management logic
- **Frontend**: HTML/CSS/JavaScript with drag-and-drop functionality
- **Data Storage**: JSON files for team persistence

## 🚀 Deployment

### Heroku Deployment
1. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

2. **Deploy**
   ```bash
   git add .
   git commit -m "Production ready"
   git push heroku main
   ```

3. **Open app**
   ```bash
   heroku open
   ```

### Other Platforms
- **Render**: Use the provided `Procfile`
- **Railway**: Automatic Python detection
- **DigitalOcean App Platform**: Deploy from Git repository

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

### Line Management
- `POST /api/lines/set-player` - Place player in line position
- `DELETE /api/lines/remove-player/<id>` - Remove player from lines
- `DELETE /api/lines/clear/<line>` - Clear entire line
- `GET /api/lines` - Get current lines
- `GET /api/print-lines` - Generate printable line sheet

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

---

**Built with ❤️ for hockey coaches and team managers**