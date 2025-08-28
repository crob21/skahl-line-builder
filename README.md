# 🏒 SKAHL Line Builder

A professional hockey line builder web application for coaches and teams.

## Features

- **Drag & Drop Line Building**: Intuitive interface for building hockey lines
- **Team Management**: Upload/Download CSV files, save/load teams
- **Smart Printing**: Print only populated lines and positions
- **Multiple Teams**: Switch between different team configurations
- **Responsive Design**: Works on desktop and mobile devices

## Local Development

### Prerequisites
- Python 3.7+
- pip

### Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python3 app.py
   ```
4. Open http://localhost:5001 in your browser

## Deployment

### Render (Recommended - Free)
1. Fork this repository to your GitHub account
2. Go to [render.com](https://render.com) and create an account
3. Click "New Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: `skahl-line-builder` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 app.py`
6. Click "Create Web Service"
7. Your app will be available at `https://your-app-name.onrender.com`

### Railway
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Deploy automatically

### Heroku
1. Install Heroku CLI
2. Create a new Heroku app
3. Deploy using Git:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

## Usage

### Adding Players
1. Enter player name and select position
2. Click "Add Player" or "Add Sample Players"

### Building Lines
1. Drag players from the bench to position slots
2. Players can only be placed in their designated positions
3. Use "Clear Line" to reset individual lines

### Team Management
- **Upload CSV**: Import team from CSV file (name,position format)
- **Download CSV**: Export current team to CSV
- **Save Team**: Save current configuration with a name
- **Load Team**: Switch between saved teams

### Printing Lines
- Click "🖨️ Print Lines" to generate a clean, print-friendly version
- Only populated lines and positions are shown
- Perfect for game day use

## File Structure

```
├── app.py              # Main Flask application
├── hockey_team.json    # Team data storage
├── sample_team.csv     # Example CSV format
├── requirements.txt    # Python dependencies
├── Procfile           # Production configuration
└── README.md          # This file
```

## CSV Format

Upload CSV files with the following format:
```csv
name,position
Connor McDavid,C
Alex Ovechkin,LW
David Pastrnak,RW
```

Valid positions: C, LW, RW, LD, RD, G

## License

This project is open source and available under the MIT License.