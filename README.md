# Escáner de Códigos V&C

## Descripción

Sistema de escaneo y verificación de códigos de barras para control de calidad y cumplimiento de normas mexicanas (NOM) en productos importados.

## Características Principales

- **Escaneo de códigos de barras** en tiempo real
- **Verificación de cumplimiento** de normas NOM
- **Edición de reportes** de mercancía directamente desde la aplicación
- **Interfaz moderna** con tema oscuro y colores corporativos
- **Gestión de archivos** CLP y reportes de mercancía
- **Índice local** para búsquedas rápidas

## Estados de Resultado

La aplicación clasifica los productos en cuatro categorías:

1. **CUMPLE**: Producto que cumple con todas las normas
2. **REQUIERE REVISIÓN**: Algunos criterios cumplen pero otros no, necesita revisión
3. **INSPECCIÓN**: Requiere inspección física
4. **SIN DATOS**: No hay información disponible

## Campos Editables

### Tipo de Proceso
- CUMPLE
- ADHERIBLE
- COSTURA
- SIN NORMA

### Criterio
- REVISADO
- NO CUMPLE
- (vacío)

## Requisitos del Sistema

- Python 3.7 o superior
- Windows 10/11
- Librerías requeridas (ver requirements.txt)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/VandC-stack/Escaner-Simplificado.git
cd Escaner-Simplificado
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```bash
python Escanaer_V0.2.1.py
```

## Uso

### Configuración Inicial
1. Abrir la pestaña "Configuración"
2. Cargar archivo CLP (Contenedor de Línea de Producto)
3. Cargar reporte de mercancía
4. Actualizar índice local

### Escaneo de Productos
1. Ir a la pestaña "Escáner"
2. Introducir código de barras manualmente o escanear
3. Revisar resultados mostrados
4. Opcional: Editar items usando el botón "Editar Items"

### Edición de Reportes
1. Después de escanear, hacer clic en "Editar Items"
2. Modificar Tipo de Proceso y Criterio según sea necesario
3. Guardar cambios (se actualiza el archivo Excel original)

## Estructura del Proyecto

```
Escaner-Simplificado/
├── Escanaer_V0.2.1.py      # Aplicación principal
├── resources/               # Recursos gráficos
│   ├── Logo (2).png
│   ├── logo.png
│   ├── Luna.png
│   └── Sol.png
├── cache/                   # Archivos de configuración
│   ├── config.json
│   └── indice.csv
├── requirements.txt         # Dependencias
└── README.md               # Documentación
```

## Dependencias

- customtkinter
- pandas
- PIL (Pillow)
- openpyxl

## Versión

v0.2.1.5

## Desarrollado por

V&C Stack

## Licencia

Este proyecto es propiedad de V&C Stack. Todos los derechos reservados.
