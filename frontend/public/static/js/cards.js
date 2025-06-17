// Enhanced Card Management with Revolut-like Swipe Interface
let cardsData = [];
let currentCardIndex = 0;
let isCustomizing = false;

class CardSwiper {
    constructor() {
        this.currentIndex = 0;
        this.cards = [];
        this.swiper = document.getElementById('cardsSwiper');
        this.indicators = document.getElementById('cardIndicators');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.customizeBtn = document.getElementById('customizeBtn');
        this.detailsBtn = document.getElementById('detailsBtn');
        this.customizationPanel = document.getElementById('customizationPanel');
        
        this.initializeEventListeners();
        this.loadCards();
    }

    initializeEventListeners() {
        // Navigation buttons
        this.prevBtn?.addEventListener('click', () => this.previousCard());
        this.nextBtn?.addEventListener('click', () => this.nextCard());
        
        // Action buttons
        this.customizeBtn?.addEventListener('click', () => this.toggleCustomization());
        this.detailsBtn?.addEventListener('click', () => this.showCardDetails());
        
        // Customization panel
        document.getElementById('saveCustomization')?.addEventListener('click', () => this.saveCustomization());
        document.getElementById('cancelCustomization')?.addEventListener('click', () => this.cancelCustomization());
        
        // Color options
        document.querySelectorAll('.color-option').forEach(option => {
            option.addEventListener('click', () => this.selectColor(option));
        });
        
        // Touch/swipe support
        this.initializeTouchEvents();
        
        // Floating add button
        document.getElementById('addCardBtn')?.addEventListener('click', () => this.addNewCard());
    }

