# JSON Reports Tools

Aplicación Streamlit completa para convertir, validar, extraer y visualizar reportes JSON de CPE basada en Broadband Forum Data Models TR-181 y TR-098.

## 🚀 Uso local

```bash
pipenv install
pipenv run streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8504`

## ☁️ Despliegue en Streamlit Cloud

1. Sube el repositorio a GitHub
2. En Streamlit Cloud, selecciona el repo y elige `app.py` como archivo principal
3. Asegúrate de que el archivo `Pipfile` esté presente

---

## 🛠️ Funcionalidades Implementadas

### ✅ Conversión JSON
- **NameValuePair → ObjectHierarchy**: Convierte formato plano a estructura jerárquica
- **ObjectHierarchy → NameValuePair**: Convierte estructura jerárquica a formato plano
- **Validación automática**: Verifica formato JSON antes de procesar
- **Estadísticas detalladas**: Muestra métricas de conversión
- **Muestra de estructura**: Preview del resultado
- **Descarga de resultados**: Exporta archivos JSON convertidos

### ✅ Validación de Métricas
- **Configuraciones predefinidas**: TR-181, TR-098, FWA con reglas YAML
- **Detección automática de formato**: NameValuePair vs ObjectHierarchy
- **Soporte de wildcards**: `%`, `*`, `{i}` para patrones flexibles
- **Conteo de instancias**: Estadísticas de patrones encontrados vs instancias reales
- **Configuraciones personalizadas**: Upload de archivos YAML o editor de texto
- **Resultados detallados**: Métricas encontradas, faltantes y estadísticas

### ✅ Extracción de Métricas
- **Extracción automática**: Convierte instancias específicas a patrones con wildcards
- **Soporte de formatos**: NameValuePair y ObjectHierarchy
- **Categorización**: Agrupa métricas por segundo nivel automáticamente
- **Múltiples salidas**: Lista simple, reglas YAML, documentación Markdown
- **Descarga flexible**: Exporta en diferentes formatos según necesidad
- **Estado persistente**: Mantiene resultados para múltiples descargas

### ✅ Visualización JSON
- **Carga flexible**: Upload de archivos o pegado de texto
- **Búsqueda inteligente**: Filtra claves por nombre con botones de confirmación
- **Estadísticas JSON**: Elementos, claves, profundidad, tamaño
- **Sintaxis highlighting**: JSON formateado con colores
- **Enlace a JSON Crack**: Integración con herramienta de diagramas externos

### ✅ Configuración y Gestión
- **Visor de configuraciones**: Visualización dinámica de archivos YAML
- **Descarga de configuraciones**: Exportar reglas de validación
- **Estadísticas de configuración**: Métricas de reglas y patrones
- **Detección automática**: Escaneo dinámico de archivos en config/

### 🔄 Gestión de Estado
- **Persistencia de datos**: Mantiene conversiones entre sesiones
- **Múltiples descargas**: Descarga con diferentes nombres
- **Control de proceso**: Botones para nueva conversión o volver al inicio
- **Reset completo**: Limpia todo el estado de la aplicación

---

## 🔍 Validación de Métricas

### Configuraciones Disponibles

#### **TR-181 (Device Data Model)**
- **WiFi Radio Statistics**: Bytes sent/received, packets, errors
- **WiFi Data Elements**: BSS/STA information, connection times, data rates
- **WiFi SSID Configuration**: SSID settings, status, layers
- **Device Information**: Serial number, model, versions, uptime
- **Ethernet Interface**: Interface statistics and status
- **IP Interface**: IP configuration and statistics

*Nota: Solo está disponible la configuración TR-181. Las configuraciones TR-098 y FWA pueden ser agregadas según sea necesario.*

### Algoritmo de Validación

#### **Detección de Formato**
```python
# Detecta automáticamente:
NameValuePair: {"Device.WiFi.Radio.1.Stats.BytesSent": 1000}
ObjectHierarchy: {"Device": {"WiFi": {"Radio": {"1": {"Stats": {"BytesSent": 1000}}}}}
```

#### **Patrones con Wildcards**
```yaml
# Ejemplos de patrones soportados:
- "Device.WiFi.Radio.%.Stats.BytesSent"     # % = cualquier valor
- "Device.WiFi.DataElements.%.Radio.%.BSS.%.STA.%.LastConnectTime"
- "InternetGatewayDevice.WANDevice.{i}.WANConnectionDevice.{i}.WANIPConnection.ConnectionStatus"
```

#### **Estadísticas de Validación**
- **Total Expected**: Número de patrones esperados
- **Total Found**: Patrones encontrados (lógica binaria)
- **Total Instances**: Instancias reales encontradas
- **Total Missing**: Patrones no encontrados
- **Success Rate**: Porcentaje de éxito

