from ...conexion import conectar


class dbCliente:

    def obtener_todos(self):
        con = None
        try:
            con = conectar()
            if con is None:
                return []
            cursor = con.cursor(dictionary=True)
            cursor.execute("SELECT * FROM clientes ORDER BY id ASC")
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_todos clientes:", e)
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
                SELECT * FROM clientes
                WHERE CAST(id AS CHAR) LIKE %s
                   OR nombre LIKE %s
                   OR telefono LIKE %s
                   OR correo LIKE %s
                   OR rfc LIKE %s
                   OR ciudad LIKE %s
                ORDER BY id ASC
                """,
                (like, like, like, like, like, like),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error buscar_por_texto clientes:", e)
            return []
        finally:
            if con:
                con.close()

    def buscar(self, id_cliente):
        con = None
        try:
            con = conectar()
            if con is None:
                return None
            cursor = con.cursor(dictionary=True)
            sql = "SELECT * FROM clientes WHERE id=%s"
            cursor.execute(sql, (id_cliente,))
            return cursor.fetchone()
        except Exception as e:
            print("Error buscar cliente:", e)
            return None
        finally:
            if con:
                con.close()

    def insertar(self, nombre, telefono, correo, rfc, ciudad, puntos):
        con = None
        try:
            con = conectar()
            if con is None:
                return False
            cursor = con.cursor()
            sql = """
            INSERT INTO clientes (nombre, telefono, correo, rfc, ciudad, puntos)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (nombre, telefono, correo, rfc, ciudad, puntos))
            con.commit()
            return True
        except Exception as e:
            print("Error insertar cliente:", e)
            return False
        finally:
            if con:
                con.close()

    def actualizar(self, id_cliente, nombre, telefono, correo, rfc, ciudad, puntos):
        con = None
        try:
            con = conectar()
            if con is None:
                return False
            cursor = con.cursor()
            sql = """
            UPDATE clientes
            SET nombre=%s, telefono=%s, correo=%s, rfc=%s, ciudad=%s, puntos=%s
            WHERE id=%s
            """
            cursor.execute(sql, (nombre, telefono, correo, rfc, ciudad, puntos, id_cliente))
            con.commit()
            return True
        except Exception as e:
            print("Error actualizar cliente:", e)
            return False
        finally:
            if con:
                con.close()

    def eliminar(self, id_cliente):
        con = None
        try:
            con = conectar()
            if con is None:
                return False
            cursor = con.cursor()
            sql = "DELETE FROM clientes WHERE id=%s"
            cursor.execute(sql, (id_cliente,))
            con.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Error eliminar cliente:", e)
            return False
        finally:
            if con:
                con.close()
