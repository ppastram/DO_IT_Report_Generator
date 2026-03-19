#!/usr/bin/env python3
"""
DO IT Report Generator — GUI (Tkinter)
Interfaz gráfica para generar infografía PNG + reporte web HTML.
"""

import json
import os
import platform
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Asegurar que el directorio del script sea el CWD
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from generar_reporte import DOITReportGenerator
from netlify_deploy import NetlifyDeployer


class DOITApp:
    """Aplicación principal."""

    # Colores DO IT
    BG_DARK = "#0D2B38"
    TEAL_DARK = "#006A91"
    TEAL_MID = "#0086AC"
    TEAL_LIGHT = "#51C3CA"
    GOLD = "#F9B401"
    WHITE = "#FFFFFF"
    GREY = "#A6A6A6"
    BG_LIGHT = "#EDF6F9"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DO IT — Generador de Reportes")
        self.root.geometry("580x800")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG_DARK)

        # Variables
        self.var_taller = tk.StringVar()
        self.var_duracion = tk.StringVar()
        self.var_lugar = tk.StringVar()
        self.var_instructor2 = tk.StringVar()
        self.var_total_participantes = tk.StringVar()
        self.var_csv = tk.StringVar()
        self.var_logo = tk.StringVar()
        self.var_qr = tk.StringVar()
        self.fotos_paths = []

        # Config vars
        self.var_nombre = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_telefono = tk.StringVar()
        self.var_web = tk.StringVar()

        # Netlify vars
        self.var_netlify_token = tk.StringVar()
        self.var_netlify_site_id = tk.StringVar()
        self.var_netlify_url = tk.StringVar()
        self.last_report_url = None

        self.generator = DOITReportGenerator()
        self._load_config()
        self._build_ui()

    def _load_config(self):
        """Load config values."""
        self.var_nombre.set(self.generator.config.get('gerente_nombre', ''))
        self.var_email.set(self.generator.config.get('gerente_email', ''))
        self.var_telefono.set(self.generator.config.get('gerente_telefono', ''))
        self.var_web.set(self.generator.config.get('gerente_web', ''))

        # Netlify config
        self.var_netlify_token.set(self.generator.config.get('netlify_token', ''))
        self.var_netlify_site_id.set(self.generator.config.get('netlify_site_id', ''))
        self.var_netlify_url.set(self.generator.config.get('netlify_url', ''))

        # Set default paths if files exist
        csv_default = self.generator.entrada_dir / "datos_curso.csv"
        if csv_default.exists():
            self.var_csv.set(str(csv_default))

        logo_default = self.generator.entrada_dir / "logo_cliente.png"
        if logo_default.exists():
            self.var_logo.set(str(logo_default))

        qr_default = self.generator.gerente_dir / "qr_gerente.png"
        if qr_default.exists():
            self.var_qr.set(str(qr_default))

        fotos = sorted(self.generator.fotos_dir.glob("*"))
        self.fotos_paths = [str(f) for f in fotos if f.suffix.lower() in ('.jpg', '.jpeg', '.png')]

    def _build_ui(self):
        """Build the UI."""
        # Notebook (tabs)
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.BG_DARK, borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=self.TEAL_DARK,
                       foreground=self.WHITE,
                       padding=[16, 8],
                       font=('Helvetica', 11, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.TEAL_MID)],
                 foreground=[('selected', self.WHITE)])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Generar Reporte
        tab1 = tk.Frame(notebook, bg=self.BG_DARK)
        notebook.add(tab1, text="  ⚡ Generar Reporte  ")
        self._build_tab_generar(tab1)

        # Tab 2: Configuración
        tab2 = tk.Frame(notebook, bg=self.BG_DARK)
        notebook.add(tab2, text="  ⚙ Configuración  ")
        self._build_tab_config(tab2)

    def _make_label(self, parent, text, **kwargs):
        return tk.Label(parent, text=text, bg=self.BG_DARK, fg=self.TEAL_LIGHT,
                       font=('Helvetica', 10), anchor='w', **kwargs)

    def _make_entry(self, parent, var, **kwargs):
        return tk.Entry(parent, textvariable=var, bg=self.WHITE, fg=self.BG_DARK,
                       font=('Helvetica', 11), relief='flat', bd=0,
                       highlightthickness=1, highlightcolor=self.TEAL_LIGHT,
                       highlightbackground=self.GREY, **kwargs)

    def _make_button(self, parent, text, command, primary=False, **kwargs):
        bg = self.GOLD if primary else self.TEAL_DARK
        fg = self.BG_DARK if primary else self.WHITE
        return tk.Button(parent, text=text, command=command,
                        bg=bg, fg=fg, font=('Helvetica', 10, 'bold'),
                        relief='flat', cursor='hand2', padx=12, pady=6, **kwargs)

    def _build_tab_generar(self, parent):
        """Build the report generation tab."""
        # Scrollable canvas for the form
        canvas = tk.Canvas(parent, bg=self.BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.BG_DARK)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw",
                             tags="scroll_window")

        # Make scroll_frame fill canvas width
        def _resize_scroll_frame(event):
            canvas.itemconfig("scroll_window", width=event.width)
        canvas.bind("<Configure>", _resize_scroll_frame)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120 or (-1 if event.delta < 0 else 1)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        content = scroll_frame

        # Title
        tk.Label(content, text="Generador de Reportes DO IT",
                bg=self.BG_DARK, fg=self.WHITE,
                font=('Helvetica', 16, 'bold')).pack(pady=(20, 5))
        tk.Label(content, text="Infografía PNG + Reporte Web HTML",
                bg=self.BG_DARK, fg=self.TEAL_LIGHT,
                font=('Helvetica', 10)).pack(pady=(0, 20))

        # Form frame
        form = tk.Frame(content, bg=self.BG_DARK)
        form.pack(fill='x', padx=30)

        # Row helper
        row = 0
        def add_field(label, var, browse_type=None):
            nonlocal row
            self._make_label(form, label).grid(row=row, column=0, sticky='w', pady=(10, 2), columnspan=2)
            row += 1
            entry = self._make_entry(form, var)
            entry.grid(row=row, column=0, sticky='ew', ipady=6, padx=(0, 8 if browse_type else 0))
            if browse_type:
                btn = self._make_button(form, "📂", lambda t=browse_type, v=var: self._browse(t, v))
                btn.grid(row=row, column=1, sticky='e')
            row += 1
            return entry

        form.columnconfigure(0, weight=1)

        add_field("Nombre del taller", self.var_taller)
        add_field("Duración (ej: 8 horas)", self.var_duracion)
        add_field("Lugar", self.var_lugar)
        add_field("Segundo instructor/a (opcional)", self.var_instructor2)
        add_field("Archivo CSV (Fillout)", self.var_csv, 'csv')
        add_field("Total participantes (opcional — por defecto usa el # de evaluaciones)", self.var_total_participantes)
        add_field("Logo del cliente", self.var_logo, 'image')

        # Fotos
        self._make_label(form, "Fotos del curso (máx 4)").grid(
            row=row, column=0, sticky='w', pady=(10, 2), columnspan=2)
        row += 1
        fotos_frame = tk.Frame(form, bg=self.BG_DARK)
        fotos_frame.grid(row=row, column=0, sticky='ew', columnspan=2)
        self.fotos_label = tk.Label(fotos_frame,
                                    text=f"{len(self.fotos_paths)} foto(s) seleccionadas" if self.fotos_paths else "Ninguna foto",
                                    bg=self.BG_DARK, fg=self.GREY, font=('Helvetica', 9))
        self.fotos_label.pack(side='left')
        self._make_button(fotos_frame, "📂 Seleccionar", self._browse_fotos).pack(side='right')
        row += 1

        # QR
        add_field("Imagen QR del gerente", self.var_qr, 'image')

        # Generate button
        self.btn_generate = self._make_button(content, "⚡  GENERAR REPORTE",
                                              self._generate, primary=True)
        self.btn_generate.configure(font=('Helvetica', 14, 'bold'), padx=30, pady=12)
        self.btn_generate.pack(pady=25)

        # Progress
        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(content, variable=self.progress_var,
                                        maximum=100, length=400)
        self.progress.pack(pady=(0, 5))

        self.status_label = tk.Label(content, text="", bg=self.BG_DARK,
                                     fg=self.TEAL_LIGHT, font=('Helvetica', 10))
        self.status_label.pack()

        # Open buttons (hidden initially)
        self.open_frame = tk.Frame(content, bg=self.BG_DARK)
        self.open_frame.pack(pady=10)

    def _build_tab_config(self, parent):
        """Build configuration tab."""
        # Scrollable canvas for longer config
        canvas = tk.Canvas(parent, bg=self.BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.BG_DARK)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Agent section
        tk.Label(scroll_frame, text="Datos del gerente comercial",
                bg=self.BG_DARK, fg=self.WHITE,
                font=('Helvetica', 14, 'bold')).pack(pady=(20, 10), padx=30, anchor='w')

        form1 = tk.Frame(scroll_frame, bg=self.BG_DARK)
        form1.pack(fill='x', padx=30)
        form1.columnconfigure(0, weight=1)

        row = 0
        for label, var in [("Nombre", self.var_nombre), ("Email", self.var_email),
                           ("Teléfono", self.var_telefono), ("Web", self.var_web)]:
            self._make_label(form1, label).grid(row=row, column=0, sticky='w', pady=(8, 2))
            row += 1
            self._make_entry(form1, var).grid(row=row, column=0, sticky='ew', ipady=5)
            row += 1

        # Separator
        sep = tk.Frame(scroll_frame, bg=self.TEAL_DARK, height=1)
        sep.pack(fill='x', padx=30, pady=20)

        # Netlify section
        tk.Label(scroll_frame, text="🌐  Netlify (subir reportes web)",
                bg=self.BG_DARK, fg=self.WHITE,
                font=('Helvetica', 14, 'bold')).pack(pady=(0, 5), padx=30, anchor='w')
        tk.Label(scroll_frame, text="Los reportes HTML se suben automáticamente y obtienes un link único por cliente.",
                bg=self.BG_DARK, fg=self.GREY,
                font=('Helvetica', 9), wraplength=480, justify='left').pack(padx=30, anchor='w')

        form2 = tk.Frame(scroll_frame, bg=self.BG_DARK)
        form2.pack(fill='x', padx=30)
        form2.columnconfigure(0, weight=1)

        row = 0
        self._make_label(form2, "Token de Netlify").grid(row=row, column=0, sticky='w', pady=(8, 2))
        row += 1
        self._make_entry(form2, self.var_netlify_token).grid(row=row, column=0, sticky='ew', ipady=5)
        row += 1

        self._make_label(form2, "Site ID (se llena automático)").grid(row=row, column=0, sticky='w', pady=(8, 2))
        row += 1
        self._make_entry(form2, self.var_netlify_site_id).grid(row=row, column=0, sticky='ew', ipady=5)
        row += 1

        self.netlify_status = tk.Label(form2, text="", bg=self.BG_DARK, fg=self.TEAL_LIGHT,
                                        font=('Helvetica', 9))
        self.netlify_status.grid(row=row, column=0, sticky='w', pady=(4, 0))
        if self.var_netlify_url.get():
            self.netlify_status.config(text=f"✅ Sitio: {self.var_netlify_url.get()}", fg=self.GOLD)
        row += 1

        # Netlify setup instructions
        instructions = tk.Frame(scroll_frame, bg="#0A2230")
        instructions.pack(fill='x', padx=30, pady=(10, 0))
        tk.Label(instructions, text="Configuración inicial (solo una vez):",
                bg="#0A2230", fg=self.TEAL_LIGHT,
                font=('Helvetica', 10, 'bold')).pack(anchor='w', padx=12, pady=(8, 4))
        for step in [
            "1. Crea cuenta gratis en netlify.com",
            "2. Ve a: app.netlify.com/user/applications",
            "3. En 'Personal access tokens' → New access token",
            "4. Copia el token y pégalo arriba",
            "5. Guarda. El sitio se crea automáticamente al generar el primer reporte."
        ]:
            tk.Label(instructions, text=step, bg="#0A2230", fg=self.GREY,
                    font=('Helvetica', 9)).pack(anchor='w', padx=20, pady=1)
        tk.Label(instructions, text="", bg="#0A2230").pack(pady=4)

        # Save button
        self._make_button(scroll_frame, "💾  Guardar configuración",
                         self._save_config, primary=True).pack(pady=20)

    def _browse(self, browse_type, var):
        """File browser."""
        if browse_type == 'csv':
            path = filedialog.askopenfilename(
                filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        elif browse_type == 'image':
            path = filedialog.askopenfilename(
                filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")])
        else:
            path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _browse_fotos(self):
        """Browse for multiple photos."""
        paths = filedialog.askopenfilenames(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")])
        if paths:
            self.fotos_paths = list(paths[:4])
            self.fotos_label.config(text=f"{len(self.fotos_paths)} foto(s) seleccionadas")

    def _save_config(self):
        """Save agent + Netlify config."""
        config = {
            "gerente_nombre": self.var_nombre.get(),
            "gerente_email": self.var_email.get(),
            "gerente_telefono": self.var_telefono.get(),
            "gerente_web": self.var_web.get(),
            "netlify_token": self.var_netlify_token.get(),
            "netlify_site_id": self.var_netlify_site_id.get(),
            "netlify_url": self.var_netlify_url.get(),
        }
        config_path = self.generator.base_dir / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.generator.config = config
        messagebox.showinfo("Guardado", "Configuración guardada correctamente.")

    def _generate(self):
        """Start report generation in a thread."""
        # Validate
        if not self.var_taller.get().strip():
            messagebox.showwarning("Campo requerido", "Ingresa el nombre del taller.")
            return
        if not self.var_csv.get().strip() or not os.path.exists(self.var_csv.get()):
            messagebox.showwarning("Campo requerido", "Selecciona un archivo CSV válido.")
            return

        self.btn_generate.config(state='disabled', text="Generando...")
        self.progress_var.set(0)
        self.status_label.config(text="Procesando CSV...")

        # Clear previous open buttons
        for w in self.open_frame.winfo_children():
            w.destroy()

        def run():
            try:
                # Parse CSV
                data = self.generator.parse_csv(self.var_csv.get())

                # Update config with current values
                self.generator.config = {
                    "gerente_nombre": self.var_nombre.get(),
                    "gerente_email": self.var_email.get(),
                    "gerente_telefono": self.var_telefono.get(),
                    "gerente_web": self.var_web.get()
                }

                # Optional: segundo instructor
                instructor2 = self.var_instructor2.get().strip() or None

                # Optional: total participantes
                try:
                    total_participantes = int(self.var_total_participantes.get().strip())
                    if total_participantes <= 0:
                        total_participantes = None
                except (ValueError, AttributeError):
                    total_participantes = None

                def update_progress(p):
                    self.root.after(0, lambda: self.progress_var.set(int(p * 0.4)))

                # Generate PNG
                self.root.after(0, lambda: self.status_label.config(text="Generando infografía PNG..."))
                png_path = self.generator.generate_png(
                    data,
                    self.var_taller.get().strip(),
                    self.var_duracion.get().strip() or "—",
                    self.var_lugar.get().strip() or "—",
                    logo_cliente_path=self.var_logo.get() if self.var_logo.get() else None,
                    qr_path=self.var_qr.get() if self.var_qr.get() else None,
                    progress_callback=update_progress,
                    instructor2=instructor2,
                    total_participantes=total_participantes
                )

                # Generate HTML
                def update_progress_html(p):
                    self.root.after(0, lambda: self.progress_var.set(40 + int(p * 0.3)))

                self.root.after(0, lambda: self.status_label.config(text="Generando reporte web HTML..."))
                html_path = self.generator.generate_html(
                    data,
                    self.var_taller.get().strip(),
                    self.var_duracion.get().strip() or "—",
                    self.var_lugar.get().strip() or "—",
                    fotos_paths=self.fotos_paths if self.fotos_paths else None,
                    progress_callback=update_progress_html,
                    instructor2=instructor2,
                    total_participantes=total_participantes,
                    logo_cliente_path=self.var_logo.get() if self.var_logo.get() else None,
                    qr_path=self.var_qr.get() if self.var_qr.get() else None
                )

                # Deploy to Netlify if configured
                report_url = None
                netlify_token = self.var_netlify_token.get().strip()
                if netlify_token:
                    self.root.after(0, lambda: self.status_label.config(text="Subiendo reporte a Netlify..."))
                    self.root.after(0, lambda: self.progress_var.set(75))

                    try:
                        site_id = self.var_netlify_site_id.get().strip()
                        deployer = NetlifyDeployer(netlify_token, site_id or None)

                        # Create site if first time
                        if not site_id:
                            self.root.after(0, lambda: self.status_label.config(text="Creando sitio en Netlify..."))
                            site_info = deployer.create_site("doit-reportes")
                            site_id = site_info['site_id']
                            # Save site_id to config
                            self.var_netlify_site_id.set(site_id)
                            self.var_netlify_url.set(site_info['url'])
                            self.root.after(0, lambda: self._save_config_silent())

                        # Generate unique filename
                        html_filename = os.path.basename(html_path)

                        def update_progress_deploy(p):
                            self.root.after(0, lambda: self.progress_var.set(75 + int(p * 0.25)))

                        result = deployer.deploy(
                            {f"/{html_filename}": html_path},
                            progress_callback=update_progress_deploy
                        )
                        report_url = result['file_urls'].get(f"/{html_filename}")

                    except Exception as ne:
                        # Netlify error is non-fatal, report still generated locally
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"⚠️ Reporte generado, pero error Netlify: {str(ne)[:60]}", fg="#FF9500"))

                # Done
                self.root.after(0, lambda: self._on_done(png_path, html_path, report_url))

            except Exception as e:
                self.root.after(0, lambda: self._on_error(str(e)))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _save_config_silent(self):
        """Save config without showing a dialog."""
        config = {
            "gerente_nombre": self.var_nombre.get(),
            "gerente_email": self.var_email.get(),
            "gerente_telefono": self.var_telefono.get(),
            "gerente_web": self.var_web.get(),
            "netlify_token": self.var_netlify_token.get(),
            "netlify_site_id": self.var_netlify_site_id.get(),
            "netlify_url": self.var_netlify_url.get(),
        }
        config_path = self.generator.base_dir / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.generator.config = config

    def _on_done(self, png_path, html_path, report_url=None):
        """Called when generation completes."""
        self.progress_var.set(100)
        self.btn_generate.config(state='normal', text="⚡  GENERAR REPORTE")
        self.last_report_url = report_url

        if report_url:
            self.status_label.config(text="✅ ¡Reporte generado y subido a Netlify!", fg=self.GOLD)
        else:
            self.status_label.config(text="✅ ¡Reporte generado con éxito!", fg=self.GOLD)

        # Open buttons (black text on teal background)
        for btn_text, btn_cmd in [
            ("📄 Abrir PNG", lambda: self._open_file(png_path)),
            ("🌐 Abrir HTML", lambda: self._open_file(html_path)),
            ("📂 Carpeta", lambda: self._open_file(os.path.dirname(png_path))),
        ]:
            btn = self._make_button(self.open_frame, btn_text, btn_cmd)
            btn.configure(fg="#000000")
            btn.pack(side='left', padx=5)

        if report_url:
            self._make_button(self.open_frame, "📋 Copiar URL",
                             lambda: self._copy_url(report_url), primary=True).pack(side='left', padx=5)

        # Show file paths
        paths_frame = tk.Frame(self.open_frame.master, bg=self.BG_DARK)
        paths_frame.pack(fill='x', padx=30, pady=(8, 0))

        png_name = os.path.basename(png_path)
        html_name = os.path.basename(html_path)
        tk.Label(paths_frame, text=f"📄 PNG: {png_name}",
                bg=self.BG_DARK, fg=self.TEAL_LIGHT,
                font=('Helvetica', 9), anchor='w').pack(fill='x')
        tk.Label(paths_frame, text=f"🌐 HTML: {html_name}",
                bg=self.BG_DARK, fg=self.TEAL_LIGHT,
                font=('Helvetica', 9), anchor='w').pack(fill='x')

        if report_url:
            url_row = tk.Frame(paths_frame, bg=self.BG_DARK)
            url_row.pack(fill='x', pady=(2, 0))
            tk.Label(url_row, text="🔗 URL:",
                    bg=self.BG_DARK, fg=self.TEAL_LIGHT,
                    font=('Helvetica', 9)).pack(side='left')
            tk.Label(url_row, text=report_url,
                    bg=self.BG_DARK, fg=self.GOLD,
                    font=('Helvetica', 9, 'bold'), cursor='hand2').pack(side='left', padx=4)

    def _copy_url(self, url):
        """Copy URL to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.root.update()
        messagebox.showinfo("Copiado", f"URL copiada al portapapeles:\n\n{url}")

    def _on_error(self, error_msg):
        """Called on generation error."""
        self.btn_generate.config(state='normal', text="⚡  GENERAR REPORTE")
        self.status_label.config(text=f"❌ Error: {error_msg}", fg="#FF6B6B")
        messagebox.showerror("Error", f"Error al generar el reporte:\n\n{error_msg}")

    def _open_file(self, path):
        """Open file with default system application."""
        try:
            if platform.system() == 'Darwin':
                subprocess.Popen(['open', path])
            elif platform.system() == 'Windows':
                os.startfile(path)
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            messagebox.showwarning("Error", f"No se pudo abrir: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = DOITApp()
    app.run()
