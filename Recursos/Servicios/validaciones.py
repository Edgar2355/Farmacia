import re


def validar_entero_positivo(valor, nombre_campo="Cantidad", permitir_cero=False):
    """Valida que un valor sea un entero positivo (o >= 0 si permitir_cero=True)."""
    texto = str(valor).strip()
    if not texto:
        return False, f"El campo '{nombre_campo}' es obligatorio.", None
    try:
        numero = int(texto)
    except ValueError:
        return False, f"El campo '{nombre_campo}' debe ser un número entero válido.", None

    if permitir_cero and numero < 0:
        return False, f"El campo '{nombre_campo}' no puede ser negativo.", None
    if not permitir_cero and numero <= 0:
        return False, f"El campo '{nombre_campo}' debe ser mayor a 0.", None

    return True, "", numero


def validar_flotante_positivo(valor, nombre_campo="Precio", permitir_cero=False):
    """Valida que un valor sea un número decimal positivo."""
    texto = str(valor).strip()
    if not texto:
        return False, f"El campo '{nombre_campo}' es obligatorio.", None
    try:
        numero = float(texto)
    except ValueError:
        return False, f"El campo '{nombre_campo}' debe ser un valor numérico válido.", None

    if permitir_cero and numero < 0:
        return False, f"El campo '{nombre_campo}' no puede ser negativo.", None
    if not permitir_cero and numero <= 0:
        return False, f"El campo '{nombre_campo}' debe ser mayor a 0.", None

    return True, "", round(numero, 2)


def validar_correo(correo, obligatorio=False):
    """Valida el formato básico de un correo electrónico."""
    texto = str(correo).strip()
    if not texto:
        if obligatorio:
            return False, "El correo electrónico es obligatorio."
        return True, ""
    patron = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(patron, texto):
        return False, "El formato del correo electrónico no es válido."
    return True, ""


def validar_telefono(telefono, obligatorio=True):
    """Valida que el teléfono contenga dígitos válidos (7 a 15 dígitos)."""
    texto = str(telefono).strip()
    if not texto:
        if obligatorio:
            return False, "El teléfono es obligatorio."
        return True, ""
    limpio = re.sub(r"[\s\-\(\)\+]", "", texto)
    if not limpio.isdigit() or not (7 <= len(limpio) <= 15):
        return False, "El teléfono debe contener entre 7 y 15 dígitos numéricos."
    return True, ""


def calcular_descuento_y_puntos(puntos_actuales, total_venta):
    """
    Regla de negocio de fidelidad:
    - Si el cliente tiene >= 50 puntos, obtiene 10% de descuento y sus puntos se reinician a 0.
    - Si tiene < 50 puntos y la compra supera $500, acumula 10 puntos adicionales.
    Retorna (descuento, nuevos_puntos, total_final).
    """
    puntos = int(puntos_actuales or 0)
    total = float(total_venta or 0.0)
    descuento = 0.0

    if puntos >= 50:
        descuento = round(total * 0.10, 2)
        nuevos_puntos = 0
    else:
        nuevos_puntos = puntos + (10 if total > 500 else 0)

    total_final = round(total - descuento, 2)
    return descuento, nuevos_puntos, total_final
