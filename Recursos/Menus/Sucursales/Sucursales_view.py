import tkinter as tk
from tkinter import ttk, messagebox, END
from .dbSucursal import dbSucursal
from ... import estilo
from ...Servicios.contexto_sucursal import guardar_sucursal


class SucursalesView(tk.Toplevel):
    def __init__(self, sucursal, ruta=None, master=None):
        super().__init__(master)
        self.sucursal = sucursal if isinstance(sucursal, dict) else {"id": 0, "direccion": "No especificado"}
        self.ruta = ruta
        self.db = dbSucursal()

        self.title("Gestión de Sucursales - Farmacia CUCEI")
        estilo.centrar_ventana(self, 780, 480)
        self.configure(background=estilo.backgroundColor)
        estilo.aplicar_tema(self)

        estilo.crear_encabezado(
            self,
            "ADMINISTRACIÓN DE SUCURSALES",
            "Esc para salir | Clic en una fila para editar",
        )

        # -------- BARRA DE BÚSQUEDA --------
        search_bar = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=14, pady=8)
        search_bar.pack(fill=tk.X, padx=18, pady=(12, 8))

        tk.Label(search_bar, text="Buscar (ID o Dirección):", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.txt_buscar = ttk.Entry(search_bar, width=35)
        self.txt_buscar.pack(side=tk.LEFT, padx=(0, 8))
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.filtrar_tabla())

        ttk.Button(search_bar, text="Buscar ID", style="BotonesEstilo.TButton", command=self.buscar_sucursal).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(search_bar, text="Mostrar Todas", style="BotonesEstilo.TButton", command=self.cargar_tabla).pack(side=tk.LEFT)

        # -------- TARJETA FORMULARIO --------
        card_form = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid", padx=16, pady=12)
        card_form.pack(fill=tk.X, padx=18, pady=(0, 8))

        tk.Label(card_form, text="ID (Auto):", bg=estilo.surfaceColor, fg=estilo.mutedTextColor, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.txt_id = ttk.Entry(card_form, width=10)
        self.txt_id.grid(row=0, column=1, sticky="w", padx=(6, 16), pady=5)

        tk.Label(card_form, text="Dirección Completa *:", bg=estilo.surfaceColor, fg=estilo.textColor, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", pady=5)
        self.txt_direccion = ttk.Entry(card_form, width=54)
        self.txt_direccion.grid(row=0, column=3, sticky="ew", padx=(6, 0), pady=5)

        btn_row = tk.Frame(card_form, bg=estilo.surfaceColor)
        btn_row.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 2))

        ttk.Button(btn_row, text="Guardar / Actualizar", style="BotonesAceptar.TButton", command=self.guardar_sucursal).pack(side=tk.LEFT, padx=(0, 8))
        self.EliminarBoton = ttk.Button(
            btn_row,
            text="Eliminar Seleccionada",
            style="BotonesRechazar.TButton",
            command=self.eliminar_sucursal,
            state="disabled",
        )
        self.EliminarBoton.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="Limpiar / Nueva", style="BotonesEstilo.TButton", command=self.limpiar_campos).pack(side=tk.LEFT)

        # -------- TABLA TREEVIEW --------
        frame_tabla = tk.Frame(self, bg=estilo.surfaceColor, bd=1, relief="solid")
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))

        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        self.tabla = ttk.Treeview(
            frame_tabla,
            columns=("ID", "Direccion"),
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="browse",
        )
        scroll_y.config(command=self.tabla.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tabla.heading("ID", text="ID")
        self.tabla.column("ID", width=80, anchor=tk.CENTER)
        self.tabla.heading("Direccion", text="Dirección de la Sucursal")
        self.tabla.column("Direccion", width=630, anchor=tk.W)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_fila)
        self.cargar_tabla()

    def cargar_tabla(self, datos=None):
        self.sucursales_cache = datos if datos is not None else self.db.obtenerSucursales()
        self._render_tabla(self.sucursales_cache)

    def _render_tabla(self, registros):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for s in registros:
            self.tabla.insert("", END, values=(s["id"], s["direccion"]))

    def filtrar_tabla(self):
        texto = self.txt_buscar.get().strip().lower()
        if not texto:
            self._render_tabla(getattr(self, "sucursales_cache", []))
            return
        filtrados = [
            s for s in getattr(self, "sucursales_cache", [])
            if texto in str(s.get("id", "")).lower() or texto in str(s.get("direccion", "")).lower()
        ]
        self._render_tabla(filtrados)

    def seleccionar_fila(self, event=None):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        valores = self.tabla.item(seleccion[0], "values")
        self.txt_id.delete(0, END)
        self.txt_id.insert(0, valores[0])
        self.txt_direccion.delete(0, END)
        self.txt_direccion.insert(0, valores[1])
        self.EliminarBoton.config(state="normal")

    def buscar_sucursal(self):
        id_busqueda = self.txt_id.get().strip() or self.txt_buscar.get().strip()
        if id_busqueda == "":
            messagebox.showwarning("Error", "Ingresa un ID a buscar", parent=self)
            return

        sucursal_db = self.db.buscar(id_busqueda)
        if sucursal_db:
            self.txt_id.delete(0, END)
            self.txt_id.insert(0, sucursal_db["id"])
            self.txt_direccion.delete(0, END)
            self.txt_direccion.insert(0, sucursal_db["direccion"])
            self.EliminarBoton.config(state="normal")
        else:
            messagebox.showerror(parent=self, title="Error", message="Sucursal no encontrada")

    def guardar_sucursal(self):
        id_sucursal = self.txt_id.get().strip()
        direccion = self.txt_direccion.get().strip()

        if direccion == "":
            messagebox.showwarning("Error", "La dirección de la sucursal es obligatoria", parent=self)
            return

        if id_sucursal != "":
            ok = self.db.actualizar(id_sucursal, direccion)
            if ok:
                messagebox.showinfo("OK", "Sucursal actualizada correctamente", parent=self)
                if str(id_sucursal) == str(self.sucursal.get("id")):
                    self.sucursal["direccion"] = direccion
                    guardar_sucursal({"id": int(id_sucursal), "direccion": direccion})
            else:
                messagebox.showerror("Error", "No se pudo actualizar la sucursal", parent=self)
        else:
            ok = self.db.insertar(direccion)
            if ok:
                messagebox.showinfo("OK", "Sucursal registrada correctamente", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo guardar la sucursal", parent=self)

        self.limpiar_campos()
        self.cargar_tabla()

    def eliminar_sucursal(self):
        id_sucursal = self.txt_id.get().strip()
        if id_sucursal == "":
            messagebox.showwarning("Error", "Selecciona o ingresa un ID de sucursal", parent=self)
            return

        confirm = messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar la sucursal #{id_sucursal}? (Se eliminarán sus registros asociados en cascada)",
            parent=self,
        )
        if confirm:
            ok = self.db.eliminar(id_sucursal)
            if ok:
                messagebox.showinfo("OK", "Sucursal eliminada correctamente", parent=self)
                if str(id_sucursal) == str(self.sucursal.get("id")):
                    self.sucursal["id"] = 0
                    self.sucursal["direccion"] = "No especificado"
                    guardar_sucursal(self.sucursal)
                self.limpiar_campos()
                self.cargar_tabla()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo eliminar la sucursal (verifique si tiene usuarios asignados).",
                    parent=self,
                )

    def limpiar_campos(self):
        self.txt_id.delete(0, END)
        self.txt_direccion.delete(0, END)
        self.txt_buscar.delete(0, END)
        self.EliminarBoton.config(state="disabled")
