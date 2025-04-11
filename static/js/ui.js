// Constantes
const API_URL = window.location.origin;

/**
 * Función para cambiar entre pestañas
 * @param {string} tabName - Nombre de la pestaña a mostrar
 */
function openTab(tabName) {
    // Ocultar todos los contenidos de pestañas
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }
    
    // Desactivar todas las pestañas
    const tabs = document.getElementsByClassName('tab');
    for (let i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove('active');
    }
    
    // Mostrar el contenido de la pestaña seleccionada
    document.getElementById(tabName).classList.add('active');
    
    // Activar la pestaña seleccionada
    event.currentTarget.classList.add('active');
    
    // Si se selecciona la pestaña de lista, cargar los códigos QR
    if (tabName === 'list') {
        loadQRCodes();
    }
}

/**
 * Función para generar códigos QR
 * Esta función obtiene los datos del formulario, envía una solicitud a la API
 * para crear un nuevo código QR, y luego genera y muestra el código QR.
 */
async function generarQR() {
    // Obtener datos del formulario
    const valor = document.getElementById("valor").value;
    const estado = document.getElementById("estado").value;
    const cantidad = parseInt(document.getElementById("cantidad").value);
    const filenamePrefix = document.getElementById("filenamePrefix").value;

    // Limpiar el contenedor de códigos QR
    const qrCodesDiv = document.getElementById("qrCodes");
    qrCodesDiv.innerHTML = "";
    
    // Ocultar el botón de descargar todos
    document.getElementById("downloadAllContainer").style.display = "none";
    
    // Almacenar los canvas para descargar todos a la vez
    window.qrCanvases = [];

    // Generar la cantidad especificada de códigos QR
    for (let i = 0; i < cantidad; i++) {
        // Crear la fecha de creación en formato ISO
        const fechaActual = new Date();
        const anio = fechaActual.getFullYear();
        const mes = String(fechaActual.getMonth() + 1).padStart(2, '0');
        const dia = String(fechaActual.getDate()).padStart(2, '0');
        const fechaCreacion = `${anio}-${mes}-${dia}`;

        try {
            // Paso 1: Crear el registro en la base de datos sin imagen
            const createResponse = await fetch(`${API_URL}/api/qrdata`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({ 
                    new_value: parseFloat(valor),
                    old_value: 0.0,
                    creation_date: fechaCreacion + "T00:00:00.000Z", 
                    state: estado
                })
            });

            // Verificar si la solicitud fue exitosa
            if (!createResponse.ok) {
                if (createResponse.status === 401) {
                    window.location.href = '/login.html';
                    return;
                }
                throw new Error(`HTTP error! status: ${createResponse.status}`);
            }

            // Obtener el ID real del QR
            const data = await createResponse.json();
            const qrcode_id = data.qrcode_id;

            if (!qrcode_id) {
                console.error('Error: No se recibió un ID de QR válido');
                continue;
            }

            // Paso 2: Crear contenedor para el código QR
            const qrContainer = document.createElement("div");
            qrContainer.className = "qr-container";

            const qrCodeWrapper = document.createElement("div");
            qrCodeWrapper.className = "qr-code-wrapper";

            // Paso 3: Generar el QR con el ID real
            console.log('Creando QR con ID real:', qrcode_id);
            const qrCode = new QRCode(qrCodeWrapper, {
                text: qrcode_id,
                width: 128,
                height: 128,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });

            // Agregar el canvas al contenedor
            qrCodeWrapper.appendChild(qrCode._el.querySelector("canvas"));
            qrContainer.appendChild(qrCodeWrapper);

            // Agregar el contenedor al div principal
            qrCodesDiv.appendChild(qrContainer);

            // Paso 4: Obtener la imagen del QR en base64
            const canvas = qrCodeWrapper.querySelector("canvas");
            const qrImageBase64 = canvas.toDataURL("image/png");

            // Paso 5: Actualizar el registro con la imagen correcta
            const updateResponse = await fetch(`${API_URL}/api/qrdata/${qrcode_id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    new_value: parseFloat(valor),
                    old_value: 0.0,
                    creation_date: fechaCreacion + "T00:00:00.000Z",
                    state: estado,
                    qr_image: qrImageBase64
                })
            });

            if (!updateResponse.ok) {
                throw new Error(`Error al actualizar la imagen del QR: ${updateResponse.status}`);
            }

            // Agregar el ID del QR debajo del código
            const qrcodeIdText = document.createElement("p");
            qrcodeIdText.textContent = qrcode_id;
            qrContainer.appendChild(qrcodeIdText);

            // Crear botón para descargar la imagen
            const downloadButton = document.createElement("button");
            downloadButton.className = "btn";
            downloadButton.textContent = "Descargar QR";
            downloadButton.style.marginTop = "10px";
            downloadButton.onclick = function() {
                canvas.toBlob(function (blob) {
                    saveAs(blob, `${filenamePrefix}${i + 1}.png`);
                });
            };
            qrContainer.appendChild(downloadButton);

            // Almacenar el canvas para descargar todos a la vez
            window.qrCanvases.push({
                canvas: canvas,
                filename: `${filenamePrefix}${i + 1}.png`
            });
            
            // Mostrar el botón de descargar todos si hay al menos un QR
            document.getElementById("downloadAllContainer").style.display = "block";

            // Mostrar el valor del QR
            const valorElement = document.createElement("p");
            valorElement.textContent = `Valor Nuevo: $${data.new_value.toFixed(2)}`;
            if (data.old_value > 0) {
                valorElement.textContent += ` (Valor Anterior: $${data.old_value.toFixed(2)})`;
            }
            qrContainer.appendChild(valorElement);

            // Mostrar el estado del QR
            const estadoElement = document.createElement("p");
            estadoElement.textContent = `Estado: ${data.state}`;
            qrContainer.appendChild(estadoElement);
        } catch (error) {
            console.error('Error en el proceso de generación del QR:', error);
        }
    }
}

/**
 * Función para obtener información de un código QR
 * Esta función obtiene el ID del código QR del input, envía una solicitud a la API
 * para obtener la información del código QR, y luego muestra la información.
 */
async function obtenerInformacion() {
    // Obtener el ID del código QR del input
    const qrcode_id = document.getElementById('qrcode_id').value;
    
    try {
        // Enviar solicitud a la API para obtener la información del código QR
        const response = await fetch(`${API_URL}/api/qrdata/${qrcode_id}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });

        // Verificar si el código QR no fue encontrado
        if (response.status === 404) {
            document.getElementById('informacionQR').textContent = 'ID no encontrado.';
            return;
        }

        // Verificar si la solicitud fue exitosa
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Obtener los datos de la respuesta
        const data = await response.json();
        
        // Extraer solo los campos específicos que queremos mostrar
        const displayData = {
            qrcode_id: data.qrcode_id,
            new_value: data.new_value,
            old_value: data.old_value,
            state: data.state,
            creation_date: data.creation_date,
            used_date: data.used_date
        };
        
        // Asegurarse de que la imagen tenga el formato correcto
        let imageSrc = data.qr_image;
        if (!imageSrc.startsWith('data:')) {
            imageSrc = `data:image/png;base64,${imageSrc}`;
        }
        console.log(`Formato de imagen para QR ${data.qrcode_id}: ${imageSrc.substring(0, 30)}...`);
        
        // Crear elementos para mostrar la imagen
        const qrImageContainer = document.createElement('div');
        qrImageContainer.className = 'qr-image-container';
        
        const qrImage = document.createElement('img');
        qrImage.src = imageSrc;
        qrImage.alt = 'QR Code Image';
        qrImage.style.maxWidth = '200px';
        
        qrImageContainer.appendChild(qrImage);
        
        // Limpiar el contenedor de información
        const informacionQR = document.getElementById('informacionQR');
        informacionQR.innerHTML = '';
        informacionQR.appendChild(qrImageContainer);
        
        // Mostrar la información del código QR con formato
        const formattedInfo = `
            ID: ${displayData.qrcode_id}
            Valor Nuevo: $${displayData.new_value}
            Valor Anterior: $${displayData.old_value}
            Estado: ${displayData.state}
            Fecha de creación: ${displayData.creation_date}
            Fecha de uso: ${displayData.used_date || 'No usado'}
        `;
        
        const infoText = document.createElement('pre');
        infoText.textContent = formattedInfo;
        informacionQR.appendChild(infoText);
    } catch (error) {
        // Mostrar el error si ocurrió alguno
        document.getElementById('informacionQR').textContent = 'Error: ' + error.message;
    }
}

// Inicializar la interfaz cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// Hacer las funciones disponibles globalmente
window.openTab = openTab;
window.generarQR = generarQR;
window.obtenerInformacion = obtenerInformacion;