from ...conexion import conectar
from ...Servicios.contexto_sucursal import obtener_sucursal
from ..Ventas.factura import generar_factura_compra
from .email_service import enviar_correo_proveedor
import traceback


class dbCompra:

    def __init__(self):
        self.sucursal = obtener_sucursal()

    def _sucursal_actual(self):
        self.sucursal = obtener_sucursal()
        return self.sucursal

    def obtener_proveedores(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre, correo FROM proveedores ORDER BY nombre ASC")
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_proveedores:", e)
            return []
        finally:
            if con:
                con.close()

    def obtener_proveedor(self, nombre):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre, correo FROM proveedores WHERE nombre=%s", (nombre,))
            return cursor.fetchone()
        except Exception as e:
            print("Error obtener_proveedor:", e)
            return None
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
                "SELECT id, nombre, id_proveedor, precio_compra, stock FROM productos WHERE sucursal_id=%s ORDER BY nombre ASC",
                (suc["id"],),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_productos compras:", e)
            return []
        finally:
            if con:
                con.close()

    def obtener_producto_id(self, id_prod):
        con = None
        try:
            con = conectar()
            suc = self._sucursal_actual()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                "SELECT nombre FROM productos WHERE id=%s AND sucursal_id=%s",
                (id_prod, suc["id"]),
            )
            datos = cursor.fetchone()
            return datos["nombre"] if datos else "Desconocido"
        finally:
            if con:
                con.close()

    def obtener_proveedor_id(self, id_prov):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT nombre FROM proveedores WHERE id=%s", (id_prov,))
            datos = cursor.fetchone()
            return datos["nombre"] if datos else "Desconocido"
        finally:
            if con:
                con.close()

    def obtener_maxID(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT MAX(id) AS max_id FROM compras")
            row = cursor.fetchone()
            if row and row["max_id"] is not None:
                return int(row["max_id"])
            return 0
        except Exception as e:
            print("Error obtener_maxID compras:", e)
            return 0
        finally:
            if con:
                con.close()

    def registrar_multiple(self, id_compra, carrito, productos_separados):
        if not carrito:
            return False, "El carrito de compras está vacío."

        con = None
        suc = self._sucursal_actual()

        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)

            cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 AS siguiente_id FROM compras")
            folio_real = int(cursor.fetchone()["siguiente_id"])
            id_compra = max(int(id_compra), folio_real)

            # Pre-cargar nombres de productos y proveedores en 2 consultas rápidas en lugar de 2*N consultas por red
            cursor.execute("SELECT id, nombre FROM productos WHERE sucursal_id=%s", (suc["id"],))
            mapa_productos = {r["id"]: r["nombre"] for r in cursor.fetchall()}

            cursor.execute("SELECT id, nombre FROM proveedores")
            mapa_proveedores = {r["id"]: r["nombre"] for r in cursor.fetchall()}

            total_general = 0.0
            producto_para_factura = []

            for item in carrito:
                id_producto = item[0]
                id_proveedor = item[1]
                cantidad = int(item[2])
                precio = float(item[3]) / float(item[2])
                subtotal = round(precio * cantidad, 2)
                total_general = round(total_general + subtotal, 2)

                nom_prod = mapa_productos.get(id_producto, "Producto")
                nom_prov = mapa_proveedores.get(id_proveedor, "Proveedor")

                producto = (
                    f"Producto: {id_producto} - {nom_prod} "
                    f"| Proveedor: {nom_prov} "
                    f"| Cantidad: {cantidad} | Precio U.: ${precio:.2f} | Subtotal: ${subtotal:.2f}"
                )
                producto_para_factura.append(producto)

                cursor.execute(
                    """
                    UPDATE productos
                    SET stock = stock + %s
                    WHERE id = %s AND sucursal_id = %s
                    """,
                    (cantidad, id_producto, suc["id"]),
                )

                cursor.execute(
                    """
                    INSERT INTO compras (id, id_producto, id_proveedor, cantidad, precio_compra, fecha, sucursal_id)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    (id_compra, id_producto, id_proveedor, cantidad, precio, suc["id"]),
                )

            cursor.execute(
                """
                INSERT INTO facturas (tipo, id_referencia, fecha, sucursal_id)
                VALUES ('Compra', %s, NOW(), %s)
                """,
                (id_compra, suc["id"]),
            )

            con.commit()

            archivo_pdf = generar_factura_compra(id_compra, producto_para_factura, total_general, suc)

            for destinatario, productos in productos_separados.items():
                enviar_correo_proveedor(destinatario, productos, suc["direccion"], async_send=True)

            return True, f"Compra #{id_compra} registrada. Total: ${total_general:.2f}\nPDF: {archivo_pdf}"

        except Exception as e:
            print("Error compra multiple:", e)
            traceback.print_exc()
            if con:
                con.rollback()
            return False, f"Error en compra: {e}"
        finally:
            if con:
                con.close()
