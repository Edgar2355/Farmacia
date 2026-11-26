import tkinter as tk
from tkinter import ttk, messagebox
from .proveedor import Proveedor
from .dbproveedor import DBProveedor
from ... import estilo
from ...Servicios.validaciones import validar_correo, validar_telefono


class ProveedoresView(tk.Toplevel):

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Directorio de Proveedores - Farmacia CUCEI")
        estilo.centrar_ventana(self, 860, 600)
        self.configure(bg=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        self.db = DBProveedor()
        self.id = None

        estilo.crear_encabezado(
            self,
            "DIRECTORIO DE PROVEEDORES",
            "Esc para salir | Clic en una fila para editar",
        )

        # -------- BARRA DE FILTROS --------
        search_bar = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=14, pady=8)
        search_bar.pack(fill=tk.X, padx=18, pady=(12, 8))

        tk.Label(search_bar, text="ID:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.buscar_id = ttk.Entry(search_bar, width=8)
        self.buscar_id.pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(search_bar, text="Buscar ID", style="BotonesEstilo.TButton", command=self.buscar_por_id).pack(side=tk.LEFT, padx=(0, 14))

        tk.Label(search_bar, text="Nombre:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.buscar_nombre = ttk.Entry(search_bar, width=20)
        self.buscar_nombre.pack(side=tk.LEFT, padx=(0, 14))
        self.buscar_nombre.bind("<KeyRelease>", lambda e: self.buscar_por_nombre())

        tk.Label(search_bar, text="Correo:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.buscar_correo = ttk.Entry(search_bar, width=20)
        self.buscar_correo.pack(side=tk.LEFT, padx=(0, 14))
        self.buscar_correo.bind("<KeyRelease>", lambda e: self.buscar_por_correo())

        ttk.Button(search_bar, text="Mostrar Todos", style="BotonesEstilo.TButton", command=self.cargar).pack(side=tk.RIGHT)

        # -------- TARJETA DE FORMULARIO --------
        card_form = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_form.pack(fill=tk.X, padx=18, pady=(0, 8))

        tk.Label(card_form, text="Nombre / Empresa *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.nombre = ttk.Entry(card_form, width=32)
        self.nombre.grid(row=0, column=1, sticky="w", padx=(8, 20), pady=5)

        tk.Label(card_form, text="Correo de Pedidos *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", pady=5)
        self.correo = ttk.Entry(card_form, width=34)
        self.correo.grid(row=0, column=3, sticky="w", padx=(8, 0), pady=5)

        tk.Label(card_form, text="Teléfono *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.telefono = ttk.Entry(card_form, width=32)
        self.telefono.grid(row=1, column=1, sticky="w", padx=(8, 20), pady=5)

        tk.Label(card_form, text="Dirección:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=2, sticky="w", pady=5)
        self.direccion = ttk.Entry(card_form, width=34)
        self.direccion.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=5)

        btn_row = tk.Frame(card_form, bg=estilo.surfaceColor)
        btn_row.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 2))

        ttk.Button(btn_row, text="Guardar Nuevo", style="BotonesAceptar.TButton", command=self.guardar).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="Actualizar Seleccionado", style="BotonesEstilo.TButton", command=self.actualizar).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="Eliminar", style="BotonesRechazar.TButton", command=self.eliminar).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="Limpiar / Nuevo", style="BotonesEstilo.TButton", command=self.limpiar).pack(side=tk.LEFT)

        # -------- TABLA --------
        frame_tabla = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))

        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        columnas = ("ID", "Nombre", "Correo", "Telefono", "Direccion")
        self.tabla = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="browse",
        )
        scroll_y.config(command=self.tabla.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        anchos = {"ID": 55, "Nombre": 180, "Correo": 200, "Telefono": 120, "Direccion": 230}
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=anchos[col], anchor=tk.CENTER if col == "ID" else tk.W)

        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar)

        self.cargar()

    def _validar(self):
        nom = self.nombre.get().strip()
        cor = self.correo.get().strip()
        tel = self.telefono.get().strip()
        dir_ = self.direccion.get().strip()

        if not nom:
            messagebox.showwarning("Validación", "El nombre del proveedor es obligatorio.", parent=self)
            return None

        ok_c, msg_c = validar_correo(cor, obligatorio=True)
        if not ok_c:
            messagebox.showwarning("Validación", msg_c, parent=self)
            return None

        ok_t, msg_t = validar_telefono(tel, obligatorio=True)
        if not ok_t:
            messagebox.showwarning("Validación", msg_t, parent=self)
            return None

        return nom, cor, tel, dir_

    def guardar(self):
        validados = self._validar()
        if not validados:
            return
        p = Proveedor(None, *validados)
        if self.db.insertar(p):
            messagebox.showinfo("Éxito", "Proveedor guardado correctamente", parent=self)
            self.limpiar()
            self.cargar()
        else:
            messagebox.showerror("Error", "No se pudo guardar el proveedor", parent=self)

    def actualizar(self):
        if not self.id:
            messagebox.showwarning("Aviso", "Selecciona un proveedor de la tabla para actualizar", parent=self)
            return
        validados = self._validar()
        if not validados:
            return
        p = Proveedor(self.id, *validados)
        if self.db.actualizar(p):
            messagebox.showinfo("Éxito", "Proveedor actualizado correctamente", parent=self)
            self.limpiar()
            self.cargar()
        else:
            messagebox.showerror("Error", "No se pudo actualizar el proveedor", parent=self)

    def eliminar(self):
        if not self.id:
            messagebox.showwarning("Aviso", "Selecciona un proveedor de la tabla para eliminar", parent=self)
            return
        confirmar = messagebox.askyesno("Confirmar", "¿Eliminar proveedor seleccionado?", parent=self)
        if confirmar:
            eliminado = self.db.eliminar(self.id)
            if eliminado:
                messagebox.showinfo("Éxito", "Proveedor eliminado correctamente", parent=self)
                self.cargar()
                self.limpiar()
            else:
                messagebox.showerror(
                    "Error",
                    "No se puede eliminar porque tiene productos o compras asociados",
                    parent=self,
                )

    def limpiar(self):
        self.id = None
        self.nombre.delete(0, tk.END)
        self.correo.delete(0, tk.END)
        self.telefono.delete(0, tk.END)
        self.direccion.delete(0, tk.END)
        self.buscar_id.delete(0, tk.END)
        self.buscar_nombre.delete(0, tk.END)
        self.buscar_correo.delete(0, tk.END)

    def cargar(self):
        self.proveedores_cache = self.db.obtener()
        self.mostrar_datos(self.proveedores_cache)

    def mostrar_datos(self, datos):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for p in datos:
            valores = tuple(x if x is not None else "" for x in p)
            self.tabla.insert("", "end", values=valores)

    def seleccionar(self, event):
        if not self.tabla.selection():
            return

        item = self.tabla.selection()[0]
        datos = self.tabla.item(item, "values")

        self.id = datos[0]

        self.nombre.delete(0, tk.END)
        self.nombre.insert(0, datos[1])

        self.correo.delete(0, tk.END)
        self.correo.insert(0, datos[2])

        self.telefono.delete(0, tk.END)
        self.telefono.insert(0, datos[3])

        self.direccion.delete(0, tk.END)
        if len(datos) > 4:
            self.direccion.insert(0, datos[4])

    def buscar_por_id(self):
        val = self.buscar_id.get().strip()
        if not val:
            self.cargar()
            return
        datos = self.db.buscar_por_id(val)
        self.mostrar_datos(datos)

    def buscar_por_nombre(self):
        texto = self.buscar_nombre.get().strip().lower()
        if not texto:
            self.mostrar_datos(getattr(self, "proveedores_cache", []))
            return
        filtrados = [p for p in getattr(self, "proveedores_cache", []) if texto in str(p[1] or "").lower()]
        self.mostrar_datos(filtrados)

    def buscar_por_correo(self):
        texto = self.buscar_correo.get().strip().lower()
        if not texto:
            self.mostrar_datos(getattr(self, "proveedores_cache", []))
            return
        filtrados = [p for p in getattr(self, "proveedores_cache", []) if texto in str(p[2] or "").lower()]
        self.mostrar_datos(filtrados)
