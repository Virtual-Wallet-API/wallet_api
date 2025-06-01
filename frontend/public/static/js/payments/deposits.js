let stripeInstance;
let stripeElements;
let stripeCardElement;
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

// Update balance with animation
function updateBalance() {
    const balanceElement = document.getElementById('balance-amount');
    if (!balanceElement) return;

    const userData = auth.getUserData();
    if (userData && userData.balance) {
        const currentBalance = parseFloat(balanceElement.textContent.replace('$', ''));
        const newBalance = userData.balance;
        animateBalanceChange(balanceElement, currentBalance, newBalance);
    } else {
        balanceElement.textContent = '$0.00';
    }
}

// Animate balance changes
function animateBalanceChange(element, startValue, endValue) {
    if (isNaN(startValue)) startValue = 0;

    const duration = 1500;
    const frameDuration = 1000 / 60;
    const totalFrames = Math.round(duration / frameDuration);
    let currentFrame = 0;

    element.classList.add('balance-updating');

    const counter = setInterval(() => {
        currentFrame++;
        const progress = currentFrame / totalFrames;
        const easeOutQuad = 1 - (1 - progress) * (1 - progress);
        const currentValue = startValue + (easeOutQuad * (endValue - startValue));

        element.textContent = `$${currentValue.toFixed(2)}`;

        if (currentFrame === totalFrames) {
            clearInterval(counter);
            element.textContent = `$${endValue.toFixed(2)}`;
            setTimeout(() => element.classList.remove('balance-updating'), 500);
        }
    }, frameDuration);
}

// ### UI Helper Functions
function setLoadingState(isLoading) {
    const submitButton = document.getElementById('btn-submit-deposit');
    const buttonText = document.getElementById('btn-deposit-text');
    const spinner = document.getElementById('deposit-spinner');
    const form = document.getElementById('deposit-form-main');
    const formLoadingOverlay = document.querySelector('.form-loading-overlay');

    if (submitButton && buttonText && spinner) {
        submitButton.disabled = isLoading;
        buttonText.style.display = isLoading ? 'none' : 'block';
        spinner.style.display = isLoading ? 'block' : 'none';

        if (formLoadingOverlay) formLoadingOverlay.style.display = isLoading ? 'flex' : 'none';
        if (form) {
            const inputs = form.querySelectorAll('input, select, button');
            inputs.forEach(input => {
                input.disabled = isLoading;
                input.classList.toggle('disabled', isLoading);
            });
        }
    }
}

function clearFormMessage() {
    const errorDiv = document.getElementById('error-message-deposit');
    const successDiv = document.getElementById('success-message-deposit');

    [errorDiv, successDiv].forEach(div => {
        if (div) {
            div.classList.remove('visible');
            div.style.display = 'none';
        }
    });
}

function displayFormMessage(message, type = 'error', containerId = 'stripe-deposit-box') {
    const messageId = type === 'success' ? 'success-message-deposit' : 'error-message-deposit';
    const messageDiv = document.getElementById(messageId);
    const otherMessageId = type === 'success' ? 'error-message-deposit' : 'success-message-deposit';
    const otherMessageDiv = document.getElementById(otherMessageId);
    const cardErrorMsg = document.getElementById('stripe-card-error-message');

    if (!messageDiv || (cardErrorMsg && cardErrorMsg.style.display !== 'none')) return;

    if (otherMessageDiv) {
        otherMessageDiv.classList.remove('visible');
        otherMessageDiv.style.display = 'none';
    }

    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
    messageDiv.setAttribute('role', 'alert');
    messageDiv.offsetHeight; // Force reflow
    messageDiv.className = `form-message alert alert-${type === 'success' ? 'success' : 'danger'} visible`;

    setTimeout(() => {
        messageDiv.classList.remove('visible');
        setTimeout(() => messageDiv.style.display = 'none', 500);
    }, 6000);
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
        messageDiv.classList.add('visible');

        setTimeout(() => {
            messageDiv.classList.remove('visible');
            setTimeout(() => messageDiv.style.display = 'none', 500);
        }, 5000);
    }
}

