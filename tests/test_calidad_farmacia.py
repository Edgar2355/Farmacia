import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from Recursos.Servicios.validaciones import (
    validar_entero_positivo,
    validar_flotante_positivo,
    validar_correo,
    validar_telefono,
    calcular_descuento_y_puntos,
)
from Recursos.Servicios import contexto_sucursal
from Recursos import conexion
from Recursos.Menus.Usuarios.dbUsuario import hash_password, dbUsuario
from Recursos.Menus.Sucursales.dbSucursal import dbSucursal
from Recursos.Menus.Productos.dbproducto import dbProducto
from Recursos.Menus.Proveedores.proveedor import Proveedor
from Recursos.Menus.Proveedores.dbproveedor import DBProveedor
from Recursos.Menus.Ventas.factura import generar_factura_venta, generar_factura_compra


class TestValidaciones(unittest.TestCase):

    def test_validar_entero_positivo(self):
        ok, msg, val = validar_entero_positivo("15", "Cantidad")
        self.assertTrue(ok)
        self.assertEqual(val, 15)

        ok, msg, val = validar_entero_positivo("0", "Cantidad", permitir_cero=False)
        self.assertFalse(ok)

        ok, msg, val = validar_entero_positivo("0", "Stock", permitir_cero=True)
        self.assertTrue(ok)
        self.assertEqual(val, 0)

        ok, msg, val = validar_entero_positivo("-5", "Stock", permitir_cero=True)
        self.assertFalse(ok)

        ok, msg, val = validar_entero_positivo("abc", "Cantidad")
        self.assertFalse(ok)

    def test_validar_flotante_positivo(self):
        ok, msg, val = validar_flotante_positivo("45.556", "Precio")
        self.assertTrue(ok)
        self.assertEqual(val, 45.56)

        ok, msg, val = validar_flotante_positivo("-10.0", "Precio")
        self.assertFalse(ok)

        ok, msg, val = validar_flotante_positivo("", "Precio")
        self.assertFalse(ok)

    def test_validar_correo(self):
        self.assertTrue(validar_correo("cliente@cucei.udg.mx")[0])
        self.assertTrue(validar_correo("", obligatorio=False)[0])
        self.assertFalse(validar_correo("", obligatorio=True)[0])
        self.assertFalse(validar_correo("correo_invalido")[0])

    def test_validar_telefono(self):
        self.assertTrue(validar_telefono("3312345678")[0])
        self.assertTrue(validar_telefono("+52 (33) 1234-5678")[0])
        self.assertFalse(validar_telefono("123")[0])
        self.assertFalse(validar_telefono("abcdefg")[0])

    def test_calcular_descuento_y_puntos(self):
        descuento, nuevos_puntos, total_final = calcular_descuento_y_puntos(50, 1000.0)
        self.assertEqual(descuento, 100.0)
        self.assertEqual(nuevos_puntos, 0)
        self.assertEqual(total_final, 900.0)

        descuento, nuevos_puntos, total_final = calcular_descuento_y_puntos(20, 600.0)
        self.assertEqual(descuento, 0.0)
        self.assertEqual(nuevos_puntos, 30)
        self.assertEqual(total_final, 600.0)

        descuento, nuevos_puntos, total_final = calcular_descuento_y_puntos(20, 300.0)
        self.assertEqual(descuento, 0.0)
        self.assertEqual(nuevos_puntos, 20)
        self.assertEqual(total_final, 300.0)


class TestContextoSucursal(unittest.TestCase):

    def test_lectura_y_escritura_sucursal_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_temp = Path(tmpdir) / "sucursal.json"
            with patch.object(contexto_sucursal, "ARCHIVO_SUCURSAL", ruta_temp):
                suc = contexto_sucursal.obtener_sucursal()
                self.assertIn("id", suc)
                self.assertIn("direccion", suc)

                contexto_sucursal.guardar_sucursal({"id": 12, "direccion": "Av. Revolución 1500"})
                leida = contexto_sucursal.obtener_sucursal()
                self.assertEqual(leida["id"], 12)
                self.assertEqual(leida["direccion"], "Av. Revolución 1500")

    def test_lectura_sucursal_json_codificacion_latin1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_temp = Path(tmpdir) / "sucursal.json"
            # Simular archivo guardado con codificación Windows CP1252 / Latin-1 con acento (0xed = 'í')
            contenido_latin1 = '{\n    "id": 1,\n    "direccion": "Blvd. Marcelino García Barragán 1421"\n}'.encode("latin-1")
            ruta_temp.write_bytes(contenido_latin1)

            with patch.object(contexto_sucursal, "ARCHIVO_SUCURSAL", ruta_temp):
                leida = contexto_sucursal.obtener_sucursal()
                self.assertEqual(leida["id"], 1)
                self.assertIn("García", leida["direccion"])

    def test_parseo_url_tunel_pinggy(self):
        host, port = conexion.parsear_url_tunel("tcp://rnxyz-189-203.a.free.pinggy.link:43219")
        self.assertEqual(host, "rnxyz-189-203.a.free.pinggy.link")
        self.assertEqual(port, 43219)

        host2, port2 = conexion.parsear_url_tunel("localhost")
        self.assertEqual(host2, "localhost")
        self.assertEqual(port2, 3306)

    def test_conexion_persistente_wrapper_reutiliza_socket(self):
        raw_mock = MagicMock()
        raw_mock.in_transaction = True
        wrapper = conexion.ConexionPersistenteWrapper(raw_mock)
        # Al llamar a wrapper.close() desde un DAO, hace rollback si hay transacción abierta pero NO cierra el socket TCP
        wrapper.close()
        raw_mock.rollback.assert_called_once()
        raw_mock.close.assert_not_called()
        # Al llamar a cerrar_definitivamente(), sí cierra el socket subyacente
        wrapper.cerrar_definitivamente()
        raw_mock.close.assert_called_once()


