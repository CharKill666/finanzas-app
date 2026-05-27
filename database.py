
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FinanzasAvanzado:
    def __init__(self, root):
        self.root = root
        self.root.title("Finanzas Personales - Dashboard Completo")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Base de datos
        self.conn = sqlite3.connect('finanzas.db')
        self.cursor = self.conn.cursor()
        self.crear_tablas()
        
        # Configuración de moneda (por defecto pesos)
        self.moneda = tk.StringVar(value="COP")  # COP o USD
        self.simbolo_moneda = {"COP": "$", "USD": "US$"}
        
        # Cargar configuración de categorías y reglas
        self.cargar_configuracion()
        
        # Variables del formulario
        self.fecha = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        self.concepto = tk.StringVar()
        self.categoria = tk.StringVar()
        self.monto = tk.StringVar()
        self.tipo = tk.StringVar(value="gasto")
        
        # Construir interfaz
        self.construir_interfaz()
        self.actualizar_todo()
        
    def crear_tablas(self):
        # Tabla de transacciones
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            concepto TEXT,
            categoria TEXT,
            monto REAL,
            tipo TEXT,
            moneda TEXT DEFAULT 'COP'
        )''')
        # Tabla de categorías personalizables
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (
            nombre TEXT PRIMARY KEY,
            tipo TEXT,
            es_gasto INTEGER,
            presupuesto_mensual REAL,
            palabras_clave TEXT
        )''')
        # Tabla de reglas de ahorro automático
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS reglas_ahorro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            tipo_regla TEXT,
            activa INTEGER,
            parametros TEXT
        )''')
        # Tabla de deudas
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS deudas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            monto_inicial REAL,
            tasa_interes_anual REAL,
            cuota_mensual REAL,
            fecha_inicio TEXT,
            saldo_restante REAL,
            activa INTEGER
        )''')
        # Tabla de ahorros automáticos
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ahorros_automaticos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            concepto TEXT,
            monto REAL
        )''')
        self.conn.commit()
        
        # Insertar categorías por defecto (incluye Educación)
        categorias_defecto = [
            ("Comida", "gasto", 1, 300.0, "supermercado, restaurante, comida, cena, almuerzo"),
            ("Transporte", "gasto", 1, 150.0, "taxi, bus, metro, gasolina, uber"),
            ("Ocio", "gasto", 1, 100.0, "cine, juego, bar, concierto"),
            ("Vivienda", "gasto", 1, 800.0, "alquiler, hipoteca, luz, agua, gas"),
            ("Educación", "gasto", 1, 200.0, "colegio, universidad, curso, libro, matrícula, capacitación"),
            ("Salario", "ingreso", 0, 0.0, "sueldo, nomina, salario"),
            ("Inversiones", "ingreso", 0, 0.0, "dividendo, ganancia"),
        ]
        for cat in categorias_defecto:
            self.cursor.execute("INSERT OR IGNORE INTO categorias (nombre, tipo, es_gasto, presupuesto_mensual, palabras_clave) VALUES (?,?,?,?,?)", cat)
        self.conn.commit()
        
        # Insertar reglas de ahorro por defecto
        self.cursor.execute("SELECT COUNT(*) FROM reglas_ahorro")
        if self.cursor.fetchone()[0] == 0:
            reglas = [
                ("Redondeo diario", "redondeo", 1, json.dumps({"redondeo_a": 1.0})),
                ("Ahorro 5% de ingresos", "porcentaje_ingreso", 1, json.dumps({"porcentaje": 5.0})),
                ("Ahorro semanal fijo", "periodico", 0, json.dumps({"monto_fijo": 10.0, "periodicidad": "semanal"}))
            ]
            for regla in reglas:
                self.cursor.execute("INSERT INTO reglas_ahorro (nombre, tipo_regla, activa, parametros) VALUES (?,?,?,?)", regla)
            self.conn.commit()
    
    def cargar_configuracion(self):
        self.cursor.execute("SELECT nombre FROM categorias WHERE es_gasto=1 ORDER BY nombre")
        self.categorias_gasto = [row[0] for row in self.cursor.fetchall()]
        self.cursor.execute("SELECT nombre FROM categorias WHERE es_gasto=0 ORDER BY nombre")
        self.categorias_ingreso = [row[0] for row in self.cursor.fetchall()]
    
    def construir_interfaz(self):
        # Barra superior con selector de moneda
        toolbar = tk.Frame(self.root, bg='#e0e0e0', height=40)
        toolbar.pack(fill='x', side='top')
        tk.Label(toolbar, text="Moneda:", bg='#e0e0e0').pack(side='left', padx=5)
        moneda_combo = ttk.Combobox(toolbar, textvariable=self.moneda, values=["COP", "USD"], width=5, state='readonly')
        moneda_combo.pack(side='left', padx=5)
        moneda_combo.bind('<<ComboboxSelected>>', lambda e: self.actualizar_todo())
        
        # Panel principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Panel izquierdo: formulario y config
        frame_izq = tk.Frame(main_frame, bg='#f0f0f0', width=350)
        frame_izq.pack(side='left', fill='y', padx=5)
        
        # Formulario nueva transacción
        frame_form = tk.LabelFrame(frame_izq, text="Nueva Transacción", bg='#f0f0f0', font=('Arial', 12, 'bold'))
        frame_form.pack(fill='x', pady=5)
        
        labels = ["Fecha (YYYY-MM-DD):", "Concepto:", "Categoría:", "Monto:"]
        vars_ = [self.fecha, self.concepto, self.categoria, self.monto]
        for i, (lab, var) in enumerate(zip(labels, vars_)):
            tk.Label(frame_form, text=lab, bg='#f0f0f0').grid(row=i, column=0, sticky='w', padx=5, pady=5)
            if lab == "Categoría:":
                self.combo_categoria = ttk.Combobox(frame_form, textvariable=var, values=self.categorias_gasto, width=20)
                self.combo_categoria.grid(row=i, column=1, padx=5, pady=5)
            else:
                tk.Entry(frame_form, textvariable=var, width=22).grid(row=i, column=1, padx=5, pady=5)
        
        # Tipo ingreso/gasto
        tk.Label(frame_form, text="Tipo:", bg='#f0f0f0').grid(row=4, column=0, sticky='w', padx=5, pady=5)
        frame_tipo = tk.Frame(frame_form, bg='#f0f0f0')
        frame_tipo.grid(row=4, column=1, sticky='w')
        tk.Radiobutton(frame_tipo, text="Gasto", variable=self.tipo, value="gasto", bg='#f0f0f0', command=self.actualizar_categorias).pack(side='left')
        tk.Radiobutton(frame_tipo, text="Ingreso", variable=self.tipo, value="ingreso", bg='#f0f0f0', command=self.actualizar_categorias).pack(side='left')
        
        tk.Button(frame_form, text="Agregar Transacción", command=self.agregar_transaccion, bg='#4CAF50', fg='white').grid(row=5, column=0, columnspan=2, pady=10)
        
        # Panel de administración
        frame_admin = tk.LabelFrame(frame_izq, text="Configuración", bg='#f0f0f0', font=('Arial', 10, 'bold'))
        frame_admin.pack(fill='x', pady=5)
        tk.Button(frame_admin, text="Gestionar Categorías", command=self.gestionar_categorias, bg='#FFC107').pack(fill='x', pady=2)
        tk.Button(frame_admin, text="Reglas de Ahorro", command=self.gestionar_reglas_ahorro, bg='#FFC107').pack(fill='x', pady=2)
        tk.Button(frame_admin, text="Presupuestos por Categoría", command=self.gestionar_presupuestos, bg='#FFC107').pack(fill='x', pady=2)
        tk.Button(frame_admin, text="Gestionar Deudas", command=self.gestionar_deudas, bg='#FFC107').pack(fill='x', pady=2)
        
        # Panel derecho: pestañas de resultados
        frame_der = tk.Frame(main_frame, bg='#f0f0f0')
        frame_der.pack(side='right', fill='both', expand=True, padx=5)
        
        notebook = ttk.Notebook(frame_der)
        notebook.pack(fill='both', expand=True)
        
        # Pestaña 1: Listado de transacciones
        tab_listado = ttk.Frame(notebook)
        notebook.add(tab_listado, text="Historial")
        self.construir_tab_listado(tab_listado)
        
        # Pestaña 2: Tablas y estadísticas
        tab_estadisticas = ttk.Frame(notebook)
        notebook.add(tab_estadisticas, text="Estadísticas")
        self.construir_tab_estadisticas(tab_estadisticas)
        
        # Pestaña 3: Gráficos
        tab_graficos = ttk.Frame(notebook)
        notebook.add(tab_graficos, text="Gráficos")
        self.construir_tab_graficos(tab_graficos)
        
    def construir_tab_listado(self, parent):
        frame = tk.Frame(parent)
        frame.pack(fill='both', expand=True)
        
        # Tabla
        scroll_y = tk.Scrollbar(frame)
        scroll_y.pack(side='right', fill='y')
        self.tree = ttk.Treeview(frame, columns=('fecha','concepto','categoria','monto','tipo'), show='headings', yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)
        for col in self.tree['columns']:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=120)
        self.tree.pack(fill='both', expand=True)
        
        tk.Button(frame, text="Eliminar Seleccionada", command=self.eliminar_transaccion, bg='#f44336', fg='white').pack(pady=5)
        tk.Button(frame, text="Exportar CSV", command=self.exportar_csv, bg='#9C27B0', fg='white').pack(pady=5)
    
    def construir_tab_estadisticas(self, parent):
        # Frame con scroll para las estadísticas
        canvas = tk.Canvas(parent)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Labels donde se mostrarán las estadísticas
        self.lbl_resumen_mensual = tk.Label(scrollable_frame, text="", font=('Arial', 10), justify='left', anchor='w', bg='white', relief='ridge')
        self.lbl_resumen_mensual.pack(fill='x', padx=5, pady=5)
        
        self.lbl_top_gastos = tk.Label(scrollable_frame, text="", font=('Arial', 10), justify='left', anchor='w', bg='white', relief='ridge')
        self.lbl_top_gastos.pack(fill='x', padx=5, pady=5)
        
        self.lbl_evolucion = tk.Label(scrollable_frame, text="", font=('Arial', 10), justify='left', anchor='w', bg='white', relief='ridge')
        self.lbl_evolucion.pack(fill='x', padx=5, pady=5)
        
        self.lbl_ahorros = tk.Label(scrollable_frame, text="", font=('Arial', 10), justify='left', anchor='w', bg='white', relief='ridge')
        self.lbl_ahorros.pack(fill='x', padx=5, pady=5)
    
    def construir_tab_graficos(self, parent):
        frame = tk.Frame(parent)
        frame.pack(fill='both', expand=True)
        self.btn_grafico = tk.Button(frame, text="Actualizar Gráficos", command=self.mostrar_graficos, bg='#2196F3', fg='white')
        self.btn_grafico.pack(pady=5)
        self.frame_grafico = tk.Frame(frame)
        self.frame_grafico.pack(fill='both', expand=True)
    
    def actualizar_categorias(self):
        if self.tipo.get() == "gasto":
            self.combo_categoria['values'] = self.categorias_gasto
        else:
            self.combo_categoria['values'] = self.categorias_ingreso
        if self.combo_categoria['values']:
            self.categoria.set(self.combo_categoria['values'][0])
    
    def agregar_transaccion(self):
        fecha = self.fecha.get().strip()
        concepto = self.concepto.get().strip()
        categoria = self.categoria.get().strip()
        monto_str = self.monto.get().strip()
        tipo = self.tipo.get()
        moneda = self.moneda.get()
        if not concepto or not categoria or not monto_str:
            messagebox.showwarning("Faltan datos", "Completa todos los campos")
            return
        try:
            monto = float(monto_str)
            if monto <= 0: raise ValueError
        except:
            messagebox.showwarning("Monto inválido", "Monto debe ser número positivo")
            return
        
        self.cursor.execute("INSERT INTO transacciones (fecha, concepto, categoria, monto, tipo, moneda) VALUES (?,?,?,?,?,?)",
                            (fecha, concepto, categoria, monto, tipo, moneda))
        self.conn.commit()
        self.aplicar_reglas_ahorro(tipo, monto, concepto)
        self.concepto.set("")
        self.monto.set("")
        self.actualizar_todo()
    
    def aplicar_reglas_ahorro(self, tipo, monto, concepto):
        self.cursor.execute("SELECT id, tipo_regla, parametros FROM reglas_ahorro WHERE activa=1")
        reglas = self.cursor.fetchall()
        ahorro_generado = 0.0
        for reg_id, tipo_regla, params_json in reglas:
            params = json.loads(params_json)
            if tipo_regla == "redondeo" and tipo == "gasto":
                redondeo_a = params.get("redondeo_a", 1.0)
                redondeado = ((monto + redondeo_a - 1) // redondeo_a) * redondeo_a
                diferencia = redondeado - monto
                if diferencia > 0:
                    ahorro_generado += diferencia
                    self.registrar_ahorro_automatico(f"Redondeo de {concepto}", diferencia)
            elif tipo_regla == "porcentaje_ingreso" and tipo == "ingreso":
                porcentaje = params.get("porcentaje", 5.0)
                ahorro = monto * porcentaje / 100.0
                ahorro_generado += ahorro
                self.registrar_ahorro_automatico(f"Ahorro {porcentaje}% de ingreso", ahorro)
        if ahorro_generado > 0:
            messagebox.showinfo("Ahorro automático", f"Se ha ahorrado {self.formatear_moneda(ahorro_generado)} automáticamente.")
    
    def registrar_ahorro_automatico(self, concepto, monto):
        self.cursor.execute("INSERT INTO ahorros_automaticos (fecha, concepto, monto) VALUES (?,?,?)",
                            (datetime.today().strftime('%Y-%m-%d'), concepto, monto))
        self.conn.commit()
    
    def formatear_moneda(self, cantidad):
        simb = self.simbolo_moneda.get(self.moneda.get(), "$")
        return f"{simb}{cantidad:,.2f}"
    
    def actualizar_todo(self):
        self.actualizar_listado()
        self.actualizar_estadisticas()
        self.actualizar_graficos()
        self.actualizar_presupuestos_alerta()
    
    def actualizar_listado(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        moneda_actual = self.moneda.get()
        self.cursor.execute("SELECT id, fecha, concepto, categoria, monto, tipo, moneda FROM transacciones ORDER BY fecha DESC")
        for row in self.cursor.fetchall():
            id_, fecha, concepto, categoria, monto, tipo, moneda = row
            if moneda != moneda_actual:
                # Aquí se podría aplicar conversión, pero por simplicidad mostramos ambas
                monto_str = f"{self.formatear_moneda(monto)} ({moneda})"
            else:
                monto_str = self.formatear_moneda(monto)
            self.tree.insert('', 'end', values=(fecha, concepto, categoria, monto_str, tipo), tags=(id_,))
    
    def actualizar_estadisticas(self):
        moneda_actual = self.moneda.get()
        # Resumen del mes actual
        mes_actual = datetime.today().strftime('%Y-%m')
        self.cursor.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='ingreso' AND strftime('%Y-%m', fecha)=? AND moneda=?", (mes_actual, moneda_actual))
        ingresos_mes = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='gasto' AND strftime('%Y-%m', fecha)=? AND moneda=?", (mes_actual, moneda_actual))
        gastos_mes = self.cursor.fetchone()[0] or 0
        balance_mes = ingresos_mes - gastos_mes
        
        texto_resumen = f"📊 RESUMEN DEL MES ({mes_actual})\n"
        texto_resumen += f"Ingresos: {self.formatear_moneda(ingresos_mes)}\n"
        texto_resumen += f"Gastos: {self.formatear_moneda(gastos_mes)}\n"
        texto_resumen += f"Balance: {self.formatear_moneda(balance_mes)}\n"
        self.lbl_resumen_mensual.config(text=texto_resumen)
        
        # Top 5 categorías de gasto del mes
        self.cursor.execute("SELECT categoria, SUM(monto) FROM transacciones WHERE tipo='gasto' AND strftime('%Y-%m', fecha)=? AND moneda=? GROUP BY categoria ORDER BY SUM(monto) DESC LIMIT 5", (mes_actual, moneda_actual))
        top = self.cursor.fetchall()
        texto_top = "🔥 TOP 5 GASTOS DEL MES\n"
        for i, (cat, monto) in enumerate(top, 1):
            texto_top += f"{i}. {cat}: {self.formatear_moneda(monto)}\n"
        self.lbl_top_gastos.config(text=texto_top)
        
        # Evolución últimos 3 meses (ingresos vs gastos)
        texto_evo = "📈 EVOLUCIÓN (últimos 3 meses)\n"
        for i in range(3):
            fecha = datetime.today() - timedelta(days=30*i)
            mes = fecha.strftime('%Y-%m')
            self.cursor.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='ingreso' AND strftime('%Y-%m', fecha)=? AND moneda=?", (mes, moneda_actual))
            ing = self.cursor.fetchone()[0] or 0
            self.cursor.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='gasto' AND strftime('%Y-%m', fecha)=? AND moneda=?", (mes, moneda_actual))
            gas = self.cursor.fetchone()[0] or 0
            texto_evo += f"{mes}: +{self.formatear_moneda(ing)} / -{self.formatear_moneda(gas)} = {self.formatear_moneda(ing-gas)}\n"
        self.lbl_evolucion.config(text=texto_evo)
        
        # Ahorros acumulados
        self.cursor.execute("SELECT SUM(monto) FROM ahorros_automaticos")
        ahorros = self.cursor.fetchone()[0] or 0
        self.lbl_ahorros.config(text=f"💰 AHORROS AUTOMÁTICOS ACUMULADOS: {self.formatear_moneda(ahorros)}")
    
    def actualizar_graficos(self):
        # Limpiar frame anterior
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
        self.mostrar_graficos_en_frame(self.frame_grafico)
    
    def mostrar_graficos_en_frame(self, parent):
        moneda_actual = self.moneda.get()
        # Datos de gastos por categoría (últimos 30 días)
        self.cursor.execute("SELECT categoria, SUM(monto) FROM transacciones WHERE tipo='gasto' AND moneda=? GROUP BY categoria", (moneda_actual,))
        datos = self.cursor.fetchall()
        if not datos:
            tk.Label(parent, text="No hay datos de gastos para mostrar").pack()
            return
        
        categorias = [d[0] for d in datos]
        montos = [d[1] for d in datos]
        
        fig, (ax1, ax2) = plt.subplots(1,2, figsize=(10,5))
        ax1.pie(montos, labels=categorias, autopct='%1.1f%%')
        ax1.set_title("Distribución de Gastos")
        
        # Evolución últimos 6 meses
        meses = []
        ingresos_mes = []
        gastos_mes = []
        for i in range(6):
            fecha = datetime.today() - timedelta(days=30*i)
            mes_str = fecha.strftime('%Y-%m')
            meses.append(mes_str)
            self.cursor.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='ingreso' AND strftime('%Y-%m', fecha)=? AND moneda=?", (mes_str, moneda_actual))
            ing = self.cursor.fetchone()[0] or 0
            self.cursor.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='gasto' AND strftime('%Y-%m', fecha)=? AND moneda=?", (mes_str, moneda_actual))
            gas = self.cursor.fetchone()[0] or 0
            ingresos_mes.append(ing)
            gastos_mes.append(gas)
        meses.reverse()
        ingresos_mes.reverse()
        gastos_mes.reverse()
        
        ax2.plot(meses, ingresos_mes, marker='o', label='Ingresos')
        ax2.plot(meses, gastos_mes, marker='o', label='Gastos')
        ax2.set_title("Evolución mensual")
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def mostrar_graficos(self):
        # Si se llama desde el botón, abrir ventana nueva
        ventana = tk.Toplevel(self.root)
        ventana.title("Gráficos Financieros")
        ventana.geometry("900x600")
        self.mostrar_graficos_en_frame(ventana)
    
    def actualizar_presupuestos_alerta(self):
        mes_actual = datetime.today().strftime('%Y-%m')
        moneda_actual = self.moneda.get()
        self.cursor.execute("SELECT nombre, presupuesto_mensual FROM categorias WHERE es_gasto=1 AND presupuesto_mensual>0")
        for cat, presu in self.cursor.fetchall():
            self.cursor.execute("SELECT SUM(monto) FROM transacciones WHERE categoria=? AND tipo='gasto' AND strftime('%Y-%m', fecha)=? AND moneda=?", (cat, mes_actual, moneda_actual))
            gastado = self.cursor.fetchone()[0] or 0
            if gastado > presu:
                messagebox.showwarning("Presupuesto excedido", f"Has superado el presupuesto de {cat} ({self.formatear_moneda(gastado)} de {self.formatear_moneda(presu)})")
    
    def eliminar_transaccion(self):
        selec = self.tree.selection()
        if not selec: return
        id_ = self.tree.item(selec[0], 'tags')[0]
        if messagebox.askyesno("Confirmar", "¿Eliminar transacción?"):
            self.cursor.execute("DELETE FROM transacciones WHERE id=?", (id_,))
            self.conn.commit()
            self.actualizar_todo()
    
    def exportar_csv(self):
        import csv
        with open('finanzas_export.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['fecha','concepto','categoria','monto','tipo','moneda'])
            self.cursor.execute("SELECT fecha, concepto, categoria, monto, tipo, moneda FROM transacciones ORDER BY fecha")
            writer.writerows(self.cursor.fetchall())
        messagebox.showinfo("Exportado", "Datos guardados en finanzas_export.csv")
    
    # Funciones de gestión (categorías, reglas, presupuestos, deudas) se mantienen similares
    # pero las incluyo resumidas para no alargar. Sin embargo, para que el código funcione completamente,
    # mantendré las versiones previas ligeramente adaptadas.
    
    def gestionar_categorias(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Administrar Categorías")
        ventana.geometry("600x400")
        tree = ttk.Treeview(ventana, columns=('nombre','tipo','presupuesto'), show='headings')
        tree.heading('nombre', text='Categoría')
        tree.heading('tipo', text='Tipo')
        tree.heading('presupuesto', text='Presupuesto (gastos)')
        tree.pack(fill='both', expand=True)
        self.cursor.execute("SELECT nombre, tipo, presupuesto_mensual FROM categorias")
        for row in self.cursor.fetchall():
            tree.insert('', 'end', values=row)
        def agregar():
            nombre = simpledialog.askstring("Nueva categoría", "Nombre:")
            if nombre:
                tipo = simpledialog.askstring("Tipo", "¿Ingreso o gasto?", initialvalue="gasto")
                if tipo.lower() not in ("ingreso","gasto"):
                    messagebox.showerror("Error","Tipo debe ser ingreso o gasto")
                    return
                es_gasto = 1 if tipo.lower() == "gasto" else 0
                self.cursor.execute("INSERT OR IGNORE INTO categorias (nombre, tipo, es_gasto, presupuesto_mensual, palabras_clave) VALUES (?,?,?,?,?)",
                                    (nombre, tipo.lower(), es_gasto, 0.0, ""))
                self.conn.commit()
                ventana.destroy()
                self.gestionar_categorias()
                self.cargar_configuracion()
        tk.Button(ventana, text="Agregar", command=agregar).pack(pady=5)
    
    def gestionar_reglas_ahorro(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Reglas de Ahorro Automático")
        ventana.geometry("500x400")
        tree = ttk.Treeview(ventana, columns=('nombre','activa'), show='headings')
        tree.heading('nombre', text='Regla')
        tree.heading('activa', text='Activa')
        tree.pack(fill='both', expand=True)
        self.cursor.execute("SELECT id, nombre, activa, tipo_regla, parametros FROM reglas_ahorro")
        for row in self.cursor.fetchall():
            activa_str = "Sí" if row[2] else "No"
            tree.insert('', 'end', values=(row[1], activa_str), tags=(row[0],))
        def cambiar_estado():
            selec = tree.selection()
            if not selec: return
            id_regla = tree.item(selec[0], 'tags')[0]
            self.cursor.execute("UPDATE reglas_ahorro SET activa = NOT activa WHERE id=?", (id_regla,))
            self.conn.commit()
            ventana.destroy()
            self.gestionar_reglas_ahorro()
        def editar_parametros():
            selec = tree.selection()
            if not selec: return
            id_regla = tree.item(selec[0], 'tags')[0]
            self.cursor.execute("SELECT tipo_regla, parametros FROM reglas_ahorro WHERE id=?", (id_regla,))
            tipo_regla, params_json = self.cursor.fetchone()
            params = json.loads(params_json)
            valor_actual = list(params.values())[0]
            nuevo_valor = simpledialog.askfloat("Parámetro", f"Nuevo valor (actual: {valor_actual})")
            if nuevo_valor is not None:
                if tipo_regla == "redondeo":
                    params["redondeo_a"] = nuevo_valor
                elif tipo_regla == "porcentaje_ingreso":
                    params["porcentaje"] = nuevo_valor
                elif tipo_regla == "periodico":
                    params["monto_fijo"] = nuevo_valor
                self.cursor.execute("UPDATE reglas_ahorro SET parametros=? WHERE id=?", (json.dumps(params), id_regla))
                self.conn.commit()
                ventana.destroy()
                self.gestionar_reglas_ahorro()
        tk.Button(ventana, text="Activar/Desactivar", command=cambiar_estado).pack(pady=5)
        tk.Button(ventana, text="Editar parámetros", command=editar_parametros).pack(pady=5)
    
    def gestionar_presupuestos(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Presupuestos Mensuales por Categoría")
        ventana.geometry("600x400")
        tree = ttk.Treeview(ventana, columns=('categoria','presupuesto','gastado'), show='headings')
        tree.heading('categoria', text='Categoría')
        tree.heading('presupuesto', text='Presupuesto ($)')
        tree.heading('gastado', text='Gastado este mes ($)')
        tree.pack(fill='both', expand=True)
        mes_actual = datetime.today().strftime('%Y-%m')
        moneda_actual = self.moneda.get()
        self.cursor.execute("SELECT nombre, presupuesto_mensual FROM categorias WHERE es_gasto=1")
        for cat, presu in self.cursor.fetchall():
            self.cursor.execute("SELECT SUM(monto) FROM transacciones WHERE categoria=? AND tipo='gasto' AND strftime('%Y-%m', fecha)=? AND moneda=?", (cat, mes_actual, moneda_actual))
            gastado = self.cursor.fetchone()[0] or 0
            tree.insert('', 'end', values=(cat, f"{presu:.2f}", f"{gastado:.2f}"))
        def editar_presupuesto():
            selec = tree.selection()
            if not selec: return
            cat = tree.item(selec[0], 'values')[0]
            nuevo = simpledialog.askfloat("Editar presupuesto", f"Nuevo presupuesto mensual para {cat} (en {moneda_actual})")
            if nuevo is not None:
                self.cursor.execute("UPDATE categorias SET presupuesto_mensual=? WHERE nombre=?", (nuevo, cat))
                self.conn.commit()
                ventana.destroy()
                self.gestionar_presupuestos()
        tk.Button(ventana, text="Editar presupuesto", command=editar_presupuesto).pack(pady=5)
    
    def gestionar_deudas(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Gestión de Deudas")
        ventana.geometry("800x500")
        frame_alta = tk.LabelFrame(ventana, text="Nueva deuda")
        frame_alta.pack(fill='x', padx=10, pady=5)
        tk.Label(frame_alta, text="Nombre:").grid(row=0, column=0)
        nombre_var = tk.StringVar()
        tk.Entry(frame_alta, textvariable=nombre_var).grid(row=0, column=1)
        tk.Label(frame_alta, text="Monto inicial:").grid(row=0, column=2)
        monto_var = tk.StringVar()
        tk.Entry(frame_alta, textvariable=monto_var).grid(row=0, column=3)
        tk.Label(frame_alta, text="Tasa interés anual %:").grid(row=1, column=0)
        tasa_var = tk.StringVar()
        tk.Entry(frame_alta, textvariable=tasa_var).grid(row=1, column=1)
        tk.Label(frame_alta, text="Cuota mensual:").grid(row=1, column=2)
        cuota_var = tk.StringVar()
        tk.Entry(frame_alta, textvariable=cuota_var).grid(row=1, column=3)
        def agregar_deuda():
            try:
                nombre = nombre_var.get()
                monto = float(monto_var.get())
                tasa = float(tasa_var.get())
                cuota = float(cuota_var.get())
                fecha_ini = datetime.today().strftime('%Y-%m-%d')
                self.cursor.execute("INSERT INTO deudas (nombre, monto_inicial, tasa_interes_anual, cuota_mensual, fecha_inicio, saldo_restante, activa) VALUES (?,?,?,?,?,?,?)",
                                    (nombre, monto, tasa, cuota, fecha_ini, monto, 1))
                self.conn.commit()
                ventana.destroy()
                self.gestionar_deudas()
            except:
                messagebox.showerror("Error", "Datos inválidos")
        tk.Button(frame_alta, text="Agregar deuda", command=agregar_deuda).grid(row=2, column=0, columnspan=4, pady=5)
        tree = ttk.Treeview(ventana, columns=('nombre','monto','tasa','cuota','saldo','avance'), show='headings')
        tree.heading('nombre', text='Deuda')
        tree.heading('monto', text='Monto inicial')
        tree.heading('tasa', text='Tasa %')
        tree.heading('cuota', text='Cuota')
        tree.heading('saldo', text='Saldo restante')
        tree.heading('avance', text='Meses restantes')
        tree.pack(fill='both', expand=True)
        self.cursor.execute("SELECT id, nombre, monto_inicial, tasa_interes_anual, cuota_mensual, saldo_restante FROM deudas WHERE activa=1")
        for deuda in self.cursor.fetchall():
            id_, nombre, monto_inicial, tasa, cuota, saldo = deuda
            meses_rest = int(saldo // cuota) + 1 if cuota > 0 else 0
            tree.insert('', 'end', values=(nombre, f"{monto_inicial:.2f}", f"{tasa:.2f}", f"{cuota:.2f}", f"{saldo:.2f}", meses_rest), tags=(id_,))
        def registrar_pago():
            selec = tree.selection()
            if not selec: return
            id_deuda = tree.item(selec[0], 'tags')[0]
            self.cursor.execute("SELECT cuota_mensual, saldo_restante FROM deudas WHERE id=?", (id_deuda,))
            cuota, saldo = self.cursor.fetchone()
            nuevo_saldo = saldo - cuota
            if nuevo_saldo < 0:
                nuevo_saldo = 0
            self.cursor.execute("UPDATE deudas SET saldo_restante=? WHERE id=?", (nuevo_saldo, id_deuda))
            self.conn.commit()
            self.cursor.execute("INSERT INTO transacciones (fecha, concepto, categoria, monto, tipo, moneda) VALUES (?,?,?,?,?,?)",
                                (datetime.today().strftime('%Y-%m-%d'), f"Pago deuda: {tree.item(selec[0], 'values')[0]}", "Deudas", cuota, "gasto", self.moneda.get()))
            self.conn.commit()
            messagebox.showinfo("Pago", f"Se ha pagado {self.formatear_moneda(cuota)} de la deuda. Saldo restante: {self.formatear_moneda(nuevo_saldo)}")
            ventana.destroy()
            self.gestionar_deudas()
            self.actualizar_todo()
        tk.Button(ventana, text="Registrar pago (una cuota)", command=registrar_pago).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanzasAvanzado(root)
    root.mainloop()