function displayStripeCriticalError(message, showRefresh = true) {
    const depositBox = document.getElementById('stripe-deposit-box');
    const recentDepositsToggle = document.getElementById('toggle-recent-deposits');
    const recentDepositsList = document.getElementById('recent-deposits-list-content');
    const errorBox = document.getElementById('stripe-critical-error-display');
    const errorTextDiv = document.getElementById('critical-error-text-stripe');
    const refreshButton = document.getElementById('btn-refresh-on-error');

    [depositBox, recentDepositsToggle, recentDepositsList].forEach(el => {
        if (el) {
            el.style.opacity = '0';
            setTimeout(() => el.style.display = 'none', 300);
        }
    });

    if (errorBox && errorTextDiv && refreshButton) {
        errorTextDiv.textContent = message;
        errorBox.style.display = 'block';
        refreshButton.style.display = showRefresh ? 'inline-block' : 'none';
        setTimeout(() => errorBox.style.opacity = '1', 10);
    }
}

// ### Authenticated Fetch Helper
async function authenticatedFetch(url, options = {}) {
    const token = auth.getToken();
    if (!token) throw new Error('Authentication token missing.');

    const headers = {
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch {
            errorData = { detail: `HTTP ${response.status}: Request failed.` };
        }
        throw new Error(errorData.detail || 'Request failed.');
    }
    return response;
}

// ### Stripe and Card Functions
async function initializeStripeElements() {
    const token = auth.getToken();
    if (!token) {
        displayStripeCriticalError('Authentication required. Please log in.', false);
        setTimeout(() => window.location.href = `${FE_BASE}/login`, 3000);
        return;
    }

    const formCard = document.querySelector('.deposit-form-card');
    if (formCard) formCard.classList.add('loading');

    try {
        const configResponse = await authenticatedFetch(`${API_BASE}/cards/config`);
        const { publishable_key } = await configResponse.json();
        stripeInstance = Stripe(publishable_key);
        stripeElements = stripeInstance.elements();

        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        const style = {
            base: {
                color: isDark ? '#e0e0e0' : '#212529',
                fontFamily: '"Inter", sans-serif',
                fontSize: '16px',
                fontWeight: '500',
                '::placeholder': { color: isDark ? '#6c757d' : '#adb5bd' },
                iconColor: isDark ? '#bb86fc' : '#6f42c1',
            },
            invalid: { color: '#dc3545', iconColor: '#dc3545' }
        };

        stripeCardElement = stripeElements.create('card', { style, hidePostalCode: true });
        stripeCardElement.mount('#stripe-card-element');

        stripeCardElement.on('change', event => {
            const displayError = document.getElementById('stripe-card-error-message');
            if (!displayError) return;

            if (event.error) {
                displayError.textContent = event.error.message;
                displayError.style.display = 'block';
                setTimeout(() => displayError.classList.add('visible'), 10);
            } else {
                displayError.classList.remove('visible');
                setTimeout(() => {
                    displayError.textContent = '';
                    displayError.style.display = 'none';
                }, 300);
            }
        });

        if (formCard) formCard.classList.remove('loading');
    } catch (error) {
        console.error('Stripe Initialization Error:', error);
        displayStripeCriticalError('Could not initialize payment system. Please try again later.');
    }
}

async function loadSavedCards() {
    const token = auth.getToken();
    if (!token) return;

    const selectEl = document.getElementById('select-payment-method');
    if (selectEl) {
        selectEl.innerHTML = '<option value="">Loading saved cards...</option>';
        selectEl.disabled = true;
    }

    try {
        const response = await authenticatedFetch(`${API_BASE}/cards`);
        const data = await response.json();
        currentSavedCards = data.cards || [];
        populatePaymentMethodsDropdown(currentSavedCards);
        populateManageCardsModal(currentSavedCards);
    } catch (error) {
        console.error('Error loading saved cards:', error);
        displayFormMessage('Could not load saved payment methods.', 'error');
        populatePaymentMethodsDropdown([]);
    }
}