### Uso de la Validación

1. **Seleccionar "Check Metrics"** en la barra lateral
2. **Cargar JSON**: Upload de archivo o pegar contenido
3. **Elegir configuración**:
   - Usar configuración existente (TR-181, TR-098, FWA)
   - Cargar configuración personalizada (archivo YAML)
   - Crear configuración personalizada (editor de texto)
4. **Validar métricas**: Ejecutar validación
5. **Revisar resultados**: Estadísticas, métricas encontradas y faltantes

---

## 📋 Funcionalidades Pendientes

### 🔧 Mejoras Futuras
- **Validación por categorías**: Estadísticas separadas por tipo de métrica
- **Filtros avanzados**: Filtrar por número de instancias
- **Exportación de resultados**: Descargar reportes de validación
- **Comparación de configuraciones**: Comparar múltiples reglas

---

## 🏗️ Arquitectura

### Estructura del Proyecto
```
json-report-tools/
├── app.py                 # Aplicación principal Streamlit
├── tools/
│   ├── __init__.py
│   ├── json_converter.py  # Lógica de conversión JSON
│   ├── metrics_validator.py # Validación de métricas
│   └── metrics_extractor.py # Extracción de métricas
├── config/               # Archivos de configuración
│   └── wei_tr181_rules.yaml  # Reglas TR-181
├── scripts/              # Scripts de testing y debugging
│   ├── test_conversion.py    # Test de conversión JSON
│   ├── test_validation.py    # Test de validación de métricas
│   ├── test_extraction.py    # Test de extracción de métricas
│   └── run_tests.py         # Runner integrado de tests
├── tests/                # Tests unitarios (pytest)
│   ├── test_json_converter.py
│   ├── test_metrics_validator.py
│   └── test_metrics_extractor.py
├── docs/                # Documentación
├── test/                # Archivos de prueba
├── Pipfile              # Dependencias Python
└── README.md           # Este archivo
```

### Tecnologías Utilizadas
- **Streamlit**: Framework web para la interfaz
- **Pipenv**: Gestión de dependencias Python
- **PyYAML**: Procesamiento de archivos de configuración
- **JSON**: Procesamiento de datos JSON
- **Logging**: Sistema de logs para debugging

---

## 🔍 Extracción de Métricas

### Funcionalidad de Extracción

#### **Proceso de Extracción**
```python
# Input: JSON con instancias específicas
{
  "Device.WiFi.Radio.1.Stats.BytesSent": 1000,
  "Device.WiFi.Radio.2.Stats.BytesSent": 2000,
  "Device.DeviceInfo.SerialNumber": "FVN22"
}

# Output: Patrones con wildcards
[
  "Device.WiFi.Radio.*.Stats.BytesSent",
  "Device.DeviceInfo.SerialNumber"
]
```

#### **Formatos de Salida**

**1. Lista Simple**
```
Device.DeviceInfo.SerialNumber
Device.WiFi.Radio.*.Stats.BytesSent
```

**2. Reglas YAML**
```yaml
name: "Extracted Metrics"
description: "Metrics extracted from JSON data"
version: "1.0"

rules:
  - name: "Device Information"
    description: "Device Information metrics"
    category: "Device Information"
    patterns:
      - "Device.DeviceInfo.SerialNumber"
  - name: "WiFi Radio Statistics"
    description: "WiFi Radio Statistics metrics"
    category: "WiFi Radio Statistics"
    patterns:
      - "Device.WiFi.Radio.*.Stats.BytesSent"
```

**3. Documentación Markdown**
```markdown
# Extracted Metrics

| Metric | TR-181 DataType | Output Type | DB Output Name | Notes |
|---|---|---|---|---|
| `Device.DeviceInfo.SerialNumber` |  |  |  |  |
| `Device.WiFi.Radio.*.Stats.BytesSent` |  |  |  |  |
```

#### **Categorización Automática (Hasta Segundo Nivel) Ejemplos:**
- **Device Information**: Métricas de información del dispositivo (`Device.DeviceInfo`)
- **WiFi Configuration**: Configuración y estadísticas WiFi (`Device.WiFi`)
- **Host Information**: Información de hosts conectados (`Device.Hosts`)
- **Ethernet Interface**: Interfaces Ethernet (`Device.Ethernet`)
- **IP Interface**: Interfaces IP (`Device.IP`)
- **WAN Interface**: Interfaces WAN (`Device.WAN`)
- **LAN Interface**: Interfaces LAN (`Device.LAN`)
- **Management Server**: Configuración del servidor de gestión (`Device.ManagementServer`)
- **Firewall Configuration**: Configuración del firewall (`Device.Firewall`)
- **WAN Device**: Dispositivos WAN (`InternetGatewayDevice.WANDevice`)
- **LAN Device**: Dispositivos LAN (`InternetGatewayDevice.LANDevice`)
- **WAN Connection**: Conexiones WAN (`InternetGatewayDevice.WANConnectionDevice`)
- **LAN Host Config**: Configuración de hosts LAN (`InternetGatewayDevice.LANHostConfigManagement`)
- **Layer 2 Bridging**: Puenteo de capa 2 (`InternetGatewayDevice.Layer2Bridging`)
- **Quality of Service**: Calidad de servicio (`InternetGatewayDevice.QoS`)
- **Upload Diagnostics**: Diagnósticos de subida (`InternetGatewayDevice.UploadDiagnostics`)
- **Download Diagnostics**: Diagnósticos de descarga (`InternetGatewayDevice.DownloadDiagnostics`)

