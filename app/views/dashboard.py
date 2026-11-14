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
        self.user_admin = UsuariosView(tabs, salon=salon, is_owner=is_owner)
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
        if not hasattr(view, "refresh"):
            return
        try:
            view.refresh()
        except ApiError as error:
            messagebox.showerror("Error de API", str(error), parent=view)


class UsuariosView(ttk.Frame):
    def __init__(self, master: tk.Misc, *, salon: SalonService, is_owner: bool) -> None:
        super().__init__(master, padding=16)
        self.salon = salon
        ttk.Label(self, text="Gestión de Vendedores", font=("Arial", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )
        if not is_owner:
            ttk.Label(self, text="Solo la dueña puede administrar vendedores.").pack(
                anchor="w"
            )
            return

        form = ttk.LabelFrame(self, text="Invitar vendedor", padding=10)
        form.pack(fill="x", pady=(0, 12))
        self.name = tk.StringVar()
        self.email = tk.StringVar()
        ttk.Label(form, text="Nombre:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(form, textvariable=self.name, width=28).grid(
            row=0, column=1, sticky="ew", padx=(0, 12)
        )
        ttk.Label(form, text="Email:").grid(row=0, column=2, sticky="w", padx=(0, 8))
        ttk.Entry(form, textvariable=self.email, width=32).grid(
            row=0, column=3, sticky="ew", padx=(0, 12)
        )
        ttk.Button(form, text="Enviar invitación", command=self.invite).grid(
            row=0, column=4, sticky="ew"
        )
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=2)

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 6))
        ttk.Label(toolbar, text="Cuentas con acceso al escritorio").pack(side="left")
        ttk.Button(toolbar, text="Actualizar", command=self.refresh).pack(side="right")

        self.table = ttk.Treeview(
            self,
            columns=("name", "email", "role", "created"),
            show="headings",
            selectmode="browse",
        )
        for column, heading, width in (
            ("name", "Nombre", 180),
            ("email", "Email", 250),
            ("role", "Rol", 100),
            ("created", "Creado", 170),
        ):
            self.table.heading(column, text=heading)
            self.table.column(column, width=width, stretch=column == "email")
        self.table.pack(fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", self._update_delete_button)
        self.delete_button = ttk.Button(
            self,
            text="Eliminar acceso del vendedor seleccionado",
            command=self.remove_seller,
            state="disabled",
        )
        self.delete_button.pack(anchor="w", pady=(8, 0))

    def refresh(self) -> None:
        try:
            staff = self.salon.listar_personal()
        except ApiError as error:
            messagebox.showerror("Personal", str(error), parent=self)
            return
        self.table.delete(*self.table.get_children())
        for person in staff:
            self.table.insert(
                "",
                "end",
                iid=str(person["id"]),
                values=(
                    person["name"],
                    person.get("email") or "",
                    person["role"],
                    person["created_at"],
                ),
            )
        self._update_delete_button()

    def invite(self) -> None:
        name = self.name.get().strip()
        email = self.email.get().strip()
        if not name or not email:
            messagebox.showwarning(
                "Datos incompletos",
                "Ingresá el nombre y el email del vendedor.",
                parent=self,
            )
            return
        try:
            self.salon.invitar_vendedor(name, email)
        except ApiError as error:
            messagebox.showerror("No se pudo invitar", str(error), parent=self)
            return
        self.name.set("")
        self.email.set("")
        self.refresh()
        messagebox.showinfo(
            "Invitación enviada",
            "Se envió un email para que el vendedor configure su contraseña.",
            parent=self,
        )

    def remove_seller(self) -> None:
        selection = self.table.selection()
        if not selection:
            return
        user_id = selection[0]
        email = self.table.item(user_id, "values")[1]
        if not messagebox.askyesno(
            "Eliminar acceso",
            f"¿Eliminar la cuenta de vendedor {email}? Esta acción no se puede deshacer.",
            parent=self,
        ):
            return
        try:
            self.salon.eliminar_vendedor(user_id)
        except ApiError as error:
            messagebox.showerror("No se pudo eliminar", str(error), parent=self)
            return
        self.refresh()

    def _update_delete_button(self, _event=None) -> None:
        if hasattr(self, "delete_button"):
            state = "normal" if self.table.selection() else "disabled"
            self.delete_button.configure(state=state)