function updateFormForSelection() {
    const selectEl = document.getElementById('select-payment-method');
    const cardIconEl = document.getElementById('selected-card-brand-icon');
    const newCardGroup = document.getElementById('stripe-card-element-group');
    const saveCardOption = document.getElementById('save-new-card-option');

    if (!selectEl || !cardIconEl) return;

    const selectedValue = selectEl.value;
    const selectedOption = selectEl.querySelector(`option[value="${selectedValue}"]`);
    const brand = selectedOption ? selectedOption.dataset.brand : 'default';

    cardIconEl.className = getCardBrandIcon(brand);

    if (selectedValue === 'new') {
        if (newCardGroup) {
            newCardGroup.style.display = 'block';
            newCardGroup.style.opacity = '0';
            setTimeout(() => {
                newCardGroup.style.opacity = '1';
                newCardGroup.style.transform = 'translateY(0)';
            }, 10);
        }
        if (saveCardOption) {
            saveCardOption.style.display = 'flex';
            saveCardOption.style.opacity = '0';
            setTimeout(() => {
                saveCardOption.style.opacity = '1';
                saveCardOption.style.transform = 'translateY(0)';
            }, 150);
        }
        if (stripeCardElement) setTimeout(() => stripeCardElement.focus(), 300);
    } else {
        [newCardGroup, saveCardOption].forEach(el => {
            if (el) {
                el.style.opacity = '0';
                el.style.transform = 'translateY(-10px)';
                setTimeout(() => el.style.display = 'none', 300);
            }
        });
    }
}

function populatePaymentMethodsDropdown(cards) {
    const selectEl = document.getElementById('select-payment-method');
    if (!selectEl) return;

    selectEl.innerHTML = '<option value="new">Use a new card</option>';
    selectEl.disabled = false;

    let defaultSelected = 'new';
    cards.forEach(card => {
        const option = document.createElement('option');
        option.value = card.stripe_payment_method_id;
        option.textContent = `${card.brand ? card.brand.charAt(0).toUpperCase() + card.brand.slice(1) : 'Card'} **** ${card.last_four} (Exp: ${card.exp_month}/${String(card.exp_year).slice(2)})`;
        option.dataset.brand = card.brand;
        selectEl.appendChild(option);
        if (card.is_default) defaultSelected = card.stripe_payment_method_id;
    });

    selectEl.value = defaultSelected;
    updateFormForSelection();
}

// ### Manage Cards Modal
function populateManageCardsModal(cards) {
    const listContainer = document.getElementById('modal-saved-cards-list-container');
    const noCardsMsg = document.getElementById('no-saved-cards-message');

    if (!listContainer) return;

    listContainer.innerHTML = '';
    if (!cards || cards.length === 0) {
        if (noCardsMsg) noCardsMsg.style.display = 'block';
        return;
    }

    if (noCardsMsg) noCardsMsg.style.display = 'none';

    cards.forEach((card, index) => {
        const item = document.createElement('div');
        item.className = 'saved-card-entry';
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
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
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, 100 * index);
    });

    setTimeout(() => {
        listContainer.querySelectorAll('.btn-remove-card').forEach(btn => btn.addEventListener('click', handleRemoveCard));
        listContainer.querySelectorAll('.btn-set-default').forEach(btn => btn.addEventListener('click', handleSetDefaultCard));
    }, 100);
}

async function handleRemoveCard(event) {
    const cardId = event.currentTarget.dataset.cardId;
    if (!confirm('Are you sure you want to remove this card?')) return;

    const token = auth.getToken();
    if (!token) {
        displayModalMessage('Authorization required. Please refresh the page.', 'error');
        return;
    }

    const cardItem = event.currentTarget.closest('.saved-card-entry');
    if (cardItem) cardItem.classList.add('removing');

    try {
        await authenticatedFetch(`${API_BASE}/cards/${cardId}`, { method: 'DELETE' });
        displayModalMessage('Card removed successfully.', 'success');

        if (cardItem) {
            cardItem.style.height = `${cardItem.offsetHeight}px`;
            cardItem.style.opacity = '0';
            cardItem.style.transform = 'translateX(50px)';
            setTimeout(() => {
                cardItem.style.height = '0';
                cardItem.style.marginBottom = '0';
                cardItem.style.padding = '0';
                setTimeout(() => loadSavedCards(), 300);
            }, 300);
        } else {
            loadSavedCards();
        }
    } catch (error) {
        displayModalMessage(error.message || 'Could not remove card.', 'error');
        if (cardItem) cardItem.classList.remove('removing');
    }
}

