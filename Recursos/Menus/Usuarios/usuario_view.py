import tkinter as tk
from tkinter import ttk, messagebox, END
from .dbUsuario import dbUsuario
from ..Sucursales.dbSucursal import dbSucursal
from ... import estilo


class UsuariosView(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Gestión de Usuarios y Permisos - Farmacia CUCEI")
        estilo.centrar_ventana(self, 840, 580)
        self.configure(background=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        self.db = dbUsuario()
        self.db_sucursal = dbSucursal()
        self.id_seleccionado = None

        estilo.crear_encabezado(
            self,
            "ADMINISTRACIÓN DE USUARIOS Y ROLES",
            "Esc para salir | Clic en una fila para editar",
        )

        # -------- BARRA DE BÚSQUEDA --------
        search_bar = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=14, pady=8)
        search_bar.pack(fill=tk.X, padx=18, pady=(12, 8))

        tk.Label(search_bar, text="Buscar (Nombre / Usuario / Rol):", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.txt_buscar = ttk.Entry(search_bar, width=36)
        self.txt_buscar.pack(side=tk.LEFT, padx=(0, 8))
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.filtrar_tabla())
        ttk.Button(search_bar, text="Ver Todos", style="BotonesEstilo.TButton", command=self.cargar_tabla).pack(side=tk.LEFT)

        # -------- TARJETA DE FORMULARIO --------
        card_form = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_form.pack(fill=tk.X, padx=18, pady=(0, 8))

        tk.Label(card_form, text="Nombre Completo *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.txt_nombre = ttk.Entry(card_form, width=30)
        self.txt_nombre.grid(row=0, column=1, sticky="w", padx=(8, 20), pady=5)

        tk.Label(card_form, text="Usuario (Login) *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", pady=5)
        self.txt_usuario = ttk.Entry(card_form, width=26)
        self.txt_usuario.grid(row=0, column=3, sticky="w", padx=(8, 0), pady=5)

        tk.Label(card_form, text="Contraseña:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.txt_password = ttk.Entry(card_form, width=30, show="*")
        self.txt_password.grid(row=1, column=1, sticky="w", padx=(8, 20), pady=5)

        tk.Label(card_form, text="Rol *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=2, sticky="w", pady=5)
        self.cmb_rol = ttk.Combobox(card_form, values=["Administrador", "Admin", "Gerente", "Vendedor"], state="readonly", width=24)
        self.cmb_rol.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=5)

        tk.Label(card_form, text="Sucursal Asignada *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.cmb_sucursal = ttk.Combobox(card_form, state="readonly", width=55)
        self.cmb_sucursal.grid(row=2, column=1, columnspan=3, sticky="w", padx=(8, 0), pady=5)

        btn_row = tk.Frame(card_form, bg=estilo.surfaceColor)
        btn_row.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 2))

        ttk.Button(btn_row, text="Guardar / Actualizar", style="BotonesAceptar.TButton", command=self.guardar).pack(side=tk.LEFT, padx=(0, 8))
        self.btn_eliminar = ttk.Button(
            btn_row,
            text="Eliminar Seleccionado",
            style="BotonesRechazar.TButton",
            command=self.eliminar,
            state="disabled",
        )
        self.btn_eliminar.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="Limpiar / Nuevo", style="BotonesEstilo.TButton", command=self.limpiar).pack(side=tk.LEFT)

        # -------- TABLA --------
        frame_tabla = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))

        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        columnas = ("ID", "Nombre", "Usuario", "Rol", "Sucursal")
        self.tabla = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="browse",
        )
        scroll_y.config(command=self.tabla.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        anchos = {"ID": 55, "Nombre": 200, "Usuario": 140, "Rol": 120, "Sucursal": 260}
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=anchos[col], anchor=tk.CENTER if col in ("ID", "Rol") else tk.W)

        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_fila)

        self.cargar_sucursales()
        self.cargar_tabla()

    def cargar_sucursales(self):
        self.sucursales = self.db_sucursal.obtenerSucursales()
        opciones = [f"{s['id']} - {s['direccion']}" for s in self.sucursales]
        self.cmb_sucursal["values"] = opciones

    def _obtener_sucursal_id_combo(self):
        valor = self.cmb_sucursal.get().strip()
        if not valor or " - " not in valor:
            return None
        try:
            return int(valor.split(" - ")[0].strip())
        except ValueError:
            return None

    def cargar_tabla(self, datos=None):
        self.usuarios_cache = datos if datos is not None else self.db.obtener_todos()
        self._render_tabla(self.usuarios_cache)

    def _render_tabla(self, usuarios):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for u in usuarios:
            suc_texto = f"{u['sucursal_id']} - {u.get('sucursal_nombre') or 'N/A'}"
            self.tabla.insert(
                "",
                END,
                values=(u["id"], u["nombre"], u["usuario"], u["rol"], suc_texto),
            )

    def filtrar_tabla(self):
        texto = self.txt_buscar.get().strip().lower()
        if not texto:
            self._render_tabla(getattr(self, "usuarios_cache", []))
            return
        filtrados = [
            u for u in getattr(self, "usuarios_cache", [])
            if texto in str(u.get("nombre", "")).lower()
            or texto in str(u.get("usuario", "")).lower()
            or texto in str(u.get("rol", "")).lower()
        ]
        self._render_tabla(filtrados)

    def seleccionar_fila(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        valores = self.tabla.item(sel[0], "values")
        self.id_seleccionado = valores[0]

        self.txt_nombre.delete(0, END)
        self.txt_nombre.insert(0, valores[1])

        self.txt_usuario.delete(0, END)
        self.txt_usuario.insert(0, valores[2])

        self.txt_password.delete(0, END)
        self.cmb_rol.set(valores[3])
        self.cmb_sucursal.set(valores[4])
        self.btn_eliminar.config(state="normal")

    def guardar(self):
        nombre = self.txt_nombre.get().strip()
        usuario = self.txt_usuario.get().strip()
        password = self.txt_password.get().strip()
        rol = self.cmb_rol.get().strip()
        sucursal_id = self._obtener_sucursal_id_combo()

        if not nombre or not usuario or not rol or sucursal_id is None:
            messagebox.showwarning(
                "Validación",
                "Nombre, usuario, rol y sucursal son obligatorios.",
                parent=self,
            )
            return

        if self.id_seleccionado is None:
            if not password:
                messagebox.showwarning(
                    "Validación",
                    "La contraseña es obligatoria para crear un nuevo usuario.",
                    parent=self,
                )
                return
            ok, msg = self.db.insertar(nombre, usuario, password, rol, sucursal_id)
        else:
            ok, msg = self.db.actualizar(self.id_seleccionado, nombre, usuario, password, rol, sucursal_id)

        if ok:
            messagebox.showinfo("OK", msg, parent=self)
            self.limpiar()
            self.cargar_tabla()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def eliminar(self):
        if self.id_seleccionado is None:
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar usuario seleccionado?", parent=self):
            return
        if self.db.eliminar(self.id_seleccionado):
            messagebox.showinfo("OK", "Usuario eliminado correctamente", parent=self)
            self.limpiar()
            self.cargar_tabla()
        else:
            messagebox.showerror("Error", "No se pudo eliminar el usuario", parent=self)

    def limpiar(self):
        self.id_seleccionado = None
        self.txt_nombre.delete(0, END)
        self.txt_usuario.delete(0, END)
        self.txt_password.delete(0, END)
        self.txt_buscar.delete(0, END)
        self.cmb_rol.set("")
        self.cmb_sucursal.set("")
        self.btn_eliminar.config(state="disabled")
