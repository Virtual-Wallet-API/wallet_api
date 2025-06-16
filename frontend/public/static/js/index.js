function showMessage(elementId, message, isSuccess) {
    $(`#${elementId}`)
        .text(message)
        .removeClass('alert-success alert-danger d-none')
        .addClass(isSuccess ? 'alert-success' : 'alert-danger')
        .show();
}

async function login() {
    if (auth.loggedIn()) {
        showMessage('loginMessage', 'You are already logged in, redirecting', true);
        setTimeout(() => window.location.href = '/account', 1500);
        return;
    }

    const username = $('#username').val().trim();
    const password = $('#password').val().trim();

    if (!username || !password) {
        showMessage('loginMessage', 'Please fill in all fields', false);
        return;
    }

    let loginAttempt = await auth.login(username, password);

    if (loginAttempt.success) {
        showMessage('loginMessage', loginAttempt.message, true);
        window.location.href = '/account';
        return true;
    } else {
        showMessage('loginMessage', loginAttempt.message, false);
        return false;
    }
}

async function register() {
    const username = $('#signupUsername').val().trim();
    const email = $('#signupEmail').val().trim();
    const phone_number = $('#signupPhone').val().trim();
    const password = $('#signupPassword').val().trim();
    const confirmPassword = $('#signupConfirmPassword').val().trim();

    if (!username || !email || !phone_number || !password || !confirmPassword) {
        showMessage('signupMessage', 'Please fill in all fields', false);
        return;
    }

    if (password !== confirmPassword) {
        showMessage('signupMessage', 'Passwords do not match', false);
        return;
    }

    try {
        const userData = { username, email, phone_number, password };
        const registrationAttempt = await auth.register(userData);

        showMessage('signupMessage', 'Registration successful! Please check your email to verify your email address.', true);
    } catch (error) {
        showMessage('signupMessage', error.message, false);
    }
}

async function requestPasswordReset() {
    const email = $('#resetEmail').val().trim();

    if (!email) {
        showMessage('resetPasswordMessage', 'Please enter your email address', false);
        return;
    }

    try {
        const response = await fetch('/api/v1/users/forgot-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });

        if (response.ok) {
            showMessage('resetPasswordMessage', 'If the email exists, a reset link has been sent to your email address.', true);
            // Clear the form
            $('#resetEmail').val('');
        } else {
            const errorData = await response.json();
            showMessage('resetPasswordMessage', errorData.detail || 'An error occurred. Please try again.', false);
        }
    } catch (error) {
        showMessage('resetPasswordMessage', 'Network error. Please try again.', false);
    }
}

const loginButtons = document.getElementById("loginButtons");
const accountButtons = document.getElementById("accountButtons");
if (auth.loggedIn()) {
    loginButtons.style.display = "none";
    accountButtons.style.display = "block";
    document.getElementById("logoutButton").addEventListener("click", () => {
        auth.logout();
        window.location.reload();
    });
}

const loginForm = document.getElementById('ajax-submit');
loginForm.addEventListener('click', async (e) => {
    e.preventDefault();
    await login();
});

const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await register();
    });
}

const resetPasswordForm = document.getElementById('resetPasswordForm');
if (resetPasswordForm) {
    resetPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await requestPasswordReset();
    });
}

// Check if the URL ends with #email-confirmed
if (window.location.hash === '#login-email') {
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();
    showMessage('loginMessage', 'Your email has been successfully verified. You can now log in.', true);
}

// Check if the URL ends with #login
if (window.location.hash === '#login-error') {
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();
    showMessage('loginMessage', 'Something went wrong, please log in again.', false);
}

// Check if the URL ends with #login
if (window.location.hash === '#login') {
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();
}