let userData = {};
let userDataLoaded = false;
let token = null;

class Auth {
    constructor() {
        this.baseUrl = '/api/v1';
        this.tokenKey = 'access_token';
        this.userKey = 'user_data';
        this.lastRefreshKey = 'last_user_data_refresh';
        this.refreshInterval = 15 * 60 * 1000; // Refresh every 15 minutes
        this.refreshTimer = null;
    }

    // Validate user data for create/update
    validateUserData({username, password, email, phone_number}) {
        // Username: 3-20 alphanumeric characters
        if (username && !/^[a-zA-Z0-9]{3,20}$/.test(username)) {
            throw new Error('Username must be 3-20 alphanumeric characters');
        }

        // Password: at least 8 characters, one uppercase, one number, one special character
        if (password && !/^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,}$/.test(password)) {
            throw new Error('Password must be at least 8 characters long, with one uppercase letter, one number, and one special character');
        }

        // Email: valid email format
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            throw new Error('Invalid email format');
        }

        // Phone number: 10 digits
        if (phone_number && !/^\d{10}$/.test(phone_number)) {
            throw new Error('Phone number must be a 10-digit number');
        }

        return true;
    }

    // Store token in localStorage
    setToken(token) {
        localStorage.setItem(this.tokenKey, token);
    }

    // Get token from localStorage
    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    // Store last refresh timestamp
    setLastRefreshTimestamp() {
        localStorage.setItem(this.lastRefreshKey, Date.now().toString());
    }

    // Get last refresh timestamp
    getLastRefreshTimestamp() {
        const timestamp = localStorage.getItem(this.lastRefreshKey);
        return timestamp ? parseInt(timestamp) : 0;
    }

    // Store user data in global userData variable
    setUserData(uData) {
        userData.id = uData.id;
        userData.username = uData.username;
        userData.balance = uData.balance;
        userData.avatar = uData.avatar;
        userData.status = uData.status;
        localStorage.setItem(this.userKey, JSON.stringify(userData));
    }

    // Get user data from global userData variable
    getUserData() {
        return localStorage.getItem(this.userKey) ? JSON.parse(localStorage.getItem(this.userKey)) : null;
    }

    loggedIn() {
        return localStorage.getItem(this.tokenKey) ? true : false;
    }

    // Clear all auth-related data
    clearAuthData() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        localStorage.removeItem(this.lastRefreshKey); // Clear timestamp
        userData = {};
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    // Login user via /users/token endpoint
    async login(username, password) {
        try {
            const response = await fetch(`${this.baseUrl}/users/token`, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({username: username, password})
            });

            if (!response.ok) {
                const {detail} = await response.json();
                throw new Error(detail || 'Failed: ' + response.statusText);
            }
            const responseData = await response.json();
            console.log(responseData);

            // const {access_token, token_type, username} = responseData;
            this.setToken(responseData.access_token);
            const userData = await this.refreshUserData();
            this.startRefreshTimer();
            return {success: true, message: 'Login successful'};
        } catch (error) {
            console.error('Login error:', error);
            return {success: false, message: error.message};
        }
    }

    // Register user via /users/ endpoint
    async register(userData) {
        try {
            const {username, email, phone_number, password} = userData;

            // Validate all fields for registration
            this.validateUserData({username, email, phone_number, password});

            // Ensure all required fields are present
            if (!username || !email || !phone_number || !password) {
                throw new Error('All fields (username, email, phone_number, password) are required');
            }

            const payload = {username, email, phone_number, password};
            const response = await fetch(`${this.baseUrl}/users/`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const {detail} = await response.json();
                throw new Error(detail || 'Registration failed');
            }

            const user = await response.json();
            return {user, message: 'Registration successful, please log in'};
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }

    // Update user information (email, phone_number, avatar)
    async updateUserInfo({email, phone_number, avatar}) {
        const token = this.getToken();
        if (!token) throw new Error('No token found');

        try {
            // Validate provided fields
            this.validateUserData({email, phone_number});

            const payload = {email, phone_number, avatar};
            // Remove undefined or null fields
            Object.keys(payload).forEach(key => payload[key] === undefined || payload[key] === null ? delete payload[key] : {});

            if (Object.keys(payload).length === 0) {
                throw new Error('At least one field (email, phone_number, avatar) must be provided');
            }

            const response = await fetch(`${this.baseUrl}/users/me`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const {detail} = await response.json();
                throw new Error(detail || 'Failed to update user information');
            }

            const userData = await response.json();
            this.setUserData(userData);
            return {user: userData, message: 'User information updated successfully'};
        } catch (error) {
            console.error('Update user info error:', error);
            throw error;
        }
    }

    // Check if token exists
    hasToken() {
        return !!this.getToken();
    }

    // Verify token validity
    async verifyToken() {
        const token = this.getToken();
        if (!token) return false;

        try {
            const response = await fetch(`${this.baseUrl}/users/me`, {
                method: 'GET',
                headers: {'Authorization': `Bearer ${token}`}
            });

            if (!response.ok) {
                this.clearAuthData();
                return false;
            }

            return true;
        } catch (error) {
            console.error('Token verification error:', error);
            this.clearAuthData();
            return false;
        }
    }

    // Refresh user data via /users/me
    async refreshUserData() {
        if (!this.getToken()) {
            console.warn('No token found, skipping user data refresh.');
            this.clearAuthData();
            return null;
        }

        // Check if 5 minutes have passed since last refresh
        const now = Date.now();
        const lastRefresh = this.getLastRefreshTimestamp();
        const fiveMinutes = 5 * 60 * 1000; // 5 minutes in milliseconds
        if (lastRefresh && now - lastRefresh < fiveMinutes) {
            this.setUserData(this.getUserData())
            token = this.getToken();
            console.log('Skipping refresh, less than 5 minutes since last refresh.');
            return true;
        }

        try {
            const response = await fetch(`${this.baseUrl}/users/me`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({detail: 'Failed to parse error response from server.'}));
                console.error('Failed to fetch user data:', response.status, errorData);
                if (response.status === 401 || response.status === 403) {
                    this.clearAuthData();
                    return null;
                }
                throw new Error(errorData.detail || `HTTP error ${response.status}`);
            }

            const udata = await response.json();
            if (!udata || typeof udata.username !== 'string') {
                console.error('Invalid user data structure received:', udata);
                throw new Error('Invalid user data format.');
            }

            if (userDataLoaded && udata.username !== userData.username) {
                console.log("User data changed, clearing auth data.");
                this.clearAuthData();
                window.location.reload();
                return null;
            }

            userData = {
                username: udata.username,
                id: udata.id,
                email: udata.email,
                phone: udata.phone_number,
                balance: parseFloat(udata.balance).toFixed(2),
                avatar: udata.avatar,
                status: udata.status
            };
            this.setUserData(userData);
            this.setLastRefreshTimestamp(); // Update timestamp after successful refresh
            userDataLoaded = true;

            console.log(`User data successfully fetched for ${userData.username}.`);
            return true;
        } catch (error) {
            console.error('Refresh user data error:', error);
            return null;
        }
    }

    // Start periodic refresh timer
    startRefreshTimer() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            this.refreshUserData();
        }, this.refreshInterval);
    }

    // Event-based refresh
    async refreshOnEvent() {
        return await this.refreshUserData();
    }

    // Logout user
    logout() {
        this.clearAuthData();
        window.location.reload();
    }
}

// export default new Auth();
const auth = new Auth();

async function refreshUserData() {
    if (!userData.username) {
        console.log("Loading user data");
    } else {
        console.log(`Checking refresh for ${userData.username}.`);
    }

    let refresh = await auth.refreshUserData();
    if (!refresh) {
        console.log('Failed to refresh user data.');
        auth.clearAuthData();
    } else {
        console.log('User data checked or fetched.');
    }
}

if (typeof preventAuth === 'undefined') {
    window.preventAuth = false;
}

if (!preventAuth) {
    if (!auth.loggedIn()) {
        console.log("Not logged in.")
        window.location.href = '/login';
    }
    refreshUserData();
}

console.log("Auth.js load completed.")