# Documentación Técnica y Manual de Usuario: Sistema de Gestión Farmacia CUCEI (v3.0)

**Asignatura:** Calidad de Software — Sexto Semestre  
**Lenguaje y Tecnologías:** Python 3.13+ | Tkinter (ttk) | MySQL / MariaDB | FPDF2 (CFDI 4.0) | Google Gemini AI | SMTP Async

---

## Índice
1. [Descripción General del Sistema](#1-descripción-general-del-sistema)
2. [Arquitectura del Software](#2-arquitectura-del-software)
3. [Estructura de Directorios y Archivos](#3-estructura-de-directorios-y-archivos)
4. [Diseño de Base de Datos (Modelo Relacional)](#4-diseño-de-base-de-datos-modelo-relacional)
5. [Descripción Detallada de Módulos y Funcionalidades](#5-descripción-detallada-de-módulos-y-funcionalidades)
6. [Cumplimiento Fiscal SAT México (CFDI 4.0)](#6-cumplimiento-fiscal-sat-méxico-cfdi-40)
7. [Instalación, Configuración y Ejecución](#7-instalación-configuración-y-ejecución)
8. [Manual de Usuario y Flujo de Navegación UX](#8-manual-de-usuario-y-flujo-de-navegación-ux)
9. [Aseguramiento de Calidad de Software (SQA) y Pruebas Unitarias](#9-aseguramiento-de-calidad-de-software-sqa-y-pruebas-unitarias)

---

## 1. Descripción General del Sistema

El **Sistema de Gestión Farmacia CUCEI** es una plataforma integral de Punto de Venta (POS), control de inventario multi-sucursal, facturación electrónica **CFDI 4.0 (Anexo 20 SAT México)**, abastecimiento automatizado con proveedores y asesoría farmacéutica asistida por **Inteligencia Artificial (Google Gemini)**.

### Características Principales
- **Operación Multi-Sucursal**: Aislamiento de inventarios, ventas, compras, facturas y reportes por sucursal activa, con cambio dinámico desde el Login o el Panel Principal.
- **Control de Acceso Basado en Roles (RBAC)**:
  - **Vendedor**: Acceso a Punto de Venta (POS), Asistente Farmacéutico IA y Gestión de Clientes.
  - **Gerente**: Acceso adicional a Inventario de Productos, Compras a Proveedores, Historial de Facturas y Centro de Reportes.
  - **Administrador (`Admin` / `Administrador`)**: Acceso total incluyendo Directorio de Proveedores, Administración de Usuarios/Roles y Gestión de Sucursales.
- **Experiencia de Usuario (UX) en Ventana Completa**: Todas las vistas se abren maximizadas e integran una **Barra de Navegación Rápida** superior para cambiar entre módulos con un solo clic y atajos de teclado (`Enter`, `Esc`, `Supr`).
- **Operaciones de Red Asíncronas (`threading`)**: El envío de facturas por correo al cliente, los pedidos por correo a proveedores y las consultas a la IA de Gemini se ejecutan en hilos secundarios sin bloquear la interfaz gráfica.

---

## 2. Arquitectura del Software

El sistema implementa una **Arquitectura Modular por Capas con Servicios Transversales**, separando la interfaz gráfica (`*_view.py`), la lógica de validación y servicios (`Recursos/Servicios/`, `factura.py`, `email_service.py`) y el acceso a datos (`db*.py`).

```
+-----------------------------------------------------------------------------------+
|                        CAPA DE PRESENTACIÓN (Tkinter / ttk)                       |
|  Login-menu.py (Login + Dashboard) | venta_view | compra_view | producto_view     |
|  cliente_view | proveedor_view | usuario_view | Sucursales_view | facturas_view   |
|  reportes_view | estilo.py (Sistema de Diseño WCAG AA + Barra Navegación Rápida)  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        CAPA DE SERVICIOS Y REGLAS DE NEGOCIO                      |
|  - contexto_sucursal.py : Persistencia segura UTF-8/Latin-1 de sucursal.json      |
|  - validaciones.py      : Validación de tipos, correo, teléfono y puntos/descuento|
|  - factura.py           : Motor PDF CFDI 4.0 (UUID, Sellos, QR, Importe en Letra) |
|  - email_service.py     : Cliente SMTP Asíncrono (Hilos daemon en segundo plano)  |
|  - Gemini AI Client     : Asistente Farmacéutico contextualizado con inventario   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                       CAPA DE ACCESO A DATOS (DAOs / Repositorios)                |
|  dbVenta | dbCompra | dbProducto | dbCliente | DBProveedor | dbUsuario            |
|  dbSucursal | dbFacturas | dbReportes  -->  Recursos/conexion.py (.env + MySQL)   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                         BASE DE DATOS RELACIONAL (MySQL / MariaDB)                |
|                                   dbfarmacia                                      |
+-----------------------------------------------------------------------------------+
```

---

## 3. Estructura de Directorios y Archivos

```text
Farmacia-main/
├── Login-menu.py                              # Punto de entrada: Login y Dashboard Principal
├── Ejecutable.bat                             # Lanzador automático (gestiona venv e inicia la app)
├── requirements.txt                           # Dependencias del proyecto (fpdf2, mysql, genai, dotenv)
├── Base de datos farmacia (plantilla).sql     # Script DDL de creación de base de datos MySQL
├── DOCUMENTACION.md                           # Documentación técnica y manual de usuario
├── Notas del parche.txt                       # Historial de versiones y mejoras
├── Facturas/                                  # Repositorio local de PDFs generados (CFDI 4.0)
│   ├── Ventas/
│   └── Compras/
├── tests/
│   └── test_calidad_farmacia.py               # Suite de 12 pruebas unitarias automatizadas
└── Recursos/
    ├── conexion.py                            # Gestor de conexión a MySQL parametrizable por .env
    ├── estilo.py                              # Sistema de diseño UI/UX, paleta y barra de navegación
    ├── sucursal.json                          # Estado persistente de la sucursal activa
    ├── Logo.png                               # Logotipo institucional
    ├── Servicios/
    │   ├── contexto_sucursal.py               # Lectura/escritura segura de sucursal activa
    │   └── validaciones.py                    # Validadores de negocio y cálculo de fidelidad
    └── Menus/
        ├── Clientes/
        │   ├── cliente_view.py                # Vista CRUD de clientes con Treeview y búsqueda
        │   └── dbCliente.py                   # DAO de clientes
        ├── Compras/
        │   ├── compra.py                      # Entidad Compra
        │   ├── compra_view.py                 # Vista de órdenes de compra a proveedor
        │   ├── dbCompra.py                    # DAO transaccional de compras
        │   └── email_service.py               # Servicio SMTP asíncrono (facturas y pedidos)
        ├── Facturas/
        │   ├── facturas_view.py               # Visor de historial de facturas y desglose por folio
        │   └── dbFacturas.py                  # DAO de consulta de facturas emitidas
        ├── Productos/
        │   ├── producto_view.py               # Vista de inventario con alertas de stock bajo
        │   └── dbproducto.py                  # DAO de productos filtrado por sucursal
        ├── Proveedores/
        │   ├── proveedor.py                   # Entidad Proveedor
        │   ├── proveedor_view.py              # Vista CRUD de proveedores
        │   └── dbproveedor.py                 # DAO de proveedores
        ├── Reportes/
        │   ├── reportes_view.py               # Centro de 6 reportes estadísticos + exportación CSV
        │   └── dbReportes.py                  # Consultas analíticas SQL agrupadas
        ├── Sucursales/
        │   ├── Sucursales_view.py             # Vista CRUD de sucursales
        │   └── dbSucursal.py                  # DAO de sucursales
        ├── Usuarios/
        │   ├── usuario_view.py                # Vista CRUD de usuarios y asignación de roles
        │   └── dbUsuario.py                   # DAO de autenticación y hash SHA-256
        └── Ventas/
            ├── venta_view.py                  # Punto de Venta (POS) + Chat Asistente IA Gemini
            ├── dbVenta.py                     # DAO transaccional de ventas y puntos
            ├── factura.py                     # Generador PDF con formato fiscal CFDI 4.0 (SAT)
            └── Gemini_api.env.example         # Plantilla para clave de API de Google Gemini
```

---

## 4. Diseño de Base de Datos (Modelo Relacional)

La base de datos `dbfarmacia` en MySQL / MariaDB está compuesta por **8 tablas relacionales** con integridad referencial:

| Tabla | Clave Primaria | Claves Foráneas / Relaciones | Propósito |
| :--- | :--- | :--- | :--- |
| **`sucursales`** | `id` (AUTO_INCREMENT) | — | Catálogo de sucursales físicas (`direccion`). |
| **`usuarios`** | `id` (AUTO_INCREMENT) | `sucursal_id` $\rightarrow$ `sucursales(id)` | Empleados, credenciales (soporte hash SHA-256) y `rol`. |
| **`clientes`** | `id` (AUTO_INCREMENT) | — | Clientes, `telefono`, `correo`, `rfc`, `ciudad` y `puntos`. |
| **`proveedores`** | `id` (AUTO_INCREMENT) | — | Laboratorios y distribuidores (`nombre`, `telefono`, `correo`, `direccion`). |
| **`productos`** | `id` (AUTO_INCREMENT) | `id_proveedor` $\rightarrow$ `proveedores(id)`<br>`sucursal_id` $\rightarrow$ `sucursales(id)` | Inventario por sucursal, `precio_compra`, `precio_venta`, `stock` y `receta` (`0`/`1`). |
| **`ventas`** | `(id, id_producto)` | `id_cliente` $\rightarrow$ `clientes(id)`<br>`id_producto` $\rightarrow$ `productos(id)`<br>`sucursal_id` $\rightarrow$ `sucursales(id)` | Partidas de cada ticket de venta (`cantidad`, `total`, `fecha`). |
| **`compras`** | `(id, id_producto)` | `id_producto` $\rightarrow$ `productos(id)`<br>`id_proveedor` $\rightarrow$ `proveedores(id)`<br>`sucursal_id` $\rightarrow$ `sucursales(id)` | Partidas de cada orden de compra (`cantidad`, `precio_compra`, `fecha`). |
| **`facturas`** | `id` (AUTO_INCREMENT) | `sucursal_id` $\rightarrow$ `sucursales(id)` | Bitácora fiscal de comprobantes emitidos (`tipo`: Venta/Compra, `id_referencia`, `fecha`). |

---

## 5. Descripción Detallada de Módulos y Funcionalidades

### 5.1 Inicio de Sesión y Gestión de Sucursal Activa (`Login-menu.py`)
- Permite seleccionar la **Sucursal Activa** antes de iniciar sesión.
- Incluye botón **Ver / Ocultar contraseña** y navegación por teclado con `Enter`.
- Soporta contraseñas cifradas con **SHA-256** y mantiene retrocompatibilidad con usuarios preexistentes.

### 5.2 Punto de Venta (POS) y Programa de Lealtad (`venta_view.py`, `dbVenta.py`)
- **Regla de Negocio de Puntos**:
  - Al seleccionar un cliente, muestra sus puntos actuales.
  - Si el cliente tiene **$\ge 50$ puntos**, aplica automáticamente un **10% de descuento** en tiempo real en el desglose inferior y reinicia sus puntos a `0` al confirmar la venta.
  - Si tiene **$< 50$ puntos** y la compra supera **$500.00 MXN**, acumula **+10 puntos**.
- **Control Sanitario de Recetas**: Si un medicamento tiene activo el campo `receta = 1`, solicita confirmación obligatoria de presentación de receta médica antes de agregarlo al carrito.
- **Asistente Farmacéutico IA (Gemini)**: Ventana de consulta en tiempo real que recibe en su prompt de sistema el catálogo y stock real de la sucursal activa para recomendar productos disponibles.

### 5.3 Gestión de Inventario con Alertas Visuales (`producto_view.py`, `dbproducto.py`)
- Filtra y registra productos asignando automáticamente el `sucursal_id` activo.
- Calcula en vivo el **Valor Total del Stock** (`precio_venta * stock`).
- **Alerta de Stock Crítico**: Todas las filas con `stock <= 5` se resaltan automáticamente en color rojo suave en la tabla `Treeview`.

### 5.4 Compras a Proveedores y Notificación Automática (`compra_view.py`, `dbCompra.py`)
- Permite armar un pedido con productos de uno o varios proveedores.
- Al confirmar la orden:
  1. Incrementa el `stock` de los productos en la sucursal activa.
  2. Registra el folio en `compras` y en `facturas`.
  3. Genera el PDF fiscal de la orden de compra en `Facturas/Compras/`.
  4. Agrupa los productos por proveedor y envía automáticamente un correo electrónico de solicitud a cada proveedor en segundo plano.

### 5.5 Historial y Visor de Facturas (`facturas_view.py`, `dbFacturas.py`)
- Consulta maestra-detalle de todas las facturas emitidas en la sucursal, con filtro por tipo (`Todas`, `Venta`, `Compra`).
- Al seleccionar una factura en la tabla superior, la tabla inferior despliega los productos, cantidades y montos de ese folio.
- Incluye botón directo para abrir la carpeta local de archivos PDF en el Explorador de Windows.

### 5.6 Centro de Reportes y Exportación a CSV (`reportes_view.py`, `dbReportes.py`)
Incluye **6 reportes analíticos** y exportación directa a archivo **CSV (compatible con Excel con codificación `utf-8-sig`)**:
1. **Clientes por Ciudad**
2. **Ventas por Fecha (N° de Tickets e Ingresos)**
3. **Compras por Fecha (N° de Órdenes y Egresos)**
4. **Facturas con Mayores Ventas (Agrupadas por Folio y Cliente)**
5. **Productos Más Vendidos (Ranking por Unidades e Ingresos)**
6. **Alerta de Stock Crítico ($\le 5$ unidades)**

---

## 6. Cumplimiento Fiscal SAT México (CFDI 4.0)

El módulo `Recursos/Menus/Ventas/factura.py` genera documentos PDF con el estándar de representación impresa del **Anexo 20 del SAT (CFDI Versión 4.0)**:

- **Datos del Emisor**: RFC (`FCU2109158A1`), Razón Social (`FARMACIAS CUCEI S.A. DE C.V.`), Régimen Fiscal (`601 - General de Ley Personas Morales`), Lugar de Expedición (C.P. extraído de la sucursal) y No. de Certificado CSD.
- **Datos del Receptor**:
  - Si el cliente cuenta con RFC válido (12 o 13 caracteres), se incluye su RFC, Régimen Fiscal (`612` o `601`), Domicilio Fiscal (C.P.) y Uso del CFDI (`G03 - Gastos en general`).
  - Si no cuenta con RFC, se emite con el RFC genérico oficial del SAT para público en general (`XAXX010101000`), Régimen `616 - Sin obligaciones fiscales` y Uso `S01 - Sin efectos fiscales`.
- **Conceptos Estructurados**: `ClaveProdServ` (`51101500`), `Cantidad`, `ClaveUnidad` (`H87 - Pieza`), `Descripción`, `Valor Unitario (Base)`, `Objeto de Impuesto` (`02 - Sí objeto de impuesto`), `Impuesto` (`002 - IVA`) e `Importe`.
- **Desglose Fiscal y Letra**: Conversión automática del total a **Importe con Letra en Pesos Mexicanos (`M.N.`)**, Subtotal Base, Descuento, **IVA Trasladado (Tasa 0.160000 / 16%)** y Total.
- **Timbre Fiscal Digital (TFD)**: Folio Fiscal **UUID v4**, Fecha/Hora de Certificación ISO-8601, **Código QR vectorial de verificación SAT**, **Sello Digital del CFDI**, **Sello Digital del SAT** y **Cadena Original del Complemento de Certificación Digital del SAT**.

---

## 7. Instalación, Configuración y Ejecución

### Requisitos Previos
1. **Windows 10 / 11** con **Python 3.10 a 3.13+** instalado.
2. **Servidor MySQL / MariaDB** activo (por ejemplo, mediante **XAMPP** en el puerto `3306`).
3. Base de datos `dbfarmacia` importada desde el archivo `Base de datos farmacia (plantilla).sql`.

### Ejecución Automática (Recomendada)
Haz doble clic sobre **`Ejecutable.bat`**. El script realiza automáticamente:
1. Verificación o creación limpia del entorno virtual en la carpeta `Librerias/`.
2. Comprobación e instalación de las dependencias de `requirements.txt` (`fpdf2`, `mysql-connector-python`, `google-genai`, `python-dotenv`).
3. Inicio de la aplicación en ventana completa (`Login-menu.py`).

### Configuración Opcional de Variables de Entorno
- **IA Gemini**: Crea el archivo `Recursos/Menus/Ventas/Gemini_api.env` con tu clave:
  ```env
  gemini_api=TU_API_KEY_DE_GEMINI
  ```
- **Base de Datos / SMTP** (Opcional en `.env` en la raíz):
  ```env
  DB_HOST=localhost
  DB_USER=root
  DB_PASSWORD=
  DB_NAME=dbfarmacia
  DB_PORT=3306
  ```

---

## 8. Manual de Usuario y Flujo de Navegación UX

### Credenciales de Acceso
| Usuario | Contraseña | Rol | Alcance |
| :--- | :--- | :--- | :--- |
| **`admin`** | **`123`** | Admin Maestro | Funciona en cualquier sucursal seleccionada |
| **`prueba`** | **`123`** | Administrador | Asignado a la Sucursal 1 |
| **`prueba2`** | **`1234`** | Administrador | Asignado a la Sucursal 2 |

### Atajos de Teclado y Navegación Rápida
- **Ventana Completa Automática**: Todas las secciones se abren maximizadas para aprovechar toda la pantalla.
- **Barra Superior de Navegación Rápida**: Dentro de cualquier módulo encontrarás en la parte superior los botones de todas las pestañas disponibles para saltar directamente de una sección a otra sin regresar al menú.
- **`Enter`**:
  - En Login: Avanza de Usuario a Contraseña e inicia sesión.
  - En Ventas y Compras: Estando en el campo *Cantidad*, agrega inmediatamente el producto al carrito.
- **`Supr` (`Delete`)**: En las tablas de carrito de Ventas y Compras, elimina el producto seleccionado.
- **`Esc`**: Cierra la pestaña actual y regresa al Menú Principal.

---

## 9. Aseguramiento de Calidad de Software (SQA) y Pruebas Unitarias

El proyecto cuenta con una suite de **12 pruebas unitarias automatizadas** en `tests/test_calidad_farmacia.py` construida con `unittest` y `unittest.mock`, que verifica:

1. **Validaciones de Entrada (`TestValidaciones`)**:
   - Números enteros positivos y manejo de cero en stock vs. cantidades de venta.
   - Números decimales positivos y redondeo a 2 decimales en precios.
   - Formato de correo electrónico y longitud de teléfonos (7 a 15 dígitos).
   - Regla de negocio de puntos de fidelidad (descuento del 10% con $\ge 50$ puntos y acumulación de +10 puntos en compras $> \$500$).
2. **Persistencia y Codificación de Configuración (`TestContextoSucursal`)**:
   - Lectura y escritura de `sucursal.json` con IDs de múltiples dígitos.
   - Recuperación automática ante archivos codificados en `Latin-1 / CP1252` con caracteres acentuados y normalización a `UTF-8`.
3. **Integridad de DAOs y Seguridad (`TestDAOsYSeguridad`)**:
   - Hash determinista `SHA-256` compatible con columnas `VARCHAR(50)`.
   - Verificación de que `dbSucursal.eliminar()` ejecute `DELETE FROM sucursales`.
   - Verificación de que `dbProducto.insertar()` inyecte el `sucursal_id` activo.
   - Verificación de que `DBProveedor.insertar()` persista el campo `direccion`.
4. **Generación de Comprobantes Fiscales CFDI 4.0 (`TestGeneracionFacturasPDF`)**:
   - Generación sin errores y sin bloqueo de interfaz gráfica de los PDFs de venta (con datos fiscales de cliente) y de compra.

### Cómo ejecutar las pruebas unitarias
Desde la terminal en la raíz del proyecto:
```powershell
.\Librerias\Scripts\python.exe -m unittest discover -s tests -v
```
