// Constantes
const API_URL = window.location.origin;

/**
 * Verifica la autenticación del usuario al cargar la página
 * Redirige a login.html si no hay token
 */
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    displayUserInfo();
}

/**
 * Cierra la sesión del usuario
 * Elimina el token y la información del usuario del localStorage
 * Redirige a login.html
 */
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_full_name');
    localStorage.removeItem('user_role');
    window.location.href = '/login.html';
}

/**
 * Muestra la información del usuario en la interfaz
 * Obtiene el nombre completo y rol del localStorage
 */
function displayUserInfo() {
    const fullName = localStorage.getItem('user_full_name');
    const role = localStorage.getItem('user_role');
    document.getElementById('userFullName').textContent = fullName;
    document.getElementById('userRole').textContent = `(${role})`;
}

/**
 * Obtiene el token de autenticación del localStorage
 * @returns {string} Token de autenticación
 */
function getAuthToken() {
    return localStorage.getItem('access_token');
}

/**
 * Alterna entre los formularios de login y registro
 */
function toggleForms() {
    const loginContainer = document.querySelector('.login-container');
    const registerContainer = document.querySelector('.register-container');
    
    if (loginContainer.style.display === 'none') {
        loginContainer.style.display = 'block';
        registerContainer.style.display = 'none';
    } else {
        loginContainer.style.display = 'none';
        registerContainer.style.display = 'block';
    }
}

/**
 * Maneja el inicio de sesión del usuario
 * @param {Event} event - Evento del formulario
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('loginError');

    try {
        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                'username': username,
                'password': password
            })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_full_name', data.full_name);
            localStorage.setItem('user_role', data.role);
            window.location.href = '/';
        } else {
            errorMessage.textContent = 'Usuario o contraseña incorrectos';
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        errorMessage.textContent = 'Error de conexión. Por favor, intente nuevamente.';
        errorMessage.style.display = 'block';
    }
}

/**
 * Maneja el registro de un nuevo usuario
 * @param {Event} event - Evento del formulario
 */
async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    const fullName = document.getElementById('regFullName').value;
    const role = document.getElementById('regRole').value;
    const errorMessage = document.getElementById('registerError');
    const successMessage = document.getElementById('registerSuccess');

    // Ocultar mensajes anteriores
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                full_name: fullName,
                role: role
            })
        });

        if (response.ok) {
            successMessage.textContent = 'Registro exitoso. Ahora puedes iniciar sesión.';
            successMessage.style.display = 'block';
            document.getElementById('registerForm').reset();
            
            // Cambiar al formulario de login después de 2 segundos
            setTimeout(() => {
                toggleForms();
            }, 2000);
        } else {
            const data = await response.json();
            errorMessage.textContent = data.detail || 'Error en el registro. Por favor, intente nuevamente.';
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        errorMessage.textContent = 'Error de conexión. Por favor, intente nuevamente.';
        errorMessage.style.display = 'block';
    }
}

// Inicializar los formularios cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

// Hacer las funciones disponibles globalmente
window.checkAuth = checkAuth;
window.logout = logout;
window.displayUserInfo = displayUserInfo;
window.getAuthToken = getAuthToken;
window.toggleForms = toggleForms;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister; 