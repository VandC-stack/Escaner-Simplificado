# Escáner de Códigos V&C v0.2.1.5

## 🎯 Descripción
Sistema de escaneo y validación de códigos de barras para verificar el cumplimiento de normas mexicanas (NOM) en productos importados. Herramienta de control de calidad para aduanas.

## 🚀 Nuevas Mejoras Implementadas

### 🔍 Búsqueda Mejorada de Códigos
- **Búsqueda Exacta**: Mantiene la funcionalidad original
- **Búsqueda Parcial**: Encuentra códigos que contengan el patrón escaneado
- **Búsqueda por Similitud**: Busca por últimos 8 dígitos cuando no hay coincidencias exactas
- **Indicadores Visuales**: Muestra el tipo de coincidencia encontrada

### 🛠️ Sistema de Diagnóstico
- **Botón de Diagnóstico**: Nueva herramienta para analizar códigos problemáticos
- **Análisis Detallado**: Muestra similitudes y posibles coincidencias
- **Información del Índice**: Estadísticas sobre códigos disponibles

### 🔄 Actualización Automática del Índice
- **Sincronización Mejorada**: El índice se actualiza automáticamente después de editar items
- **Confirmación Visual**: Mensajes de confirmación para el usuario
- **Manejo de Errores**: Mejor robustez en la limpieza de datos

### 🛡️ Robustez Mejorada
- **Limpieza de Datos**: Función mejorada para manejar formatos diversos
- **Manejo de Excepciones**: Mejor control de errores en procesamiento
- **Logging**: Sistema de registro para debugging

## 📋 Funcionalidades Principales

### 1. Escaneo de Códigos
- Entrada de códigos de barras con búsqueda flexible
- Múltiples estrategias de búsqueda
- Indicadores de tipo de coincidencia

### 2. Gestión de Índice
- Actualización desde archivos Excel (CLP y Reporte)
- Verificación de integridad
- Borrado completo del índice

### 3. Editor de Items
- Edición de tipo de proceso y criterio
- Actualización automática del reporte
- Regeneración automática del índice

### 4. Sistema de Diagnóstico
- Análisis de códigos problemáticos
- Búsqueda de similitudes
- Estadísticas del índice

## 🗂️ Estructura de Archivos

```
Escaner 0.2.1.5/
├── Escanaer_V0.2.1.5.py    # Aplicación principal
├── requirements.txt         # Dependencias
├── README.md               # Documentación
├── cache/                  # Directorio de caché
│   ├── config.json        # Configuración
│   └── indice.csv         # Índice generado
└── resources/             # Recursos
    ├── Escaner.ico        # Icono
    └── Logo (2).png       # Logo
```

## 🔧 Instalación

1. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

2. **Ejecutar la aplicación**:
```bash
python Escanaer_V0.2.1.5.py
```

## 📊 Estados de Resultado

- **CUMPLE**: Todos los criterios cumplen las normas
- **REQUIERE REVISIÓN**: Algunos criterios cumplen, otros no
- **INSPECCIÓN**: Ningún criterio cumple las normas
- **SIN DATOS**: No se encontró información en el reporte

## 🎮 Uso de la Aplicación

### Configuración Inicial
1. Ir a la pestaña "Configuración"
2. Cargar archivo CLP (Código de Línea de Producto)
3. Cargar archivo de Reporte de Mercancía
4. Actualizar el índice

### Escaneo de Códigos
1. Ingresar código de barras en el campo de entrada
2. Presionar "Buscar" o Enter
3. Revisar resultados mostrados

### Edición de Items
1. Buscar un código que tenga resultados
2. Hacer clic en "Editar Items"
3. Modificar tipo de proceso y criterio
4. Guardar cambios

### Diagnóstico de Problemas
1. Hacer clic en "Diagnóstico de Código"
2. Ingresar código problemático
3. Revisar análisis detallado

## 🔍 Tipos de Coincidencia

- **Exacta**: Coincidencia perfecta al inicio del código
- **Parcial**: El código escaneado está contenido en el código del índice
- **Final**: Coincidencia por últimos 8 dígitos

## 🚨 Solución de Problemas

### Código no encontrado
1. Usar el botón "Diagnóstico de Código"
2. Verificar que el índice esté actualizado
3. Revisar formato del código escaneado

### Error de actualización
1. Verificar permisos de archivos
2. Asegurar que los archivos Excel no estén abiertos
3. Revisar formato de los archivos

## 📝 Changelog

### v0.2.1.5
- ✅ Búsqueda mejorada con múltiples estrategias
- ✅ Sistema de diagnóstico integrado
- ✅ Actualización automática del índice
- ✅ Mejor manejo de errores y robustez
- ✅ Indicadores visuales de tipo de coincidencia

## 🤝 Soporte

Para reportar problemas o solicitar mejoras, contactar al equipo de desarrollo V&C.
