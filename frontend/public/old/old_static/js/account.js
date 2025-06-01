// Helper to format currency consistently
function formatCurrency(amount) {
    const absAmount = Math.abs(parseFloat(amount) || 0);
    return absAmount.toLocaleString('en-US', {style: 'currency', currency: 'USD'});
}

// Transaction Modal
function attachItemEntryListeners() {
    document.querySelectorAll('.item-entry').forEach(item => {
        item.addEventListener('click', function () {
            const dataset = this.dataset;
            document.getElementById('modal-date').textContent = dataset.date || 'N/A';
            document.getElementById('modal-description').textContent = dataset.description || 'N/A';

            const amount = parseFloat(dataset.amount);
            const amountFormatted = formatCurrency(amount);
            document.getElementById('modal-amount').textContent = (amount < 0 ? '-' : '+') + amountFormatted;
            document.getElementById('modal-amount').className = amount < 0 ? 'text-danger' : 'text-success';

            document.getElementById('modal-category').textContent = dataset.category || 'N/A';
            document.getElementById('modal-status').textContent = dataset.status || 'N/A'; // For deposits or detailed transactions
            document.getElementById('modal-ref-id').textContent = dataset.transactionId || dataset.depositId || 'N/A';

            var transactionModal = new bootstrap.Modal(document.getElementById('transactionModal'));
            transactionModal.show();
        });
    });
}

// Generic "View More" Toggle
function toggleMoreItems(listId, buttonId, seeAllUrl) {
    const additionalList = document.getElementById(listId);
    const viewBtn = document.getElementById(buttonId);
    const isShown = additionalList.style.maxHeight !== '0px';

    if (isShown) { // If shown, and clicked, means "See All"
        window.location.href = seeAllUrl;
    } else { // If hidden, show more
        additionalList.style.maxHeight = additionalList.scrollHeight + 'px';
        additionalList.style.opacity = '1';
        viewBtn.textContent = 'See All';
    }
}

