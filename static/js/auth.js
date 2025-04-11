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

// Hacer las funciones disponibles globalmente
window.checkAuth = checkAuth;
window.logout = logout;
window.displayUserInfo = displayUserInfo;
window.getAuthToken = getAuthToken; 