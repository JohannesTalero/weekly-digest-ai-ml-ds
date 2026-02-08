# Datos del digest

- **`sent-urls.json`**: historial de URLs ya enviadas en digests anteriores. El script lo lee para no reenviar los mismos artículos y lo actualiza tras cada envío; el workflow hace commit de este archivo.

**Primera ejecución:** si el archivo no existe, el script lo trata como lista vacía y lo crea al persistir las URLs del primer envío. No es obligatorio crear este archivo a mano.
