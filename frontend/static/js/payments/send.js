document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    const sendForm = document.getElementById('send-form');
    const receiverInput = document.getElementById('receiver-identifier');
    const amountInput = document.getElementById('send-amount');
    const descriptionInput = document.getElementById('description');
    const categorySelect = document.getElementById('category-select');
    const recurringCheckbox = document.getElementById('recurring-checkbox');
    const intervalGroup = document.getElementById('interval-group');
    const intervalSelect = document.getElementById('interval-select');
    const submitButton = document.getElementById('submit-button');
    const buttonText = document.getElementById('button-text');
    const spinner = document.getElementById('spinner');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    const balanceDisplay = document.getElementById('balance-display');
    const balanceText = document.getElementById('balance-text');
    const balanceAmount = document.getElementById('balance-amount');
    const balanceAmountLoading = document.getElementById('balance-amount-loading');

    // Initialize modals
    const transactionConfirmModal = new bootstrap.Modal(document.getElementById('transactionConfirmModal'));
    const transactionModal = new bootstrap.Modal(document.getElementById('transactionModal'));

    // Initialize section toggles
    const pendingToggle = document.getElementById('pending-toggle');
    const pendingContent = document.getElementById('pending-transactions-list-content');
    const awaitingToggle = document.getElementById('awaiting-toggle');
    const awaitingContent = document.getElementById('awaiting-transactions-list-content');

    // Check for receiver query parameter
    const urlParams = new URLSearchParams(window.location.search);
    const receiverParam = urlParams.get('receiver');
    if (receiverParam) {
        receiverInput.value = receiverParam;
    }

    // Load categories
    loadCategories();

    // Load initial transactions
    loadTransactions('pending');
    loadTransactions('awaiting_acceptance');

    // Update balance display
    updateBalanceDisplay();

    // Event Listeners
    sendForm.addEventListener('submit', handleFormSubmit);
    recurringCheckbox.addEventListener('change', toggleIntervalGroup);
    pendingToggle.addEventListener('click', () => toggleSection(pendingToggle, pendingContent));
    awaitingToggle.addEventListener('click', () => toggleSection(awaitingToggle, awaitingContent));
    document.getElementById('confirm-transaction-btn').addEventListener('click', confirmTransaction);

    // Functions
    function updateBalanceDisplay() {
        balanceText.style.opacity = '1';
        balanceAmount.textContent = `$${userData.balance.toFixed(2)}`;
        balanceAmount.style.opacity = '1';
    }

    async function loadCategories() {
        try {
            const response = await fetch('/api/v1/categories');
            const data = await response.json();
            
            if (data.categories) {
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    categorySelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async function loadTransactions(status) {
        const loadingElement = document.getElementById(`${status === 'pending' ? 'pending' : 'awaiting'}-loading`);
        const initialContainer = document.getElementById(`initial-${status === 'pending' ? 'pending' : 'awaiting'}`);
        const viewMoreContainer = document.getElementById(`view-more-${status === 'pending' ? 'pending' : 'awaiting'}-btn-container`);

        try {
            loadingElement.style.display = 'block';
            const response = await fetch(`/api/v1/transactions?limit=100&status=${status}`);
            const data = await response.json();

            if (data.transactions) {
                initialContainer.innerHTML = '';
                data.transactions.forEach(transaction => {
                    const transactionElement = createTransactionElement(transaction);
                    initialContainer.appendChild(transactionElement);
                });

                viewMoreContainer.style.display = data.has_more ? 'block' : 'none';
            }
        } catch (error) {
            console.error(`Error loading ${status} transactions:`, error);
        } finally {
            loadingElement.style.display = 'none';
        }
    }

    function createTransactionElement(transaction) {
        const div = document.createElement('div');
        div.className = 'transaction-item';
        div.innerHTML = `
            <div class="transaction-info">
                <span class="transaction-amount">$${transaction.amount.toFixed(2)}</span>
                <span class="transaction-description">${transaction.description || 'No description'}</span>
            </div>
            <div class="transaction-date">${new Date(transaction.date).toLocaleDateString()}</div>
        `;
        div.addEventListener('click', () => showTransactionDetails(transaction));
        return div;
    }

    function showTransactionDetails(transaction) {
        document.getElementById('modal-date').textContent = new Date(transaction.date).toLocaleString();
        document.getElementById('modal-receiver').textContent = transaction.receiver_id;
        document.getElementById('modal-amount').textContent = `$${transaction.amount.toFixed(2)}`;
        document.getElementById('modal-description').textContent = transaction.description || 'No description';
        document.getElementById('modal-status').textContent = transaction.status;
        transactionModal.show();
    }

    function toggleIntervalGroup() {
        if (recurringCheckbox.checked) {
            intervalGroup.style.display = 'block';
        } else {
            intervalGroup.style.display = 'none';
        }
    }

    function toggleSection(toggle, content) {
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', !isExpanded);
        content.style.maxHeight = isExpanded ? '0' : content.scrollHeight + 'px';
        content.style.opacity = isExpanded ? '0' : '1';
        toggle.querySelector('i').className = isExpanded ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
    }

    async function handleFormSubmit(e) {
        e.preventDefault();
        
        // Validate amount
        const amount = parseFloat(amountInput.value);
        if (amount > userData.balance) {
            showError('Amount exceeds available balance');
            return;
        }
        if (amount < 0.01) {
            showError('Amount must be at least $0.01');
            return;
        }

        // Prepare transaction data
        const transactionData = {
            identifier: receiverInput.value,
            amount: amount,
            description: descriptionInput.value,
            category_id: categorySelect.value || null,
            recurring: recurringCheckbox.checked,
            interval: recurringCheckbox.checked ? parseInt(intervalSelect.value) : null
        };

        try {
            // Show loading state
            setLoading(true);

            // Create transaction
            const response = await fetch('/api/v1/transactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(transactionData)
            });

            const data = await response.json();

            if (response.ok) {
                // Show confirmation modal
                document.getElementById('modal-receiver').textContent = receiverInput.value;
                document.getElementById('modal-amount').textContent = `$${amount.toFixed(2)}`;
                document.getElementById('modal-description').textContent = descriptionInput.value || 'No description';
                transactionConfirmModal.show();

                // Store transaction ID for confirmation
                window.pendingTransactionId = data.id;

                // Reset form
                sendForm.reset();
                intervalGroup.style.display = 'none';
            } else {
                showError(data.message || 'Failed to create transaction');
            }
        } catch (error) {
            showError('An error occurred while creating the transaction');
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    }

    async function confirmTransaction() {
        if (!window.pendingTransactionId) return;

        try {
            setLoading(true);

            const response = await fetch(`/api/v1/transactions/status/${window.pendingTransactionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: 'confirm' })
            });

            if (response.ok) {
                transactionConfirmModal.hide();
                showSuccess('Transaction confirmed successfully');
                loadTransactions('pending');
                loadTransactions('awaiting_acceptance');
                updateBalanceDisplay();
            } else {
                const data = await response.json();
                showError(data.message || 'Failed to confirm transaction');
            }
        } catch (error) {
            showError('An error occurred while confirming the transaction');
            console.error('Error:', error);
        } finally {
            setLoading(false);
            window.pendingTransactionId = null;
        }
    }

    function setLoading(isLoading) {
        submitButton.disabled = isLoading;
        buttonText.style.display = isLoading ? 'none' : 'inline';
        spinner.style.display = isLoading ? 'inline' : 'none';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        successMessage.style.display = 'none';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }

    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        errorMessage.style.display = 'none';
        setTimeout(() => {
            successMessage.style.display = 'none';
        }, 5000);
    }
}); 