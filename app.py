# app.py (versión final con resultados alineados a la izquierda)

import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import bibtexparser
import os
import csv

from similarity_calculator import find_similar_documents

def parse_ris_file(file_path):
    data = {}
    abstract_keys = ["AB", "N1"]
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("TI  - ") or line.startswith("T1  - "):
                data['title'] = line[6:]
            elif any(line.startswith(f"{key}  - ") for key in abstract_keys) and 'abstract' not in data:
                data['abstract'] = line[6:]
    if 'title' not in data: data['title'] = ''
    if 'abstract' not in data: data['abstract'] = ''
    return [data]

class SimilarityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Artículos Similares v3.1")
        self.root.geometry("900x700")

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.bib_data = None
        self.raw_data = self.load_raw_corpus()

        main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=10)
        options_frame = ctk.CTkFrame(top_frame)
        options_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(options_frame, text="Corpus:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.corpus_var = ctk.StringVar(value="arxiv")
        self.corpus_combo = ctk.CTkComboBox(options_frame, variable=self.corpus_var, values=["arxiv", "pubmed"], state="readonly")
        self.corpus_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(options_frame, text="Features:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.feature_var = ctk.StringVar(value="unigram")
        self.feature_combo = ctk.CTkComboBox(options_frame, variable=self.feature_var, values=["unigram", "bigram"], state="readonly")
        self.feature_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(options_frame, text="Representación:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.vector_var = ctk.StringVar(value="tfidf")
        self.vector_combo = ctk.CTkComboBox(options_frame, variable=self.vector_var, values=["freq", "binary", "tfidf"], state="readonly")
        self.vector_combo.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        options_frame.columnconfigure((1, 3), weight=1)
        file_frame = ctk.CTkFrame(top_frame)
        file_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.select_file_btn = ctk.CTkButton(file_frame, text="Seleccionar Archivo de Consulta (.bib o .ris)", command=self.load_file)
        self.select_file_btn.pack(fill="x", padx=10, pady=10)
        self.query_label = ctk.CTkLabel(file_frame, text="Archivo no cargado.", text_color="gray", wraplength=350, justify="center")
        self.query_label.pack(fill="x", padx=10, pady=(0, 10))
        self.search_btn = ctk.CTkButton(main_frame, text="Buscar Documentos Similares", command=self.run_search, state="disabled", height=40)
        self.search_btn.pack(fill="x", padx=10, pady=5)
        self.results_title_label = ctk.CTkLabel(main_frame, text="Resultados de la Búsqueda", font=ctk.CTkFont(size=16, weight="bold"))
        self.results_title_label.pack(fill="x", padx=10, pady=(10, 0))
        self.results_frame = ctk.CTkScrollableFrame(main_frame, corner_radius=10)
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def load_raw_corpus(self):
        data = {}
        try:
            print("Cargando corpus raw de Arxiv (con separador TAB)...")
            data['arxiv'] = pd.read_csv('raw_corpus/arxiv_raw_corpus.csv', sep='\t', engine='python')
            print("Cargando corpus raw de Pubmed (con separador TAB)...")
            data['pubmed'] = pd.read_csv('raw_corpus/pubmed_raw_corpus.csv', sep='\t', engine='python')
            print("Corpus raw cargados correctamente.")
        except FileNotFoundError as e:
            messagebox.showerror("Error Crítico", f"No se encontró el archivo de corpus raw: {e.filename}\nLa aplicación no puede continuar.")
            if self.root: self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Ocurrió un error al cargar los corpus raw: {e}\nLa aplicación no puede continuar.")
            if self.root: self.root.destroy()
        return data

    def load_file(self):
        file_path = filedialog.askopenfilename(title="Selecciona un archivo de referencia", filetypes=[("Reference Files", "*.bib *.ris"), ("All files", "*.*")])
        if not file_path: return
        try:
            _, file_extension = os.path.splitext(file_path)
            if file_extension.lower() == '.bib':
                with open(file_path, 'r', encoding='utf-8') as bibfile:
                    bib_database = bibtexparser.load(bibfile)
                entries = bib_database.entries
            elif file_extension.lower() == '.ris':
                entries = parse_ris_file(file_path)
            else:
                messagebox.showerror("Error", f"Extensión de archivo no soportada: {file_extension}")
                return
            if not entries:
                messagebox.showerror("Error", "El archivo de referencia no contiene entradas válidas.")
                return
            self.bib_data = entries[0]
            title_display = self.bib_data.get('title', 'Título no encontrado')
            self.query_label.configure(text=f"Archivo Cargado: {title_display}")
            self.search_btn.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Error al leer archivo", f"No se pudo procesar el archivo.\nError: {e}")
            self.bib_data = None
            self.search_btn.configure(state="disabled")

    def run_search(self):
        if not self.bib_data:
            messagebox.showerror("Error", "No hay ningún archivo cargado.")
            return

        for widget in self.results_frame.winfo_children():
            widget.destroy()

        title_text = self.bib_data.get('title', '')
        abstract_text = self.bib_data.get('abstract', '')
        combined_query_text = f"{title_text} {abstract_text}".strip()
        if not combined_query_text:
            messagebox.showwarning("Advertencia", "El título y el abstracto del archivo están vacíos.")
            return

        corpus = self.corpus_var.get()
        feature = self.feature_var.get()
        vector = self.vector_var.get()
        
        results = find_similar_documents(combined_query_text, corpus, feature, vector)

        if not results:
            ctk.CTkLabel(self.results_frame, text="No se encontraron resultados o ocurrió un error.").pack(pady=10)
            return

        for i, (doc_id, score) in enumerate(results):
            result_entry_frame = ctk.CTkFrame(self.results_frame)
            # --- LA ÚNICA LÍNEA MODIFICADA ---
            result_entry_frame.pack(fill="x", pady=5, padx=5, anchor="w")

            doc_title = self.raw_data[corpus].iloc[doc_id]['Title']
            
            label_text = f"{i+1}. Similitud: {score:.4f}\n{doc_title}"
            
            ctk.CTkLabel(result_entry_frame, text=label_text, justify="left", wraplength=600).pack(side="left", fill="x", expand=True, padx=10, pady=5)
            
            view_button = ctk.CTkButton(result_entry_frame, text="Ver Detalles", width=120,
                                        command=lambda c=corpus, index=doc_id: self.view_document_details(c, index))
            view_button.pack(side="right", padx=10, pady=5)

    def view_document_details(self, corpus, index):
        details_window = ctk.CTkToplevel(self.root)
        details_window.title("Detalles del Documento")
        details_window.geometry("700x500")

        try:
            doc_data = self.raw_data[corpus].iloc[index]
            
            details_text = (
                f"TÍTULO:\n{doc_data.get('Title', 'N/A')}\n\n"
                f"AUTORES:\n{doc_data.get('Authors', 'N/A')}\n\n"
                f"DOI:\n{doc_data.get('DOI', 'N/A')}\n\n"
                f"FECHA:\n{doc_data.get('Date', 'N/A')}\n\n"
                f"SECCIÓN:\n{doc_data.get('Section', 'N/A')}\n\n"
                f"ABSTRACT:\n{doc_data.get('Abstract', 'N/A')}"
            )

            textbox = ctk.CTkTextbox(details_window, wrap="word", font=("Arial", 12))
            textbox.pack(fill="both", expand=True, padx=10, pady=10)
            textbox.insert("1.0", details_text)
            textbox.configure(state="disabled")

        except Exception as e:
            ctk.CTkLabel(details_window, text=f"No se pudieron cargar los detalles.\nError: {e}").pack(pady=20)
        
        details_window.transient(self.root)
        details_window.grab_set()

if __name__ == "__main__":
    root = ctk.CTk()
    app = SimilarityApp(root)
    root.mainloop()