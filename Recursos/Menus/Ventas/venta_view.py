import tkinter as tk
from tkinter import ttk, messagebox, END
import threading
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from .dbVenta import dbVenta
from ... import estilo
from ...Servicios.validaciones import validar_entero_positivo, calcular_descuento_y_puntos

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "Gemini_api.env"))
load_dotenv()
Gemini_api = os.getenv("gemini_api") or os.getenv("GEMINI_API_KEY")


class VentaView(tk.Toplevel):

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Punto de Venta (POS) - Farmacia CUCEI")
        estilo.centrar_ventana(self, 780, 650)
        self.configure(bg=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        self.db = dbVenta()
        self.ID = self.db.obtener_maxID() + 1
        self.puntos_cliente_actual = 0

        estilo.crear_encabezado(
            self,
            f"PUNTO DE VENTA (Ticket #{self.ID})",
            "Esc para salir | Enter en Cantidad para añadir al carrito",
        )

        # -------- PANEL SUPERIOR DE SELECCIÓN --------
        card_top = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_top.pack(fill=tk.X, padx=18, pady=(12, 8))

        # Fila 1: Cliente y Puntos
        tk.Label(card_top, text="Cliente *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        self.combo_cliente = ttk.Combobox(card_top, state="readonly", width=34)
        self.combo_cliente.grid(row=0, column=1, sticky="w", padx=(8, 16), pady=6)

        self.lbl_puntos_cliente = tk.Label(
            card_top,
            text="Puntos acumulados: 0",
            bg="#dbeafe",
            fg="#1e3a8a",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
        )
        self.lbl_puntos_cliente.grid(row=0, column=2, columnspan=2, sticky="w", pady=6)

        # Fila 2: Producto y Stock
        tk.Label(card_top, text="Producto *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        self.combo_producto = ttk.Combobox(card_top, state="readonly", width=34)
        self.combo_producto.grid(row=1, column=1, sticky="w", padx=(8, 16), pady=6)

        tk.Label(card_top, text="Stock Disponible:", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).grid(row=1, column=2, sticky="e", pady=6)
        self.ent_stock = ttk.Entry(card_top, state="disabled", width=12)
        self.ent_stock.grid(row=1, column=3, sticky="w", padx=(6, 0), pady=6)

        # Fila 3: Cantidad, Precio Unitario y Botón IA
        tk.Label(card_top, text="Cantidad *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.txt_cantidad = ttk.Entry(card_top, width=18)
        self.txt_cantidad.grid(row=2, column=1, sticky="w", padx=(8, 16), pady=6)
        self.txt_cantidad.bind("<Return>", lambda e: self.añadir())

        tk.Label(card_top, text="Precio Unitario:", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).grid(row=2, column=2, sticky="e", pady=6)
        self.lbl_precio = tk.Label(card_top, text="$0.00", bg="#f1f5f9", fg=estilo.textColor, font=("Segoe UI", 10, "bold"), width=12, pady=3)
        self.lbl_precio.grid(row=2, column=3, sticky="w", padx=(6, 0), pady=6)

        # Fila 4: Botones de acción sobre el carrito
        bar_btns = tk.Frame(card_top, bg=estilo.surfaceColor)
        bar_btns.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 2))

        ttk.Button(bar_btns, text="Añadir al Carrito (Enter)", style="BotonesAceptar.TButton", command=self.añadir).pack(side=tk.LEFT, padx=(0, 8))
        self.btt_eliminar = ttk.Button(
            bar_btns,
            text="Quitar Seleccionado (Supr)",
            style="BotonesRechazar.TButton",
            state="disabled",
            command=self.eliminar,
        )
        self.btt_eliminar.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(bar_btns, text="Vaciar Carrito", style="BotonesEstilo.TButton", command=self.limpiar_carrito).pack(side=tk.LEFT)

        ttk.Button(bar_btns, text="Asistente Farmacéutico IA", style="BotonesEstilo.TButton", command=self.chat_ia).pack(side=tk.RIGHT)

        # -------- TABLA CARRITO DE VENTAS --------
        frame_tree = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=18, pady=6)

        scroll_y = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL)
        self.ventas_tree = ttk.Treeview(
            frame_tree,
            columns=("Producto", "Cantidad", "Precio_Unit", "Precio"),
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="browse",
        )
        scroll_y.config(command=self.ventas_tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.ventas_tree.column("Producto", width=330, stretch=True, anchor=tk.W)
        self.ventas_tree.heading("Producto", text="Producto")

        self.ventas_tree.column("Cantidad", width=110, anchor=tk.CENTER)
        self.ventas_tree.heading("Cantidad", text="Cantidad")

        self.ventas_tree.column("Precio_Unit", width=130, anchor=tk.CENTER)
        self.ventas_tree.heading("Precio_Unit", text="Precio Unit.")

        self.ventas_tree.column("Precio", width=140, anchor=tk.CENTER)
        self.ventas_tree.heading("Precio", text="Subtotal")

        self.ventas_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.ventas_tree.bind("<Delete>", lambda e: self.eliminar())

        # -------- PANEL INFERIOR DE RESUMEN Y COBRO --------
        card_bottom = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_bottom.pack(fill=tk.X, padx=18, pady=(6, 14))

        resumen_frame = tk.Frame(card_bottom, bg=estilo.surfaceColor)
        resumen_frame.pack(side=tk.LEFT)

        self.lbl_resumen_desglose = tk.Label(
            resumen_frame,
            text="Subtotal: $0.00   |   Descuento (0%): -$0.00",
            bg=estilo.surfaceColor,
            fg=estilo.mutedTextColor,
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_resumen_desglose.pack(anchor="w")

        self.str_total = tk.StringVar(value="TOTAL A PAGAR: $0.00")
        self.txt_total = tk.Label(
            resumen_frame,
            textvariable=self.str_total,
            bg=estilo.surfaceColor,
            fg=estilo.headerColor,
            font=("Segoe UI", 16, "bold"),
        )
        self.txt_total.pack(anchor="w", pady=(2, 0))

        ttk.Button(
            card_bottom,
            text="Confirmar y Realizar Venta",
            style="BotonesAceptar.TButton",
            command=self.realizar_venta,
        ).pack(side=tk.RIGHT, ipadx=12, ipady=4)

        self.cargar_clientes()
        self.cargar_productos()

        self.combo_cliente.bind("<<ComboboxSelected>>", self.mostrar_puntos_cliente)
        self.combo_producto.bind("<<ComboboxSelected>>", self.mostrar_stock)
        self.ventas_tree.bind("<<TreeviewSelect>>", self.desbloquearEliminar)

    def mostrar_puntos_cliente(self, event=None):
        nombre = self.combo_cliente.get()
        self.puntos_cliente_actual = 0
        for c in self.lista_clientes:
            if c["nombre"] == nombre:
                self.puntos_cliente_actual = int(c.get("puntos") or 0)
                if self.puntos_cliente_actual >= 50:
                    self.lbl_puntos_cliente.config(
                        text=f"Puntos: {self.puntos_cliente_actual} (¡Aplica 10% de Descuento!)",
                        bg="#dcfce7",
                        fg="#166534",
                    )
                else:
                    self.lbl_puntos_cliente.config(
                        text=f"Puntos acumulados: {self.puntos_cliente_actual} (50 pts para 10% desc.)",
                        bg="#dbeafe",
                        fg="#1e3a8a",
                    )
                break
        self.actualizarTotal()

    def chat_ia(self):
        ventana = tk.Toplevel(self)
        ventana.title("Asistente Farmacéutico IA - Farmacia CUCEI")
        estilo.centrar_ventana(ventana, 900, 650, maximizar=True)
        ventana.configure(bg=estilo.backgroundColor)

        api_key = os.getenv("gemini_api") or os.getenv("GEMINI_API_KEY") or Gemini_api
        if not api_key:
            messagebox.showinfo(
                parent=ventana,
                title="API Key no detectada",
                message=(
                    "No se ha detectado ninguna API Key válida para Gemini.\n"
                    "Configúrela en Recursos/Menus/Ventas/Gemini_api.env como:\n"
                    "gemini_api=TU_CLAVE"
                ),
            )
            ventana.destroy()
            return

        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            messagebox.showerror(parent=ventana, title="Error IA", message=f"No se pudo inicializar Gemini: {e}")
            ventana.destroy()
            return

        estilo.crear_encabezado(ventana, "Asistente Farmacéutico IA", "Conectado al Inventario")

        frame_chat = ttk.Frame(ventana)
        frame_chat.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(frame_chat)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.chat_display = tk.Text(
            frame_chat,
            wrap=tk.WORD,
            yscrollcommand=self.scrollbar.set,
            bg="#ffffff",
            state="disabled",
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
        )

        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.chat_display.yview)

        self.chat_display.tag_config("usuario", justify="right", foreground="#1d4ed8", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("bot", justify="left", foreground="#15803d")
        self.chat_display.tag_config("sistema", justify="center", foreground="#64748b", font=("Segoe UI", 9, "italic"))

        frame_input = tk.Frame(ventana, bg=estilo.backgroundColor)
        frame_input.pack(padx=12, pady=(0, 12), fill=tk.X)

        self.entry_mensaje = ttk.Entry(frame_input, font=("Segoe UI", 10))
        self.entry_mensaje.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry_mensaje.bind("<Return>", lambda e: self.enviar_mensaje())

        btn_enviar = ttk.Button(frame_input, text="Enviar", style="BotonesEstilo.TButton", command=self.enviar_mensaje)
        btn_enviar.pack(side=tk.RIGHT)

        self.agregar_mensaje(
            "Sistema",
            "Pregunta por síntomas, dosis o disponibilidad en el inventario de esta sucursal.",
            "sistema",
        )
        self.entry_mensaje.focus_set()

    def agregar_mensaje(self, emisor, texto, tag):
        if not hasattr(self, "chat_display") or not self.chat_display.winfo_exists():
            return
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"{emisor}: {texto}\n\n", tag)
        self.chat_display.config(state="disabled")
        self.chat_display.see(tk.END)

    def enviar_mensaje(self):
        mensaje = self.entry_mensaje.get().strip()
        if not mensaje:
            return

        self.agregar_mensaje("Tú", mensaje, "usuario")
        self.entry_mensaje.delete(0, tk.END)
        self.agregar_mensaje("Sistema", "Consultando al asistente...", "sistema")

        threading.Thread(
            target=self._consultar_gemini_background,
            args=(mensaje,),
            daemon=True,
        ).start()

    def _consultar_gemini_background(self, mensaje_usuario):
        catalogo_txt = "\n".join(
            [
                f"- {p['nombre']} (${p['precio_venta']}, Stock: {p['stock']}, "
                f"Receta: {'Sí' if p.get('receta') else 'No'})"
                for p in (self.lista_productos or [])
            ]
        )
        cliente_actual = self.combo_cliente.get() or "Cliente general"

        instruccion = (
            "Eres un farmacéutico experto de Farmacia CUCEI. "
            "Un vendedor o cliente te consulta sobre síntomas o medicamentos. "
            f"Cliente actual: {cliente_actual}.\n"
            f"Catálogo disponible en esta sucursal:\n{catalogo_txt}\n"
            "Recomienda opciones del catálogo si aplican, indica si requieren receta y sé breve y claro."
        )

        contexto = types.GenerateContentConfig(system_instruction=instruccion)
        modelos_candidatos = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        ultimo_error = None

        for modelo in modelos_candidatos:
            try:
                respuesta = self.client.models.generate_content(
                    model=modelo,
                    contents=mensaje_usuario,
                    config=contexto,
                )
                texto_resp = respuesta.text
                self.after(0, lambda t=texto_resp: self.agregar_mensaje("Farmacéutico IA", t, "bot"))
                return
            except Exception as e:
                ultimo_error = e

        self.after(
            0,
            lambda err=ultimo_error: self.agregar_mensaje("Sistema", f"No se pudo consultar Gemini: {err}", "sistema"),
        )

    # -------- FUNCIONES DE VENTA --------
    def añadir(self):
        if any(c.get().strip() == "" for c in [self.combo_producto, self.txt_cantidad, self.ent_stock]):
            messagebox.showerror(
                title="Datos incompletos",
                message="Seleccione un producto e ingrese la cantidad que desea agregar.",
                parent=self,
            )
            return

        ok_cant, msg_cant, cantidad_solicitada = validar_entero_positivo(self.txt_cantidad.get(), "Cantidad")
        if not ok_cant:
            messagebox.showwarning("Validación", msg_cant, parent=self)
            return

        stock_disponible = int(self.ent_stock.get())
        if cantidad_solicitada > stock_disponible:
            messagebox.showerror(
                title="Stock insuficiente",
                message=f"Está solicitando {cantidad_solicitada} unidades y solo hay {stock_disponible} en stock.",
                parent=self,
            )
            return

        producto_info = self.obtener_producto()
        if not producto_info:
            return

        if producto_info.get("receta") == 1:
            if not messagebox.askyesno(
                title="Receta médica obligatoria",
                message="El medicamento seleccionado requiere receta médica.\n¿El cliente presentó receta válida?",
                parent=self,
            ):
                return

        precio_unit = float(producto_info["precio_venta"])

        encontrado = False
        for item in self.ventas_tree.get_children():
            prod = self.ventas_tree.item(item, "values")
            if prod[0] == self.combo_producto.get():
                nueva_cant = int(prod[1]) + cantidad_solicitada
                if nueva_cant > stock_disponible:
                    messagebox.showerror(
                        title="Stock insuficiente",
                        message="La cantidad acumulada en el carrito supera el stock disponible.",
                        parent=self,
                    )
                    return
                encontrado = True
                nuevo_sub = round(precio_unit * nueva_cant, 2)
                self.ventas_tree.item(
                    item,
                    values=(prod[0], str(nueva_cant), f"${precio_unit:.2f}", f"{nuevo_sub:.2f}"),
                )
                break

        if not encontrado:
            subtotal = round(cantidad_solicitada * precio_unit, 2)
            self.ventas_tree.insert(
                "",
                END,
                values=(
                    self.combo_producto.get(),
                    str(cantidad_solicitada),
                    f"${precio_unit:.2f}",
                    f"{subtotal:.2f}",
                ),
            )

        self.txt_cantidad.delete(0, END)
        self.actualizarTotal()

    def eliminar(self):
        seleccion = self.ventas_tree.selection()
        if not seleccion:
            return
        nombre = str(self.ventas_tree.item(seleccion[0], "values")[0])
        if messagebox.askyesno(title="Confirmación", message=f"¿Desea quitar '{nombre}' del carrito?", parent=self):
            self.ventas_tree.delete(seleccion[0])
            self.actualizarTotal()
            self.btt_eliminar.config(state="disabled")

    def actualizarTotal(self):
        subtotal = 0.0
        for item in self.ventas_tree.get_children():
            producto = self.ventas_tree.item(item, "values")
            subtotal += float(producto[-1])

        descuento, _, total_final = calcular_descuento_y_puntos(self.puntos_cliente_actual, subtotal)
        porcentaje_txt = "10%" if descuento > 0 else "0%"
        self.lbl_resumen_desglose.config(
            text=f"Subtotal: ${subtotal:.2f}   |   Descuento por puntos ({porcentaje_txt}): -${descuento:.2f}"
        )
        self.str_total.set(f"TOTAL A PAGAR: ${total_final:.2f}")

    def desbloquearEliminar(self, event=None):
        if self.ventas_tree.selection():
            self.btt_eliminar.config(state="normal")
        else:
            self.btt_eliminar.config(state="disabled")

    def cargar_clientes(self):
        self.lista_clientes = self.db.obtener_clientes()
        self.combo_cliente["values"] = [c["nombre"] for c in self.lista_clientes]

    def cargar_productos(self):
        self.lista_productos = self.db.obtener_productos()
        self.combo_producto["values"] = [p["nombre"] for p in self.lista_productos]

    def obtener_id_cliente(self):
        nombre = self.combo_cliente.get()
        for c in self.lista_clientes:
            if c["nombre"] == nombre:
                return c["id"]
        return None

    def obtener_producto(self):
        nombre = self.combo_producto.get()
        for p in self.lista_productos:
            if p["nombre"] == nombre:
                return p
        return None

    def mostrar_stock(self, event=None):
        producto = self.obtener_producto()
        if producto:
            self.ent_stock.config(state="normal")
            self.ent_stock.delete(0, END)
            self.ent_stock.insert(0, str(producto["stock"]))
            self.ent_stock.config(state="disabled")
            self.lbl_precio.config(text=f"${float(producto['precio_venta']):.2f}")
            self.txt_cantidad.focus_set()

    def realizar_venta(self):
        if self.combo_cliente.get() == "":
            messagebox.showerror(
                title="Cliente no seleccionado",
                message="Seleccione un cliente antes de realizar la venta.",
                parent=self,
            )
            return

        id_cliente = self.obtener_id_cliente()
        productos = []
        costo_total = 0.0

        for item in self.ventas_tree.get_children():
            datos = self.ventas_tree.item(item, "values")
            # datos: (Producto, Cantidad, Precio_Unit, Subtotal)
            subtotal_val = float(datos[-1])
            productos.append((datos[0], datos[1], subtotal_val))
            costo_total += subtotal_val

        if not productos:
            messagebox.showerror(
                title="Carrito vacío",
                message="Agregue al menos un producto al carrito para completar la venta.",
                parent=self,
            )
            return

        ok, mensaje = self.db.registrar(self.ID, id_cliente, productos, costo_total)

        if ok:
            messagebox.showinfo("Venta Exitosa", mensaje, parent=self)
            self.limpiar_carrito()
            self.cargar_productos()
            self.cargar_clientes()
        else:
            messagebox.showerror("Error", mensaje, parent=self)

    def limpiar_carrito(self):
        self.ID = self.db.obtener_maxID() + 1
        self.combo_cliente.set("")
        self.combo_producto.set("")
        self.puntos_cliente_actual = 0
        self.lbl_puntos_cliente.config(text="Puntos acumulados: 0", bg="#dbeafe", fg="#1e3a8a")
        self.txt_cantidad.delete(0, END)
        self.ent_stock.config(state="normal")
        self.ent_stock.delete(0, END)
        self.ent_stock.config(state="disabled")
        self.lbl_precio.config(text="$0.00")
        self.ventas_tree.delete(*self.ventas_tree.get_children())
        self.actualizarTotal()
