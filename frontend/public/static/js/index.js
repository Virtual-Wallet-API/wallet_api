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
        //setTimeout(() => window.location.href = '/fe/account', 2500);
        return true;
    } else {
        showMessage('loginMessage', loginAttempt.message, false);
        return false;
    }
}

const loginButtons = document.getElementById("loginButtons")
const accountButtons = document.getElementById("accountButtons")
if (auth.loggedIn()) {
    loginButtons.style.display = "none";
    accountButtons.style.display = "block";
    document.getElementById("logoutButton").addEventListener("click", () => {
        auth.logout();
        window.location.reload();
    })
}

const loginForm = document.getElementById('ajax-submit');

loginForm.addEventListener('click', async (e) => {
    e.preventDefault();
    await login();
})

