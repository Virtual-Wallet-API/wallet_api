document.addEventListener('DOMContentLoaded', function() {
    // Initialize section toggle
    initializeSectionToggle();
    
    // Initialize form submission
    initializeFormSubmission();
    
    // Initialize search functionality
    initializeSearch();
    
    // Load initial contacts
    loadContacts();

    document.dispatchEvent(new Event('pageContentLoaded'));
});

// Section Toggle Functionality
function initializeSectionToggle() {
    const toggle = document.getElementById('contacts-toggle');
    const content = document.getElementById('contacts-list-content');
    const icon = toggle.querySelector('i.bi-chevron-down');
    
    toggle.addEventListener('click', function() {
        // Toggle expanded state
        const isExpanded = this.getAttribute('aria-expanded') === 'true';
        this.setAttribute('aria-expanded', !isExpanded);
        
        // Toggle content visibility
        if (isExpanded) {
            content.style.maxHeight = '0';
            content.style.opacity = '0';
            content.classList.remove('show');
            icon.classList.remove('up');
        } else {
            content.style.maxHeight = content.scrollHeight + 'px';
            content.style.opacity = '1';
            content.classList.add('show');
            icon.classList.add('up');
        }
    });
}

// Form Submission
function initializeFormSubmission() {
    const form = document.getElementById('add-contact-form');
    const submitButton = document.getElementById('submit-button');
    const buttonText = document.getElementById('button-text');
    const spinner = document.getElementById('spinner');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        successMessage.classList.remove('visible');
        errorMessage.classList.remove('visible');
        
        // Disable form and show loading state
        form.querySelectorAll('input').forEach(input => input.disabled = true);
        submitButton.disabled = true;
        buttonText.style.display = 'none';
        spinner.style.display = 'inline-block';
        
        // Get form data
        contactAddInput = document.getElementById("contact-identifier")
        const data = {
            identifier: contactAddInput.value
        };
        console.log(data);
        // Submit contact
        fetch('/api/v1/users/contacts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${auth.getToken()}`
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (!data.detail) {
                // Show success message
                successMessage.textContent = 'Contact added successfully!';
                successMessage.classList.add('visible');
                
                // Reset form
                form.reset();
                
                // Reload contacts list
                loadContacts();
            } else {
                throw new Error(data.detail);
            }
        })
        .catch(error => {
            // Show error message
            console.log(error.message);
            errorMessage.textContent = error.message;
            errorMessage.classList.add('visible');
        })
        .finally(() => {
            // Re-enable form and hide loading state
            form.querySelectorAll('input').forEach(input => input.disabled = false);
            submitButton.disabled = false;
            buttonText.style.display = 'inline-block';
            spinner.style.display = 'none';
        });
    });
}

// Search Functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-contacts');
    
    searchInput.addEventListener('keyup', function() {
        const query = this.value.toLowerCase();
        const contacts = document.querySelectorAll('.contact-item');
        
        contacts.forEach(contact => {
            const username = contact.querySelector('.username').textContent.toLowerCase();
            const email = contact.querySelector('.email').textContent.toLowerCase();
            
            if (username.includes(query) || email.includes(query)) {
                contact.style.opacity = '1';
                contact.style.maxHeight = contact.scrollHeight + 'px';
                contact.style.transform = 'translateX(0)';
            } else {
                contact.style.opacity = '0';
                contact.style.maxHeight = '0';
                contact.style.transform = 'translateX(-20px)';
            }
        });
    });
}

