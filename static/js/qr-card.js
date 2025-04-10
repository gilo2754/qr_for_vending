class QRCardComponent {
    static createCard(qrData) {
        const { qrcode_id, value, state, creation_date, used_date, qr_image } = qrData;
        const qrCard = document.createElement('div');
        qrCard.className = 'qr-card';
        
        let cardContent = `
            <div class="qr-info">
                <p><strong>ID:</strong> ${qrcode_id}</p>
                <p><strong>Valor:</strong> $${value}</p>
                <p><strong>Estado:</strong> <span class="state-badge state-${state}">${state}</span></p>
                <p><strong>Fecha de creación:</strong> ${formatDateToElSalvador(creation_date)}</p>
                ${used_date ? `<p><strong>Fecha de uso:</strong> ${formatDateToElSalvador(used_date)}</p>` : ''}
            </div>
        `;

        if (qr_image) {
            let imageSrc = qr_image;
            if (!imageSrc.startsWith('data:')) {
                imageSrc = `data:image/png;base64,${imageSrc}`;
            }
            cardContent = `
                <img src="${imageSrc}" alt="QR Code #${qrcode_id}" class="qr-image">
                ${cardContent}
            `;
        }

        qrCard.innerHTML = cardContent;
        return qrCard;
    }
}

// Hacer el componente disponible globalmente
window.QRCardComponent = QRCardComponent; 