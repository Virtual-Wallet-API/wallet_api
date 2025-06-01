let isInitialized = false;

async function initializeBaseScripts() {
    if (isInitialized) {
        return;
    }
    isInitialized = true;

    const pageContentLoaded = new Promise(resolve => {
        const timeoutId = setTimeout(() => {
            resolve();
        }, 3500);

        document.addEventListener('pageContentLoaded', () => {
            clearTimeout(timeoutId);
            resolve();
        }, {once: true});
    });

    document.getElementById("logout-btn").addEventListener('click', async (e) => {
        e.preventDefault();
        await auth.logout();
        window.location.href = '/fe/';
    })

    try {
        // Base requirements
        if (typeof jQuery === 'undefined' || typeof bootstrap === 'undefined') {
            throw new Error('jQuery or Bootstrap not loaded');
        }

        // Fetch user data early
        if (!userDataLoaded) {
            await auth.refreshUserData()
        }

        await pageContentLoaded;

        // Page loaded
        const loadingScreen = document.getElementById('loading-screen');
        const mainContent = document.getElementById('main-content');

        if (loadingScreen) loadingScreen.classList.add('hidden');
        if (mainContent) {
            mainContent.classList.remove('loading');
            mainContent.classList.add('loaded');
        }

        // Ensure loading screen is removed from DOM after transition
        if (loadingScreen) {
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500); // Match CSS transition duration
        }

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
            // Optionally display an error message in main content
            // mainContent.innerHTML = `<p class="text-danger text-center">Error loading page content.</p>`;
        }
    }
}

initializeBaseScripts();