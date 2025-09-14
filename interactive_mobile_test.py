#!/usr/bin/env python3
"""
🦭 Interactive Mobile Test for Line Walrus
==========================================

This script helps test mobile functionality interactively without pushing to repo.
It simulates mobile touch events and provides real-time debugging.
"""

import requests
import json
import time
import sys
from datetime import datetime

class MobileTester:
    def __init__(self, base_url="http://127.0.0.1:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "DEBUG": "🔍"}
        print(f"[{timestamp}] {emoji.get(level, '📝')} {message}")
    
    def test_connection(self):
        """Test if the app is running"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log("App is running and accessible", "SUCCESS")
                return True
            else:
                self.log(f"App returned status {response.status_code}", "ERROR")
                return False
        except requests.exceptions.ConnectionError:
            self.log("Cannot connect to app. Is it running?", "ERROR")
            return False
    
    def load_team(self, team_name="Jackalopes"):
        """Load a team and get session ID"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/teams/load",
                json={"team_name": team_name}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Team '{team_name}' loaded successfully", "SUCCESS")
                
                # Extract session ID from cookies
                if 'session' in self.session.cookies:
                    self.session_id = self.session.cookies['session']
                    self.log(f"Session ID: {self.session_id[:8]}...", "DEBUG")
                
                return True
            else:
                self.log(f"Failed to load team: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error loading team: {e}", "ERROR")
            return False
    
    def get_players(self):
        """Get list of players"""
        try:
            response = self.session.get(f"{self.base_url}/api/players")
            if response.status_code == 200:
                players = response.json()
                self.log(f"Retrieved {len(players)} players", "SUCCESS")
                return players
            else:
                self.log(f"Failed to get players: {response.status_code}", "ERROR")
                return []
        except Exception as e:
            self.log(f"Error getting players: {e}", "ERROR")
            return []
    
    def get_lines(self):
        """Get current lines"""
        try:
            response = self.session.get(f"{self.base_url}/api/lines")
            if response.status_code == 200:
                lines = response.json()
                self.log("Retrieved current lines", "SUCCESS")
                return lines
            else:
                self.log(f"Failed to get lines: {response.status_code}", "ERROR")
                return {}
        except Exception as e:
            self.log(f"Error getting lines: {e}", "ERROR")
            return {}
    
    def place_player(self, player_id, line, position):
        """Place a player in a specific position"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/lines/set-player",
                json={
                    "player_id": player_id,
                    "line": str(line),
                    "position": position
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log(f"Player {player_id} placed in Line {line} {position}", "SUCCESS")
                    return True
                else:
                    self.log(f"Placement failed: {data.get('message', 'Unknown error')}", "ERROR")
                    return False
            else:
                self.log(f"Placement failed with status {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error placing player: {e}", "ERROR")
            return False
    
    def clear_lines(self):
        """Clear all lines"""
        try:
            response = self.session.post(f"{self.base_url}/api/lines/clear")
            if response.status_code == 200:
                self.log("All lines cleared", "SUCCESS")
                return True
            else:
                self.log(f"Failed to clear lines: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error clearing lines: {e}", "ERROR")
            return False
    
    def test_mobile_simulation(self):
        """Simulate mobile touch interactions"""
        self.log("Starting mobile touch simulation...", "INFO")
        
        # Get players
        players = self.get_players()
        if not players:
            self.log("No players available for testing", "ERROR")
            return False
        
        # Test placing first few players
        test_placements = [
            (players[0]["id"], 1, "LW"),
            (players[1]["id"], 1, "C"),
            (players[2]["id"], 1, "RW"),
            (players[3]["id"], 2, "LW"),
            (players[4]["id"], 2, "C")
        ]
        
        success_count = 0
        for player_id, line, position in test_placements:
            player_name = next((p["name"] for p in players if p["id"] == player_id), "Unknown")
            self.log(f"Testing: {player_name} -> Line {line} {position}", "DEBUG")
            
            if self.place_player(player_id, line, position):
                success_count += 1
                time.sleep(0.5)  # Small delay between placements
            else:
                self.log(f"Failed to place {player_name}", "WARNING")
        
        self.log(f"Mobile simulation complete: {success_count}/{len(test_placements)} successful", 
                "SUCCESS" if success_count == len(test_placements) else "WARNING")
        
        return success_count == len(test_placements)
    
    def interactive_menu(self):
        """Interactive testing menu"""
        while True:
            print("\n" + "="*60)
            print("🦭 INTERACTIVE MOBILE TESTER - Line Walrus")
            print("="*60)
            print("1. Test Connection")
            print("2. Load Team")
            print("3. Show Players")
            print("4. Show Lines")
            print("5. Place Player (Interactive)")
            print("6. Run Mobile Simulation")
            print("7. Clear All Lines")
            print("8. Test Session Persistence")
            print("9. Exit")
            print("="*60)
            
            choice = input("\nChoose an option (1-9): ").strip()
            
            if choice == "1":
                self.test_connection()
            
            elif choice == "2":
                team_name = input("Team name (default: Jackalopes): ").strip() or "Jackalopes"
                self.load_team(team_name)
            
            elif choice == "3":
                players = self.get_players()
                if players:
                    print(f"\n📋 Players ({len(players)}):")
                    for i, player in enumerate(players[:10]):  # Show first 10
                        print(f"  {player['id']}: {player['name']} ({player['position']})")
                    if len(players) > 10:
                        print(f"  ... and {len(players) - 10} more")
            
            elif choice == "4":
                lines = self.get_lines()
                if lines:
                    print(f"\n🏒 Current Lines:")
                    for line_num in ["1", "2", "3"]:
                        if line_num in lines:
                            line = lines[line_num]
                            print(f"  Line {line_num}:")
                            for pos in ["LW", "C", "RW", "LD", "RD", "G"]:
                                if pos in line and line[pos]:
                                    print(f"    {pos}: {line[pos]['name']}")
                                else:
                                    print(f"    {pos}: Empty")
            
            elif choice == "5":
                players = self.get_players()
                if not players:
                    self.log("No players available. Load a team first.", "WARNING")
                    continue
                
                print(f"\nAvailable players:")
                for i, player in enumerate(players[:10]):
                    print(f"  {player['id']}: {player['name']} ({player['position']})")
                
                try:
                    player_id = int(input("\nPlayer ID: "))
                    line = int(input("Line (1-3): "))
                    position = input("Position (LW/C/RW/LD/RD/G): ").strip().upper()
                    
                    self.place_player(player_id, line, position)
                except ValueError:
                    self.log("Invalid input", "ERROR")
            
            elif choice == "6":
                self.test_mobile_simulation()
            
            elif choice == "7":
                self.clear_lines()
            
            elif choice == "8":
                self.log("Testing session persistence...", "INFO")
                # Make a request, then another to see if session persists
                players1 = self.get_players()
                time.sleep(1)
                players2 = self.get_players()
                
                if len(players1) == len(players2) and len(players1) > 0:
                    self.log("Session persistence working", "SUCCESS")
                else:
                    self.log("Session persistence issue detected", "WARNING")
            
            elif choice == "9":
                self.log("Goodbye! 🦭", "INFO")
                break
            
            else:
                self.log("Invalid choice", "WARNING")

def main():
    print("🦭 Interactive Mobile Test for Line Walrus")
    print("=" * 50)
    
    tester = MobileTester()
    
    # Quick initial test
    if tester.test_connection():
        tester.log("Starting interactive testing...", "INFO")
        tester.interactive_menu()
    else:
        tester.log("Please start the app first: python3 app_simple.py", "ERROR")

if __name__ == "__main__":
    main()
