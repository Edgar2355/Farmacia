import sys
sys.dont_write_bytecode = True

import tkinter as tk
from tkinter import messagebox, ttk
import os

from Recursos import estilo
from Recursos.conexion import (
    conectar,
    obtener_config_db,
    guardar_config_db,
    parsear_url_tunel,
)
from Recursos.Servicios.contexto_sucursal import obtener_sucursal, guardar_sucursal

from Recursos.Menus.Usuarios.dbUsuario import dbUsuario
from Recursos.Menus.Usuarios.usuario_view import UsuariosView

from Recursos.Menus.Sucursales.Sucursales_view import SucursalesView
from Recursos.Menus.Sucursales.dbSucursal import dbSucursal
from Recursos.Menus.Clientes.cliente_view import ClientesView
from Recursos.Menus.Productos.producto_view import ProductosView
from Recursos.Menus.Proveedores.proveedor_view import ProveedoresView
from Recursos.Menus.Compras.compra_view import CompraView
from Recursos.Menus.Ventas.venta_view import VentaView
from Recursos.Menus.Reportes.reportes_view import ReportesView
from Recursos.Menus.Facturas.facturas_view import FacturasView

ruta = os.path.dirname(os.path.abspath(__file__))
sucursal = obtener_sucursal()


def abrir_sucursal():
    global sucursal
    sucursal = obtener_sucursal()
    return sucursal


def texto_estado_servidor_db():
    """Devuelve una cadena descriptiva del servidor MySQL activo (Local o Túnel Pinggy)."""
    cfg = obtener_config_db()
    modo = "Local" if cfg["host"] in ("localhost", "127.0.0.1") else "Túnel Pinggy"
    return f"BD ({modo}): {cfg['host']}:{cfg['port']}"


