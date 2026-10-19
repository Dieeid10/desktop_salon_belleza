from datetime import date, datetime, timedelta
import re
import tkinter as tk
from tkinter import messagebox, ttk

from app.views._base import DataView


class TurnosView(DataView):
    def __init__(self, master: tk.Misc, salon) -> None:
        super().__init__(master, salon)
        self.on_client_selected = lambda _client: None
        self.professionals: dict[str, int] = {}
        self.services: dict[str, int] = {}
        self.client: dict | None = None

        controls = tk.LabelFrame(self, text=" Panel de Control de Turnos ", padx=10, pady=8)
        controls.pack(fill="x", padx=20, pady=8)
        left = ttk.Frame(controls)
        left.pack(side="left", fill="y", padx=5)
        self.client_label = tk.Label(
            left, text="Cliente: ninguno seleccionado", font=("Arial", 10, "bold"), fg="red"
        )
        self.client_label.pack(anchor="w", pady=2)
        ttk.Label(left, text="Profesional:").pack(anchor="w", pady=(4, 1))
        self.professional_choice = tk.StringVar()
        self.professional_combo = ttk.Combobox(
            left, textvariable=self.professional_choice, state="readonly", width=30
        )
        self.professional_combo.pack(anchor="w", fill="x")
        ttk.Label(left, text="Seleccionar Servicios (Ctrl+Click):").pack(anchor="w", pady=(6, 1))
        services_frame = ttk.Frame(left)
        services_frame.pack(fill="x")
        self.service_list = tk.Listbox(
            services_frame, selectmode="multiple", height=4, width=34, exportselection=0
        )
        service_scroll = ttk.Scrollbar(services_frame, orient="vertical", command=self.service_list.yview)
        self.service_list.configure(yscrollcommand=service_scroll.set)
        self.service_list.pack(side="left", fill="both", expand=True)
        service_scroll.pack(side="right", fill="y")
        ttk.Label(left, text="Fecha y Hora (AAAA-MM-DD HH:MM):").pack(anchor="w", pady=(6, 1))
        self.start_text = tk.StringVar(
            value=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
        )
        self.start_entry = ttk.Entry(left, textvariable=self.start_text, width=30)
        self.start_entry.pack(anchor="w", fill="x")

        right = ttk.Frame(controls)
        right.pack(side="right", fill="both", expand=True, padx=10)
        self.book_button = self._button(right, "Agendar Cita", "#16833b", "white", lambda: self.run_action(self.book))
        self.book_button.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        self.clear_button = self._button(right, "Limpiar Selección", "#f0ad4e", "black", self.clear_form)
        self.clear_button.grid(row=0, column=1, sticky="nsew", padx=3, pady=3)
        self.done_button = self._button(right, "Realizado", "#5cb85c", "white", lambda: self.run_action(lambda: self.change_status("completado")))
        self.done_button.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        self.cancel_button = self._button(right, "Cancelar Turno", "#d9534f", "white", lambda: self.run_action(lambda: self.change_status("cancelado")))
        self.cancel_button.grid(row=1, column=1, sticky="nsew", padx=3, pady=3)
        self.confirm_button = self._button(right, "Confirmar", "#0275d8", "white", lambda: self.run_action(lambda: self.change_status("confirmado")))
        self.confirm_button.grid(row=2, column=0, sticky="nsew", padx=3, pady=3)
        self.availability_button = self._button(right, "Ver Horarios Disponibles", "#5bc0de", "black", lambda: self.run_action(self.check_availability))
        self.availability_button.grid(row=2, column=1, sticky="nsew", padx=3, pady=3)
        for column in (0, 1):
            right.columnconfigure(column, weight=1)
        for row in (0, 1, 2):
            right.rowconfigure(row, weight=1)

        availability = ttk.Frame(self, padding=(20, 0, 20, 6))
        availability.pack(fill="x")
        ttk.Label(availability, text="Horarios disponibles:").pack(side="left")
        self.slots = ttk.Combobox(availability, state="readonly", width=26)
        self.slots.pack(side="left", padx=8)
        self.slots.bind("<<ComboboxSelected>>", self._select_slot)
        tk.Button(
            availability, text="Actualizar Lista", bg="#5bc0de",
            command=lambda: self.run_action(self.refresh),
        ).pack(side="right")

        frame_table = ttk.Frame(self, padding=(20, 0, 20, 10))
        frame_table.pack(fill="both", expand=True)
        self.table = self.tree(
            frame_table,
            ("ID", "Cliente", "Servicio", "Fecha/Hora", "Estado"),
            {"ID": 60, "Cliente": 145, "Servicio": 250, "Fecha/Hora": 160, "Estado": 110},
        )
        self.table.bind("<<TreeviewSelect>>", self._select_turn)
        self.service_list.bind("<<ListboxSelect>>", self._update_buttons)
        self.start_entry.bind("<KeyRelease>", self._update_buttons)
        self._update_buttons()

    @staticmethod
    def _button(parent, text, bg, fg, command):
        return tk.Button(parent, text=text, bg=bg, fg=fg, command=command)

    def refresh(self) -> None:
        professionals = self.salon.listar_profesionales()
        self.professionals = {person["nombre"]: person["id"] for person in professionals}
        self.professional_combo["values"] = tuple(self.professionals)
        if self.professionals and not self.professional_choice.get():
            self.professional_choice.set(next(iter(self.professionals)))
        catalog = self.salon.listar_servicios()
        self.services = {item["nombre_servicio"]: item["id"] for item in catalog}
        self.service_list.delete(0, tk.END)
        for name in self.services:
            self.service_list.insert(tk.END, name)
        today = date.today()
        turns = self.salon.listar_turnos(today - timedelta(days=30), today + timedelta(days=90))
        clients = self.salon.listar_clientes_con_estado()
        client_names = {item["id"]: f"{item['nombre']} {item['apellido']}" for item in clients}
        self.clear_tree(self.table)
        for turn in turns:
            services = ", ".join(detail["nombre"] for detail in turn.get("detalles", []))
            self.table.insert("", "end", values=(
                turn["id"], client_names.get(turn["cliente_id"], f"Cliente {turn['cliente_id']}"),
                services, turn["inicio"], turn["estado"],
            ))
        self._update_buttons()

    def book(self) -> None:
        if not self.client:
            raise ValueError("Seleccioná un cliente desde la pestaña ABM Clientes.")
        professional_id = self.professionals.get(self.professional_choice.get())
        if professional_id is None:
            raise ValueError("Seleccioná un profesional.")
        service_ids = [
            self.services[self.service_list.get(index)]
            for index in self.service_list.curselection()
        ]
        if not service_ids:
            raise ValueError("Seleccioná al menos un servicio.")
        try:
            start = datetime.strptime(self.start_text.get().strip(), "%Y-%m-%d %H:%M")
        except ValueError as error:
            raise ValueError("La fecha debe respetar el formato AAAA-MM-DD HH:MM.") from error
        start = start.replace(tzinfo=datetime.now().astimezone().tzinfo)
        phone = re.sub(r"\D", "", self.client.get("telefono") or "")
        if not 8 <= len(phone) <= 15:
            raise ValueError("El teléfono debe contener entre 8 y 15 dígitos para reservar.")
        payload = {
            "nombre": self.client["nombre"],
            "apellido": self.client["apellido"],
            "telefono": phone,
            "profesional_id": professional_id,
            "servicio_ids": service_ids,
            "inicio": start.isoformat(timespec="minutes"),
        }
        self.salon.reservar_turno(payload)
        self.refresh()
        self.clear_form()
        messagebox.showinfo("Agenda", "Turno reservado.", parent=self)

    def check_availability(self) -> None:
        professional_id = self.professionals.get(self.professional_choice.get())
        service_ids = [
            self.services[self.service_list.get(index)]
            for index in self.service_list.curselection()
        ]
        if professional_id is None or not service_ids:
            raise ValueError("Elegí profesional y servicios antes de consultar horarios.")
        day = datetime.strptime(self.start_text.get().strip()[:10], "%Y-%m-%d").date()
        result = self.salon.consultar_disponibilidad(professional_id, day, service_ids)
        values = tuple(
            datetime.fromisoformat(slot).astimezone().strftime("%Y-%m-%d %H:%M")
            for slot in result["horarios"]
        )
        self.slots["values"] = values
        if values:
            self.slots.current(0)
            self._select_slot()
        else:
            messagebox.showinfo("Agenda", "No hay horarios disponibles para esa fecha.", parent=self)

    def _select_slot(self, _event=None) -> None:
        self.start_text.set(self.slots.get())
        self._update_buttons()

    def fill_client(self, client: dict) -> None:
        self.client = client
        self.client_label.configure(
            text=f"Cliente: {client['nombre']} {client['apellido']}", fg="green"
        )
        self._update_buttons()

    def clear_form(self) -> None:
        self.service_list.selection_clear(0, tk.END)
        self.start_text.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.slots.set("")
        self.table.selection_remove(self.table.selection())
        self._update_buttons()

    def _select_turn(self, _event=None) -> None:
        self._update_buttons()

    def _update_buttons(self, _event=None) -> None:
        selected = self.table.selection() if hasattr(self, "table") else ()
        selected_turn = bool(selected)
        state = (
            str(self.table.item(selected[0], "values")[4]).casefold()
            if selected_turn else ""
        )
        has_form = bool(self.service_list.curselection()) or bool(self.client)
        self.book_button.configure(
            state="normal" if has_form and not selected_turn else "disabled",
            bg="#16833b" if has_form and not selected_turn else "#aaaaaa",
        )
        self.clear_button.configure(
            state="normal" if has_form or selected_turn else "disabled",
            bg="#f0ad4e" if has_form or selected_turn else "#aaaaaa",
        )
        self.done_button.configure(
            state="normal" if state == "confirmado" else "disabled",
            bg="#5cb85c" if state == "confirmado" else "#aaaaaa",
        )
        self.cancel_button.configure(
            state="normal" if state in {"pendiente", "confirmado"} else "disabled",
            bg="#d9534f" if state in {"pendiente", "confirmado"} else "#aaaaaa",
        )
        self.confirm_button.configure(
            state="normal" if state == "pendiente" else "disabled",
            bg="#0275d8" if state == "pendiente" else "#aaaaaa",
        )

    def change_status(self, state: str) -> None:
        selected = self.table.selection()
        if not selected:
            raise ValueError("Seleccioná un turno de la agenda.")
        turn_id = int(self.table.item(selected[0], "values")[0])
        self.salon.cambiar_estado_turno(turn_id, state)
        self.refresh()
        self.clear_form()