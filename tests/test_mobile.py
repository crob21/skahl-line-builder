#!/usr/bin/env python3
"""
Mobile Testing Script for Line Walrus
Tests mobile-specific functionality and provides debugging information.
"""

import requests
import json
import time

def test_mobile_functionality():
    """Test mobile-specific functionality"""
    base_url = "http://127.0.0.1:5001"
    
    print("🦭 Mobile Testing for Line Walrus")
    print("=" * 50)
    
    # Test 1: Basic API connectivity
    print("\n1. Testing API connectivity...")
    try:
        response = requests.get(f"{base_url}/api/teams/list")
        if response.status_code == 200:
            teams = response.json()
            print(f"✅ API working - Found {len(teams)} teams")
            for team in teams:
                print(f"   - {team['name']} ({team['player_count']} players)")
        else:
            print(f"❌ API error - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return
    
    # Test 2: Load a team
    print("\n2. Testing team loading...")
    try:
        if teams:
            team_name = teams[0]['name']
            response = requests.post(f"{base_url}/api/teams/load", 
                                   json={"team_name": team_name})
            if response.status_code == 200:
                print(f"✅ Team loaded: {team_name}")
            else:
                print(f"❌ Team load failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Team loading failed: {e}")
    
    # Test 3: Get players
    print("\n3. Testing player data...")
    try:
        response = requests.get(f"{base_url}/api/players")
        if response.status_code == 200:
            players = response.json()
            print(f"✅ Players loaded: {len(players)} players")
            
            # Check for different player types
            bench_players = [p for p in players if p.get('location') == 'bench']
            spare_players = [p for p in players if p.get('location') == 'spares']
            line_players = [p for p in players if p.get('location') == 'line']
            
            print(f"   - Bench: {len(bench_players)} players")
            print(f"   - Spares: {len(spare_players)} players")
            print(f"   - On Lines: {len(line_players)} players")
            
            # Show sample players
            if bench_players:
                print(f"   - Sample bench player: {bench_players[0]['name']}")
        else:
            print(f"❌ Player data failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Player data failed: {e}")
    
    # Test 4: Get lines
    print("\n4. Testing line data...")
    try:
        response = requests.get(f"{base_url}/api/lines")
        if response.status_code == 200:
            lines = response.json()
            print(f"✅ Lines loaded: {len(lines)} lines")
            
            for line_num, line in lines.items():
                filled_positions = sum(1 for pos, player in line.items() if player)
                print(f"   - Line {line_num}: {filled_positions} positions filled")
        else:
            print(f"❌ Line data failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Line data failed: {e}")
    
    # Test 5: Test player placement
    print("\n5. Testing player placement...")
    try:
        if bench_players:
            player = bench_players[0]
            response = requests.post(f"{base_url}/api/lines/set-player", 
                                   json={
                                       "player_id": player['id'],
                                       "line": "1",
                                       "position": "LW"
                                   })
            if response.status_code == 200:
                print(f"✅ Player placed: {player['name']} → Line 1 LW")
            else:
                print(f"❌ Player placement failed: {response.status_code}")
        else:
            print("⚠️  No bench players available for testing")
    except Exception as e:
        print(f"❌ Player placement failed: {e}")
    
    # Test 6: Check mobile-specific endpoints
    print("\n6. Testing mobile-specific features...")
    try:
        # Test main page loads
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            
            # Check for mobile-specific CSS
            if "touch-action: manipulation" in response.text:
                print("✅ Mobile touch CSS found")
            else:
                print("⚠️  Mobile touch CSS not found")
                
            if "viewport" in response.text:
                print("✅ Viewport meta tag found")
            else:
                print("⚠️  Viewport meta tag not found")
        else:
            print(f"❌ Main page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Main page test failed: {e}")
    
    print("\n" + "=" * 50)
    print("📱 Mobile Testing Complete!")
    print("\nNext Steps:")
    print("1. Open http://127.0.0.1:5001 on your mobile device")
    print("2. Open browser developer tools (if possible)")
    print("3. Check console for touch event logs")
    print("4. Test tap functionality on players and positions")
    print("5. Report any specific issues found")

if __name__ == "__main__":
    test_mobile_functionality()
