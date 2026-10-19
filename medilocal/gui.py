"""Native desktop UI. No browser, network connection or third-party runtime package."""
import sqlite3
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

from .i18n import tr
from .paths import legacy_candidates, load_settings, save_settings
from .store import DataError
from .validation import ValidationError

PALETTES = {
    "light": dict(bg="#F5F7F6", panel="#FFFFFF", fg="#213431", muted="#405D56", border="#748E85", accent="#245E55", onaccent="#FFFFFF", field="#FFFFFF", error="#A01C28", selected="#245E55"),
    "dark": dict(bg="#172622", panel="#22352F", fg="#EEF5F1", muted="#BCD3C7", border="#78978A", accent="#B7DFD1", onaccent="#173A30", field="#192E27", error="#FFB7BA", selected="#345D4F"),
}


class App:
    def __init__(self, root, store):
        self.root, self.store = root, store
        self.settings = load_settings(store.path.parent)
        self.profile_id = None
        self.screen = "profiles"
        self.search = tk.StringVar()
        self.status = tk.StringVar()
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        root.title("MediLocal")
        root.geometry("1080x760")
        root.minsize(720, 540)
        root.report_callback_exception = self.callback_error
        self.apply_theme()
        self.build()
        self.legacy_timer = root.after(200, self.offer_legacy)
        root.bind("<Destroy>", self.cancel_timer, add="+")

    def cancel_timer(self, event):
        if event.widget is self.root and self.legacy_timer:
            self.root.after_cancel(self.legacy_timer)
            self.legacy_timer = None

    def t(self, key, **kw):
        return tr(key, self.settings["language"], **kw)

    def run_action(self, action):
        try:
            return action()
        except ValidationError as error:
            messagebox.showerror(self.t("error"), self.t(error.key), parent=self.root)
        except DataError as error:
            messagebox.showerror(self.t("error"), self.t(str(error)), parent=self.root)
        except (sqlite3.Error, OSError):
            messagebox.showerror(self.t("error"), self.t("storage_error"), parent=self.root)

    def callback_error(self, exc, value, traceback):
        # Deliberately do not log exception values or user-provided data.
        key = "storage_error" if issubclass(exc, (OSError, sqlite3.Error)) else "unexpected_error"
        messagebox.showerror(self.t("error"), self.t(key), parent=self.root)

    def apply_theme(self):
        c = PALETTES[self.settings["theme"]]
        size = self.settings["font_size"]
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
            tkfont.nametofont(name).configure(size=size)
        self.root.configure(background=c["bg"])
        self.root.option_add("*selectBackground", c["selected"])
        self.root.option_add("*selectForeground", c["fg"] if self.settings["theme"] == "dark" else "#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.background", c["field"])
        self.root.option_add("*TCombobox*Listbox.foreground", c["fg"])
        self.style.configure(".", background=c["bg"], foreground=c["fg"], font="TkDefaultFont", bordercolor=c["border"], focuscolor=c["accent"])
        self.style.configure("TLabel", background=c["bg"], foreground=c["fg"])
        self.style.configure("Title.TLabel", font=(tkfont.nametofont("TkDefaultFont").actual("family"), size + 7, "bold"))
        self.style.configure("Error.TLabel", foreground=c["error"])
        self.style.configure("TButton", padding=(12, 8), background=c["panel"], foreground=c["fg"], borderwidth=1)
        self.style.map("TButton", background=[("active", c["selected"])], foreground=[("active", "#FFFFFF")])
        self.style.configure("Primary.TButton", background=c["accent"], foreground=c["onaccent"])
        self.style.map("Primary.TButton", background=[("active", c["accent"])], foreground=[("active", c["onaccent"])])
        for kind in ("TEntry", "TCombobox", "TSpinbox"):
            self.style.configure(kind, fieldbackground=c["field"], foreground=c["fg"], insertcolor=c["fg"], arrowcolor=c["fg"], padding=5)
            self.style.map(kind, fieldbackground=[("readonly", c["field"])], foreground=[("readonly", c["fg"])], selectbackground=[("readonly", c["field"])], selectforeground=[("readonly", c["fg"])])
        self.style.configure("Treeview", background=c["field"], fieldbackground=c["field"], foreground=c["fg"], rowheight=int(size*2.8))
        self.style.configure("Treeview.Heading", background=c["panel"], foreground=c["fg"], padding=8)
        self.style.map("Treeview", background=[("selected", c["selected"])], foreground=[("selected", "#FFFFFF")])

    def button(self, parent, key, command, primary=False):
        return ttk.Button(parent, text=self.t(key), command=lambda: self.run_action(command), style="Primary.TButton" if primary else "TButton")

    def build(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        header = ttk.Frame(self.root, padding=(20, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="MediLocal", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=self.t("subtitle"), wraplength=640).grid(row=1, column=0, sticky="w", pady=(2, 12))
        controls = ttk.Frame(header)
        controls.grid(row=2, column=0, sticky="w")
        ttk.Label(controls, text=self.t("language")).grid(row=0, column=0, sticky="w")
        lang = ttk.Combobox(controls, values=["Español", "English"], state="readonly", width=10)
        lang.current(self.settings["language"] == "en")
        lang.grid(row=1, column=0, padx=(0, 15))
        lang.bind("<<ComboboxSelected>>", lambda e: self.change_setting("language", ("es", "en")[lang.current()]))
        ttk.Label(controls, text=self.t("theme")).grid(row=0, column=1, sticky="w")
        theme = ttk.Combobox(controls, values=[self.t("dark"), self.t("light")], state="readonly", width=10)
        theme.current(self.settings["theme"] == "light")
        theme.grid(row=1, column=1, padx=(0, 15))
        theme.bind("<<ComboboxSelected>>", lambda e: self.change_setting("theme", ("dark", "light")[theme.current()]))
        ttk.Label(controls, text=self.t("text_size")).grid(row=0, column=2, sticky="w")
        sizes = ttk.Combobox(controls, values=[10, 12, 14, 16, 18, 20], state="readonly", width=4)
        sizes.set(self.settings["font_size"])
        sizes.grid(row=1, column=2)
        sizes.bind("<<ComboboxSelected>>", lambda e: self.change_setting("font_size", int(sizes.get())))
        center = ttk.Frame(self.root)
        center.grid(row=1, column=0, sticky="nsew")
        center.columnconfigure(0, weight=1)
        center.rowconfigure(0, weight=1)
        canvas = tk.Canvas(center, highlightthickness=0, background=PALETTES[self.settings["theme"]]["bg"])
        canvas.grid(row=0, column=0, sticky="nsew")
        outer_scroll = ttk.Scrollbar(center, command=canvas.yview)
        outer_scroll.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=outer_scroll.set)
        self.content = ttk.Frame(canvas, padding=(20, 4, 20, 10))
        item = canvas.create_window(0, 0, window=self.content, anchor="nw")
        def resize_content(event=None):
            canvas.itemconfigure(item, width=canvas.winfo_width(), height=max(canvas.winfo_height(), self.content.winfo_reqheight()))
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.content.bind("<Configure>", resize_content)
        canvas.bind("<Configure>", resize_content)
        def reveal_focus(event):
            widget = event.widget
            if not str(widget).startswith(str(self.content)):
                return
            top = widget.winfo_rooty()-self.content.winfo_rooty()
            if top < canvas.canvasy(0) or top+widget.winfo_height() > canvas.canvasy(0)+canvas.winfo_height():
                canvas.yview_moveto(max(0, top-10)/max(1, self.content.winfo_height()))
        self.root.bind("<FocusIn>", reveal_focus)
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(3, weight=1)
        footer = ttk.Frame(self.root, padding=(20, 8))
        footer.grid(row=2, column=0, sticky="ew")
        ttk.Label(footer, textvariable=self.status, wraplength=650).pack(anchor="w")
        ttk.Label(footer, text=self.t("footer"), wraplength=650).pack(anchor="w")
        self.show(self.screen, reset=False)

    def change_setting(self, key, value):
        self.settings[key] = value
        self.run_action(lambda: save_settings(self.settings, self.store.path.parent))
        self.status.set("")
        self.apply_theme()
        self.build()

    def show(self, screen="profiles", reset=True):
        self.screen = screen
        for child in self.content.winfo_children():
            child.destroy()
        if reset:
            self.search.set("")
            self.status.set("")
        if screen == "backups":
            self.backup_screen()
            return
        self.rows = {}
        profile = self.current_profile() if screen == "products" else None
        if screen == "products" and profile is None:
            self.show("profiles")
            return
        title = self.t("profiles") if profile is None else f'{profile["nombre"]} / {self.t(profile["tipo"])}'
        ttk.Label(self.content, text=title, style="Title.TLabel", wraplength=650).grid(row=0, column=0, sticky="w", pady=(8, 12))
        bar = ttk.Frame(self.content)
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(bar, text=self.t("search")).pack(side="left", padx=(0, 10))
        entry = ttk.Entry(bar, textvariable=self.search)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda e: self.refresh())
        actions = ttk.Frame(self.content)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        if profile is None:
            keys = [("new_profile", lambda: self.profile_form()), ("open_profile", self.open_selected), ("edit_profile", self.edit_profile), ("delete_profile", self.delete_profile), ("backups", lambda: self.show("backups"))]
        else:
            keys = [("add_product", lambda: self.product_form()), ("edit_product", self.edit_product), ("details", self.product_details), ("delete_product", self.delete_product), ("back", lambda: self.show("profiles"))]
        # Wrap actions onto two rows so translated labels and enlarged text fit.
        for index, (key, command) in enumerate(keys):
            self.button(actions, key, command, index == 0).grid(row=index//2, column=index%2, sticky="ew", padx=(0, 8), pady=3)
        for column in (0, 1):
            actions.columnconfigure(column, weight=1)
        frame = ttk.Frame(self.content)
        frame.grid(row=3, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        columns = ("nombre", "tipo") if profile is None else ("nombre", "tipo", "hours_column")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=3)
        for col in columns:
            self.tree.heading(col, text=self.t(col))
            self.tree.column(col, width=200, minwidth=110)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        command = self.open_selected if profile is None else self.product_details
        self.tree.bind("<Double-1>", lambda e: self.run_action(command))
        self.tree.bind("<Return>", lambda e: self.run_action(command))
        self.refresh()

    def current_profile(self):
        return next((p for p in self.store.profiles() if p["id"] == self.profile_id), None)

    def refresh(self):
        previous = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        rows = self.store.profiles(self.search.get()) if self.screen == "profiles" else self.store.products(self.profile_id, self.search.get())
        self.rows = {str(row["id"]): row for row in rows}
        for key, row in self.rows.items():
            values = [row["nombre"], self.t(row["tipo"])]
            if self.screen == "products":
                values.append(", ".join(row["horarios"]) if row["hora_original"] is None else self.t("review"))
            self.tree.insert("", "end", iid=key, values=values)
        if previous and previous[0] in self.rows:
            self.tree.selection_set(previous[0])
        if not rows:
            self.status.set(self.t("empty"))

    def selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("MediLocal", self.t("select"), parent=self.root)
            return None
        return self.rows[selection[0]]

    def open_selected(self):
        row = self.selected()
        if row:
            self.profile_id = row["id"]
            self.show("products")

    def edit_profile(self):
        row = self.selected()
        if row:
            self.profile_form(row)

    def delete_profile(self):
        row = self.selected()
        if row and messagebox.askyesno(self.t("confirm"), self.t("confirm_profile", name=row["nombre"], count=len(self.store.products(row["id"]))), parent=self.root, default="no"):
            self.store.delete_profile(row["id"])
            self.refresh()
            self.status.set(self.t("deleted"))

    def edit_product(self):
        row = self.selected()
        if row:
            self.product_form(row)

    def delete_product(self):
        row = self.selected()
        if row and messagebox.askyesno(self.t("confirm"), self.t("confirm_product", name=row["nombre"]), parent=self.root, default="no"):
            self.store.delete_product(self.profile_id, row["id"])
            self.refresh()
            self.status.set(self.t("deleted"))

    def dialog(self, title):
        window = tk.Toplevel(self.root)
        window.title(self.t(title))
        window.transient(self.root)
        window.geometry("660x610")
        window.minsize(500, 400)
        window.configure(background=PALETTES[self.settings["theme"]]["bg"])
        window.grab_set()
        window.bind("<Escape>", lambda e: window.destroy())
        # Scrollable forms keep every field/action reachable with enlarged text.
        canvas = tk.Canvas(window, highlightthickness=0, background=PALETTES[self.settings["theme"]]["bg"])
        scroll = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
        scroll.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        canvas.configure(yscrollcommand=scroll.set)
        body = ttk.Frame(canvas, padding=20)
        body.columnconfigure(0, weight=1)
        item = canvas.create_window(0, 0, window=body, anchor="nw")
        def body_changed(event):
            for child in body.winfo_children():
                if isinstance(child, ttk.Label):
                    child.configure(wraplength=max(100, body.winfo_width()-40))
            canvas.configure(scrollregion=canvas.bbox("all"))
        body.bind("<Configure>", body_changed)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(item, width=e.width))
        def reveal(event):
            window.update_idletasks()
            widget = event.widget
            if widget is body or not str(widget).startswith(str(body)):
                return
            top = widget.winfo_rooty() - body.winfo_rooty()
            height = max(body.winfo_height(), 1)
            visible_top = canvas.canvasy(0)
            if top < visible_top or top + widget.winfo_height() > visible_top + canvas.winfo_height():
                canvas.yview_moveto(max(0, top - 20) / height)
        window.bind("<FocusIn>", reveal, add="+")
        return window, body

    def form(self, title, fields, initial, submit, warning=""):
        window, body = self.dialog(title)
        variables, errors, widgets = {}, {}, {}
        rownum = 0
        if warning:
            ttk.Label(body, text=warning, style="Error.TLabel", wraplength=560).grid(row=rownum, column=0, sticky="ew", pady=(0, 12))
            rownum += 1
        for key, choices in fields:
            ttk.Label(body, text=self.t(key)).grid(row=rownum, column=0, sticky="w", pady=(8, 2))
            rownum += 1
            variables[key] = tk.StringVar(value=initial.get(key, ""))
            if choices:
                widget = ttk.Combobox(body, values=[self.t(v) for v in choices], state="readonly", textvariable=variables[key])
                widget.current(choices.index(initial.get(key, choices[0])))
            elif key == "notas":
                c = PALETTES[self.settings["theme"]]
                widget = tk.Text(body, height=4, width=30, wrap="word", font="TkTextFont", background=c["field"], foreground=c["fg"], insertbackground=c["fg"], selectbackground=c["selected"], selectforeground="#FFFFFF", highlightbackground=c["border"], highlightcolor=c["accent"], highlightthickness=2, relief="flat", padx=6, pady=6)
                widget.insert("1.0", initial.get(key, ""))
                def move_focus(event):
                    (event.widget.tk_focusPrev() if event.state & 1 else event.widget.tk_focusNext()).focus_set()
                    return "break"
                widget.bind("<Tab>", move_focus)
                widget.bind("<ISO_Left_Tab>", lambda e: (e.widget.tk_focusPrev().focus_set(), "break")[1])
            else:
                widget = ttk.Entry(body, textvariable=variables[key])
            widgets[key] = widget
            widget.grid(row=rownum, column=0, sticky="ew")
            rownum += 1
            errors[key] = tk.StringVar()
            ttk.Label(body, textvariable=errors[key], style="Error.TLabel", wraplength=560).grid(row=rownum, column=0, sticky="w")
            rownum += 1
        def save():
            for var in errors.values():
                var.set("")
            values = {key: (choices[widgets[key].current()] if choices else widgets[key].get("1.0", "end-1c") if key == "notas" else variables[key].get()) for key, choices in fields}
            try:
                submit(values)
            except ValidationError as error:
                errors[error.field].set(self.t(error.key))
                widgets[error.field].focus_set()
                return
            window.destroy()
            self.refresh()
            self.status.set(self.t("saved"))
        actions = ttk.Frame(body)
        actions.grid(row=rownum, column=0, sticky="w", pady=15)
        self.button(actions, "save", save, True).pack(side="left", padx=(0, 10))
        self.button(actions, "cancel", window.destroy).pack(side="left")
        widgets[fields[0][0]].focus_set()

    def profile_form(self, row=None):
        row = row or {}
        self.form("edit_profile" if row else "new_profile", [("nombre", None), ("tipo", ["Persona", "Mascota"])], row,
                  lambda values: self.store.save_profile(values["nombre"], values["tipo"], row.get("id")))

    def product_form(self, row=None):
        row = row or {}
        initial = {**row, "horarios": ", ".join(row.get("horarios", []))}
        warning = self.t("legacy_warning", hour=row["hora_original"]) if row.get("hora_original") is not None and row else ""
        self.form("edit_product" if row else "add_product", [("tipo", ["Medicamento", "Suplemento"]), ("nombre", None), ("cantidad", None), ("horarios", None), ("notas", None)], initial,
                  lambda v: self.store.save_product(self.profile_id, v["tipo"], v["nombre"], v["cantidad"], v["horarios"], v["notas"], row.get("id")), warning)

    def product_details(self):
        row = self.selected()
        if not row:
            return
        window, body = self.dialog("details")
        for key in ("nombre", "tipo", "cantidad", "hours_column", "notas"):
            value = row.get(key, "")
            if key == "tipo":
                value = self.t(value)
            if key == "hours_column":
                value = self.t("legacy_warning", hour=row["hora_original"]) if row["hora_original"] is not None else ", ".join(row["horarios"])
            ttk.Label(body, text=self.t(key)).pack(anchor="w", pady=(10, 0))
            ttk.Label(body, text=value, wraplength=560).pack(anchor="w")
        self.button(body, "close", window.destroy).pack(anchor="w", pady=20)

    def backup_screen(self):
        ttk.Label(self.content, text=self.t("backups"), style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=12)
        ttk.Label(self.content, text=self.t("backup_info"), wraplength=640).grid(row=1, column=0, sticky="w", pady=8)
        actions = ttk.Frame(self.content)
        actions.grid(row=2, column=0, sticky="w")
        for i, (key, command) in enumerate((("export", self.export), ("restore", self.restore), ("import_legacy", self.import_legacy), ("back", lambda: self.show("profiles")))):
            self.button(actions, key, command).grid(row=i, column=0, sticky="ew", pady=5)
        ttk.Label(self.content, text=self.t("data_location", path=self.store.path.parent), wraplength=640).grid(row=3, column=0, sticky="sw", pady=16)

    def file_options(self):
        return dict(parent=self.root, filetypes=[(self.t("file_type"), "*.db *.sqlite *.sqlite3")])

    def export(self):
        filename = filedialog.asksaveasfilename(title=self.t("export"), defaultextension=".db", initialfile="medilocal-backup.db", **self.file_options())
        if filename:
            self.store.backup(filename)
            self.status.set(self.t("export_done", path=filename))

    def restore(self):
        filename = filedialog.askopenfilename(title=self.t("restore"), **self.file_options())
        if filename and messagebox.askyesno(self.t("restore"), self.t("restore_confirm"), parent=self.root, default="no"):
            safety = self.store.restore(filename)
            self.profile_id = None
            self.status.set(self.t("restore_done", path=safety))

    def import_legacy(self, filename=None):
        filename = filename or filedialog.askopenfilename(title=self.t("import_legacy"), **self.file_options())
        if filename and messagebox.askyesno(self.t("import_legacy"), self.t("import_confirm"), parent=self.root, default="no"):
            count = self.store.import_legacy(filename)
            if self.screen != "backups":
                self.refresh()
            self.status.set(self.t("import_done", count=count))

    def offer_legacy(self):
        self.legacy_timer = None
        if self.store.profiles():
            return
        for path in legacy_candidates():
            if path.is_file() and path.resolve() != self.store.path.resolve():
                if messagebox.askyesno(self.t("import_legacy"), self.t("legacy_detected"), parent=self.root, default="no"):
                    self.run_action(lambda: self.import_legacy(path))
                break
