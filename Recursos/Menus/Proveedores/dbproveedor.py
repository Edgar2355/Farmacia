from ...conexion import conectar


class DBProveedor:

    def insertar(self, proveedor):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            sql = "INSERT INTO proveedores (nombre, telefono, correo, direccion) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (proveedor.nombre, proveedor.telefono, proveedor.correo, proveedor.direccion))
            con.commit()
            return True
        except Exception as e:
            print("Error insertar proveedor:", e)
            return False
        finally:
            if con:
                con.close()

    def obtener(self):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            cursor.execute("SELECT id, nombre, correo, telefono, direccion FROM proveedores ORDER BY id ASC")
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener proveedores:", e)
            return []
        finally:
            if con:
                con.close()

    def actualizar(self, proveedor):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            sql = "UPDATE proveedores SET nombre=%s, correo=%s, telefono=%s, direccion=%s WHERE id=%s"
            cursor.execute(
                sql,
                (proveedor.nombre, proveedor.correo, proveedor.telefono, proveedor.direccion, proveedor.id),
            )
            con.commit()
            return True
        except Exception as e:
            print("Error actualizar proveedor:", e)
            return False
        finally:
            if con:
                con.close()

    def eliminar(self, id_proveedor):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            cursor.execute("DELETE FROM proveedores WHERE id=%s", (id_proveedor,))
            con.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
        finally:
            if con:
                con.close()

    # BUSQUEDAS
    def buscar_por_id(self, id_proveedor):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            cursor.execute(
                "SELECT id, nombre, correo, telefono, direccion FROM proveedores WHERE id=%s",
                (id_proveedor,),
            )
            return cursor.fetchall()
        except Exception:
            return []
        finally:
            if con:
                con.close()

    def buscar_por_nombre(self, nombre):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            cursor.execute(
                "SELECT id, nombre, correo, telefono, direccion FROM proveedores WHERE nombre LIKE %s",
                ("%" + nombre + "%",),
            )
            return cursor.fetchall()
        except Exception:
            return []
        finally:
            if con:
                con.close()

    def buscar_por_correo(self, correo):
        con = None
        try:
            con = conectar()
            cursor = con.cursor()
            cursor.execute(
                "SELECT id, nombre, correo, telefono, direccion FROM proveedores WHERE correo LIKE %s",
                ("%" + correo + "%",),
            )
            return cursor.fetchall()
        except Exception:
            return []
        finally:
            if con:
                con.close()
