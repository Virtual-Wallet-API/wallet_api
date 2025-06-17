document.addEventListener('DOMContentLoaded', () => {

    // DOM Elements
    const balanceAmount = document.getElementById('balance-amount');
    const balanceAmountLoading = document.getElementById('balance-amount-loading');
    const pendingToggle = document.getElementById('toggle-pending-transactions');
    const pendingContent = document.getElementById('pending-transactions-list-content');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');

    // Modals
    let transactionConfirmModal = null;
    let transactionDetailsModal = null;

    // Initialize Modals
    const confirmModalElement = document.getElementById('transactionConfirmModal');
    const detailsModalElement = document.getElementById('transactionDetailsModal');

    console.log('receive.js: Modal elements:', {
        confirmModalElement: !!confirmModalElement,
        detailsModalElement: !!detailsModalElement
    });

    if (!window.bootstrap || !window.bootstrap.Modal) {
        showError('Failed to initialize modals. Please refresh the page.');
        return;
    }

    if (confirmModalElement) {
        try {
            transactionConfirmModal = new bootstrap.Modal(confirmModalElement);
        } catch (error) {
            showError('Failed to initialize confirmation modal.');
        }
    } else {
        showError('Confirmation modal not found.');
    }

    if (detailsModalElement) {
        try {
            transactionDetailsModal = new bootstrap.Modal(detailsModalElement);
        } catch (error) {
            console.error('receive.js: Error initializing transactionDetailsModal:', error);
            showError('Failed to initialize details modal.');
        }
    } else {
        console.error('receive.js: transactionDetailsModal element not found.');
        showError('Details modal not found.');
    }

    // Exit if critical elements are missing
    if (!balanceAmount || !balanceAmountLoading || !pendingToggle || !pendingContent) {
        console.error('receive.js: Critical DOM elements missing.');
        showError('Page failed to load properly.');
        return;
    }

    // Initial Setup
    balanceAmount.style.opacity = '0';
    balanceAmountLoading.style.display = 'block';
    pendingContent.style.display = 'block';
    // pendingContent.style.maxHeight = `${pendingContent.scrollHeight}px`;
    pendingContent.style.opacity = '1';
    pendingToggle.setAttribute('aria-expanded', 'true');
    pendingToggle.querySelector('.toggle-icon').classList.replace('bi-chevron-down', 'bi-chevron-up');

    // Event Listeners
    pendingToggle.addEventListener('click', () => toggleSection(pendingToggle, pendingContent));
    if (transactionConfirmModal) {
        document.getElementById('confirm-transaction-btn')?.addEventListener('click', confirmTransaction);
        document.getElementById('decline-transaction-btn')?.addEventListener('click', declineTransaction);
    }

    // Load Data
    Promise.all([
        updateBalanceDisplay(),
        loadTransactions('pending'),
        loadSummaryData()
    ]).catch(error => {
        console.error('receive.js: Error loading initial data:', error);
        showError('Failed to load page data.');
    });

    // Functions
    async function updateBalanceDisplay() {
        try {
            const userData = await auth.getUserData();
            balanceAmountLoading.style.transition = 'opacity 0.3s ease';
            balanceAmountLoading.style.opacity = '0';
            setTimeout(() => {
                balanceAmountLoading.style.display = 'none';
                balanceAmount.textContent = `$${userData.balance.toFixed(2)}`;
                balanceAmount.style.opacity = '1';
                balanceAmount.classList.add('balance-updated');
                setTimeout(() => balanceAmount.classList.remove('balance-updated'), 500);
            }, 300);
        } catch (error) {
            console.error('receive.js: Error updating balance:', error);
            balanceAmount.textContent = 'Error';
            showError('Failed to load balance');
        }
    }

    async function loadTransactions(status) {
        const loadingElement = document.getElementById(`${status}-loading`);
        const container = document.getElementById(`initial-${status}`);
        const viewMoreContainer = document.getElementById(`view-more-${status}-btn-container`);

        if (!loadingElement || !container || !viewMoreContainer) {
            console.error('receive.js: Transaction list elements missing.');
            showError('Failed to load transactions.');
            return;
        }

        try {
            loadingElement.style.display = 'flex';
            const response = await fetch(`/api/v1/transactions?limit=100&status=awaiting_acceptance&direction=in`, {
                headers: {'Authorization': `Bearer ${auth.getToken()}`}
            });
            const data = await response.json();
            container.innerHTML = '';
            if (data.transactions && data.transactions.length > 0) {
                data.transactions.forEach(transaction => {
                    container.appendChild(createTransactionElement(transaction));
                });
                viewMoreContainer.style.display = data.has_more ? 'block' : 'none';
            } else {
                container.innerHTML = `<p class="text-muted text-center" id="no-${status}">No pending transactions</p>`;
            }
            document.getElementById('pending-transactions-count').textContent = data.transactions.length;
        } catch (error) {
            console.error(`receive.js: Error loading ${status} transactions:`, error);
            container.innerHTML = `<p class="text-danger text-center" id="error-${status}">Error loading transactions</p>`;
        } finally {
            loadingElement.style.display = 'none';
        }
    }

    async function loadSummaryData() {
        try {
            const dateTo = new Date().toISOString().split('T')[0];
            const dateFrom = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            const response = await fetch(`/api/v1/transactions/?date_from=${dateFrom}&date_to=${dateTo}&direction=in`, {
                headers: {'Authorization': `Bearer ${auth.getToken()}`}
            });
            const data = await response.json();
            document.getElementById('money-received-value').textContent = `$${data.incoming_total.toFixed(2)}`;
            document.getElementById('avg-transaction-value').textContent = `$${data.avg_incoming_transaction.toFixed(2)}`;
            document.getElementById('total-completed-count').textContent = data.total_completed;
        } catch (error) {
            console.error('receive.js: Error loading summary data:', error);
            showError('Failed to load summary data.');
        }
    }

    function createTransactionElement(transaction) {
        const div = document.createElement('div');
        div.className = 'transaction-item';
        div.dataset.id = transaction.id;
        div.innerHTML = `
            <span class="date">${new Date(transaction.date).toLocaleDateString()}</span>
            <span class="sender">${transaction.sender_id || 'Unknown'}</span>
            <span class="status">${transaction.status.replace('_', ' ')}</span>
            <span class="amount">$${transaction.amount.toFixed(2)}</span>
            <button class="btn btn-sm btn-primary btn-action btn-review" data-id="${transaction.id}">Review</button>
            <i class="bi bi-info-circle info-icon"></i>
        `;
        div.querySelector('.info-icon').addEventListener('click', () => showTransactionDetails(transaction));
        div.querySelector('.btn-review').addEventListener('click', () => prepareReviewTransaction(transaction));
        return div;
    }

    function toggleSection(toggle, content) {
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', !isExpanded);
        const icon = toggle.querySelector('.toggle-icon');
        if (!isExpanded) {
            content.style.display = 'block';
            content.style.transition = 'max-height 0.4s ease-in-out, opacity 0.4s ease-in-out';
            content.style.maxHeight = `${content.scrollHeight}px`;
            content.style.opacity = '1';
            icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
        } else {
            content.style.maxHeight = '0';
            content.style.opacity = '0';
            icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
            setTimeout(() => {
                content.style.display = 'none';
            }, 400);
        }
    }

    function prepareReviewTransaction(transaction) {
        console.log('receive.js: Preparing review transaction:', transaction.id);
        window.currentTransactionId = transaction.id;
        document.getElementById('modal-sender').textContent = transaction.sender_id || 'Unknown';
        document.getElementById('modal-amount').textContent = `$${transaction.amount.toFixed(2)}`;
        document.getElementById('modal-description').textContent = transaction.description || 'No description';
        if (transactionConfirmModal) {
            transactionConfirmModal.show();
        } else {
            console.error('receive.js: transactionConfirmModal not initialized');
            showError('Review modal unavailable.');
        }
    }

    async function confirmTransaction() {
        const transactionId = window.currentTransactionId;
        if (!transactionId) {
            console.error('receive.js: No transaction ID for confirm');
            return;
        }

        try {
            const response = await fetch(`/api/v1/transactions/status/${transactionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({ action: 'accept' })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to confirm transaction');

            if (transactionConfirmModal) transactionConfirmModal.hide();
            showSuccess('Transaction confirmed successfully');
            await Promise.all([loadTransactions('pending'), loadSummaryData()]);
            const transactionElement = document.querySelector(`#initial-pending .transaction-item[data-id="${transactionId}"]`);
            if (transactionElement) {
                transactionElement.style.opacity = '0';
                setTimeout(() => {
                    transactionElement.remove();
                    if (!document.querySelector('#initial-pending .transaction-item')) {
                        document.getElementById('initial-pending').innerHTML = '<p class="text-muted text-center" id="no-pending">No pending transactions</p>';
                        document.getElementById('pending-transactions-count').textContent = '0';
                    } else {
                        document.getElementById('pending-transactions-count').textContent = document.querySelectorAll('#initial-pending .transaction-item').length.toString();
                    }
                }, 300);
            }
            await auth.refreshOnEvent();
            await updateBalanceDisplay();
        } catch (error) {
            console.error('receive.js: Error confirming transaction:', error);
            showError(error.message);
        } finally {
            window.currentTransactionId = null;
        }
    }

    async function declineTransaction() {
        const transactionId = window.currentTransactionId;
        if (!transactionId) {
            console.error('receive.js: No transaction ID for decline');
            return;
        }

        try {
            const response = await fetch(`/api/v1/transactions/status/${transactionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({ action: 'decline' })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to decline transaction');

            if (transactionConfirmModal) transactionConfirmModal.hide();
            if (transactionDetailsModal) transactionDetailsModal.hide();
            showSuccess('Transaction declined successfully');
            await Promise.all([loadTransactions('pending'), loadSummaryData()]);
            const transactionElement = document.querySelector(`#initial-pending .transaction-item[data-id="${transactionId}"]`);
            if (transactionElement) {
                transactionElement.style.opacity = '0';
                setTimeout(() => {
                    transactionElement.remove();
                    if (!document.querySelector('#initial-pending .transaction-item')) {
                        document.getElementById('initial-pending').innerHTML = '<p class="text-muted text-center" id="no-pending">No pending transactions</p>';
                        document.getElementById('pending-transactions-count').textContent = '0';
                    } else {
                        document.getElementById('pending-transactions-count').textContent = document.querySelectorAll('#initial-pending .transaction-item').length.toString();
                    }
                }, 300);
            }
        } catch (error) {
            console.error('receive.js: Error declining transaction:', error);
            showError(error.message);
        } finally {
            window.currentTransactionId = null;
        }
    }

    function showTransactionDetails(transaction) {
        console.log('receive.js: Showing transaction details:', transaction.id);
        document.getElementById('detail-modal-date').textContent = new Date(transaction.date).toLocaleString();
        document.getElementById('detail-modal-sender').textContent = transaction.sender_id || 'Unknown';
        document.getElementById('detail-modal-amount').textContent = `$${transaction.amount.toFixed(2)}`;
        document.getElementById('detail-modal-description').textContent = transaction.description || 'No description';
        document.getElementById('detail-modal-status').textContent = transaction.status.replace('_', ' ');
        window.currentTransactionId = transaction.id;

        const declineButton = document.getElementById('decline-transaction-btn-details');
        declineButton.style.display = transaction.status === 'awaiting_acceptance' ? 'inline-block' : 'none';

        if (transactionDetailsModal) {
            transactionDetailsModal.show();
        } else {
            console.error('receive.js: transactionDetailsModal not initialized');
            showError('Details modal unavailable.');
        }
    }

    function showSuccess(message) {
        if (successMessage) {
            successMessage.textContent = message;
            successMessage.style.display = 'block';
            successMessage.classList.add('visible');
            setTimeout(() => {
                successMessage.classList.remove('visible');
                setTimeout(() => successMessage.style.display = 'none', 300);
            }, 10000);
        } else {
            console.warn('receive.js: successMessage element not found');
        }
    }

    function showError(message) {
        if (errorMessage) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
            errorMessage.classList.add('visible');
            setTimeout(() => {
                errorMessage.classList.remove('visible');
                setTimeout(() => errorMessage.style.display = 'none', 300);
            }, 10000);
        } else {
            console.warn('receive.js: errorMessage element not found');
        }
    }
});