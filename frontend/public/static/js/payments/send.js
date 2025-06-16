document.addEventListener('DOMContentLoaded', async () => {
    // DOM Elements
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
    const balanceAmount = document.getElementById('balance-amount');
    const balanceAmountLoading = document.getElementById('balance-amount-loading');
    const pendingToggle = document.getElementById('toggle-pending-transactions');
    const pendingContent = document.getElementById('pending-transactions-list-content');
    const awaitingToggle = document.getElementById('toggle-awaiting-transactions');
    const awaitingContent = document.getElementById('awaiting-transactions-list-content');
    const formLoadingOverlay = document.getElementById('form-loading-overlay');
    const addCategoryCheckbox = document.getElementById('add-category-checkbox');
    const categoryGroup = document.getElementById('category-group');
    const addCategoryModal = new bootstrap.Modal(document.getElementById('addCategoryModal'));
    const categoryNameInput = document.getElementById('category-name');
    const categoryDescriptionInput = document.getElementById('category-description');
    const submitCategoryBtn = document.getElementById('submit-category-btn');
    const categoryErrorMessage = document.getElementById('category-error-message');

    // Modals
    const transactionConfirmModal = new bootstrap.Modal(document.getElementById('transactionConfirmModal'));
    const transactionDetailsModal = new bootstrap.Modal(document.getElementById('transactionDetailsModal'));
    const manageCategoriesModal = new bootstrap.Modal(document.getElementById('manageCategoriesModal'));

    // Initial Setup
    balanceAmount.style.opacity = '0';
    balanceAmountLoading.style.display = 'block';
    pendingContent.style.display = 'block';
    pendingContent.style.opacity = '1';
    pendingToggle.setAttribute('aria-expanded', 'true');
    pendingToggle.querySelector('.toggle-icon').classList.replace('bi-chevron-down', 'bi-chevron-up');
    awaitingContent.style.display = 'block';
    awaitingContent.style.opacity = '1';
    awaitingToggle.setAttribute('aria-expanded', 'true');
    awaitingToggle.querySelector('.toggle-icon').classList.replace('bi-chevron-down', 'bi-chevron-up');
    categoryGroup.style.display = 'none'; // Initially hide category group

    // Event Listeners
    sendForm.addEventListener('submit', handleFormSubmit);
    recurringCheckbox.addEventListener('change', toggleIntervalGroup);
    addCategoryCheckbox.addEventListener('change', toggleCategoryGroup);
    pendingToggle.addEventListener('click', () => toggleSection(pendingToggle, pendingContent));
    awaitingToggle.addEventListener('click', () => toggleSection(awaitingToggle, awaitingContent));
    document.getElementById('confirm-transaction-btn').addEventListener('click', confirmTransaction);
    document.getElementById('confirm-transaction-btn2').addEventListener('click', confirmTransaction);
    document.getElementById('cancel-transaction-btn').addEventListener('click', cancelTransaction);
    document.querySelectorAll('.quick-amount').forEach(button => {
        button.addEventListener('click', () => {
            amountInput.value = button.dataset.amount;
            document.querySelectorAll('.quick-amount').forEach(btn => btn.classList.remove('selected'));
            button.classList.add('selected');
        });
    });
    categorySelect.addEventListener('change', () => {
        if (categorySelect.value === 'add_new') {
            addCategoryModal.show();
            categorySelect.value = '';
        }
    });
    submitCategoryBtn.addEventListener('click', handleAddCategory);
    document.getElementById('addCategoryModal').addEventListener('show.bs.modal', resetCategoryForm);
    document.getElementById('open-manage-categories-modal').addEventListener('click', async () => {
        await loadCategoriesForManagement();
        manageCategoriesModal.show();
    });

    // Load Data
    await Promise.all([
        loadCategories(),
        loadTransactions('pending'),
        loadTransactions('awaiting'),
        loadSummaryData()
    ]).then(() => {
        document.dispatchEvent(new Event('pageContentLoaded'));
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
            console.error('Error updating balance:', error);
            balanceAmount.textContent = 'Error';
            showError('Failed to load balance');
        }
    }

    await updateBalanceDisplay();

    async function loadCategories() {
        try {
            const response = await fetch('/api/v1/categories', {
                headers: {'Authorization': `Bearer ${auth.getToken()}`}
            });
            const data = await response.json();
            categorySelect.innerHTML = '<option value="">Select a category</option>';
            const addNewOption = document.createElement('option');
            addNewOption.value = 'add_new';
            addNewOption.textContent = 'Add a new category';
            categorySelect.appendChild(addNewOption);
            if (data.categories && data.categories.length > 0) {
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    categorySelect.appendChild(option);
                });
            }
            categorySelect.disabled = false; // Never disable, even with no categories
        } catch (error) {
            console.error('Error loading categories:', error);
            categorySelect.innerHTML = '<option value="">Select a category</option>' +
                                     '<option value="add_new">Add a new category</option>';
            categorySelect.disabled = false; // Keep enabled even on error
        }
    }

    async function loadCategoriesForManagement() {
        const listContainer = document.getElementById('categories-list-container');
        const noCategoriesMsg = document.getElementById('no-categories-message');

        if (!listContainer || !noCategoriesMsg) return;

        listContainer.innerHTML = '';
        noCategoriesMsg.style.display = 'none';

        try {
            const response = await fetch('/api/v1/categories', {
                headers: { 'Authorization': `Bearer ${auth.getToken()}` }
            });
            if (!response.ok) throw new Error('Failed to fetch categories');
            const data = await response.json();
            const categories = data.categories || [];

            if (categories.length === 0) {
                noCategoriesMsg.style.display = 'block';
                return;
            }

            categories.forEach((category, index) => {
                const item = document.createElement('div');
                item.className = 'category-entry';
                item.style.opacity = '0';
                item.style.transform = 'translateY(20px)';
                item.innerHTML = `
                    <div class="category-info">
                        <span>${category.name}</span>
                    </div>
                    <div class="category-actions">
                        <button type="button" class="btn-remove-category" data-category-id="${category.id}" aria-label="Delete category">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                `;
                listContainer.appendChild(item);
                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, 100 * index);
            });

            listContainer.querySelectorAll('.btn-remove-category').forEach(btn => {
                btn.addEventListener('click', handleDeleteCategory);
            });
        } catch (error) {
            console.error('Error loading categories:', error);
            displayModalMessage('Could not load categories.', 'error', 'manageCategoriesModal');
        }
    }

    async function handleDeleteCategory(event) {
        const categoryId = event.currentTarget.dataset.categoryId;
        if (!confirm('Are you sure you want to delete this category?')) return;

        const token = auth.getToken();
        if (!token) {
            displayModalMessage('Authorization required. Please refresh the page.', 'error', 'manageCategoriesModal');
            return;
        }

        const categoryItem = event.currentTarget.closest('.category-entry');
        if (categoryItem) categoryItem.classList.add('removing');

        try {
            const response = await fetch(`/api/v1/categories/${categoryId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete category.');
            }

            displayModalMessage('Category deleted successfully.', 'success', 'manageCategoriesModal');
            if (categoryItem) {
                categoryItem.style.height = `${categoryItem.offsetHeight}px`;
                categoryItem.style.opacity = '0';
                categoryItem.style.transform = 'translateX(50px)';
                setTimeout(() => {
                    categoryItem.style.height = '0';
                    categoryItem.style.marginBottom = '0';
                    categoryItem.style.padding = '0';
                    setTimeout(() => {
                        loadCategoriesForManagement();
                        loadCategories();
                    }, 300);
                }, 300);
            } else {
                loadCategoriesForManagement();
                loadCategories();
            }
        } catch (error) {
            displayModalMessage(error.message || 'Could not delete category.', 'error', 'manageCategoriesModal');
            if (categoryItem) categoryItem.classList.remove('removing');
        }
    }

    function displayModalMessage(message, type = 'error', modalId = 'manageCategoriesModal') {
        const messageId = type === 'success' ? 'manage-categories-success' : 'manage-categories-error';
        const messageDiv = document.getElementById(messageId);
        const otherMessageId = type === 'success' ? 'manage-categories-error' : 'manage-categories-success';
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

    async function loadTransactions(status) {
        const loadingElement = document.getElementById(`${status}-loading`);
        const container = document.getElementById(`initial-${status}`);
        const viewMoreContainer = document.getElementById(`view-more-${status}-btn-container`);
        const apiStatus = status === 'awaiting' ? 'awaiting_acceptance' : 'pending';

        try {
            loadingElement.style.display = 'flex';
            const response = await fetch(`/api/v1/transactions?limit=100&status=${apiStatus}&direction=out`, {
                headers: {'Authorization': `Bearer ${auth.getToken()}`}
            });
            const data = await response.json();
            container.innerHTML = '';
            if (data.transactions && data.transactions.length > 0) {
                data.transactions.forEach(transaction => {
                    container.appendChild(createTransactionElement(transaction, status));
                });
                viewMoreContainer.style.display = data.has_more ? 'block' : 'none';
            } else {
                container.innerHTML = `<p class="text-muted text-center" id="no-${status}">No ${status} transactions</p>`;
            }
        } catch (error) {
            console.error(`Error loading ${status} transactions:`, error);
            container.innerHTML = '<p class="text-danger text-center" id="error-' + status + '">Error loading transactions</p>';
        } finally {
            loadingElement.style.display = 'none';
        }
    }

    async function loadSummaryData() {
        try {
            const dateTo = new Date().toISOString().split('T')[0];
            const dateFrom = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            const response = await fetch(`/api/v1/transactions/?date_from=${dateFrom}&date_to=${dateTo}&direction=out`, {
                headers: {'Authorization': `Bearer ${auth.getToken()}`}
            });
            const data = await response.json();
            let ddata = calculateOutTrend(data.transactions);
            document.getElementById('money-sent-value').textContent = `$${ddata.total_without_pending.toFixed(2)}`;
            if (ddata.total_without_pending > 0) {
                document.getElementById('avg-transaction-value').textContent = `$${(ddata.total_without_pending / (ddata.total_awaiting + ddata.total_completed)).toFixed(2)}`;
            }
            document.getElementById('total-transactions-count').textContent = ddata.total_awaiting;
            document.getElementById('transaction-trend-value').textContent = `${ddata.total_completed.toFixed(0)}`;
        } catch (error) {
            console.error('Error loading summary data:', error);
        }
    }

    function calculateOutTrend(transactions) {
        let data = {
            total_completed: 0,
            total_pending_or_awaiting: 0,
            total_amount: 0,
            total_without_pending: 0,
            total_awaiting: 0
        };
        transactions.forEach((t) => {
            if (t.status === "completed") {
                data.total_completed++;
                data.total_amount += t.amount;
                data.total_without_pending += t.amount;
            }
            if (t.status === "pending" || t.status === "awaiting_acceptance") {
                data.total_pending_or_awaiting++;
                data.total_amount += t.amount;
                if (t.status !== "pending") {
                    data.total_without_pending += t.amount;
                    data.total_awaiting += 1;
                }
            }
        });
        return data;
    }

    function createTransactionElement(transaction, status) {
        const div = document.createElement('div');
        div.className = 'transaction-item';
        div.dataset.id = transaction.id;
        div.innerHTML = `
            <span class="date">${new Date(transaction.date).toLocaleDateString()}</span>
            <span class="description">${transaction.description || 'No description'}</span>
            <span class="status">${transaction.status.replace('_', ' ')}</span>
            <span class="amount">$${transaction.amount.toFixed(2)}</span>
        `;
        div.addEventListener('click', () => showTransactionDetails(transaction, status));
        return div;
    }

    function toggleIntervalGroup() {
        if (recurringCheckbox.checked) {
            intervalGroup.style.display = 'block';
            setTimeout(() => {
                intervalGroup.style.maxHeight = `${intervalGroup.scrollHeight}px`;
                intervalGroup.style.opacity = '1';
                intervalGroup.style.transition = 'max-height 0.3s ease, opacity 0.3s ease';
            }, 10);
        } else {
            intervalGroup.style.maxHeight = '0';
            intervalGroup.style.opacity = '0';
            intervalGroup.style.transition = 'max-height 0.3s ease, opacity 0.3s ease';
            setTimeout(() => {
                intervalGroup.style.display = 'none';
            }, 300);
        }
    }

    function toggleCategoryGroup() {
        if (addCategoryCheckbox.checked) {
            categoryGroup.style.display = 'block';
            setTimeout(() => {
                categoryGroup.style.maxHeight = `${categoryGroup.scrollHeight}px`;
                categoryGroup.style.opacity = '1';
                categoryGroup.style.transition = 'max-height 0.3s ease, opacity 0.3s ease';
            }, 10);
        } else {
            categoryGroup.style.maxHeight = '0';
            categoryGroup.style.opacity = '0';
            categoryGroup.style.transition = 'max-height 0.3s ease, opacity 0.3s ease';
            setTimeout(() => {
                categoryGroup.style.display = 'none';
            }, 300);
            categorySelect.value = '';
        }
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

    async function handleFormSubmit(e) {
        e.preventDefault();
        const amount = parseFloat(amountInput.value);
        if (isNaN(amount) || amount < 0.01) {
            showError('Amount must be at least $0.01');
            return;
        }
        const userData = await auth.getUserData();
        if (amount > userData.balance) {
            showError('Insufficient balance');
            return;
        }

        const transactionData = {
            identifier: receiverInput.value,
            amount: amount,
            description: descriptionInput.value,
            recurring: recurringCheckbox.checked,
            interval: recurringCheckbox.checked ? intervalSelect.value : null
        };

        if (addCategoryCheckbox.checked && categorySelect.value) {
            transactionData.category_id = categorySelect.value;
        }

        setLoading(true);
        try {
            const response = await fetch('/api/v1/transactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify(transactionData)
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to create transaction');

            document.getElementById('modal-receiver').textContent = transactionData.identifier;
            document.getElementById('modal-amount').textContent = `$${transactionData.amount.toFixed(2)}`;
            document.getElementById('modal-description').textContent = transactionData.description || 'No description';
            window.currentTransactionId = data.id;
            showSuccess('Transaction created successfully');
            document.getElementById("confirm-transaction-btn2").style.display = 'block';
            transactionConfirmModal.show();
            const transactionElement = createTransactionElement({
                id: data.id,
                date: new Date().toISOString(),
                description: transactionData.description,
                status: 'pending',
                amount: transactionData.amount
            }, "pending");
            document.getElementById('initial-pending').prepend(transactionElement);
            await loadSummaryData();
            await updateBalanceDisplay();
            clearTransactionBoxMessages();
        } catch (error) {
            showError(error.message);
        } finally {
            setLoading(false);
        }
    }

    function clearTransactionBoxMessages() {
        const boxMessages = [
            document.getElementById('no-pending'),
            document.getElementById('no-awaiting'),
            document.getElementById('error-pending'),
            document.getElementById('error-awaiting')
        ];
        boxMessages.forEach(message => {
            if (message) {
                message.remove();
            }
        });
    }

    async function confirmTransaction() {
        const transactionId = window.currentTransactionId;
        if (!transactionId) return;

        setLoading(true);
        try {
            const response = await fetch(`/api/v1/transactions/${transactionId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({action: 'confirm'})
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to confirm transaction');

            transactionConfirmModal.hide();
            showSuccess('Transaction confirmed successfully');
            await auth.refreshOnEvent();
            await updateBalanceDisplay();
            sendForm.reset();
            setTimeout(() => {
                location.reload();
            }, 100);
        } catch (error) {
            showError(error.message);
        } finally {
            setLoading(false);
            window.currentTransactionId = null;
        }
    }

    async function cancelTransaction() {
        const transactionId = window.currentTransactionId;
        if (!transactionId) return;

        try {
            const response = await fetch(`/api/v1/transactions/${transactionId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({action: 'cancel'})
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to cancel transaction');

            await auth.refreshOnEvent();
            transactionDetailsModal.hide();
            showSuccess('Transaction cancelled successfully');
            const transactionElement = document.querySelector(`#initial-pending .transaction-item[data-id="${transactionId}"]`);
            if (transactionElement) {
                transactionElement.style.opacity = '0';
            }
            setTimeout(() => location.reload(), 100);
        } catch (error) {
            showError(error.message);
        } finally {
            window.currentTransactionId = null;
        }
    }

    function showTransactionDetails(transaction, status) {
        document.getElementById('detail-modal-date').textContent = new Date(transaction.date).toLocaleString();
        document.getElementById('detail-modal-receiver').textContent = transaction.receiver_id || transaction.identifier;
        document.getElementById('detail-modal-amount').textContent = `$${transaction.amount.toFixed(2)}`;
        document.getElementById('detail-modal-description').textContent = transaction.description || 'No description';
        document.getElementById('detail-modal-status').textContent = transaction.status.replace('_', ' ');
        window.currentTransactionId = transaction.id;

        const cancelButton = document.getElementById('cancel-transaction-btn');
        cancelButton.style.display = transaction.status === 'pending' ? 'inline-block' : 'inline-block';

        if (status == "awaiting") {
            document.getElementById("confirm-transaction-btn2").style.display = 'none';
        } else {
            document.getElementById("confirm-transaction-btn2").style.display = 'block';
        }
        transactionDetailsModal.show();
    }

    function setLoading(isLoading) {
        submitButton.disabled = isLoading;
        buttonText.style.display = isLoading ? 'none' : 'inline';
        spinner.style.display = isLoading ? 'inline-block' : 'none';
        formLoadingOverlay.style.display = isLoading ? 'flex' : 'none';
    }

    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        successMessage.classList.add('visible');
        setTimeout(() => {
            successMessage.classList.remove('visible');
            setTimeout(() => successMessage.style.display = 'none', 300);
        }, 10000);
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.classList.add('visible');
        setTimeout(() => {
            errorMessage.classList.remove('visible');
            setTimeout(() => errorMessage.style.display = 'none', 300);
        }, 10000);
    }

    function setCategoryLoading(isLoading) {
        categoryNameInput.disabled = isLoading;
        categoryDescriptionInput.disabled = isLoading;
        submitCategoryBtn.disabled = isLoading;
        if (isLoading) {
            submitCategoryBtn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Adding...';
        } else {
            submitCategoryBtn.innerHTML = 'Add Category';
        }
    }

    function showCategoryError(message) {
        categoryErrorMessage.textContent = message;
        categoryErrorMessage.style.display = 'block';
        categoryErrorMessage.classList.add('visible');
        setTimeout(() => {
            categoryErrorMessage.classList.remove('visible');
            setTimeout(() => categoryErrorMessage.style.display = 'none', 300);
        }, 10000);
    }

    function resetCategoryForm() {
        categoryNameInput.value = '';
        categoryDescriptionInput.value = '';
        categoryErrorMessage.style.display = 'none';
    }

    async function handleAddCategory() {
        const name = categoryNameInput.value.trim();
        const description = categoryDescriptionInput.value.trim();
        if (!name) {
            showCategoryError('Category name is required');
            return;
        }
        setCategoryLoading(true);
        try {
            const response = await fetch('/api/v1/categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({ name: name, description: description })
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create category');
            }
            await loadCategories();
            const newCategoryOption = Array.from(categorySelect.options).find(option => option.textContent === name);
            if (newCategoryOption) {
                categorySelect.value = newCategoryOption.value;
            } else {
                showCategoryError('Failed to select the new category');
            }
            addCategoryModal.hide();
        } catch (error) {
            showCategoryError(error.message);
        } finally {
            setCategoryLoading(false);
        }
    }
});