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
    const openManageCategoriesModalBtn = document.getElementById('open-manage-categories-modal');
    const addCategoryForm = document.getElementById('add-category-form');
    const categoryNameInput = document.getElementById('category-name');
    const categoryDescriptionInput = document.getElementById('category-description');
    const submitCategoryBtn = document.getElementById('submit-category-btn');
    const manageCategoriesError = document.getElementById('manage-categories-error');
    const manageCategoriesSuccess = document.getElementById('manage-categories-success');
    const categoryErrorMessage = document.getElementById('category-error-message');

    // Modals
    const transactionConfirmModal = new bootstrap.Modal(document.getElementById('transactionConfirmModal'));
    const transactionDetailsModal = new bootstrap.Modal(document.getElementById('transactionDetailsModal'));
    const addCategoryModal = new bootstrap.Modal(document.getElementById('addCategoryModal'));
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

    // Event Listeners
    sendForm.addEventListener('submit', handleFormSubmit);
    recurringCheckbox.addEventListener('change', toggleIntervalGroup);
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
    openManageCategoriesModalBtn.addEventListener('click', handleOpenManageCategories);
    document.getElementById('open-add-category-modal').addEventListener('click', () => {
        addCategoryModal.show();
        manageCategoriesModal.hide();
    });
    submitCategoryBtn.addEventListener('click', handleAddCategory);

    // Load Data
    const categories = await loadCategories();
    await Promise.all([
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

    async function loadCategories(name = null) {
        try {
            const response = await fetch('/api/v1/categories', {
                headers: {'Authorization': `Bearer ${auth.getToken()}`}
            });
            const data = await response.json();
            if (data.categories && data.categories.length > 0) {
                categorySelect.innerHTML = '<option value="">Select a category</option> <option value="add-category">Create new category</option>';
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    categorySelect.appendChild(option);
                    if (category.name === name) {
                        setTimeout( () => {
                            categorySelect.value = category.id
                        }, 1750);
                    }
                });
            } else {
                categorySelect.innerHTML = '<option value="">Select a category</option> <option value="add-category">Create new category</option>';
                categorySelect.value = ''
            }
            return data.categories;
        } catch (error) {
            console.error('Error loading categories:', error);
            document.getElementById('category-group').style.display = 'none';
            return [];
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
            ${transaction.category_name ? `<span class="category">${transaction.category_name}</span>` : ''}
            <span class="amount">$${transaction.amount.toFixed(2)}</span>
        `;
        div.addEventListener('click', () => showTransactionDetails(transaction, status));
        return div;
    }

    async function handleOpenManageCategories(e) {
        e.preventDefault();
        const categoriesList = document.getElementById('categories-list');
        const categoriesLoading = document.getElementById('categories-loading');
        const noCategoriesMessage = document.getElementById('no-categories-message');

        categoriesList.style.opacity = '0';
        categoriesList.style.maxHeight = '0';
        categoriesLoading.style.display = 'flex';
        categoriesLoading.style.opacity = '1'
        noCategoriesMessage.style.display = 'none';
        manageCategoriesModal.show();

        try {
            const categories = await loadCategories();
            categoriesLoading.style.transition = 'opacity 0.3s ease';
            categoriesLoading.style.opacity = '0';
            setTimeout(() => {
                categoriesLoading.style.display = 'none';
                if (categories.length > 0) {
                    categoriesList.innerHTML = '';
                    categories.forEach(category => {
                        categoriesList.appendChild(createCategoryElement(category));
                    });
                    categoriesList.style.transition = 'opacity 0.3s ease, max-height 0.3s ease';
                    categoriesList.style.maxHeight = `${categoriesList.scrollHeight}px`;
                    categoriesList.style.opacity = '1';
                } else {
                    noCategoriesMessage.style.display = 'block';
                    categoriesList.style.maxHeight = '0';
                    categoriesList.style.opacity = '0';
                }
            }, 300);
        } catch (error) {
            console.error('Error loading categories for modal:', error);
            showManageCategoriesError('Failed to load categories');
            categoriesLoading.style.display = 'none';
            noCategoriesMessage.style.display = 'block';
        }
    }

    function createCategoryElement(category) {
        const div = document.createElement('div');
        div.className = 'category-entry';
        div.dataset.id = category.id;
        div.innerHTML = `
        <div class="category-info">
            <div class="category-name">${category.name}</div>
            ${category.description ? `<div class="category-description">${category.description}</div>` : ''}
        </div>
        <div class="category-actions">
            <i class="bi bi-trash" data-id="${category.id}"></i>
            <button class="confirm-delete" data-id="${category.id}">Confirm</button>
        </div>
    `;

        const trashIcon = div.querySelector('.bi-trash');
        const confirmButton = div.querySelector('.confirm-delete');
        const actions = trashIcon.parentElement;

        trashIcon.addEventListener('click', () => {
            if (!actions.classList.contains('confirm-active')) {
                actions.classList.add('confirm-active');
                setTimeout(() => {
                    if (actions.classList.contains('confirm-active')) {
                        actions.classList.remove('confirm-active');
                    }
                }, 5000);
            } else {
                actions.classList.remove('confirm-active');
            }
        });

        confirmButton.addEventListener('click', () => handleDeleteCategory(category.id));
        return div;
    }

    async function handleAddCategory() {
        const name = categoryNameInput.value.trim();
        const description = categoryDescriptionInput.value.trim();
        if (!name) {
            showCategoryError('Category name is required');
            return;
        }

        try {
            const response = await fetch('/api/v1/categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify({name, description})
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to add category');

            addCategoryForm.reset();
            addCategoryModal.hide();
            showManageCategoriesSuccess('Category added successfully');
            await loadCategories(name);

            await handleOpenManageCategories({
                preventDefault: () => {
                }
            });
        } catch (error) {
            showCategoryError(error.message);
        }
    }

    async function handleDeleteCategory(categoryId) {
        try {
            const response = await fetch(`/api/v1/categories/${categoryId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`
                }
            });
            if (!response.ok) throw new Error('Failed to delete category');
            loadTransactions("pending");
            loadTransactions("awaiting");

            showManageCategoriesSuccess('Category deleted successfully');
            const categoryElement = document.querySelector(`.category-entry[data-id="${categoryId}"]`);
            if (categoryElement) {
                categoryElement.style.opacity = '0';
                setTimeout(() => categoryElement.remove(), 300);
            }
            await loadCategories();
        } catch (error) {
            showManageCategoriesError(error.message);
        }
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
            category_id: categorySelect.value || null,
            recurring: recurringCheckbox.checked,
            interval: recurringCheckbox.checked ? intervalSelect.value : null
        };

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
                category_name: categorySelect.selectedOptions[0]?.text || null,
                amount: transactionData.amount,
                status: "pending"
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
            updateBalanceDisplay();
            loadTransactions("pending");
            loadTransactions("awaiting");
            sendForm.reset();
            // setTimeout(() => {
            //     location.reload();
            // }, 100);
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
            setLoading(true);
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

            transactionDetailsModal.hide();
            showSuccess('Transaction cancelled successfully');
            await auth.refreshOnEvent();
            updateBalanceDisplay();
            loadTransactions("pending");
            loadTransactions("awaiting");

            const transactionElement = document.querySelector(`.transaction-item[data-id="${transactionId}"]`);
            if (transactionElement) {
                transactionElement.style.opacity = '0';
                transactionElement.style.maxHeight = '0'
                setTimeout(() => {
                    transactionElement.style.display = 'none'
                }, 300)
            }
            // setTimeout(() => location.reload(), 100);
        } catch (error) {
            showError(error.message);
        } finally {
            setLoading(false);
            window.currentTransactionId = null;
        }
    }

    function showTransactionDetails(transaction, status) {
        document.getElementById('detail-modal-date').textContent = new Date(transaction.date).toLocaleString();
        document.getElementById('detail-modal-receiver').textContent = transaction.receiver_id || transaction.identifier;
        document.getElementById('detail-modal-amount').textContent = `$${transaction.amount.toFixed(2)}`;
        document.getElementById('detail-modal-description').textContent = transaction.description || 'No description';
        document.getElementById('detail-modal-status').textContent = transaction.status.replace('_', ' ');
        document.getElementById('detail-modal-category').textContent = transaction.category_name || 'Not categorized';
        window.currentTransactionId = transaction.id;

        const cancelButton = document.getElementById('cancel-transaction-btn');
        cancelButton.style.display = transaction.status === 'pending' ? 'inline-block' : 'inline-block';

        if (status === "awaiting") {
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

    function showCategoryError(message) {
        categoryErrorMessage.textContent = message;
        categoryErrorMessage.style.display = 'block';
        categoryErrorMessage.classList.add('visible');
        setTimeout(() => {
            categoryErrorMessage.classList.remove('visible');
            setTimeout(() => categoryErrorMessage.style.display = 'none', 300);
        }, 10000);
    }

    function showManageCategoriesError(message) {
        const manageCategoriesError = document.getElementById('manage-categories-error');
        manageCategoriesError.textContent = message;
        manageCategoriesError.style.display = 'block';
        manageCategoriesError.classList.add('visible');
        setTimeout(() => {
            manageCategoriesError.classList.remove('visible');
            setTimeout(() => manageCategoriesError.style.display = 'none', 300);
        }, 7500);
    }

    function showManageCategoriesSuccess(message) {
        const manageCategoriesSuccess = document.getElementById('manage-categories-success');
        manageCategoriesSuccess.textContent = message;
        manageCategoriesSuccess.style.display = 'block';
        manageCategoriesSuccess.classList.add('visible');
        setTimeout(() => {
            manageCategoriesSuccess.classList.remove('visible');
            setTimeout(() => manageCategoriesSuccess.style.display = 'none', 300);
        }, 7500);
    }

    const addToCategoryCheckbox = document.getElementById('add-to-category-checkbox');
    const categoryGroup = document.getElementById('category-group');

    addToCategoryCheckbox.addEventListener('change', () => {
        if (addToCategoryCheckbox.checked) {
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
        }
    });

    addToCategoryCheckbox.dispatchEvent(new Event('change'));
    recurringCheckbox.dispatchEvent(new Event('change'));

    // const categorySelect = document.getElementById('category-select');
    categorySelect.addEventListener('change', () => {
        if (categorySelect.value === 'add-category') {
            addCategoryModal.show(); // Assumes addCategoryModal is defined (e.g., Bootstrap modal)
            categorySelect.value = ''; // Reset to default
        }
    });
});