async function handleSetDefaultCard(event) {
    const cardId = event.currentTarget.dataset.cardId;
    const token = auth.getToken();
    if (!token) {
        displayModalMessage('Authorization required. Please refresh the page.', 'error');
        return;
    }

    const button = event.currentTarget;
    const originalText = button.textContent;
    button.innerHTML = '<i class="bi bi-arrow-repeat"></i>';
    button.disabled = true;

    try {
        await authenticatedFetch(`${API_BASE}/cards/${cardId}/set-default`, { method: 'POST' });
        displayModalMessage('Default card updated.', 'success');

        const cardItem = button.closest('.saved-card-entry');
        if (cardItem) {
            cardItem.classList.add('highlight-success');
            setTimeout(() => loadSavedCards(), 700);
        } else {
            loadSavedCards();
        }
    } catch (error) {
        displayModalMessage(error.message || 'Could not set default card.', 'error');
        button.textContent = originalText;
        button.disabled = false;
    }
}

// ### Deposit Submission
document.getElementById('deposit-form-main')?.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!stripeInstance || !stripeElements || !stripeCardElement) {
        console.error('Stripe not initialized:', { stripeInstance, stripeElements, stripeCardElement });
        displayFormMessage('Payment system not ready. Please refresh the page.', 'error');
        return;
    }

    const token = auth.getToken();
    const userData = auth.getUserData();
    if (!API_BASE || !token) {
        console.error('API configuration missing:', { API_BASE, token });
        displayFormMessage('System configuration error. Please try again later.', 'error');
        return;
    }

    setLoadingState(true);
    clearFormMessage();

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
        amountInput.classList.add('is-invalid');
        setTimeout(() => amountInput.classList.remove('is-invalid'), 3000);
        setLoadingState(false);
        return;
    }

    amountInput.classList.add('is-valid');
    setTimeout(() => amountInput.classList.remove('is-valid'), 2000);

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
            const { paymentMethod, error } = await stripeInstance.createPaymentMethod({
                type: 'card',
                card: stripeCardElement,
                billing_details: { name: userData?.username || 'VWallet User' }
            });
            if (error) throw new Error(error.message || 'Failed to create payment method.');
            paymentMethodToUse = paymentMethod.id;
        }

        const intentResponse = await authenticatedFetch(`${API_BASE}/deposits/payment-intent`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                amount_cents: Math.round(amount * 100),
                payment_method_id: paymentMethodToUse,
                save_payment_method: saveCard
            })
        });

        const { client_secret, payment_intent_id } = await intentResponse.json();
        if (!client_secret || !payment_intent_id) throw new Error('Invalid response from payment server.');

        const confirmResult = await stripeInstance.confirmCardPayment(client_secret, {
            payment_method: paymentMethodToUse,
            setup_future_usage: saveCard ? 'off_session' : undefined
        });
        if (confirmResult.error) throw new Error(confirmResult.error.message || 'Payment confirmation failed.');

        await authenticatedFetch(`${API_BASE}/deposits/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                payment_intent_id,
                save_card: saveCard,
                cardholder_name: userData?.username || 'VWallet User'
            })
        });

        const depositForm = document.getElementById('deposit-form-main');
        if (depositForm) {
            depositForm.classList.add('success');
            setTimeout(() => depositForm.classList.remove('success'), 2000);
            depositForm.reset();
        }

        if (isNewCard && stripeCardElement) stripeCardElement.clear();

        displayFormMessage(`Deposit of $${amount.toFixed(2)} successful!`, 'success');

        setTimeout(() => {
            if (typeof loadSavedCards === 'function') loadSavedCards();
            if (typeof loadRecentDeposits === 'function') loadRecentDeposits();
            if (typeof refreshUserData === 'function') refreshUserData();
        }, 500);

        await updateDepositStatistics();
    } catch (error) {
        console.error('Deposit Error:', error);
        displayFormMessage(error.message || 'An error occurred during deposit.', 'error');
    } finally {
        setLoadingState(false);
    }
});

// ### Recent Deposits
async function loadRecentDeposits() {
    const listContainer = document.getElementById('initial-recent-deposits');
    const loadingDiv = document.getElementById('recent-deposits-loading');
    const viewMoreContainer = document.getElementById('view-more-deposits-btn-container');

    if (!listContainer || !loadingDiv) return;

    const token = auth.getToken();
    if (!token) return;

    loadingDiv.style.display = 'flex';
    listContainer.innerHTML = '';
    if (viewMoreContainer) viewMoreContainer.style.display = 'none';

    try {
        const response = await authenticatedFetch(`${API_BASE}/deposits?limit=16`);
        const data = await response.json();
        const deposits = data.deposits || [];

        setTimeout(() => {
            if (deposits.length === 0) {
                listContainer.innerHTML = '<p class="text-muted p-3 text-center">No recent deposits.</p>';
            } else {
                deposits.forEach((deposit, index) => {
                    const item = document.createElement('div');
                    item.className = 'deposit-list-item';
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(-20px)';
                    item.innerHTML = `
                        <span class="date">${new Date(deposit.created_at).toLocaleDateString()}</span>
                        <span class="card-details">Card **** ${deposit.card_last_four || 'N/A'}</span>
                        <span class="status">${deposit.status.charAt(0).toUpperCase() + deposit.status.slice(1)}</span>
                        <span class="amount text-success">+$${parseFloat(deposit.amount).toFixed(2)}</span>
                        <span class="info-icon"><i class="bi bi-info-circle" data-deposit-id="${deposit.id}"></i></span>
                    `;
                    listContainer.appendChild(item);
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateX(0)';
                    }, 80 * index);
                });

                setTimeout(() => {
                    listContainer.querySelectorAll('.info-icon i').forEach(icon => {
                        icon.addEventListener('click', e => {
                            e.stopPropagation();
                            showDepositDetailsModal(e.currentTarget.dataset.depositId);
                        });
                    });
                    listContainer.querySelectorAll('.deposit-list-item').forEach(item => {
                        item.addEventListener('click', e => {
                            const depositId = item.querySelector('.info-icon i')?.dataset.depositId;
                            if (depositId) {
                                item.style.transform = 'translateX(8px) scale(0.98)';
                                setTimeout(() => {
                                    item.style.transform = 'translateX(0)';
                                    showDepositDetailsModal(depositId);
                                }, 150);
                            }
                        });
                    });
                }, deposits.length * 80 + 100);

                if (viewMoreContainer && deposits.length >= 5) {
                    viewMoreContainer.style.opacity = '0';
                    viewMoreContainer.style.display = 'block';
                    setTimeout(() => viewMoreContainer.style.opacity = '1', deposits.length * 80 + 200);
                }
            }
            loadingDiv.style.opacity = '0';
            setTimeout(() => loadingDiv.style.display = 'none', 300);
        }, 600);
    } catch (error) {
        console.error('Error loading recent deposits:', error);
        listContainer.innerHTML = '<p class="text-danger p-3 text-center">Could not load recent deposits.</p>';
        loadingDiv.style.display = 'none';
    }
}

async function showDepositDetailsModal(depositId) {
    const token = auth.getToken();
    if (!token) return;

    const modal = document.getElementById('depositDetailsModal');
    if (!modal) return;

    const detailsModal = new bootstrap.Modal(modal);
    detailsModal.show();

    const modalBody = modal.querySelector('.modal-body');
    if (modalBody) {
        modalBody.innerHTML = `
            <div class="text-center p-5">
                <div class="loading-spinner"><i class="bi bi-arrow-repeat"></i></div>
                <p class="mt-3">Loading details...</p>
            </div>
        `;
    }

    try {
        const response = await authenticatedFetch(`${API_BASE}/deposits/${depositId}`);
        const deposit = await response.json();

        setTimeout(() => {
            if (modalBody) {
                modalBody.innerHTML = `
                    <div class="transaction-detail-item">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">${deposit.created_at ? new Date(deposit.created_at).toLocaleString() : 'N/A'}</span>
                    </div>
                    <div class="transaction-detail-item">
                        <span class="detail-label">Card:</span>
                        <span class="detail-value">${deposit.card_last_four ? `**** ${deposit.card_last_four}` : 'N/A'}</span>
                    </div>
                    <div class="transaction-detail-item">
                        <span class="detail-label">Amount:</span>
                        <span class="detail-value">${deposit.amount ? `$${parseFloat(deposit.amount).toFixed(2)}` : 'N/A'}</span>
                    </div>
                    <div class="transaction-detail-item">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value">${deposit.status ? deposit.status.charAt(0).toUpperCase() + deposit.status.slice(1) : 'N/A'}</span>
                    </div>
                    <div class="transaction-detail-item">
                        <span class="detail-label">Reference ID:</span>
                        <span class="detail-value">${deposit.reference_id || 'N/A'}</span>
                    </div>
                `;

                const items = modalBody.querySelectorAll('.transaction-detail-item');
                items.forEach((item, index) => {
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(-10px)';
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateX(0)';
                    }, 100 * index);
                });
            }
        }, 400);
    } catch (error) {
        console.error('Error fetching deposit details:', error);
        if (modalBody) {
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> Could not load deposit details.
                </div>
            `;
        }
    }
}

