import json
import os
from datetime import datetime

class HockeyTeamManager:
    def __init__(self, data_file="hockey_team.json"):
        self.data_file = data_file
        self.players = []
        self.lines = {
            1: {"LW": None, "C": None, "RW": None, "LD": None, "RD": None, "G": None},
            2: {"LW": None, "C": None, "RW": None, "LD": None, "RD": None, "G": None},
            3: {"LW": None, "C": None, "RW": None, "LD": None, "RD": None, "G": None}
        }
        self.load_data()
    
    def save_data(self):
        """Save players and lines to JSON file"""
        data = {
            "players": self.players,
            "lines": self.lines,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Data saved to {self.data_file}")
    
    def load_data(self):
        """Load players and lines from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.players = data.get("players", [])
                    self.lines = data.get("lines", self.lines)
                print(f"✅ Data loaded from {self.data_file}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  Error loading data: {e}")
                print("Starting with empty roster")
        else:
            print("📝 No saved data found, starting fresh")
    
    def add_player(self, name, position):
        """Add a new player to the roster"""
        # Check if player already exists
        if any(p["name"].lower() == name.lower() for p in self.players):
            print(f"❌ {name} is already on the roster!")
            return False
        
        # Validate position
        valid_positions = ["C", "LW", "RW", "LD", "RD", "G"]
        if position.upper() not in valid_positions:
            print(f"❌ Invalid position. Use: {', '.join(valid_positions)}")
            return False
        
        player = {
            "name": name.strip(),
            "position": position.upper(),
            "id": len(self.players) + 1
        }
        
        self.players.append(player)
        self.save_data()
        print(f"✅ Added {name} ({position.upper()}) to the roster!")
        return True
    
    def remove_player(self, name):
        """Remove a player from roster and all lines"""
        player_found = False
        
        # Remove from roster
        for i, player in enumerate(self.players):
            if player["name"].lower() == name.lower():
                self.players.pop(i)
                player_found = True
                break
        
        if not player_found:
            print(f"❌ {name} not found on roster")
            return False
        
        # Remove from all lines
        for line_num in self.lines:
            for position in self.lines[line_num]:
                if (self.lines[line_num][position] and 
                    self.lines[line_num][position].lower() == name.lower()):
                    self.lines[line_num][position] = None
        
        self.save_data()
        print(f"✅ Removed {name} from roster and all lines!")
        return True
    
    def show_roster(self):
        """Display the current roster organized by position"""
        if not self.players:
            print("📝 No players on the roster yet!")
            return
        
        print("\n🏒 TEAM ROSTER 🏒")
        print("=" * 30)
        
        # Group by position
        positions = ["G", "LD", "RD", "C", "LW", "RW"]
        for pos in positions:
            pos_players = [p["name"] for p in self.players if p["position"] == pos]
            if pos_players:
                print(f"{pos:2}: {', '.join(pos_players)}")
        
        print(f"\nTotal Players: {len(self.players)}")
        print()
    
    def set_line(self, line_num, position, player_name):
        """Set a player in a specific line position"""
        if line_num not in [1, 2, 3]:
            print("❌ Line number must be 1, 2, or 3")
            return False
        
        if position not in ["LW", "C", "RW", "LD", "RD", "G"]:
            print("❌ Invalid position. Use: LW, C, RW, LD, RD, G")
            return False
        
        # Check if player exists
        player = next((p for p in self.players if p["name"].lower() == player_name.lower()), None)
        if not player:
            print(f"❌ {player_name} not found on roster")
            return False
        
        # Remove player from any other position first
        for ln in self.lines:
            for pos in self.lines[ln]:
                if (self.lines[ln][pos] and 
                    self.lines[ln][pos].lower() == player_name.lower()):
                    self.lines[ln][pos] = None
        
        # Set player in new position
        self.lines[line_num][position] = player["name"]
        self.save_data()
        print(f"✅ Set {player['name']} as {position} on Line {line_num}")
        return True
    
    def show_lines(self):
        """Display all current lines"""
        print("\n🏒 CURRENT LINES 🏒")
        print("=" * 40)
        
        for line_num in [1, 2, 3]:
            line = self.lines[line_num]
            print(f"\nLine {line_num}:")
            print(f"  {line['LW'] or '___':10} - {line['C'] or '___':10} - {line['RW'] or '___'}")
            print(f"  {line['LD'] or '___':10} - {line['RD'] or '___'}")
            print(f"  G: {line['G'] or '___'}")
        
        # Show bench players
        self.show_bench()
        print()
    
    def show_bench(self):
        """Show players not currently in any line"""
        assigned_players = set()
        for line in self.lines.values():
            for player in line.values():
                if player:
                    assigned_players.add(player.lower())
        
        bench_players = [p["name"] for p in self.players 
                        if p["name"].lower() not in assigned_players]
        
        if bench_players:
            print(f"\nBench: {', '.join(bench_players)}")
        else:
            print("\nBench: Empty")
    
    def clear_line(self, line_num):
        """Clear all positions in a specific line"""
        if line_num not in [1, 2, 3]:
            print("❌ Line number must be 1, 2, or 3")
            return False
        
        self.lines[line_num] = {"LW": None, "C": None, "RW": None, 
                               "LD": None, "RD": None, "G": None}
        self.save_data()
        print(f"✅ Cleared Line {line_num}")
        return True
    
    def clear_all_lines(self):
        """Clear all lines"""
        for line_num in [1, 2, 3]:
            self.lines[line_num] = {"LW": None, "C": None, "RW": None, 
                                   "LD": None, "RD": None, "G": None}
        self.save_data()
        print("✅ Cleared all lines!")

def main():
    """Main interactive menu"""
    manager = HockeyTeamManager()
    
    while True:
        print("\n" + "="*50)
        print("🏒 HOCKEY TEAM MANAGER 🏒")
        print("="*50)
        print("1. Show Roster")
        print("2. Add Player")
        print("3. Remove Player")
        print("4. Show Lines")
        print("5. Set Player in Line")
        print("6. Clear Line")
        print("7. Clear All Lines")
        print("8. Quick Setup (add sample players)")
        print("9. Exit")
        print("="*50)
        
        choice = input("\nChoose an option (1-9): ").strip()
        
        if choice == "1":
            manager.show_roster()
        
        elif choice == "2":
            name = input("Player name: ").strip()
            if not name:
                print("❌ Name cannot be empty")
                continue
            
            print("Positions: C, LW, RW, LD, RD, G")
            position = input("Position: ").strip().upper()
            manager.add_player(name, position)
        
        elif choice == "3":
            if not manager.players:
                print("📝 No players to remove")
                continue
            
            manager.show_roster()
            name = input("\nPlayer name to remove: ").strip()
            if name:
                manager.remove_player(name)
        
        elif choice == "4":
            manager.show_lines()
        
        elif choice == "5":
            if not manager.players:
                print("📝 Add some players first!")
                continue
            
            manager.show_roster()
            print("\nPositions: LW, C, RW, LD, RD, G")
            
            try:
                line_num = int(input("Line number (1, 2, 3): "))
                position = input("Position: ").strip().upper()
                player_name = input("Player name: ").strip()
                
                if line_num and position and player_name:
                    manager.set_line(line_num, position, player_name)
            except ValueError:
                print("❌ Please enter a valid line number")
        
        elif choice == "6":
            try:
                line_num = int(input("Line number to clear (1, 2, 3): "))
                manager.clear_line(line_num)
            except ValueError:
                print("❌ Please enter a valid line number")
        
        elif choice == "7":
            confirm = input("Clear all lines? (yes/no): ").lower()
            if confirm in ["yes", "y"]:
                manager.clear_all_lines()
        
        elif choice == "8":
            # Quick setup with sample players
            sample_players = [
                ("Connor McDavid", "C"),
                ("Alex Ovechkin", "LW"), 
                ("David Pastrnak", "RW"),
                ("Erik Karlsson", "LD"),
                ("Cale Makar", "RD"),
                ("Igor Shesterkin", "G"),
                ("Sidney Crosby", "C"),
                ("Brad Marchand", "LW"),
                ("Mitch Marner", "RW"),
                ("Victor Hedman", "LD"),
                ("Aaron Ekblad", "RD"),
                ("Frederik Andersen", "G")
            ]
            
            print("Adding sample players...")
            for name, pos in sample_players:
                manager.add_player(name, pos)
            
            print("✅ Sample players added!")
        
        elif choice == "9":
            print("Thanks for using Hockey Team Manager! 🏒")
            break
        
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    main()