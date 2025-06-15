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

            // Fix: Remove lingering modal-backdrop on close
            const modalEl = document.getElementById('transactionModal');
            modalEl.addEventListener('hidden.bs.modal', function handler() {
                document.body.classList.remove('modal-open');
                document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                modalEl.removeEventListener('hidden.bs.modal', handler);
            });
        });
    });
}

function toggleMoreItems(listId, buttonId, seeAllUrl) {
    const additionalList = document.getElementById(listId); // e.g., additional-deposits-list
    const viewBtn = document.getElementById(buttonId); // e.g., view-deposits-btn
    const contentElement = additionalList.parentElement; // e.g., deposits-list-content
    const contentParent = contentElement.parentElement; // e.g., .card
    const isShown = additionalList.classList.contains('show'); // Use class instead of style check

    if (!additionalList || !viewBtn || !contentElement || !contentParent) {
        console.error(`List, button, content, or parent element not found: ${listId}, ${buttonId}`);
        return;
    }

    // Find the toggle element (.card-header sibling of contentElement)
    const toggleElement = contentParent.querySelector('.card-header[role="button"][aria-expanded]');
    const toggleHeight = toggleElement ? toggleElement.getBoundingClientRect().height : 0;

    // Animation configuration - defined at the top so it's available for both cases
    const animationDuration = 500; // Match setupSectionToggle
    const easing = 'ease-in-out';

    if (isShown) {
        // Store the current heights before animation
        const additionalHeight = additionalList.scrollHeight;
        const contentHeight = contentElement.scrollHeight;

        // Collapse
        additionalList.animate(
            [{maxHeight: `${additionalHeight}px`, opacity: 1}, {maxHeight: '0px', opacity: 0}],
            {duration: animationDuration, easing: easing, fill: 'forwards'}
        );
        additionalList.classList.remove('show');

        contentElement.animate(
            [{maxHeight: `${contentHeight}px`}, {maxHeight: `${contentHeight - additionalHeight}px`}],
            {duration: animationDuration, easing: easing, fill: 'forwards'}
        );

        contentParent.animate(
            [{height: `${contentParent.scrollHeight}px`}, {height: `${toggleHeight + (contentHeight - additionalHeight)}px`}],
            {duration: animationDuration, easing: easing, fill: 'forwards'}
        ).onfinish = () => {
            // Reset to auto after animation to prevent fixed heights
            contentParent.style.height = 'auto';
            contentParent.style.maxHeight = 'none';
        };

        // Ensure button text is visible
        viewBtn.innerHTML = 'View More';
    } else {
        // Reset heights to ensure accurate measurements
        additionalList.style.maxHeight = '0px';
        contentElement.style.maxHeight = null; // Clear previous maxHeight
        contentParent.style.height = null; // Clear previous height

        // Force reflow to measure full height
        additionalList.style.maxHeight = 'none';
        const additionalHeight = additionalList.scrollHeight;
        additionalList.style.maxHeight = '0px'; // Reset for animation

        // Calculate heights
        const contentCurrentHeight = contentElement.scrollHeight; // Current height without additionalList
        const newContentHeight = contentCurrentHeight + additionalHeight; // Include additionalList
        const newParentHeight = toggleHeight + newContentHeight; // Total height for .card

        // Animate additionalList
        additionalList.animate(
            [
                {maxHeight: '0px', opacity: 0},
                {maxHeight: `${additionalHeight}px`, opacity: 1}
            ],
            {
                duration: animationDuration,
                easing: easing,
                fill: 'forwards'
            }
        );
        additionalList.classList.add('show'); // Mark as shown

        // Animate contentElement
        contentElement.animate(
            [
                {maxHeight: `${contentCurrentHeight}px`},
                {maxHeight: `${newContentHeight}px`}
            ],
            {
                duration: animationDuration,
                easing: easing,
                fill: 'forwards'
            }
        ).onfinish = () => {
            // Reset maxHeight after animation to prevent fixed heights
            contentElement.style.maxHeight = 'none';
        };

        // Animate contentParent
        contentParent.animate(
            [
                {height: `${contentParent.scrollHeight}px`},
                {height: `${newParentHeight}px`}
            ],
            {
                duration: animationDuration,
                easing: easing,
                fill: 'forwards'
            }
        ).onfinish = () => {
            // Reset to auto after animation to prevent fixed heights
            contentParent.style.height = 'auto';
            contentParent.style.maxHeight = 'none';
        };

        // Update button text with innerHTML to ensure visibility
        viewBtn.innerHTML = 'See All';
    }
}