// ### Enhanced UI Interactions
function setupEnhancedInteractions() {
    const formInputs = document.querySelectorAll('.form-control, .stripe-element');
    formInputs.forEach(input => {
        input.addEventListener('focus', () => input.closest('.form-group')?.classList.add('input-focused'));
        input.addEventListener('blur', () => input.closest('.form-group')?.classList.remove('input-focused'));
    });

    const balanceDisplay = document.querySelector('.current-balance');
    if (balanceDisplay) {
        balanceDisplay.addEventListener('mouseenter', () => {
            const amount = balanceDisplay.querySelector('.balance-amount');
            if (amount) {
                amount.classList.add('pulse-once');
                setTimeout(() => amount.classList.remove('pulse-once'), 1000);
            }
        });
    }

    const depositsToggle = document.getElementById('toggle-recent-deposits');
    const depositsListContent = document.getElementById('recent-deposits-list-content');
    if (depositsToggle && depositsListContent) {
        depositsToggle.addEventListener('mouseenter', () => depositsToggle.querySelector('i.bi-chevron-down')?.classList.add('hover-effect'));
        depositsToggle.addEventListener('mouseleave', () => depositsToggle.querySelector('i.bi-chevron-down')?.classList.remove('hover-effect'));
    }

    const amountInput = document.getElementById('deposit-amount');
    if (amountInput) {
        amountInput.addEventListener('input', e => {
            const value = parseFloat(e.target.value);
            const amountHint = amountInput.parentElement.parentElement.querySelector('.amount-hint');
            const isValid = value >= 0.5 && value <= 10000;

            amountInput.classList.toggle('is-valid', isValid);
            amountInput.classList.toggle('is-invalid', !isValid);
            if (amountHint) {
                amountHint.classList.toggle('text-success', isValid);
                amountHint.classList.toggle('text-danger', !isValid);
            }
        });

        amountInput.addEventListener('blur', () => {
            setTimeout(() => {
                amountInput.classList.remove('is-valid', 'is-invalid');
                const amountHint = amountInput.parentElement.parentElement.querySelector('.amount-hint');
                if (amountHint) amountHint.classList.remove('text-success', 'text-danger');
            }, 500);
        });
    }
}

