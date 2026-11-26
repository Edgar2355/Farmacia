# Sistema de Diseño y Tema Visual - Farmacia CUCEI
# Paleta moderna, accesible (alto contraste WCAG AA) y ergonómica para punto de venta
import tkinter as tk
from tkinter import ttk

backgroundColor = "#eef6f9"       # Azul hielo suave (reduce fatiga visual)
surfaceColor = "#ffffff"          # Blanco puro para tarjetas, paneles y tablas
headerColor = "#0d3b66"           # Azul marino institucional para barras superiores
textColor = "#1e293b"             # Gris pizarra oscuro para texto principal
mutedTextColor = "#64748b"        # Gris medio para subtítulos y etiquetas secundarias

buttonColor = "#1d4ed8"           # Azul primario (Alto contraste con texto blanco)
buttonHoverColor = "#1e40af"

OkButtonColor = "#15803d"         # Verde esmeralda oscuro (Legible con texto blanco)
OkButtonHover = "#166534"

CancelButtonColor = "#dc2626"     # Rojo carmesí (Acciones destructivas)
CancelButtonHover = "#b91c1c"

WarningColor = "#fef3c7"          # Fondo ámbar suave para avisos
DangerRowBg = "#fee2e2"           # Fondo rojo suave para alertas de stock bajo
DangerRowFg = "#991b1b"           # Texto rojo oscuro para alertas de stock bajo

buttonstyle = {
    "background": buttonColor,
    "foreground": "white",
    "font": ("Segoe UI", 10, "bold"),
    "padding": (10, 5),
}

buttonmap = {
    "background": [("active", buttonHoverColor), ("disabled", "#94a3b8")],
    "foreground": [("active", "#ffffff"), ("disabled", "#e2e8f0")],
    "bordercolor": [("!active", buttonColor), ("active", buttonHoverColor)],
    "relief": [("pressed", "sunken"), ("!pressed", "flat")],
}

buttonstyle_aceptar = {
    "background": OkButtonColor,
    "foreground": "white",
    "font": ("Segoe UI", 10, "bold"),
    "padding": (10, 5),
}

buttonmap_aceptar = {
    "background": [("active", OkButtonHover), ("disabled", "#94a3b8")],
    "foreground": [("active", "#ffffff"), ("disabled", "#e2e8f0")],
    "bordercolor": [("!active", OkButtonColor), ("active", OkButtonHover)],
    "relief": [("pressed", "sunken"), ("!pressed", "flat")],
}

buttonstyle_rechazar = {
    "background": CancelButtonColor,
    "foreground": "white",
    "font": ("Segoe UI", 10, "bold"),
    "padding": (10, 5),
}

buttonmap_rechazar = {
    "background": [("active", CancelButtonHover), ("disabled", "#94a3b8")],
    "foreground": [("active", "#ffffff"), ("disabled", "#e2e8f0")],
    "bordercolor": [("!active", CancelButtonColor), ("active", CancelButtonHover)],
    "relief": [("pressed", "sunken"), ("!pressed", "flat")],
}


