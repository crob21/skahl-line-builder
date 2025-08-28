#!/usr/bin/env python3
"""
Mobile Touch Test Script for Line Walrus
Tests mobile touch functionality and provides debugging information.
"""

import requests
import json
import time

def test_mobile_touch():
    """Test mobile touch functionality"""
    base_url = "http://127.0.0.1:5001"
    session = requests.Session()  # Use session to maintain cookies
    
    print("🦭 Mobile Touch Test for Line Walrus")
    print("=" * 50)
    
    # Test 1: Check if app is running
    try:
        response = session.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ App is running")
        else:
            print(f"❌ App returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to app: {e}")
        return
    
    # Test 2: Load a team
    try:
        response = session.post(f"{base_url}/api/teams/load", 
                               json={"team_name": "Jackalopes"})
        if response.status_code == 200:
            print("✅ Team loaded successfully")
        else:
            print(f"❌ Team load failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Team load error: {e}")
        return
    
    # Test 3: Get players
    try:
        response = session.get(f"{base_url}/api/players")
        if response.status_code == 200:
            players = response.json()
            print(f"✅ Found {len(players)} players")
        else:
            print(f"❌ Player fetch failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Player fetch error: {e}")
        return
    
    # Test 4: Check mobile CSS
    try:
        response = session.get(f"{base_url}/")
        html = response.text
        
        mobile_features = {
            "touch-action": "touch-action: manipulation" in html,
            "viewport": "viewport" in html,
            "player-card": "player-card" in html,
            "position-slot": "position-slot" in html,
            "mobile detection": "isMobile" in html,
            "touchstart": "touchstart" in html,
            "touchend": "touchend" in html
        }
        
        print("\n📱 Mobile Features Check:")
        for feature, present in mobile_features.items():
            status = "✅" if present else "❌"
            print(f"  {status} {feature}")
            
    except Exception as e:
        print(f"❌ Mobile features check error: {e}")
    
    # Test 5: Test player placement API
    if players:
        try:
            player_id = players[0].get('id')
            response = session.post(f"{base_url}/api/lines/set-player", 
                                   json={
                                       "player_id": player_id,
                                       "line": "1",
                                       "position": "LW"
                                   })
            if response.status_code == 200:
                print("✅ Player placement API working")
            else:
                print(f"❌ Player placement failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Player placement error: {e}")
    
    print("\n📋 Manual Testing Instructions:")
    print("1. Open http://127.0.0.1:5001 on your mobile device")
    print("2. Open browser developer tools (if possible)")
    print("3. Check console for mobile detection logs")
    print("4. Try tapping on player cards")
    print("5. Try tapping on position slots")
    print("6. Look for console logs showing touch events")
    
    print("\n🔍 Debugging Tips:")
    print("- Check if 'Mobile detection:' appears in console")
    print("- Look for 'Touch start:' and 'Touch end:' logs")
    print("- Verify player cards have 'player-card' class")
    print("- Verify position slots have 'position-slot' class")
    print("- Check if touch events are being prevented")

if __name__ == "__main__":
    test_mobile_touch()