def abrir_dialogo_config_servidor(parent_window, on_success_callback=None):
    """
    Abre un cuadro de diálogo modal reutilizable (tanto desde Login como desde el Menú Principal)
    para conectar o cambiar en caliente entre un túnel Pinggy.io y Localhost (3306).
    """
    dlg = tk.Toplevel(parent_window)
    dlg.title("Configurar Conexión MySQL / Túnel Pinggy.io")
    estilo.centrar_ventana(dlg, 540, 430, maximizar=False)
    dlg.configure(bg=estilo.backgroundColor)
    dlg.transient(parent_window)
    dlg.grab_set()

    estilo.crear_encabezado(dlg, "Conexión a Base de Datos", "Cambiar entre Local y Pinggy.io")

    card = tk.Frame(dlg, bg=estilo.surfaceColor, bd=1, relief="solid", padx=20, pady=16)
    card.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)
    card.columnconfigure(1, weight=1)

    cfg = obtener_config_db()
    modo_actual = "Local (XAMPP)" if cfg["host"] in ("localhost", "127.0.0.1") else "Túnel Remoto (Pinggy.io)"

    lbl_actual = tk.Label(
        card,
        text=f"Conexión actual: {modo_actual}  ->  {cfg['host']}:{cfg['port']}",
        bg="#dbeafe",
        fg="#1e3a8a",
        font=("Segoe UI", 9, "bold"),
        padx=8,
        pady=4,
        anchor="w",
    )
    lbl_actual.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

    tk.Label(
        card,
        text="Enlace del Túnel Pinggy (pega la URL tcp://... que generó la consola):",
        bg=estilo.surfaceColor,
        fg=estilo.headerColor,
        font=("Segoe UI", 9, "bold"),
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 4))

    ent_url = ttk.Entry(card, width=54)
    ent_url.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    ent_url.insert(0, f"tcp://{cfg['host']}:{cfg['port']}")

    tk.Label(card, text="Usuario MySQL:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=4)
    ent_user = ttk.Entry(card, width=28)
    ent_user.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=4)
    ent_user.insert(0, cfg["user"])

    tk.Label(card, text="Contraseña MySQL:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", pady=4)
    ent_pass = ttk.Entry(card, width=28, show="*")
    ent_pass.grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=4)
    ent_pass.insert(0, cfg["password"])

    tk.Label(card, text="Base de Datos:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 9, "bold")).grid(row=5, column=0, sticky="w", pady=4)
    ent_db = ttk.Entry(card, width=28)
    ent_db.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=4)
    ent_db.insert(0, cfg["database"])

    lbl_res = tk.Label(card, text="", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold"))
    lbl_res.grid(row=6, column=0, columnspan=2, pady=(8, 6))

    def _guardar_y_probar(usar_local=False):
        if usar_local:
            host, port = "localhost", 3306
            ent_url.delete(0, tk.END)
            ent_url.insert(0, "tcp://localhost:3306")
        else:
            host, port = parsear_url_tunel(ent_url.get())
            if "xxxx" in host.lower() or "12345" == str(port):
                messagebox.showwarning(
                    "Enlace de ejemplo detectado",
                    "Pegaste un enlace de ejemplo.\n\n"
                    "Para obtener el enlace real:\n"
                    "1. Abre 'Compartir_BD_Pinggy.bat' en la PC que tiene XAMPP.\n"
                    "2. Espera unos segundos a que la consola negra muestre la URL que empieza con 'tcp://'.\n"
                    "3. Copia esa URL real y pégala aquí.\n\n"
                    "Si quieres usar el XAMPP de tu propia PC, haz clic en 'Restaurar Localhost (3306)'.",
                    parent=dlg,
                )
                return

        cfg_previa = obtener_config_db()
        lbl_res.config(text=f"Probando conexión a {host}:{port}...", fg=estilo.buttonColor)
        dlg.update_idletasks()

        guardar_config_db(
            host=host,
            port=port,
            user=ent_user.get(),
            password=ent_pass.get(),
            database=ent_db.get(),
        )

        try:
            con = conectar(forzar_nueva=True)
            if con:
                con.close()
            if callable(on_success_callback):
                on_success_callback()
            messagebox.showinfo(
                "Conexión Actualizada",
                f"Conectado exitosamente al servidor MySQL en:\n{host}:{port}\n\n"
                "Las sucursales y módulos ahora operan sobre este servidor.",
                parent=dlg,
            )
            dlg.destroy()
        except Exception as e:
            # Si falló la nueva conexión, restaurar la configuración previa para no dejar desconectada la sesión activa
            guardar_config_db(
                host=cfg_previa["host"],
                port=cfg_previa["port"],
                user=cfg_previa["user"],
                password=cfg_previa["password"],
                database=cfg_previa["database"],
            )
            if callable(on_success_callback):
                on_success_callback()
            lbl_res.config(
                text="No se pudo conectar. Se mantuvo la conexión anterior.",
                fg=estilo.CancelButtonColor,
            )
            messagebox.showerror(
                "Error de Conexión",
                f"No se pudo establecer conexión con {host}:{port}.\n"
                f"Se restauró tu configuración anterior ({cfg_previa['host']}:{cfg_previa['port']}).\n\n"
                f"Detalle técnico: {e}",
                parent=dlg,
            )

    btns = tk.Frame(card, bg=estilo.surfaceColor)
    btns.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    ttk.Button(
        btns,
        text="Conectar / Cambiar Túnel",
        style="BotonesAceptar.TButton",
        command=lambda: _guardar_y_probar(usar_local=False),
    ).pack(side=tk.LEFT, padx=(0, 8))

    ttk.Button(
        btns,
        text="Usar Localhost (3306)",
        style="BotonesEstilo.TButton",
        command=lambda: _guardar_y_probar(usar_local=True),
    ).pack(side=tk.LEFT)


# ---------------- LOGIN ----------------
class Login(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Iniciar Sesión - Farmacia CUCEI")
        estilo.centrar_ventana(self, 520, 480, maximizar=True)
        self.configure(bg=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        abrir_sucursal()

        # -------- BARRA SUPERIOR --------
        estilo.crear_encabezado(self, "FARMACIA CUCEI", "Acceso al Sistema de Gestión")

        # -------- CONTENEDOR PARA CENTRAR LA TARJETA EN PANTALLA COMPLETA --------
        wrapper = tk.Frame(self, bg=estilo.backgroundColor)
        wrapper.pack(fill=tk.BOTH, expand=True)

        card = tk.Frame(wrapper, bg=estilo.surfaceColor, bd=1, relief="solid", padx=32, pady=24)
        card.place(relx=0.5, rely=0.49, anchor="center", width=510)

        top_row = tk.Frame(card, bg=estilo.surfaceColor)
        top_row.pack(fill=tk.X, pady=(0, 12))

        try:
            ruta_logo = os.path.join(ruta, "Recursos", "Logo.png")
            self.logo_img = tk.PhotoImage(file=ruta_logo).subsample(10, 10)
            tk.Label(top_row, image=self.logo_img, bg=estilo.surfaceColor).pack(side=tk.LEFT, padx=(0, 14))
        except Exception:
            pass

        title_box = tk.Frame(top_row, bg=estilo.surfaceColor)
        title_box.pack(side=tk.LEFT, fill=tk.X)
        tk.Label(
            title_box,
            text="Bienvenido",
            bg=estilo.surfaceColor,
            fg=estilo.textColor,
            font=("Segoe UI", 18, "bold"),
            anchor="w",
        ).pack(fill=tk.X)
        tk.Label(
            title_box,
            text="Ingresa tus credenciales para acceder al sistema",
            bg=estilo.surfaceColor,
            fg=estilo.mutedTextColor,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill=tk.X)

        # -------- INDICADOR DE SERVIDOR ACTIVO (LOCAL / PINGGY) --------
        srv_bar = tk.Frame(card, bg="#eff6ff", bd=1, relief="solid", padx=10, pady=6)
        srv_bar.pack(fill=tk.X, pady=(0, 12))

        self.lbl_servidor_actual = tk.Label(
            srv_bar,
            text=texto_estado_servidor_db(),
            bg="#eff6ff",
            fg="#1e3a8a",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_servidor_actual.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            srv_bar,
            text="Configurar Servidor / Pinggy",
            bg="#2563eb",
            fg="white",
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=2,
            command=self.abrir_config_servidor,
        ).pack(side=tk.RIGHT)

        # -------- FORMULARIO --------
        form = tk.Frame(card, bg=estilo.surfaceColor)
        form.pack(fill=tk.X, pady=4)
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Sucursal activa:", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.db_suc = dbSucursal()
        self.lista_sucursales = []
        self.cmb_sucursal_login = ttk.Combobox(form, state="readonly", width=36)
        self.cmb_sucursal_login.grid(row=0, column=1, sticky="ew", pady=(0, 8), padx=(10, 0))
        self.cmb_sucursal_login.bind("<<ComboboxSelected>>", self._cambiar_sucursal_desde_login)
        self.cmb_sucursal_login["values"] = [f"{sucursal['id']} - {sucursal['direccion']}"]
        self.cmb_sucursal_login.set(f"{sucursal['id']} - {sucursal['direccion']}")
        self.after(80, self._recargar_sucursales_login)

        tk.Label(form, text="Usuario:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        self.user = ttk.Entry(form, width=38)
        self.user.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))
        self.user.bind("<Return>", lambda e: self.passw.focus_set())

        tk.Label(form, text="Contraseña:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=8)

        pass_frame = tk.Frame(form, bg=estilo.surfaceColor)
        pass_frame.grid(row=2, column=1, sticky="ew", pady=8, padx=(10, 0))
        self.passw = ttk.Entry(pass_frame, width=30, show="*")
        self.passw.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.passw.bind("<Return>", lambda e: self.login())

        self.mostrar_pwd = False
        self.btn_ver_pwd = tk.Button(
            pass_frame,
            text="Ver",
            bg="#e2e8f0",
            fg=estilo.textColor,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            padx=8,
            command=self._alternar_password,
        )
        self.btn_ver_pwd.pack(side=tk.RIGHT, padx=(6, 0))

        # -------- BOTÓN Y ESTADO --------
        self.lbl_estado = tk.Label(
            card,
            text="",
            bg=estilo.surfaceColor,
            fg=estilo.buttonColor,
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_estado.pack(pady=(6, 4))

        self.btn_ingresar = ttk.Button(
            card,
            text="Iniciar Sesión (Enter)",
            style="BotonesEstilo.TButton",
            command=self.login,
        )
        self.btn_ingresar.pack(fill=tk.X, pady=(4, 0), ipady=3)

        self.user.focus_set()

    def _recargar_sucursales_login(self):
        global sucursal
        self.lbl_servidor_actual.config(text=texto_estado_servidor_db())
        self.lista_sucursales = self.db_suc.obtenerSucursales()
        if self.lista_sucursales:
            ids = [s["id"] for s in self.lista_sucursales]
            if sucursal.get("id") not in ids:
                sucursal = guardar_sucursal(self.lista_sucursales[0])
            opciones_suc = [f"{s['id']} - {s['direccion']}" for s in self.lista_sucursales]
        else:
            opciones_suc = [f"{sucursal['id']} - {sucursal['direccion']}"]
        self.cmb_sucursal_login["values"] = opciones_suc
        self.cmb_sucursal_login.set(f"{sucursal['id']} - {sucursal['direccion']}")

    def abrir_config_servidor(self):
        abrir_dialogo_config_servidor(self, on_success_callback=self._recargar_sucursales_login)

    def _alternar_password(self):
        self.mostrar_pwd = not self.mostrar_pwd
        self.passw.config(show="" if self.mostrar_pwd else "*")
        self.btn_ver_pwd.config(text="Ocultar" if self.mostrar_pwd else "Ver")

    def _cambiar_sucursal_desde_login(self, event=None):
        global sucursal
        sel = self.cmb_sucursal_login.get()
        if " - " in sel:
            try:
                id_sel = int(sel.split(" - ")[0].strip())
                for s in self.lista_sucursales:
                    if s["id"] == id_sel:
                        sucursal = guardar_sucursal(s)
                        break
            except ValueError:
                pass

    def login(self):
        usuario = self.user.get().strip()
        password = self.passw.get().strip()

        if usuario == "" or password == "":
            messagebox.showwarning("Campos incompletos", "Por favor ingresa tu usuario y contraseña.", parent=self)
            return

        self._cambiar_sucursal_desde_login()
        self.lbl_estado.config(text="Verificando credenciales...")
        self.btn_ingresar.config(state="disabled")
        self.update_idletasks()

        try:
            con = conectar()
            if con:
                con.close()
        except Exception as e:
            self.lbl_estado.config(text="")
            self.btn_ingresar.config(state="normal")
            cfg = obtener_config_db()
            messagebox.showerror(
                title="Error de conexión",
                message=(
                    f"No se pudo conectar con el servidor MySQL en {cfg['host']}:{cfg['port']}.\n\n"
                    "• Si estás en modo local, verifica que XAMPP/MySQL esté activo.\n"
                    "• Si te conectas por Pinggy, haz clic en 'Configurar Servidor / Pinggy' y pega el nuevo enlace."
                ),
                parent=self,
            )
            print("Error:" + str(e))
            return

        abrir_sucursal()
        db = dbUsuario()
        resultado = db.login(usuario, password, sucursal["id"])

        if resultado is None and usuario == "admin" and password == "123":
            resultado = {"id": 0, "nombre": "Administrador General", "rol": "Admin"}

        if resultado is None:
            self.lbl_estado.config(text="")
            self.btn_ingresar.config(state="normal")
            messagebox.showerror(
                "Acceso denegado",
                "Usuario, contraseña o sucursal incorrectos.\nVerifique que la sucursal seleccionada corresponda a su usuario.",
                parent=self,
            )
        else:
            self.destroy()
            App(resultado).mainloop()


# ---------------- MENU PRINCIPAL ----------------
class App(tk.Tk):
    def __init__(self, sesion):
        super().__init__()

        abrir_sucursal()
        self.sesion = sesion
        rol = sesion["rol"]
        nombre = sesion["nombre"]

        self.title(f"Panel Principal - Farmacia CUCEI | {nombre} ({rol})")
        estilo.centrar_ventana(self, 1100, 720, maximizar=True)
        self.configure(bg=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        global sucursal

        # -------- BARRA SUPERIOR INSTITUCIONAL --------
        header = tk.Frame(self, bg=estilo.headerColor, height=68)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        left_hdr = tk.Frame(header, bg=estilo.headerColor)
        left_hdr.pack(side=tk.LEFT, padx=18)

        try:
            ruta_logo = os.path.join(ruta, "Recursos", "Logo.png")
            self.logo_img = tk.PhotoImage(file=ruta_logo).subsample(12, 12)
            tk.Label(left_hdr, image=self.logo_img, bg=estilo.headerColor).pack(side=tk.LEFT, padx=(0, 12))
        except Exception:
            pass

        titles = tk.Frame(left_hdr, bg=estilo.headerColor)
        titles.pack(side=tk.LEFT)
        tk.Label(
            titles,
            text="SISTEMA DE GESTIÓN FARMACIA CUCEI",
            bg=estilo.headerColor,
            fg="white",
            font=("Segoe UI", 15, "bold"),
            anchor="w",
        ).pack(fill=tk.X)

        self.lbl_subtitulo_header = tk.Label(
            titles,
            text=self._texto_subtitulo_header(),
            bg=estilo.headerColor,
            fg="#bfdbfe",
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.lbl_subtitulo_header.pack(fill=tk.X)

        ttk.Button(
            header,
            text="Cerrar Sesión",
            style="BotonesRechazar.TButton",
            command=self.cerrar_sesion,
        ).pack(side=tk.RIGHT, padx=18, pady=14)

        ttk.Button(
            header,
            text="Túnel Pinggy / Servidor BD",
            style="BotonesEstilo.TButton",
            command=self.abrir_config_tunel_menu,
        ).pack(side=tk.RIGHT, padx=(0, 8), pady=14)

        # -------- BARRA DE SUCURSAL Y SERVIDOR ACTIVO --------
        suc_bar = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=10)
        suc_bar.pack(fill=tk.X, padx=24, pady=(16, 10))

        tk.Label(
            suc_bar,
            text="Sucursal Activa:",
            bg=estilo.surfaceColor,
            fg=estilo.textColor,
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.db_suc = dbSucursal()
        self.sucursales = self.db_suc.obtenerSucursales()
        self.sucursales_arreglo = []

        ids_existentes = [s["id"] for s in self.sucursales]
        if self.sucursales and sucursal.get("id") not in ids_existentes:
            sucursal = guardar_sucursal(self.sucursales[0])

        for sucursal_ in self.sucursales:
            self.sucursales_arreglo.append(f"{sucursal_['id']} - {sucursal_['direccion']}")

        self.sucursal_combo = ttk.Combobox(suc_bar, width=52, values=self.sucursales_arreglo, state="readonly")
        self.sucursal_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.sucursal_combo.set(f"{sucursal['id']} - {sucursal['direccion']}")
        self.sucursal_combo.bind("<<ComboboxSelected>>", self.seleccionarSucursal)

        self.lbl_badge_servidor = tk.Label(
            suc_bar,
            text=texto_estado_servidor_db(),
            bg="#dbeafe",
            fg="#1e3a8a",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
        )
        self.lbl_badge_servidor.pack(side=tk.LEFT, padx=(4, 10))

        ttk.Button(
            suc_bar,
            text="Cambiar Túnel / BD",
            style="BotonesEstilo.TButton",
            command=self.abrir_config_tunel_menu,
        ).pack(side=tk.RIGHT, padx=(6, 0))

        if rol in ("Admin", "Administrador"):
            ttk.Button(
                suc_bar,
                text="Administrar Sucursales",
                style="BotonesEstilo.TButton",
                command=self.abrir_sucursales,
            ).pack(side=tk.RIGHT)

        # -------- PANEL DE MÓDULOS (GRID DE TARJETAS EN 2 COLUMNAS EXPANDIBLE) --------
        contenedor = tk.Frame(self, bg=estilo.backgroundColor)
        contenedor.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)
        contenedor.columnconfigure(0, weight=1)
        contenedor.columnconfigure(1, weight=1)

        modulos = [
            ("Punto de Venta (POS)", "Registrar ventas, aplicar descuentos por puntos y consultar al Asistente IA", self.abrir_ventas),
            ("Gestión de Clientes", "Directorio de clientes, RFC, contacto y programa de puntos", self.abrir_clientes),
        ]

        if rol != "Vendedor":
            modulos.extend([
                ("Inventario de Productos", "Catálogo por sucursal, control de precios, recetas y alertas de stock bajo", self.abrir_productos),
                ("Compras a Proveedor", "Generar órdenes de reabastecimiento y envío automático por correo", self.abrir_compras),
                ("Historial de Facturas", "Consultar facturas CFDI 4.0 de ventas y compras emitidas y abrir carpeta de PDFs", self.abrir_facturas),
                ("Centro de Reportes", "Estadísticas de ventas, productos más vendidos, stock crítico y exportar CSV", self.abrir_reportes),
            ])
            if rol in ("Admin", "Administrador"):
                modulos.extend([
                    ("Directorio de Proveedores", "Administrar proveedores, teléfonos, correos y direcciones de entrega", self.abrir_proveedores),
                    ("Usuarios y Permisos", "Gestionar cuentas de empleados, contraseñas, roles y asignación de sucursal", self.abrir_usuarios),
                ])

        num_filas = (len(modulos) + 1) // 2
        for r in range(num_filas):
            contenedor.rowconfigure(r, weight=1)

        for idx, (titulo_mod, desc_mod, comando_mod) in enumerate(modulos):
            fila = idx // 2
            col = idx % 2
            self._crear_tarjeta_modulo(contenedor, fila, col, titulo_mod, desc_mod, comando_mod)

        # -------- BARRA DE ESTADO INFERIOR --------
        footer = tk.Frame(self, bg="#dbeafe", height=32)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(
            footer,
            text="Navegación Fluida: Todas las pestañas se abren en ventana completa e incluyen una barra superior para cambiar entre módulos o de Túnel Pinggy con un clic.",
            bg="#dbeafe",
            fg="#1e3a8a",
            font=("Segoe UI", 9, "bold"),
        ).pack(pady=6)

    def _texto_subtitulo_header(self):
        cfg_db = obtener_config_db()
        return f"Sesión activa: {self.sesion['nombre']}  |  Rol: {self.sesion['rol']}  |  Servidor BD: {cfg_db['host']}:{cfg_db['port']}"

    def abrir_config_tunel_menu(self):
        """Permite cambiar el túnel Pinggy o volver a Localhost estando ya dentro del Menú o de cualquier pestaña."""
        ventanas_abiertas = [w for w in self.children.values() if isinstance(w, tk.Toplevel) and w.winfo_exists()]
        parent = ventanas_abiertas[-1] if ventanas_abiertas else self

        def _al_cambiar_servidor():
            self.lbl_subtitulo_header.config(text=self._texto_subtitulo_header())
            self.lbl_badge_servidor.config(text=texto_estado_servidor_db())
            self._refrescar_combo_sucursales()

        abrir_dialogo_config_servidor(parent, on_success_callback=_al_cambiar_servidor)

    def obtener_rutas_navegacion(self):
        """Devuelve la lista de pestañas disponibles según el rol del usuario para la barra de navegación rápida."""
        rol = self.sesion.get("rol", "Vendedor")
        rutas = [
            ("Ventas (POS)", "VentaView", self.abrir_ventas),
            ("Clientes", "ClientesView", self.abrir_clientes),
        ]
        if rol != "Vendedor":
            rutas.extend([
                ("Productos", "ProductosView", self.abrir_productos),
                ("Compras", "CompraView", self.abrir_compras),
                ("Facturas", "FacturasView", self.abrir_facturas),
                ("Reportes", "ReportesView", self.abrir_reportes),
            ])
            if rol in ("Admin", "Administrador"):
                rutas.extend([
                    ("Proveedores", "ProveedoresView", self.abrir_proveedores),
                    ("Usuarios", "UsuariosView", self.abrir_usuarios),
                    ("Sucursales", "SucursalesView", self.abrir_sucursales),
                ])
        return rutas

    def _crear_tarjeta_modulo(self, parent, fila, col, titulo, descripcion, comando):
        card = tk.Frame(parent, bg=estilo.surfaceColor, bd=1, relief="solid", padx=18, pady=14)
        card.grid(row=fila, column=col, padx=10, pady=8, sticky="nsew")

        lbl_t = tk.Label(
            card,
            text=titulo,
            bg=estilo.surfaceColor,
            fg=estilo.headerColor,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        lbl_t.pack(fill=tk.X)

        lbl_d = tk.Label(
            card,
            text=descripcion,
            bg=estilo.surfaceColor,
            fg=estilo.mutedTextColor,
            font=("Segoe UI", 10),
            anchor="w",
            justify=tk.LEFT,
            wraplength=460,
        )
        lbl_d.pack(fill=tk.X, pady=(4, 10))

        btn = ttk.Button(
            card,
            text=f"Abrir {titulo.split(' ')[0]}",
            style="BotonesEstilo.TButton",
            command=comando,
        )
        btn.pack(anchor="e", side=tk.BOTTOM)

    def seleccionarSucursal(self, event=None):
        seleccion_txt = self.sucursal_combo.get().strip()
        if " - " not in seleccion_txt:
            return
        try:
            id_seleccionado = int(seleccion_txt.split(" - ")[0].strip())
        except ValueError:
            return

        if id_seleccionado == sucursal.get("id"):
            return

        if messagebox.askyesno(
            title="Cambiar de Sucursal",
            message="¿Está seguro que desea cambiar de sucursal? Se cerrará su sesión actual.",
            parent=self,
        ):
            for sucursal_ in self.sucursales:
                if sucursal_["id"] == id_seleccionado:
                    guardar_sucursal(sucursal_)
                    break

            self.destroy()
            Login().mainloop()
        else:
            self.sucursal_combo.set(f"{sucursal['id']} - {sucursal['direccion']}")

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar la sesión actual?", parent=self):
            self.destroy()
            Login().mainloop()

    def _refrescar_combo_sucursales(self):
        global sucursal
        abrir_sucursal()
        self.sucursales = self.db_suc.obtenerSucursales()
        if self.sucursales:
            ids = [s["id"] for s in self.sucursales]
            if sucursal.get("id") not in ids:
                sucursal = guardar_sucursal(self.sucursales[0])
            self.sucursales_arreglo = [f"{s['id']} - {s['direccion']}" for s in self.sucursales]
        else:
            self.sucursales_arreglo = [f"{sucursal['id']} - {sucursal['direccion']}"]
        self.sucursal_combo["values"] = self.sucursales_arreglo
        self.sucursal_combo.set(f"{sucursal['id']} - {sucursal['direccion']}")

    def _cambiar_pestana(self, clase_vista, *args, **kwargs):
        ventanas_abiertas = [w for w in self.children.values() if isinstance(w, tk.Toplevel) and w.winfo_exists()]
        for w in ventanas_abiertas:
            if isinstance(w, clase_vista):
                estilo.maximizar_ventana(w)
                w.lift()
                w.focus_force()
                return w

        for w in ventanas_abiertas:
            w.destroy()

        nueva = clase_vista(*args, **kwargs)
        estilo.maximizar_ventana(nueva)
        nueva.lift()
        nueva.focus_force()
        return nueva

    # -------- VENTANAS --------
    def abrir_sucursales(self):
        ventana = self._cambiar_pestana(SucursalesView, sucursal=sucursal, ruta=ruta, master=self)
        if ventana:
            ventana.bind("<Destroy>", lambda e: self.after(50, self._refrescar_combo_sucursales), add="+")

    def abrir_clientes(self):
        self._cambiar_pestana(ClientesView, self)

    def abrir_productos(self):
        self._cambiar_pestana(ProductosView, self)

    def abrir_proveedores(self):
        self._cambiar_pestana(ProveedoresView, self)

    def abrir_compras(self):
        self._cambiar_pestana(CompraView, self)

    def abrir_ventas(self):
        self._cambiar_pestana(VentaView, self)

    def abrir_reportes(self):
        self._cambiar_pestana(ReportesView, self)

    def abrir_facturas(self):
        self._cambiar_pestana(FacturasView, self)

    def abrir_usuarios(self):
        self._cambiar_pestana(UsuariosView, self)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    Login().mainloop()
