import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, END
from pathlib import Path
from .dbFacturas import dbFacturas
from ... import estilo


class FacturasView(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Historial y Visor de Facturas - Farmacia CUCEI")
        estilo.centrar_ventana(self, 880, 600)
        self.configure(bg=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        self.db = dbFacturas()
        self.carpeta_facturas = Path(__file__).resolve().parents[3] / "Facturas"

        estilo.crear_encabezado(
            self,
            "HISTORIAL DE FACTURAS Y COMPROBANTES",
            "Esc para salir | Clic en una factura para ver sus productos",
        )

        # -------- BARRA SUPERIOR --------
        top_bar = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=14, pady=10)
        top_bar.pack(fill=tk.X, padx=18, pady=(12, 8))

        tk.Label(top_bar, text="Filtrar por Tipo:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.cmb_tipo = ttk.Combobox(top_bar, values=["Todas", "Venta", "Compra"], state="readonly", width=18)
        self.cmb_tipo.set("Todas")
        self.cmb_tipo.pack(side=tk.LEFT, padx=(0, 12))
        self.cmb_tipo.bind("<<ComboboxSelected>>", lambda e: self.cargar_facturas())

        ttk.Button(top_bar, text="Actualizar Lista", style="BotonesEstilo.TButton", command=self.cargar_facturas).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(top_bar, text="Abrir Carpeta de PDFs", style="BotonesAceptar.TButton", command=self.abrir_carpeta_pdfs).pack(side=tk.RIGHT)

        # -------- TABLA DE FACTURAS REGISTRADAS --------
        tk.Label(
            self,
            text="1. Facturas Emitidas en la Sucursal Activa:",
            bg=estilo.backgroundColor,
            fg=estilo.headerColor,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill=tk.X, padx=18, pady=(2, 4))

        frame_facturas = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_facturas.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 8))

        scroll_f = ttk.Scrollbar(frame_facturas, orient=tk.VERTICAL)
        cols_f = ("ID", "Tipo", "Folio_Ref", "Fecha", "Sucursal")
        self.tabla_facturas = ttk.Treeview(
            frame_facturas,
            columns=cols_f,
            show="headings",
            yscrollcommand=scroll_f.set,
            selectmode="browse",
        )
        scroll_f.config(command=self.tabla_facturas.yview)
        scroll_f.pack(side=tk.RIGHT, fill=tk.Y)

        encabezados_f = {
            "ID": ("ID Factura", 95),
            "Tipo": ("Tipo", 105),
            "Folio_Ref": ("Folio Venta/Compra", 145),
            "Fecha": ("Fecha y Hora", 180),
            "Sucursal": ("Sucursal", 280),
        }
        for col, (txt, ancho) in encabezados_f.items():
            self.tabla_facturas.heading(col, text=txt)
            self.tabla_facturas.column(col, width=ancho, anchor=tk.CENTER if col != "Sucursal" else tk.W)

        self.tabla_facturas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tabla_facturas.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        # -------- TABLA DE DETALLE DE LA OPERACIÓN --------
        tk.Label(
            self,
            text="2. Desglose de Productos del Folio Seleccionado:",
            bg=estilo.backgroundColor,
            fg=estilo.headerColor,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill=tk.X, padx=18, pady=(2, 4))

        frame_detalle = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_detalle.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))

        scroll_d = ttk.Scrollbar(frame_detalle, orient=tk.VERTICAL)
        cols_d = ("Producto", "Tercero", "Cantidad", "Subtotal")
        self.tabla_detalle = ttk.Treeview(
            frame_detalle,
            columns=cols_d,
            show="headings",
            yscrollcommand=scroll_d.set,
            selectmode="browse",
        )
        scroll_d.config(command=self.tabla_detalle.yview)
        scroll_d.pack(side=tk.RIGHT, fill=tk.Y)

        encabezados_d = {
            "Producto": ("Producto", 290),
            "Tercero": ("Cliente / Proveedor", 250),
            "Cantidad": ("Cantidad", 110),
            "Subtotal": ("Monto ($)", 150),
        }
        for col, (txt, ancho) in encabezados_d.items():
            self.tabla_detalle.heading(col, text=txt)
            self.tabla_detalle.column(col, width=ancho, anchor=tk.CENTER if col in ("Cantidad", "Subtotal") else tk.W)

        self.tabla_detalle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.cargar_facturas()

    def cargar_facturas(self):
        for row in self.tabla_facturas.get_children():
            self.tabla_facturas.delete(row)
        for row in self.tabla_detalle.get_children():
            self.tabla_detalle.delete(row)

        datos = self.db.obtener_facturas(self.cmb_tipo.get())
        for f in datos:
            self.tabla_facturas.insert(
                "",
                END,
                values=(
                    f["id"],
                    f["tipo"],
                    f["id_referencia"],
                    str(f["fecha"]),
                    f.get("sucursal") or "",
                ),
            )

    def mostrar_detalle(self, event=None):
        sel = self.tabla_facturas.selection()
        if not sel:
            return
        valores = self.tabla_facturas.item(sel[0], "values")
        tipo = valores[1]
        id_ref = valores[2]

        for row in self.tabla_detalle.get_children():
            self.tabla_detalle.delete(row)

        detalles = self.db.obtener_detalle_referencia(tipo, id_ref)
        for d in detalles:
            self.tabla_detalle.insert(
                "",
                END,
                values=(
                    d.get("producto") or "N/A",
                    d.get("tercero") or "N/A",
                    d.get("cantidad") or 0,
                    f"${float(d.get('subtotal') or 0):.2f}",
                ),
            )

    def abrir_carpeta_pdfs(self):
        os.makedirs(self.carpeta_facturas, exist_ok=True)
        ruta_str = str(self.carpeta_facturas)
        try:
            if hasattr(os, "startfile"):
                os.startfile(ruta_str)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", ruta_str])
            else:
                subprocess.Popen(["xdg-open", ruta_str])
        except Exception as e:
            messagebox.showinfo(
                "Ruta de Facturas",
                f"Las facturas PDF se encuentran en:\n{ruta_str}\n({e})",
                parent=self,
            )
