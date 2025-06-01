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

// Update balance from userData with animation
function updateBalance() {
    const balanceElement = document.getElementById('balance-amount');
    if (!balanceElement) return;

    const userData = auth.getUserData();
    if (userData && userData.balance) {
        // Animate balance update
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

    // Add a highlight class
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

            setTimeout(() => {
                element.classList.remove('balance-updating');
            }, 500);
        }
    }, frameDuration);
}

// --- UI Helper Functions ---
function setLoadingState(isLoading) {
    const submitButton = document.getElementById('btn-submit-withdrawal');
    const buttonText = document.getElementById('btn-withdrawal-text');
    const spinner = document.getElementById('withdrawal-spinner');
    const form = document.getElementById('withdrawal-form');
    const formLoadingOverlay = document.querySelector('.form-loading-overlay');

    if (submitButton && buttonText && spinner) {
        submitButton.disabled = isLoading;
        buttonText.style.display = isLoading ? 'none' : 'block';
        spinner.style.display = isLoading ? 'block' : 'none';

        if (formLoadingOverlay) {
            formLoadingOverlay.style.display = isLoading ? 'flex' : 'none';
        }

        if (form) {
            const inputs = form.querySelectorAll('input, select, button');
            inputs.forEach(input => {
                input.disabled = isLoading;
                if (isLoading) {
                    input.classList.add('disabled');
                } else {
                    input.classList.remove('disabled');
                }
            });
        }
    }
}

function clearFormMessage() {
    const errorDiv = document.getElementById('error-message-withdrawal');
    const successDiv = document.getElementById('success-message-withdrawal');

    if (errorDiv) {
        errorDiv.classList.remove("visible");
        errorDiv.style.display = 'none';
    }

    if (successDiv) {
        successDiv.classList.remove("visible");
        successDiv.style.display = 'none';
    }
}

function displayFormMessage(message, type = 'error') {
    const messageId = type === 'success' ? 'success-message-withdrawal' : 'error-message-withdrawal';
    const messageDiv = document.getElementById(messageId);
    const otherMessageId = type === 'success' ? 'error-message-withdrawal' : 'success-message-withdrawal';
    const otherMessageDiv = document.getElementById(otherMessageId);

    if (messageDiv === null) return;

    messageDiv.style.display = 'none';

    if (otherMessageDiv) {
        otherMessageDiv.classList.remove('visible');
        otherMessageDiv.style.display = 'none';
    }

    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.style.display = 'block';
        messageDiv.setAttribute('role', 'alert');

        // Force reflow before adding visible class for smooth animation
        messageDiv.offsetHeight;
        messageDiv.className = `form-message alert alert-${type === 'success' ? 'success' : 'danger'} visible`;

        // Auto-hide after 6 seconds
        setTimeout(() => {
            messageDiv.classList.remove('visible');
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 500); // Wait for transition to complete
        }, 6000);
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

        // Add animation classes
        messageDiv.classList.add('visible');

        setTimeout(() => {
            messageDiv.classList.remove('visible');
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 500);
        }, 5000);
    }
}

// --- Card Functions ---
async function loadSavedCards() {
    const token = auth.getToken();
    if (!token) return;

    // Show loading state
    const selectEl = document.getElementById('select-payment-method');
    if (selectEl) {
        selectEl.innerHTML = '<option value="">Loading saved cards...</option>';
        selectEl.disabled = true;
    }

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
        populatePaymentMethodsDropdown([]); // Show empty state
    }
}

