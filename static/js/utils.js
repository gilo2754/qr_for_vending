// Constantes
const TIMEZONE_OFFSET = 6; // El Salvador is UTC-6

// Función para formatear fechas a la zona horaria de El Salvador (UTC-6)
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
        
        // Cargar los códigos QR
        const response = await fetch(`${apiUrl}/api/qrcodes`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        if (!response.ok) {
            throw new Error(`Error al cargar los códigos QR: ${response.status}`);
        }
        const qrCodes = await response.json();

        // Actualizar contadores usando la función de utilidad
        const stats = countQRStats(qrCodes);

        // Actualizar los valores en el DOM
        document.getElementById('valid-count').textContent = stats.valido;
        document.getElementById('used-count').textContent = stats.usado;
        document.getElementById('expired-count').textContent = stats.expirado;
        document.getElementById('invalidated-count').textContent = stats.invalidado;
        document.getElementById('total-count').textContent = stats.total;

        // Mostrar la lista de códigos QR usando el componente
        qrCodes.forEach(qr => {
            const qrCard = QRCardComponent.createCard({
                qrcode_id: qr.qrcode_id,
                value: qr.value,
                state: qr.state,
                creation_date: qr.creation_date,
                used_date: qr.used_date,
                qr_image: qr.qr_image
            });
            qrListElement.appendChild(qrCard);
        });

        loadingElement.style.display = 'none';
    } catch (error) {
        console.error('Error:', error);
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
        loadingElement.style.display = 'none';
    }
}

// Hacer las funciones disponibles globalmente
window.formatDateToElSalvador = formatDateToElSalvador;
window.countQRStats = countQRStats;
window.loadQRCodes = loadQRCodes; 