class TestDAOsYSeguridad(unittest.TestCase):

    def test_hash_password_longitud_compatible(self):
        h = hash_password("secreto123")
        self.assertEqual(len(h), 50)
        self.assertEqual(h, hash_password("secreto123"))

    @patch("Recursos.Menus.Sucursales.dbSucursal.conectar")
    def test_eliminar_sucursal_apunta_a_tabla_sucursales(self, mock_conectar):
        mock_con = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_con.cursor.return_value = mock_cursor
        mock_conectar.return_value = mock_con

        dao = dbSucursal()
        ok = dao.eliminar(3)

        self.assertTrue(ok)
        sql_ejecutado = mock_cursor.execute.call_args[0][0]
        self.assertIn("DELETE FROM sucursales", sql_ejecutado)
        self.assertNotIn("clientes", sql_ejecutado)

    @patch("Recursos.Menus.Productos.dbproducto.conectar")
    @patch("Recursos.Menus.Productos.dbproducto.obtener_sucursal")
    def test_insertar_producto_incluye_sucursal_id(self, mock_suc, mock_conectar):
        mock_suc.return_value = {"id": 7, "direccion": "Sucursal Norte"}
        mock_con = MagicMock()
        mock_cursor = MagicMock()
        mock_con.cursor.return_value = mock_cursor
        mock_conectar.return_value = mock_con

        dao = dbProducto()
        ok = dao.insertar("Paracetamol 500mg", "Medicamento", 1, 15.0, 28.0, 40, 0)
        self.assertTrue(ok)

        sql_ejecutado, params = mock_cursor.execute.call_args[0]
        self.assertIn("sucursal_id", sql_ejecutado)
        self.assertEqual(params[-1], 7)

    @patch("Recursos.Menus.Proveedores.dbproveedor.conectar")
    def test_insertar_proveedor_incluye_direccion(self, mock_conectar):
        mock_con = MagicMock()
        mock_cursor = MagicMock()
        mock_con.cursor.return_value = mock_cursor
        mock_conectar.return_value = mock_con

        dao = DBProveedor()
        prov = Proveedor(None, "Farmacéutica GDL", "contacto@fgdl.mx", "3311223344", "Calz. Independencia 200")
        ok = dao.insertar(prov)
        self.assertTrue(ok)

        sql_ejecutado, params = mock_cursor.execute.call_args[0]
        self.assertIn("direccion", sql_ejecutado)
        self.assertEqual(params[3], "Calz. Independencia 200")


class TestGeneracionFacturasPDF(unittest.TestCase):

    def test_generar_pdf_venta_y_compra_sin_ui(self):
        sucursal = {"id": 1, "direccion": "Blvd. Marcelino García Barragán 1421, 44430 Guadalajara, Jal."}
        productos_venta = [("Paracetamol 500mg", 2, 56.0)]
        # Probar pasando diccionario completo de cliente con RFC fiscal mexicano
        cliente_dict = {
            "nombre": "Juan Pérez López",
            "rfc": "PELJ900512AB1",
            "ciudad": "Guadalajara 44100",
            "correo": "juan@ejemplo.mx",
        }
        ruta_pdf_v = generar_factura_venta(cliente_dict, productos_venta, 56.0, 0.0, sucursal, folio=999)
        self.assertTrue(os.path.exists(ruta_pdf_v))
        os.remove(ruta_pdf_v)

        productos_compra = ["Producto: 1 - Paracetamol | Proveedor: Pisa | Cantidad: 10 | Subtotal: $150.00"]
        ruta_pdf_c = generar_factura_compra(888, productos_compra, 150.0, sucursal)
        self.assertTrue(os.path.exists(ruta_pdf_c))
        os.remove(ruta_pdf_c)


if __name__ == "__main__":
    unittest.main()
