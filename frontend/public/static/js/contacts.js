document.addEventListener('DOMContentLoaded', async () => {
    // DOM Elements
    const addContactToggle = document.getElementById('add-contact-toggle');
    const addContactBox = document.getElementById('add-contact-box');
    const contactsToggle = document.getElementById('contacts-toggle');
    const contactsContent = document.getElementById('contacts-list-content');
    const addContactForm = document.getElementById('add-contact-form');
    const submitButton = document.getElementById('submit-button');
    const buttonText = document.getElementById('button-text');
    const spinner = document.getElementById('spinner');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    const balanceAmount = document.getElementById('balance-amount');
    const balanceAmountLoading = document.getElementById('balance-amount-loading');
    const formLoadingOverlay = document.getElementById('form-loading-overlay');
    const contactDetailsModal = new bootstrap.Modal(document.getElementById('contactDetailsModal'));

    // Initial Setup
    balanceAmount.style.opacity = '0';
    balanceAmountLoading.style.display = 'block';
    contactsContent.style.display = 'block';
    contactsContent.style.opacity = '1';
    contactsContent.style.maxHeight = '1000px'; // Sufficiently large value for smooth transition
    contactsToggle.setAttribute('aria-expanded', 'true');
    contactsToggle.querySelector('.toggle-icon').classList.replace('bi-chevron-down', 'bi-chevron-up');
    addContactBox.style.display = 'block';
    addContactBox.style.opacity = '1';
    addContactBox.style.maxHeight = '1000px'; // Sufficiently large value for smooth transition

    // Event Listeners
    addContactToggle.addEventListener('click', () => toggleSection(addContactToggle, addContactBox));
    contactsToggle.addEventListener('click', () => toggleSection(contactsToggle, contactsContent));
    addContactForm.addEventListener('submit', handleFormSubmit);
    document.getElementById('create-transaction-btn').addEventListener('click', createTransaction);
    document.getElementById('remove-contact-btn').addEventListener('click', removeContact);
    document.querySelectorAll('.contact-item').forEach(item => {
        item.addEventListener('click', () => {
            const contactId = item.getAttribute('data-contact-id');
            showContactDetails(contactId);
        });
    });
    initializeSearch();

    // Load Data
    await Promise.all([
        loadContacts(),
        updateBalanceDisplay()
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

    function toggleSection(toggle, content) {
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', !isExpanded);
        const icon = toggle.querySelector('.toggle-icon');
        if (!isExpanded) {
            content.style.display = 'block';
            content.style.transition = 'max-height 0.4s ease-in-out, opacity 0.4s ease-in-out';
            content.style.maxHeight = '1000px'; // Large enough to accommodate content
            content.style.opacity = '1';
            icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
        } else {
            content.style.transition = 'max-height 0.4s ease-in-out, opacity 0.4s ease-in-out';
            content.style.maxHeight = '0';
            content.style.opacity = '0';
            setTimeout(() => {
                content.style.display = 'none';
            }, 400);
        }
    }

    async function handleFormSubmit(e) {
        e.preventDefault();
        successMessage.style.display = 'none';
        errorMessage.style.display = 'none';
        setLoading(true);

        const contactAddInput = document.getElementById('contact-identifier');
        const data = { identifier: contactAddInput.value.trim() };

        try {
            const response = await fetch('/api/v1/users/contacts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.getToken()}`
                },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (response.ok) {
                showSuccess('Contact added successfully!');
                addContactForm.reset();
                await loadContacts();
                await updateBalanceDisplay();
            } else {
                throw new Error(result.detail || 'Failed to add contact');
            }
        } catch (error) {
            showError(error.message || 'User not found or invalid identifier');
        } finally {
            setLoading(false);
        }
    }

    function initializeSearch() {
        const searchInput = document.getElementById('search-contacts');
        searchInput.addEventListener('keyup', function() {
            const query = this.value.toLowerCase();
            const contacts = document.querySelectorAll('.contact-item');
            contacts.forEach(contact => {
                const username = contact.getAttribute('data-username').toLowerCase();
                const email = contact.getAttribute('data-email').toLowerCase();
                if (username.includes(query) || email.includes(query)) {
                    contact.classList.remove('hidden');
                } else {
                    contact.classList.add('hidden');
                }
            });
            const container = document.getElementById('contacts-list-content');
            container.style.maxHeight = '1000px'; // Adjust dynamically if needed
        });
    }

    async function loadContacts() {
        const loadingContainer = document.getElementById('contacts-loading');
        const initialContainer = document.getElementById('initial-contacts');
        const additionalContainer = document.getElementById('additional-contacts');
        const viewMoreContainer = document.getElementById('view-more-contacts-btn-container');

        loadingContainer.style.display = 'flex';
        try {
            const response = await fetch('/api/v1/users/contacts', {
                headers: { 'Authorization': `Bearer ${auth.getToken()}` }
            });
            const contacts = await response.json();
            initialContainer.innerHTML = '';
            additionalContainer.innerHTML = '';
            viewMoreContainer.style.display = 'none';

            if (contacts && contacts.length > 0) {
                renderContacts(contacts.slice(0, 5), initialContainer);
                if (contacts.length > 5) {
                    renderContacts(contacts.slice(5), additionalContainer);
                    viewMoreContainer.style.display = 'block';
                    document.getElementById('view-contacts-btn').addEventListener('click', () => {
                        additionalContainer.style.display = 'block';
                        additionalContainer.style.maxHeight = '1000px';
                        additionalContainer.style.opacity = '1';
                        viewMoreContainer.style.display = 'none';
                        contactsContent.style.maxHeight = '1000px';
                    });
                }
            } else {
                initialContainer.innerHTML = '<p class="text-muted text-center">No contacts found.</p>';
            }
        } catch (error) {
            console.error('Error loading contacts:', error);
            initialContainer.innerHTML = '<p class="text-danger text-center">Error loading contacts.</p>';
        } finally {
            loadingContainer.style.display = 'none';
            contactsContent.style.maxHeight = '1000px';
        }
    }

    function renderContacts(contacts, container) {
        container.innerHTML = contacts.map(contact => `
            <div class="contact-item" data-contact-id="${contact.id}" 
                 data-username="${contact.contact_user.username}" 
                 data-email="${contact.contact_user.email}" 
                 data-phone="${contact.contact_user.phone || 'Not provided'}" 
                 data-status="${contact.contact_user.status || 'Active'}" 
                 data-avatar="${contact.contact_user.avatar || ''}">
                <div class="contact-avatar">
                    ${contact.contact_user.avatar ? 
                        `<img src="${contact.contact_user.avatar}" alt="Avatar" class="avatar-img">` : 
                        `<i class="bi bi-person-circle"></i>`}
                </div>
                <div class="contact-info">
                    <div class="username">${contact.contact_user.username}</div>
                    <div class="email">${contact.contact_user.email}</div>
                </div>
            </div>
        `).join('');
        document.querySelectorAll('.contact-item').forEach(item => {
            item.addEventListener('click', () => {
                const contactId = item.getAttribute('data-contact-id');
                showContactDetails(contactId);
            });
        });
    }

    function showContactDetails(contactId) {
        const contactItem = document.querySelector(`.contact-item[data-contact-id="${contactId}"]`);
        if (!contactItem) return;

        const username = contactItem.getAttribute('data-username');
        const email = contactItem.getAttribute('data-email');
        const phone = contactItem.getAttribute('data-phone');
        const status = contactItem.getAttribute('data-status');
        const avatar = contactItem.getAttribute('data-avatar');

        document.getElementById('modal-username').textContent = username;
        document.getElementById('modal-email').textContent = email;
        document.getElementById('modal-phone').textContent = phone;
        document.getElementById('modal-status').textContent = status;
        const modalAvatar = document.getElementById('modal-avatar');
        modalAvatar.innerHTML = avatar ? `<img src="${avatar}" alt="Avatar" class="avatar-img">` : '<i class="bi bi-person-circle"></i>';

        window.currentContactId = contactId;
        window.currentContactUsername = username;
        contactDetailsModal.show();
    }

    function createTransaction() {
        if (window.currentContactUsername) {
            window.location.href = `/send#contact-${window.currentContactUsername}`;
        }
        contactDetailsModal.hide();
    }

    function removeContact() {
        const contactId = window.currentContactId;
        if (!contactId) return;

        if (confirm('Are you sure you want to remove this contact?')) {
            fetch(`/api/v1/users/contacts/${contactId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${auth.getToken()}` }
            })
            .then(response => {
                if (response.status === 204) {
                    const contactItem = document.querySelector(`.contact-item[data-contact-id="${contactId}"]`);
                    if (contactItem) {
                        contactItem.classList.add('hidden');
                        setTimeout(() => {
                            contactItem.remove();
                            if (!document.querySelector('.contact-item')) {
                                document.getElementById('initial-contacts').innerHTML = '<p class="text-muted text-center">No contacts found.</p>';
                            }
                            contactsContent.style.maxHeight = '1000px';
                        }, 300);
                    }
                    contactDetailsModal.hide();
                    showSuccess('Contact removed successfully!');
                } else {
                    throw new Error('Failed to remove contact');
                }
            })
            .catch(error => {
                console.error('Error removing contact:', error);
                showError('Failed to remove contact');
            });
        }
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
});