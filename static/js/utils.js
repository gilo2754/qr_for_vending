// Constantes
const TIMEZONE_OFFSET = 6; // El Salvador is UTC-6

// Función para formatear fechas a la zona horaria de El Salvador (UTC-6)
/*
function formatDateToElSalvador(dateString) {
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            console.error('Fecha inválida:', dateString);
            return 'Fecha inválida';
        }
        
        return date.toLocaleString('es-SV', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZone: 'America/El_Salvador'
        }) + ' (UTC-6)';
    } catch (error) {
        console.error('Error al formatear la fecha:', error);
        return dateString;
    }
}
*/

// Función para contar estadísticas de QRs por estado
function countQRStats(qrCodes) {
    const stats = {
        valido: 0,
        usado: 0,
        expirado: 0,
        invalidado: 0,
        total: qrCodes.length
    };

    qrCodes.forEach(qr => {
        if (stats.hasOwnProperty(qr.state)) {
            stats[qr.state]++;
        } else {
            console.warn(`Estado desconocido: ${qr.state}`);
        }
    });

    return stats;
}

// Función para cargar los códigos QR
async function loadQRCodes() {
    const loadingElement = document.getElementById('loading');
    const errorElement = document.getElementById('error');
    const qrListElement = document.getElementById('qrList');
    const statsContainer = document.querySelector('.stats-container');

    // Mostrar mensaje de carga
    loadingElement.style.display = 'block';
    errorElement.style.display = 'none';
    qrListElement.innerHTML = '';

    try {
        // Obtener la URL base de la API
        const apiUrl = window.location.origin;
        
        // Cargar los códigos QR con paginación
        const response = await fetch(`${apiUrl}/api/qrcodes?skip=${(window.currentPage - 1) * window.itemsPerPage}&limit=${window.itemsPerPage}`, {
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }
            throw new Error(`Error al cargar los códigos QR: ${response.status}`);
        }

        const data = await response.json();
        const qrCodes = Array.isArray(data) ? data : [];

        // Actualizar contadores usando la función de utilidad
        const stats = countQRStats(qrCodes);

        // Actualizar los valores en el DOM
        document.getElementById('valid-count').textContent = stats.valido;
        document.getElementById('used-count').textContent = stats.usado;
        document.getElementById('expired-count').textContent = stats.expirado;
        document.getElementById('invalidated-count').textContent = stats.invalidado;
        document.getElementById('total-count').textContent = stats.total;

        // Actualizar información de paginación
        window.totalItems = stats.total;
        window.totalPages = Math.ceil(window.totalItems / window.itemsPerPage);
        updatePaginationControls();

        // Mostrar la lista de códigos QR usando el componente
        if (qrCodes.length > 0) {
            qrCodes.forEach(qr => {
                try {
                    const qrCard = QRCardComponent.createCard({
                        qrcode_id: qr.qrcode_id,
                        new_value: qr.new_value,
                        old_value: qr.old_value || 0,
                        state: qr.state,
                        creation_date: new Date(qr.creation_date).toLocaleDateString(),
                        used_date: qr.used_date ? new Date(qr.used_date).toLocaleDateString() : null,
                        qr_image: qr.qr_image
                    });
                    qrListElement.appendChild(qrCard);
                } catch (error) {
                    console.error('Error al crear la tarjeta QR:', error);
                }
            });
        } else {
            qrListElement.innerHTML = '<p class="no-results">No se encontraron códigos QR.</p>';
        }

        loadingElement.style.display = 'none';
    } catch (error) {
        console.error('Error:', error);
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
        loadingElement.style.display = 'none';
    }
}

// Función para actualizar los controles de paginación
function updatePaginationControls() {
    document.getElementById('currentPage').textContent = window.currentPage;
    document.getElementById('totalPages').textContent = window.totalPages;
    document.getElementById('prevPage').disabled = window.currentPage <= 1;
    document.getElementById('nextPage').disabled = window.currentPage >= window.totalPages;
}

// Función para cambiar de página
function changePage(delta) {
    const newPage = window.currentPage + delta;
    if (newPage >= 1 && newPage <= window.totalPages) {
        window.currentPage = newPage;
        loadQRCodes();
    }
}

// Función para borrar QRs por estado
async function deleteQRCodesByState(state) {
    if (!confirm(`¿Estás seguro de que deseas borrar todos los códigos QR con estado "${state}"?`)) {
        return;
    }
    
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    
    loading.style.display = 'block';
    error.style.display = 'none';
    
    try {
        const token = getAuthToken();
        const response = await fetch(`${window.location.origin}/api/qrdata/state/${state}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Error al borrar los códigos QR: ${response.status}`);
        }
        
        const result = await response.json();
        alert(result.message);
        
        // Recargar la lista después de borrar
        loadQRCodes();
    } catch (err) {
        error.textContent = err.message;
        error.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
}

// Función para descargar todos los QR generados
function descargarTodos() {
    if (!window.qrCanvases || window.qrCanvases.length === 0) {
        alert('No hay códigos QR para descargar');
        return;
    }

    window.qrCanvases.forEach(({canvas, filename}) => {
        canvas.toBlob(function(blob) {
            saveAs(blob, filename);
        });
    });
}

// Inicializar variables de paginación
window.currentPage = 1;
window.itemsPerPage = 200;
window.totalItems = 0;
window.totalPages = 1;

// Hacer las funciones disponibles globalmente
window.countQRStats = countQRStats;
window.loadQRCodes = loadQRCodes;
window.deleteQRCodesByState = deleteQRCodesByState;
window.descargarTodos = descargarTodos;
window.changePage = changePage;
window.updatePaginationControls = updatePaginationControls; 