// Generic function to render items
function renderItems(items, initialListEl, additionalListEl, viewBtnContainerEl, viewBtnEl, itemType, noItemsMessage, seeAllUrl) {
    initialListEl.innerHTML = '';
    additionalListEl.innerHTML = '';

    if (!items || items.length === 0) {
        initialListEl.innerHTML = `<div class='alert alert-info mx-3'>${noItemsMessage}</div>`;
        viewBtnContainerEl.style.display = 'none';
        return;
    }

    const itemEntries = items.map(item => {
        let date, descriptionText, amountStr, amountFloat, amountClass, statusText, categoryText, refId;

        if (itemType === 'transaction') {
            date = new Date(item.date).toLocaleDateString();
            descriptionText = item.description || `Transaction ${item.id}`; // Fallback description
            statusText = item.status;
            categoryText = item.category || 'General';
            refId = item.id;
            if (item.sender_id === userData.id) { // Assuming userData.id is available
                amountFloat = -(parseFloat(item.amount) || 0);
                amountClass = 'negative';
            } else {
                amountFloat = parseFloat(item.amount) || 0;
                amountClass = 'positive';
            }
            amountStr = (amountFloat < 0 ? '-' : '+') + formatCurrency(amountFloat);
        } else { // deposit
            date = new Date(item.created_at).toLocaleDateString();
            descriptionText = `Deposit via ${item.method}`;
            statusText = item.status.charAt(0).toUpperCase() + item.status.slice(1);
            categoryText = 'Deposit';
            refId = item.id;
            amountFloat = parseFloat(item.amount) || 0;
            amountStr = '+' + formatCurrency(amountFloat);
            amountClass = 'positive';
        }

        return `
                <div class="item-entry"
                     data-transaction-id="${itemType === 'transaction' ? refId : ''}"
                     data-deposit-id="${itemType === 'deposit' ? refId : ''}"
                     data-date="${date}"
                     data-description="${descriptionText}"
                     data-amount="${amountFloat.toFixed(2)}"
                     data-category="${categoryText}"
                     data-status="${statusText}">
                    <span class="date">${date}</span>
                    <span class="description">${descriptionText}</span>
                    <span class="amount ${amountClass}">${amountStr}</span>
                    <span class="info-icon"><i class="bi bi-info-circle"></i></span>
                </div>`;
    }).join('');

    if (items.length <= 3) {
        initialListEl.innerHTML = itemEntries;
        viewBtnContainerEl.style.display = 'none';
    } else {
        initialListEl.innerHTML = items.slice(0, 3).map(item => { /* Regenerate HTML for first 3 */
            let date, descriptionText, amountStr, amountFloat, amountClass, statusText, categoryText, refId;
            if (itemType === 'transaction') {
                date = new Date(item.date).toLocaleDateString();
                descriptionText = item.description || `Transaction ${item.id}`;
                statusText = item.status;
                categoryText = item.category || 'General';
                refId = item.id;
                if (item.sender_id === userData.id) {
                    amountFloat = -(parseFloat(item.amount) || 0);
                    amountClass = 'negative';
                } else {
                    amountFloat = parseFloat(item.amount) || 0;
                    amountClass = 'positive';
                }
                amountStr = (amountFloat < 0 ? '-' : '+') + formatCurrency(amountFloat);
            } else {
                date = new Date(item.created_at).toLocaleDateString();
                descriptionText = `Deposit via ${item.method}`;
                statusText = item.status.charAt(0).toUpperCase() + item.status.slice(1);
                categoryText = 'Deposit';
                refId = item.id;
                amountFloat = parseFloat(item.amount) || 0;
                amountStr = '+' + formatCurrency(amountFloat);
                amountClass = 'positive';
            }
            return `
                <div class="item-entry"
                     data-transaction-id="${itemType === 'transaction' ? refId : ''}" data-deposit-id="${itemType === 'deposit' ? refId : ''}"
                     data-date="${date}" data-description="${descriptionText}" data-amount="${amountFloat.toFixed(2)}" data-category="${categoryText}" data-status="${statusText}">
                    <span class="date">${date}</span> <span class="description">${descriptionText}</span> <span class="amount ${amountClass}">${amountStr}</span> <span class="info-icon"><i class="bi bi-info-circle"></i></span>
                </div>`;
        }).join('');

        additionalListEl.innerHTML = items.slice(3).map(item => { /* Regenerate HTML for rest */
            let date, descriptionText, amountStr, amountFloat, amountClass, statusText, categoryText, refId;
            if (itemType === 'transaction') {
                date = new Date(item.date).toLocaleDateString();
                descriptionText = item.description || `Transaction ${item.id}`;
                statusText = item.status;
                categoryText = item.category || 'General';
                refId = item.id;
                if (item.sender_id === userData.id) {
                    amountFloat = -(parseFloat(item.amount) || 0);
                    amountClass = 'negative';
                } else {
                    amountFloat = parseFloat(item.amount) || 0;
                    amountClass = 'positive';
                }
                amountStr = (amountFloat < 0 ? '-' : '+') + formatCurrency(amountFloat);
            } else {
                date = new Date(item.created_at).toLocaleDateString();
                descriptionText = `Deposit via ${item.method}`;
                statusText = item.status.charAt(0).toUpperCase() + item.status.slice(1);
                categoryText = 'Deposit';
                refId = item.id;
                amountFloat = parseFloat(item.amount) || 0;
                amountStr = '+' + formatCurrency(amountFloat);
                amountClass = 'positive';
            }
            return `
                <div class="item-entry"
                     data-transaction-id="${itemType === 'transaction' ? refId : ''}" data-deposit-id="${itemType === 'deposit' ? refId : ''}"
                     data-date="${date}" data-description="${descriptionText}" data-amount="${amountFloat.toFixed(2)}" data-category="${categoryText}" data-status="${statusText}">
                    <span class="date">${date}</span> <span class="description">${descriptionText}</span> <span class="amount ${amountClass}">${amountStr}</span> <span class="info-icon"><i class="bi bi-info-circle"></i></span>
                </div>`;
        }).join('');

        additionalListEl.style.maxHeight = '0px'; // Ensure it's collapsed initially
        additionalListEl.style.opacity = '0';
        viewBtnEl.textContent = 'View More';
        viewBtnContainerEl.style.display = 'block';

        // Remove old listener before adding new one to prevent multiple bindings
        const newViewBtnEl = viewBtnEl.cloneNode(true);
        viewBtnEl.parentNode.replaceChild(newViewBtnEl, viewBtnEl);

        newViewBtnEl.addEventListener('click', function (e) {
            e.preventDefault();
            toggleMoreItems(additionalListEl.id, newViewBtnEl.id, seeAllUrl);
        });
    }
    attachItemEntryListeners();
}


