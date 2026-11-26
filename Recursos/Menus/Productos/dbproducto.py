from ...conexion import conectar
from ...Servicios.contexto_sucursal import obtener_sucursal


class dbProducto:

    def __init__(self):
        self.sucursal = obtener_sucursal()

    def _sucursal_id(self):
        self.sucursal = obtener_sucursal()
        return self.sucursal.get("id", 0)

    def obtener_todos(self):
        con = None
        try:
            con = conectar()
            if con is None:
                return []
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT p.*, pr.nombre AS proveedor
                FROM productos p
                LEFT JOIN proveedores pr ON p.id_proveedor = pr.id
                WHERE p.sucursal_id = %s
                ORDER BY p.id ASC
                """,
                (self._sucursal_id(),),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_todos productos:", e)
            return []
        finally:
            if con:
                con.close()

    def buscar_por_texto(self, texto):
        con = None
        try:
            con = conectar()
            if con is None:
                return []
            cursor = con.cursor(dictionary=True)
            like = f"%{texto}%"
            cursor.execute(
                """
                SELECT p.*, pr.nombre AS proveedor
                FROM productos p
                LEFT JOIN proveedores pr ON p.id_proveedor = pr.id
                WHERE p.sucursal_id = %s
                  AND (p.nombre LIKE %s OR p.tipo LIKE %s OR CAST(p.id AS CHAR) LIKE %s)
                ORDER BY p.id ASC
                """,
                (self._sucursal_id(), like, like, like),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error buscar_por_texto productos:", e)
            return []
        finally:
            if con:
                con.close()

    def buscar(self, nombre):
        con = None
        try:
            con = conectar()
            if con is None:
                return None
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT p.*, pr.nombre AS proveedor
                FROM productos p
                LEFT JOIN proveedores pr ON p.id_proveedor = pr.id
                WHERE p.nombre = %s AND p.sucursal_id = %s
                """,
                (nombre, self._sucursal_id()),
            )
            dato = cursor.fetchone()
            if not dato:
                cursor.execute(
                    """
                    SELECT p.*, pr.nombre AS proveedor
                    FROM productos p
                    LEFT JOIN proveedores pr ON p.id_proveedor = pr.id
                    WHERE p.nombre LIKE %s AND p.sucursal_id = %s
                    LIMIT 1
                    """,
                    (f"%{nombre}%", self._sucursal_id()),
                )
                dato = cursor.fetchone()
            return dato
        except Exception as e:
            print("Error buscar producto:", e)
            return None
        finally:
            if con:
                con.close()

    def insertar(self, nombre, tipo, id_proveedor, compra, venta, stock, receta):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            sql = """
            INSERT INTO productos (nombre, tipo, id_proveedor, precio_compra, precio_venta, stock, receta, sucursal_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (nombre, tipo, id_proveedor, compra, venta, stock, receta, self._sucursal_id()),
            )
            con.commit()
            return True
        finally:
            if con:
                con.close()

    def editar(self, idp, nombre, tipo, id_proveedor, compra, venta, stock, receta):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            sql = """
            UPDATE productos
            SET nombre=%s, tipo=%s, id_proveedor=%s,
                precio_compra=%s, precio_venta=%s, stock=%s, receta=%s
            WHERE id=%s AND sucursal_id=%s
            """
            cursor.execute(
                sql,
                (nombre, tipo, id_proveedor, compra, venta, stock, receta, idp, self._sucursal_id()),
            )
            con.commit()
            return True
        finally:
            if con:
                con.close()

    def eliminar(self, idp):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            cursor.execute(
                "DELETE FROM productos WHERE id=%s AND sucursal_id=%s",
                (idp, self._sucursal_id()),
            )
            con.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Error eliminar producto:", e)
            return False
        finally:
            if con:
                con.close()

    def obtener_proveedores(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre ASC")
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_proveedores:", e)
            return []
        finally:
            if con:
                con.close()

    def obtener_productos(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, nombre FROM productos WHERE sucursal_id=%s ORDER BY nombre ASC",
                (self._sucursal_id(),),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_productos:", e)
            return []
        finally:
            if con:
                con.close()

    def getMaxID(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT MAX(id) AS max_id FROM productos")
            datos = cursor.fetchone()
            if datos and datos["max_id"] is not None:
                return int(datos["max_id"])
            return 0
        except Exception as e:
            print("Error getMaxID productos:", e)
            return 0
        finally:
            if con:
                con.close()