function populatePaymentMethodsDropdown(cards) {
    const selectEl = document.getElementById('select-payment-method');
    const cardIconEl = document.getElementById('selected-card-brand-icon');

    if (!selectEl || !cardIconEl) return;

    selectEl.innerHTML = '<option value="" disabled selected>Select a card</option>';
    selectEl.disabled = false;

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

// --- Manage Cards Modal ---
function populateManageCardsModal(cards) {
    const listContainer = document.getElementById('modal-saved-cards-list-container');
    const noCardsMsg = document.getElementById('no-saved-cards-message');

    if (!listContainer) return;

    listContainer.innerHTML = ''; // Clear previous items

    if (!cards || cards.length === 0) {
        if (noCardsMsg) noCardsMsg.style.display = 'block';
        return;
    }

    if (noCardsMsg) noCardsMsg.style.display = 'none';

    // Add with staggered animation
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
                ${card.is_default ?
            '<span class="default-badge">Default</span>' :
            `<button type="button" class="btn btn-sm btn-outline-secondary btn-set-default" data-card-id="${card.id}">Set Default</button>`}
                <button type="button" class="btn-remove-card" data-card-id="${card.id}" aria-label="Remove card">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;

        listContainer.appendChild(item);

        // Stagger the animations
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, 100 * index);
    });

    // Add event listeners for new buttons
    setTimeout(() => {
        listContainer.querySelectorAll('.btn-remove-card').forEach(btn =>
            btn.addEventListener('click', handleRemoveCard)
        );
        listContainer.querySelectorAll('.btn-set-default').forEach(btn =>
            btn.addEventListener('click', handleSetDefaultCard)
        );
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
    if (cardItem) {
        cardItem.classList.add('removing');
    }

    try {
        const response = await fetch(`${API_BASE}/cards/${cardId}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${token}`}
        });

        if (!response.ok) throw new Error('Failed to remove card.');

        displayModalMessage('Card removed successfully.', 'success');

        // Animate removal before actual removal
        if (cardItem) {
            cardItem.style.height = cardItem.offsetHeight + 'px';
            cardItem.style.opacity = '0';
            cardItem.style.transform = 'translateX(50px)';

            setTimeout(() => {
                cardItem.style.height = '0';
                cardItem.style.marginBottom = '0';
                cardItem.style.padding = '0';
                setTimeout(() => {
                    loadSavedCards(); // Refresh lists after animation
                }, 300);
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

    // Show loading state
    button.innerHTML = '<i class="bi bi-arrow-repeat"></i>';
    button.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/cards/${cardId}/set-default`, {
            method: 'POST',
            headers: {'Authorization': `Bearer ${token}`}
        });

        if (!response.ok) throw new Error('Failed to set default card.');

        displayModalMessage('Default card updated.', 'success');

        // Highlight the card with a success animation before refreshing
        const cardItem = button.closest('.saved-card-entry');
        if (cardItem) {
            cardItem.classList.add('highlight-success');
            setTimeout(() => {
                loadSavedCards(); // Refresh lists
            }, 700);
        } else {
            loadSavedCards();
        }

    } catch (error) {
        displayModalMessage(error.message || 'Could not set default card.', 'error');
        button.textContent = originalText;
        button.disabled = false;
    }
}

// --- Recent Withdrawals ---
async function loadRecentWithdrawals() {
    const listContainer = document.getElementById('initial-recent-withdrawals');
    const loadingDiv = document.getElementById('recent-withdrawals-loading');
    const viewMoreContainer = document.getElementById('view-more-withdrawals-btn-container');

    if (!listContainer || !loadingDiv) return;

    const token = auth.getToken();
    if (!token) return;

    // Show loading state
    loadingDiv.style.display = 'flex';
    listContainer.innerHTML = '';
    if (viewMoreContainer) viewMoreContainer.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/withdrawals?limit=16`, {
            headers: {'Authorization': `Bearer ${token}`}
        });

        if (!response.ok) throw new Error('Failed to fetch recent withdrawals.');

        const data = await response.json();
        const withdrawals = data.withdrawals || [];

        // Add a slight delay for a better loading feel
        setTimeout(() => {
            if (withdrawals.length === 0) {
                listContainer.innerHTML = '<p class="text-muted p-3 text-center">No recent withdrawals.</p>';
            } else {
                // Stagger the withdrawal items
                withdrawals.forEach((withdrawal, index) => {
                    const item = document.createElement('div');
                    item.className = 'withdrawal-list-item';
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(-20px)';

                    item.innerHTML = `
                        <span class="date">${new Date(withdrawal.created_at).toLocaleDateString()}</span>
                        <span class="card-details">Card **** ${withdrawal.card_last_four || 'N/A'}</span>
                        <span class="status">${withdrawal.status.charAt(0).toUpperCase() + withdrawal.status.slice(1)}</span>
                        <span class="amount text-danger">-$${parseFloat(withdrawal.amount).toFixed(2)}</span>
                        <span class="info-icon"><i class="bi bi-info-circle" data-withdrawal-id="${withdrawal.id}"></i></span>
                    `;

                    listContainer.appendChild(item);

                    // Stagger the entrance animations
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateX(0)';
                    }, 80 * index);
                });

                // Add listeners for withdrawal item clicks after all are loaded
                setTimeout(() => {
                    listContainer.querySelectorAll('.info-icon i').forEach(icon => {
                        icon.addEventListener('click', (e) => {
                            e.stopPropagation();
                            showWithdrawalDetailsModal(e.currentTarget.dataset.withdrawalId);
                        });
                    });

                    listContainer.querySelectorAll('.withdrawal-list-item').forEach(item => {
                        item.addEventListener('click', (e) => {
                            const withdrawalId = item.querySelector('.info-icon i')?.dataset.withdrawalId;
                            if (withdrawalId) {
                                item.style.transform = 'translateX(8px) scale(0.98)';
                                setTimeout(() => {
                                    item.style.transform = 'translateX(0)';
                                    showWithdrawalDetailsModal(withdrawalId);
                                }, 150);
                            }
                        });
                    });
                }, withdrawals.length * 80 + 100);

                // Show view more button if there are enough withdrawals
                if (viewMoreContainer && withdrawals.length >= 5) {
                    viewMoreContainer.style.opacity = '0';
                    viewMoreContainer.style.display = 'block';

                    setTimeout(() => {
                        viewMoreContainer.style.opacity = '1';
                    }, withdrawals.length * 80 + 200);
                }
            }

            loadingDiv.style.opacity = '0';
            setTimeout(() => {
                loadingDiv.style.display = 'none';
            }, 300);

        }, 600);

    } catch (error) {
        console.error('Error loading recent withdrawals:', error);
        listContainer.innerHTML = '<p class="text-danger p-3 text-center">Could not load recent withdrawals.</p>';
        loadingDiv.style.display = 'none';
    }
}

