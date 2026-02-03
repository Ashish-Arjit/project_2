document.addEventListener('DOMContentLoaded', () => {
    const loginCard = document.getElementById('login-card');
    const signupCard = document.getElementById('signup-card');
    const otpCard = document.getElementById('otp-card');

    const showSignup = document.getElementById('show-signup');
    const showLogin = document.getElementById('show-login');

    const loginBtn = document.getElementById('login-btn');
    const signupBtn = document.getElementById('signup-btn');
    const verifyBtn = document.getElementById('verify-btn');

    const notify = (msg, type = 'info') => {
        const el = document.getElementById('notification');
        el.textContent = msg;
        el.className = `notification ${type}`;
        el.classList.remove('hidden');
        setTimeout(() => el.classList.add('hidden'), 5000);
    };

    // CAPTCHA Management
    const captchaCode = document.getElementById('captcha-code');
    const refreshCaptcha = document.getElementById('refresh-captcha');
    const captchaInput = document.getElementById('login-captcha');

    const getNewCaptcha = async () => {
        try {
            const res = await fetch('/api/get_captcha');
            const data = await res.json();
            captchaCode.textContent = data.captcha;
        } catch (err) {
            captchaCode.textContent = 'ERROR';
        }
    };

    // Load initial captcha
    getNewCaptcha();
    if (refreshCaptcha) refreshCaptcha.onclick = getNewCaptcha;

    // Toggle forms
    showSignup.onclick = (e) => {
        e.preventDefault();
        loginCard.classList.add('hidden');
        signupCard.classList.remove('hidden');
    };

    showLogin.onclick = (e) => {
        e.preventDefault();
        signupCard.classList.add('hidden');
        loginCard.classList.remove('hidden');
    };

    // Login logic
    loginBtn.onclick = async () => {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const captcha = captchaInput ? captchaInput.value : '';

        if (!email || !password || !captcha) return notify('Please fill all fields', 'error');

        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, captcha })
        });

        const data = await res.json();
        if (data.success && data.require_otp) {
            notify(data.message, 'info');
            loginCard.classList.add('hidden');
            otpCard.classList.remove('hidden');
            document.querySelector('#otp-card p').textContent = "Security Check: Enter the code sent to your email.";
        } else if (data.success) {
            window.location.href = '/';
        } else {
            notify(data.message || 'Login failed', 'error');
            getNewCaptcha(); // Refresh captcha on failure
            if (captchaInput) captchaInput.value = '';
        }
    };

    // Signup logic
    signupBtn.onclick = async () => {
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;

        // Policy check client-side
        if (!email.endsWith('.com') && !email.endsWith('.in')) {
            return notify('Email must end with .com or .in', 'error');
        }

        const specialCharRegex = /[!@#$%^&*(),.?\":{}|<>]/;
        if (password.length < 8 || !specialCharRegex.test(password)) {
            return notify('Password must be 8+ chars and have a special char', 'error');
        }

        signupBtn.textContent = 'Sending Code...';
        signupBtn.disabled = true;

        try {
            const res = await fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();
            if (data.success) {
                notify(data.message, 'success');
                signupCard.classList.add('hidden');
                otpCard.classList.remove('hidden');
                document.querySelector('#otp-card p').textContent = "Verify your email to create your account.";
            } else {
                notify(data.message, 'error');
            }
        } finally {
            signupBtn.textContent = 'Sign Up';
            signupBtn.disabled = false;
        }
    };

    // OTP Verification logic
    verifyBtn.onclick = async () => {
        let otp = document.getElementById('otp-input').value;
        if (!otp) return notify('Enter verification code', 'error');

        otp = otp.trim().toUpperCase();

        const res = await fetch('/api/verify_otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ otp })
        });

        const data = await res.json();
        if (data.success) {
            if (data.mode === 'login') {
                window.location.href = '/';
            } else {
                notify(data.message, 'success');
                otpCard.classList.add('hidden');
                loginCard.classList.remove('hidden');
                getNewCaptcha(); // Get fresh captcha for login
            }
        } else {
            notify(data.message, 'error');
        }
    };
});
