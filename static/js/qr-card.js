class QRCardComponent {
    static createCard(qrData) {
        const { qrcode_id, new_value, old_value, state, creation_date, used_date, qr_image } = qrData;
        const qrCard = document.createElement('div');
        qrCard.className = 'qr-container';
        
        let cardContent = '';

        // Agregar la imagen QR si existe
        if (qr_image) {
            let imageSrc = qr_image;
            if (!imageSrc.startsWith('data:')) {
                imageSrc = `data:image/png;base64,${imageSrc}`;
            }
            cardContent += `<img src="${imageSrc}" alt="QR Code #${qrcode_id}" class="qr-image">`;
        }

        // Agregar la información del QR
        cardContent += `
            <div class="qr-info">
                <p><strong>QRCODE_ID:</strong> ${qrcode_id}</p>
                <p><strong>Valor Nuevo:</strong> $${new_value}</p>
                ${old_value > 0 ? `<p><strong>Valor Anterior:</strong> $${old_value}</p>` : ''}
                <p><strong>Estado:</strong> <span class="state-badge state-${state}">${state}</span></p>
                <p><strong>Fecha de creación:</strong> ${creation_date}</p>
                ${used_date ? `<p><strong>Fecha de uso:</strong> ${used_date}</p>` : ''}
            </div>
        `;

        qrCard.innerHTML = cardContent;
        return qrCard;
    }
}

// Hacer el componente disponible globalmente
window.QRCardComponent = QRCardComponent; 
