let stripeInstance;
let stripeElements;
let stripeCardElement;
let currentSavedCards = []; // To store fetched saved cards

const brandIconClasses = {
    visa: 'bi bi-credit-card-2-front-fill',
    mastercard: 'bi bi-credit-card-fill', // Using a generic fill for MC
    amex: 'bi bi-credit-card-fill', // AMEX often uses a filled icon
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
    const submitButton = document.getElementById('btn-submit-deposit');
    const buttonText = document.getElementById('btn-deposit-text');
    const spinner = document.getElementById('deposit-spinner');
    const formBox = document.getElementById('stripe-deposit-box');

    if (submitButton && buttonText && spinner && formBox) {
        submitButton.disabled = isLoading;
        buttonText.style.display = isLoading ? 'none' : 'inline';
        spinner.style.display = isLoading ? 'inline-block' : 'none'; // Use inline-block for spinner icon
        formBox.classList.toggle('form-loading', isLoading); // Optional: class to dim form
    }
}

function clearFormMessage() {
    const errorDiv = document.getElementById('error-message-deposit');
    const successDiv = document.getElementById('success-message-deposit');
    errorDiv.classList.remove("visible")
    successDiv.classList.remove("visible")
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
}

function displayFormMessage(message, type = 'error', containerId = 'stripe-deposit-box') {
    const messageId = type === 'success' ? 'success-message-deposit' : 'error-message-deposit';
    const messageDiv = document.getElementById(messageId);
    const otherMessageId = type === 'success' ? 'error-message-deposit' : 'success-message-deposit';
    const otherMessageDiv = document.getElementById(otherMessageId);

    messageDiv.style.display = 'none';
    if (document.getElementById("stripe-card-error-message").style.display !== "none") {
        return
    }

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

function displayModalMessage(message, type = 'error', modalId = 'manageCardsModal') {
    const messageId = type === 'success' ? 'manage-cards-modal-success' : 'manage-cards-modal-error';
    const messageDiv = document.getElementById(messageId);
    const otherMessageId = type === 'success' ? 'manage-cards-modal-error' : 'manage-cards-modal-success';
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

function displayStripeCriticalError(message, showRefresh = true) {
    document.getElementById('stripe-deposit-box').style.display = 'none';
    document.getElementById('toggle-recent-deposits').style.display = 'none';
    document.getElementById('recent-deposits-list-content').style.display = 'none';
    const errorBox = document.getElementById('stripe-critical-error-display');
    const errorTextDiv = document.getElementById('critical-error-text-stripe');
    const refreshButton = document.getElementById('btn-refresh-on-error');

    if (errorBox && errorTextDiv && refreshButton) {
        errorTextDiv.textContent = message;
        errorBox.style.display = 'block';
        refreshButton.style.display = showRefresh ? 'block' : 'none';
    }
}

// --- Stripe and Card Functions ---
async function initializeStripeElements() {
    const token = auth.getToken();
    if (!token) {
        displayStripeCriticalError('Authentication required. Please log in.', false);
        setTimeout(() => window.location.href = `${FE_BASE}/login`, 3000);
        return;
    }
    try {
        const configResponse = await fetch(`${API_BASE}/cards/config`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        if (!configResponse.ok) throw new Error('Failed to fetch Stripe configuration.');

        const {publishable_key} = await configResponse.json();
        stripeInstance = Stripe(publishable_key);
        stripeElements = stripeInstance.elements();

        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        const style = {
            base: {
                color: isDark ? '#e0e0e0' : '#212529', // Match theme text
                fontFamily: '"Inter", sans-serif',
                fontSize: '16px', // Bootstrap base font size
                '::placeholder': {color: isDark ? '#6c757d' : '#adb5bd'},
            },
            invalid: {color: '#dc3545', iconColor: '#dc3545'},
        };
        stripeCardElement = stripeElements.create('card', {style});
        stripeCardElement.mount('#stripe-card-element');

        stripeCardElement.on('change', event => {
            const displayError = document.getElementById('stripe-card-error-message');
            displayError.textContent = event.error ? event.error.message : '';
            displayError.style.display = event.error ? 'block' : 'none';
        });
    } catch (error) {
        console.error('Stripe Initialization Error:', error);
        displayStripeCriticalError('Could not initialize payment system. Please try again later.');
    }
}

async function loadSavedCards() {
    if (!token) return;
    try {
        const response = await fetch(`${API_BASE}/cards`, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error('Failed to fetch saved cards.');

        const data = await response.json();
        currentSavedCards = data.cards || [];
        populatePaymentMethodsDropdown(currentSavedCards);
        populateManageCardsModal(currentSavedCards);
    } catch (error) {
        console.error('Error loading saved cards:', error);
        displayFormMessage('Could not load saved payment methods.', 'error');
        populatePaymentMethodsDropdown([]); // Show 'new card' only
    }
}

function populatePaymentMethodsDropdown(cards) {
    const selectEl = document.getElementById('select-payment-method');
    const cardIconEl = document.getElementById('selected-card-brand-icon');
    const newCardGroup = document.getElementById('stripe-card-element-group');
    const saveCardOption = document.getElementById('save-new-card-option');

    selectEl.innerHTML = '<option value="new">Use a new card</option>'; // Default option

    let defaultSelected = 'new';
    cards.forEach(card => {
        const option = document.createElement('option');
        option.value = card.stripe_payment_method_id;
        option.textContent = `${card.brand ? card.brand.charAt(0).toUpperCase() + card.brand.slice(1) : 'Card'} **** ${card.last_four} (Exp: ${card.exp_month}/${String(card.exp_year).slice(2)})`;
        option.dataset.brand = card.brand;
        selectEl.appendChild(option);
        if (card.is_default) defaultSelected = card.stripe_payment_method_id;
    });

    selectEl.value = defaultSelected; // Select default or 'new'

    function updateFormForSelection() {
        const selectedValue = selectEl.value;
        const selectedOption = selectEl.querySelector(`option[value="${selectedValue}"]`);
        const brand = selectedOption ? selectedOption.dataset.brand : 'default';

        cardIconEl.className = getCardBrandIcon(brand);
        if (selectedValue === 'new') {
            newCardGroup.style.display = 'block';
            saveCardOption.style.display = 'flex'; // Show save card option
            if (stripeCardElement) stripeCardElement.focus();
        } else {
            newCardGroup.style.display = 'none';
            saveCardOption.style.display = 'none'; // Hide save card for existing
        }
    }

    selectEl.addEventListener('change', updateFormForSelection);
    updateFormForSelection(); // Initial call
}

// --- Manage Cards Modal ---
function populateManageCardsModal(cards) {
    const listContainer = document.getElementById('modal-saved-cards-list-container');
    const noCardsMsg = document.getElementById('no-saved-cards-message');
    listContainer.innerHTML = ''; // Clear previous items

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

    // Add event listeners for new buttons
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
        loadSavedCards(); // Refresh lists
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
        loadSavedCards(); // Refresh lists
    } catch (error) {
        displayModalMessage(error.message || 'Could not set default card.', 'error');
    }
}

// --- Deposit Submission ---
document.getElementById('deposit-form-main')?.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Check if required dependencies are available
    if (!stripeInstance || !stripeElements || !stripeCardElement) {
        console.error('Stripe not initialized:', {stripeInstance, stripeElements, stripeCardElement});
        displayFormMessage('Payment system not ready. Please refresh.', 'error');
        return;
    }
    if (!API_BASE || !token) {
        console.error('API configuration missing:', {API_BASE, token});
        displayFormMessage('System configuration error. Please try again later.', 'error');
        return;
    }

    setLoadingState(true);
    clearFormMessage();

    // Validate amount
    const amountInput = document.getElementById('deposit-amount');
    if (!amountInput) {
        console.error('Deposit amount input not found');
        displayFormMessage('Form error: Amount field missing.', 'error');
        setLoadingState(false);
        return;
    }
    const amount = parseFloat(amountInput.value);
    if (isNaN(amount) || amount < 0.50) {
        displayFormMessage('Minimum deposit amount is $0.50.', 'error');
        setLoadingState(false);
        return;
    }

    // Get payment method
    const paymentMethodSelect = document.getElementById('select-payment-method');
    if (!paymentMethodSelect) {
        console.error('Payment method select not found');
        displayFormMessage('Form error: Payment method field missing.', 'error');
        setLoadingState(false);
        return;
    }
    const selectedPaymentMethodId = paymentMethodSelect.value;
    const isNewCard = selectedPaymentMethodId === 'new';
    const saveCardCheckbox = document.getElementById('checkbox-save-card');
    const saveCard = isNewCard && saveCardCheckbox?.checked;

    try {
        let paymentMethodToUse = selectedPaymentMethodId;
        if (isNewCard) {
            const {paymentMethod, error} = await stripeInstance.createPaymentMethod({
                type: 'card',
                card: stripeCardElement,
                billing_details: {name: userData?.username || 'VWallet User'}
            });
            if (error) {
                console.error('Stripe createPaymentMethod error:', error);
                throw new Error(error.message || 'Failed to create payment method.');
            }
            paymentMethodToUse = paymentMethod.id;
        }

        // Create payment intent
        const intentResponse = await fetch(`${API_BASE}/deposits/payment-intent`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                amount_cents: Math.round(amount * 100),
                payment_method_id: paymentMethodToUse,
                save_payment_method: saveCard
            })
        });
        if (!intentResponse.ok) {
            let errorData;
            try {
                errorData = await intentResponse.json();
            } catch {
                errorData = {detail: `HTTP ${intentResponse.status}: Failed to create payment intent.`};
            }
            console.error('Payment intent error:', errorData);
            throw new Error(errorData.detail || 'Failed to create payment intent.');
        }

        const {client_secret, payment_intent_id} = await intentResponse.json();
        console.log(`Intent fetched: ${payment_intent_id}`);
        if (!client_secret || !payment_intent_id) {
            console.error('Invalid payment intent response:', {client_secret, payment_intent_id});
            throw new Error('Invalid response from payment server.');
        }

        // Confirm payment
        const confirmResult = await stripeInstance.confirmCardPayment(client_secret, {
            payment_method: paymentMethodToUse,
            setup_future_usage: saveCard ? 'off_session' : undefined
        });
        if (confirmResult.error) {
            console.error('Stripe confirmCardPayment error:', confirmResult.error);
            throw new Error(confirmResult.error.message || 'Payment confirmation failed.');
        }

        // Confirm deposit on backend
        const backendConfirmResponse = await fetch(`${API_BASE}/deposits/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                payment_intent_id: payment_intent_id,
                save_card: saveCard,
                cardholder_name: userData?.username || 'VWallet User'
            })
        });

        if (!backendConfirmResponse.ok) {
            let errorData;
            try {
                errorData = await backendConfirmResponse.json();
            } catch {
                errorData = {detail: `HTTP ${backendConfirmResponse.status}: Failed to confirm deposit.`};
            }
            console.error('Backend confirm error:', errorData);
            throw new Error(errorData.detail || 'Failed to confirm deposit on server.');
        }

        // Success handling
        displayFormMessage(`Deposit of $${amount.toFixed(2)} successful!`, 'success');
        document.getElementById('deposit-form-main').reset();
        if (isNewCard && stripeCardElement) {
            stripeCardElement.clear();
        }
        if (typeof populatePaymentMethodsDropdown === 'function' && currentSavedCards) {
            populatePaymentMethodsDropdown(currentSavedCards);
        }
        if (typeof loadRecentDeposits === 'function') {
            loadRecentDeposits();
        }
        if (typeof refreshUserData === 'function') {
            refreshUserData();
        }

    } catch (error) {
        console.error('Deposit Error:', error);
        displayFormMessage(error.message || 'An error occurred during deposit.', 'error');
    } finally {
        setLoadingState(false);
    }
});

// --- Recent Deposits ---
async function loadRecentDeposits() {
    const listContainer = document.getElementById('initial-recent-deposits');
    const loadingDiv = document.getElementById('recent-deposits-loading');
    // const viewMoreContainer = document.getElementById('view-more-deposits-btn-container');
    if (!listContainer || !loadingDiv) return;

    loadingDiv.style.display = 'flex';
    listContainer.innerHTML = '';
    // if(viewMoreContainer) viewMoreContainer.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/deposits?limit=16`, { // Fetch last 5
            headers: {'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error('Failed to fetch recent deposits.');
        const data = await response.json();
        const deposits = data.deposits || [];

        if (deposits.length === 0) {
            listContainer.innerHTML = '<p class="text-muted p-3 text-center">No recent deposits.</p>';
        } else {
            deposits.forEach(deposit => {
                const item = document.createElement('div');
                item.className = 'deposit-list-item'; // Use new class
                item.innerHTML = `
                        <span class="date">${new Date(deposit.created_at).toLocaleDateString()}</span>
                        <span class="card-details">Card **** ${deposit.card_last_four || 'N/A'}</span>
                        <span class="status">${deposit.status.charAt(0).toUpperCase() + deposit.status.slice(1)}</span>
                        <span class="amount text-success">+$${parseFloat(deposit.amount).toFixed(2)}</span>
                        <span class="info-icon"><i class="bi bi-info-circle" data-deposit-id="${deposit.id}"></i></span>
                    `;
                listContainer.appendChild(item);
            });
            // Add listeners for new info icons
            listContainer.querySelectorAll('.info-icon i').forEach(icon => {
                icon.addEventListener('click', (e) => showDepositDetailsModal(e.currentTarget.dataset.depositId));
            });
        }
        // Logic for "View More" can be added here if needed
    } catch (error) {
        console.error('Error loading recent deposits:', error);
        listContainer.innerHTML = '<p class="text-danger p-3 text-center">Could not load recent deposits.</p>';
    } finally {
        loadingDiv.style.display = 'none';
    }
}

function showDepositDetailsModal(depositId) {
    // Find deposit in currentSavedCards or fetch details
    // For now, let's assume we need to fetch, or find it in a pre-fetched detailed list
    // This is a placeholder - you'd fetch full details for the modal
    const deposit = currentSavedCards.find(d => d.id === depositId); // This is wrong, need a proper deposits list

    // Dummy data for now
    document.getElementById('detail-modal-date').textContent = 'N/A'; // Populate with actual data
    document.getElementById('detail-modal-card').textContent = 'N/A';
    document.getElementById('detail-modal-amount').textContent = 'N/A';
    document.getElementById('detail-modal-status').textContent = 'N/A';
    document.getElementById('detail-modal-ref-id').textContent = depositId || 'N/A';

    var detailsModal = new bootstrap.Modal(document.getElementById('depositDetailsModal'));
    detailsModal.show();
}

// --- Initial Setup ---
document.addEventListener('DOMContentLoaded', async () => {
    await initializeStripeElements();
    await loadSavedCards();
    await loadRecentDeposits();

    document.getElementById('open-manage-cards-modal')?.addEventListener('click', () => {
        var manageCardsModal = new bootstrap.Modal(document.getElementById('manageCardsModal'));
        populateManageCardsModal(currentSavedCards); // Ensure it's up-to-date
        manageCardsModal.show();
    });

    document.getElementById('btn-refresh-on-error')?.addEventListener('click', () => window.location.reload());

    // Toggle for recent deposits
    const depositsToggle = document.getElementById('toggle-recent-deposits');
    const depositsListContent = document.getElementById('recent-deposits-list-content');
    const depositsArrow = depositsToggle?.querySelector('i.bi-chevron-down');

    if (depositsToggle && depositsListContent && depositsArrow) {
        // Start collapsed
        depositsListContent.classList.remove('show');
        depositsListContent.style.maxHeight = '0px';
        depositsListContent.style.opacity = '0';
        depositsArrow.classList.remove('up');
        depositsToggle.setAttribute('aria-expanded', 'false');


        depositsToggle.addEventListener('click', () => {
            const isCurrentlyShown = depositsListContent.classList.toggle('show');
            depositsToggle.setAttribute('aria-expanded', isCurrentlyShown.toString());
            depositsArrow.classList.toggle('up', isCurrentlyShown);

            if (isCurrentlyShown) {
                depositsListContent.style.maxHeight = depositsListContent.scrollHeight + 'px';
                depositsListContent.style.opacity = '1';
                setTimeout(() => { // Allow dynamic content changes
                    if (depositsListContent.classList.contains('show')) depositsListContent.style.maxHeight = '2500px';
                }, 500);
            } else {
                depositsListContent.style.maxHeight = depositsListContent.scrollHeight + 'px';
                depositsListContent.offsetHeight; // Trigger reflow
                depositsListContent.style.maxHeight = '0px';
                depositsListContent.style.opacity = '0';
            }
        });
    }

    document.dispatchEvent(new CustomEvent('pageContentLoaded'));
});
