import customtkinter as ct
from tkinter import StringVar, messagebox, filedialog
from PIL import Image
import os
import json
import logging
from typing import Dict, List, Optional
import pandas as pd
import re

ct.set_appearance_mode("dark")
ct.set_default_color_theme("dark-blue")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BuscadorApp:
    def __init__(self, root):
        try:
            self.root = root
            self.logo_path = os.path.join(os.path.dirname(__file__), 'resources', 'Logo (2).png')
            self.indice_codigos = {}
            self.indice_resultados = {}
            self.indice_detalles = {}
            self.config_data = self.cargar_config()
            
            # Variables para almacenar resultados del escaneo
            self.resultados_actuales = []
            self.codigo_actual = ""
            
            self.tabview = ct.CTkTabview(self.root, fg_color="#000000")
            self.tabview.pack(fill="both", expand=True, padx=40, pady=20)
            
            # Crear pestañas disponibles
            self.tabview.add("Escáner")
            self._configurar_interfaz(parent=self.tabview.tab("Escáner"))
            
            self.tabview.add("Configuración")
            self._configurar_configuracion(parent=self.tabview.tab("Configuración"))
            
            self.tabview.set("Escáner")
            self.cargar_indice_local()
        except Exception as e:
            import traceback
            error_text = f"ERROR EN BuscadorApp:\n{e}\n{traceback.format_exc()}"
            ct.CTkLabel(self.root, text=error_text, font=("Segoe UI", 16, "bold"), text_color="#FF3333").pack(pady=40)

    def cargar_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"clp": "", "reporte": ""}

    def guardar_config(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f)
        except PermissionError:
            # Si hay error de permisos, usar directorio temporal
            import tempfile
            temp_config_path = os.path.join(tempfile.gettempdir(), "config_temp.json")
            with open(temp_config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f)
            # No cambiar CONFIG_PATH global, solo usar la ruta temporal
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar configuración: {str(e)}")

    def _configurar_interfaz(self, parent=None):
        frame = parent
        # Frame horizontal para dividir en dos columnas
        main_hframe = ct.CTkFrame(frame, fg_color="#000000")
        main_hframe.pack(fill="both", expand=True, padx=40, pady=40)
        # Columna izquierda: logo, título, estado, entrada, botones, resultados
        left_col = ct.CTkFrame(main_hframe, fg_color="#000000")
        left_col.pack(side="left", fill="both", expand=True, padx=(0,40))
        logo_visible = False
        if os.path.exists(self.logo_path):
            try:
                logo_img = ct.CTkImage(light_image=Image.open(self.logo_path), dark_image=Image.open(self.logo_path), size=(90, 90))
                self.logo_label = ct.CTkLabel(left_col, image=logo_img, text="", fg_color="#000000")
                self.logo_label.pack(pady=(10, 10))
                logo_visible = True
            except Exception as e:
                ct.CTkLabel(left_col, text=f"[Error al cargar logo]", font=("Segoe UI", 18, "bold"), text_color="#00FFAA", fg_color="#000000").pack(pady=(10, 10))
        if not logo_visible:
            ct.CTkLabel(left_col, text="V&C", font=("Segoe UI", 28, "bold"), text_color="#00FFAA", fg_color="#000000").pack(pady=(10, 10))
        self.title_label = ct.CTkLabel(left_col, text="Escáner de Códigos", font=("Segoe UI", 22, "bold"), text_color="#00FFAA", fg_color="#000000")
        self.title_label.pack(pady=(0, 8))
        self.codigo_var = StringVar()
        self.codigo_entry = ct.CTkEntry(left_col, textvariable=self.codigo_var, font=("Segoe UI", 15), width=400, height=36, corner_radius=12, border_width=2, border_color="#00FFAA", fg_color="#000000", text_color="#00FFAA", placeholder_text="Código de barras")
        self.codigo_entry.pack(pady=(0, 18))
        self.codigo_entry.bind("<Return>", lambda e: self.buscar_codigo())
        self.botones_frame = ct.CTkFrame(left_col, fg_color="#000000")
        self.botones_frame.pack(pady=(0, 10))
        self.search_button = ct.CTkButton(self.botones_frame, text="Buscar", font=("Segoe UI", 14, "bold"), fg_color="#000000", hover_color="#111111", border_width=2, border_color="#00FFAA", text_color="#00FFAA", corner_radius=12, width=160, height=36, command=self.buscar_codigo)
        self.search_button.pack(side="left", padx=(0, 8))
        self.clear_index_button = ct.CTkButton(self.botones_frame, text="Borrar Índice", font=("Segoe UI", 12), fg_color="#000000", hover_color="#333333", border_width=2, border_color="#FF5555", text_color="#FF5555", corner_radius=12, width=160, height=36, command=self.borrar_indice)
        self.clear_index_button.pack(side="left", padx=(0, 8))
        
        # Botón de edición (inicialmente deshabilitado)
        self.edit_button = ct.CTkButton(self.botones_frame, text="Editar Items", font=("Segoe UI", 12, "bold"), fg_color="#000000", hover_color="#111111", border_width=2, border_color="#FFAA00", text_color="#FFAA00", corner_radius=12, width=160, height=36, command=self.abrir_editor_items, state="disabled")
        self.edit_button.pack(side="left")
        
        # Frame para resultados con scroll
        resultados_frame = ct.CTkScrollableFrame(left_col, fg_color="#000000", height=400, width=500)
        resultados_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        self.clave_valor = ct.CTkLabel(resultados_frame, text="ITEM: ", font=("Segoe UI", 13, "bold"), text_color="#00FFAA", fg_color="#000000")
        self.clave_valor.pack(pady=(0, 5), anchor="w", padx=10)
        self.resultado_valor = ct.CTkLabel(resultados_frame, text="RESULTADO: ", font=("Segoe UI", 12), text_color="#00FFAA", fg_color="#000000", wraplength=600)
        self.resultado_valor.pack(pady=(0, 5), anchor="w", padx=10)
        self.nom_valor = ct.CTkLabel(resultados_frame, text="NOM: ", font=("Segoe UI", 12, "italic"), text_color="#55DDFF", fg_color="#000000", wraplength=600)
        self.nom_valor.pack(pady=(0, 5), anchor="w", padx=10)
        self.detalles_valor = ct.CTkLabel(resultados_frame, text="DETALLES: ", font=("Segoe UI", 11), text_color="#FFAA00", fg_color="#000000", wraplength=600)
        self.detalles_valor.pack(pady=(0, 5), anchor="w", padx=10)
        
        # Columna derecha: totales, última actualización, botones índice
        right_col = ct.CTkFrame(main_hframe, fg_color="#000000")
        right_col.pack(side="right", fill="y", expand=False, padx=(40,0))
        self.total_codigos_label = ct.CTkLabel(right_col, text="Total de códigos: 0", font=("Segoe UI", 11), text_color="#00FFAA", fg_color="#000000")
        self.total_codigos_label.pack(pady=(0, 2))
        self.ultima_actualizacion_label = ct.CTkLabel(right_col, text="Última actualización: Nunca", font=("Segoe UI", 11), text_color="#00FFAA", fg_color="#000000")
        self.ultima_actualizacion_label.pack(pady=(0, 8))
        self.update_button = ct.CTkButton(right_col, text="Actualizar Índice", font=("Segoe UI", 12, "bold"), fg_color="#000000", hover_color="#111111", border_width=2, border_color="#00FFAA", text_color="#00FFAA", corner_radius=12, width=200, height=32, command=self.actualizar_indice)
        self.update_button.pack(pady=(0, 18))
        self.verificar_button = ct.CTkButton(right_col, text="Verificar Índice", font=("Segoe UI", 12), fg_color="#000000", hover_color="#333333", border_width=2, border_color="#00FFAA", text_color="#00FFAA", corner_radius=12, width=200, height=32, command=self.verificar_indice)
        self.verificar_button.pack(pady=(0, 8))

    def actualizar_indice(self):
        try:
            clp_path = self.config_data.get("clp", "")
            reporte_path = self.config_data.get("reporte", "")
            
            if not clp_path or not reporte_path:
                messagebox.showerror("Error", "Debes cargar tanto el archivo CLP como el Reporte de Mercancía en Configuración.")
                return
            
            # Leer archivo CLP
            df_clp = pd.read_excel(clp_path, dtype=str)
            if df_clp.empty or df_clp.shape[1] < 6:
                messagebox.showerror("Error", "El archivo CLP está vacío o no tiene suficientes columnas (mínimo 6).")
                return

            # Leer archivo de reporte de mercancía
            df_reporte = pd.read_excel(reporte_path, dtype=str)
            if df_reporte.empty:
                messagebox.showerror("Error", "El archivo de reporte de mercancía está vacío.")
                return

            def limpiar_item(valor):
                return re.sub(r'\D', '', str(valor)).lstrip('0')

            # Tipos de proceso a ignorar
            tipos_ignorar = ["Cumple", "Sin norma", "Criterio", "Revisado"]
            
            # Filtrar reporte por tipos de proceso válidos
            df_reporte_filtrado = df_reporte[~df_reporte.iloc[:, 2].str.contains('|'.join(tipos_ignorar), case=False, na=False)]
            
            # Crear diccionario de resultados del reporte
            reporte_dict = {}
            for _, row in df_reporte_filtrado.iterrows():
                item = str(row.iloc[0]).strip() if len(row) > 0 and pd.notnull(row.iloc[0]) else ""
                tipo_proceso = str(row.iloc[1]).strip() if len(row) > 1 and pd.notnull(row.iloc[1]) else ""
                norma = str(row.iloc[2]).strip() if len(row) > 2 and pd.notnull(row.iloc[2]) else ""
                criterio = str(row.iloc[3]).strip() if len(row) > 3 and pd.notnull(row.iloc[3]) else ""
                descripcion = str(row.iloc[4]).strip() if len(row) > 4 and pd.notnull(row.iloc[4]) else ""
                
                # Si tipo de proceso es "cumple" y criterio está vacío, asignar "CUMPLE" al criterio
                if tipo_proceso.lower() == "cumple" and (not criterio or criterio.lower() in ["nan", "none", ""]):
                    criterio = "CUMPLE"
                
                if item and item.lower() not in ["nan", "none", ""]:
                    # Limpiar item para buscar en CLP
                    item_limpio = re.sub(r'\D', '', str(item)).lstrip('0')
                    if item_limpio:
                        if item_limpio not in reporte_dict:
                            reporte_dict[item_limpio] = []
                        reporte_dict[item_limpio].append({
                            'item': item,
                            'tipo_proceso': tipo_proceso,
                            'norma': norma,
                            'criterio': criterio,
                            'descripcion': descripcion,
                            'fila_original': row
                        })

            # Construir índice con clave compuesta
            datos_indice = []
            for _, fila in df_clp.iterrows():
                item_code = limpiar_item(fila.iloc[0]) if len(fila) > 0 else ""
                codigo_barras = str(fila.iloc[5]).strip() if len(fila) > 5 else ""
                
                # Forzar código de barras a string sin notación científica
                if codigo_barras:
                    try:
                        if 'e' in codigo_barras.lower():
                            codigo_barras = '{0:.0f}'.format(float(codigo_barras))
                    except Exception:
                        pass
                
                if item_code and codigo_barras:
                    codigo_limpio = ''.join(c for c in codigo_barras if c.isdigit())
                    if codigo_limpio:
                        clave = f"{codigo_limpio}|{item_code}"
                        
                        # Buscar en reporte por item_code
                        resultados_reporte = reporte_dict.get(item_code, [])
                        
                        if resultados_reporte:
                            # Hay resultados en el reporte
                            # Determinar resultado basado en criterio y descripción
                            cumple_count = 0
                            total_count = len(resultados_reporte)
                            
                            for r in resultados_reporte:
                                if r['criterio'].lower() in ['cumple', 'conforme', 'aprobado'] or r['descripcion'].lower() in ['cumple', 'conforme', 'aprobado']:
                                    cumple_count += 1
                            
                            if cumple_count == total_count:
                                resultado_final = "CUMPLE"
                            elif cumple_count > 0:
                                resultado_final = "PARCIAL"
                            else:
                                resultado_final = "INSPECCIÓN"
                            
                            detalles = []
                            for r in resultados_reporte:
                                detalles.append(f"Item: {r['item']} - Tipo: {r['tipo_proceso']} - NOM: {r['norma']} - Criterio: {r['criterio']} - Descripción: {r['descripcion']}")
                        else:
                            # No hay resultados en el reporte
                            resultado_final = "SIN DATOS"
                            detalles = ["No se encontró información en el reporte"]
                        
                        datos_indice.append([clave, codigo_limpio, item_code, resultado_final, '; '.join(detalles)])

            df_indice = pd.DataFrame(datos_indice, columns=["CLAVE", "CODIGO", "ITEM", "RESULTADO", "DETALLES"])
            
            # Intentar guardar el archivo con manejo de errores
            try:
                df_indice.to_csv(INDICE_PATH, index=False, encoding="utf-8")
                self.cargar_indice_local()
                messagebox.showinfo("Éxito", f"Índice actualizado localmente. Registros: {len(df_indice)}\nUbicación: {INDICE_PATH}")
            except PermissionError:
                # Si hay error de permisos, intentar con directorio temporal
                import tempfile
                temp_path = os.path.join(tempfile.gettempdir(), "indice_temp.csv")
                df_indice.to_csv(temp_path, index=False, encoding="utf-8")
                messagebox.showwarning("Advertencia", f"Índice guardado en ubicación temporal debido a permisos.\nUbicación: {temp_path}")
                # Cargar el índice desde la ubicación temporal
                self.cargar_indice_local()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar el índice: {str(e)}")
        except Exception as e:
            import traceback
            messagebox.showerror("Error", f"Error al actualizar el índice local: {str(e)}\n\n{traceback.format_exc()}")

    def verificar_indice(self):
        try:
            df = pd.read_csv(INDICE_PATH, encoding="utf-8")
            num_registros = len(df)
            if num_registros > 0:
                # Contar resultados
                cumple = len(df[df['RESULTADO'] == 'CUMPLE'])
                parcial = len(df[df['RESULTADO'] == 'PARCIAL'])
                inspeccion = len(df[df['RESULTADO'] == 'INSPECCIÓN'])
                sin_datos = len(df[df['RESULTADO'] == 'SIN DATOS'])
                
                mensaje = f"El índice local existe.\nRegistros: {num_registros}\n\nDesglose:\n- Cumple: {cumple}\n- Parcial: {parcial}\n- Inspección: {inspeccion}\n- Sin datos: {sin_datos}"
                messagebox.showinfo("Verificar Índice", mensaje)
            else:
                messagebox.showwarning("Verificar Índice", "El índice local está vacío.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al verificar el índice local: {str(e)}")

    def borrar_indice(self):
        try:
            with open(INDICE_PATH, "w", encoding="utf-8") as f:
                f.write("CLAVE,CODIGO,ITEM,RESULTADO,DETALLES\n")
            self.indice_codigos.clear()
            self.indice_resultados.clear()
            self.indice_detalles.clear()
            self.clave_valor.configure(text="ITEM: ")
            self.resultado_valor.configure(text="RESULTADO: ")
            self.nom_valor.configure(text="NOM: ")
            self.detalles_valor.configure(text="DETALLES: ")
            self.total_codigos_label.configure(text="Total de códigos: 0")
            self.ultima_actualizacion_label.configure(text="Última actualización: Nunca")
            messagebox.showinfo("Éxito", "Índice local borrado completamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al borrar el índice local: {str(e)}")

    def cargar_indice_local(self):
        try:
            df = pd.read_csv(INDICE_PATH, encoding="utf-8")
            self.indice_codigos = {str(row["CLAVE"]): str(row["ITEM"]) for _, row in df.iterrows()}
            self.indice_resultados = {str(row["CLAVE"]): str(row["RESULTADO"]) for _, row in df.iterrows()}
            self.indice_detalles = {str(row["CLAVE"]): str(row["DETALLES"]) for _, row in df.iterrows()}
            self.total_codigos_label.configure(text=f"Total de códigos: {len(self.indice_codigos)}")
        except Exception:
            self.indice_codigos = {}
            self.indice_resultados = {}
            self.indice_detalles = {}
            self.total_codigos_label.configure(text="Total de códigos: 0")

    def buscar_codigo(self):
        codigo = self.codigo_var.get().strip()
        if not codigo:
            self.resultado_valor.configure(text="Ingrese un código válido")
            self.clave_valor.configure(text="ITEM: ")
            self.nom_valor.configure(text="NOM: ")
            self.detalles_valor.configure(text="DETALLES: ")
            self.codigo_var.set("")
            self.codigo_entry.focus_set()
            return
        if not self.indice_codigos or not self.indice_resultados:
            self.resultado_valor.configure(text="El índice no está cargado. Por favor, actualice el índice.")
            self.clave_valor.configure(text="ITEM: ")
            self.nom_valor.configure(text="NOM: ")
            self.detalles_valor.configure(text="DETALLES: ")
            self.codigo_var.set("")
            self.codigo_entry.focus_set()
            return
        self.search_button.configure(state="disabled")
        self.search_button.configure(text="Buscando...")
        self.root.update()
        try:
            codigo_limpio = ''.join(c for c in str(codigo) if c.isdigit())
            logger.info(f"Buscando código: {codigo_limpio}")
            encontrado = False
            
            # Limpiar resultados anteriores
            self.resultados_actuales = []
            self.codigo_actual = codigo_limpio
            
            # Buscar todos los códigos que coincidan
            coincidencias = []
            for clave in self.indice_codigos:
                if clave.startswith(f"{codigo_limpio}|"):
                    item_code = self.indice_codigos[clave]
                    resultado = self.indice_resultados.get(clave, "")
                    detalles = self.indice_detalles.get(clave, "")
                    coincidencias.append({
                        'clave': clave,
                        'item': item_code,
                        'resultado': resultado,
                        'detalles': detalles
                    })
            
            if coincidencias:
                encontrado = True
                # Almacenar resultados para edición
                self.resultados_actuales = coincidencias
                
                if len(coincidencias) == 1:
                    # Un solo resultado
                    item = coincidencias[0]['item']
                    resultado = coincidencias[0]['resultado']
                    detalles = coincidencias[0]['detalles']
                    
                    # Extraer NOM de los detalles
                    nom_info = "NOM: No disponible"
                    if "NOM:" in detalles:
                        nom_parts = detalles.split("NOM:")
                        if len(nom_parts) > 1:
                            nom_part = nom_parts[1].split(" - ")[0].strip()
                            if nom_part and nom_part.lower() not in ["nan", "none", ""]:
                                nom_info = f"NOM: {nom_part}"
                    
                    self.clave_valor.configure(text=f"ITEM: {item}")
                    self.resultado_valor.configure(text=f"RESULTADO: {resultado}")
                    self.nom_valor.configure(text=nom_info)
                    self.detalles_valor.configure(text=f"DETALLES: {detalles}")
                else:
                    # Múltiples resultados
                    self.clave_valor.configure(text=f"ITEM: Múltiples items encontrados ({len(coincidencias)})")
                    self.resultado_valor.configure(text="RESULTADO: Ver detalles")
                    self.nom_valor.configure(text="NOM: Múltiples NOMs")
                    
                    detalles_texto = "DETALLES:\n"
                    for i, coinci in enumerate(coincidencias, 1):
                        detalles_texto += f"{i}. Item: {coinci['item']} - {coinci['resultado']}\n"
                        detalles_texto += f"   {coinci['detalles']}\n\n"
                    
                    self.detalles_valor.configure(text=detalles_texto)
                
                # Habilitar botón de edición
                self.edit_button.configure(state="normal")
            
            if not encontrado:
                logger.info(f"Código no encontrado: {codigo_limpio}")
                self.clave_valor.configure(text="ITEM: ")
                self.resultado_valor.configure(text="Código no encontrado")
                self.nom_valor.configure(text="NOM: ")
                self.detalles_valor.configure(text="DETALLES: ")
                # Deshabilitar botón de edición
                self.edit_button.configure(state="disabled")
        except Exception as e:
            logger.error(f"Error al buscar código: {str(e)}")
            self.clave_valor.configure(text="ITEM: ")
            self.resultado_valor.configure(text="Error al buscar código")
            self.nom_valor.configure(text="NOM: ")
            self.detalles_valor.configure(text="DETALLES: ")
        finally:
            self.search_button.configure(text="Buscar")
            self.search_button.configure(state="normal")
            self.codigo_var.set("")
            self.codigo_entry.focus_set()

    def abrir_editor_items(self):
        """Abre la ventana de edición de items encontrados"""
        if not self.resultados_actuales:
            messagebox.showwarning("Advertencia", "No hay items para editar.")
            return
        
        # Crear ventana de edición
        editor_window = ct.CTkToplevel(self.root)
        editor_window.title("Editor de Items - V&C")
        editor_window.geometry("1000x700")
        editor_window.configure(fg_color="#000000")
        editor_window.grab_set()  # Hacer modal
        
        # Frame principal
        main_frame = ct.CTkFrame(editor_window, fg_color="#000000")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ct.CTkLabel(main_frame, text=f"Editor de Reporte - Código: {self.codigo_actual}", 
                   font=("Segoe UI", 16, "bold"), text_color="#00FFAA", fg_color="#000000").pack(pady=(0, 20))
        
        # Frame scrollable para los items (más pequeño para dejar espacio a los botones)
        items_frame = ct.CTkScrollableFrame(main_frame, fg_color="#000000", height=400)
        items_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Opciones disponibles
        tipos_proceso = ["CUMPLE", "ADHERIBLE", "COSTURA", "SIN NORMA"]
        criterios = ["REVISADO", "NO CUMPLE", ""]
        
        # Variables para almacenar los cambios
        cambios_items = {}
        
        # Crear widgets para cada item
        for i, resultado in enumerate(self.resultados_actuales):
            item_frame = ct.CTkFrame(items_frame, fg_color="#111111", corner_radius=8)
            item_frame.pack(fill="x", pady=5, padx=10)
            
            # Información del item
            item_info = ct.CTkLabel(item_frame, 
                                  text=f"Item: {resultado['item']} - Estado actual: {resultado['resultado']}", 
                                  font=("Segoe UI", 12, "bold"), text_color="#00FFAA", fg_color="#111111")
            item_info.pack(anchor="w", padx=10, pady=(10, 5))
            
            # Detalles
            detalles_label = ct.CTkLabel(item_frame, 
                                       text=f"Detalles: {resultado['detalles'][:150]}...", 
                                       font=("Segoe UI", 10), text_color="#55DDFF", fg_color="#111111", wraplength=900)
            detalles_label.pack(anchor="w", padx=10, pady=(0, 10))
            
            # Extraer información actual del reporte
            tipo_actual = ""
            criterio_actual = ""
            
            # Buscar en el reporte original
            reporte_path = self.config_data.get("reporte", "")
            if reporte_path and os.path.exists(reporte_path):
                try:
                    df_reporte = pd.read_excel(reporte_path, dtype=str)
                    # Buscar el item en el reporte
                    for _, row in df_reporte.iterrows():
                        if str(row.iloc[0]).strip() == str(resultado['item']).strip():
                            tipo_actual = str(row.iloc[1]).strip() if len(row) > 1 and pd.notnull(row.iloc[1]) else ""
                            criterio_actual = str(row.iloc[3]).strip() if len(row) > 3 and pd.notnull(row.iloc[3]) else ""
                            break
                except Exception:
                    pass
            
            # Frame para controles
            controles_frame = ct.CTkFrame(item_frame, fg_color="#111111")
            controles_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # TIPO DE PROCESO
            ct.CTkLabel(controles_frame, text="Tipo de Proceso:", font=("Segoe UI", 11), text_color="#FFAA00", fg_color="#111111").pack(side="left", padx=(0, 10))
            
            tipo_var = StringVar(value=tipo_actual)
            tipo_menu = ct.CTkOptionMenu(controles_frame, 
                                       values=tipos_proceso, 
                                       variable=tipo_var,
                                       fg_color="#000000", 
                                       button_color="#00FFAA",
                                       button_hover_color="#00DD88",
                                       text_color="#00FFAA",
                                       width=120)
            tipo_menu.pack(side="left", padx=(0, 20))
            
            # CRITERIO
            ct.CTkLabel(controles_frame, text="Criterio:", font=("Segoe UI", 11), text_color="#FFAA00", fg_color="#111111").pack(side="left", padx=(0, 10))
            
            criterio_var = StringVar(value=criterio_actual)
            criterio_menu = ct.CTkOptionMenu(controles_frame, 
                                           values=criterios, 
                                           variable=criterio_var,
                                           fg_color="#000000", 
                                           button_color="#00FFAA",
                                           button_hover_color="#00DD88",
                                           text_color="#00FFAA",
                                           width=120)
            criterio_menu.pack(side="left", padx=(0, 20))
            
            # Almacenar referencia para acceso posterior
            cambios_items[resultado['clave']] = {
                'item': resultado['item'],
                'tipo_original': tipo_actual,
                'criterio_original': criterio_actual,
                'tipo_var': tipo_var,
                'criterio_var': criterio_var,
                'tipo_menu': tipo_menu,
                'criterio_menu': criterio_menu
            }
        
        # Frame para botones
        botones_frame = ct.CTkFrame(main_frame, fg_color="#000000")
        botones_frame.pack(fill="x", pady=(10, 0))
        
        # Botón guardar
        guardar_button = ct.CTkButton(botones_frame, 
                                    text="Guardar Cambios", 
                                    font=("Segoe UI", 14, "bold"),
                                    fg_color="#000000", 
                                    hover_color="#111111", 
                                    border_width=2, 
                                    border_color="#00FFAA", 
                                    text_color="#00FFAA", 
                                    corner_radius=12, 
                                    width=200, 
                                    height=45,
                                    command=lambda: self.guardar_cambios_items(cambios_items, editor_window))
        guardar_button.pack(side="left", padx=(20, 10))
        
        # Botón cancelar
        cancelar_button = ct.CTkButton(botones_frame, 
                                     text="Cancelar", 
                                     font=("Segoe UI", 14),
                                     fg_color="#000000", 
                                     hover_color="#333333", 
                                     border_width=2, 
                                     border_color="#FF5555", 
                                     text_color="#FF5555", 
                                     corner_radius=12, 
                                     width=150, 
                                     height=45,
                                     command=editor_window.destroy)
        cancelar_button.pack(side="left")

    def guardar_cambios_items(self, cambios_items, editor_window):
        """Guarda los cambios realizados en el reporte de mercancía"""
        try:
            reporte_path = self.config_data.get("reporte", "")
            if not reporte_path or not os.path.exists(reporte_path):
                messagebox.showerror("Error", "No se encontró el archivo de reporte de mercancía.")
                return
            
            # Leer el reporte original
            df_reporte = pd.read_excel(reporte_path, dtype=str)
            
            # Contador de cambios
            cambios_realizados = 0
            
            # Aplicar cambios al reporte
            for clave, info in cambios_items.items():
                item = info['item']
                nuevo_tipo = info['tipo_var'].get()
                nuevo_criterio = info['criterio_var'].get()
                
                # Buscar la fila correspondiente en el reporte
                for idx, row in df_reporte.iterrows():
                    if str(row.iloc[0]).strip() == str(item).strip():
                        # Verificar si hay cambios
                        tipo_actual = str(row.iloc[1]).strip() if len(row) > 1 and pd.notnull(row.iloc[1]) else ""
                        criterio_actual = str(row.iloc[3]).strip() if len(row) > 3 and pd.notnull(row.iloc[3]) else ""
                        
                        if nuevo_tipo != tipo_actual or nuevo_criterio != criterio_actual:
                            # Actualizar tipo de proceso (columna 1)
                            if len(row) > 1:
                                df_reporte.iloc[idx, 1] = nuevo_tipo
                            
                            # Actualizar criterio (columna 3)
                            if len(row) > 3:
                                df_reporte.iloc[idx, 3] = nuevo_criterio
                            
                            cambios_realizados += 1
                        break
            
            if cambios_realizados > 0:
                # Guardar el reporte actualizado
                try:
                    df_reporte.to_excel(reporte_path, index=False)
                    messagebox.showinfo("Éxito", f"Se guardaron {cambios_realizados} cambios en el reporte de mercancía.")
                except PermissionError:
                    # Si hay error de permisos, crear copia de respaldo
                    backup_path = reporte_path.replace('.xlsx', '_backup.xlsx').replace('.xls', '_backup.xls')
                    df_reporte.to_excel(backup_path, index=False)
                    messagebox.showwarning("Advertencia", 
                                         f"No se pudo guardar el archivo original debido a permisos.\n"
                                         f"Los cambios se guardaron en: {backup_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar el reporte: {str(e)}")
                    return
                
                # Actualizar el índice local
                self.actualizar_indice()
                
                # Cerrar ventana de edición
                editor_window.destroy()
                
                # Limpiar resultados actuales y deshabilitar botón
                self.resultados_actuales = []
                self.edit_button.configure(state="disabled")
                
                # Limpiar pantalla de resultados
                self.clave_valor.configure(text="ITEM: ")
                self.resultado_valor.configure(text="RESULTADO: ")
                self.nom_valor.configure(text="NOM: ")
                self.detalles_valor.configure(text="DETALLES: ")
                
            else:
                messagebox.showinfo("Información", "No se realizaron cambios.")
                editor_window.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar los cambios: {str(e)}")

    def _configurar_configuracion(self, parent=None):
        frame = parent
        frame.configure(fg_color="#000000")
        ct.CTkLabel(frame, text="Configuración de Archivos", font=("Segoe UI", 18, "bold"), text_color="#00FFAA", fg_color="#000000").pack(pady=(20, 10))
        self.ruta_clp_var = StringVar(value=self.config_data.get("clp", ""))
        self.ruta_reporte_var = StringVar(value=self.config_data.get("reporte", ""))
        ct.CTkLabel(frame, text="Archivo CLP:", text_color="#00FFAA", font=("Segoe UI", 14, "bold"), fg_color="#000000").pack(anchor="w", padx=20, pady=(10,0))
        self.ruta_clp_label = ct.CTkLabel(frame, textvariable=self.ruta_clp_var, text_color="#55DDFF", wraplength=600, fg_color="#000000")
        self.ruta_clp_label.pack(anchor="w", padx=20)
        ct.CTkButton(frame, text="Cargar Archivo CLP", command=self.cargar_archivo_clp, font=("Segoe UI", 13, "bold"), fg_color="#000000", hover_color="#111111", border_width=2, border_color="#00FFAA", text_color="#00FFAA", corner_radius=12, width=260, height=36).pack(pady=5, padx=20, anchor="w")
        ct.CTkLabel(frame, text="Reporte de Mercancía:", text_color="#00FFAA", font=("Segoe UI", 14, "bold"), fg_color="#000000").pack(anchor="w", padx=20, pady=(10,0))
        self.ruta_reporte_label = ct.CTkLabel(frame, textvariable=self.ruta_reporte_var, text_color="#55DDFF", wraplength=600, fg_color="#000000")
        self.ruta_reporte_label.pack(anchor="w", padx=20)
        ct.CTkButton(frame, text="Cargar Reporte de Mercancía", command=self.cargar_archivo_reporte, font=("Segoe UI", 13, "bold"), fg_color="#000000", hover_color="#111111", border_width=2, border_color="#00FFAA", text_color="#00FFAA", corner_radius=12, width=260, height=36).pack(pady=5, padx=20, anchor="w")

    def cargar_archivo_clp(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xls;*.xlsx"), ("Todos", "*.*")])
        if ruta:
            self.config_data["clp"] = ruta
            self.ruta_clp_var.set(ruta)
            self.guardar_config()

    def cargar_archivo_reporte(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xls;*.xlsx"), ("Todos", "*.*")])
        if ruta:
            self.config_data["reporte"] = ruta
            self.ruta_reporte_var.set(ruta)
            self.guardar_config()

# Crear directorio de caché en el directorio actual si no existe
import os
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR)
    except Exception:
        # Si no se puede crear, usar directorio temporal
        import tempfile
        CACHE_DIR = tempfile.gettempdir()

CONFIG_PATH = os.path.join(CACHE_DIR, "config.json")
INDICE_PATH = os.path.join(CACHE_DIR, "indice.csv")

if __name__ == "__main__":
    root = ct.CTk()
    root.title("Escáner de Códigos V&C")
    root.geometry("900x700")
    root.resizable(True, True)
    app = BuscadorApp(root)
    root.mainloop() 