function setupQuickAmountButtons() {
    const quickAmounts = document.querySelectorAll('.quick-amount');
    const amountInput = document.getElementById('deposit-amount');
    if (!quickAmounts.length || !amountInput) return;

    quickAmounts.forEach(button => {
        button.addEventListener('click', () => {
            quickAmounts.forEach(btn => btn.classList.remove('selected'));
            button.classList.add('selected');
            amountInput.value = button.dataset.amount;
            amountInput.dispatchEvent(new Event('input', { bubbles: true }));
            button.classList.add('pulse');
            setTimeout(() => button.classList.remove('pulse'), 500);
        });
    });
}

// ### Layout Fixes
function fixLayoutIssues() {
    document.querySelectorAll('.row').forEach(row => {
        if (!row.style.margin) row.style.margin = '0';
    });

    document.querySelectorAll('.summary-card').forEach(card => {
        card.style.height = '100%';
        card.style.minHeight = '180px';
    });

    const depositFormCard = document.querySelector('.deposit-form-card');
    if (depositFormCard) depositFormCard.style.minHeight = '400px';

    const actionCards = document.querySelectorAll('.action-card');
    if (actionCards.length) {
        const containerWidth = document.querySelector('.quick-actions-bar').clientWidth;
        actionCards.forEach(card => {
            card.style.minWidth = '150px';
            card.style.flexBasis = `calc(${100 / actionCards.length}% - 16px)`;
        });
    }
}

