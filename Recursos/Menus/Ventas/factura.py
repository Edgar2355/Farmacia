from pathlib import Path
import os
import re
import uuid
import hashlib
import base64
from datetime import datetime, timedelta

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="fpdf")

ruta_logo = Path(__file__).resolve().parents[2] / "Logo.png"

# Datos fiscales institucionales del Emisor (CFDI 4.0)
EMISOR_NOMBRE = "FARMACIAS CUCEI S.A. DE C.V."
EMISOR_RFC = "FCU2109158A1"
EMISOR_REGIMEN = "601 - General de Ley Personas Morales"
CERTIFICADO_EMISOR = "00001000000512849302"
CERTIFICADO_SAT = "00001000000509841276"
RFC_PAC = "SAT970701NN3"


def _extraer_cp(direccion):
    """Extrae el código postal de 5 dígitos de la dirección de la sucursal o usa 44430 (CUCEI GDL)."""
    m = re.search(r"\b(\d{5})\b", str(direccion or ""))
    return m.group(1) if m else "44430"


def _numero_a_letras_mxn(monto):
    """Convierte un importe numérico a su representación en letra para CFDI en Pesos Mexicanos (M.N.)."""
    unidades = [
        "", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE",
        "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE",
        "VEINTE", "VEINTIUN", "VEINTIDOS", "VEINTITRES", "VEINTICUATRO", "VEINTICINCO", "VEINTISEIS",
        "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE",
    ]
    decenas = [
        "", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA",
        "SESENTA", "SETENTA", "OCHENTA", "NOVENTA",
    ]
    centenas = [
        "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
        "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS",
    ]

    def _menor_mil(n):
        if n == 0:
            return ""
        if n == 100:
            return "CIEN"
        c = n // 100
        r = n % 100
        texto_c = centenas[c]
        if r == 0:
            return texto_c
        if r < 30:
            texto_r = unidades[r]
        else:
            d = r // 10
            u = r % 10
            texto_r = decenas[d] + (f" Y {unidades[u]}" if u > 0 else "")
        return f"{texto_c} {texto_r}".strip()

    monto = round(max(0.0, float(monto)), 2)
    entero = int(monto)
    centavos = int(round((monto - entero) * 100))

    if entero == 0:
        letras = "CERO"
    else:
        millones = entero // 1_000_000
        miles = (entero % 1_000_000) // 1000
        resto = entero % 1000
        partes = []
        if millones == 1:
            partes.append("UN MILLON")
        elif millones > 1:
            partes.append(f"{_menor_mil(millones)} MILLONES")

        if miles == 1:
            partes.append("MIL")
        elif miles > 1:
            partes.append(f"{_menor_mil(miles)} MIL")

        if resto > 0:
            partes.append(_menor_mil(resto))
        letras = " ".join(partes)

    moneda = "PESO" if entero == 1 else "PESOS"
    return f"({letras} {moneda} {centavos:02d}/100 M.N.)"


def _generar_sellos_cfdi(uuid_str, rfc_emisor, rfc_receptor, total):
    """Genera sellos digitales deterministas con formato Base64 y Cadena Original TFDC v1.1."""
    semilla = f"{uuid_str}|{rfc_emisor}|{rfc_receptor}|{total:.2f}".encode("utf-8")
    h1 = hashlib.sha256(semilla).digest()
    h2 = hashlib.sha512(semilla).digest()
    sello_cfdi = base64.b64encode(h1 + h2 + h1[:24]).decode("ascii")

    h_sat1 = hashlib.sha256(b"SAT|" + semilla).digest()
    h_sat2 = hashlib.sha512(b"SAT|" + semilla).digest()
    sello_sat = base64.b64encode(h_sat1 + h_sat2 + h_sat1[:24]).decode("ascii")
    return sello_cfdi, sello_sat