---

## 🎯 Casos de Uso

### Para Técnicos de Campo
1. **Cargar reporte JSON** de dispositivo CPE
2. **Convertir formato** según necesidades del sistema
3. **Validar métricas** contra estándares TR-181/TR-098
4. **Visualizar estructura** para análisis rápido
5. **Buscar claves específicas** en reportes grandes
6. **Exportar resultados** para uso posterior

### Para Desarrolladores
1. **Validar formatos** de entrada y salida
2. **Probar conversiones** con datos reales
3. **Crear configuraciones personalizadas** para validaciones específicas
4. **Analizar estadísticas** de procesamiento y validación
5. **Debuggear problemas** con logs detallados

### Para Analistas de Datos
1. **Validar cumplimiento** de estándares TR-181/TR-098
2. **Identificar métricas faltantes** en reportes de dispositivos
3. **Analizar patrones** de implementación de métricas
4. **Comparar configuraciones** entre diferentes dispositivos

---

## 📚 Documentación

- **PRD**: `docs/json_reports_tools_prd.md` - Especificaciones del producto
- **Reglas de validación**: `config/validation_rules.json` - Configuración de validación
- **Métricas TR-181**: `config/wei_tr181_metrics.md` - Especificaciones de métricas

---

## 🧪 Testing

### Sistema de Testing Completo

#### **Tests Unitarios (pytest)**
```bash
# Ejecutar todos los tests unitarios
pipenv run pytest tests/

# Ejecutar tests específicos
pipenv run pytest tests/test_json_converter.py
pipenv run pytest tests/test_metrics_validator.py

# Con cobertura de código
pipenv run pytest tests/ --cov=tools --cov-report=term-missing
```

#### **Tests de Integración (scripts)**
```bash
# Test de conversión JSON
pipenv run python scripts/test_conversion.py

# Test de validación de métricas
pipenv run python scripts/test_validation.py

# Test de extracción de métricas
pipenv run python scripts/test_extraction.py
```

#### **Runner Integrado**
```bash
# Ejecutar todos los tests (unitarios + integración)
pipenv run python scripts/run_tests.py
```

### Cobertura de Tests

#### **JSON Converter**
- ✅ Conversión ObjectHierarchy → NameValuePair
- ✅ Conversión NameValuePair → ObjectHierarchy
- ✅ Conversión de bytes a string
- ✅ Manejo de errores
- ✅ Estadísticas de conversión

#### **Metrics Validator**
- ✅ Detección de formato (NameValuePair vs ObjectHierarchy)
- ✅ Aplanado de estructuras jerárquicas
- ✅ Patrones con wildcards (%, *, {i})
- ✅ Búsqueda de claves coincidentes

#### **Metrics Extractor**
- ✅ Extracción de métricas desde NameValuePair
- ✅ Extracción de métricas desde ObjectHierarchy
- ✅ Conversión de instancias específicas a patrones con wildcards
- ✅ Categorización automática por segundo nivel
- ✅ Generación de reglas YAML
- ✅ Generación de documentación Markdown
- ✅ Estado persistente para múltiples descargas
- ✅ Estadísticas de extracción
- ✅ Configuraciones personalizadas

---

## 📚 Documentación

- **Reglas de validación**: `config/wei_tr181_rules.yaml` - Configuración de validación TR-181

---

## 🚀 Despliegue

### Local
```bash
pipenv install
pipenv run streamlit run app.py
```

### Streamlit Cloud
1. Sube el repositorio a GitHub
2. En Streamlit Cloud, selecciona el repo y elige `app.py` como archivo principal
3. Asegúrate de que el archivo `Pipfile` esté presente

---

## 📋 Estado del Proyecto

**✅ Completado**: Todas las funcionalidades principales implementadas y probadas
**✅ Testing**: Sistema completo de tests unitarios e integración
**✅ Documentación**: README actualizado con todas las funcionalidades
**✅ Configuración**: Gestión de dependencias con Pipenv