// ### Update Deposit Statistics
async function updateDepositStatistics() {
    const token = auth.getToken();
    if (!token) return;

    try {
        const response = await authenticatedFetch(`${API_BASE}/deposits/stats`);
        const data = await response.json();

        const updates = [
            { el: 'monthly-deposits-value', value: data.monthly_total / 100, animate: true },
            { el: 'deposit-frequency', value: `${data.frequency} per month` },
            { el: 'average-deposit-value', value: data.average_amount / 100, animate: true },
            { el: 'total-deposits-count', value: data.total_count },
            { el: 'deposit-trend-percentage', value: `${data.trend_percentage}%` }
        ];

        updates.forEach(({ el, value, animate }) => {
            console.log(`Updating ${el} with value:`, value);
            const element = document.getElementById(el);
            if (element && value !== undefined) {
                if (animate) animateBalanceChange(element, 0, value);
                else element.textContent = value;
            }
        });
    } catch (error) {
        console.error('Error fetching deposit statistics:', error);
        const placeholders = [
            { el: 'monthly-deposits-value', value: 325.00, animate: true },
            { el: 'deposit-frequency', value: '2 per month' },
            { el: 'average-deposit-value', value: 162.50, animate: true },
            { el: 'total-deposits-count', value: '6' },
            { el: 'deposit-trend-percentage', value: '15%' }
        ];
        placeholders.forEach(({ el, value, animate }) => {
            const element = document.getElementById(el);
            if (element) {
                if (animate) animateBalanceChange(element, 0, value);
                else element.textContent = value;
            }
        });
    }
}

// ### Initial Setup
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Deposits page loaded - initializing with enhanced styling');
    document.querySelector('.deposit-page-container')?.classList.add('page-loaded');
    fixLayoutIssues();

    await initializeStripeElements();
    await loadSavedCards();
    await loadRecentDeposits();

    setupEnhancedInteractions();
    setupQuickAmountButtons();
    updateDepositStatistics();

    if (typeof refreshUserData === 'function') {
        await refreshUserData();
        if (userData && typeof userData.balance_cents !== 'undefined') {
            const balanceEl = document.getElementById('balance-amount');
            if (balanceEl) animateBalanceChange(balanceEl, 0, userData.balance_cents / 100);
        }
    }

    document.querySelectorAll('#open-manage-cards-modal, #open-manage-cards-modal-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const manageCardsModal = new bootstrap.Modal(document.getElementById('manageCardsModal'));
            populateManageCardsModal(currentSavedCards);
            manageCardsModal.show();
        });
    });

    const refreshButton = document.getElementById('btn-refresh-on-error');
    if (refreshButton) refreshButton.addEventListener('click', () => window.location.reload());

    const depositsToggle = document.getElementById('toggle-recent-deposits');
    const depositsListContent = document.getElementById('recent-deposits-list-content');
    const depositsArrow = depositsToggle?.querySelector('.toggle-icon');
    if (depositsToggle && depositsListContent && depositsArrow) {
        depositsListContent.classList.remove('collapsed');
        depositsArrow.classList.add('up');
        depositsToggle.setAttribute('aria-expanded', 'true');
        depositsToggle.addEventListener('click', () => {
            const isExpanded = depositsToggle.getAttribute('aria-expanded') === 'true';
            depositsToggle.setAttribute('aria-expanded', String(!isExpanded));
            depositsArrow.classList.toggle('up', !isExpanded);
            depositsListContent.classList.toggle('collapsed', isExpanded);
            if (!isExpanded) {
                depositsListContent.style.overflow = 'hidden';
                setTimeout(() => depositsListContent.style.overflow = 'visible', 400);
            }
        });
    }

    const selectEl = document.getElementById('select-payment-method');
    if (selectEl) selectEl.addEventListener('change', updateFormForSelection);

    updateBalance();
    setInterval(updateBalance, 20000);
    setTimeout(fixLayoutIssues, 500);

    document.dispatchEvent(new CustomEvent('pageContentLoaded'));
});

window.addEventListener('resize', fixLayoutIssues);
document.documentElement.classList.add('deposits-page-enhanced');