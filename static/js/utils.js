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