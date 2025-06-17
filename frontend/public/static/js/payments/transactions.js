document.addEventListener('DOMContentLoaded', () => {
    // State management
    const state = {
        filters: {},
        sort: 'date_desc',
        page: 1,
        limit: 30,
        totalPages: 1,
        userId: null,
        transactions: [],
        total: 0,
        total_completed: 0,
        total_incoming: 0,
        total_outgoing: 0,
        average_incoming: 0,
        average_outgoing: 0,
        showTransactions: true
    };

    // DOM elements
    const elements = {
        balanceAmount: $('#balance-amount'),
        subtitle: $('#page-subtitle'),
        totalTransactions: $('#total-transactions'),
        avgAmount: $('#avg-amount'),
        netMovement: $('#net-movement'),
        filterType: $('#filter-type'),
        sortBy: $('#sort-by'),
        filterInputs: $('#filter-inputs'),
        applyBtn: $('#apply-filters'),
        resetBtn: $('#reset-filters'),
        filterBadges: $('#filter-badges'),
        list: $('#transactions-list'),
        placeholder: $('#transactions-placeholder'),
        loading: $('#transactions-loading'),
        showTransactionsBtn: $('#show-transactions'),
        prevBtn: $('#prev-page'),
        nextBtn: $('#next-page'),
        pageInfo: $('#page-info'),
        modal: $('#transactionModal'),
        modalDate: $('#detail-date'),
        modalDescription: $('#detail-description'),
        modalAmount: $('#detail-amount'),
        modalStatus: $('#detail-status'),
        modalSenderId: $('#detail-sender-id'),
        modalReceiverId: $('#detail-receiver-id'),
        modalCategory: $('#detail-category'),
        filterBar: $('.filter-bar'),
        filterHeader: $('.filter-bar .card-header')
    };

    // Initialize Bootstrap modal
    const modal = new bootstrap.Modal(elements.modal[0]);

    // Category Management
    let categories = [];
    let currentTransactionId = null;

    // Helper function to display messages
    function showMessage(type, text) {
        const alert = $(`
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${text}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `).css({ position: 'fixed', top: '20px', right: '20px', zIndex: 2000 });
        $('body').append(alert);
        setTimeout(() => alert.fadeOut(300, () => alert.remove()), 4000);
    }

    // Fetch balance and update UI
    function updateBalance() {
        const userData = window.auth.getUserData();
        if (userData && userData.balance !== undefined) {
            elements.balanceAmount.text(`$${userData.balance.toFixed(2)}`);
        } else {
            elements.balanceAmount.text('N/A');
        }
    }

    // Fetch transactions from API
    async function fetchTransactions() {
        try {
            const token = window.auth.getToken();
            if (!token) {
                showMessage('danger', 'Please log in to view transactions');
                throw new Error('No authentication token');
            }

            const queryParams = {
                page: state.page,
                limit: state.limit,
                order_by: state.sort,
                ...state.filters
            };
            const query = new URLSearchParams(queryParams).toString();
            const response = await fetch(`/api/v1/transactions/?${query}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch transactions');
    }

            const data = await response.json();
            return data;
        } catch (error) {
            showMessage('danger', `Error: ${error.message}`);
            return null;
        }
    }

    // Initialize the page
    async function initTransactions() {
        elements.loading.show();
        const data = await fetchTransactions();
        console.log(data);
        if (data) {
            state.transactions = data.transactions;
            state.total = data.total;
            state.total_completed = data.total_completed;
            state.total_incoming = data.incoming_total;
            state.total_outgoing = data.outgoing_total;
            state.average_incoming = data.avg_incoming_transaction;
            state.average_outgoing = data.avg_outgoing_transaction;
            state.totalPages = data.pages;
            // state.totalPages = Math.ceil(data.total_matching / state.limit) || 1;
            state.userId = window.userData.id;
            elements.subtitle.text(``);
            renderTransactions();
            updateSummary(data);
            updateBalance(); // Update balance display
        } else {
            elements.list.html('<p class="text-muted text-center">No transactions available</p>');
        }
        elements.loading.hide();
    }

    // Render transactions list
    function renderTransactions() {
        elements.list.empty();
        if (state.transactions.length === 0) {
            elements.placeholder.fadeIn(300);
            elements.list.hide();
        } else {
            elements.placeholder.hide();
            elements.list.show();
            const grouped = {};
            state.transactions.forEach(tx => {
                const monthYear = new Date(tx.date).toLocaleString('default', { month: 'long', year: 'numeric' });
                grouped[monthYear] = grouped[monthYear] || [];
                grouped[monthYear].push(tx);
            });
            Object.keys(grouped).forEach(monthYear => {
                const $group = $('<div class="transaction-group"></div>');
                $group.append($('<h6 class="transaction-group-header">' + monthYear + '</h6>'));
                grouped[monthYear].forEach(tx => {
                    const amountClass = tx.sender_id === state.userId ? 'amount-negative' : 'amount-positive';
                    const amountText = tx.sender_id === state.userId ? '-$' + tx.amount.toFixed(2) : '+$' + tx.amount.toFixed(2);
                    const $item = $('<div class="transaction-item" data-tx-id="' + tx.id + '">'
                        + '<div class="transaction-date">' + new Date(tx.date).toLocaleDateString() + '</div>'
                        + '<div class="transaction-details">' + (tx.description || 'N/A') + '</div>'
                        + '<span class="status transaction-' + tx.status + '">' + tx.status + '</span>'
                        + '<div class="transaction-amount ' + amountClass + '">' + amountText + '</div>'
                        + '<span class="info-icon"><i class="bi bi-info-circle"></i></span>'
                        + '</div>');
                    $item.find('.info-icon').on('click', () => showTransactionDetails(tx));
                    $group.append($item);
                });
                elements.list.append($group);
            });
        }
        updatePagination();
        updateFilterBadges();
    }

    // Update summary cards with API aggregate data
    function updateSummary(data) {
        elements.totalTransactions.text(data.total_completed);
        document.getElementById("total-all-transactions").textContent = data.total;
        elements.avgAmount.text(`$${data.avg_incoming_transaction}`);
        document.getElementById("total-incoming").textContent = data.incoming_total;
        elements.netMovement.text(`$${data.avg_outgoing_transaction}`);
        document.getElementById("total-outgoing").textContent = data.outgoing_total;
    }

    // Update pagination controls
    function updatePagination() {
        elements.pageInfo.text(`Page ${state.page} of ${state.totalPages}`);
        elements.prevBtn.prop('disabled', state.page === 1);
        elements.nextBtn.prop('disabled', state.page === state.totalPages);
    }

    // Update filter badges
    function updateFilterBadges() {
        elements.filterBadges.empty();
        Object.entries(state.filters).forEach(([key, value]) => {
            if (value) {
                const displayKey = key.replace('_', ' ').toUpperCase();
                const $badge = $('<span class="filter-badge">' + displayKey + ': ' + value + '<i class="bi bi-x"></i></span>');
                $badge.on('click', () => {
                    delete state.filters[key];
                    initTransactions();
                });
                elements.filterBadges.append($badge);
            }
        });
    }

    // Show transaction details in modal
    async function showTransactionDetails(tx) {
        currentTransactionId = tx.id;
        
        // Update existing fields
        elements.modalDate.text(new Date(tx.date).toLocaleString());
        elements.modalDescription.text(tx.description || 'N/A');
        const isOutgoing = tx.sender_id === state.userId;
        elements.modalAmount.text(`${isOutgoing ? '-' : '+'}$${tx.amount.toFixed(2)}`);
        elements.modalStatus.text(tx.status);
        elements.modalSenderId.text(tx.sender_id);
        elements.modalReceiverId.text(tx.receiver_id);
        
        // Load and populate categories
        if (categories.length === 0) {
            await loadCategories();
        }
        
        const categorySelect = document.getElementById('detail-category');
        categorySelect.innerHTML = '<option value="">Select Category</option>';
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            if (tx.category_id === category.id) {
                option.selected = true;
            }
            categorySelect.appendChild(option);
        });
        
        // Show category section
        categorySelect.parentElement.style.display = 'block';
        
        // Add event listener for category changes
        categorySelect.onchange = async function() {
            const categoryId = this.value;
            if (categoryId) {
                await updateTransactionCategory(currentTransactionId, parseInt(categoryId));
            } else {
                await removeTransactionCategory(currentTransactionId);
            }
            // Refresh transaction list to show updated category
            initTransactions();
        };
        
        modal.show();
    }

    // Update filters from UI inputs
    function updateFilters() {
        state.filters = {};
        const type = elements.filterType.val();
        if (type === 'date') {
            const dateFrom = elements.filterInputs.find('#filter-date-from').val();
            const dateTo = elements.filterInputs.find('#filter-date-to').val();
            if (dateFrom) state.filters.date_from = dateFrom;
            if (dateTo) state.filters.date_to = dateTo;
        } else if (type === 'direction') {
            const direction = elements.filterInputs.find('input[name="direction"]:checked').val();
            if (direction) state.filters.direction = direction;
        } else if (type === 'status') {
            const status = elements.filterInputs.find('#filter-status').val();
            if (status) state.filters.status = status;
        }
    }

    // Validate filter inputs
    function validateFilters() {
        const { date_from, date_to } = state.filters;
        if (date_from && !/^\d{4}-\d{2}-\d{2}$/.test(date_from)) {
            showMessage('danger', 'Invalid "From" date format (YYYY-MM-DD)');
            return false;
        }
        if (date_to && !/^\d{4}-\d{2}-\d{2}$/.test(date_to)) {
            showMessage('danger', 'Invalid "To" date format (YYYY-MM-DD)');
            return false;
        }
        if (date_from && date_to && new Date(date_from) > new Date(date_to)) {
            showMessage('danger', '"From" date must be before "To" date');
            return false;
        }
        return true;
    }

    // Event listeners
    elements.filterType.on('change', () => {
        const type = elements.filterType.val();
        let inputHtml = '';
        if (type === 'date') {
            inputHtml = `
                <div class="filter-input active">
                    <div class="filter-group">
                        <label for="filter-date-from">From</label>
                        <input type="text" id="filter-date-from" class="form-control date-picker" placeholder="YYYY-MM-DD">
                    </div>
                    <div class="filter-group">
                        <label for="filter-date-to">To</label>
                        <input type="text" id="filter-date-to" class="form-control date-picker" placeholder="YYYY-MM-DD">
                    </div>
                </div>
            `;
        } else if (type === 'direction') {
            inputHtml = `
                <div class="filter-input active">
                    <div class="filter-group">
                        <label>Direction</label>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="direction" id="direction-out" value="out">
                            <label class="form-check-label" for="direction-out">Outgoing</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="direction" id="direction-in" value="in">
                            <label class="form-check-label" for="direction-in">Incoming</label>
                        </div>
                    </div>
                </div>
            `;
        } else if (type === 'status') {
            inputHtml = `
                <div class="filter-input active">
                    <div class="filter-group">
                        <label for="filter-status">Status</label>
                        <select id="filter-status" class="form-control">
                            <option value="">All</option>
                            <option value="pending">Pending</option>
                            <option value="awaiting_acceptance">Awaiting Acceptance</option>
                            <option value="completed">Completed</option>
                            <option value="denied">Denied</option>
                            <option value="cancelled">Cancelled</option>
                            <option value="failed">Failed</option>
                        </select>
                    </div>
                </div>
            `;
        }
        elements.filterInputs.hide().html(inputHtml).fadeIn(200);
        if (type === 'date') {
            flatpickr('.date-picker', { dateFormat: 'Y-m-d' });
        }
    });

    elements.applyBtn.on('click', async () => {
        updateFilters();
        if (!validateFilters()) return;
        state.page = 1;
        await initTransactions();
    });

    elements.resetBtn.on('click', () => {
        state.filters = {};
        state.sort = 'date_desc';
        state.page = 1;
        elements.filterInputs.empty().hide();
        elements.sortBy.val('date_desc');
        elements.filterType.val('');
        initTransactions();
    });

    elements.sortBy.on('change', () => {
        state.sort = elements.sortBy.val();
        state.page = 1;
        initTransactions();
    });

    elements.prevBtn.on('click', () => {
        if (state.page > 1) {
            state.page--;
            initTransactions();
        }
    });

    elements.nextBtn.on('click', () => {
        if (state.page < state.totalPages) {
            state.page++;
            initTransactions();
        }
    });

    elements.showTransactionsBtn.on('click', () => {
        state.showTransactions = true;
        new bootstrap.Collapse('#transactions-content', { toggle: true });
    });

    // Initialize UI
    function initUI() {
        $('[data-bs-toggle="tooltip"]').tooltip();
        flatpickr('.date-picker', { dateFormat: 'Y-m-d' });
    }

    async function loadCategories() {
        try {
            const response = await fetch('/api/v1/categories', {
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`
                }
            });
            const data = await response.json();
            categories = data.categories;
            return categories;
        } catch (error) {
            console.error('Error loading categories:', error);
            showMessage('danger', 'Error loading categories');
            return [];
        }
    }

    async function updateTransactionCategory(transactionId, categoryId) {
        try {
            const response = await fetch(`/api/v1/transactions/${transactionId}/category`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({ category_id: categoryId })
            });

            if (!response.ok) {
                throw new Error('Failed to update category');
            }

            showMessage('success', 'Category updated successfully');
            return true;
        } catch (error) {
            console.error('Error updating category:', error);
            showMessage('danger', 'Error updating category');
            return false;
        }
    }

    async function removeTransactionCategory(transactionId) {
        try {
            const response = await fetch(`/api/v1/transactions/${transactionId}/category`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to remove category');
            }

            showMessage('success', 'Category removed successfully');
            return true;
        } catch (error) {
            console.error('Error removing category:', error);
            showMessage('danger', 'Error removing category');
            return false;
        }
    }

    initUI();
    initTransactions();
});