class Auth {
    constructor() {
        this.baseUrl = 'http://localhost:8000/api/v1';
        this.tokenKey = 'auth_token';
        this.userKey = 'user_data';
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

    // Store user data in localStorage
    setUserData(userData) {
        localStorage.setItem(this.userKey, JSON.stringify(userData));
    }

    // Get user data from localStorage (accessible on every page)
    getUserData() {
        const data = localStorage.getItem(this.userKey);
        return data ? JSON.parse(data) : null;
    }

    // Clear all auth-related data
    clearAuthData() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    // Login user via /users/token endpoint
    async login(email, password) {
        try {
            // Validate email and password
            this.validateUserData({email, password});

            const response = await fetch(`${this.baseUrl}/users/token`, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({username: email, password})
            });

            if (!response.ok) {
                const {detail} = await response.json();
                throw new Error(detail || 'Login failed');
            }

            const {access_token, username} = await response.json();
            this.setToken(access_token);
            const userData = await this.refreshUserData();
            this.startRefreshTimer();
            return {user: userData, message: 'Login successful'};
        } catch (error) {
            console.error('Login error:', error);
            throw error;
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
        const token = this.getToken();
        if (!token) return null;

        try {
            const response = await fetch(`${this.baseUrl}/users/me`, {
                method: 'GET',
                headers: {'Authorization': `Bearer ${token}`}
            });

            if (!response.ok) {
                this.clearAuthData();
                throw new Error('Failed to refresh user data');
            }

            const userData = await response.json();
            this.setUserData(userData); // Store username, email, phone_number, avatar, id, balance, status
            return userData;
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
    }
}

export default new Auth();