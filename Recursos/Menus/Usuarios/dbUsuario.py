import hashlib
from ...conexion import conectar


def hash_password(password):
    """Genera un hash SHA-256 truncado a 50 caracteres (compatible con VARCHAR(50) en la BD)."""
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()[:50]


class dbUsuario:

    def login(self, usuario, password, sucursal_id):
        con = None
        try:
            con = conectar()
            if con is None:
                return None

            cursor = con.cursor(dictionary=True)
            pwd_hash = hash_password(password)
            sql = """
            SELECT id, nombre, rol, sucursal_id
            FROM usuarios
            WHERE usuario=%s AND (password=%s OR password=%s) AND sucursal_id=%s
            """
            cursor.execute(sql, (usuario, password, pwd_hash, sucursal_id))
            return cursor.fetchone()
        except Exception as e:
            print("Error login:", e)
            return None
        finally:
            if con:
                con.close()

    def obtener_todos(self):
        con = None
        try:
            con = conectar()
            if con is None:
                return []
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT u.id, u.nombre, u.usuario, u.rol, u.sucursal_id, s.direccion AS sucursal_nombre
                FROM usuarios u
                LEFT JOIN sucursales s ON u.sucursal_id = s.id
                ORDER BY u.id ASC
                """
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error obtener_todos usuarios:", e)
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
                SELECT u.id, u.nombre, u.usuario, u.rol, u.sucursal_id, s.direccion AS sucursal_nombre
                FROM usuarios u
                LEFT JOIN sucursales s ON u.sucursal_id = s.id
                WHERE u.nombre LIKE %s OR u.usuario LIKE %s OR u.rol LIKE %s
                ORDER BY u.id ASC
                """,
                (like, like, like),
            )
            return cursor.fetchall()
        except Exception as e:
            print("Error buscar_por_texto usuarios:", e)
            return []
        finally:
            if con:
                con.close()

    def insertar(self, nombre, usuario, password, rol, sucursal_id):
        con = None
        try:
            con = conectar()
            if con is None:
                return False, "Sin conexión a la base de datos"
            cursor = con.cursor()
            pwd_hash = hash_password(password)
            cursor.execute(
                """
                INSERT INTO usuarios (nombre, usuario, password, rol, sucursal_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nombre, usuario, pwd_hash, rol, sucursal_id),
            )
            con.commit()
            return True, "Usuario registrado correctamente"
        except Exception as e:
            print("Error insertar usuario:", e)
            return False, f"No se pudo registrar el usuario (verifique que el usuario no esté duplicado): {e}"
        finally:
            if con:
                con.close()

    def actualizar(self, id_usuario, nombre, usuario, password, rol, sucursal_id):
        con = None
        try:
            con = conectar()
            if con is None:
                return False, "Sin conexión a la base de datos"
            cursor = con.cursor()
            if password and str(password).strip():
                pwd_hash = hash_password(password)
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET nombre=%s, usuario=%s, password=%s, rol=%s, sucursal_id=%s
                    WHERE id=%s
                    """,
                    (nombre, usuario, pwd_hash, rol, sucursal_id, id_usuario),
                )
            else:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET nombre=%s, usuario=%s, rol=%s, sucursal_id=%s
                    WHERE id=%s
                    """,
                    (nombre, usuario, rol, sucursal_id, id_usuario),
                )
            con.commit()
            return True, "Usuario actualizado correctamente"
        except Exception as e:
            print("Error actualizar usuario:", e)
            return False, f"No se pudo actualizar el usuario: {e}"
        finally:
            if con:
                con.close()

    def eliminar(self, id_usuario):
        con = None
        try:
            con = conectar()
            if con is None:
                return False
            cursor = con.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id=%s", (id_usuario,))
            con.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Error eliminar usuario:", e)
            return False
        finally:
            if con:
                con.close()
