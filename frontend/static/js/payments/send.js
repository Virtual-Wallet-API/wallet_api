document.addEventListener('DOMContentLoaded', async function () {
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

    // Wait for userData to be available
    if (!window.userData || !window.userData.balance) {
        await auth.refreshUserData();
    }

    let originalPendingContentHeight;
    let originalAwaitingContentHeight;

    pendingContent.style.opacity = '0';
    awaitingContent.style.opacity = '0';

    Promise.all([
        loadCategories(),
        loadTransactions('pending'),
        loadTransactions('awaiting'),
        updateBalanceDisplay()
    ]).then(() => {
        document.dispatchEvent(new Event('pageContentLoaded'));
        updateTransactionsHeight();
        pendingContent.style.maxHeight = '0';
        awaitingContent.style.maxHeight = '0';
    })

    // Event Listeners
    sendForm.addEventListener('submit', handleFormSubmit);
    recurringCheckbox.addEventListener('change', toggleIntervalGroup);
    toggleIntervalGroup();
    pendingToggle.addEventListener('click', () => toggleSection(pendingToggle, pendingContent));
    awaitingToggle.addEventListener('click', () => toggleSection(awaitingToggle, awaitingContent));
    document.getElementById('confirm-transaction-btn').addEventListener('click', confirmTransaction);


    function updateTransactionsHeight() {
        originalPendingContentHeight = pendingContent.scrollHeight * 1.4;
        pendingContent.setAttribute("originalHeight", originalPendingContentHeight)
        pendingContent.style.maxHeight = originalPendingContentHeight + 'px';

        originalAwaitingContentHeight = awaitingContent.scrollHeight * 1.4;
        awaitingContent.setAttribute("originalHeight", originalAwaitingContentHeight)
        awaitingContent.style.maxHeight = originalAwaitingContentHeight + 'px';
    }

    // Functions
    async function updateBalanceDisplay() {
        if (!userData || !userData.balance) {
            await auth.refreshUserData();
        }
        balanceText.style.opacity = '1';
        balanceAmount.textContent = `$${userData.balance.toFixed(2)}`;
        balanceAmount.style.opacity = '1'
        balanceAmountLoading.style.opacity = '0';
        return true;
    }

    async function loadCategories() {
        try {
            const response = await fetch('/api/v1/categories', {
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`
                }
            });
            const data = await response.json();

            if (data.categories && data.categories.length > 0) {
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    categorySelect.appendChild(option);
                });
            } else {
                categorySelect.disabled = true;
                categorySelect.innerHTML = '<option value="" selected>You have no categories</option>';
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            categorySelect.disabled = true;
            categorySelect.innerHTML = '<option value="" selected>Error loading categories</option>';
        }
    }

    async function loadTransactions(status) {
        const loadingElement = document.getElementById(`${status === 'pending' ? 'pending' : 'awaiting'}-loading`);
        const initialContainer = document.getElementById(`initial-${status === 'pending' ? 'pending' : 'awaiting'}`);
        const viewMoreContainer = document.getElementById(`view-more-${status === 'pending' ? 'pending' : 'awaiting'}-btn-container`);
        let api_status = status === "awaiting" ? "awaiting_acceptance" : "pending"

        try {
            let data = localStorage.getItem(`${status}-transactions-cache`);
            data = data ? JSON.parse(data) : null;
            if (!data || data.updated < new Date().getTime() - 1000 * 60 * 5) {
                loadingElement.style.display = 'block';
                const response = await fetch(`/api/v1/transactions?limit=100&status=${api_status}`, {
                    headers: {
                        'Authorization': `Bearer ${auth.getToken()}`
                    }
                });
                data = await response.json();
                data.updated = new Date().getTime();
                localStorage.setItem(`${status}-transactions-cache`, JSON.stringify(data));
            }

            if (data.transactions && data.transactions.length > 0) {
                initialContainer.innerHTML = '';
                data.transactions.forEach(transaction => {
                    const transactionElement = createTransactionElement(transaction);
                    initialContainer.appendChild(transactionElement);
                });

                viewMoreContainer.style.display = data.has_more ? 'block' : 'none';
            } else {
                initialContainer.innerHTML = `
                    <div class="no-transactions-alert">
                        No ${status === 'pending' ? 'pending' : 'awaiting acceptance'} transactions found
                    </div>
                `;
                viewMoreContainer.style.display = 'none';
            }
            updateTransactionsHeight();
        } catch (error) {
            console.error(`Error loading ${status} transactions:`, error);
            initialContainer.innerHTML = `
                <div class="alert alert-danger">
                    Error loading transactions. Please try again later.
                </div>
            `;
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

        // Store transaction ID for cancellation
        window.currentTransactionId = transaction.id;

        // Show cancel button if transaction is pending
        const cancelButton = document.getElementById('cancel-transaction-btn');
        if (!cancelButton) {
            const footer = document.querySelector('#transactionModal .modal-footer');
            const newCancelButton = document.createElement('button');
            newCancelButton.id = 'cancel-transaction-btn';
            newCancelButton.className = 'btn btn-danger';
            newCancelButton.textContent = 'Cancel Transaction';
            newCancelButton.addEventListener('click', cancelTransaction);
            footer.insertBefore(newCancelButton, footer.firstChild);
        } else {
            cancelButton.style.display = 'inline-block';
        }

        transactionModal.show();
    }

    async function cancelTransaction() {
        if (!window.currentTransactionId) return;

        try {
            const response = await fetch(`/api/v1/transactions/status/${window.currentTransactionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({action: 'cancel'})
            });

            if (response.ok) {
                transactionModal.hide();
                showSuccess('Transaction cancelled successfully');
                localStorage.removeItem(`pending-transactions-cache`);
                localStorage.removeItem(`awaiting-transactions-cache`);
                loadTransactions('pending');
                loadTransactions('awaiting');
                await auth.refreshUserData();
                await updateBalanceDisplay();
            } else {
                const data = await response.json();
                showError(data.detail || 'Failed to cancel transaction');
            }
        } catch (error) {
            showError('An error occurred while cancelling the transaction');
            console.error('Error:', error);
        } finally {
            window.currentTransactionId = null;
        }
    }

    function toggleIntervalGroup() {
        if (recurringCheckbox.checked) {
            intervalGroup.style.maxHeight = intervalGroup.scrollHeight + 'px';
            intervalGroup.style.opacity = '1';
        } else {
            intervalGroup.style.maxHeight = '0';
            intervalGroup.style.opacity = '0';
        }
    }

    function toggleSection(toggle, content) {
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', !isExpanded);

        if (!isExpanded) {
            content.style.display = 'block';
            // Force a reflow
            content.offsetHeight;
            content.style.maxHeight = content.getAttribute("originalHeight") + 'px';
            content.style.opacity = '1';
            content.classList.add('show');
        } else {
            content.style.maxHeight = '0';
            content.style.opacity = '0';
            content.classList.remove('show');
            setTimeout(() => {
                // content.style.display = 'none';
            }, 300);
        }

        toggle.querySelector('i').className = isExpanded ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
    }

    async function handleFormSubmit(e) {
        e.preventDefault();

        // Clear any existing messages
        successMessage.style.display = 'none';
        successMessage.classList.remove('visible');
        errorMessage.style.display = 'none';
        errorMessage.classList.remove('visible');

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
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify(transactionData)
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.removeItem(`pending-transactions-cache`);
                loadTransactions('pending');
                // Show confirmation modal
                document.getElementById('modal-receiver').textContent = receiverInput.value;
                document.getElementById('modal-amount').textContent = `$${amount.toFixed(2)}`;
                document.getElementById('modal-description').textContent = descriptionInput.value || 'No description';
                transactionConfirmModal.show();

                // Store transaction ID for confirmation
                window.pendingTransactionId = data.id;

                // Reset form
                sendForm.reset();
                intervalGroup.style.maxHeight = '0';
                intervalGroup.style.opacity = '0';
            } else {
                showError(data.detail || 'Failed to create transaction');
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
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({action: 'confirm'})
            });

            if (response.ok) {
                localStorage.removeItem(`pending-transactions-cache`);
                localStorage.removeItem(`awaiting-transactions-cache`);
                transactionConfirmModal.hide();
                showSuccess('Transaction confirmed successfully');
                await auth.refreshUserData();
                loadTransactions('pending');
                loadTransactions('awaiting');
                await updateBalanceDisplay();
            } else {
                const data = await response.json();
                showError(data.detail || 'Failed to confirm transaction');
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
        errorMessage.classList.add('visible');
        successMessage.style.display = 'none';
        successMessage.classList.remove('visible');
        setTimeout(() => {
            errorMessage.classList.remove('visible');
            setTimeout(() => {
                errorMessage.style.display = 'none';
            }, 300);
        }, 5000);
    }

    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        successMessage.classList.add('visible');
        errorMessage.style.display = 'none';
        errorMessage.classList.remove('visible');
        setTimeout(() => {
            successMessage.classList.remove('visible');
            setTimeout(() => {
                successMessage.style.display = 'none';
            }, 300);
        }, 5000);
    }
}); 