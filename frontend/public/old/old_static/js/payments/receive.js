document.addEventListener('DOMContentLoaded', async function () {
    // Initialize variables
    const loadingElement = document.getElementById('awaiting-loading');
    const initialContainer = document.getElementById('initial-awaiting');
    const viewMoreContainer = document.getElementById('view-more-awaiting-btn-container');
    const transactionModal = new bootstrap.Modal(document.getElementById('transactionModal'));
    const acceptButton = document.getElementById('accept-transaction-btn');
    const declineButton = document.getElementById('decline-transaction-btn');

    // Event Listeners
    acceptButton.addEventListener('click', () => handleTransactionAction('accept'));
    declineButton.addEventListener('click', () => handleTransactionAction('decline'));

    async function loadTransactions() {
        try {
            let data = localStorage.getItem('incoming-transactions-cache');
            data = data ? JSON.parse(data) : null;
            if (!data || data.updated < new Date().getTime() - 1000 * 60 * 5) {
                loadingElement.style.display = 'block';
                const response = await fetch('/api/v1/transactions?status=awaiting_acceptance&direction=in', {
                    headers: {
                        'Authorization': `Bearer ${auth.getToken()}`
                    }
                });
                data = await response.json();
                data.updated = new Date().getTime();
                localStorage.setItem('incoming-transactions-cache', JSON.stringify(data));
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
                        No incoming transactions found
                    </div>
                `;
                viewMoreContainer.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading transactions:', error);
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
        document.getElementById('modal-sender').textContent = transaction.sender_id;
        document.getElementById('modal-amount').textContent = `$${transaction.amount.toFixed(2)}`;
        document.getElementById('modal-description').textContent = transaction.description || 'No description';
        document.getElementById('modal-status').textContent = transaction.status;

        // Store transaction ID for actions
        window.currentTransactionId = transaction.id;

        transactionModal.show();
    }

    async function handleTransactionAction(action) {
        if (!window.currentTransactionId) return;

        try {
            const response = await fetch(`/api/v1/transactions/status/${window.currentTransactionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({ action: action })
            });

            if (response.ok) {
                transactionModal.hide();
                localStorage.removeItem('incoming-transactions-cache');
                await auth.refreshUserData();
                loadTransactions();
            } else {
                const data = await response.json();
                showError(data.detail || `Failed to ${action} transaction`);
            }
        } catch (error) {
            showError(`An error occurred while ${action}ing the transaction`);
            console.error('Error:', error);
        } finally {
            window.currentTransactionId = null;
        }
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        errorDiv.style.position = 'fixed';
        errorDiv.style.top = '20px';
        errorDiv.style.left = '50%';
        errorDiv.style.transform = 'translateX(-50%)';
        errorDiv.style.zIndex = '9999';
        document.body.appendChild(errorDiv);

        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    // Load initial transactions
    await loadTransactions();
    document.dispatchEvent(new Event('pageContentLoaded'));
});


