let currentSavedCards = []; // To store fetched saved cards

const brandIconClasses = {
    visa: 'bi bi-credit-card-2-front-fill',
    mastercard: 'bi bi-credit-card-fill',
    amex: 'bi bi-credit-card-fill',
    discover: 'bi bi-credit-card',
    diners: 'bi bi-credit-card',
    jcb: 'bi bi-credit-card',
    unionpay: 'bi bi-credit-card',
    unknown: 'bi bi-credit-card',
    default: 'bi bi-credit-card'
};

function getCardBrandIcon(brand) {
    return brandIconClasses[brand?.toLowerCase()] || brandIconClasses.default;
}

// --- UI Helper Functions ---
function setLoadingState(isLoading) {
    const submitButton = document.getElementById('submit-button');
    const buttonText = document.getElementById('button-text');
    const spinner = document.getElementById('spinner');
    const formBox = document.getElementById('withdrawal-box');

    if (submitButton && buttonText && spinner && formBox) {
        submitButton.disabled = isLoading;
        buttonText.style.display = isLoading ? 'none' : 'inline';
        spinner.style.display = isLoading ? 'inline-block' : 'none';
        formBox.classList.toggle('form-loading', isLoading);
    }
}

function displayFormMessage(message, type = 'error') {
    const messageId = type === 'success' ? 'success-message' : 'error-message';
    const messageDiv = document.getElementById(messageId);
    const otherMessageId = type === 'success' ? 'error-message' : 'success-message';
    const otherMessageDiv = document.getElementById(otherMessageId);

    if (otherMessageDiv) {
        otherMessageDiv.classList.remove('visible');
        otherMessageDiv.style.display = 'none';
    }
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.className = `form-message alert alert-${type === 'success' ? 'success' : 'danger'} visible`;
        messageDiv.style.display = 'block';
        messageDiv.setAttribute('role', 'alert');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageDiv.classList.remove('visible');
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

function displayModalMessage(message, type = 'error') {
    const messageId = type === 'success' ? 'modal-success-message' : 'modal-error-message';
    const messageDiv = document.getElementById(messageId);
    const otherMessageId = type === 'success' ? 'modal-error-message' : 'modal-success-message';
    const otherMessageDiv = document.getElementById(otherMessageId);

    if (otherMessageDiv) otherMessageDiv.style.display = 'none';
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.style.display = 'block';
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

// --- Card Functions ---
async function loadSavedCards() {
    if (!token) return;
    try {
        const response = await fetch(`${API_BASE}/cards`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error('Failed to fetch saved cards.');

        const data = await response.json();
        currentSavedCards = data.cards || [];
        populateCardDropdown(currentSavedCards);
        populateManageCardsModal(currentSavedCards);
    } catch (error) {
        console.error('Error loading saved cards:', error);
        displayFormMessage('Could not load saved cards.', 'error');
        populateCardDropdown([]);
    }
}

function populateCardDropdown(cards) {
    const selectEl = document.getElementById('card-select');
    const cardIconEl = document.getElementById('selected-card-brand-icon');

    selectEl.innerHTML = '<option value="" disabled selected>Select a card</option>';

    let defaultSelected = '';
    cards.forEach(card => {
        const option = document.createElement('option');
        option.value = card.id;
        option.textContent = `${card.brand ? card.brand.charAt(0).toUpperCase() + card.brand.slice(1) : 'Card'} **** ${card.last_four} (Exp: ${card.exp_month}/${String(card.exp_year).slice(2)})`;
        option.dataset.brand = card.brand;
        selectEl.appendChild(option);
        if (card.is_default) defaultSelected = card.id;
    });

    if (defaultSelected) selectEl.value = defaultSelected;

    function updateIconForSelection() {
        const selectedValue = selectEl.value;
        const selectedOption = selectEl.querySelector(`option[value="${selectedValue}"]`);
        const brand = selectedOption ? selectedOption.dataset.brand : 'default';
        cardIconEl.className = getCardBrandIcon(brand);
    }

    selectEl.addEventListener('change', updateIconForSelection);
    updateIconForSelection();
}

function populateManageCardsModal(cards) {
    const listContainer = document.getElementById('saved-cards-list');
    const noCardsMsg = document.getElementById('no-saved-cards-message');
    listContainer.innerHTML = '';

    if (cards.length === 0) {
        if (noCardsMsg) noCardsMsg.style.display = 'block';
        return;
    }
    if (noCardsMsg) noCardsMsg.style.display = 'none';

    cards.forEach(card => {
        const item = document.createElement('div');
        item.className = 'saved-card-entry';
        item.innerHTML = `
                <div class="card-info">
                    <i class="${getCardBrandIcon(card.brand)} card-icon"></i>
                    <span>${card.brand ? card.brand.charAt(0).toUpperCase() + card.brand.slice(1) : 'Card'} **** ${card.last_four} (Exp: ${card.exp_month}/${String(card.exp_year).slice(2)})</span>
                </div>
                <div class="card-actions">
                    ${card.is_default ? '<span class="default-badge">Default</span>' : `<button type="button" class="btn btn-sm btn-outline-secondary btn-set-default" data-card-id="${card.id}">Set Default</button>`}
                    <button type="button" class="btn-remove-card" data-card-id="${card.id}" aria-label="Remove card"><i class="bi bi-trash"></i></button>
                </div>
            `;
        listContainer.appendChild(item);
    });

    listContainer.querySelectorAll('.btn-remove-card').forEach(btn => btn.addEventListener('click', handleRemoveCard));
    listContainer.querySelectorAll('.btn-set-default').forEach(btn => btn.addEventListener('click', handleSetDefaultCard));
}

async function handleRemoveCard(event) {
    const cardId = event.currentTarget.dataset.cardId;
    if (!confirm('Are you sure you want to remove this card?')) return;
    try {
        const response = await fetch(`${API_BASE}/cards/${cardId}`, {
            method: 'DELETE', headers: {'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error('Failed to remove card.');
        displayModalMessage('Card removed successfully.', 'success');
        loadSavedCards();
    } catch (error) {
        displayModalMessage(error.message || 'Could not remove card.', 'error');
    }
}

async function handleSetDefaultCard(event) {
    const cardId = event.currentTarget.dataset.cardId;
    try {
        const response = await fetch(`${API_BASE}/cards/${cardId}/set-default`, {
            method: 'POST', headers: {'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error('Failed to set default card.');
        displayModalMessage('Default card updated.', 'success');
        loadSavedCards();
    } catch (error) {
        displayModalMessage(error.message || 'Could not set default card.', 'error');
    }
}

// --- Withdrawal Functions ---
async function loadRecentWithdrawals() {
    const listContainer = document.getElementById('initial-withdrawals');
    const loadingDiv = document.getElementById('withdrawals-loading');
    if (!listContainer || !loadingDiv) return;

    loadingDiv.style.display = 'flex';
    listContainer.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/withdrawals?limit=16`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error('Failed to fetch recent withdrawals.');
        const data = await response.json();
        console.log(data); // todo-remove
        const withdrawals = data.withdrawals || [];

        if (withdrawals.length === 0) {
            listContainer.innerHTML = '<p class="text-muted p-3 text-center">No recent withdrawals.</p>';
        } else {
            withdrawals.forEach(withdrawal => {
                const item = document.createElement('div');
                item.className = 'withdrawal-list-item';
                item.innerHTML = `
                        <span class="date">${new Date(withdrawal.created_at).toLocaleDateString()}</span>
                        <span class="card-details">Card **** ${withdrawal.card_info?.last_four || 'N/A'}</span>
                        <span class="status">${withdrawal.status.charAt(0).toUpperCase() + withdrawal.status.slice(1)}</span>
                        <span class="amount text-danger">-$${Math.abs(withdrawal.amount).toFixed(2)}</span>
                        <span class="info-icon"><i class="bi bi-info-circle" data-withdrawal-id="${withdrawal.id}"></i></span>
                    `;
                listContainer.appendChild(item);
            });
            listContainer.querySelectorAll('.info-icon i').forEach(icon => {
                icon.addEventListener('click', (e) => showWithdrawalDetailsModal(e.currentTarget.dataset.withdrawalId));
            });
        }
    } catch (error) {
        console.error('Error loading recent withdrawals:', error);
        listContainer.innerHTML = '<p class="text-danger p-3 text-center">Could not load recent withdrawals.</p>';
    } finally {
        loadingDiv.style.display = 'none';
    }
}

function showWithdrawalDetailsModal(withdrawalId) {
    // Placeholder - you'd fetch full details for the modal
    document.getElementById('modal-date').textContent = 'N/A';
    document.getElementById('modal-card').textContent = 'N/A';
    document.getElementById('modal-amount').textContent = 'N/A';
    document.getElementById('modal-status').textContent = 'N/A';

    var detailsModal = new bootstrap.Modal(document.getElementById('withdrawalModal'));
    detailsModal.show();
}

// --- Form Submission ---
document.getElementById('withdrawal-form')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const cardId = document.getElementById('card-select').value;
    const amount = parseFloat(document.getElementById('withdrawal-amount').value);

    if (!cardId) {
        displayFormMessage('Please select a card.', 'error');
        return;
    }
    if (isNaN(amount) || amount < 0.50) {
        displayFormMessage('Please enter a valid amount (minimum $0.50).', 'error');
        return;
    }
    if (amount > parseFloat(userData.balance)) {
        displayFormMessage('Insufficient balance.', 'error');
        return;
    }

    setLoadingState(true);

    try {
        const response = await fetch(`${API_BASE}/withdrawals`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                amount_cents: Math.round(amount * 100),
                card_id: cardId,
                currency_code: "USD",
                withdrawal_type: "payout",
                method: "card",
                description: "Default description"
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to process withdrawal');
        }

        displayFormMessage(`Withdrawal request of $${amount.toFixed(2)} submitted successfully!`, 'success');
        await updateBalancePostWithdrawal(amount)
        document.getElementById('withdrawal-form').reset();
        populateCardDropdown(currentSavedCards);
        loadRecentWithdrawals();
        if (typeof refreshUserData === 'function') refreshUserData();

    } catch (error) {
        console.error('Withdrawal Error:', error);
        displayFormMessage(error.message || 'An error occurred during withdrawal.', 'error');
    } finally {
        setLoadingState(false);
    }
});

async function updateBalancePostWithdrawal(amount = 0) {
    const balanceAmount = document.getElementById('balance-amount');
    const balanceText = document.getElementById('balance-text');
    const balanceLoading = document.getElementById('balance-amount-loading');
    setTimeout(() => {
        balanceAmount.textContent = `$${(userData.balance - amount).toFixed(2)}`;
    }, 150);
    refreshUserData()
}


// --- Initial Setup ---
document.addEventListener('DOMContentLoaded', async () => {
    // Update balance display
    const balanceAmount = document.getElementById('balance-amount');
    const balanceText = document.getElementById('balance-text');
    const balanceLoading = document.getElementById('balance-amount-loading');

    balanceLoading.classList.remove('hidden');
    if (!userData.balance) {
        await refreshUserData();
    }

    await loadSavedCards();

    setTimeout(() => {
        balanceLoading.classList.add('hidden');
        balanceAmount.textContent = `$${userData.balance.toFixed(2)}`;
        balanceAmount.style.opacity = '1';
        balanceText.style.opacity = '1';
    }, 350);

    document.dispatchEvent(new CustomEvent('pageContentLoaded'));

    document.getElementById('manage-cards-button')?.addEventListener('click', () => {
        var manageCardsModal = new bootstrap.Modal(document.getElementById('manageCardsModal'));
        populateManageCardsModal(currentSavedCards);
        manageCardsModal.show();
    });

    // Toggle for recent withdrawals
    const withdrawalsToggle = document.getElementById('withdrawals-toggle');
    const withdrawalsListContent = document.getElementById('recent-withdrawals-list-content');
    const withdrawalsArrow = withdrawalsToggle?.querySelector('i.bi-chevron-down');

    if (withdrawalsToggle && withdrawalsListContent && withdrawalsArrow) {
        // Start collapsed
        withdrawalsListContent.classList.remove('show');
        withdrawalsListContent.style.maxHeight = '0px';
        withdrawalsListContent.style.opacity = '0';
        withdrawalsArrow.classList.remove('up');
        withdrawalsToggle.setAttribute('aria-expanded', 'false');

        withdrawalsToggle.addEventListener('click', () => {
            const isCurrentlyShown = withdrawalsListContent.classList.toggle('show');
            withdrawalsToggle.setAttribute('aria-expanded', isCurrentlyShown.toString());
            withdrawalsArrow.classList.toggle('up', isCurrentlyShown);

            if (isCurrentlyShown) {
                loadRecentWithdrawals(); // Load data when expanding
                withdrawalsListContent.style.maxHeight = withdrawalsListContent.scrollHeight + 'px';
                withdrawalsListContent.style.opacity = '1';
                setTimeout(() => {
                    if (withdrawalsListContent.classList.contains('show')) withdrawalsListContent.style.maxHeight = '2500px';
                }, 500);
            } else {
                withdrawalsListContent.style.maxHeight = withdrawalsListContent.scrollHeight + 'px';
                withdrawalsListContent.offsetHeight;
                withdrawalsListContent.style.maxHeight = '0px';
                withdrawalsListContent.style.opacity = '0';
            }
        });
    }
});