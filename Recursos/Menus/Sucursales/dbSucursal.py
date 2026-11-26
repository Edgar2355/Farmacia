from ...conexion import conectar


class dbSucursal:

    def obtenerSucursales(self):
        con = None
        try:
            con = conectar()
            if con is None:
                return []
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT * FROM sucursales ORDER BY id ASC")
            return cursor.fetchall()
        except Exception as e:
            print("Error al cargar todas las sucursales:", e)
            return []
        finally:
            if con:
                con.close()

    def buscar(self, criterio):
        con = None
        try:
            con = conectar()
            if con is None:
                return None
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT * FROM sucursales WHERE id=%s", (criterio,))
            return cursor.fetchone()
        except Exception as e:
            print("Error buscar sucursal:", e)
            return None
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
                "SELECT * FROM sucursales WHERE CAST(id AS CHAR) LIKE %s OR direccion LIKE %s ORDER BY id ASC",
                (like, like),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error buscar_por_texto sucursales:", e)
            return []
        finally:
            if con:
                con.close()

    def insertar(self, direccion):
        con = None
        try:
            con = conectar()
            if con is None:
                return False
            cursor = con.cursor()
            cursor.execute("INSERT INTO sucursales (direccion) VALUES (%s)", (direccion,))
            con.commit()
            return True
        except Exception as e:
            print("Error insertar sucursal:", e)
            return False
        finally:
            if con:
                con.close()

    def actualizar(self, id_sucursal, direccion):
        con = None
        try:
            con = conectar()
            if con is None:
                return False
            cursor = con.cursor()
            cursor.execute(
                "UPDATE sucursales SET direccion=%s WHERE id=%s",
                (direccion, id_sucursal),
            )
            con.commit()
            return True
        except Exception as e:
            print("Error actualizar sucursal:", e)
            return False
        finally:
            if con:
                con.close()

    def eliminar(self, id_sucursal):
        con = None
        try:
            con = conectar()
            if con is None:
                return False
            cursor = con.cursor()
            # CORRECCIÓN CRÍTICA: antes borraba de la tabla `clientes` por error
            cursor.execute("DELETE FROM sucursales WHERE id=%s", (id_sucursal,))
            con.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Error eliminar sucursal:", e)
            return False
        finally:
            if con:
                con.close()