async function fetchTransactions() {
    const loadingAlert = document.getElementById('transactions-loading-alert');
    try {
        loadingAlert.classList.remove('hidden');
        const response = await fetch(`${API_BASE}/transactions`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error(`Failed to fetch transactions: ${response.status}`);

        const data = await response.json();
        const transactions = data.transactions.sort((a, b) => new Date(b.date) - new Date(a.date));

        renderItems(
            transactions.slice(0, 12), // Show up to 12, JS handles 3 + more
            document.getElementById('initial-transactions-list'),
            document.getElementById('additional-transactions-list'),
            document.getElementById('view-transactions-btn-container'),
            document.getElementById('view-transactions-btn'),
            'transaction',
            'No transactions yet.',
            '/fe/transactions' // URL for "See All"
        );
    } catch (error) {
        console.error('Error fetching transactions:', error);
        document.getElementById('initial-transactions-list').innerHTML = "<div class='alert alert-danger mx-3'>Could not load transactions.</div>";
    } finally {
        loadingAlert.classList.add('hidden');
    }
}

async function fetchDeposits() {
    const loadingAlert = document.getElementById('deposits-loading-alert');
    try {
        loadingAlert.classList.remove('hidden');
        const response = await fetch(`${API_BASE}/deposits`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error(`Failed to fetch deposits: ${response.status}`);

        const data = await response.json();
        const deposits = data.deposits.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        renderItems(
            deposits.slice(0, 12), // Show up to 12
            document.getElementById('initial-deposits-list'),
            document.getElementById('additional-deposits-list'),
            document.getElementById('view-deposits-btn-container'),
            document.getElementById('view-deposits-btn'),
            'deposit',
            'No deposits yet.',
            '/fe/all-deposits' // URL for "See All"
        );
    } catch (error) {
        console.error('Error fetching deposits:', error);
        document.getElementById('initial-deposits-list').innerHTML = "<div class='alert alert-danger mx-3'>Could not load deposits.</div>";
    } finally {
        loadingAlert.classList.add('hidden');
    }
}

// Generic Toggle Function for Sections
function setupSectionToggle(toggleId, listId) {
    const toggleElement = document.getElementById(toggleId);
    const listElement = document.getElementById(listId);
    const arrowIcon = toggleElement.querySelector('i.bi-chevron-down');

    // Initialize based on 'show' class (which means expanded)
    const isInitiallyShown = listElement.classList.contains('show');
    toggleElement.setAttribute('aria-expanded', isInitiallyShown.toString());
    if (!isInitiallyShown) { // If not shown, ensure it's collapsed and arrow is up
        listElement.style.maxHeight = '0px';
        listElement.style.opacity = '0';
        arrowIcon.classList.remove('up'); // Ensure arrow points down if collapsed
    } else {
        arrowIcon.classList.add('up'); // Ensure arrow points up if expanded
        listElement.style.maxHeight = listElement.scrollHeight + 'px'; // Set initial max-height if shown
    }


    toggleElement.addEventListener('click', () => {
        const isCurrentlyShown = listElement.classList.toggle('show');
        toggleElement.setAttribute('aria-expanded', isCurrentlyShown.toString());
        arrowIcon.classList.toggle('up', isCurrentlyShown);

        if (isCurrentlyShown) {
            listElement.style.maxHeight = listElement.scrollHeight + 'px';
            listElement.style.opacity = '1';
            // After transition, set to auto or large value if content might change
            setTimeout(() => {
                if (listElement.classList.contains('show')) listElement.style.maxHeight = '2500px';
            }, 500); // Match CSS transition
        } else {
            // Temporarily set max-height to current scroll height to animate from there
            listElement.style.maxHeight = listElement.scrollHeight + 'px';
            // Force reflow
            listElement.offsetHeight;
            listElement.style.maxHeight = '0px';
            listElement.style.opacity = '0';
        }
    });

    // Keyboard accessibility
    toggleElement.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleElement.click();
        }
    });

    // Observe changes in list content to readjust max-height if shown
    const observer = new MutationObserver(() => {
        if (listElement.classList.contains('show')) {
            listElement.style.maxHeight = listElement.scrollHeight + 'px';
            setTimeout(() => { // Reset to allow further expansion if needed
                if (listElement.classList.contains('show')) listElement.style.maxHeight = '2500px';
            }, 500);
        }
    });
    observer.observe(listElement, {childList: true, subtree: true});
}


document.addEventListener("DOMContentLoaded", async function () {
    await initializeBaseScripts();

    try {
        const balanceAmountEl = document.getElementById('balance-amount');
        if (userData && userData.balance !== undefined) { // Check if userData and balance are already populated
            balanceAmountEl.innerHTML = formatCurrency(userData.balance);
        } else {
            await refreshUserData(); // refreshUserData should populate global `userData`
            balanceAmountEl.innerHTML = userData.balance ? formatCurrency(userData.balance) : '$ 0.00';
        }

        if (userData && userData.id) {
            await Promise.all([fetchTransactions(), fetchDeposits()]);
        } else { // Fallback if userData wasn't populated by base.html's initial call
            await refreshUserData();
            if (userData && userData.id) {
                await Promise.all([fetchTransactions(), fetchDeposits()]);
            } else {
                console.error("User data not available after refresh for overview page.");
                // Display error messages in lists
                document.getElementById('initial-transactions-list').innerHTML = "<div class='alert alert-danger mx-3'>Could not load user data for transactions.</div>";
                document.getElementById('initial-deposits-list').innerHTML = "<div class='alert alert-danger mx-3'>Could not load user data for deposits.</div>";
            }
        }

        setupSectionToggle('transactions-toggle', 'transactions-list-content');
        setupSectionToggle('deposits-toggle', 'deposits-list-content');

        document.dispatchEvent(new CustomEvent('pageContentLoaded', {bubbles: true}));

    } catch (error) {
        console.error('Error loading page content:', error);
        document.getElementById('balance-amount').innerHTML = `<span class="text-danger" style="font-size: 1rem;">Error</span>`;
        document.dispatchEvent(new CustomEvent('pageContentLoaded')); // Still dispatch so loading screen hides
    }
});