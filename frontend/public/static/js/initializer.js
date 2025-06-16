async function initializeBaseScripts() {

    try {
        if (isInitialized) return;
    } catch (error) {
        isInitialized = true;
    }

    const pageContentLoaded = new Promise(resolve => {
        const timeoutId = setTimeout(resolve, 1000);
        document.addEventListener('pageContentLoaded', () => {
            clearTimeout(timeoutId);
            resolve();
        }, { once: true });
    });

    const logoutButton = document.getElementById("logout-btn");
    if (logoutButton) {
        logoutButton.addEventListener('click', async (e) => {
            e.preventDefault();
            await auth.logout();
            window.location.href = '/';
        });
    }

    try {
        if (typeof jQuery === 'undefined' || typeof bootstrap === 'undefined') {
            throw new Error('jQuery or Bootstrap not loaded');
        }

        // Wait for page content to be fully loaded
        await pageContentLoaded;

        const loadingScreen = document.getElementById('loading-screen');
        const mainContent = document.getElementById('main-content');

        setTimeout(() => {
            if (loadingScreen) {
                loadingScreen.classList.add('hidden');
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                }, 500); // Match CSS transition duration
            }
            if (mainContent) {
                mainContent.classList.remove('loading');
                mainContent.classList.add('loaded');
            }
        }, 500);

    } catch (error) {
        console.error('Error initializing base scripts:', error);
        const loadingScreen = document.getElementById('loading-screen');
        const mainContent = document.getElementById('main-content');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }
        if (mainContent) {
            mainContent.classList.remove('loading');
            mainContent.classList.add('loaded');
        }
    }
}

document.addEventListener('DOMContentLoaded', initializeBaseScripts);