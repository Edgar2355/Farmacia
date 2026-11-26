import tkinter as tk
from tkinter import ttk, messagebox, END
from .dbCliente import dbCliente
from ... import estilo
from ...Servicios.validaciones import validar_correo, validar_telefono, validar_entero_positivo


class ClientesView(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Gestión de Clientes - Farmacia CUCEI")
        estilo.centrar_ventana(self, 860, 620)
        self.configure(background=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        self.db = dbCliente()

        estilo.crear_encabezado(
            self,
            "DIRECTORIO Y GESTIÓN DE CLIENTES",
            "Esc para salir | Clic en una fila para editar",
        )

        # -------- BARRA DE BÚSQUEDA --------
        search_bar = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=14, pady=8)
        search_bar.pack(fill=tk.X, padx=18, pady=(12, 8))

        tk.Label(
            search_bar,
            text="Filtro rápido (ID / Nombre / RFC / Ciudad):",
            bg=estilo.surfaceColor,
            fg=estilo.textColor,
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.txt_buscar = ttk.Entry(search_bar, width=38)
        self.txt_buscar.pack(side=tk.LEFT, padx=(0, 8))
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.filtrar_tabla())

        ttk.Button(search_bar, text="Buscar por ID", style="BotonesEstilo.TButton", command=self.buscar_cliente).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(search_bar, text="Mostrar Todos", style="BotonesEstilo.TButton", command=self.cargar_tabla).pack(side=tk.LEFT)

        # -------- TARJETA DE FORMULARIO --------
        card_form = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_form.pack(fill=tk.X, padx=18, pady=(0, 8))

        self.lbl_modo = tk.Label(
            card_form,
            text="MODO: REGISTRAR NUEVO CLIENTE",
            bg="#dcfce7",
            fg="#166534",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        )
        self.lbl_modo.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))

        tk.Label(card_form, text="ID (Auto):", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.txt_id = ttk.Entry(card_form, width=12)
        self.txt_id.grid(row=1, column=1, sticky="w", padx=(6, 16), pady=5)

        tk.Label(card_form, text="Nombre Completo *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=2, sticky="w", pady=5)
        self.txt_nombre = ttk.Entry(card_form, width=32)
        self.txt_nombre.grid(row=1, column=3, columnspan=3, sticky="ew", padx=(6, 0), pady=5)

        tk.Label(card_form, text="Teléfono *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.txt_telefono = ttk.Entry(card_form, width=18)
        self.txt_telefono.grid(row=2, column=1, sticky="w", padx=(6, 16), pady=5)

        tk.Label(card_form, text="Correo Electrónico:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=2, sticky="w", pady=5)
        self.txt_correo = ttk.Entry(card_form, width=32)
        self.txt_correo.grid(row=2, column=3, columnspan=3, sticky="ew", padx=(6, 0), pady=5)

        tk.Label(card_form, text="RFC:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        self.txt_rfc = ttk.Entry(card_form, width=18)
        self.txt_rfc.grid(row=3, column=1, sticky="w", padx=(6, 16), pady=5)

        tk.Label(card_form, text="Ciudad:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=3, column=2, sticky="w", pady=5)
        self.txt_ciudad = ttk.Entry(card_form, width=22)
        self.txt_ciudad.grid(row=3, column=3, sticky="w", padx=(6, 16), pady=5)

        tk.Label(card_form, text="Puntos:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=3, column=4, sticky="w", pady=5)
        self.txt_puntos = ttk.Entry(card_form, width=10)
        self.txt_puntos.grid(row=3, column=5, sticky="w", padx=(6, 0), pady=5)

        # -------- BOTONES DE ACCIÓN --------
        btn_row = tk.Frame(card_form, bg=estilo.surfaceColor)
        btn_row.grid(row=4, column=0, columnspan=6, sticky="ew", pady=(10, 2))

        self.btn_guardar = ttk.Button(btn_row, text="Guardar Cliente", style="BotonesAceptar.TButton", command=self.guardar_cliente)
        self.btn_guardar.pack(side=tk.LEFT, padx=(0, 8))

        self.EliminarBoton = ttk.Button(
            btn_row,
            text="Eliminar Seleccionado",
            style="BotonesRechazar.TButton",
            command=self.eliminar_cliente,
            state="disabled",
        )
        self.EliminarBoton.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(btn_row, text="Limpiar / Nuevo", style="BotonesEstilo.TButton", command=self.limpiar_campos).pack(side=tk.LEFT)

        # -------- TABLA TREEVIEW --------
        frame_tabla = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))

        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        columnas = ("ID", "Nombre", "Telefono", "Correo", "RFC", "Ciudad", "Puntos")
        self.tabla = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="browse",
        )
        scroll_y.config(command=self.tabla.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        anchos = {
            "ID": 55,
            "Nombre": 180,
            "Telefono": 110,
            "Correo": 180,
            "RFC": 110,
            "Ciudad": 110,
            "Puntos": 70,
        }
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=anchos[col], anchor=tk.CENTER if col in ("ID", "Puntos") else tk.W)

        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_fila)

        self.cargar_tabla()
        self.after_idle_id = None

    def cargar_tabla(self, datos=None):
        self.clientes_cache = datos if datos is not None else self.db.obtener_todos()
        self._render_tabla(self.clientes_cache)

    def _render_tabla(self, clientes):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for c in clientes:
            self.tabla.insert(
                "",
                END,
                values=(
                    c["id"],
                    c["nombre"] or "",
                    c["telefono"] or "",
                    c["correo"] or "",
                    c["rfc"] or "",
                    c["ciudad"] or "",
                    c["puntos"] if c["puntos"] is not None else 0,
                ),
            )

    def filtrar_tabla(self):
        texto = self.txt_buscar.get().strip().lower()
        if not texto:
            self._render_tabla(getattr(self, "clientes_cache", []))
            return
        filtrados = [
            c for c in getattr(self, "clientes_cache", [])
            if texto in str(c.get("id", "")).lower()
            or texto in str(c.get("nombre", "")).lower()
            or texto in str(c.get("telefono", "")).lower()
            or texto in str(c.get("correo", "")).lower()
            or texto in str(c.get("rfc", "")).lower()
            or texto in str(c.get("ciudad", "")).lower()
        ]
        self._render_tabla(filtrados)

    def _poblar_formulario(self, cliente):
        self.txt_id.delete(0, END)
        self.txt_id.insert(0, cliente["id"])

        self.txt_nombre.delete(0, END)
        self.txt_nombre.insert(0, cliente["nombre"] or "")

        self.txt_telefono.delete(0, END)
        self.txt_telefono.insert(0, cliente["telefono"] or "")

        self.txt_correo.delete(0, END)
        self.txt_correo.insert(0, cliente["correo"] or "")

        self.txt_rfc.delete(0, END)
        self.txt_rfc.insert(0, cliente["rfc"] or "")

        self.txt_ciudad.delete(0, END)
        self.txt_ciudad.insert(0, cliente["ciudad"] or "")

        self.txt_puntos.delete(0, END)
        self.txt_puntos.insert(0, cliente["puntos"] if cliente["puntos"] is not None else 0)

        self.lbl_modo.config(
            text=f"MODO: EDITANDO CLIENTE #{cliente['id']} ({cliente['nombre']})",
            bg="#dbeafe",
            fg="#1e3a8a",
        )
        self.btn_guardar.config(text="Actualizar Cliente")
        self.EliminarBoton.config(state="normal")

    def seleccionar_fila(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        valores = self.tabla.item(sel[0], "values")
        cliente = self.db.buscar(valores[0])
        if cliente:
            self._poblar_formulario(cliente)

    def buscar_cliente(self):
        id_cliente = self.txt_id.get().strip() or self.txt_buscar.get().strip()
        if id_cliente == "":
            messagebox.showwarning("Error", "Ingresa un ID a buscar", parent=self)
            return

        cliente = self.db.buscar(id_cliente)
        if cliente:
            self._poblar_formulario(cliente)
        else:
            messagebox.showerror(parent=self, title="Error", message="Cliente no encontrado")

    def guardar_cliente(self):
        id_cliente = self.txt_id.get().strip()
        nombre = self.txt_nombre.get().strip()
        telefono = self.txt_telefono.get().strip()
        correo = self.txt_correo.get().strip()
        rfc = self.txt_rfc.get().strip().upper()
        ciudad = self.txt_ciudad.get().strip()
        puntos_str = self.txt_puntos.get().strip()

        if nombre == "" or telefono == "":
            messagebox.showwarning("Validación", "Nombre y teléfono son obligatorios", parent=self)
            return

        ok_tel, msg_tel = validar_telefono(telefono, obligatorio=True)
        if not ok_tel:
            messagebox.showwarning("Validación", msg_tel, parent=self)
            return

        ok_cor, msg_cor = validar_correo(correo, obligatorio=False)
        if not ok_cor:
            messagebox.showwarning("Validación", msg_cor, parent=self)
            return

        if puntos_str == "":
            puntos = 0
        else:
            ok_pts, msg_pts, puntos = validar_entero_positivo(puntos_str, "Puntos", permitir_cero=True)
            if not ok_pts:
                messagebox.showwarning("Validación", msg_pts, parent=self)
                return

        if id_cliente != "":
            ok = self.db.actualizar(id_cliente, nombre, telefono, correo, rfc, ciudad, puntos)
            if ok:
                messagebox.showinfo("OK", "Cliente actualizado correctamente", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo actualizar el cliente", parent=self)
        else:
            ok = self.db.insertar(nombre, telefono, correo, rfc, ciudad, puntos)
            if ok:
                messagebox.showinfo("OK", "Cliente registrado correctamente", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo guardar el cliente", parent=self)

        self.limpiar_campos()
        self.cargar_tabla()

    def eliminar_cliente(self):
        id_cliente = self.txt_id.get().strip()
        if id_cliente == "":
            messagebox.showwarning("Error", "Selecciona o ingresa un ID", parent=self)
            return

        confirm = messagebox.askyesno("Confirmar", "¿Eliminar cliente seleccionado?", parent=self)
        if confirm:
            ok = self.db.eliminar(id_cliente)
            if ok:
                messagebox.showinfo("OK", "Cliente eliminado", parent=self)
                self.limpiar_campos()
                self.cargar_tabla()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo eliminar el cliente (puede tener historial de ventas).",
                    parent=self,
                )

    def limpiar_campos(self):
        self.txt_id.delete(0, END)
        self.txt_nombre.delete(0, END)
        self.txt_telefono.delete(0, END)
        self.txt_correo.delete(0, END)
        self.txt_rfc.delete(0, END)
        self.txt_ciudad.delete(0, END)
        self.txt_puntos.delete(0, END)
        self.txt_buscar.delete(0, END)
        self.lbl_modo.config(
            text="MODO: REGISTRAR NUEVO CLIENTE",
            bg="#dcfce7",
            fg="#166534",
        )
        self.btn_guardar.config(text="Guardar Cliente")
        self.EliminarBoton.config(state="disabled")
