import tkinter as tk
from tkinter import messagebox, ttk
from collections.abc import Callable

from app.services.api_client import ApiError


class DataView(ttk.Frame):
    def __init__(self, master: tk.Misc, salon) -> None:
        super().__init__(master, padding=12)
        self.salon = salon

    def add_to(self, notebook: ttk.Notebook, label: str) -> None:
        notebook.add(self, text=label)

    def run_action(self, action: Callable[[], None]) -> None:
        try:
            action()
        except ApiError as error:
            messagebox.showerror("Error de API", str(error), parent=self)
        except (ValueError, TypeError) as error:
            messagebox.showwarning("Revisá los datos", str(error), parent=self)

    def tree(self, parent: tk.Misc, columns: tuple[str, ...], widths: dict[str, int]):
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=widths.get(column, 120), stretch=True)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    @staticmethod
    def clear_tree(tree: ttk.Treeview) -> None:
        tree.delete(*tree.get_children())