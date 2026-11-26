from ...conexion import conectar
from ...Servicios.contexto_sucursal import obtener_sucursal


class dbFacturas:

    def __init__(self):
        self.sucursal = obtener_sucursal()

    def _sucursal_id(self):
        self.sucursal = obtener_sucursal()
        return self.sucursal.get("id", 0)

    def obtener_facturas(self, tipo_filtro="Todas"):
        con = None
        try:
            con = conectar()
            if con is None:
                return []
            cursor = con.cursor(dictionary=True)
            suc_id = self._sucursal_id()

            sql = """
                SELECT
                    f.id,
                    f.tipo,
                    f.id_referencia,
                    f.fecha,
                    s.direccion AS sucursal
                FROM facturas f
                LEFT JOIN sucursales s ON f.sucursal_id = s.id
                WHERE f.sucursal_id = %s
            """
            params = [suc_id]

            if tipo_filtro in ("Venta", "Compra"):
                sql += " AND f.tipo = %s"
                params.append(tipo_filtro)

            sql += " ORDER BY f.fecha DESC, f.id DESC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_facturas:", e)
            return []
        finally:
            if con:
                con.close()

    def obtener_detalle_referencia(self, tipo, id_referencia):
        con = None
        try:
            con = conectar()
            if con is None:
                return []
            cursor = con.cursor(dictionary=True)
            suc_id = self._sucursal_id()

            if str(tipo).lower() == "venta":
                cursor.execute(
                    """
                    SELECT
                        p.nombre AS producto,
                        c.nombre AS tercero,
                        v.cantidad,
                        v.total AS subtotal
                    FROM ventas v
                    LEFT JOIN productos p ON v.id_producto = p.id
                    LEFT JOIN clientes c ON v.id_cliente = c.id
                    WHERE v.id = %s AND v.sucursal_id = %s
                    """,
                    (id_referencia, suc_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        p.nombre AS producto,
                        pr.nombre AS tercero,
                        co.cantidad,
                        (co.cantidad * co.precio_compra) AS subtotal
                    FROM compras co
                    LEFT JOIN productos p ON co.id_producto = p.id
                    LEFT JOIN proveedores pr ON co.id_proveedor = pr.id
                    WHERE co.id = %s AND co.sucursal_id = %s
                    """,
                    (id_referencia, suc_id),
                )
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_detalle_referencia:", e)
            return []
        finally:
            if con:
                con.close()
