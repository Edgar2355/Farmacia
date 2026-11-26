import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .dbReportes import dbReportes
from ... import estilo


class ReportesView(tk.Toplevel):

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Centro de Reportes y Estadísticas - Farmacia CUCEI")
        estilo.centrar_ventana(self, 960, 600)
        self.configure(bg=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        self.db = dbReportes()
        self.reporte_actual = "Sin seleccionar"
        self.encabezados_actuales = []

        estilo.crear_encabezado(
            self,
            "CENTRO DE REPORTES Y ESTADÍSTICAS",
            "Esc para salir | Exportación directa a CSV compatible con Excel",
        )

        # =========================
        # BARRA DE SELECTORES DE REPORTE
        # =========================
        bar_btns = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=12, pady=10)
        bar_btns.pack(fill=tk.X, padx=18, pady=(12, 8))

        for col_idx in range(4):
            bar_btns.columnconfigure(col_idx, weight=1)

        ttk.Button(
            bar_btns,
            text="Clientes por Ciudad",
            style="BotonesEstilo.TButton",
            command=self.reporte_clientes,
        ).grid(row=0, column=0, padx=5, pady=4, sticky="ew")

        ttk.Button(
            bar_btns,
            text="Ventas por Fecha",
            style="BotonesEstilo.TButton",
            command=self.reporte_ventas,
        ).grid(row=0, column=1, padx=5, pady=4, sticky="ew")

        ttk.Button(
            bar_btns,
            text="Compras por Fecha",
            style="BotonesEstilo.TButton",
            command=self.reporte_compras,
        ).grid(row=0, column=2, padx=5, pady=4, sticky="ew")

        ttk.Button(
            bar_btns,
            text="Mayores Ventas (Folios)",
            style="BotonesEstilo.TButton",
            command=self.reporte_facturas,
        ).grid(row=0, column=3, padx=5, pady=4, sticky="ew")

        ttk.Button(
            bar_btns,
            text="Productos Más Vendidos",
            style="BotonesEstilo.TButton",
            command=self.reporte_mas_vendidos,
        ).grid(row=1, column=0, padx=5, pady=4, sticky="ew")

        ttk.Button(
            bar_btns,
            text="Alerta Stock Crítico",
            style="BotonesEstilo.TButton",
            command=self.reporte_stock_critico,
        ).grid(row=1, column=1, padx=5, pady=4, sticky="ew")

        ttk.Button(
            bar_btns,
            text="Exportar Reporte Actual a CSV",
            style="BotonesAceptar.TButton",
            command=self.exportar_csv,
        ).grid(row=1, column=2, columnspan=2, padx=5, pady=4, sticky="ew")

        # =========================
        # TITULO DEL REPORTE ACTIVO
        # =========================
        self.lbl_titulo = tk.Label(
            self,
            text="Mostrando: Ventas por Fecha",
            bg=estilo.backgroundColor,
            fg=estilo.headerColor,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        self.lbl_titulo.pack(fill=tk.X, padx=18, pady=(2, 4))

        # =========================
        # TABLA CON SCROLLBAR
        # =========================
        frame_tabla = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_tabla.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        self.tabla = ttk.Treeview(frame_tabla, show="headings", yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tabla.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla.pack(side=tk.LEFT, fill="both", expand=True)
        self.tabla.tag_configure("critico", background=estilo.DangerRowBg, foreground=estilo.DangerRowFg)

        # Cargar reporte inicial automáticamente para no mostrar una tabla vacía al abrir
        self.reporte_ventas()

    def _configurar_columnas(self, titulo, definicion_columnas):
        self.reporte_actual = titulo
        self.lbl_titulo.config(text=f"Reporte Activo: {titulo}")
        self.tabla.delete(*self.tabla.get_children())

        ids_cols = [c[0] for c in definicion_columnas]
        self.encabezados_actuales = [c[1] for c in definicion_columnas]
        self.tabla["columns"] = ids_cols

        for col_id, texto, ancho, alineacion in definicion_columnas:
            self.tabla.heading(col_id, text=texto)
            self.tabla.column(col_id, width=ancho, anchor=alineacion)

    def reporte_clientes(self):
        self._configurar_columnas(
            "Clientes por Ciudad",
            [
                ("ciudad", "Ciudad", 350, tk.W),
                ("total", "Total de Clientes", 180, tk.CENTER),
            ],
        )
        for d in self.db.clientes_por_ciudad():
            self.tabla.insert("", "end", values=(d["ciudad"], d["total"]))

    def reporte_ventas(self):
        self._configurar_columnas(
            "Ventas por Fecha (Sucursal Actual)",
            [
                ("fecha", "Fecha", 240, tk.CENTER),
                ("num_ventas", "N° de Tickets", 160, tk.CENTER),
                ("total", "Total Ingresos", 220, tk.CENTER),
            ],
        )
        for d in self.db.ventas_por_fecha():
            self.tabla.insert(
                "",
                "end",
                values=(str(d["fecha"]), d.get("num_ventas", 0), f"${float(d['total'] or 0):.2f}"),
            )

    def reporte_compras(self):
        self._configurar_columnas(
            "Compras por Fecha (Sucursal Actual)",
            [
                ("fecha", "Fecha", 240, tk.CENTER),
                ("num_compras", "N° de Órdenes", 160, tk.CENTER),
                ("total", "Total Compras", 220, tk.CENTER),
            ],
        )
        for d in self.db.compras_por_fecha():
            self.tabla.insert(
                "",
                "end",
                values=(str(d["fecha"]), d.get("num_compras", 0), f"${float(d['total'] or 0):.2f}"),
            )

    def reporte_facturas(self):
        self._configurar_columnas(
            "Facturas con Mayores Ventas",
            [
                ("id", "Folio Venta", 100, tk.CENTER),
                ("cliente", "Cliente", 280, tk.W),
                ("articulos", "Unidades", 120, tk.CENTER),
                ("total", "Total Venta", 160, tk.CENTER),
                ("fecha", "Fecha", 200, tk.CENTER),
            ],
        )
        for d in self.db.facturas_mayores_ventas():
            self.tabla.insert(
                "",
                "end",
                values=(
                    d["id"],
                    d["cliente"],
                    d.get("articulos", 0),
                    f"${float(d['total'] or 0):.2f}",
                    str(d["fecha"]),
                ),
            )

    def reporte_mas_vendidos(self):
        self._configurar_columnas(
            "Productos Más Vendidos",
            [
                ("id", "ID Producto", 100, tk.CENTER),
                ("nombre", "Producto", 280, tk.W),
                ("tipo", "Categoría", 150, tk.CENTER),
                ("unidades", "Unidades Vendidas", 150, tk.CENTER),
                ("ingresos", "Ingresos Generados", 180, tk.CENTER),
            ],
        )
        for d in self.db.productos_mas_vendidos():
            self.tabla.insert(
                "",
                "end",
                values=(
                    d["id"],
                    d["nombre"],
                    d["tipo"],
                    d["unidades_vendidas"],
                    f"${float(d['ingresos'] or 0):.2f}",
                ),
            )

    def reporte_stock_critico(self):
        self._configurar_columnas(
            "Productos con Stock Crítico (<= 5 unidades)",
            [
                ("id", "ID", 80, tk.CENTER),
                ("nombre", "Producto", 260, tk.W),
                ("tipo", "Categoría", 150, tk.CENTER),
                ("stock", "Stock Actual", 130, tk.CENTER),
                ("proveedor", "Proveedor", 220, tk.W),
            ],
        )
        for d in self.db.stock_critico():
            self.tabla.insert(
                "",
                "end",
                values=(d["id"], d["nombre"], d["tipo"], d["stock"], d["proveedor"]),
                tags=("critico",),
            )

    def exportar_csv(self):
        filas = self.tabla.get_children()
        if not filas:
            messagebox.showwarning("Sin datos", "El reporte actual no contiene filas para exportar.", parent=self)
            return

        ruta_archivo = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Reporte como CSV",
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile=f"reporte_{self.reporte_actual.lower().replace(' ', '_')}.csv",
        )
        if not ruta_archivo:
            return

        try:
            with open(ruta_archivo, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(self.encabezados_actuales)
                for item in filas:
                    writer.writerow(self.tabla.item(item, "values"))
            messagebox.showinfo("Exportación exitosa", f"Reporte guardado en:\n{ruta_archivo}", parent=self)
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e), parent=self)