def maximizar_ventana(ventana, ancho_base=1100, alto_base=720):
    """Abre cualquier ventana Tk o Toplevel en formato de ventana completa (compatible con Windows, Linux y macOS)."""
    ventana.resizable(True, True)
    ventana.update_idletasks()
    sw = ventana.winfo_screenwidth()
    sh = ventana.winfo_screenheight()
    x = max(0, (sw - ancho_base) // 2)
    y = max(0, (sh - alto_base) // 2)
    ventana.geometry(f"{ancho_base}x{alto_base}+{x}+{y}")

    # 1. En Linux / X11 / Wayland la forma estándar de maximizar en Tk es attributes("-zoomed", True)
    import sys
    if sys.platform.startswith("linux"):
        try:
            ventana.attributes("-zoomed", True)
            return
        except Exception:
            pass

    # 2. En Windows / macOS se utiliza state("zoomed")
    try:
        ventana.state("zoomed")
        return
    except Exception:
        pass

    # 3. Fallback universal a las dimensiones completas del monitor
    try:
        ventana.attributes("-zoomed", True)
    except Exception:
        ventana.geometry(f"{sw}x{sh}+0+0")


def centrar_ventana(ventana, ancho, alto, maximizar=True):
    """
    Si maximizar=True (por defecto para el menú y todas las pestañas de la app),
    muestra la ventana en formato ventana completa ('zoomed').
    Si maximizar=False (ej. diálogos pequeños), la centra con el tamaño indicado.
    """
    if maximizar:
        maximizar_ventana(ventana, ancho, alto)
        return
    ventana.update_idletasks()
    sw = ventana.winfo_screenwidth()
    sh = ventana.winfo_screenheight()
    x = max(0, (sw - ancho) // 2)
    y = max(0, (sh - alto) // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


def aplicar_tema(ventana):
    """Configura los estilos ttk unificados (botones, tablas Treeview, entradas y etiquetas)."""
    style = ttk.Style(ventana)
    style.theme_use("clam")

    style.configure("TLabel", background=backgroundColor, foreground=textColor, font=("Segoe UI", 10))
    style.configure("Header.TLabel", background=headerColor, foreground="white", font=("Segoe UI", 14, "bold"))
    style.configure("SubHeader.TLabel", background=headerColor, foreground="#cbd5e1", font=("Segoe UI", 9))
    style.configure("Card.TFrame", background=surfaceColor, relief="solid", borderwidth=1)

    style.configure("BotonesEstilo.TButton", **buttonstyle)
    style.map("BotonesEstilo.TButton", **buttonmap)

    style.configure("BotonesAceptar.TButton", **buttonstyle_aceptar)
    style.map("BotonesAceptar.TButton", **buttonmap_aceptar)

    style.configure("BotonesRechazar.TButton", **buttonstyle_rechazar)
    style.map("BotonesRechazar.TButton", **buttonmap_rechazar)

    nav_btn = {
        "background": "#1e3a8a",
        "foreground": "#e2e8f0",
        "font": ("Segoe UI", 9, "bold"),
        "padding": (10, 4),
    }
    style.configure("NavTab.TButton", **nav_btn)
    style.map(
        "NavTab.TButton",
        background=[("active", "#2563eb"), ("disabled", "#0f172a")],
        foreground=[("active", "#ffffff")],
        relief=[("pressed", "sunken"), ("!pressed", "flat")],
    )

    nav_active = {
        "background": "#2563eb",
        "foreground": "#ffffff",
        "font": ("Segoe UI", 9, "bold"),
        "padding": (10, 4),
    }
    style.configure("NavTabActive.TButton", **nav_active)
    style.map("NavTabActive.TButton", background=[("active", "#1d4ed8")])

    menu_btn = dict(buttonstyle)
    menu_btn["font"] = ("Segoe UI", 12, "bold")
    menu_btn["padding"] = (12, 8)
    style.configure("MenuPrincipal.TButton", **menu_btn)
    style.map("MenuPrincipal.TButton", **buttonmap)

    # Estilo moderno para tablas Treeview
    style.configure(
        "Treeview",
        background=surfaceColor,
        fieldbackground=surfaceColor,
        foreground=textColor,
        rowheight=30,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Treeview.Heading",
        background="#dbeafe",
        foreground="#1e3a8a",
        font=("Segoe UI", 10, "bold"),
        padding=(6, 6),
    )
    style.map(
        "Treeview",
        background=[("selected", "#2563eb")],
        foreground=[("selected", "white")],
    )
    return style


def crear_encabezado(ventana, titulo, subtitulo=""):
    """
    Crea una barra superior institucional con título, subtítulo, botón 'Volver al Menú Principal'
    y una barra de pestañas de navegación rápida entre todos los módulos permitidos por el rol.
    """
    header = tk.Frame(ventana, bg=headerColor, height=56)
    header.pack(fill=tk.X, side=tk.TOP)
    header.pack_propagate(False)

    lbl_titulo = tk.Label(
        header,
        text=titulo,
        bg=headerColor,
        fg="white",
        font=("Segoe UI", 14, "bold"),
    )
    lbl_titulo.pack(side=tk.LEFT, padx=18, pady=(8, 2))

    if isinstance(ventana, tk.Toplevel):
        ventana.bind("<Escape>", lambda e: ventana.destroy())
        btn_volver = ttk.Button(
            header,
            text="Volver al Menú Principal (Esc)",
            style="BotonesRechazar.TButton",
            command=ventana.destroy,
        )
        btn_volver.pack(side=tk.RIGHT, padx=16, pady=10)

    if subtitulo:
        lbl_sub = tk.Label(
            header,
            text=subtitulo,
            bg=headerColor,
            fg="#bfdbfe",
            font=("Segoe UI", 9),
        )
        lbl_sub.pack(side=tk.RIGHT, padx=14)

    # Barra de navegación rápida entre pestañas si la ventana es hija del menú principal (App)
    master = getattr(ventana, "master", None)
    if isinstance(ventana, tk.Toplevel) and master is not None and hasattr(master, "obtener_rutas_navegacion"):
        nav_bar = tk.Frame(ventana, bg="#172554", pady=5, padx=14)
        nav_bar.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            nav_bar,
            text="Navegación Rápida:",
            bg="#172554",
            fg="#93c5fd",
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(4, 10))

        nombre_clase_actual = ventana.__class__.__name__
        for etiqueta_tab, nombre_clase_destino, comando_nav in master.obtener_rutas_navegacion():
            es_actual = (nombre_clase_actual == nombre_clase_destino)
            estilo_btn = "NavTabActive.TButton" if es_actual else "NavTab.TButton"
            btn_tab = ttk.Button(
                nav_bar,
                text=etiqueta_tab,
                style=estilo_btn,
                command=(lambda: None) if es_actual else comando_nav,
            )
            btn_tab.pack(side=tk.LEFT, padx=3)

        if hasattr(master, "abrir_config_tunel_menu"):
            ttk.Button(
                nav_bar,
                text="Cambiar Túnel Pinggy / BD",
                style="NavTab.TButton",
                command=master.abrir_config_tunel_menu,
            ).pack(side=tk.RIGHT, padx=4)

    return header
