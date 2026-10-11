# Proyecto de ventas

Aplicación de consola en Python para administrar clientes, productos y ventas.

## Ejecutar

Requiere Python 3. No necesita instalar paquetes adicionales.

Abre una terminal en la carpeta del repositorio y ejecuta:

```bash
cd proyecto_ventas
python main.py
```

En sistemas donde el comando sea `python3`, usa `python3 main.py`.
Ejecuta el programa desde `proyecto_ventas` para guardar los datos en su carpeta `data`.

## Archivos

- `proyecto_ventas/main.py`: vista; menús, entrada de datos y mensajes.
- `proyecto_ventas/views.py`: controladores de clientes, productos y ventas.
- `proyecto_ventas/models.py`: clases `ModeloBase`, `Persona`, `Cliente`, `Producto` y `Venta`.
- `proyecto_ventas/shared/__init__.py`: inicialización del paquete `shared`.
- `proyecto_ventas/shared/herramientas.py`: funciones reutilizables de consola y validación.
- `proyecto_ventas/shared/json_manager.py`: lectura y guardado de archivos JSON.
- `proyecto_ventas/data/clientes.json`: datos de clientes.
- `proyecto_ventas/data/productos.json`: datos de productos.
- `proyecto_ventas/data/ventas.json`: datos de ventas.

Los tres archivos JSON comienzan con una lista vacía. Si faltan, el programa los crea al guardar registros de cada entidad.

El código conserva el comportamiento proporcionado: registrar una venta descuenta stock; anularla devuelve el stock. Las ventas registradas se anulan y se vuelven a registrar cuando se necesita corregirlas.
