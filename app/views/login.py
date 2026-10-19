import tkinter as tk
from tkinter import ttk
from collections.abc import Callable


class LoginView(ttk.Frame):
    def __init__(self, master: tk.Misc, on_login: Callable[[str, str], None]) -> None:
        super().__init__(master, padding=12)
        self.on_login = on_login

        panel = ttk.Frame(self)
        panel.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(panel, text="Email:", font=("Arial", 10, "bold")).pack(pady=5)
        self.email = ttk.Entry(panel, font=("Arial", 10), width=27)
        self.email.pack()
        ttk.Label(panel, text="Contraseña:", font=("Arial", 10, "bold")).pack(pady=5)
        self.password = ttk.Entry(panel, show="*", font=("Arial", 10), width=27)
        self.password.pack()
        self.submit = tk.Button(
            panel,
            text="Ingresar",
            command=self._submit,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.submit.pack(pady=15, fill="x")
        self.email.focus_set()
        self.email.bind("<Return>", self._on_enter)
        self.password.bind("<Return>", self._on_enter)

    def _submit(self) -> None:
        email = self.email.get().strip()
        password = self.password.get()
        if not email or not password:
            from tkinter import messagebox

            messagebox.showwarning("Datos incompletos", "Ingresá email y contraseña.", parent=self)
            return
            self.submit.configure(state="disabled")
        try:
            self.on_login(email, password)
        finally:
            if self.winfo_exists():
                self.submit.configure(state="normal")

    def _on_enter(self, _event: tk.Event) -> None:
        self._submit()