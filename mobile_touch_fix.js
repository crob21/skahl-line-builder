// 🦭 Mobile Touch Fix for Line Walrus
// ===================================
// Simplified touch handling to fix mobile interactions

console.log('🦭 Loading Mobile Touch Fix...');

// Remove all existing touch event listeners and replace with simplified version
function fixMobileTouch() {
    console.log('🔧 Applying mobile touch fix...');
    
    // Clear any existing event listeners by cloning elements
    const playerCards = document.querySelectorAll('.player-card');
    const positionSlots = document.querySelectorAll('.position-slot');
    
    // Variables for player selection
    let selectedPlayer = null;
    let selectedPlayerElement = null;
    
    // Function to select a player
    function selectPlayer(playerId, playerName, element) {
        // Clear previous selection
        if (selectedPlayerElement) {
            selectedPlayerElement.classList.remove('selected');
        }
        
        // Select new player
        selectedPlayer = { id: playerId, name: playerName };
        selectedPlayerElement = element;
        element.classList.add('selected');
        
        console.log(`✅ Selected player: ${playerName} (ID: ${playerId})`);
    }
    
    // Function to place player in position
    function placePlayerInPosition(line, position, element) {
        if (!selectedPlayer) {
            console.log('⚠️ No player selected. Tap a player first.');
            return;
        }
        
        console.log(`✅ Placing ${selectedPlayer.name} in Line ${line} ${position}`);
        
        // Make API call to place player
        fetch('/api/lines/set-player', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                player_id: selectedPlayer.id,
                line: line,
                position: position
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`✅ Player placed successfully: ${data.message}`);
                // Update the UI
                element.classList.add('occupied');
                element.textContent = selectedPlayer.name;
                
                // Clear selection
                clearSelection();
            } else {
                console.log(`❌ Failed to place player: ${data.message}`);
            }
        })
        .catch(error => {
            console.log(`❌ Error placing player: ${error}`);
        });
    }
    
    // Function to clear selection
    function clearSelection() {
        if (selectedPlayerElement) {
            selectedPlayerElement.classList.remove('selected');
        }
        
        selectedPlayer = null;
        selectedPlayerElement = null;
        
        console.log('ℹ️ Selection cleared');
    }
    
    // Add click event listeners to player cards
    playerCards.forEach(card => {
        // Remove existing event listeners by cloning
        const newCard = card.cloneNode(true);
        card.parentNode.replaceChild(newCard, card);
        
        // Add new click event listener
        newCard.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const playerId = this.dataset.playerId;
            const playerName = this.dataset.playerName;
            
            if (playerId && playerName) {
                console.log(`🎯 Player card clicked: ${playerName}`);
                selectPlayer(playerId, playerName, this);
            }
        });
    });
    
    // Add click event listeners to position slots
    positionSlots.forEach(slot => {
        // Remove existing event listeners by cloning
        const newSlot = slot.cloneNode(true);
        slot.parentNode.replaceChild(newSlot, slot);
        
        // Add new click event listener
        newSlot.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const line = this.dataset.line;
            const position = this.dataset.position;
            
            if (line && position) {
                console.log(`🎯 Position slot clicked: Line ${line} ${position}`);
                placePlayerInPosition(line, position, this);
            }
        });
    });
    
    console.log('✅ Mobile touch fix applied successfully!');
    console.log('📱 Touch interactions should now work on mobile devices');
}

// Apply the fix when the page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixMobileTouch);
} else {
    fixMobileTouch();
}

// Also apply the fix after a short delay to ensure all elements are loaded
setTimeout(fixMobileTouch, 1000);