    initializeTouchEvents() {
        let startX = 0;
        let startY = 0;
        let isSwipeReady = false;

        this.swiper?.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            isSwipeReady = true;
        });

        this.swiper?.addEventListener('touchmove', (e) => {
            if (!isSwipeReady) return;
            e.preventDefault();
        });

        this.swiper?.addEventListener('touchend', (e) => {
            if (!isSwipeReady) return;
            isSwipeReady = false;
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            // Check if it's a horizontal swipe
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (diffX > 0) {
                    this.nextCard();
                } else {
                    this.previousCard();
                }
            }
        });
    }

    async loadCards() {
        try {
            const response = await fetch('/api/v1/cards/user-cards', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const cards = await response.json();
                this.cards = cards;
                cardsData = cards;
                this.renderCards();
                this.updateNavigation();
                this.loadCardsList();
            } else {
                console.error('Failed to load cards');
                this.showEmptyState();
            }
        } catch (error) {
            console.error('Error loading cards:', error);
            this.showEmptyState();
        }
    }

    renderCards() {
        if (!this.swiper) return;
        
        this.swiper.innerHTML = '';
        
        if (this.cards.length === 0) {
            this.showEmptyState();
            return;
        }

        this.cards.forEach((card, index) => {
            const cardElement = this.createCardElement(card, index);
            this.swiper.appendChild(cardElement);
        });

        this.updateCardPositions();
        this.createIndicators();
    }

    createCardElement(card, index) {
        const cardDiv = document.createElement('div');
        cardDiv.className = `card-slide ${this.getCardTheme(card)}`;
        cardDiv.setAttribute('data-card-id', card.id);
        
        // Determine card status
        const isExpired = this.isCardExpired(card);
        const statusText = isExpired ? 'EXPIRED' : (card.is_active ? 'ACTIVE' : 'INACTIVE');
        
        cardDiv.innerHTML = `
            <div class="card-header">
                <div class="card-brand">${card.brand.toUpperCase()}</div>
                <div class="card-type-badge">${card.type}</div>
            </div>
            
            <div class="card-number">${card.masked_number || this.formatCardNumber(card.last_four)}</div>
            
            <div class="card-footer">
                <div class="card-holder">${card.cardholder_name}</div>
                <div class="card-expiry">${String(card.exp_month).padStart(2, '0')}/${String(card.exp_year).slice(-2)}</div>
            </div>
            
            <div class="card-status-overlay" style="position: absolute; top: 10px; right: 10px; 
                 background: rgba(255,255,255,0.9); color: #333; padding: 4px 8px; 
                 border-radius: 12px; font-size: 0.7rem; font-weight: bold;">
                ${statusText}
            </div>
        `;

        return cardDiv;
    }

    formatCardNumber(lastFour) {
        return `•••• •••• •••• ${lastFour}`;
    }

    getCardTheme(card) {
        // Get custom theme from card design or default based on brand
        if (card.design && card.design.color) {
            return this.colorToTheme(card.design.color);
        }
        
        // Default themes based on card brand
        const brandThemes = {
            'mastercard': 'mastercard-red',
            'visa': 'visa-blue',
            'amex': 'amex-green',
            'american express': 'amex-green',
            'discover': 'discover-orange'
        };
        
        return brandThemes[card.brand.toLowerCase()] || 'custom-purple';
    }

    colorToTheme(color) {
        const colorMap = {
            '#ff416c': 'mastercard-red',
            '#667eea': 'visa-blue',
            '#56ab2f': 'amex-green',
            '#f093fb': 'discover-orange',
            '#667eea': 'custom-purple',
            '#11998e': 'custom-teal',
            '#ff9a9e': 'custom-sunset',
            '#667eea': 'custom-ocean',
            '#232526': 'custom-midnight'
        };
        
        return colorMap[color] || 'custom-purple';
    }

    updateCardPositions() {
        const cards = this.swiper.querySelectorAll('.card-slide');
        
        cards.forEach((card, index) => {
            card.classList.remove('active', 'prev', 'next');
            
            if (index === this.currentIndex) {
                card.classList.add('active');
            } else if (index === this.currentIndex - 1) {
                card.classList.add('prev');
            } else if (index === this.currentIndex + 1) {
                card.classList.add('next');
            }
        });
        
        currentCardIndex = this.currentIndex;
    }

    createIndicators() {
        if (!this.indicators) return;
        
        this.indicators.innerHTML = '';
        
        this.cards.forEach((_, index) => {
            const indicator = document.createElement('div');
            indicator.className = `indicator ${index === this.currentIndex ? 'active' : ''}`;
            indicator.addEventListener('click', () => this.goToCard(index));
            this.indicators.appendChild(indicator);
        });
    }

    updateNavigation() {
        if (this.prevBtn) {
            this.prevBtn.disabled = this.currentIndex === 0;
        }
        
        if (this.nextBtn) {
            this.nextBtn.disabled = this.currentIndex >= this.cards.length - 1;
        }
        
        // Update indicators
        document.querySelectorAll('.indicator').forEach((indicator, index) => {
            indicator.classList.toggle('active', index === this.currentIndex);
        });
    }

    previousCard() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.updateCardPositions();
            this.updateNavigation();
        }
    }

    nextCard() {
        if (this.currentIndex < this.cards.length - 1) {
            this.currentIndex++;
            this.updateCardPositions();
            this.updateNavigation();
        }
    }

    goToCard(index) {
        if (index >= 0 && index < this.cards.length) {
            this.currentIndex = index;
            this.updateCardPositions();
            this.updateNavigation();
        }
    }

    toggleCustomization() {
        if (this.cards.length === 0) {
            this.showMessage('No cards available to customize', 'warning');
            return;
        }
        
        isCustomizing = !isCustomizing;
        this.customizationPanel.classList.toggle('active', isCustomizing);
        
        if (isCustomizing) {
            this.loadCurrentCardTheme();
        }
    }

    loadCurrentCardTheme() {
        const currentCard = this.cards[this.currentIndex];
        if (!currentCard) return;
        
        const currentTheme = this.getCardTheme(currentCard);
        
        // Clear previous selections
        document.querySelectorAll('.color-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        // Select current theme
        const currentOption = document.querySelector(`[data-theme="${currentTheme}"]`);
        if (currentOption) {
            currentOption.classList.add('selected');
        }
    }

    selectColor(option) {
        // Clear previous selections
        document.querySelectorAll('.color-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        
        // Select new color
        option.classList.add('selected');
        
        // Preview the change
        const newTheme = option.getAttribute('data-theme');
        const activeCard = this.swiper.querySelector('.card-slide.active');
        if (activeCard) {
            // Remove all theme classes
            const themeClasses = [
                'mastercard-red', 'visa-blue', 'amex-green', 'discover-orange',
                'custom-purple', 'custom-teal', 'custom-sunset', 'custom-ocean', 'custom-midnight'
            ];
            activeCard.classList.remove(...themeClasses);
            activeCard.classList.add(newTheme);
        }
    }

    async saveCustomization() {
        const selectedOption = document.querySelector('.color-option.selected');
        if (!selectedOption) {
            this.showMessage('Please select a color theme', 'warning');
            return;
        }
        
        const currentCard = this.cards[this.currentIndex];
        const newTheme = selectedOption.getAttribute('data-theme');
        
        try {
            const response = await fetch(`/api/v1/cards/${currentCard.id}/customize`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    theme: newTheme,
                    color: this.themeToColor(newTheme)
                })
            });
            
            if (response.ok) {
                this.showMessage('Card customization saved successfully!', 'success');
                this.toggleCustomization();
                await this.loadCards(); // Refresh cards
            } else {
                throw new Error('Failed to save customization');
            }
        } catch (error) {
            console.error('Error saving customization:', error);
            this.showMessage('Failed to save customization. Please try again.', 'error');
        }
    }

    themeToColor(theme) {
        const themeColors = {
            'mastercard-red': '#ff416c',
            'visa-blue': '#667eea',
            'amex-green': '#56ab2f',
            'discover-orange': '#f093fb',
            'custom-purple': '#667eea',
            'custom-teal': '#11998e',
            'custom-sunset': '#ff9a9e',
            'custom-ocean': '#667eea',
            'custom-midnight': '#232526'
        };
        
        return themeColors[theme] || '#667eea';
    }

    cancelCustomization() {
        this.toggleCustomization();
        // Restore original theme
        const currentCard = this.cards[this.currentIndex];
        if (currentCard) {
            const originalTheme = this.getCardTheme(currentCard);
            const activeCard = this.swiper.querySelector('.card-slide.active');
            if (activeCard) {
                const themeClasses = [
                    'mastercard-red', 'visa-blue', 'amex-green', 'discover-orange',
                    'custom-purple', 'custom-teal', 'custom-sunset', 'custom-ocean', 'custom-midnight'
                ];
                activeCard.classList.remove(...themeClasses);
                activeCard.classList.add(originalTheme);
            }
        }
    }

    showCardDetails() {
        if (this.cards.length === 0) {
            this.showMessage('No cards available', 'warning');
            return;
        }
        
        const currentCard = this.cards[this.currentIndex];
        this.populateCardModal(currentCard);
        
        const modal = new bootstrap.Modal(document.getElementById('cardDetailsModal'));
        modal.show();
    }

    populateCardModal(card) {
        document.getElementById('modal-card-number').textContent = card.masked_number || this.formatCardNumber(card.last_four);
        document.getElementById('modal-expiry').textContent = `${String(card.exp_month).padStart(2, '0')}/${card.exp_year}`;
        document.getElementById('modal-card-type').textContent = `${card.brand.toUpperCase()} ${card.type.toUpperCase()}`;
        document.getElementById('modal-cardholder').textContent = card.cardholder_name;
        document.getElementById('modal-status').textContent = this.isCardExpired(card) ? 'EXPIRED' : (card.is_active ? 'ACTIVE' : 'INACTIVE');
        document.getElementById('modal-added').textContent = new Date(card.created_at).toLocaleDateString();
    }

    isCardExpired(card) {
        const now = new Date();
        const expiry = new Date(card.exp_year, card.exp_month - 1);
        return expiry < now;
    }

    showEmptyState() {
        if (!this.swiper) return;
        
        this.swiper.innerHTML = `
            <div class="empty-state" style="display: flex; flex-direction: column; align-items: center; 
                 justify-content: center; height: 220px; color: var(--bs-secondary-color);">
                <i class="bi bi-credit-card-2-front" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <h3>No Cards Yet</h3>
                <p>Add your first card to get started</p>
                <button class="btn btn-primary mt-2" onclick="cardSwiper.addNewCard()">
                    <i class="bi bi-plus"></i> Add Card
                </button>
            </div>
        `;
        
        // Hide navigation and actions
        document.querySelector('.swiper-navigation')?.style.setProperty('display', 'none');
        document.querySelector('.card-actions')?.style.setProperty('display', 'none');
    }

    addNewCard() {
        // Navigate to add card page or show modal
        window.location.href = '/deposits'; // Assuming cards are added through deposits
    }

    showMessage(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Legacy card list functionality
    async loadCardsList() {
        const initialCardsContainer = document.getElementById('initial-cards');
        if (!initialCardsContainer) return;
        
        initialCardsContainer.innerHTML = '';
        
        this.cards.forEach(card => {
            const cardItem = this.createCardListItem(card);
            initialCardsContainer.appendChild(cardItem);
        });
        
        // Hide loading indicator
        const loadingContainer = document.getElementById('cards-loading');
        if (loadingContainer) {
            loadingContainer.classList.add('hidden');
        }
    }

    createCardListItem(card) {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card-item';
        cardDiv.setAttribute('data-card-id', card.id);
        
        const isExpired = this.isCardExpired(card);
        const statusClass = isExpired ? 'text-danger' : (card.is_active ? 'text-success' : 'text-warning');
        const statusText = isExpired ? 'Expired' : (card.is_active ? 'Active' : 'Inactive');
        
        cardDiv.innerHTML = `
            <div class="card-icon ${card.type}">
                <i class="bi bi-credit-card"></i>
            </div>
            <div class="card-details">
                <div class="card-number">${card.brand.toUpperCase()} ••••${card.last_four}</div>
                <div class="expiry">Expires ${String(card.exp_month).padStart(2, '0')}/${card.exp_year}</div>
            </div>
            <div class="card-status ${statusClass}">${statusText}</div>
            <i class="bi bi-chevron-right info-icon"></i>
        `;
        
        cardDiv.addEventListener('click', () => {
            this.populateCardModal(card);
            const modal = new bootstrap.Modal(document.getElementById('cardDetailsModal'));
            modal.show();
        });
        
        return cardDiv;
    }
}

// Initialize the card swiper when page loads
let cardSwiper;

document.addEventListener('DOMContentLoaded', function() {
    cardSwiper = new CardSwiper();
    
    // Section toggle functionality
    const toggleElement = document.getElementById('cards-toggle');
    const contentElement = document.getElementById('cards-list-content');
    
    if (toggleElement && contentElement) {
        toggleElement.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !isExpanded);
            contentElement.classList.toggle('show');
            
            const chevron = this.querySelector('.bi-chevron-down, .bi-chevron-up');
            if (chevron) {
                chevron.classList.toggle('bi-chevron-down');
                chevron.classList.toggle('bi-chevron-up');
            }
        });
    }
    
    // Modal customize button
    document.getElementById('customize-card-btn')?.addEventListener('click', function() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('cardDetailsModal'));
        modal.hide();
        cardSwiper.toggleCustomization();
    });
});

// Legacy functions for compatibility
function showMessage(elementId, message, isSuccess) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.className = `alert ${isSuccess ? 'alert-success' : 'alert-danger'}`;
        element.style.display = 'block';
    }
} 