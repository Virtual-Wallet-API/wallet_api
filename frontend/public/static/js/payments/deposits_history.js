// JavaScript remains unchanged
document.addEventListener('DOMContentLoaded', () => {
    const filterForm = document.getElementById('filter-form');
    const searchBySelect = document.getElementById('search_by');
    const queryInputs = document.getElementById('query-inputs');
    const depositsContainer = document.getElementById('deposits-container');
    const loadingAlert = document.getElementById('deposits-loading-alert');
    const paginationTop = document.getElementById('pagination-top');
    const paginationBottom = document.getElementById('pagination-bottom');
    const depositInvite = document.getElementById('deposit-invite');
    const limitSelect = document.getElementById('limit-select');
    const orderByBtn = document.querySelector('.order-by-btn');
    let currentPage = 1;
    let totalPages = 1;
    let totalDeposits = 0;
    let filterChanged = false;
    let orderBy = 'desc';

    function updateQueryInputs() {
        queryInputs.classList.add('fade');
        setTimeout(() => {
            queryInputs.innerHTML = '';
            const searchBy = searchBySelect.value;
            if (!searchBy) {
                queryInputs.innerHTML = `<div class="no-filter">${filterChanged ? 'No Filter' : 'Choose a filter'}</div>`;
            } else if (searchBy === 'date_period') {
                queryInputs.innerHTML = `
                        <div class="row" style="flex-wrap: nowrap; gap: 1rem;">
                            <div class="form-group">
                                <input type="date" id="from_date" name="from_date" class="form-control date-input" placeholder="From Date (YYYY-MM-DD)">
                            </div>
                            <div class="form-group">
                                <input type="date" id="to_date" name="to_date" class="form-control date-input" placeholder="To Date (YYYY-MM-DD)">
                            </div>
                        </div>
                    `;
            } else if (searchBy === 'amount_range') {
                queryInputs.innerHTML = `
                        <div class="row" style="flex-wrap: nowrap; gap: 1rem;">
                            <div class="form-group">
                                <input type="number" id="min_amount" name="min_amount" step="0.01" class="form-control amount-input" placeholder="Min Amount (e.g., 10.00)">
                            </div>
                            <div class="form-group">
                                <input type="number" id="max_amount" name="max_amount" step="0.01" class="form-control amount-input" placeholder="Max Amount (e.g., 100.00)">
                            </div>
                        </div>
                    `;
            } else if (searchBy === 'status') {
                queryInputs.innerHTML = `
                        <div class="form-group">
                            <select id="status" name="status" class="form-control status-select">
                                <option value="Pending">Pending</option>
                                <option value="Completed">Completed</option>
                                <option value="Failed">Failed</option>
                            </select>
                        </div>
                    `;
            }
            queryInputs.classList.remove('fade');
        }, 300);
        return true
    }

    function updateSearchByOptions() {
        if (!filterChanged && searchBySelect.value) {
            filterChanged = true;
            searchBySelect.innerHTML = `
                    <option value="" selected>Clear Filters</option>
                    <option value="date_period" ${searchBySelect.value === 'date_period' ? 'selected' : ''}>Date Period</option>
                    <option value="amount_range" ${searchBySelect.value === 'amount_range' ? 'selected' : ''}>Amount Range</option>
                    <option value="status" ${searchBySelect.value === 'status' ? 'selected' : ''}>Status</option>
                `;
        }
    }

    function toggleOrderBy() {
        if (orderBy === 'desc') {
            orderBy = 'asc';
            orderByBtn.textContent = 'Oldest';
            orderByBtn.dataset.value = 'asc';
        } else {
            orderBy = 'desc';
            orderByBtn.textContent = 'Newest';
            orderByBtn.dataset.value = 'desc';
        }
        currentPage = 1;
        fetchDeposits();
    }

    function getFilterParams() {
        const params = new URLSearchParams();
        const searchBy = searchBySelect.value;
        if (searchBy) {
            let searchQuery = '';
            if (searchBy === 'date_period') {
                const fromDate = document.getElementById('from_date')?.value;
                const toDate = document.getElementById('to_date')?.value;
                if (fromDate && toDate) {
                    searchQuery = `${fromDate}_${toDate}`;
                }
            } else if (searchBy === 'amount_range') {
                const minAmount = document.getElementById('min_amount')?.value;
                const maxAmount = document.getElementById('max_amount')?.value;
                if (minAmount && maxAmount) {
                    searchQuery = `${parseFloat(minAmount).toFixed(2)}_${parseFloat(maxAmount).toFixed(2)}`;
                }
            } else if (searchBy === 'status') {
                searchQuery = document.getElementById('status')?.value;
            }
            if (searchQuery) {
                params.set('search_by', searchBy);
                params.set('search_query', searchQuery);
            }
        }
        params.set('page', currentPage);
        params.set('limit', limitSelect.value);
        params.set('order_by', orderBy);
        return params;
    }

    async function fetchDeposits() {
        loadingAlert.classList.remove('hidden');
        depositInvite.style.display = 'none';
        const params = getFilterParams();
        const url = `${API_BASE}/deposits?${params.toString()}`;
        console.log('Fetching URL:', url); // Debug log
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                }
            });
            if (!response.ok) {
                if (response.status === 401) throw new Error('Unauthorized');
                throw new Error(`Failed to fetch deposits: ${response.status}`);
            }
            const data = await response.json();
            console.log('API Response:', data); // Debug log
            const deposits = data.deposits || [];
            totalPages = data.total_pages || Math.ceil((data.total_matching || 0) / parseInt(limitSelect.value)) || 1;
            totalDeposits = data.total || 0;
            // Ensure currentPage is valid
            if (currentPage > totalPages) {
                currentPage = totalPages;
            }
            console.log(`Current Page: ${currentPage}, Total Pages: ${totalPages}, Total Deposits: ${totalDeposits}, Total Matching: ${data.total_matching || 0}`); // Debug log
            renderDeposits(deposits, data.total_matching || 0);
            updatePagination();
        } catch (error) {
            console.error('Error fetching deposits:', error);
            depositsContainer.innerHTML = `<div class="alert alert-danger">${error.message === 'Unauthorized' ? 'Please log in to view deposits' : 'Error loading deposits'}</div>`;
            if (error.message === 'Unauthorized') {
                setTimeout(() => window.location.href = `${FE_BASE}/login`, 3000);
            }
        } finally {
            loadingAlert.classList.add('hidden');
        }
    }

    function renderDeposits(deposits, total_matching) {
        if (deposits.length === 0) {
            const message = searchBySelect.value ? 'No deposits matching the selected filters found.' : 'No deposits yet? Kickstart your wallet with your first deposit today!';
            depositsContainer.innerHTML = `<div class="alert alert-info">${message}</div>`;
            paginationTop.style.display = 'none';
            paginationBottom.style.display = 'none';
            depositInvite.style.display = searchBySelect.value ? 'none' : 'flex';
            return;
        }
        depositsContainer.innerHTML = deposits.map(deposit => {
            const date = new Date(deposit.created_at).toISOString().split('T')[0];
            const amount = `$${deposit.amount.toFixed(2)}`;
            const status = deposit.status.charAt(0).toUpperCase() + deposit.status.slice(1);
            const card = `Card ending in ${deposit.card_last_four}`;
            return `
                    <div class="deposit-item" data-deposit-id="${deposit.id}" data-date="${date}" data-card="${card}" data-amount="${deposit.amount}" data-status="${status}">
                        <span class="date">${date}</span>
                        <span class="deposit-card">${card}</span>
                        <span class="status">${status}</span>
                        <span class="amount">${amount}</span>
                        <span class="info-icon"><i class="bi bi-info-circle"></i></span>
                    </div>
                `;
        }).join('');
        paginationTop.style.display = parseInt(limitSelect.value) < total_matching ? 'flex' : 'none';
        paginationBottom.style.display = parseInt(limitSelect.value) < total_matching ? 'flex' : 'none';
        depositInvite.style.display = totalDeposits <= 6 && !searchBySelect.value ? 'flex' : 'none';
        attachDepositListeners();
    }

    function renderPagination(container) {
        container.innerHTML = '';
        const prevButton = document.createElement('button');
        prevButton.textContent = '<';
        prevButton.disabled = currentPage <= 1;
        prevButton.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                console.log('Previous Page Clicked:', currentPage); // Debug log
                fetchDeposits();
            }
        });

        // Add nearby page numbers (±2)
        const pages = [];
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = 'page-number';
            pageBtn.textContent = i;
            pageBtn.disabled = i === currentPage;
            pageBtn.addEventListener('click', () => {
                currentPage = i;
                console.log('Page Clicked:', currentPage); // Debug log
                fetchDeposits();
            });
            pages.push(pageBtn);
        }

        const nextButton = document.createElement('button');
        nextButton.textContent = '>';
        nextButton.disabled = currentPage >= totalPages;
        nextButton.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                console.log('Next Page Clicked:', currentPage); // Debug log
                fetchDeposits();
            }
        });

        container.appendChild(prevButton);
        pages.forEach(page => container.appendChild(page));
        container.appendChild(nextButton);
    }

    function updatePagination() {
        renderPagination(paginationTop);
        renderPagination(paginationBottom);
        console.log(`Pagination Updated: Page ${currentPage}/${totalPages}`); // Debug log
    }

    function attachDepositListeners() {
        document.querySelectorAll('.deposit-item').forEach(item => {
            item.addEventListener('click', () => {
                const date = item.dataset.date;
                const card = item.dataset.card;
                const amount = `$${parseFloat(item.dataset.amount).toFixed(2)}`;
                const status = item.dataset.status;
                document.getElementById('modal-date').textContent = date;
                document.getElementById('modal-card').textContent = card;
                document.getElementById('modal-amount').textContent = amount;
                document.getElementById('modal-status').textContent = status;
                $('#depositModal').modal('show');
            });
        });
    }

    searchBySelect.addEventListener('change', () => {
        updateSearchByOptions();
        updateQueryInputs();
    });

    filterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        currentPage = 1;
        fetchDeposits();
    });

    limitSelect.addEventListener('change', () => {
        currentPage = 1;
        fetchDeposits();
    });

    orderByBtn.addEventListener('click', toggleOrderBy);

    // Initial load
    Promise.all([
        updateQueryInputs(),
        fetchDeposits()
    ]).then(() => {
        document.documentElement.classList.remove('pageContentLoaded');
    });

});