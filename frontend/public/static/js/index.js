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
        setTimeout(() => window.location.href = '/fe/account', 2500);
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

// Check if the URL ends with #email-confirmed
if (window.location.hash === '#email-confirmed') {
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();
    showMessage('loginMessage', 'Your email has been successfully verified. You can now log in.', true);
}