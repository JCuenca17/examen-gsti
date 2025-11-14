import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class EstimadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Estimador de Demanda (BI Consultant)")
        self.root.geometry("550x450")

        self.df_2023 = None
        self.df_2024 = None
        self.df_estimado = None

        self._crear_widgets()

    def _crear_widgets(self):
        # Estilo
        style = ttk.Style(self.root)
        style.configure("TButton", padding=6, relief="flat", font=('Helvetica', 10, 'bold'))
        style.configure("TLabel", padding=5, font=('Helvetica', 10))
        style.configure("Header.TLabel", padding=5, font=('Helvetica', 12, 'bold'))

        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15 15 15 15")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- 1. Carga de Archivos ---
        frame_carga = ttk.LabelFrame(main_frame, text="1. Cargar Archivos CSV", padding="10 10")
        frame_carga.pack(fill=tk.X, expand=True)

        self.btn_2023 = ttk.Button(frame_carga, text="Cargar 2023", command=lambda: self._cargar_csv(2023))
        self.btn_2023.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.lbl_2023 = ttk.Label(frame_carga, text="No cargado", foreground="red", width=40, relief=tk.SUNKEN)
        self.lbl_2023.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.btn_2024 = ttk.Button(frame_carga, text="Cargar 2024", command=lambda: self._cargar_csv(2024))
        self.btn_2024.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.lbl_2024 = ttk.Label(frame_carga, text="No cargado", foreground="red", width=40, relief=tk.SUNKEN)
        self.lbl_2024.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        frame_carga.columnconfigure(1, weight=1)

        # --- 2. Procesamiento ---
        frame_proc = ttk.LabelFrame(main_frame, text="2. Procesar Datos", padding="10 10")
        frame_proc.pack(fill=tk.X, expand=True, pady=10)

        self.btn_procesar = ttk.Button(frame_proc, text="Procesar y Estimar", state="disabled", command=self._procesar_estimar)
        self.btn_procesar.pack(fill=tk.X, padx=5, pady=5)

        # --- 3. Visualización y Descarga ---
        frame_res = ttk.LabelFrame(main_frame, text="3. Resultados", padding="10 10")
        frame_res.pack(fill=tk.X, expand=True)

        ttk.Label(frame_res, text="Agrupar gráfico por:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.combo_agrupacion = ttk.Combobox(
            frame_res,
            values=["Total General", "Por Departamento", "Por Tarifa"],
            state="disabled"
        )
        self.combo_agrupacion.current(0)
        self.combo_agrupacion.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.btn_mostrar_grafico = ttk.Button(frame_res, text="Mostrar Gráfico", state="disabled", command=self._mostrar_grafico)
        self.btn_mostrar_grafico.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.btn_descargar = ttk.Button(frame_res, text="Descargar Estimación (.csv)", state="disabled", command=self._descargar_csv)
        self.btn_descargar.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        frame_res.columnconfigure(1, weight=1)

        # --- 4. Barra de Estado ---
        self.lbl_status = ttk.Label(main_frame, text="Listo.", relief=tk.SUNKEN, anchor=tk.W)
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X, expand=False, pady=(10,0))

    def _cargar_csv(self, anio):
        
        #Maneja la carga y validación de los archivos CSV.
        filepath = filedialog.askopenfilename(
            title=f"Seleccionar archivo de Mayo {anio}",
            filetypes=[("CSV files", "*.csv")]
        )
        if not filepath:
            return

        df = None
        last_error = None

        # --- Lógica de Carga Robusta ---
        # Lista de configuraciones para probar
        # (separador, decimal, encoding)
        configs_to_try = [
            (',', '.', 'latin-1'),  # Coma + Punto (Estándar) + Latin
            (';', '.', 'latin-1'),  # Punto y Coma + Punto (Común en EU/LATAM) + Latin
            (',', ',', 'latin-1'),  # Coma + Coma (Común en EU/LATAM) + Latin
            (';', ',', 'latin-1'),  # Punto y Coma + Coma (Común en EU/LATAM) + Latin
            (',', '.', 'utf-8'),    # Coma + Punto + UTF-8
            (';', '.', 'utf-8'),    # Punto y Coma + Punto + UTF-8
        ]

        self.lbl_status.config(text=f"Probando {len(configs_to_try)} configuraciones...")
        self.root.update_idletasks()

        for i, (sep, dec, enc) in enumerate(configs_to_try):
            try:
                self.lbl_status.config(text=f"Intento {i+1}: sep='{sep}' dec='{dec}' enc='{enc}'")
                df = pd.read_csv(
                    filepath,
                    sep=sep,
                    decimal=dec,
                    encoding=enc,
                    skipinitialspace=True # Ignorar espacios después del separador
                )
                
                # --- LIMPIEZA DE COLUMNAS ---
                # Quitar espacios y estandarizar a mayúsculas
                df.columns = df.columns.str.strip().str.upper()

                # --- VALIDACIÓN ---
                if 'CONSUMO' not in df.columns:
                     raise ValueError("Columna 'CONSUMO' no encontrada (después de limpiar).")
                
                # Forzar la conversión a numérico
                pd.to_numeric(df['CONSUMO'], errors='raise')

                # Si todo sale bien, rompemos el bucle
                self.lbl_status.config(text=f"Éxito con: sep='{sep}' dec='{dec}' enc='{enc}'")
                break
            
            except Exception as e:
                last_error = e
                df = None # Resetear df en caso de fallo
                continue # Probar la siguiente configuración

        if df is None:
            # Si df sigue siendo None, todos los intentos fallaron
            messagebox.showerror("Error de Lectura", 
                f"No se pudo leer el archivo CSV o la columna 'CONSUMO' no es numérica.\n"
                f"Se probaron {len(configs_to_try)} configuraciones (separador, decimal, encoding).\n"
                f"Último error: {last_error}")
            self.lbl_status.config(text="Error de lectura.")
            return

        # Si todo OK
        if anio == 2023:
            self.df_2023 = df
            self.lbl_2023.config(text=filepath.split('/')[-1], foreground="green")
        else:
            self.df_2024 = df
            self.lbl_2024.config(text=filepath.split('/')[-1], foreground="green")
        
        self.lbl_status.config(text=f"Archivo {anio} cargado.")
        self._verificar_listo_para_procesar()

    def _verificar_listo_para_procesar(self):
        # Habilita el botón de procesar si ambos archivos están cargados.
        if self.df_2023 is not None and self.df_2024 is not None:
            self.btn_procesar.config(state="normal")
            self.lbl_status.config(text="Archivos listos. Presione 'Procesar'.")

    def _procesar_estimar(self):
        # Núcleo de la lógica de BI: agrupar, unir y extrapolar.
        self.lbl_status.config(text="Procesando...")
        self.root.update_idletasks() # Forzar actualización de la GUI

        try:
            # 1. Limpiar y validar columnas (DEPARTAMENTO, TARIFA, CONSUMO)
            cols_necesarias = ['DEPARTAMENTO', 'TARIFA', 'CONSUMO']
            
            # Estandarizar columnas (por si acaso, aunque ya se hizo al cargar)
            self.df_2023.columns = self.df_2023.columns.str.strip().str.upper()
            self.df_2024.columns = self.df_2024.columns.str.strip().str.upper()

            for col in cols_necesarias:
                if col not in self.df_2023.columns or col not in self.df_2024.columns:
                    raise ValueError(f"Columna requerida '{col}' no encontrada en ambos archivos.")
            
            # 2. Convertir CONSUMO a numérico (con coerción por si acaso)
            self.df_2023['CONSUMO'] = pd.to_numeric(self.df_2023['CONSUMO'], errors='coerce').fillna(0)
            self.df_2024['CONSUMO'] = pd.to_numeric(self.df_2024['CONSUMO'], errors='coerce').fillna(0)
            
            # 3. Agrupar por las dimensiones clave
            # --- LIMPIEZA DE DATOS ---
            # Limpiar espacios y estandarizar datos de texto antes de agrupar
            self.df_2023['DEPARTAMENTO'] = self.df_2023['DEPARTAMENTO'].astype(str).str.strip().str.upper()
            self.df_2023['TARIFA'] = self.df_2023['TARIFA'].astype(str).str.strip().str.upper()
            self.df_2024['DEPARTAMENTO'] = self.df_2024['DEPARTAMENTO'].astype(str).str.strip().str.upper()
            self.df_2024['TARIFA'] = self.df_2024['TARIFA'].astype(str).str.strip().str.upper()

            df_2023_agg = self.df_2023.groupby(['DEPARTAMENTO', 'TARIFA'])['CONSUMO'].sum().reset_index()
            df_2024_agg = self.df_2024.groupby(['DEPARTAMENTO', 'TARIFA'])['CONSUMO'].sum().reset_index()

            # 4. Renombrar para la unión
            df_2023_agg = df_2023_agg.rename(columns={'CONSUMO': 'CONSUMO_2023'})
            df_2024_agg = df_2024_agg.rename(columns={'CONSUMO': 'CONSUMO_2024'})

            # 5. Unir los dos años. 'outer' asegura que no perdamos grupos que solo existen en un año.
            df_merged = pd.merge(df_2023_agg, df_2024_agg, on=['DEPARTAMENTO', 'TARIFA'], how='outer')

            # 6. Rellenar NaNs con 0 (para grupos que no existían en un año)
            df_merged = df_merged.fillna(0)

            # 7. La Extrapolación Lineal Simple
            # Crecimiento = Consumo(2024) - Consumo(2023)
            df_merged['CRECIMIENTO'] = df_merged['CONSUMO_2024'] - df_merged['CONSUMO_2023']
            
            # Estimación(2025) = Consumo(2024) + Crecimiento
            df_merged['CONSUMO_2025_ESTIMADO'] = df_merged['CONSUMO_2024'] + df_merged['CRECIMIENTO']

            # 8. Regla de negocio: El consumo no puede ser negativo
            df_merged['CONSUMO_2025_ESTIMADO'] = df_merged['CONSUMO_2025_ESTIMADO'].apply(lambda x: max(0, x))

            self.df_estimado = df_merged
            
            # 9. Habilitar botones de resultados
            self.btn_descargar.config(state="normal")
            self.btn_mostrar_grafico.config(state="normal")
            self.combo_agrupacion.config(state="readonly")
            
            self.lbl_status.config(text="¡Proceso completado! Listo para ver gráficos o descargar.")
            messagebox.showinfo("Proceso Completado", f"Estimación calculada para {len(self.df_estimado)} grupos (Dpto/Tarifa).")

        except Exception as e:
            self.lbl_status.config(text="Error.")
            messagebox.showerror("Error de Procesamiento", f"Ocurrió un error: {e}")

    def _mostrar_grafico(self):
        # Crea una nueva ventana Toplevel con el gráfico de Matplotlib.
        if self.df_estimado is None:
            return

        agrupacion = self.combo_agrupacion.get()

        # Crear nueva ventana para el gráfico
        plot_window = tk.Toplevel(self.root)
        plot_window.title(f"Gráfico de Consumo: {agrupacion}")
        plot_window.geometry("900x600")

        # Crear figura de Matplotlib
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)

        try:
            if agrupacion == "Total General":
                # Sumar el total de las columnas
                datos = self.df_estimado[['CONSUMO_2023', 'CONSUMO_2024', 'CONSUMO_2025_ESTIMADO']].sum()
                etiquetas = ['Mayo 2023', 'Mayo 2024', 'Estim. Mayo 2025']
                colores = ['#1f77b4', '#ff7f0e', '#2ca02c'] # Azul, Naranja, Verde
                
                bars = ax.bar(etiquetas, datos, color=colores)
                ax.set_title("Consumo Total General (Kwh)")
                
                # Añadir etiquetas de valor
                for bar in bars:
                    yval = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:,.0f}', va='bottom', ha='center')

            else:
                if agrupacion == "Por Departamento":
                    grupo_col = 'DEPARTAMENTO'
                elif agrupacion == "Por Tarifa":
                    grupo_col = 'TARIFA'
                
                df_plot = self.df_estimado.groupby(grupo_col)[['CONSUMO_2023', 'CONSUMO_2024', 'CONSUMO_2025_ESTIMADO']].sum()
                
                # Graficar como barras agrupadas
                df_plot.plot(kind='bar', ax=ax, width=0.8)
                
                ax.set_title(f"Consumo {agrupacion} (Kwh)")
                ax.legend(["Consumo 2023", "Consumo 2024", "Estim. 2025"])
                # Rotar etiquetas si hay muchas
                if len(df_plot) > 10:
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=8)
                else:
                     plt.setp(ax.get_xticklabels(), rotation=0)

            ax.set_ylabel("Consumo (Kwh)")
            # Formatear eje Y para que sea legible (con comas)
            ax.get_yaxis().set_major_formatter(
                plt.FuncFormatter(lambda x, p: format(int(x), ','))
            )
            fig.tight_layout() # Ajustar layout

            # Incrustar el gráfico en la ventana de Tkinter
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            # Añadir la barra de herramientas de Matplotlib
            toolbar = NavigationToolbar2Tk(canvas, plot_window)
            toolbar.update()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        except Exception as e:
            messagebox.showerror("Error al Graficar", f"No se pudo generar el gráfico: {e}")
            plot_window.destroy()

    def _descargar_csv(self):
        # Guarda el DataFrame de estimación en un CSV.
        if self.df_estimado is None:
            messagebox.showwarning("Aviso", "No hay datos estimados para descargar.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Guardar estimación como...",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not filepath:
            return

        try:
            # Guardar con formato estándar
            self.df_estimado.to_csv(filepath, index=False, sep=',', decimal='.')
            self.lbl_status.config(text=f"Archivo guardado en {filepath}")
            messagebox.showinfo("Éxito", f"Archivo guardado exitosamente en:\n{filepath}")
        except Exception as e:
            self.lbl_status.config(text="Error al guardar.")
            messagebox.showerror("Error al Guardar", f"No se pudo guardar el archivo: {e}")

# --- Bloque de Ejecución Principal ---
if __name__ == "__main__":
    root = tk.Tk()
    app = EstimadorApp(root)
    root.mainloop()