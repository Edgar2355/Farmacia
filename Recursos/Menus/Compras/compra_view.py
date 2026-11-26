import tkinter as tk
from tkinter import ttk, messagebox, END
from .dbCompra import dbCompra
from ... import estilo
from ...Servicios.validaciones import validar_entero_positivo


class CompraView(tk.Toplevel):

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Compras a Proveedor - Farmacia CUCEI")
        estilo.centrar_ventana(self, 780, 620)
        self.configure(bg=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        self.db = dbCompra()
        self.ID = self.db.obtener_maxID() + 1

        estilo.crear_encabezado(
            self,
            f"ÓRDENES DE COMPRA A PROVEEDOR (Folio #{self.ID})",
            "Esc para salir | Enter en Cantidad para añadir",
        )

        # -------- PANEL SUPERIOR DE FORMULARIO --------
        card_top = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_top.pack(fill=tk.X, padx=18, pady=(12, 8))

        tk.Label(card_top, text="Producto *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        self.combo_producto = ttk.Combobox(card_top, state="readonly", width=34)
        self.combo_producto.grid(row=0, column=1, sticky="w", padx=(8, 16), pady=6)

        tk.Label(card_top, text="Folio Orden:", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="e", pady=6)
        self.entry_id = ttk.Entry(card_top, width=14)
        self.entry_id.insert(0, self.ID)
        self.entry_id.config(state="disabled")
        self.entry_id.grid(row=0, column=3, sticky="w", padx=(6, 0), pady=6)

        tk.Label(card_top, text="Proveedor:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        self.entry_proveedor = ttk.Entry(card_top, state="disabled", width=36)
        self.entry_proveedor.grid(row=1, column=1, sticky="w", padx=(8, 16), pady=6)

        tk.Label(card_top, text="Costo Unitario:", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).grid(row=1, column=2, sticky="e", pady=6)
        self.lbl_precio = tk.Label(card_top, text="$0.00", bg="#f1f5f9", fg=estilo.textColor, font=("Segoe UI", 10, "bold"), width=12, pady=3)
        self.lbl_precio.grid(row=1, column=3, sticky="w", padx=(6, 0), pady=6)

        tk.Label(card_top, text="Cantidad a pedir *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.txt_cantidad = ttk.Entry(card_top, width=18)
        self.txt_cantidad.grid(row=2, column=1, sticky="w", padx=(8, 16), pady=6)
        self.txt_cantidad.bind("<Return>", lambda e: self.añadir())

        bar_btns = tk.Frame(card_top, bg=estilo.surfaceColor)
        bar_btns.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 2))

        ttk.Button(bar_btns, text="Añadir a la Orden (Enter)", style="BotonesAceptar.TButton", command=self.añadir).pack(side=tk.LEFT, padx=(0, 8))
        self.btt_eliminar = ttk.Button(
            bar_btns,
            text="Quitar Seleccionado (Supr)",
            style="BotonesRechazar.TButton",
            state="disabled",
            command=self.eliminar,
        )
        self.btt_eliminar.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(bar_btns, text="Vaciar Orden", style="BotonesEstilo.TButton", command=self.limpiar).pack(side=tk.LEFT)

        # -------- TABLA DE ORDEN DE COMPRA --------
        frame_tree = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=18, pady=6)

        scroll_y = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL)
        self.compras_tree = ttk.Treeview(
            frame_tree,
            columns=("Producto", "Proveedor", "Cantidad", "Precio_compra"),
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="browse",
        )
        scroll_y.config(command=self.compras_tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.compras_tree.column("Producto", width=250, stretch=True)
        self.compras_tree.heading("Producto", text="Producto")

        self.compras_tree.column("Proveedor", width=230, stretch=True)
        self.compras_tree.heading("Proveedor", text="Proveedor")

        self.compras_tree.column("Cantidad", width=110, anchor=tk.CENTER)
        self.compras_tree.heading("Cantidad", text="Cantidad")

        self.compras_tree.column("Precio_compra", width=130, anchor=tk.CENTER)
        self.compras_tree.heading("Precio_compra", text="Subtotal ($)")

        self.compras_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.compras_tree.bind("<Delete>", lambda e: self.eliminar())

        # -------- PANEL INFERIOR DE TOTAL Y REGISTRO --------
        card_bottom = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_bottom.pack(fill=tk.X, padx=18, pady=(6, 14))

        self.str_total = tk.StringVar(value="TOTAL ORDEN DE COMPRA: $0.00")
        self.txt_total = tk.Label(
            card_bottom,
            textvariable=self.str_total,
            bg=estilo.surfaceColor,
            fg=estilo.headerColor,
            font=("Segoe UI", 15, "bold"),
        )
        self.txt_total.pack(side=tk.LEFT)

        ttk.Button(
            card_bottom,
            text="Confirmar y Enviar Pedido",
            style="BotonesAceptar.TButton",
            command=self.registrar_compra,
        ).pack(side=tk.RIGHT, ipadx=12, ipady=4)

        self.cargar_productos()
        self.cargar_proveedores()

        self.combo_producto.bind("<<ComboboxSelected>>", self.mostrar_producto)
        self.compras_tree.bind("<<TreeviewSelect>>", self.desbloquearEliminar)

    def añadir(self):
        if any(c.get().strip() == "" for c in [self.combo_producto, self.entry_proveedor, self.txt_cantidad]):
            messagebox.showerror(title="Campos faltantes", message="Seleccione un producto e ingrese la cantidad.", parent=self)
            return

        ok_cant, msg_cant, cantidad_nueva = validar_entero_positivo(self.txt_cantidad.get(), "Cantidad")
        if not ok_cant:
            messagebox.showwarning("Validación", msg_cant, parent=self)
            return

        producto_info = self.obtener_producto(self.combo_producto.get())
        if not producto_info:
            messagebox.showerror("Error", "No se encontró información del producto seleccionado", parent=self)
            return

        precio_unit = float(producto_info["precio_compra"])

        encontrado = False
        for item in self.compras_tree.get_children():
            prod = self.compras_tree.item(item, "values")
            if prod[0] == self.combo_producto.get():
                encontrado = True
                cant_acumulada = int(prod[2]) + cantidad_nueva
                subtotal_nuevo = round(precio_unit * cant_acumulada, 2)
                self.compras_tree.item(
                    item,
                    values=(prod[0], prod[1], str(cant_acumulada), f"{subtotal_nuevo:.2f}"),
                )
                break

        if not encontrado:
            subtotal = round(cantidad_nueva * precio_unit, 2)
            self.compras_tree.insert(
                "",
                END,
                values=(
                    self.combo_producto.get(),
                    self.entry_proveedor.get(),
                    str(cantidad_nueva),
                    f"{subtotal:.2f}",
                ),
            )

        self.txt_cantidad.delete(0, END)
        self.actualizarTotal()

    def eliminar(self):
        seleccion = self.compras_tree.selection()
        if not seleccion:
            return
        nombre = str(self.compras_tree.item(seleccion[0], "values")[0])
        confirmacion = messagebox.askyesno(
            title="Confirmación",
            message=f"¿Está seguro que desea quitar '{nombre}' de la orden?",
            parent=self,
        )
        if confirmacion:
            self.compras_tree.delete(seleccion[0])
            self.actualizarTotal()
            self.btt_eliminar.config(state="disabled")

    def mostrar_producto(self, event=None):
        producto = self.obtener_producto(self.combo_producto.get())
        if producto:
            self.entry_proveedor.config(state="normal")
            self.entry_proveedor.delete(0, END)
            nombre_prov = self.obtener_nombre_proveedor(producto["id_proveedor"]) or "Sin proveedor"
            self.entry_proveedor.insert(0, str(nombre_prov))
            self.entry_proveedor.config(state="disabled")
            self.lbl_precio.config(text=f"${float(producto['precio_compra']):.2f}")
            self.txt_cantidad.focus_set()

    def actualizarTotal(self):
        costo_total = 0.0
        for item in self.compras_tree.get_children():
            producto = self.compras_tree.item(item, "values")
            costo_total += float(producto[3])
        self.str_total.set(f"TOTAL ORDEN DE COMPRA: ${costo_total:.2f}")

    def desbloquearEliminar(self, event=None):
        if self.compras_tree.selection():
            self.btt_eliminar.config(state="normal")
        else:
            self.btt_eliminar.config(state="disabled")

    def cargar_productos(self):
        self.lista_productos = self.db.obtener_productos()
        self.combo_producto["values"] = [p["nombre"] for p in self.lista_productos]

    def obtener_producto(self, nombre):
        for p in self.lista_productos:
            if p["nombre"] == nombre:
                return p
        return None

    def cargar_proveedores(self):
        self.lista_proveedores = self.db.obtener_proveedores()

    def obtener_id_producto(self, nombre):
        for p in self.lista_productos:
            if p["nombre"] == nombre:
                return p["id"]
        return None

    def obtener_nombre_proveedor(self, id_prov):
        for p in self.lista_proveedores:
            if p["id"] == id_prov:
                return p["nombre"]
        return None

    def obtener_id_proveedor(self, nombre):
        for p in self.lista_proveedores:
            if p["nombre"] == nombre:
                return p["id"]
        return None

    def registrar_compra(self):
        if not self.compras_tree.get_children():
            messagebox.showwarning("Orden vacía", "Añada al menos un producto antes de registrar la compra.", parent=self)
            return

        carrito = []
        productos_separados = {}
        mapa_correos_prov = {p["nombre"]: p.get("correo") for p in (self.lista_proveedores or [])}

        for item in self.compras_tree.get_children():
            producto = self.compras_tree.item(item, "values")
            id_prod = self.obtener_id_producto(producto[0])
            id_prov = self.obtener_id_proveedor(producto[1])
            datos = [id_prod, id_prov, int(producto[2]), float(producto[3])]
            carrito.append(datos)

            correo = mapa_correos_prov.get(producto[1])
            if correo:
                producto_para_separar = {
                    "nombre": producto[0],
                    "cantidad": producto[2],
                    "precio": producto[3],
                }
                productos_separados.setdefault(correo, []).append(producto_para_separar)

        ok, mensaje = self.db.registrar_multiple(self.ID, carrito, productos_separados)

        if ok:
            messagebox.showinfo(
                title="Compra Registrada",
                message=mensaje + "\n\nSe ha enviado la orden por correo al proveedor en segundo plano.",
                parent=self,
            )
            self.limpiar()
            self.cargar_productos()
        else:
            messagebox.showerror(title="Error", message=mensaje, parent=self)

    def limpiar(self):
        self.entry_id.config(state="normal")
        self.entry_id.delete(0, END)

        self.ID = self.db.obtener_maxID() + 1
        self.entry_id.insert(0, self.ID)
        self.entry_id.config(state="disabled")

        self.combo_producto.set("")
        self.entry_proveedor.config(state="normal")
        self.entry_proveedor.delete(0, END)
        self.entry_proveedor.config(state="disabled")
        self.txt_cantidad.delete(0, END)
        self.lbl_precio.config(text="$0.00")

        for item in self.compras_tree.get_children():
            self.compras_tree.delete(item)

        self.actualizarTotal()
