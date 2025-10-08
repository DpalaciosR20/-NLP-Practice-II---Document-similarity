# app.py (versión con la lógica de búsqueda corregida)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import bibtexparser
import os

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
    if 'title' not in data: data['title'] = '' # Devolver string vacío si no se encuentra
    if 'abstract' not in data: data['abstract'] = '' # Devolver string vacío si no se encuentra
    return [data]

class SimilarityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Artículos Similares")
        self.root.geometry("800x600")
        self.bib_data = None
        self.query_content = tk.StringVar()
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        options_frame = ttk.LabelFrame(main_frame, text="Configuración de Búsqueda", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        ttk.Label(options_frame, text="Corpus:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.corpus_var = tk.StringVar(value="arxiv")
        self.corpus_combo = ttk.Combobox(options_frame, textvariable=self.corpus_var, values=["arxiv", "pubmed"], state="readonly")
        self.corpus_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(options_frame, text="Contenido Comparativo:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.content_var = tk.StringVar(value="Abstract")
        self.content_combo = ttk.Combobox(options_frame, textvariable=self.content_var, values=["Title", "Abstract"], state="readonly")
        self.content_combo.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        self.content_combo.bind("<<ComboboxSelected>>", self.update_query_text)
        ttk.Label(options_frame, text="Features:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.feature_var = tk.StringVar(value="unigram")
        self.feature_combo = ttk.Combobox(options_frame, textvariable=self.feature_var, values=["unigram", "bigram"], state="readonly")
        self.feature_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(options_frame, text="Representación:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.vector_var = tk.StringVar(value="tfidf")
        self.vector_combo = ttk.Combobox(options_frame, textvariable=self.vector_var, values=["freq", "binary", "tfidf"], state="readonly")
        self.vector_combo.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(3, weight=1)
        file_frame = ttk.LabelFrame(main_frame, text="Documento de Entrada", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        self.select_file_btn = ttk.Button(file_frame, text="Seleccionar Archivo (.bib o .ris)", command=self.load_file)
        self.select_file_btn.pack(fill=tk.X)
        self.query_text_area = tk.Text(file_frame, height=8, wrap="word", state="disabled")
        self.query_text_area.pack(fill=tk.X, pady=5, expand=True)
        self.search_btn = ttk.Button(main_frame, text="Buscar Documentos Similares", command=self.run_search, state="disabled")
        self.search_btn.pack(fill=tk.X, pady=10)
        results_frame = ttk.LabelFrame(main_frame, text="Resultados (10 más similares)", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.results_text_area = tk.Text(results_frame, height=15, wrap="word", state="disabled")
        self.results_text_area.pack(fill=tk.BOTH, expand=True)

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
            self.update_query_text()
            self.search_btn.config(state="normal")
        except Exception as e:
            messagebox.showerror("Error al leer archivo", f"No se pudo procesar el archivo.\nError: {e}")
            self.bib_data = None
            self.search_btn.config(state="disabled")

    def update_query_text(self, event=None):
        if not self.bib_data: return
        content_type = self.content_var.get().lower()
        text_to_display = self.bib_data.get(content_type, f"'{content_type.capitalize()}' no encontrado en el archivo.")
        self.query_text_area.config(state="normal")
        self.query_text_area.delete("1.0", tk.END)
        self.query_text_area.insert("1.0", text_to_display)
        self.query_text_area.config(state="disabled")
        self.query_content.set(text_to_display)

    # --- MÉTODO MODIFICADO ---
    def run_search(self):
        if not self.bib_data:
            messagebox.showerror("Error", "No hay ningún archivo cargado.")
            return

        # <<-- CAMBIO CLAVE: CONSTRUIMOS EL TEXTO COMBINADO -->>
        # Ignoramos la selección del ComboBox y en su lugar combinamos Título y Abstracto,
        # tal como se hizo al crear los archivos .pkl.
        title_text = self.bib_data.get('title', '')
        abstract_text = self.bib_data.get('abstract', '')
        
        # Combinamos Título y Abstracto con un espacio en medio
        combined_query_text = f"{title_text} {abstract_text}".strip()

        if not combined_query_text:
            messagebox.showwarning("Advertencia", "El título y el abstracto del archivo están vacíos.")
            return

        corpus = self.corpus_var.get()
        feature = self.feature_var.get()
        vector = self.vector_var.get()
        
        # Enviamos el texto combinado a la función de similitud
        results = find_similar_documents(combined_query_text, corpus, feature, vector)

        display_text = "No se encontraron resultados o ocurrió un error.\nRevisa la consola para más detalles."
        if results:
            display_text = "Ranking | Índice del Documento | Similitud (Coseno)\n"
            display_text += "="*60 + "\n"
            for i, (doc_id, score) in enumerate(results):
                display_text += f"{i+1:<8}| {doc_id:<22} | {score:.6f}\n"
        
        self.results_text_area.config(state="normal")
        self.results_text_area.delete("1.0", tk.END)
        self.results_text_area.insert("1.0", display_text)
        self.results_text_area.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimilarityApp(root)
    root.mainloop()