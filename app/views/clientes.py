import tkinter as tk
from tkinter import messagebox, ttk

from app.views._base import DataView

class ClientesView(DataView):
    def __init__(self, master: tk.Misc, salon, *, is_owner: bool) -> None:
        super().__init__(master, salon)
        self.is_owner = is_owner
        self.on_use_client = lambda _client: None
        self.clients: list[dict] = []
        self.active_tab = True
        self.fields: dict[str, tk.StringVar] = {}
        self.tables: dict[bool, ttk.Treeview] = {}
        self.buttons: dict[str, tk.Button] = {}
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)
        self.active_page = ttk.Frame(self.tabs)
        self.tabs.add(self.active_page, text="Clientes Activos")
        self._build_page(self.active_page, inactive=False)
        if is_owner:
            self.inactive_page = ttk.Frame(self.tabs)
            self.tabs.add(self.inactive_page, text="Clientes Eliminados")
            self._build_page(self.inactive_page, inactive=True)
        self.tabs.bind("<<NotebookTabChanged>>", self._tab_changed)

    def _build_page(self, page: ttk.Frame, *, inactive: bool) -> None:
        layout = ttk.Panedwindow(page, orient="horizontal")
        layout.pack(fill="both", expand=True)
        if inactive:
            listing = ttk.Frame(layout, padding=10)
            layout.add(listing, weight=1)
            toolbar = ttk.Frame(listing, padding=(0, 0, 0, 5))
            toolbar.pack(fill="x")
            ttk.Label(toolbar, text="Clientes eliminados", font=("Arial", 9, "bold")).pack(side="left")
            search = ttk.Entry(toolbar)
            search.pack(side="left", fill="x", expand=True, padx=8)
            ttk.Button(toolbar, text="Actualizar", command=lambda: self.run_action(self.refresh)).pack(side="right")
            table = ttk.Treeview(
                listing,
                columns=("ID", "Nombre", "Apellido", "Teléfono", "Email"),
                show="headings",
                selectmode="browse",
            )
            for name, width in zip(("ID", "Nombre", "Apellido", "Teléfono", "Email"), (55, 120, 120, 120, 200)):
                table.heading(name, text=name)
                table.column(name, width=width, stretch=name == "Email")
            scrollbar = ttk.Scrollbar(listing, orient="vertical", command=table.yview)
            table.configure(yscrollcommand=scrollbar.set)
            table.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            table.bind("<<TreeviewSelect>>", self.select_client)
            search.bind("<KeyRelease>", lambda _event: self.filter_table(search.get(), True))
            self.tables[True] = table
            tk.Button(
                listing,
                text="Reactivar Cliente",
                bg="#5cb85c",
                fg="white",
                command=lambda: self.run_action(self.activate),
            ).pack(anchor="w", pady=8)
            return
        form = ttk.Frame(layout, padding=10)
        listing = ttk.Frame(layout, padding=10)
        layout.add(form, weight=1)
        layout.add(listing, weight=3)
        labels = ("Nombre:", "Apellido:", "Teléfono:", "Email:")
        for row, (key, label) in enumerate(zip(("nombre", "apellido", "telefono", "email"), labels)):
            ttk.Label(form, text=label).grid(row=row * 2, column=0, sticky="w", pady=(4, 1))
            variable = tk.StringVar()
            self.fields[key] = variable
            entry = ttk.Entry(form, textvariable=variable)
            entry.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(0, 3))
            entry.bind("<KeyRelease>", self.update_buttons)
        form.columnconfigure(0, weight=1)

        specs = (
            ("Registrar Cliente", "#16833b", "white", self.save),
            ("Actualizar Datos", "#0275d8", "white", self.save),
            ("Cancelar Selección / Limpiar", "#f0ad4e", "black", self.clear_form),
            ("Eliminar Seleccionado", "#d9534f", "white", self.deactivate),
            ("Usar para Comprobante / Turno", "#f0a020", "black", self.use_client),
        )
        
        for row, (label, color, foreground, action) in enumerate(specs, start=8):
            button = tk.Button(
                form, text=label, bg=color, fg=foreground,
                command=lambda callback=action: self.run_action(callback),
            )
            button.grid(row=row, column=0, sticky="ew", pady=3)
            self.buttons[label] = button

        toolbar = ttk.Frame(listing, padding=(0, 0, 0, 5))
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="Buscar Cliente (Nombre/Apellido):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))
        search = ttk.Entry(toolbar)
        search.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(toolbar, text="Actualizar", command=lambda: self.run_action(self.refresh)).pack(side="right", padx=(6, 0))
        columns = ("ID", "Nombre", "Apellido", "Teléfono", "Email")
        table = ttk.Treeview(listing, columns=columns, show="headings", selectmode="browse")
        for name, width in zip(columns, (55, 100, 105, 100, 155)):
            table.heading(name, text=name)
            table.column(name, width=width, stretch=name in ("Nombre", "Apellido", "Email"))
        scrollbar = ttk.Scrollbar(listing, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        table.bind("<<TreeviewSelect>>", self.select_client)
        search.bind("<KeyRelease>", lambda _event: self.filter_table(search.get(), inactive))
        self.tables[inactive] = table

    def refresh(self) -> None:
        self.clients = self.salon.listar_clientes_con_estado()
        self.filter_table("", not self.active_tab)

    def _tab_changed(self, _event=None) -> None:
        self.active_tab = self.tabs.index(self.tabs.select()) == 0
        self.run_action(self.refresh)

    def filter_table(self, text: str, inactive: bool) -> None:
        table = self.tables[inactive]
        query = text.strip().casefold()
        table.delete(*table.get_children())
        for client in self.clients:
            if bool(client["activo"]) == inactive:
                continue
            full_name = f"{client['nombre']} {client['apellido']}".casefold()
            if query and query not in full_name:
                continue
            table.insert("", "end", iid=str(client["id"]), values=(
                client["id"], client["nombre"], client["apellido"],
                client.get("telefono") or "", client.get("email") or "",
            ))
        if not inactive:
            self.update_buttons()

    def select_client(self, _event=None) -> None:
        table = self.tables[not self.active_tab]
        selected = table.selection()
        if not selected:
            return
        values = table.item(selected[0], "values")
        for key, value in zip(self.fields, values[1:]):
            self.fields[key].set(value)
        self.update_buttons()

    def save(self) -> None:
        data = {key: var.get().strip() or None for key, var in self.fields.items()}
        if not data["nombre"] or not data["apellido"]:
            raise ValueError("Nombre y apellido son obligatorios.")
        selected = self.tables[False].selection()
        if selected:
            self.salon.actualizar_cliente(int(selected[0]), data)
        else:
            self.salon.crear_cliente(data)
        self.clear_form()
        self.refresh()

    def deactivate(self) -> None:
        selected = self.tables[False].selection()
        if not selected:
            raise ValueError("Seleccioná un cliente.")
        client_id = int(selected[0])
        if self.is_owner and messagebox.askyesno("Confirmar baja", "¿Eliminar el cliente seleccionado?", parent=self):
            self.salon.desactivar_cliente(client_id)
            self.clear_form()
            self.refresh()

    def activate(self) -> None:
        selected = self.tables[True].selection()
        if not selected:
            raise ValueError("Seleccioná un cliente eliminado.")
        client_id = int(selected[0])
        if messagebox.askyesno("Confirmar reactivación", "¿Reactivar el cliente seleccionado?", parent=self):
            self.salon.activar_cliente(client_id)
            self.clear_form()
            self.refresh()

    def use_client(self) -> None:
        selected = self.tables[False].selection()
        if not selected:
            raise ValueError("Seleccioná primero un cliente activo.")
        client = next(item for item in self.clients if item["id"] == int(selected[0]))
        self.on_use_client(client)
        messagebox.showinfo("Cliente seleccionado", f"{client['nombre']} {client['apellido']}", parent=self)

    def clear_form(self) -> None:
        for variable in self.fields.values():
            variable.set("")
        self.tables[False].selection_remove(self.tables[False].selection())
        self.update_buttons()

    def update_buttons(self, _event=None) -> None:
        table = self.tables.get(False)
        selected = bool(table and table.selection())
        can_create = bool(self.fields.get("nombre") and self.fields["nombre"].get().strip()
                          and self.fields["apellido"].get().strip() and not selected)
        self.buttons["Registrar Cliente"].configure(
            state="normal" if can_create else "disabled", bg="#16833b" if can_create else "#aaaaaa"
        )
        self.buttons["Actualizar Datos"].configure(state="normal" if selected else "disabled")
        self.buttons["Eliminar Seleccionado"].configure(
            state="normal" if selected and self.is_owner else "disabled",
            bg="#d9534f" if selected and self.is_owner else "#aaaaaa",
        )
        self.buttons["Usar para Comprobante / Turno"].configure(state="normal" if selected else "disabled")
        has_input = any(var.get().strip() for var in self.fields.values())
        self.buttons["Cancelar Selección / Limpiar"].configure(
            state="normal" if selected or has_input else "disabled"
        )