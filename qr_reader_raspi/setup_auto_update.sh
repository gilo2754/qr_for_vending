#!/bin/bash

# Verificar si se está ejecutando como root
if [ "$EUID" -ne 0 ]; then 
    echo "Por favor, ejecuta este script como root (usando sudo)"
    exit 1
fi

# Configurar los scripts
SCRIPTS_DIR="/home/camenjiv/Desktop/qr_for_vending/automa_raspi"
SYSTEMD_DIR="/etc/systemd/system"

# Dar permisos de ejecución a los scripts
chmod +x "$SCRIPTS_DIR/update_and_restart.sh"

# Copiar el servicio systemd
cp "$SCRIPTS_DIR/qr-reader.service" "$SYSTEMD_DIR/"
systemctl daemon-reload

# Configurar el servicio para que inicie con el sistema
systemctl enable qr-reader.service

# Configurar el hook de post-receive en git
HOOK_DIR="/home/camenjiv/Desktop/qr_for_vending/.git/hooks"
cat > "$HOOK_DIR/post-merge" << 'EOF'
#!/bin/bash
/home/camenjiv/Desktop/qr_for_vending/automa_raspi/update_and_restart.sh
EOF

chmod +x "$HOOK_DIR/post-merge"

# Crear archivo de log
touch /var/log/qr_reader_update.log
chown camenjiv:camenjiv /var/log/qr_reader_update.log

echo "Configuración completada. El servicio se iniciará automáticamente después de cada actualización del repositorio."
echo "Para iniciar el servicio ahora, ejecuta: sudo systemctl start qr-reader.service" 