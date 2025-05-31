document.addEventListener('DOMContentLoaded', function() {
    // Initialize section toggle
    initializeSectionToggle();
    
    // Load initial cards
    loadCards();
});

// Section Toggle Functionality
function initializeSectionToggle() {
    const toggle = document.getElementById('cards-toggle');
    const content = document.getElementById('cards-list-content');
    const icon = toggle.querySelector('i.bi-chevron-down');
    
    toggle.addEventListener('click', function() {
        // Toggle expanded state
        const isExpanded = this.getAttribute('aria-expanded') === 'true';
        this.setAttribute('aria-expanded', !isExpanded);
        
        // Toggle content visibility
        if (isExpanded) {
            content.style.maxHeight = '0';
            content.style.opacity = '0';
            content.classList.remove('show');
            icon.classList.remove('up');
        } else {
            content.style.maxHeight = content.scrollHeight + 'px';
            content.style.opacity = '1';
            content.classList.add('show');
            icon.classList.add('up');
        }
    });
}

// Load Cards
function loadCards() {
    const loadingContainer = document.getElementById('cards-loading');
    const initialContainer = document.getElementById('initial-cards');
    const viewMoreContainer = document.getElementById('view-more-cards-btn-container');
    
    // Show loading state
    loadingContainer.classList.remove('hidden');
    
    // Fetch cards from API
    fetch('/api/v1/cards', {
        headers: {
            'Authorization': `Bearer ${auth.getToken()}`
        }
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading state
        loadingContainer.classList.add('hidden');
        
        if (data.cards && data.cards.length > 0) {
            // Render initial cards
            renderCards(data.cards.slice(0, 5), initialContainer);
            
            // Handle additional cards
            if (data.cards.length > 5) {
                const additionalContainer = document.getElementById('additional-cards');
                renderCards(data.cards.slice(5), additionalContainer);
                viewMoreContainer.style.display = 'block';
                
                // Add view more functionality
                document.getElementById('view-cards-btn').addEventListener('click', function(e) {
                    e.preventDefault();
                    additionalContainer.style.maxHeight = additionalContainer.scrollHeight + 'px';
                    additionalContainer.style.opacity = '1';
                    viewMoreContainer.style.display = 'none';
                });
            }
        } else {
            initialContainer.innerHTML = '<p class="text-center text-muted">No cards found.</p>';
        }
    })
    .catch(error => {
        console.error('Error loading cards:', error);
        loadingContainer.classList.add('hidden');
        initialContainer.innerHTML = '<p class="text-center text-danger">Error loading cards. Please try again later.</p>';
    });
}

// Render Cards
function renderCards(cards, container) {
    container.innerHTML = cards.map(card => `
        <div class="card-item" data-card-id="${card.id}" onclick="showCardDetails('${card.id}')">
            <div class="card-icon ${card.type.toLowerCase()}">
                <i class="bi bi-credit-card"></i>
            </div>
            <div class="card-details">
                <div class="card-number">${card.brand} Card ending in ${card.last_four}</div>
                <div class="expiry">Expiry: ${card.exp_month}/${card.exp_year}</div>
            </div>
            <div class="card-status">
                <div>${card.is_default ? 'Default Card' : 'Active'}</div>
            </div>
            <span class="info-icon">
                <i class="bi bi-info-circle"></i>
            </span>
        </div>
    `).join('');
}

// Show Card Details Modal
function showCardDetails(cardId) {
    // Find card in the list
    const cardItem = document.querySelector(`.card-item[data-card-id="${cardId}"]`);
    const cardNumber = cardItem.querySelector('.card-number').textContent;
    const expiry = cardItem.querySelector('.expiry').textContent;
    const status = cardItem.querySelector('.card-status div').textContent;
    
    // Update modal content
    document.getElementById('modal-card-number').textContent = cardNumber;
    document.getElementById('modal-expiry').textContent = expiry.split(': ')[1];
    document.getElementById('modal-card-type').textContent = cardNumber.split(' ')[0];
    document.getElementById('modal-status').textContent = status;
    document.getElementById('modal-added').textContent = new Date().toLocaleDateString(); // You might want to add this to the API response
    
    // Update remove button
    const removeButton = document.getElementById('remove-card-btn');
    removeButton.onclick = function() {
        if (confirm('Are you sure you want to remove this card?')) {
            removeCard(cardId);
        }
    };
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('cardDetailsModal'));
    modal.show();
}

// Remove Card
function removeCard(cardId) {
    fetch(`/api/v1/cards/${cardId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${auth.getToken()}`
        }
    })
    .then(response => {
        if (response.status === 204) {
            // Find and fade out the card
            const cardItem = document.querySelector(`.card-item[data-card-id="${cardId}"]`);
            if (cardItem) {
                cardItem.style.opacity = '0';
                cardItem.style.transform = 'translateX(-20px)';
                setTimeout(() => {
                    cardItem.remove();
                    
                    // Check if there are any cards left
                    const remainingCards = document.querySelectorAll('.card-item');
                    if (remainingCards.length === 0) {
                        const container = document.getElementById('initial-cards');
                        container.innerHTML = '<p class="text-center text-muted">No cards found.</p>';
                    }
                }, 300);
            }
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('cardDetailsModal'));
            modal.hide();
        } else {
            throw new Error('Failed to remove card');
        }
    })
    .catch(error => {
        console.error('Error removing card:', error);
        alert('Error removing card. Please try again later.');
    });
} 