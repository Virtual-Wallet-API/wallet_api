// Change Password
const passwordForm = document.getElementById('change-password-form');
if (passwordForm) {
    passwordForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        const statusSpan = document.getElementById('password-status');
        statusSpan.textContent = '';
        if (newPassword !== confirmPassword) {
            statusSpan.textContent = 'Passwords do not match.';
            statusSpan.className = 'ms-2 text-danger';
            return;
        }
        try {
            const token = auth.getToken();
            const response = await fetch('/api/v1/users/', {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ password: newPassword, current_password: currentPassword })
            });
            if (!response.ok) {
                const { detail } = await response.json();
                throw new Error(detail || 'Failed to change password');
            }
            statusSpan.textContent = 'Password changed successfully!';
            statusSpan.className = 'ms-2 text-success';
            passwordForm.reset();
        } catch (err) {
            statusSpan.textContent = err.message;
            statusSpan.className = 'ms-2 text-danger';
        }
    });
}

// Change Email
const emailForm = document.getElementById('change-email-form');
if (emailForm) {
    emailForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const newEmail = document.getElementById('new-email').value;
        const confirmEmail = document.getElementById('confirm-email').value;
        const currentPassword = document.getElementById('password-for-email').value;
        const statusSpan = document.getElementById('email-status');
        statusSpan.textContent = '';
        if (newEmail !== confirmEmail) {
            statusSpan.textContent = 'Emails do not match.';
            statusSpan.className = 'ms-2 text-danger';
            return;
        }
        try {
            const token = auth.getToken();
            const response = await fetch('/api/v1/users/', {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: newEmail, current_password: currentPassword })
            });
            if (!response.ok) {
                const { detail } = await response.json();
                throw new Error(detail || 'Failed to change email');
            }
            statusSpan.textContent = 'Email changed successfully!';
            statusSpan.className = 'ms-2 text-success';
            emailForm.reset();
            await auth.refreshUserData();
        } catch (err) {
            statusSpan.textContent = err.message;
            statusSpan.className = 'ms-2 text-danger';
        }
    });
}

// Change Phone Number
const phoneForm = document.getElementById('change-phone-form');
if (phoneForm) {
    phoneForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const newPhone = document.getElementById('new-phone').value;
        const confirmPhone = document.getElementById('confirm-phone').value;
        const currentPassword = document.getElementById('password-for-phone').value;
        const statusSpan = document.getElementById('phone-status');
        statusSpan.textContent = '';
        if (newPhone !== confirmPhone) {
            statusSpan.textContent = 'Phone numbers do not match.';
            statusSpan.className = 'ms-2 text-danger';
            return;
        }
        try {
            const token = auth.getToken();
            const response = await fetch('/api/v1/users/', {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ phone_number: newPhone, current_password: currentPassword })
            });
            if (!response.ok) {
                const { detail } = await response.json();
                throw new Error(detail || 'Failed to change phone number');
            }
            statusSpan.textContent = 'Phone number changed successfully!';
            statusSpan.className = 'ms-2 text-success';
            phoneForm.reset();
            await auth.refreshUserData();
        } catch (err) {
            statusSpan.textContent = err.message;
            statusSpan.className = 'ms-2 text-danger';
        }
    });
} 