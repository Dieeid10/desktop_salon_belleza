import tkinter as tk
from tkinter import messagebox, ttk

from app.services.api_client import ApiError
from app.services.salon_service import SalonService
from app.views.clientes import ClientesView
from app.views.servicios import ServiciosView
from app.views.turnos import TurnosView
from app.views.ventas import ComprobanteView, HistorialView


class DashboardView(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        email: str,
        is_owner: bool,
        salon: SalonService,
        on_logout,
    ) -> None:
        super().__init__(master)
        header = tk.Frame(self, bg="#333333", padx=10, pady=5)
        header.pack(fill="x")
        tk.Label(
            header,
            text=f"Usuario: {email} ({'DUEÑO' if is_owner else 'VENDEDOR'})",
            fg="white",
            bg="#333333",
            font=("Arial", 10, "bold"),
        ).pack(side="left")
        tk.Button(
            header,
            text="Cambiar Usuario",
            command=on_logout,
            bg="#d9534f",
            fg="white",
            font=("Arial", 9, "bold"),
            bd=0,
            padx=10,
        ).pack(side="right", padx=5)

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        self.tabs = tabs
        self.views = []
        self.clients = ClientesView(tabs, salon, is_owner=is_owner)
        self.services = ServiciosView(tabs, salon, is_owner=is_owner)
        self.receipts = ComprobanteView(tabs, salon, email=email)
        self.history = HistorialView(tabs, salon)
        self.turns = TurnosView(tabs, salon)
        self.user_admin = UsuariosView(tabs, is_owner=is_owner)
        self.clients.on_use_client = self._select_client
        self.turns.on_client_selected = self.turns.fill_client

        self.views.extend((self.clients, self.services, self.receipts, self.history, self.turns, self.user_admin))
        tabs.add(self.clients, text="ABM Clientes")
        tabs.add(self.services, text="Lista de Precios")
        tabs.add(self.receipts, text="Emitir Comprobante")
        tabs.add(self.history, text="Historial de Ventas")
        tabs.add(self.turns, text="Agenda de Turnos")
        if is_owner:
            tabs.add(self.user_admin, text="Gestión de Usuarios")

        self.loaded: set[int] = set()
        tabs.bind("<<NotebookTabChanged>>", self._tab_changed)
        self._tab_changed()

    def _select_client(self, client: dict) -> None:
        self.receipts.filter_client(client)
        self.turns.fill_client(client)

    def _tab_changed(self, _event=None) -> None:
        tab = self.tabs.select()
        if not tab:
            return
        view = self.nametowidget(tab)
        if id(view) in self.loaded or not hasattr(view, "refresh"):
            return
        try:
            view.refresh()
        except ApiError as error:
            messagebox.showerror("Error de API", str(error), parent=view)
        else:
            self.loaded.add(id(view))


class UsuariosView(ttk.Frame):
    def __init__(self, master: tk.Misc, *, is_owner: bool) -> None:
        super().__init__(master, padding=16)
        title = "Gestión de Usuarios" if is_owner else "Gestión restringida"
        ttk.Label(self, text=title, font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(
            self,
            text=(
                "La API actual delega las cuentas y contraseñas en Supabase Auth.\n"
                "Todavía no expone operaciones para listar usuarios, crear cuentas\n"
                "o cambiar contraseñas desde el desktop."
                if is_owner else "Solo la dueña puede administrar usuarios."
            ),
            justify="left",
        ).pack(anchor="w")