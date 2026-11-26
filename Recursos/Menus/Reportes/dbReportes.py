from ...conexion import conectar
from ...Servicios.contexto_sucursal import obtener_sucursal


class dbReportes:

    def __init__(self):
        self.sucursal = obtener_sucursal()

    def _sucursal_id(self):
        self.sucursal = obtener_sucursal()
        return self.sucursal.get("id", 0)

    # =========================
    # CLIENTES POR CIUDAD
    # =========================
    def clientes_por_ciudad(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    COALESCE(NULLIF(TRIM(ciudad), ''), 'No especificada') AS ciudad,
                    COUNT(*) AS total
                FROM clientes
                GROUP BY COALESCE(NULLIF(TRIM(ciudad), ''), 'No especificada')
                ORDER BY total DESC
                """
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error clientes_por_ciudad:", e)
            return []
        finally:
            if con:
                con.close()

    # =========================
    # VENTAS POR FECHA
    # =========================
    def ventas_por_fecha(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    DATE(fecha) AS fecha,
                    COUNT(DISTINCT id) AS num_ventas,
                    SUM(total) AS total
                FROM ventas
                WHERE sucursal_id = %s
                GROUP BY DATE(fecha)
                ORDER BY fecha DESC
                """,
                (self._sucursal_id(),),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error ventas_por_fecha:", e)
            return []
        finally:
            if con:
                con.close()

    # =========================
    # COMPRAS POR FECHA
    # =========================
    def compras_por_fecha(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    DATE(fecha) AS fecha,
                    COUNT(DISTINCT id) AS num_compras,
                    SUM(precio_compra * cantidad) AS total
                FROM compras
                WHERE sucursal_id = %s
                GROUP BY DATE(fecha)
                ORDER BY fecha DESC
                """,
                (self._sucursal_id(),),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error compras_por_fecha:", e)
            return []
        finally:
            if con:
                con.close()

    # =========================
    # FACTURAS MAYORES VENTAS (AGRUPADO POR FOLIO)
    # =========================
    def facturas_mayores_ventas(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    v.id,
                    COALESCE(c.nombre, CONCAT('Cliente #', v.id_cliente)) AS cliente,
                    SUM(v.cantidad) AS articulos,
                    SUM(v.total) AS total,
                    MAX(v.fecha) AS fecha
                FROM ventas v
                LEFT JOIN clientes c ON v.id_cliente = c.id
                WHERE v.sucursal_id = %s
                GROUP BY v.id, v.id_cliente, c.nombre
                ORDER BY total DESC
                LIMIT 15
                """,
                (self._sucursal_id(),),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error facturas_mayores_ventas:", e)
            return []
        finally:
            if con:
                con.close()

    # =========================
    # PRODUCTOS MÁS VENDIDOS
    # =========================
    def productos_mas_vendidos(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.nombre,
                    p.tipo,
                    COALESCE(SUM(v.cantidad), 0) AS unidades_vendidas,
                    COALESCE(SUM(v.total), 0) AS ingresos
                FROM productos p
                INNER JOIN ventas v ON p.id = v.id_producto AND v.sucursal_id = p.sucursal_id
                WHERE p.sucursal_id = %s
                GROUP BY p.id, p.nombre, p.tipo
                ORDER BY unidades_vendidas DESC, ingresos DESC
                LIMIT 20
                """,
                (self._sucursal_id(),),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error productos_mas_vendidos:", e)
            return []
        finally:
            if con:
                con.close()

    # =========================
    # PRODUCTOS CON STOCK CRÍTICO
    # =========================
    def stock_critico(self, umbral=5):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.nombre,
                    p.tipo,
                    p.stock,
                    COALESCE(pr.nombre, 'Sin proveedor') AS proveedor
                FROM productos p
                LEFT JOIN proveedores pr ON p.id_proveedor = pr.id
                WHERE p.sucursal_id = %s AND p.stock <= %s
                ORDER BY p.stock ASC
                """,
                (self._sucursal_id(), umbral),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error stock_critico:", e)
            return []
        finally:
            if con:
                con.close()