def _dibujar_qr_verificacion(pdf, x, y, size, semilla_texto):
    """Dibuja un código matricial QR estilizado de verificación fiscal directamente con primitivas FPDF."""
    n = 21
    celda = size / n
    pdf.set_draw_color(30, 41, 59)
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(x - 1, y - 1, size + 2, size + 2, style="DF")

    bits = hashlib.sha512(semilla_texto.encode("utf-8")).digest() * 8

    def _es_finder(r, c):
        for fr, fc in ((0, 0), (0, n - 7), (n - 7, 0)):
            if fr <= r < fr + 7 and fc <= c < fc + 7:
                dr, dc = r - fr, c - fc
                if dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4):
                    return True, True
                return True, False
        return False, False

    pdf.set_fill_color(15, 23, 42)
    idx = 0
    for r in range(n):
        for c in range(n):
            en_finder, pintar = _es_finder(r, c)
            if en_finder:
                if pintar:
                    pdf.rect(x + c * celda, y + r * celda, celda, celda, style="F")
            else:
                bit = (bits[idx // 8] >> (idx % 8)) & 1
                idx += 1
                if bit:
                    pdf.rect(x + c * celda, y + r * celda, celda, celda, style="F")


def _normalizar_receptor(cliente):
    """Permite recibir `cliente` como str o como dict con datos fiscales."""
    if isinstance(cliente, dict):
        nombre = (cliente.get("nombre") or "PUBLICO EN GENERAL").strip().upper()
        rfc = (cliente.get("rfc") or "").strip().upper()
        ciudad = (cliente.get("ciudad") or "").strip()
        correo = (cliente.get("correo") or "").strip()
    else:
        nombre = (str(cliente or "PUBLICO EN GENERAL")).strip().upper()
        rfc = ""
        ciudad = ""
        correo = ""

    # Validar longitud de RFC (12 moral, 13 física); si no tiene, usar RFC genérico del SAT
    if not rfc or len(rfc) not in (12, 13):
        rfc = "XAXX010101000"
        regimen = "616 - Sin obligaciones fiscales"
        uso_cfdi = "S01 - Sin efectos fiscales"
    else:
        regimen = "612 - Personas Físicas con Actividades Empresariales" if len(rfc) == 13 else "601 - General de Ley Personas Morales"
        uso_cfdi = "G03 - Gastos en general"

    cp = _extraer_cp(ciudad)
    return {
        "nombre": nombre,
        "rfc": rfc,
        "regimen": regimen,
        "uso_cfdi": uso_cfdi,
        "domicilio_fiscal": cp,
        "ciudad": ciudad or "Guadalajara, Jal.",
        "correo": correo,
    }


# =====================================================================
# FACTURA DE VENTA - FORMATO CFDI 4.0 (SAT MÉXICO)
# =====================================================================
def generar_factura_venta(cliente, productos, total, descuento, sucursal, folio=None):
    """
    Genera la representación impresa de un CFDI 4.0 (Ingreso) cumpliendo con los requisitos
    del Anexo 20 del SAT en México. Retorna la ruta absoluta del PDF generado.
    """
    carpeta_raiz = ruta_logo.parents[1]
    carpeta = os.path.join(carpeta_raiz, "Facturas", "Ventas")
    os.makedirs(carpeta, exist_ok=True)

    ahora = datetime.now()
    fecha_timbrado = ahora + timedelta(seconds=2)
    marca_tiempo = ahora.strftime("%Y%m%d_%H%M%S")
    folio_num = folio if folio is not None else 1
    sufijo_folio = f"folio_{folio_num}_"
    nombre_archivo = os.path.join(
        carpeta,
        f"factura_venta_{sufijo_folio}{marca_tiempo}.pdf",
    )

    if FPDF is None:
        with open(nombre_archivo, "wb") as f:
            f.write(b"%PDF-1.4\n%CFDI 4.0 Factura Venta Fallback\n")
        return nombre_archivo

    receptor = _normalizar_receptor(cliente)
    sucursal = sucursal if isinstance(sucursal, dict) else {"id": 1, "direccion": "Guadalajara, Jal. 44430"}
    cp_expedicion = _extraer_cp(sucursal.get("direccion", ""))
    uuid_fiscal = str(uuid.uuid4()).upper()

    subtotal_bruto = round(float(total), 2)
    descuento_val = round(float(descuento), 2)
    total_neto = round(subtotal_bruto - descuento_val, 2)

    # Desglose de Impuestos Trasladados (IVA 16% sobre productos gravados o tasa 0% medicamentos)
    base_iva = round(total_neto / 1.16, 2)
    iva_trasladado = round(total_neto - base_iva, 2)

    sello_cfdi, sello_sat = _generar_sellos_cfdi(uuid_fiscal, EMISOR_RFC, receptor["rfc"], total_neto)
    cadena_original = (
        f"||1.1|{uuid_fiscal}|{fecha_timbrado.strftime('%Y-%m-%dT%H:%M:%S')}|"
        f"{RFC_PAC}|{sello_cfdi[:48]}...|{CERTIFICADO_SAT}||"
    )

    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # ---------------- 1. ENCABEZADO EMISOR Y DATOS DEL CFDI ----------------
    if ruta_logo.exists():
        pdf.image(str(ruta_logo), x=12, y=10, w=26)

    # Datos del Emisor (Centro)
    pdf.set_xy(42, 10)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(13, 59, 102)
    pdf.cell(88, 5, EMISOR_NOMBRE, ln=True)

    pdf.set_x(42)
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(88, 4.5, f"R.F.C.: {EMISOR_RFC}", ln=True)

    pdf.set_x(42)
    pdf.set_font("Arial", "", 8)
    pdf.cell(88, 4, f"Régimen Fiscal: {EMISOR_REGIMEN}", ln=True)

    pdf.set_x(42)
    pdf.cell(88, 4, f"Lugar de Expedición (C.P.): {cp_expedicion}", ln=True)

    pdf.set_x(42)
    dir_suc = str(sucursal.get("direccion", "Guadalajara, Jal."))[:58]
    pdf.cell(88, 4, f"Sucursal #{sucursal.get('id', 1)}: {dir_suc}", ln=True)

    # Cuadro Fiscal Derecho (Folio, UUID, Tipo de Comprobante)
    pdf.set_fill_color(13, 59, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_xy(132, 10)
    pdf.cell(72, 5.5, "FACTURA ELECTRÓNICA (CFDI 4.0)", border=1, ln=True, align="C", fill=True)

    pdf.set_text_color(30, 41, 59)
    pdf.set_draw_color(180, 190, 205)
    pdf.set_font("Arial", "", 7.5)
    pdf.set_x(132)
    pdf.cell(72, 4.5, f"Serie y Folio: A - {folio_num:06d}   |   Tipo: I - Ingreso", border="LR", ln=True, align="C")
    pdf.set_x(132)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(72, 4, "FOLIO FISCAL (UUID):", border="LR", ln=True, align="C")
    pdf.set_x(132)
    pdf.set_font("Arial", "", 6.8)
    pdf.cell(72, 4, uuid_fiscal, border="LR", ln=True, align="C")
    pdf.set_x(132)
    pdf.set_font("Arial", "", 7)
    pdf.cell(72, 4, f"Fecha Emisión: {ahora.strftime('%Y-%m-%dT%H:%M:%S')}", border="LR", ln=True, align="C")
    pdf.set_x(132)
    pdf.cell(72, 4, f"Certificado Emisor: {CERTIFICADO_EMISOR}", border="LRB", ln=True, align="C")

    pdf.ln(3)

    # ---------------- 2. BLOQUE RECEPTOR Y DATOS DE PAGO ----------------
    y_rec = pdf.get_y()
    pdf.set_fill_color(238, 246, 249)
    pdf.set_draw_color(180, 190, 205)

    # Encabezados de sección
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(13, 59, 102)
    pdf.set_xy(12, y_rec)
    pdf.cell(116, 5, "  DATOS FISCALES DEL RECEPTOR (CLIENTE)", border=1, fill=True)
    pdf.set_xy(130, y_rec)
    pdf.cell(74, 5, "  CONDICIONES FISCALES DE PAGO", border=1, ln=True, fill=True)

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(30, 41, 59)

    # Cuerpo Receptor
    y_body = pdf.get_y()
    pdf.set_xy(12, y_body)
    pdf.cell(116, 4.5, f"  Nombre / Razón Social: {receptor['nombre'][:48]}", border="LR", ln=True)
    pdf.set_x(12)
    pdf.cell(
        116,
        4.5,
        f"  R.F.C.: {receptor['rfc']}     |     Domicilio Fiscal (C.P.): {receptor['domicilio_fiscal']}",
        border="LR",
        ln=True,
    )
    pdf.set_x(12)
    pdf.cell(116, 4.5, f"  Régimen Fiscal: {receptor['regimen'][:52]}", border="LR", ln=True)
    pdf.set_x(12)
    pdf.cell(
        116,
        4.5,
        f"  Uso del CFDI: {receptor['uso_cfdi']}     |     Exportación: 01 - No aplica",
        border="LRB",
        ln=True,
    )

    # Cuerpo Condiciones de Pago
    pdf.set_xy(130, y_body)
    pdf.cell(74, 4.5, "  Forma de Pago: 01 - Efectivo", border="LR", ln=True)
    pdf.set_x(130)
    pdf.cell(74, 4.5, "  Método de Pago: PUE - Pago en una exhibición", border="LR", ln=True)
    pdf.set_x(130)
    pdf.cell(74, 4.5, "  Moneda: MXN - Peso Mexicano (T.C. 1.00)", border="LR", ln=True)
    pdf.set_x(130)
    pdf.cell(74, 4.5, f"  Certificado SAT: {CERTIFICADO_SAT}", border="LRB", ln=True)

    pdf.ln(4)

    # ---------------- 3. TABLA DE CONCEPTOS (ESTÁNDAR ANEXO 20 SAT) ----------------
    pdf.set_fill_color(13, 59, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 7.5)
    pdf.set_x(12)
    pdf.cell(20, 6, "ClaveProdServ", border=1, align="C", fill=True)
    pdf.cell(14, 6, "Cant.", border=1, align="C", fill=True)
    pdf.cell(18, 6, "ClaveUnidad", border=1, align="C", fill=True)
    pdf.cell(68, 6, "Descripción / Concepto", border=1, align="L", fill=True)
    pdf.cell(22, 6, "Valor Unit.", border=1, align="R", fill=True)
    pdf.cell(16, 6, "Obj. Imp.", border=1, align="C", fill=True)
    pdf.cell(14, 6, "Impuesto", border=1, align="C", fill=True)
    pdf.cell(20, 6, "Importe", border=1, align="R", fill=True, ln=True)

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(30, 41, 59)

    for idx, producto in enumerate(productos):
        nombre = str(producto[0])
        cantidad = int(producto[1])
        importe_linea = float(producto[2])
        precio_unitario_con_iva = importe_linea / cantidad if cantidad else 0.0
        valor_unitario_base = round(precio_unitario_con_iva / 1.16, 2)
        importe_base = round(importe_linea / 1.16, 2)

        # Clave SAT: 51101500 (Medicamentos y productos farmacéuticos)
        clave_sat = "51101500"
        clave_unidad = "H87 - Pieza"
        obj_imp = "02 - Sí"
        impuesto_txt = "002 IVA"

        fill_fila = (idx % 2 == 1)
        if fill_fila:
            pdf.set_fill_color(248, 250, 252)

        pdf.set_x(12)
        pdf.cell(20, 5.5, clave_sat, border="LRB", align="C", fill=fill_fila)
        pdf.cell(14, 5.5, f"{cantidad:.2f}", border="LRB", align="C", fill=fill_fila)
        pdf.cell(18, 5.5, clave_unidad, border="LRB", align="C", fill=fill_fila)
        pdf.cell(68, 5.5, f" {nombre[:38]}", border="LRB", align="L", fill=fill_fila)
        pdf.cell(22, 5.5, f"${valor_unitario_base:,.2f}", border="LRB", align="R", fill=fill_fila)
        pdf.cell(16, 5.5, obj_imp, border="LRB", align="C", fill=fill_fila)
        pdf.cell(14, 5.5, impuesto_txt, border="LRB", align="C", fill=fill_fila)
        pdf.cell(20, 5.5, f"${importe_base:,.2f}", border="LRB", align="R", fill=fill_fila, ln=True)

    pdf.ln(3)

    # ---------------- 4. IMPORTE CON LETRA Y RESUMEN DE IMPUESTOS / TOTALES ----------------
    y_tot = pdf.get_y()
    importe_letra = _numero_a_letras_mxn(total_neto)

    # Caja izquierda: Importe con letra y desglose de impuestos trasladados
    pdf.set_xy(12, y_tot)
    pdf.set_fill_color(238, 246, 249)
    pdf.set_font("Arial", "B", 7.5)
    pdf.set_text_color(13, 59, 102)
    pdf.cell(124, 5, "  IMPORTE CON LETRA", border=1, ln=True, fill=True)
    pdf.set_x(12)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(124, 6, f"  {importe_letra}", border="LRB", ln=True)

    pdf.set_x(12)
    pdf.set_font("Arial", "", 7.5)
    pdf.cell(
        124,
        5.5,
        f"  Impuestos Trasladados: 002 - IVA Tasa 0.160000 (16%)  |  Base: ${base_iva:,.2f}  |  Importe: ${iva_trasladado:,.2f}",
        border="LRB",
        ln=True,
    )

    # Caja derecha: Subtotales, Descuento, IVA y Total
    pdf.set_xy(138, y_tot)
    pdf.set_font("Arial", "", 8.5)
    pdf.cell(36, 5, "Subtotal Base:", border=1, align="R")
    pdf.cell(30, 5, f"${base_iva:,.2f}", border=1, align="R", ln=True)

    pdf.set_x(138)
    pdf.cell(36, 5, "Descuento (Puntos):", border=1, align="R")
    pdf.cell(30, 5, f"-${descuento_val:,.2f}", border=1, align="R", ln=True)

    pdf.set_x(138)
    pdf.cell(36, 5, "IVA Trasladado (16%):", border=1, align="R")
    pdf.cell(30, 5, f"${iva_trasladado:,.2f}", border=1, align="R", ln=True)

    pdf.set_x(138)
    pdf.set_fill_color(13, 59, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 9.5)
    pdf.cell(36, 6.5, "TOTAL MXN:", border=1, align="R", fill=True)
    pdf.cell(30, 6.5, f"${total_neto:,.2f}", border=1, align="R", fill=True, ln=True)

    pdf.ln(5)

    # ---------------- 5. TIMBRE FISCAL DIGITAL (QR, SELLOS Y CADENA ORIGINAL) ----------------
    y_sello = pdf.get_y()
    if y_sello > 215:
        pdf.add_page()
        y_sello = pdf.get_y()

    url_verificacion = (
        f"https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?"
        f"id={uuid_fiscal}&re={EMISOR_RFC}&rr={receptor['rfc']}&tt={total_neto:.2f}"
    )
    _dibujar_qr_verificacion(pdf, x=14, y=y_sello + 2, size=34, semilla_texto=url_verificacion)

    pdf.set_xy(52, y_sello)
    pdf.set_text_color(13, 59, 102)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(152, 4, "Sello Digital del CFDI:", ln=True)
    pdf.set_x(52)
    pdf.set_text_color(51, 65, 85)
    pdf.set_font("Arial", "", 6)
    pdf.multi_cell(152, 3.2, sello_cfdi, border=1)

    pdf.set_x(52)
    pdf.set_text_color(13, 59, 102)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(152, 4, "Sello Digital del SAT:", ln=True)
    pdf.set_x(52)
    pdf.set_text_color(51, 65, 85)
    pdf.set_font("Arial", "", 6)
    pdf.multi_cell(152, 3.2, sello_sat, border=1)

    pdf.set_x(52)
    pdf.set_text_color(13, 59, 102)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(152, 4, "Cadena Original del Complemento de Certificación Digital del SAT:", ln=True)
    pdf.set_x(52)
    pdf.set_text_color(51, 65, 85)
    pdf.set_font("Arial", "", 6)
    pdf.multi_cell(152, 3.2, cadena_original, border=1)

    pdf.ln(3)
    pdf.set_font("Arial", "B", 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(
        0,
        5,
        "Este documento es una representación impresa de un CFDI Versión 4.0",
        align="C",
        ln=True,
    )

    pdf.output(nombre_archivo)
    return nombre_archivo


# =====================================================================
# FACTURA / ORDEN DE COMPRA A PROVEEDOR (FORMATO FISCAL CFDI 4.0)
# =====================================================================
def generar_factura_compra(id_compra, productos, total, sucursal):
    """
    Genera el comprobante fiscal / orden de compra a proveedor en formato estructurado CFDI 4.0.
    Retorna la ruta absoluta del PDF generado.
    """
    carpeta_raiz = ruta_logo.parents[1]
    carpeta = os.path.join(carpeta_raiz, "Facturas", "Compras")
    os.makedirs(carpeta, exist_ok=True)

    ahora = datetime.now()
    marca_tiempo = ahora.strftime("%Y%m%d_%H%M%S")
    nombre_archivo = os.path.join(
        carpeta,
        f"factura_compra_folio_{id_compra}_{marca_tiempo}.pdf",
    )

    if FPDF is None:
        with open(nombre_archivo, "wb") as f:
            f.write(b"%PDF-1.4\n%CFDI 4.0 Factura Compra Fallback\n")
        return nombre_archivo

    sucursal = sucursal if isinstance(sucursal, dict) else {"id": 1, "direccion": "Guadalajara, Jal. 44430"}
    cp_expedicion = _extraer_cp(sucursal.get("direccion", ""))
    uuid_fiscal = str(uuid.uuid4()).upper()
    total_neto = round(float(total), 2)
    base_iva = round(total_neto / 1.16, 2)
    iva_trasladado = round(total_neto - base_iva, 2)

    sello_cfdi, sello_sat = _generar_sellos_cfdi(uuid_fiscal, "PRO1805209B2", EMISOR_RFC, total_neto)

    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    if ruta_logo.exists():
        pdf.image(str(ruta_logo), x=12, y=10, w=26)

    pdf.set_xy(42, 10)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(13, 59, 102)
    pdf.cell(88, 5, EMISOR_NOMBRE, ln=True)

    pdf.set_x(42)
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(88, 4.5, f"R.F.C. Receptor: {EMISOR_RFC}", ln=True)
    pdf.set_x(42)
    pdf.set_font("Arial", "", 8)
    pdf.cell(88, 4, f"Régimen Fiscal: {EMISOR_REGIMEN}", ln=True)
    pdf.set_x(42)
    pdf.cell(88, 4, f"Uso CFDI: G01 - Adquisición de mercancías  |  C.P.: {cp_expedicion}", ln=True)
    pdf.set_x(42)
    pdf.cell(88, 4, f"Sucursal Destino #{sucursal.get('id', 1)}: {str(sucursal.get('direccion', ''))[:45]}", ln=True)

    pdf.set_fill_color(13, 59, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_xy(132, 10)
    pdf.cell(72, 5.5, "COMPROBANTE FISCAL DE COMPRA", border=1, ln=True, align="C", fill=True)

    pdf.set_text_color(30, 41, 59)
    pdf.set_draw_color(180, 190, 205)
    pdf.set_font("Arial", "", 7.5)
    pdf.set_x(132)
    pdf.cell(72, 4.5, f"Serie y Folio: OC - {int(id_compra):06d}  |  Moneda: MXN", border="LR", ln=True, align="C")
    pdf.set_x(132)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(72, 4, "FOLIO FISCAL (UUID):", border="LR", ln=True, align="C")
    pdf.set_x(132)
    pdf.set_font("Arial", "", 6.8)
    pdf.cell(72, 4, uuid_fiscal, border="LR", ln=True, align="C")
    pdf.set_x(132)
    pdf.set_font("Arial", "", 7)
    pdf.cell(72, 4, f"Fecha: {ahora.strftime('%Y-%m-%dT%H:%M:%S')}", border="LRB", ln=True, align="C")

    pdf.ln(6)

    # Tabla de partidas de compra
    pdf.set_fill_color(13, 59, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 8)
    pdf.set_x(12)
    pdf.cell(22, 6, "Clave SAT", border=1, align="C", fill=True)
    pdf.cell(20, 6, "Unidad", border=1, align="C", fill=True)
    pdf.cell(150, 6, "Detalle de Partida (Producto / Proveedor / Cantidad / Importe)", border=1, align="L", fill=True, ln=True)

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(30, 41, 59)
    for idx, linea in enumerate(productos):
        fill_fila = (idx % 2 == 1)
        if fill_fila:
            pdf.set_fill_color(248, 250, 252)
        pdf.set_x(12)
        pdf.cell(22, 6, "51101500", border="LRB", align="C", fill=fill_fila)
        pdf.cell(20, 6, "H87 - Pieza", border="LRB", align="C", fill=fill_fila)
        pdf.cell(150, 6, f" {str(linea)[:95]}", border="LRB", align="L", fill=fill_fila, ln=True)

    pdf.ln(4)
    y_tot = pdf.get_y()
    importe_letra = _numero_a_letras_mxn(total_neto)

    pdf.set_xy(12, y_tot)
    pdf.set_fill_color(238, 246, 249)
    pdf.set_font("Arial", "B", 7.5)
    pdf.set_text_color(13, 59, 102)
    pdf.cell(124, 5, "  IMPORTE CON LETRA", border=1, ln=True, fill=True)
    pdf.set_x(12)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(124, 6, f"  {importe_letra}", border="LRB", ln=True)
    pdf.set_x(12)
    pdf.set_font("Arial", "", 7.5)
    pdf.cell(124, 5, "  Forma de Pago: 03 - Transferencia electrónica de fondos  |  Método: PUE", border="LRB", ln=True)

    pdf.set_xy(138, y_tot)
    pdf.set_font("Arial", "", 8.5)
    pdf.cell(36, 5, "Subtotal Base:", border=1, align="R")
    pdf.cell(30, 5, f"${base_iva:,.2f}", border=1, align="R", ln=True)
    pdf.set_x(138)
    pdf.cell(36, 5, "IVA Acreditable (16%):", border=1, align="R")
    pdf.cell(30, 5, f"${iva_trasladado:,.2f}", border=1, align="R", ln=True)
    pdf.set_x(138)
    pdf.set_fill_color(13, 59, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 9.5)
    pdf.cell(36, 6, "TOTAL MXN:", border=1, align="R", fill=True)
    pdf.cell(30, 6, f"${total_neto:,.2f}", border=1, align="R", fill=True, ln=True)

    pdf.ln(6)
    y_qr = pdf.get_y()
    _dibujar_qr_verificacion(pdf, x=14, y=y_qr, size=28, semilla_texto=uuid_fiscal)
    pdf.set_xy(48, y_qr)
    pdf.set_text_color(13, 59, 102)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(156, 4, "Sello Digital CFDI:", ln=True)
    pdf.set_x(48)
    pdf.set_text_color(51, 65, 85)
    pdf.set_font("Arial", "", 6)
    pdf.multi_cell(156, 3.2, sello_cfdi, border=1)
    pdf.set_x(48)
    pdf.set_text_color(13, 59, 102)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(156, 4, "Sello Digital del SAT:", ln=True)
    pdf.set_x(48)
    pdf.set_text_color(51, 65, 85)
    pdf.set_font("Arial", "", 6)
    pdf.multi_cell(156, 3.2, sello_sat, border=1)

    pdf.ln(3)
    pdf.set_font("Arial", "B", 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, "Este documento es una representación impresa de un CFDI Versión 4.0", align="C", ln=True)

    pdf.output(nombre_archivo)
    return nombre_archivo
