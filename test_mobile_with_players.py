#!/usr/bin/env python3
"""
🦭 Mobile Test with Players - Line Walrus
========================================

Test mobile functionality with actual players loaded.
"""

import requests
import json
import time

def test_mobile_with_players():
    base_url = "http://127.0.0.1:5001"
    session = requests.Session()
    
    print("🦭 Mobile Test with Players - Line Walrus")
    print("=" * 50)
    
    # Test connection
    try:
        response = session.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ App is running and accessible")
        else:
            print(f"❌ App returned status {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to app. Is it running?")
        return
    
    # Load Kraken team
    print("\n🏒 Loading Seattle Kraken team...")
    try:
        response = session.post(
            f"{base_url}/api/teams/load",
            json={"team_name": "Seattle Kraken"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Team loaded: {data.get('message', 'Success')}")
        else:
            print(f"❌ Failed to load team: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error loading team: {e}")
        return
    
    # Get players
    print("\n👥 Getting players...")
    try:
        response = session.get(f"{base_url}/api/players")
        if response.status_code == 200:
            players = response.json()
            print(f"✅ Retrieved {len(players)} players")
            
            if players:
                print("\n📋 First 5 players:")
                for i, player in enumerate(players[:5]):
                    print(f"  {player['id']}: {player['name']} ({player.get('roster_position', 'N/A')})")
            else:
                print("❌ No players found")
                return
        else:
            print(f"❌ Failed to get players: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting players: {e}")
        return
    
    # Test player placement
    print("\n🎯 Testing player placement...")
    if players:
        first_player = players[0]
        print(f"Testing with: {first_player['name']} (ID: {first_player['id']})")
        
        try:
            response = session.post(
                f"{base_url}/api/lines/set-player",
                json={
                    "player_id": first_player['id'],
                    "line": "1",
                    "position": "LW"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ Player placed successfully: {data.get('message', 'Success')}")
                else:
                    print(f"❌ Placement failed: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ Placement failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ Error placing player: {e}")
    
    # Get current lines
    print("\n🏒 Getting current lines...")
    try:
        response = session.get(f"{base_url}/api/lines")
        if response.status_code == 200:
            lines = response.json()
            print("✅ Current lines retrieved")
            
            # Show line 1
            if "1" in lines:
                line1 = lines["1"]
                print("\n📋 Line 1:")
                for pos in ["LW", "C", "RW", "LD", "RD", "G"]:
                    if pos in line1 and line1[pos]:
                        print(f"  {pos}: {line1[pos]['name']}")
                    else:
                        print(f"  {pos}: Empty")
        else:
            print(f"❌ Failed to get lines: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting lines: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Mobile test with players completed!")
    print("\n📱 Now you can test on your iPhone:")
    print("1. Open http://127.0.0.1:5001 on your iPhone")
    print("2. The Kraken team should be loaded")
    print("3. Try tapping player cards to select them")
    print("4. Try tapping position slots to place players")
    print("5. Check browser console for touch event logs")
    print("\n🔍 Debug URLs:")
    print("• Mobile Fix Test: http://127.0.0.1:8080/mobile_fix.html")
    print("• Touch Debugger: http://127.0.0.1:8080/mobile_touch_debugger.html")

if __name__ == "__main__":
    test_mobile_with_players()
