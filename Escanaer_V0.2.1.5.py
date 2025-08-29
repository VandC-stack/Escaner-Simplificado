"""
================================================================
   Creado con sangre, sudor y lágrimas
   mientras lloraba envuelto en una manta 
   por: Enrique Guzmán
   Autor: El Don del Ciber
   Tlalnepantla, México · 2025
================================================================
"""

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
            # Verificar y sincronizar configuración
            self.verificar_configuracion()
            # Actualizar etiquetas con información guardada
            self.actualizar_etiquetas_configuracion()
        except Exception as e:
            import traceback
            error_text = f"ERROR EN BuscadorApp:\n{e}\n{traceback.format_exc()}"
            ct.CTkLabel(self.root, text=error_text, font=("Segoe UI", 16, "bold"), text_color="#FF3333").pack(pady=40)

    def cargar_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Asegurar que todas las claves existan
                if "clp" not in config:
                    config["clp"] = ""
                if "reporte" not in config:
                    config["reporte"] = ""
                if "ultima_actualizacion" not in config:
                    config["ultima_actualizacion"] = "Nunca"
                if "nombre_archivo_reporte" not in config:
                    config["nombre_archivo_reporte"] = ""
                
                # Si existe reporte pero no nombre_archivo_reporte, sincronizar
                if config["reporte"] and not config["nombre_archivo_reporte"]:
                    config["nombre_archivo_reporte"] = config["reporte"]
                
                return config
        except Exception:
            return {"clp": "", "reporte": "", "ultima_actualizacion": "Nunca", "nombre_archivo_reporte": ""}

    def guardar_config(self):
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f)
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
        
        # Botón de edición (deshabilitado hasta que se escanee)
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
        self.ultima_actualizacion_label.pack(pady=(0, 2))
        
        # Mostrar nombre del archivo de tipos de proceso
        self.nombre_archivo_label = ct.CTkLabel(right_col, text="Archivo: No cargado", font=("Segoe UI", 10), text_color="#55DDFF", fg_color="#000000")
        self.nombre_archivo_label.pack(pady=(0, 8))
        self.update_button = ct.CTkButton(right_col, text="Actualizar Índice", font=("Segoe UI", 12, "bold"), fg_color="#000000", hover_color="#111111", border_width=2, border_color="#00FFAA", text_color="#00FFAA", corner_radius=12, width=200, height=32, command=self.actualizar_indice)
        self.update_button.pack(pady=(0, 18))
        self.verificar_button = ct.CTkButton(right_col, text="Verificar Índice", font=("Segoe UI", 12), fg_color="#000000", hover_color="#333333", border_width=2, border_color="#00FFAA", text_color="#00FFAA", corner_radius=12, width=200, height=32, command=self.verificar_indice)
        self.verificar_button.pack(pady=(0, 8))
        
        # Botón de diagnóstico
        self.diagnostico_button = ct.CTkButton(right_col, text="Diagnóstico de Código", font=("Segoe UI", 12), fg_color="#000000", hover_color="#333333", border_width=2, border_color="#FFAA00", text_color="#FFAA00", corner_radius=12, width=200, height=32, command=self.mostrar_diagnostico)
        self.diagnostico_button.pack(pady=(0, 8))
        
        # Botón de debug de configuración
        self.debug_config_button = ct.CTkButton(right_col, text="Debug Config", font=("Segoe UI", 10), fg_color="#000000", hover_color="#333333", border_width=2, border_color="#FF00FF", text_color="#FF00FF", corner_radius=12, width=200, height=28, command=self.debug_configuracion)
        self.debug_config_button.pack(pady=(0, 8))

    def mostrar_diagnostico(self):
        """Muestra una ventana de diagnóstico para códigos problemáticos"""
        # Crear ventana de diagnóstico
        diagnostico_window = ct.CTkToplevel(self.root)
        diagnostico_window.title("Diagnóstico de Códigos - V&C")
        diagnostico_window.geometry("800x600")
        diagnostico_window.configure(fg_color="#000000")
        diagnostico_window.grab_set()  # Hacer modal
        
        # Frame principal
        main_frame = ct.CTkFrame(diagnostico_window, fg_color="#000000")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ct.CTkLabel(main_frame, text="Diagnóstico de Códigos", 
                   font=("Segoe UI", 16, "bold"), text_color="#00FFAA", fg_color="#000000").pack(pady=(0, 20))
        
        # Frame para entrada de código
        entrada_frame = ct.CTkFrame(main_frame, fg_color="#111111")
        entrada_frame.pack(fill="x", pady=(0, 20))
        
        ct.CTkLabel(entrada_frame, text="Ingrese el código que no se encuentra:", 
                   font=("Segoe UI", 12), text_color="#FFAA00", fg_color="#111111").pack(pady=(10, 5))
        
        codigo_var = StringVar()
        codigo_entry = ct.CTkEntry(entrada_frame, textvariable=codigo_var, font=("Segoe UI", 14), 
                                 width=400, height=36, corner_radius=12, border_width=2, 
                                 border_color="#00FFAA", fg_color="#000000", text_color="#00FFAA")
        codigo_entry.pack(pady=(0, 10))
        
        # Frame para resultados y botones (contenedor principal)
        contenido_frame = ct.CTkFrame(main_frame, fg_color="#000000")
        contenido_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Frame para resultados (dentro del contenedor)
        resultados_frame = ct.CTkScrollableFrame(contenido_frame, fg_color="#000000", height=350)
        resultados_frame.pack(fill="both", expand=True, pady=(10, 10), padx=10)
        
        resultado_label = ct.CTkLabel(resultados_frame, text="", font=("Segoe UI", 11), 
                                    text_color="#55DDFF", fg_color="#000000", wraplength=750, justify="left")
        resultado_label.pack(anchor="w", padx=10, pady=10)
        
        def ejecutar_diagnostico():
            codigo = codigo_var.get().strip()
            if not codigo:
                resultado_label.configure(text="Por favor, ingrese un código para diagnosticar.")
                return
            
            codigo_limpio = ''.join(c for c in str(codigo) if c.isdigit())
            diagnostico = self.diagnosticar_codigo(codigo_limpio)
            resultado_label.configure(text=diagnostico)
        
        # Botones (dentro del mismo contenedor)
        botones_frame = ct.CTkFrame(contenido_frame, fg_color="#000000")
        botones_frame.pack(fill="x", pady=(0, 10), padx=10)
        
        ct.CTkButton(botones_frame, text="Ejecutar Diagnóstico", command=ejecutar_diagnostico,
                    font=("Segoe UI", 14, "bold"), fg_color="#000000", hover_color="#111111", 
                    border_width=2, border_color="#00FFAA", text_color="#00FFAA", 
                    corner_radius=12, width=200, height=45).pack(side="left", padx=(0, 10))
        
        ct.CTkButton(botones_frame, text="Cerrar", command=diagnostico_window.destroy,
                    font=("Segoe UI", 14), fg_color="#000000", hover_color="#333333", 
                    border_width=2, border_color="#FF5555", text_color="#FF5555", 
                    corner_radius=12, width=150, height=45).pack(side="left")

    def actualizar_indice(self):
        try:
            clp_path = self.config_data.get("clp", "")
            reporte_path = self.config_data.get("reporte", "")
            
            if not clp_path or not reporte_path:
                messagebox.showerror("Error", "Debes cargar tanto el archivo CLP como el archivo de Tipos de Procesos en Configuración.")
                return
            
            # Leer archivo CLP
            df_clp = pd.read_excel(clp_path, dtype=str)
            if df_clp.empty or df_clp.shape[1] < 6:
                messagebox.showerror("Error", "El archivo CLP está vacío o no tiene suficientes columnas (mínimo 6).")
                return

            # Leer archivo de reporte de mercancía
            df_reporte = pd.read_excel(reporte_path, dtype=str)
            if df_reporte.empty:
                messagebox.showerror("Error", "El archivo de tipos de procesos está vacío.")
                return

            def limpiar_item(valor):
                """Función mejorada para limpiar items"""
                try:
                    if pd.isna(valor) or valor is None:
                        return ""
                    valor_str = str(valor).strip()
                    if not valor_str or valor_str.lower() in ['nan', 'none', '']:
                        return ""
                    # Remover caracteres no numéricos y ceros a la izquierda
                    solo_numeros = re.sub(r'\D', '', valor_str)
                    return solo_numeros.lstrip('0') if solo_numeros else ""
                except Exception:
                    return ""

            # Tipos de proceso a ignorar
            tipos_ignorar = ["Cumple", "Sin norma", "Criterio", "Revisado"]
            
            # Filtrar reporte por tipos de proceso válidos
            df_reporte_filtrado = df_reporte[~df_reporte.iloc[:, 2].str.contains('|'.join(tipos_ignorar), case=False, na=False)]
            
            # Crear diccionario de resultados del reporte
            reporte_dict = {}
            for _, row in df_reporte_filtrado.iterrows():
                try:
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
                        item_limpio = limpiar_item(item)
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
                except Exception as e:
                    logger.warning(f"Error procesando fila del reporte: {e}")
                    continue

            # Construir índice con clave compuesta
            datos_indice = []
            for _, fila in df_clp.iterrows():
                try:
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
                                    
                                # Determinar resultado basado en criterio y descripción
                                cumple_count = 0
                                total_count = len(resultados_reporte)
                                
                                for r in resultados_reporte:
                                    criterio_lower = r['criterio'].lower()
                                    descripcion_lower = r['descripcion'].lower()
                                    if (criterio_lower in ['cumple', 'conforme', 'aprobado'] or 
                                        descripcion_lower in ['cumple', 'conforme', 'aprobado']):
                                        cumple_count += 1
                                
                                if cumple_count == total_count:
                                    resultado_final = "CUMPLE"
                                elif cumple_count > 0:
                                    resultado_final = "REQUIERE REVISIÓN"
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
                except Exception as e:
                    logger.warning(f"Error procesando fila del CLP: {e}")
                    continue

            df_indice = pd.DataFrame(datos_indice, columns=["CLAVE", "CODIGO", "ITEM", "RESULTADO", "DETALLES"])
            
            # Intentar guardar el archivo con manejo de errores
            try:
                # Asegurar que el directorio existe
                os.makedirs(os.path.dirname(INDICE_PATH), exist_ok=True)
                df_indice.to_csv(INDICE_PATH, index=False, encoding="utf-8")
                
                # Guardar fecha y hora de la actualización
                from datetime import datetime
                fecha_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M")
                self.config_data["ultima_actualizacion"] = fecha_actualizacion
                self.guardar_config()
                
                # Recargar el índice en memoria inmediatamente
                self.cargar_indice_local()
                
                # Actualizar etiquetas
                self.actualizar_etiquetas_configuracion()
                
                messagebox.showinfo("Éxito", f"Índice actualizado localmente. Registros: {len(df_indice)}\nUbicación: {INDICE_PATH}")
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
                requiere_revision = len(df[df['RESULTADO'] == 'REQUIERE REVISIÓN'])
                inspeccion = len(df[df['RESULTADO'] == 'INSPECCIÓN'])
                sin_datos = len(df[df['RESULTADO'] == 'SIN DATOS'])
                
                mensaje = f"El índice local existe.\nRegistros: {num_registros}\n\nDesglose:\n- Cumple: {cumple}\n- Requiere Revisión: {requiere_revision}\n- Inspección: {inspeccion}\n- Sin datos: {sin_datos}"
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
            
            # Actualizar última actualización y etiquetas
            self.config_data["ultima_actualizacion"] = "Nunca"
            self.guardar_config()
            self.actualizar_etiquetas_configuracion()
            
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
    
    def verificar_configuracion(self):
        """Verifica y sincroniza la configuración al inicio"""
        try:
            # Sincronizar nombre_archivo_reporte con reporte si es necesario
            if self.config_data.get("reporte") and not self.config_data.get("nombre_archivo_reporte"):
                self.config_data["nombre_archivo_reporte"] = self.config_data["reporte"]
                self.guardar_config()
            
            # Verificar que los archivos configurados existan
            if self.config_data.get("reporte") and not os.path.exists(self.config_data["reporte"]):
                logger.warning(f"Archivo de reporte no encontrado: {self.config_data['reporte']}")
                # No limpiar la configuración, solo registrar el warning
        except Exception as e:
            logger.error(f"Error al verificar configuración: {e}")
    
    def actualizar_etiquetas_configuracion(self):
        """Actualiza las etiquetas con la información guardada en configuración"""
        try:
            # Actualizar última actualización
            ultima_actualizacion = self.config_data.get("ultima_actualizacion", "Nunca")
            self.ultima_actualizacion_label.configure(text=f"Última actualización: {ultima_actualizacion}")
            
            # Actualizar nombre del archivo de tipos de proceso
            # Primero intentar con nombre_archivo_reporte, si no existe usar la ruta del reporte
            nombre_archivo = self.config_data.get("nombre_archivo_reporte", "")
            if not nombre_archivo:
                nombre_archivo = self.config_data.get("reporte", "")
            
            if nombre_archivo and os.path.exists(nombre_archivo):
                # Extraer solo el nombre del archivo, no la ruta completa
                nombre_solo = os.path.basename(nombre_archivo)
                self.nombre_archivo_label.configure(text=f"Archivo: {nombre_solo}")
            else:
                self.nombre_archivo_label.configure(text="Archivo: No cargado")
        except Exception as e:
            logger.error(f"Error al actualizar etiquetas: {e}")

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
            
            # Buscar todos los códigos que coincidan - BÚSQUEDA MEJORADA
            coincidencias = []
            
            # Estrategia 1: Búsqueda exacta al inicio (original)
            for clave in self.indice_codigos:
                if clave.startswith(f"{codigo_limpio}|"):
                    item_code = self.indice_codigos[clave]
                    resultado = self.indice_resultados.get(clave, "")
                    detalles = self.indice_detalles.get(clave, "")
                    coincidencias.append({
                        'clave': clave,
                        'item': item_code,
                        'resultado': resultado,
                        'detalles': detalles,
                        'tipo_coincidencia': 'exacta'
                    })
            
            # Estrategia 2: Si no hay coincidencias exactas, buscar códigos que contengan el patrón
            if not coincidencias:
                for clave in self.indice_codigos:
                    codigo_en_clave = clave.split('|')[0] if '|' in clave else ""
                    if codigo_limpio in codigo_en_clave:
                        item_code = self.indice_codigos[clave]
                        resultado = self.indice_resultados.get(clave, "")
                        detalles = self.indice_detalles.get(clave, "")
                        coincidencias.append({
                            'clave': clave,
                            'item': item_code,
                            'resultado': resultado,
                            'detalles': detalles,
                            'tipo_coincidencia': 'parcial'
                        })
            
            # Estrategia 3: Si aún no hay coincidencias, buscar por similitud (últimos dígitos)
            if not coincidencias and len(codigo_limpio) >= 8:
                ultimos_digitos = codigo_limpio[-8:]  # Últimos 8 dígitos
                for clave in self.indice_codigos:
                    codigo_en_clave = clave.split('|')[0] if '|' in clave else ""
                    if codigo_en_clave.endswith(ultimos_digitos):
                        item_code = self.indice_codigos[clave]
                        resultado = self.indice_resultados.get(clave, "")
                        detalles = self.indice_detalles.get(clave, "")
                        coincidencias.append({
                            'clave': clave,
                            'item': item_code,
                            'resultado': resultado,
                            'detalles': detalles,
                            'tipo_coincidencia': 'final'
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
                    tipo_coincidencia = coincidencias[0]['tipo_coincidencia']
                    
                    # Extraer NOM de los detalles
                    nom_info = "NOM: No disponible"
                    if "NOM:" in detalles:
                        nom_parts = detalles.split("NOM:")
                        if len(nom_parts) > 1:
                            nom_part = nom_parts[1].split(" - ")[0].strip()
                            if nom_part and nom_part.lower() not in ["nan", "none", ""]:
                                nom_info = f"NOM: {nom_part}"
                    
                    # Mostrar tipo de coincidencia si no es exacta
                    tipo_info = ""
                    if tipo_coincidencia != 'exacta':
                        tipo_info = f" (Coincidencia {tipo_coincidencia})"
                    
                    self.clave_valor.configure(text=f"ITEM: {item}{tipo_info}")
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
                        tipo_info = f" [{coinci['tipo_coincidencia']}]" if coinci['tipo_coincidencia'] != 'exacta' else ""
                        detalles_texto += f"{i}. Item: {coinci['item']}{tipo_info} - {coinci['resultado']}\n"
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
                   font=("Segoe UI", 16, "bold"), text_color="#00FFAA", fg_color="#000000").pack(pady=(0, 10))
        
        # Frame para buscador
        buscador_frame = ct.CTkFrame(main_frame, fg_color="#111111")
        buscador_frame.pack(fill="x", pady=(0, 10), padx=10)
        
        ct.CTkLabel(buscador_frame, text="Buscar Item:", 
                   font=("Segoe UI", 12), text_color="#FFAA00", fg_color="#111111").pack(side="left", padx=(10, 5))
        
        # Variable para el buscador
        busqueda_var = StringVar()
        busqueda_entry = ct.CTkEntry(buscador_frame, textvariable=busqueda_var, 
                                   font=("Segoe UI", 12), width=300, height=32, 
                                   corner_radius=8, border_width=2, border_color="#00FFAA", 
                                   fg_color="#000000", text_color="#00FFAA", 
                                   placeholder_text="Escriba para buscar items...")
        busqueda_entry.pack(side="left", padx=(0, 10))
        
        # Botón para limpiar búsqueda
        def limpiar_busqueda():
            busqueda_var.set("")
        
        ct.CTkButton(buscador_frame, text="Limpiar", command=limpiar_busqueda,
                    font=("Segoe UI", 11), fg_color="#000000", hover_color="#333333", 
                    border_width=2, border_color="#FF5555", text_color="#FF5555", 
                    corner_radius=8, width=80, height=32).pack(side="left")
        
        # Frame scrollable para los items 
        items_frame = ct.CTkScrollableFrame(main_frame, fg_color="#000000", height=350)
        items_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Opciones disponibles
        tipos_proceso = ["CUMPLE", "ADHERIBLE", "COSTURA", "SIN NORMA", ""]
        criterios = ["REVISADO", "INSTRUCCIONES DE CUIDADO", "INSUMOS", "PAIS DE ORIGEN", "TALLA", "IMPORTADOR", "MARCA", "EDAD RECOMENDADA", "INGRESAR TEXTO", ""]
        
        # Variables para almacenar los cambios
        cambios_items = {}
        
        # Lista para almacenar referencias a los widgets de items
        item_widgets = []
        
        # Función para filtrar items
        def filtrar_items(*args):
            busqueda = busqueda_var.get().lower().strip()
            
            # Ocultar/mostrar widgets según la búsqueda
            for widget_info in item_widgets:
                item_text = widget_info['item_text'].lower()
                if not busqueda or busqueda in item_text:
                    widget_info['frame'].pack(fill="x", pady=5, padx=10)
                else:
                    widget_info['frame'].pack_forget()
        
        # Vincular la función de filtrado al cambio de texto
        busqueda_var.trace("w", filtrar_items)
        
        # Crear widgets para cada item
        for i, resultado in enumerate(self.resultados_actuales):
            item_frame = ct.CTkFrame(items_frame, fg_color="#111111", corner_radius=8)
            item_frame.pack(fill="x", pady=3, padx=10)
            
            # Almacenar referencia para filtrado
            item_widgets.append({
                'frame': item_frame,
                'item_text': f"Item: {resultado['item']} - Estado actual: {resultado['resultado']}"
            })
            
            # Información del item
            item_info = ct.CTkLabel(item_frame, 
                                  text=f"Item: {resultado['item']} - Estado actual: {resultado['resultado']}", 
                                  font=("Segoe UI", 12, "bold"), text_color="#00FFAA", fg_color="#111111")
            item_info.pack(anchor="w", padx=10, pady=(8, 3))
            
            # Detalles
            detalles_label = ct.CTkLabel(item_frame, 
                                       text=f"Detalles: {resultado['detalles'][:150]}...", 
                                       font=("Segoe UI", 10), text_color="#55DDFF", fg_color="#111111", wraplength=900)
            detalles_label.pack(anchor="w", padx=10, pady=(0, 8))
            
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
            controles_frame.pack(fill="x", padx=10, pady=(0, 8))
            
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
            
            # Frame para contener el menú y el campo de texto
            criterio_container = ct.CTkFrame(controles_frame, fg_color="#111111")
            criterio_container.pack(side="left", padx=(0, 20))
            
            # Crear el campo de texto (inicialmente oculto)
            texto_personalizado_var = StringVar()
            criterio_entry = ct.CTkEntry(criterio_container, 
                                       textvariable=texto_personalizado_var,
                                       font=("Segoe UI", 11), 
                                       width=120, height=32,
                                       corner_radius=8, 
                                       border_width=2, 
                                       border_color="#00FFAA",
                                       fg_color="#000000", 
                                       text_color="#00FFAA",
                                       placeholder_text="INGRESE TEXTO...")
            
            # Función para convertir a mayúsculas
            def convertir_mayusculas(*args):
                texto = texto_personalizado_var.get()
                if texto and texto != texto.upper():
                    texto_personalizado_var.set(texto.upper())
            
            # Vincular la función al cambio de texto
            texto_personalizado_var.trace("w", convertir_mayusculas)
            
            # Crear el menú desplegable
            criterio_menu = ct.CTkOptionMenu(criterio_container, 
                                           values=criterios, 
                                           variable=criterio_var,
                                           fg_color="#000000", 
                                           button_color="#00FFAA",
                                           button_hover_color="#00DD88",
                                           text_color="#00FFAA",
                                           width=120)
            criterio_menu.pack(side="left")
            
            # Función para manejar la selección del menú (definida dentro del loop para cada item)
            def crear_on_menu_select(menu_widget, entry_widget, var_widget):
                def on_menu_select(selection):
                    if selection == "INGRESAR TEXTO":
                        menu_widget.pack_forget()
                        entry_widget.pack(side="left")
                        entry_widget.focus_set()
                    else:
                        entry_widget.pack_forget()
                        menu_widget.pack(side="left")
                        # Limpiar el texto personalizado si se selecciona otra opción
                        if selection != "INGRESAR TEXTO":
                            var_widget.set("")
                return on_menu_select
            
            # Función para manejar teclas en el campo de texto (definida dentro del loop)
            def crear_manejar_teclas(entry_widget, menu_widget, criterio_var_widget, texto_var_widget):
                def manejar_teclas(event):
                    if event.keysym == 'Escape':
                        # ESC: Volver al menú desplegable
                        entry_widget.pack_forget()
                        menu_widget.pack(side="left")
                        criterio_var_widget.set("")  # Limpiar la selección
                        texto_var_widget.set("")  # Limpiar el texto
                        return "break"  # Prevenir propagación del evento
                    elif event.keysym == 'Return':
                        # ENTER: Confirmar el texto
                        texto_ingresado = texto_var_widget.get().strip()
                        if texto_ingresado:
                            # Si hay texto, mantener el campo visible y confirmar
                            criterio_var_widget.set("INGRESAR TEXTO")
                            # Asegurar que el texto esté en mayúsculas
                            texto_var_widget.set(texto_ingresado.upper())
                            # Quitar el foco del campo
                            entry_widget.master.focus_set()
                            # También quitar el foco de la ventana principal
                            editor_window.focus_set()
                        else:
                            # Si no hay texto, volver al menú sin confirmar
                            criterio_var_widget.set("")
                            entry_widget.pack_forget()
                            menu_widget.pack(side="left")
                        return "break"  # Prevenir propagación del evento
                    return None
                return manejar_teclas
            
            # Crear y vincular la función de manejo de teclas
            manejar_teclas = crear_manejar_teclas(criterio_entry, criterio_menu, criterio_var, texto_personalizado_var)
            criterio_entry.bind('<Key>', manejar_teclas)
            
            # Configurar el callback del menú
            on_menu_select = crear_on_menu_select(criterio_menu, criterio_entry, texto_personalizado_var)
            criterio_menu.configure(command=on_menu_select)
            
            # Si el criterio actual no está en la lista predefinida, mostrar campo de texto
            if criterio_actual and criterio_actual not in criterios[:-2]:  # Excluir "INGRESAR TEXTO" y ""
                texto_personalizado_var.set(criterio_actual)
                criterio_var.set("INGRESAR TEXTO")
                criterio_menu.pack_forget()
                criterio_entry.pack(side="left")
            
            # Almacenar referencia para acceso posterior
            cambios_items[resultado['clave']] = {
                'item': resultado['item'],
                'tipo_original': tipo_actual,
                'criterio_original': criterio_actual,
                'tipo_var': tipo_var,
                'criterio_var': criterio_var,
                'texto_personalizado_var': texto_personalizado_var,
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
        """Guarda los cambios realizados en el archivo de tipos de procesos"""
        try:
            reporte_path = self.config_data.get("reporte", "")
            if not reporte_path or not os.path.exists(reporte_path):
                messagebox.showerror("Error", "No se encontró el archivo de tipos de procesos.")
                return
            
            # Leer el archivo de tipos de procesos original
            df_reporte = pd.read_excel(reporte_path, dtype=str)
            
            # Contador de cambios
            cambios_realizados = 0
            
            # Aplicar cambios al reporte
            for clave, info in cambios_items.items():
                item = info['item']
                nuevo_tipo = info['tipo_var'].get()
                nuevo_criterio = info['criterio_var'].get()
                
                # Si el criterio es "INGRESAR TEXTO", usar el texto personalizado
                if nuevo_criterio == "INGRESAR TEXTO":
                    nuevo_criterio = info['texto_personalizado_var'].get()
                
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
                # Guardar el archivo de tipos de procesos actualizado
                try:
                    df_reporte.to_excel(reporte_path, index=False)
                    messagebox.showinfo("Éxito", f"Se guardaron {cambios_realizados} cambios en el archivo de tipos de procesos.")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar el archivo de tipos de procesos: {str(e)}")
                    return
                
                # Actualizar el índice local y recargar en memoria
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
                
                # Mostrar mensaje de confirmación
                messagebox.showinfo("Actualización Completa", 
                                  f"Se actualizaron {cambios_realizados} items en el reporte.\n"
                                  "El índice ha sido regenerado automáticamente.")
                
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
        ct.CTkLabel(frame, text="Tipos de Procesos:", text_color="#00FFAA", font=("Segoe UI", 14, "bold"), fg_color="#000000").pack(anchor="w", padx=20, pady=(10,0))
        self.ruta_reporte_label = ct.CTkLabel(frame, textvariable=self.ruta_reporte_var, text_color="#55DDFF", wraplength=600, fg_color="#000000")
        self.ruta_reporte_label.pack(anchor="w", padx=20)
        ct.CTkButton(frame, text="Cargar Tipos de Procesos", command=self.cargar_archivo_reporte, font=("Segoe UI", 13, "bold"), fg_color="#000000", hover_color="#111111", border_width=2, border_color="#00FFAA", text_color="#00FFAA", corner_radius=12, width=260, height=36).pack(pady=5, padx=20, anchor="w")

    def cargar_archivo_clp(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xls;*.xlsx"), ("Todos", "*.*")])
        if ruta:
            self.config_data["clp"] = ruta
            self.ruta_clp_var.set(ruta)
            self.guardar_config()
            # Actualizar etiquetas después de cargar archivo
            self.actualizar_etiquetas_configuracion()

    def cargar_archivo_reporte(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xls;*.xlsx"), ("Todos", "*.*")])
        if ruta:
            self.config_data["reporte"] = ruta
            self.ruta_reporte_var.set(ruta)
            # Guardar también el nombre del archivo para mostrar
            self.config_data["nombre_archivo_reporte"] = ruta
            self.guardar_config()
            # Actualizar etiquetas después de cargar archivo
            self.actualizar_etiquetas_configuracion()

    def debug_configuracion(self):
        """Muestra información de debug de la configuración"""
        try:
            debug_info = f"""
DEBUG DE CONFIGURACIÓN:

Archivo CLP: {self.config_data.get('clp', 'No configurado')}
Archivo Reporte: {self.config_data.get('reporte', 'No configurado')}
Nombre Archivo Reporte: {self.config_data.get('nombre_archivo_reporte', 'No configurado')}
Última Actualización: {self.config_data.get('ultima_actualizacion', 'No configurado')}

Verificaciones:
- CLP existe: {os.path.exists(self.config_data.get('clp', '')) if self.config_data.get('clp') else False}
- Reporte existe: {os.path.exists(self.config_data.get('reporte', '')) if self.config_data.get('reporte') else False}
- Nombre archivo reporte existe: {os.path.exists(self.config_data.get('nombre_archivo_reporte', '')) if self.config_data.get('nombre_archivo_reporte') else False}

Ruta de configuración: {CONFIG_PATH}
Ruta de índice: {INDICE_PATH}
"""
            messagebox.showinfo("Debug Configuración", debug_info)
        except Exception as e:
            messagebox.showerror("Error Debug", f"Error al mostrar debug: {str(e)}")

    def diagnosticar_codigo(self, codigo_limpio: str) -> str:
        """Función de diagnóstico para códigos que no se encuentran"""
        try:
            logger.info(f"Diagnosticando código: {codigo_limpio}")
            
            if not self.indice_codigos:
                return "El índice no está cargado. Por favor, actualice el índice."
            
            # Verificar si el código está en el índice
            codigos_en_indice = []
            for clave in self.indice_codigos:
                codigo_en_clave = clave.split('|')[0] if '|' in clave else ""
                codigos_en_indice.append(codigo_en_clave)
            
            # Buscar similitudes
            similitudes = []
            for codigo in codigos_en_indice:
                if codigo_limpio in codigo or codigo in codigo_limpio:
                    similitudes.append(codigo)
            
            # Buscar por últimos dígitos
            ultimos_digitos = codigo_limpio[-6:] if len(codigo_limpio) >= 6 else codigo_limpio
            coincidencias_finales = []
            for codigo in codigos_en_indice:
                if codigo.endswith(ultimos_digitos):
                    coincidencias_finales.append(codigo)
            
            diagnostico = f"""
DIAGNÓSTICO PARA CÓDIGO: {codigo_limpio}

Total de códigos en índice: {len(codigos_en_indice)}
Código buscado: {codigo_limpio}

Similitudes encontradas: {len(similitudes)}
{chr(10).join(similitudes[:10]) if similitudes else 'Ninguna'}

Coincidencias por últimos 6 dígitos: {len(coincidencias_finales)}
{chr(10).join(coincidencias_finales[:10]) if coincidencias_finales else 'Ninguna'}

Primeros 10 códigos en índice:
{chr(10).join(codigos_en_indice[:10])}
"""
            return diagnostico
        except Exception as e:
            return f"Error en diagnóstico: {str(e)}"

# Crear directorio de caché en el directorio actual si no existe
import os
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR)
    except Exception as e:
        # Si no se puede crear en el directorio actual, usar directorio de usuario
        import tempfile
        user_cache_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "EscanerVC")
        if not os.path.exists(user_cache_dir):
            try:
                os.makedirs(user_cache_dir)
                CACHE_DIR = user_cache_dir
            except Exception:
                # Último recurso: directorio temporal del sistema
                CACHE_DIR = tempfile.gettempdir()

CONFIG_PATH = os.path.join(CACHE_DIR, "config.json")
INDICE_PATH = os.path.join(CACHE_DIR, "indice.csv")

if __name__ == "__main__":
    root = ct.CTk()
    root.title("Escáner de Códigos V&C")
    root.geometry("900x700")
    root.resizable(True, True)
    
    # Configurar icono de la aplicación
    try:
        icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'Escaner.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
            # También configurar para la barra de tareas en Windows
            try:
                import ctypes
                myappid = 'vandc.escaner.1.0'  # ID único para la aplicación
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except:
                pass
        else:
            # Si no existe el .ico, intentar con el .png
            png_path = os.path.join(os.path.dirname(__file__), 'resources', 'Logo (2).png')
            if os.path.exists(png_path):
                # Convertir PNG a ICO temporalmente para Windows
                try:
                    from PIL import Image
                    img = Image.open(png_path)
                    # Crear un archivo ICO temporal
                    temp_ico = os.path.join(os.path.dirname(__file__), 'temp_icon.ico')
                    img.save(temp_ico, format='ICO')
                    root.iconbitmap(temp_ico)
                    
                    # Configurar para la barra de tareas
                    try:
                        import ctypes
                        myappid = 'vandc.escaner.1.0'
                        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                    except:
                        pass
                    
                    # Limpiar archivo temporal después de un tiempo
                    import threading
                    import time
                    def cleanup_temp_ico():
                        time.sleep(2)
                        try:
                            if os.path.exists(temp_ico):
                                os.remove(temp_ico)
                        except:
                            pass
                    threading.Thread(target=cleanup_temp_ico, daemon=True).start()
                except Exception as e:
                    print(f"No se pudo configurar el icono: {e}")
    except Exception as e:
        print(f"Error al configurar icono: {e}")
    
    # Configurar favicon para la barra de título (Windows)
    try:
        if os.path.exists(icon_path):
            # Usar el icono existente
            pass
        elif os.path.exists(png_path):
            # Crear un favicon temporal pequeño
            try:
                from PIL import Image
                img = Image.open(png_path)
                # Redimensionar para favicon (16x16, 32x32)
                favicon_sizes = [(16, 16), (32, 32)]
                favicon_images = []
                for size in favicon_sizes:
                    favicon_img = img.resize(size, Image.Resampling.LANCZOS)
                    favicon_images.append(favicon_img)
                
                # Guardar como ICO con múltiples tamaños
                temp_favicon = os.path.join(os.path.dirname(__file__), 'temp_favicon.ico')
                favicon_images[0].save(temp_favicon, format='ICO', sizes=favicon_sizes)
                
                # Limpiar favicon temporal
                def cleanup_favicon():
                    time.sleep(3)
                    try:
                        if os.path.exists(temp_favicon):
                            os.remove(temp_favicon)
                    except:
                        pass
                threading.Thread(target=cleanup_favicon, daemon=True).start()
            except Exception as e:
                print(f"No se pudo crear favicon: {e}")
    except Exception as e:
        print(f"Error al configurar favicon: {e}")
    
    app = BuscadorApp(root)
    
    # Configurar el protocolo de cierre para guardar configuración
    def on_closing():
        try:
            app.guardar_config()
            root.destroy()
        except Exception as e:
            print(f"Error al cerrar: {e}")
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop() 
    