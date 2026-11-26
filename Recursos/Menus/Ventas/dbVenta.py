from ...conexion import conectar
from ...Servicios.contexto_sucursal import obtener_sucursal
from ...Servicios.validaciones import calcular_descuento_y_puntos
from .factura import generar_factura_venta
from ..Compras.email_service import enviar_factura


class dbVenta:

    def __init__(self):
        self.sucursal = obtener_sucursal()

    def _sucursal_actual(self):
        self.sucursal = obtener_sucursal()
        return self.sucursal

    def obtener_maxID(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT MAX(id) AS maximo FROM ventas")
            row = cursor.fetchone()
            if row and row["maximo"] is not None:
                return int(row["maximo"])
            return 0
        except Exception as e:
            print("Error obtener_maxID ventas:", e)
            return 0
        finally:
            if con:
                con.close()

    def obtener_clientes(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre, correo, puntos FROM clientes ORDER BY nombre ASC")
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_clientes:", e)
            return []
        finally:
            if con:
                con.close()

    def obtener_productos(self):
        con = None
        try:
            con = conectar()
            suc = self._sucursal_actual()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, nombre, tipo, precio_venta, stock, receta
                FROM productos
                WHERE sucursal_id = %s
                ORDER BY nombre ASC
                """,
                (suc["id"],),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_productos ventas:", e)
            return []
        finally:
            if con:
                con.close()

    def obtener_productoID(self, nombre):
        con = None
        try:
            con = conectar()
            suc = self._sucursal_actual()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                "SELECT id FROM productos WHERE nombre = %s AND sucursal_id = %s",
                (nombre, suc["id"]),
            )
            datos = cursor.fetchone()
            return datos["id"] if datos else None
        finally:
            if con:
                con.close()

    def registrar(self, id_venta, id_cliente, productos_datos, total):
        con = None
        try:
            con = conectar()
            suc = self._sucursal_actual()
            cursor = con.cursor(dictionary=True)

            # Obtener el folio real al momento de la transacción para evitar colisiones
            cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 AS siguiente_id FROM ventas")
            folio_real = int(cursor.fetchone()["siguiente_id"])
            id_venta = max(int(id_venta), folio_real)

            cursor.execute("SELECT * FROM clientes WHERE id = %s", (id_cliente,))
            cliente = cursor.fetchone()
            if not cliente:
                return False, "Cliente no encontrado"

            descuento, nuevos_puntos, total_final = calcular_descuento_y_puntos(
                cliente.get("puntos", 0),
                total,
            )

            # Factor proporcional si hubo descuento para que la suma de `total` en `ventas` refleje el monto real
            factor_descuento = (total_final / float(total)) if float(total) > 0 else 1.0

            for dato in productos_datos:
                nombre_producto = dato[0]
                cantidad = int(dato[1])
                subtotal = float(dato[2])

                cursor.execute(
                    "SELECT * FROM productos WHERE nombre = %s AND sucursal_id = %s",
                    (nombre_producto, suc["id"]),
                )
                producto = cursor.fetchone()
                if not producto:
                    con.rollback()
                    return False, f"Producto '{nombre_producto}' no encontrado en esta sucursal"

                producto_id = producto["id"]
                stock_actual = int(producto["stock"])

                if cantidad > stock_actual:
                    con.rollback()
                    return False, f"Stock insuficiente para {nombre_producto} (Disponible: {stock_actual})"

                total_linea = round(subtotal * factor_descuento, 2)

                cursor.execute(
                    """
                    INSERT INTO ventas (id, id_cliente, id_producto, cantidad, total, fecha, sucursal_id)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    (id_venta, id_cliente, producto_id, cantidad, total_linea, suc["id"]),
                )

                cursor.execute(
                    """
                    UPDATE productos
                    SET stock = stock - %s
                    WHERE id = %s AND sucursal_id = %s
                    """,
                    (cantidad, producto_id, suc["id"]),
                )

            cursor.execute(
                "UPDATE clientes SET puntos = %s WHERE id = %s",
                (nuevos_puntos, id_cliente),
            )

            # Registrar en la tabla `facturas`
            cursor.execute(
                """
                INSERT INTO facturas (tipo, id_referencia, fecha, sucursal_id)
                VALUES ('Venta', %s, NOW(), %s)
                """,
                (id_venta, suc["id"]),
            )

            con.commit()

            archivo = generar_factura_venta(
                cliente,
                productos_datos,
                total,
                descuento,
                suc,
                folio=id_venta,
            )

            correo_cliente = (cliente.get("correo") or "").strip()
            if correo_cliente and "@" in correo_cliente:
                cuerpo_mail = (
                    f"Hola {cliente['nombre']},\n\n"
                    f"Adjuntamos la factura de tu compra #{id_venta} en Farmacia CUCEI.\n"
                    f"Subtotal: ${float(total):.2f}\n"
                    f"Descuento aplicado: ${descuento:.2f}\n"
                    f"Total pagado: ${total_final:.2f}\n"
                    f"Puntos acumulados actuales: {nuevos_puntos}\n\n"
                    f"¡Gracias por tu preferencia!"
                )
                enviar_factura(
                    correo_cliente,
                    f"Factura de Venta #{id_venta} - Farmacia CUCEI",
                    cuerpo_mail,
                    archivo,
                    async_send=True,
                )

            msg_exito = (
                f"Venta #{id_venta} realizada correctamente.\n"
                f"Subtotal: ${float(total):.2f}\n"
                f"Descuento por puntos: -${descuento:.2f}\n"
                f"Total pagado: ${total_final:.2f}\n"
                f"Factura PDF guardada en: {archivo}"
            )
            return True, msg_exito

        except Exception as e:
            import traceback
            traceback.print_exc()
            if con:
                con.rollback()
            return False, str(e)
        finally:
            if con:
                con.close()