// Load Contacts
function loadContacts() {
    const loadingContainer = document.getElementById('contacts-loading');
    const initialContainer = document.getElementById('initial-contacts');
    const viewMoreContainer = document.getElementById('view-more-contacts-btn-container');
    
    // Show loading state
    loadingContainer.classList.remove('hidden');
    
    // Fetch contacts from API
    fetch('/api/v1/users/contacts', {
        headers: {
            'Authorization': `Bearer ${auth.getToken()}`
        }
    })
    .then(response => response.json())
    .then(contacts => {
        // Hide loading state
        loadingContainer.classList.add('hidden');
        
        if (contacts && contacts.length > 0) {
            // Render initial contacts
            renderContacts(contacts.slice(0, 5), initialContainer);
            
            // Handle additional contacts
            if (contacts.length > 5) {
                const additionalContainer = document.getElementById('additional-contacts');
                renderContacts(contacts.slice(5), additionalContainer);
                viewMoreContainer.style.display = 'block';
                
                // Add view more functionality
                document.getElementById('view-contacts-btn').addEventListener('click', function(e) {
                    e.preventDefault();
                    additionalContainer.style.maxHeight = additionalContainer.scrollHeight + 'px';
                    additionalContainer.style.opacity = '1';
                    viewMoreContainer.style.display = 'none';
                });
            }
        } else {
            initialContainer.innerHTML = '<p class="text-center text-muted">No contacts found.</p>';
        }
    })
    .catch(error => {
        console.error('Error loading contacts:', error);
        loadingContainer.classList.add('hidden');
        initialContainer.innerHTML = '<p class="text-center text-danger">Error loading contacts. Please try again later.</p>';
    });
}

// Render Contacts
function renderContacts(contacts, container) {
    container.innerHTML = contacts.map(contact => `
        <div class="contact-item" data-contact-id="${contact.id}">
            <div class="contact-icon">
                <i class="bi bi-person"></i>
            </div>
            <div class="contact-details">
                <div class="username">${contact.contact_user.username}</div>
                <div class="email">${contact.contact_user.email}</div>
            </div>
            <div class="contact-actions">
                <button class="btn btn-sm btn-outline-primary" onclick="showContactDetails('${contact.id}')">
                    <i class="bi bi-info-circle"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Show Contact Details Modal
function showContactDetails(contactId) {
    // Find contact in the list
    const contactItem = document.querySelector(`.contact-item[data-contact-id="${contactId}"]`);
    const username = contactItem.querySelector('.username').textContent;
    const email = contactItem.querySelector('.email').textContent;
    
    // Update modal content
    document.getElementById('modal-username').textContent = username;
    document.getElementById('modal-email').textContent = email;
    document.getElementById('modal-phone').textContent = 'Not provided'; // You might want to add this to the API response
    document.getElementById('modal-status').textContent = 'Active'; // You might want to add this to the API response
    
    // Update remove button
    const removeButton = document.getElementById('remove-contact-btn');
    removeButton.onclick = function() {
        if (confirm('Are you sure you want to remove this contact?')) {
            removeContact(contactId);
        }
    };
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('contactDetailsModal'));
    modal.show();
}

// Remove Contact
function removeContact(contactId) {
    fetch(`/api/v1/users/contacts/${contactId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${auth.getToken()}`
        }
    })
    .then(response => {
        if (response.status === 204) {
            // Find and fade out the contact
            const contactItem = document.querySelector(`.contact-item[data-contact-id="${contactId}"]`);
            if (contactItem) {
                contactItem.style.opacity = '0';
                contactItem.style.maxHeight = '0';
                contactItem.style.transform = 'translateX(-20px)';
                setTimeout(() => {
                    contactItem.remove();
                    
                    // Check if there are any contacts left
                    const remainingContacts = document.querySelectorAll('.contact-item');
                    if (remainingContacts.length === 0) {
                        const container = document.getElementById('initial-contacts');
                        container.innerHTML = '<p class="text-center text-muted">No contacts found.</p>';
                    }
                }, 300);
            }
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('contactDetailsModal'));
            modal.hide();
        } else {
            throw new Error('Failed to remove contact');
        }
    })
    .catch(error => {
        console.error('Error removing contact:', error);
        alert('Error removing contact. Please try again later.');
    });
} 