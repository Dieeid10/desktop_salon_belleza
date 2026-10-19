import tkinter as tk
from tkinter import messagebox, ttk

from app.views._base import DataView


class ServiciosView(DataView):
    def __init__(self, master: tk.Misc, salon, *, is_owner: bool) -> None:
        super().__init__(master, salon)
        self.is_owner = is_owner
        layout = ttk.Panedwindow(self, orient="vertical")
        layout.pack(fill="both", expand=True)
        form = ttk.Frame(layout, padding=(0, 0, 0, 8))
        listing = ttk.Frame(layout)
        layout.add(form, weight=1)
        layout.add(listing, weight=3)
        self.selected_id = None
        self.values = {
            "nombre_servicio": tk.StringVar(),
            "descripcion": tk.StringVar(),
            "precio": tk.StringVar(),
            "duracion_minutos": tk.StringVar(value="60"),
        }
        labels = (("nombre_servicio", "Servicio"), ("descripcion", "Descripción"),
                  ("precio", "Precio"), ("duracion_minutos", "Duración (min)"))
        self.form_entries = []
        for column, (key, label) in enumerate(labels):
            ttk.Label(form, text=label).grid(row=0, column=column, sticky="w", padx=4, pady=(4, 2))
            entry = ttk.Entry(form, textvariable=self.values[key])
            entry.grid(row=1, column=column, sticky="ew", padx=4)
            self.form_entries.append(entry)
            form.columnconfigure(column, weight=1)
        self.visible_online = tk.BooleanVar(value=True)
        self.visible_online_check = ttk.Checkbutton(form, text="Visible online", variable=self.visible_online)
        self.visible_online_check.grid(row=2, column=0, columnspan=4, sticky="w", padx=4, pady=4)
        buttons = ttk.Frame(form)
        buttons.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(2, 4))
        self.add_button = tk.Button(buttons, text="Añadir Servicio", bg="#16833b", fg="white", command=lambda: self.run_action(self.save))
        self.add_button.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.update_button = tk.Button(buttons, text="Actualizar Precio", bg="#0275d8", fg="white", command=lambda: self.run_action(self.save))
        self.update_button.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        self.clear_button = tk.Button(buttons, text="Limpiar", bg="#f0ad4e", fg="black", command=self.clear_form)
        self.clear_button.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.delete_button = tk.Button(buttons, text="Borrar Seleccionado", bg="#d9534f", fg="white", command=lambda: self.run_action(self.deactivate))
        self.delete_button.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        buttons.rowconfigure(0, weight=1)
        buttons.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(listing)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Catálogo").pack(side="left")
        ttk.Button(toolbar, text="Actualizar", command=lambda: self.run_action(self.refresh)).pack(side="right")
        self.table = self.tree(
            listing,
            ("ID", "Servicio", "Descripción", "Precio", "Min", "Visible", "Activo"),
            {"ID": 55, "Servicio": 150, "Descripción": 180, "Precio": 90,
             "Min": 70, "Visible": 75, "Activo": 75},
        )
        self.table.bind("<<TreeviewSelect>>", self.select_service)
        self._set_editing_state(False)

    def refresh(self) -> None:
        services = self.salon.listar_servicios(gestion=self.is_owner)
        self.clear_tree(self.table)
        for service in services:
            self.table.insert("", "end", values=(
                service["id"], service["nombre_servicio"], service.get("descripcion") or "",
                service["precio"],
                service["duracion_minutos"], "Sí" if service["visible_online"] else "No",
                "Sí" if service["activo"] else "No",
            ))

    def select_service(self, _event=None) -> None:
        selected = self.table.selection()
        if not selected:
            return
        values = self.table.item(selected[0], "values")
        self.selected_id = int(values[0])
        for key, value in zip(self.values, (values[1], values[2], values[3], values[4])):
            self.values[key].set(value)
        self.visible_online.set(values[5] == "Sí")
        self._set_editing_state(True)

    def save(self) -> None:
        data = {key: variable.get().strip() for key, variable in self.values.items()}
        data["nombre_servicio"] = data["nombre_servicio"]
        data["descripcion"] = data["descripcion"] or None
        data["precio"] = float(data["precio"])
        data["duracion_minutos"] = int(data["duracion_minutos"])
        data["visible_online"] = self.visible_online.get()
        if self.selected_id is None:
            self.salon.crear_servicio(data)
        else:
            self.salon.actualizar_servicio(self.selected_id, data)
        self.clear_form()
        self.refresh()

    def deactivate(self) -> None:
        if self.selected_id is None:
            messagebox.showinfo("Servicios", "Seleccioná un servicio.", parent=self)
            return
        if messagebox.askyesno("Desactivar servicio", f"¿Desactivar el servicio {self.selected_id}?", parent=self):
            self.salon.desactivar_servicio(self.selected_id)
            self.clear_form()
            self.refresh()

    def clear_form(self) -> None:
        self.selected_id = None
        for variable in self.values.values():
            variable.set("")
        self.values["duracion_minutos"].set("60")
        self.visible_online.set(True)
        self.table.selection_remove(self.table.selection())
        self._set_editing_state(False)

    def _set_editing_state(self, selected: bool) -> None:
        enabled = self.is_owner
        for entry in self.form_entries:
            entry.configure(state="normal" if enabled else "disabled")
        self.visible_online_check.configure(state="normal" if enabled else "disabled")
        self.add_button.configure(
            state="normal" if enabled and not selected else "disabled",
            bg="#16833b" if enabled and not selected else "#aaaaaa",
        )
        self.update_button.configure(
            state="normal" if enabled and selected else "disabled",
            bg="#0275d8" if enabled and selected else "#aaaaaa",
        )
        self.clear_button.configure(
            state="normal" if enabled else "disabled",
            bg="#f0ad4e" if enabled else "#aaaaaa",
        )
        self.delete_button.configure(
            state="normal" if enabled and selected else "disabled",
            bg="#d9534f" if enabled and selected else "#aaaaaa",
        )