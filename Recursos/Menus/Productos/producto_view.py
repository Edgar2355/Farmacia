import tkinter as tk
from tkinter import ttk, messagebox, END
from .dbproducto import dbProducto
from ... import estilo
from ...Servicios.validaciones import validar_entero_positivo, validar_flotante_positivo


class ProductosView(tk.Toplevel):

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Gestión de Productos e Inventario - Farmacia CUCEI")
        estilo.centrar_ventana(self, 900, 660)
        self.configure(bg=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        self.db = dbProducto()

        estilo.crear_encabezado(
            self,
            "CATÁLOGO E INVENTARIO DE PRODUCTOS",
            "Esc para salir | Filas en rojo indican Stock Bajo (<= 5)",
        )

        # -------- BARRA DE BÚSQUEDA --------
        search_bar = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=14, pady=8)
        search_bar.pack(fill=tk.X, padx=18, pady=(12, 8))

        tk.Label(
            search_bar,
            text="Buscar producto (Nombre / Categoría / ID):",
            bg=estilo.surfaceColor,
            fg=estilo.textColor,
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.txt_buscar = ttk.Entry(search_bar, width=38)
        self.txt_buscar.pack(side=tk.LEFT, padx=(0, 8))
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.filtrar_tabla())

        ttk.Button(search_bar, text="Buscar Exacto", style="BotonesEstilo.TButton", command=self.buscar_producto).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(search_bar, text="Ver Todos", style="BotonesEstilo.TButton", command=self.cargar_tabla).pack(side=tk.LEFT)

        # -------- TARJETA DE FORMULARIO --------
        card_form = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_form.pack(fill=tk.X, padx=18, pady=(0, 8))

        self.ID = self.db.getMaxID() + 1

        tk.Label(card_form, text="ID:", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.txt_id = ttk.Entry(card_form, width=12)
        self.txt_id.grid(row=0, column=1, sticky="w", padx=(6, 16), pady=5)
        self.txt_id.insert(0, self.ID)
        self.txt_id.config(state="disabled")

        tk.Label(card_form, text="Nombre *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", pady=5)
        self.txt_nombre = ttk.Entry(card_form, width=30)
        self.txt_nombre.grid(row=0, column=3, sticky="w", padx=(6, 16), pady=5)

        tk.Label(card_form, text="Categoría *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=4, sticky="w", pady=5)
        self.cmb_tipo = ttk.Combobox(
            card_form,
            values=["Medicamento", "Higiene", "Bebidas", "Snacks", "Otro"],
            state="readonly",
            width=18,
        )
        self.cmb_tipo.grid(row=0, column=5, sticky="w", padx=(6, 0), pady=5)

        tk.Label(card_form, text="Proveedor *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.cmb_proveedor = ttk.Combobox(card_form, state="readonly", width=26)
        self.cmb_proveedor.grid(row=1, column=1, columnspan=2, sticky="w", padx=(6, 16), pady=5)

        self.receta = tk.IntVar()
        self.Check_receta = tk.Checkbutton(
            card_form,
            text="¿Requiere receta médica?",
            variable=self.receta,
            background=estilo.surfaceColor,
            font=("Segoe UI", 10, "bold"),
        )
        self.Check_receta.grid(row=1, column=3, columnspan=3, sticky="w", padx=(6, 0), pady=5)

        tk.Label(card_form, text="Precio Compra *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.txt_compra = ttk.Entry(card_form, width=16)
        self.txt_compra.grid(row=2, column=1, sticky="w", padx=(6, 16), pady=5)

        tk.Label(card_form, text="Precio Venta *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=2, sticky="w", pady=5)
        self.txt_venta = ttk.Entry(card_form, width=16)
        self.txt_venta.grid(row=2, column=3, sticky="w", padx=(6, 16), pady=5)

        tk.Label(card_form, text="Stock Actual *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=4, sticky="w", pady=5)
        self.txt_stock = ttk.Entry(card_form, width=14)
        self.txt_stock.grid(row=2, column=5, sticky="w", padx=(6, 0), pady=5)

        # -------- BARRA DE BOTONES Y VALOR INVENTARIO --------
        btn_row = tk.Frame(card_form, bg=estilo.surfaceColor)
        btn_row.grid(row=3, column=0, columnspan=6, sticky="ew", pady=(10, 2))

        self.agregar_button = ttk.Button(btn_row, text="Agregar Nuevo", style="BotonesAceptar.TButton", command=self.agregar)
        self.agregar_button.pack(side=tk.LEFT, padx=(0, 8))

        self.editar_button = ttk.Button(btn_row, text="Guardar Cambios", style="BotonesEstilo.TButton", state="disabled", command=self.editar)
        self.editar_button.pack(side=tk.LEFT, padx=(0, 8))

        self.eliminar_button = ttk.Button(btn_row, text="Eliminar", style="BotonesRechazar.TButton", state="disabled", command=self.eliminar)
        self.eliminar_button.pack(side=tk.LEFT, padx=(0, 8))

        self.limpiar_button = ttk.Button(btn_row, text="Limpiar / Nuevo", style="BotonesEstilo.TButton", command=self.limpiar)
        self.limpiar_button.pack(side=tk.LEFT)

        val_frame = tk.Frame(btn_row, bg=estilo.surfaceColor)
        val_frame.pack(side=tk.RIGHT)
        tk.Label(val_frame, text="Valor Total Stock:", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.txt_total = ttk.Entry(val_frame, state="readonly", width=16)
        self.txt_total.pack(side=tk.LEFT)

        self.txt_venta.bind("<KeyRelease>", self.calcular_total)
        self.txt_stock.bind("<KeyRelease>", self.calcular_total)

        # -------- TABLA TREEVIEW --------
        frame_tabla = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))

        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        columnas = ("ID", "Nombre", "Tipo", "Proveedor", "Compra", "Venta", "Stock", "Receta")
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
            "Nombre": 200,
            "Tipo": 110,
            "Proveedor": 160,
            "Compra": 90,
            "Venta": 90,
            "Stock": 75,
            "Receta": 75,
        }
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=anchos[col], anchor=tk.CENTER if col != "Nombre" else tk.W)

        self.tabla.tag_configure("stock_bajo", background=estilo.DangerRowBg, foreground=estilo.DangerRowFg)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_fila)

        self.cargar_proveedores()
        self.cargar_tabla()

    def cargar_proveedores(self):
        self.lista_proveedores = self.db.obtener_proveedores()
        nombres = [p["nombre"] for p in self.lista_proveedores]
        self.cmb_proveedor["values"] = nombres

    def obtener_id_proveedor(self):
        nombre = self.cmb_proveedor.get()
        for p in self.lista_proveedores:
            if p["nombre"] == nombre:
                return p["id"]
        return None

    def cargar_tabla(self, datos=None):
        self.productos_cache = datos if datos is not None else self.db.obtener_todos()
        self._render_tabla(self.productos_cache)

    def _render_tabla(self, productos):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for p in productos:
            stock_val = int(p.get("stock") or 0)
            tags = ("stock_bajo",) if stock_val <= 5 else ()
            self.tabla.insert(
                "",
                END,
                values=(
                    p["id"],
                    p["nombre"],
                    p["tipo"],
                    p.get("proveedor") or "Sin proveedor",
                    f"${float(p['precio_compra'] or 0):.2f}",
                    f"${float(p['precio_venta'] or 0):.2f}",
                    stock_val,
                    "Sí" if p.get("receta") else "No",
                ),
                tags=tags,
            )

    def filtrar_tabla(self):
        texto = self.txt_buscar.get().strip().lower()
        if not texto:
            self._render_tabla(getattr(self, "productos_cache", []))
            return
        filtrados = [
            p for p in getattr(self, "productos_cache", [])
            if texto in str(p.get("id", "")).lower()
            or texto in str(p.get("nombre", "")).lower()
            or texto in str(p.get("tipo", "")).lower()
            or texto in str(p.get("proveedor", "")).lower()
        ]
        self._render_tabla(filtrados)

    def _cargar_producto_en_formulario(self, producto):
        self.txt_id.config(state="normal")
        self.txt_id.delete(0, END)
        self.txt_id.insert(0, producto["id"])
        self.txt_id.config(state="disabled")

        self.txt_nombre.delete(0, END)
        self.txt_nombre.insert(0, producto["nombre"] or "")

        self.cmb_tipo.set(producto["tipo"] or "")
        if producto.get("receta"):
            self.Check_receta.select()
            self.receta.set(1)
        else:
            self.Check_receta.deselect()
            self.receta.set(0)

        self.cmb_proveedor.set("")
        for p in self.lista_proveedores:
            if p["id"] == producto["id_proveedor"]:
                self.cmb_proveedor.set(p["nombre"])
                break

        self.txt_compra.delete(0, END)
        self.txt_compra.insert(0, producto["precio_compra"])

        self.txt_venta.delete(0, END)
        self.txt_venta.insert(0, producto["precio_venta"])

        self.txt_stock.delete(0, END)
        self.txt_stock.insert(0, producto["stock"])

        self.calcular_total()

        self.agregar_button.config(state="disabled")
        self.editar_button.config(state="normal")
        self.eliminar_button.config(state="normal")

    def seleccionar_fila(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        valores = self.tabla.item(sel[0], "values")
        producto = self.db.buscar(valores[1])
        if producto:
            self._cargar_producto_en_formulario(producto)

    def buscar_producto(self):
        nombre = self.txt_buscar.get().strip()
        if nombre == "":
            messagebox.showwarning("Error", "Escribe un nombre de producto", parent=self)
            return

        producto = self.db.buscar(nombre)
        if producto:
            self._cargar_producto_en_formulario(producto)
        else:
            messagebox.showerror("Error", "Producto no encontrado en esta sucursal", parent=self)

    def _validar_formulario(self):
        nombre = self.txt_nombre.get().strip()
        tipo = self.cmb_tipo.get().strip()
        id_proveedor = self.obtener_id_proveedor()

        if not nombre:
            messagebox.showwarning("Validación", "El nombre del producto es obligatorio.", parent=self)
            return None
        if not tipo:
            messagebox.showwarning("Validación", "Selecciona el tipo de producto.", parent=self)
            return None
        if not id_proveedor:
            messagebox.showwarning("Validación", "Selecciona un proveedor.", parent=self)
            return None

        ok_c, msg_c, compra = validar_flotante_positivo(self.txt_compra.get(), "Precio compra")
        if not ok_c:
            messagebox.showwarning("Validación", msg_c, parent=self)
            return None

        ok_v, msg_v, venta = validar_flotante_positivo(self.txt_venta.get(), "Precio venta")
        if not ok_v:
            messagebox.showwarning("Validación", msg_v, parent=self)
            return None

        ok_s, msg_s, stock = validar_entero_positivo(self.txt_stock.get(), "Stock", permitir_cero=True)
        if not ok_s:
            messagebox.showwarning("Validación", msg_s, parent=self)
            return None

        return nombre, tipo, id_proveedor, compra, venta, stock, self.receta.get()

    def agregar(self):
        datos = self._validar_formulario()
        if not datos:
            return
        try:
            self.db.insertar(*datos)
            messagebox.showinfo("OK", "Producto agregado correctamente", parent=self)
            self.limpiar()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def editar(self):
        datos = self._validar_formulario()
        if not datos:
            return
        try:
            self.db.editar(self.txt_id.get(), *datos)
            messagebox.showinfo("OK", "Producto actualizado correctamente", parent=self)
            self.limpiar()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def eliminar(self):
        idp = self.txt_id.get()
        if idp == "":
            messagebox.showwarning("Error", "Selecciona un producto", parent=self)
            return

        if not messagebox.askyesno("Confirmar", "¿Deseas eliminar este producto?", parent=self):
            return

        if self.db.eliminar(idp):
            messagebox.showinfo("OK", "Producto eliminado", parent=self)
            self.limpiar()
            self.cargar_tabla()
        else:
            messagebox.showerror(
                "Error",
                "No se pudo eliminar el producto (puede tener ventas o compras asociadas).",
                parent=self,
            )

    def calcular_total(self, event=None):
        try:
            venta = float(self.txt_venta.get())
            stock = int(self.txt_stock.get())
            total = round(venta * stock, 2)

            self.txt_total.config(state="normal")
            self.txt_total.delete(0, END)
            self.txt_total.insert(0, f"${total:.2f}")
            self.txt_total.config(state="readonly")
        except Exception:
            pass

    def limpiar(self):
        self.ID = self.db.getMaxID() + 1
        self.txt_id.config(state="normal")
        self.txt_id.delete(0, END)
        self.txt_id.insert(0, self.ID)
        self.txt_id.config(state="disabled")
        self.txt_nombre.delete(0, END)
        self.txt_compra.delete(0, END)
        self.txt_venta.delete(0, END)
        self.txt_stock.delete(0, END)
        self.txt_buscar.delete(0, END)

        self.cmb_tipo.set("")
        self.cmb_proveedor.set("")

        self.txt_total.config(state="normal")
        self.txt_total.delete(0, END)
        self.txt_total.config(state="readonly")

        self.agregar_button.config(state="normal")
        self.editar_button.config(state="disabled")
        self.eliminar_button.config(state="disabled")

        self.Check_receta.deselect()
        self.receta.set(0)