// Generic function to render items
function renderItems(items, initialListEl, additionalListEl, viewBtnContainerEl, viewBtnEl, itemType, noItemsMessage, seeAllUrl) {
    // Guard against null elements
    if (!initialListEl) {
        console.error(`Initial list element for ${itemType} is null`);
        return;
    }

    initialListEl.innerHTML = '';

    if (additionalListEl) {
        additionalListEl.innerHTML = '';
    }

    if (!items || items.length === 0) {
        initialListEl.innerHTML = `<div class='alert alert-info mx-3 mt-3'>${noItemsMessage}</div>`;
        if (viewBtnContainerEl) {
            viewBtnContainerEl.style.display = 'none';
        }
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

    if (items.length <= 3 || !additionalListEl || !viewBtnContainerEl || !viewBtnEl) {
        initialListEl.innerHTML = itemEntries;
        if (viewBtnContainerEl) {
            viewBtnContainerEl.style.display = 'none';
        }
    } else {
        initialListEl.innerHTML = items.slice(0, 3).map(item => { /* Regenerate HTML for first 3 */
            // ... existing code ...
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
            // ... existing code ...
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
    const initialList = document.getElementById('initial-transactions-list');

    try {
        if (loadingAlert) {
            loadingAlert.classList.remove('hidden');
        }

        const response = await fetch(`${API_BASE}/transactions`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) {
            console.log(response.json());
            throw new Error(`Failed to fetch transactions: ${response.status}`);
        }

        const data = await response.json();
        const transactions = data.transactions.sort((a, b) => new Date(b.date) - new Date(a.date));

        renderItems(
            transactions.slice(0, 12), // Show up to 12, JS handles 3 + more
            initialList,
            document.getElementById('additional-transactions-list'),
            document.getElementById('view-transactions-btn-container'),
            document.getElementById('view-transactions-btn'),
            'transaction',
            'No transactions yet.',
            '/transactions' // URL for "See All"
        );
    } catch (error) {
        console.error('Error fetching transactions:', error);
        console.log()
        if (initialList) {
            initialList.innerHTML = "<div class='alert alert-danger mx-3'>Could not load transactions.</div>";
        }
    } finally {
        if (loadingAlert) {
            loadingAlert.classList.add('hidden');
        }
    }
}

async function fetchDeposits() {
    const loadingAlert = document.getElementById('deposits-loading-alert');
    const initialList = document.getElementById('initial-deposits-list');

    try {
        if (loadingAlert) {
            loadingAlert.classList.remove('hidden');
        }

        const response = await fetch(`${API_BASE}/deposits`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`}
        });
        if (!response.ok) throw new Error(`Failed to fetch deposits: ${response.status}`);

        const data = await response.json();
        const deposits = data.deposits.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        document.getElementById("income-amount").textContent = "$" + data.total_amount.toFixed(2);
        const money_out = (data.total_amount - window.userData.balance).toFixed(2)
        document.getElementById("spending-amount").textContent = "$" + money_out

        renderItems(
            deposits.slice(0, 12), // Show up to 12
            initialList,
            document.getElementById('additional-deposits-list'),
            document.getElementById('view-deposits-btn-container'),
            document.getElementById('view-deposits-btn'),
            'deposit',
            'No deposits yet.',
            '/deposits' // URL for "See All"
        );
    } catch (error) {
        console.error('Error fetching deposits:', error);
        if (initialList) {
            initialList.innerHTML = "<div class='alert alert-danger mx-3'>Could not load deposits.</div>";
        }
    } finally {
        if (loadingAlert) {
            loadingAlert.classList.add('hidden');
        }
    }
}

// Modified Toggle Function for Sections
function setupSectionToggle(toggleId, contentId) {
    const toggleElement = document.getElementById(toggleId);
    const contentElement = document.getElementById(contentId);
    const contentParent = contentElement.parentElement;

    if (!toggleElement || !contentElement || !contentParent) {
        console.error(`Toggle, content, or parent element not found: ${toggleId}, ${contentId}`);
        return;
    }

    console.log(`Setting up toggle for: ${toggleId} -> ${contentId}`);

    const arrowIcon = toggleElement.querySelector('i.bi-chevron-down');
    if (!arrowIcon) {
        console.error(`Arrow icon not found in toggle element: ${toggleId}`);
        return;
    }

    // Calculate toggle height (used for collapsed state)
    const boxToggleHeight = toggleElement.getBoundingClientRect().height;

    // Initialize state based on aria-expanded attribute
    let isExpanded = toggleElement.getAttribute('aria-expanded') === 'true';
    console.log(`isExpanded initial state for ${toggleId}: ${isExpanded}`);

    // Set initial state
    if (isExpanded) {
        contentParent.style.height = 'auto';
        contentParent.style.maxHeight = 'none';
        contentElement.classList.add('show');
        arrowIcon.classList.add('up');
        contentElement.style.maxHeight = contentElement.scrollHeight + 'px';
        contentElement.style.opacity = '1';
        contentElement.style.paddingTop = '0.5rem';
        contentElement.style.paddingBottom = '0.5rem';
    } else {
        contentParent.style.height = boxToggleHeight + 'px';
        contentParent.style.maxHeight = boxToggleHeight + 'px';
        contentElement.classList.remove('show');
        arrowIcon.classList.remove('up');
        contentElement.style.maxHeight = '0px';
        contentElement.style.opacity = '0';
        contentElement.style.paddingTop = '0';
        contentElement.style.paddingBottom = '0';
    }

    // Animation configuration
    const animationDuration = 500; // Match original 500ms transition
    const easing = 'ease-in-out'; // Smooth easing for natural animation

    // Toggle functionality
    toggleElement.addEventListener('click', (e) => {
        e.preventDefault();
        isExpanded = !isExpanded;

        toggleElement.setAttribute('aria-expanded', isExpanded);
        arrowIcon.classList.toggle('up', isExpanded);
        contentElement.classList.toggle('show', isExpanded);

        if (isExpanded) {
            // Expand content
            const contentHeight = contentElement.scrollHeight;

            contentParent.style.maxHeight = 'none';
            // Animate contentParent height
            contentParent.animate(
                [
                    {height: `${boxToggleHeight}px`},
                    {height: `${contentHeight + boxToggleHeight}px`}
                ],
                {
                    duration: animationDuration,
                    easing: easing,
                    fill: 'forwards'
                }
            ).onfinish = () => {
                contentParent.style.height = 'auto';
                contentParent.style.maxHeight = 'none';
            };

            // Animate contentElement properties
            contentElement.animate(
                [
                    {maxHeight: '0px', opacity: 0, paddingTop: '0', paddingBottom: '0'},
                    {maxHeight: `${contentHeight}px`, opacity: 1, paddingTop: '0.5rem', paddingBottom: '0.5rem'}
                ],
                {
                    duration: animationDuration,
                    easing: easing,
                    fill: 'forwards'
                }
            );

            // Animate arrow rotation (assuming CSS .up class uses transform: rotate(180deg))
            arrowIcon.animate(
                [
                    {transform: 'rotate(0deg)'},
                    {transform: 'rotate(180deg)'}
                ],
                {
                    duration: animationDuration,
                    easing: easing,
                    fill: 'forwards'
                }
            );
        } else {
            // Collapse content
            const currentContentHeight = contentElement.scrollHeight;

            // Animate contentParent height
            contentParent.animate(
                [
                    {height: `${contentParent.scrollHeight}px`},
                    {height: `${boxToggleHeight}px`}
                ],
                {
                    duration: animationDuration,
                    easing: easing,
                    fill: 'forwards'
                }
            ).onfinish = () => {
                contentParent.style.maxHeight = `${boxToggleHeight}px`;
            };

            // Animate contentElement properties
            contentElement.animate(
                [
                    {maxHeight: `${currentContentHeight}px`, opacity: 1, paddingTop: '0.5rem', paddingBottom: '0.5rem'},
                    {maxHeight: '0px', opacity: 0, paddingTop: '0', paddingBottom: '0'}
                ],
                {
                    duration: animationDuration,
                    easing: easing,
                    fill: 'forwards'
                }
            );

            // Animate arrow rotation back
            arrowIcon.animate(
                [
                    {transform: 'rotate(180deg)'},
                    {transform: 'rotate(0deg)'}
                ],
                {
                    duration: animationDuration,
                    easing: easing,
                    fill: 'forwards'
                }
            );
        }

        console.log(`isExpanded state for ${toggleId} after click: ${isExpanded}`);
    });


    // Keyboard accessibility
    toggleElement.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleElement.click();
        }
    });

    // Observe content changes to adjust heights when expanded
    const observer = new MutationObserver(() => {
        if (contentElement.classList.contains('show')) {
            console.log(`Observer adjusting heights for ${contentId}`);
            contentElement.style.maxHeight = contentElement.scrollHeight + 'px';
            contentParent.style.height = 'auto';
            contentParent.style.maxHeight = 'none';
        }
    });
    observer.observe(contentElement, {childList: true, subtree: true});
}

document.addEventListener("DOMContentLoaded", async function () {
    await initializeBaseScripts();

    try {
        const balanceAmountEl = document.getElementById('balance-amount');
        window.auth.ready.then(async (isInitialized) => {
            if (userData && userData.balance !== undefined) { // Check if userData and balance are already populated
                balanceAmountEl.innerHTML = formatCurrency(userData.balance);
            } else {
                await refreshUserData(); // refreshUserData should populate global `userData`
                if (balanceAmountEl) {
                    balanceAmountEl.innerHTML = userData.balance ? formatCurrency(userData.balance) : '$ 0.00';
                }
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
                    const transactionsList = document.getElementById('initial-transactions-list');
                    const depositsList = document.getElementById('initial-deposits-list');

                    if (transactionsList) {
                        transactionsList.innerHTML = "<div class='alert alert-danger mx-3'>Could not load user data for transactions.</div>";
                    }

                    if (depositsList) {
                        depositsList.innerHTML = "<div class='alert alert-danger mx-3'>Could not load user data for deposits.</div>";
                    }
                }
            }
        }).then(() => {
            document.dispatchEvent(new CustomEvent('pageContentLoaded', {bubbles: true}));
        });

        // Only attempt to set up toggles if elements exist
        if (document.getElementById('transactions-toggle') && document.getElementById('transactions-list-content')) {
            setupSectionToggle('transactions-toggle', 'transactions-list-content');
        }

        if (document.getElementById('deposits-toggle') && document.getElementById('deposits-list-content')) {
            setupSectionToggle('deposits-toggle', 'deposits-list-content');
        }

    } catch (error) {
        console.error('Error loading page content:', error);
        const balanceAmount = document.getElementById('balance-amount');
        if (balanceAmount) {
            balanceAmount.innerHTML = `<span class="text-danger" style="font-size: 1rem;">Error</span>`;
        }
        document.dispatchEvent(new CustomEvent('pageContentLoaded')); // Still dispatch so loading screen hides
    }
});