async function showWithdrawalDetailsModal(withdrawalId) {
    const token = auth.getToken();
    if (!token) return;

    // Create loading overlay in the modal
    const modal = document.getElementById('withdrawalDetailsModal');
    if (!modal) return;

    // Show modal immediately with loading state
    const detailsModal = new bootstrap.Modal(modal);
    detailsModal.show();

    // Add loading effect
    const modalBody = modal.querySelector('.modal-body');
    if (modalBody) {
        modalBody.innerHTML = `
            <div class="text-center p-5">
                <div class="loading-spinner">
                    <i class="bi bi-arrow-repeat"></i>
                </div>
                <p class="mt-3">Loading details...</p>
            </div>
        `;
    }

    try {
        const response = await fetch(`${API_BASE}/withdrawals/${withdrawalId}`, {
            headers: {'Authorization': `Bearer ${token}`}
        });

        if (!response.ok) {
            throw new Error('Failed to fetch withdrawal details.');
        }

        const withdrawal = await response.json();

        // Once data is loaded, populate modal with animation
        setTimeout(() => {
            if (modalBody) {
                modalBody.innerHTML = `
                    <div class="transaction-detail-item">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value" id="detail-modal-date">
                            ${withdrawal.created_at ? new Date(withdrawal.created_at).toLocaleString() : 'N/A'}
                        </span>
                    </div>
                    <div class="transaction-detail-item">
                        <span class="detail-label">Card:</span>
                        <span class="detail-value" id="detail-modal-card">
                            ${withdrawal.card_last_four ? `**** ${withdrawal.card_last_four}` : 'N/A'}
                        </span>
                    </div>
                    <div class="transaction-detail-item">
                        <span class="detail-label">Amount:</span>
                        <span class="detail-value" id="detail-modal-amount">
                            ${withdrawal.amount ? `-$${Math.abs(parseFloat(withdrawal.amount)).toFixed(2)}` : 'N/A'}
                        </span>
                    </div>
                    <div class="transaction-detail-item">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value" id="detail-modal-status">
                            ${withdrawal.status ? withdrawal.status.charAt(0).toUpperCase() + withdrawal.status.slice(1) : 'N/A'}
                        </span>
                    </div>
                    <div class="transaction-detail-item">
                        <span class="detail-label">Reference ID:</span>
                        <span class="detail-value" id="detail-modal-ref-id">
                            ${withdrawal.reference_id || 'N/A'}
                        </span>
                    </div>
                `;

                // Animate in the items
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
        console.error('Error fetching withdrawal details:', error);

        if (modalBody) {
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Could not load withdrawal details.
                </div>
            `;
        }
    }
}

// --- Form Submission ---
document.getElementById('withdrawal-form')?.addEventListener('submit', async (event) => {
    event.preventDefault();

    const token = auth.getToken();
    const userData = auth.getUserData();

    if (!API_BASE || !token) {
        console.error('API configuration missing:', {API_BASE, token});
        displayFormMessage('System configuration error. Please try again later.', 'error');
        return;
    }

    setLoadingState(true);
    clearFormMessage();

    // Validate amount with enhanced UI feedback
    const amountInput = document.getElementById('withdrawal-amount');
    if (!amountInput) {
        console.error('Withdrawal amount input not found');
        displayFormMessage('Form error: Amount field missing.', 'error');
        setLoadingState(false);
        return;
    }

    const amount = parseFloat(amountInput.value);
    if (isNaN(amount) || amount < 0.50) {
        displayFormMessage('Minimum withdrawal amount is $0.50.', 'error');

        // Highlight the amount input with error style
        amountInput.classList.add('is-invalid');
        setTimeout(() => {
            amountInput.classList.remove('is-invalid');
        }, 3000);

        setLoadingState(false);
        return;
    }

    // Convert userData.balance from cents to dollars for comparison
    const currentBalance = userData && userData.balance ? userData.balance / 100 : 0;
    if (amount > currentBalance) {
        displayFormMessage(`Insufficient balance. Your current balance is $${currentBalance.toFixed(2)}.`, 'error');

        amountInput.classList.add('is-invalid');
        setTimeout(() => {
            amountInput.classList.remove('is-invalid');
        }, 3000);

        setLoadingState(false);
        return;
    }

    // Show a subtle success animation on the amount
    amountInput.classList.add('is-valid');
    setTimeout(() => {
        amountInput.classList.remove('is-valid');
    }, 2000);

    // Get card selection
    const cardSelect = document.getElementById('select-payment-method');
    if (!cardSelect || !cardSelect.value) {
        displayFormMessage('Please select a card for withdrawal.', 'error');
        setLoadingState(false);
        return;
    }

    const cardId = cardSelect.value;

    try {
        // Submit withdrawal request
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
                description: "Withdrawal to card"
            })
        });

        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch {
                errorData = {detail: `HTTP ${response.status}: Failed to process withdrawal.`};
            }
            console.error('Withdrawal error:', errorData);
            throw new Error(errorData.detail || 'Failed to process withdrawal.');
        }

        const data = await response.json();

        // Success handling with animations
        const withdrawalForm = document.getElementById('withdrawal-form');
        if (withdrawalForm) {
            withdrawalForm.classList.add('success');
            setTimeout(() => {
                withdrawalForm.classList.remove('success');
            }, 2000);
        }

        displayFormMessage(`Withdrawal of $${amount.toFixed(2)} submitted successfully!`, 'success');

        if (withdrawalForm) withdrawalForm.reset();

        // Refresh data with smooth transitions
        setTimeout(() => {
            loadSavedCards();
            loadRecentWithdrawals();
            updateBalance();
            if (typeof refreshUserData === 'function') {
                refreshUserData();
            }
        }, 500);

    } catch (error) {
        console.error('Withdrawal Error:', error);
        displayFormMessage(error.message || 'An error occurred during withdrawal.', 'error');
    } finally {
        setLoadingState(false);
    }
});

// --- Enhanced UI Interactions ---
function setupEnhancedInteractions() {
    // Add input focus effects
    const formInputs = document.querySelectorAll('.form-control');
    formInputs.forEach(input => {
        input.addEventListener('focus', () => {
            const formGroup = input.closest('.form-group');
            if (formGroup) formGroup.classList.add('input-focused');
        });

        input.addEventListener('blur', () => {
            const formGroup = input.closest('.form-group');
            if (formGroup) formGroup.classList.remove('input-focused');
        });
    });

    // Add pulse animation to balance on hover
    const balanceDisplay = document.querySelector('.current-balance');
    if (balanceDisplay) {
        balanceDisplay.addEventListener('mouseenter', () => {
            const amount = balanceDisplay.querySelector('.balance-amount');
            if (amount) amount.classList.add('pulse-once');

            setTimeout(() => {
                if (amount) amount.classList.remove('pulse-once');
            }, 1000);
        });
    }

    // Make amount input more interactive
    const amountInput = document.getElementById('withdrawal-amount');
    if (amountInput) {
        amountInput.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            const amountHint = amountInput.parentElement.parentElement.querySelector('.amount-hint');
            const userData = auth.getUserData();
            const currentBalance = userData && userData.balance ? userData.balance / 100 : 0;

            if (value >= 0.5 && value <= Math.min(10000, currentBalance)) {
                amountInput.classList.remove('is-invalid');
                amountInput.classList.add('is-valid');

                if (amountHint) {
                    amountHint.classList.add('text-success');
                    amountHint.classList.remove('text-danger');
                }
            } else {
                amountInput.classList.add('is-invalid');
                amountInput.classList.remove('is-valid');

                if (amountHint) {
                    amountHint.classList.remove('text-success');
                    amountHint.classList.add('text-danger');

                    if (value > currentBalance) {
                        amountHint.textContent = `Insufficient balance. Available: $${currentBalance.toFixed(2)}`;
                    } else {
                        amountHint.textContent = 'Min: $0.50 / Max: $10,000.00 (or your available balance)';
                    }
                }
            }
        });

        // Reset validation state on blur
        amountInput.addEventListener('blur', () => {
            setTimeout(() => {
                amountInput.classList.remove('is-valid', 'is-invalid');

                const amountHint = amountInput.parentElement.parentElement.querySelector('.amount-hint');
                if (amountHint) {
                    amountHint.classList.remove('text-success', 'text-danger');
                    amountHint.textContent = 'Min: $0.50 / Max: $10,000.00 (or your available balance)';
                }
            }, 500);
        });
    }
}

// Function to set up quick amount buttons
function setupQuickAmountButtons() {
    const quickAmounts = document.querySelectorAll('.quick-amount');
    const amountInput = document.getElementById('withdrawal-amount');
    const userData = auth.getUserData();
    const currentBalance = userData && userData.balance ? userData.balance / 100 : 0;

    if (!quickAmounts.length || !amountInput) return;

    // Check against balance and disable buttons for amounts higher than balance
    quickAmounts.forEach(button => {
        const amount = parseFloat(button.dataset.amount);
        if (amount > currentBalance) {
            button.classList.add('disabled');
            button.setAttribute('title', 'Insufficient balance');
        } else {
            button.addEventListener('click', () => {
                // Remove selected class from all buttons
                quickAmounts.forEach(btn => btn.classList.remove('selected'));

                // Add selected class to clicked button
                button.classList.add('selected');

                // Update amount input
                amountInput.value = amount;

                // Trigger input event to validate the amount
                const event = new Event('input', {bubbles: true});
                amountInput.dispatchEvent(event);

                // Add animation effect
                button.classList.add('pulse');
                setTimeout(() => {
                    button.classList.remove('pulse');
                }, 500);
            });
        }
    });
}

// Fix issues with Bootstrap rows and columns
function fixLayoutIssues() {
    // Fix row layout issues
    const rows = document.querySelectorAll('.row');
    rows.forEach(row => {
        if (!row.style.margin) {
            row.style.margin = '0';
        }
    });

    // Ensure summary cards are displayed correctly
    const summaryCards = document.querySelectorAll('.summary-card');
    summaryCards.forEach(card => {
        card.style.height = '100%';
        card.style.minHeight = '180px';
    });

    // Fix withdrawal form card sizing
    const withdrawalFormCard = document.querySelector('.withdrawal-form-card');
    if (withdrawalFormCard) {
        withdrawalFormCard.style.minHeight = '400px';
    }

    // Make action cards equal width
    const actionCards = document.querySelectorAll('.action-card');
    if (actionCards.length) {
        const containerWidth = document.querySelector('.quick-actions-bar').clientWidth;
        const cardWidth = (containerWidth - (actionCards.length - 1) * 16) / actionCards.length;

        actionCards.forEach(card => {
            card.style.minWidth = '150px';
            card.style.flexBasis = `calc(${100 / actionCards.length}% - 16px)`;
        });
    }
}

// Function to update withdrawal statistics
async function updateWithdrawalStatistics() {
    const token = auth.getToken();
    if (!token) return;

    try {
        const response = await fetch(`${API_BASE}/withdrawals/stats`, {
            headers: {'Authorization': `Bearer ${token}`}
        });

        if (!response.ok) throw new Error('Failed to fetch withdrawal statistics');

        const data = await response.json();

        // Update monthly withdrawals value
        const monthlyWithdrawalsEl = document.getElementById('monthly-withdrawals-value');
        if (monthlyWithdrawalsEl && data.monthly_total) {
            animateBalanceChange(monthlyWithdrawalsEl, 0, data.monthly_total / 100);
        }

        // Update withdrawal frequency
        const frequencyEl = document.getElementById('withdrawal-frequency');
        if (frequencyEl && data.frequency) {
            frequencyEl.textContent = `${data.frequency} per month`;
        }

        // Update average withdrawal
        const avgWithdrawalEl = document.getElementById('average-withdrawal-value');
        if (avgWithdrawalEl && data.average_amount) {
            animateBalanceChange(avgWithdrawalEl, 0, data.average_amount / 100);
        }

        // Update total withdrawals count
        const totalCountEl = document.getElementById('total-withdrawals-count');
        if (totalCountEl && data.total_count) {
            totalCountEl.textContent = data.total_count;
        }

        // Update trend percentage
        const trendEl = document.getElementById('withdrawal-trend-percentage');
        if (trendEl && data.trend_percentage) {
            trendEl.textContent = `${data.trend_percentage}%`;
        }

        // Update last withdrawal date
        const lastDateEl = document.getElementById('last-withdrawal-date');
        if (lastDateEl && data.last_withdrawal_date) {
            lastDateEl.textContent = new Date(data.last_withdrawal_date).toLocaleDateString();
        }

    } catch (error) {
        console.error('Error fetching withdrawal statistics:', error);
        // Use placeholder values if API call fails

        // Set placeholder values with animation
        const placeholders = [
            {id: 'monthly-withdrawals-value', value: '$225.00'},
            {id: 'withdrawal-frequency', value: '1 per month'},
            {id: 'average-withdrawal-value', value: '$112.50'},
            {id: 'total-withdrawals-count', value: '4'},
            {id: 'withdrawal-trend-percentage', value: '10%'},
            {id: 'last-withdrawal-date', value: 'Last week'}
        ];

        placeholders.forEach(item => {
            const el = document.getElementById(item.id);
            if (el) {
                if (item.id.includes('value')) {
                    const numValue = parseFloat(item.value.replace('$', ''));
                    animateBalanceChange(el, 0, numValue);
                } else {
                    el.textContent = item.value;
                }
            }
        });
    }
}

// Enhanced initial setup
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Withdrawals page loaded - initializing with enhanced styling');

    // Apply page entrance animation
    document.querySelector('.withdrawal-page-container')?.classList.add('page-loaded');

    // Make sure the styling is correctly applied
    fixLayoutIssues();

    // Load saved cards and populate dropdowns
    await loadSavedCards();

    // Load recent withdrawals
    await loadRecentWithdrawals();

    // Setup UI interactions
    setupEnhancedInteractions();
    setupQuickAmountButtons();

    // Update withdrawal statistics
    updateWithdrawalStatistics();

    // Ensure balance updates on page load
    if (typeof refreshUserData === 'function') {
        await refreshUserData();
    }
    updateBalance();

    // Add event listener to open the manage cards modal
    document.querySelectorAll('#open-manage-cards-modal, #open-manage-cards-modal-btn').forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                const manageCardsModal = new bootstrap.Modal(document.getElementById('manageCardsModal'));
                populateManageCardsModal(currentSavedCards); // Ensure it's up-to-date
                manageCardsModal.show();
            });
        }
    });

    // Toggle for recent withdrawals with enhanced animation
    const withdrawalsToggle = document.getElementById('toggle-recent-withdrawals');
    const withdrawalsListContent = document.getElementById('recent-withdrawals-list-content');
    const withdrawalsArrow = withdrawalsToggle?.querySelector('.toggle-icon');

    if (withdrawalsToggle && withdrawalsListContent && withdrawalsArrow) {
        // Start with content visible
        withdrawalsListContent.classList.remove('collapsed');
        withdrawalsArrow.classList.add('up');
        withdrawalsToggle.setAttribute('aria-expanded', 'true');

        withdrawalsToggle.addEventListener('click', () => {
            const isExpanded = withdrawalsToggle.getAttribute('aria-expanded') === 'true';
            withdrawalsToggle.setAttribute('aria-expanded', (!isExpanded).toString());
            withdrawalsArrow.classList.toggle('up', !isExpanded);

            withdrawalsListContent.classList.toggle('collapsed', isExpanded);

            // Ensure smooth scroll behavior after animation
            if (!isExpanded) {
                withdrawalsListContent.style.overflow = 'hidden';
                setTimeout(() => {
                    withdrawalsListContent.style.overflow = 'visible';
                }, 400); // Match transition duration
            }
        });
    }

    // Update balance every 20 seconds
    setInterval(updateBalance, 20000);

    // Recheck layout after page fully loads
    setTimeout(fixLayoutIssues, 500);

    // Dispatch event that page is loaded
    document.dispatchEvent(new CustomEvent('pageContentLoaded'));
});

// Fix layout issues on window resize
window.addEventListener('resize', fixLayoutIssues);

// Add CSS class for animations to document
document.documentElement.classList.add('withdrawals-page-enhanced');

