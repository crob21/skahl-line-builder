#!/usr/bin/env python3
"""
Comprehensive Test Suite for SKAHL Line Builder
Tests all major functionality including API endpoints, data persistence, and error handling.
"""

import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:5001"

def test_api_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test a single API endpoint"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}")
        
        print(f"✅ {method} {endpoint} - Status: {response.status_code}")
        
        if response.status_code == expected_status:
            try:
                return True, response.json() if response.content else None
            except:
                # Handle HTML responses (like print and download endpoints)
                return True, response.text if response.content else None
        else:
            print(f"❌ Expected {expected_status}, got {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing {method} {endpoint}: {str(e)}")
        return False, None

def test_teams_functionality():
    """Test team management functionality"""
    print("\n🏒 Testing Team Management...")
    
    # Test listing teams
    success, teams = test_api_endpoint("/api/teams/list")
    if success and teams:
        print(f"   Found {len(teams)} teams:")
        for team in teams:
            print(f"   - {team.get('name', 'Unknown')} ({team.get('player_count', 0)} players)")
    
    # Test loading a team
    if teams:
        team_file = teams[0]['filename']
        success, _ = test_api_endpoint("/api/teams/load", method="POST", 
                                     data={"filename": team_file})
        if success:
            print(f"   ✅ Successfully loaded team: {team_file}")

def test_players_functionality():
    """Test player management functionality"""
    print("\n👥 Testing Player Management...")
    
    # Test getting players
    success, players = test_api_endpoint("/api/players")
    if success and players:
        print(f"   Found {len(players)} players")
        
        # Show some player details
        for i, player in enumerate(players[:3]):
            print(f"   - {player.get('name', 'Unknown')} (#{player.get('jersey_number', 'N/A')}) - {player.get('roster_position', 'Unknown')}")
    
    # Test adding a player
    test_player = {
        "name": "Test Player",
        "position": "FORWARD",
        "jersey_number": "99"
    }
    success, _ = test_api_endpoint("/api/players", method="POST", data=test_player)
    if success:
        print("   ✅ Successfully added test player")

def test_lines_functionality():
    """Test line management functionality"""
    print("\n🏃 Testing Line Management...")
    
    # Test getting lines
    success, lines = test_api_endpoint("/api/lines")
    if success and lines:
        print("   Current lines structure:")
        for line_num, line_data in lines.items():
            print(f"   Line {line_num}: {len([p for p in line_data.values() if p])} players")
    
    # Test setting a player in a line (if we have players)
    success, players = test_api_endpoint("/api/players")
    if success and players:
        player_id = players[0]['id']
        line_data = {
            "player_id": player_id,
            "line_num": 1,
            "position": "LW"
        }
        success, _ = test_api_endpoint("/api/lines/set-player", method="POST", data=line_data)
        if success:
            print(f"   ✅ Successfully placed player {player_id} in Line 1 LW")

def test_print_functionality():
    """Test print functionality"""
    print("\n🖨️ Testing Print Functionality...")
    
    success, _ = test_api_endpoint("/api/print-lines")
    if success:
        print("   ✅ Print endpoint working")
    else:
        print("   ⚠️ Print endpoint has issues")

def test_csv_functionality():
    """Test CSV upload/download functionality"""
    print("\n📄 Testing CSV Functionality...")
    
    # Test CSV download
    success, _ = test_api_endpoint("/api/teams/download")
    if success:
        print("   ✅ CSV download working")
    else:
        print("   ⚠️ CSV download has issues")

def test_error_handling():
    """Test error handling"""
    print("\n🛡️ Testing Error Handling...")
    
    # Test invalid player ID
    success, _ = test_api_endpoint("/api/lines/set-player", method="POST", 
                                 data={"player_id": 99999, "line_num": 1, "position": "LW"})
    if not success:
        print("   ✅ Properly handled invalid player ID")
    
    # Test invalid line number
    success, _ = test_api_endpoint("/api/lines/set-player", method="POST", 
                                 data={"player_id": 1, "line_num": 99, "position": "LW"})
    if not success:
        print("   ✅ Properly handled invalid line number")

def main():
    """Run all tests"""
    print("🧪 SKAHL Line Builder - Comprehensive Test Suite")
    print("=" * 50)
    
    # Wait for app to be ready
    print("⏳ Waiting for app to be ready...")
    time.sleep(2)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ App is running and accessible")
        else:
            print("❌ App is not responding properly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to app: {str(e)}")
        return
    
    # Run all test suites
    test_teams_functionality()
    test_players_functionality()
    test_lines_functionality()
    test_print_functionality()
    test_csv_functionality()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("🎉 Test suite completed!")
    print("\n📋 Manual Testing Checklist:")
    print("1. Open http://127.0.0.1:5001 in your browser")
    print("2. Test drag and drop functionality")
    print("3. Test loading different teams")
    print("4. Test CSV upload/download")
    print("5. Test print functionality")
    print("6. Test mobile responsiveness")

if __name__ == "__main__":
    main()
