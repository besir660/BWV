import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
import re

# Concept dictionary for regex expansion
CONCEPT_MAP = {
    "strings": "violin|cello|viola|bass|gamba|lute",
    "woodwinds": "flute|oboe|recorder|bassoon",
    "brass": "trumpet|horn|cornetto|trombone",
    "keyboard": "harpsichord|organ|clavier|cembalo",
    "vocal": "soprano|alto|tenor|bass|choir|chorus",
    "passion": "matthew|john|luke|mark"
}

# The Wikipedia legend mapping for column '2a'
CHAPTER_LEGEND = {
    "All Works (Clear Filter)": "",
    "1. Cantatas": "^1\\.?$",
    "2. Motets": "^2\\.?$",
    "3. Masses, Mass movements, Magnificat": "^3\\.?$",
    "4. Passions, Oratorios": "^4\\.?$",
    "5. Four-part chorales": "^5\\.?$",
    "6. Songs, Arias and Quodlibet": "^6\\.?$",
    "7. Works for organ": "^7\\.?$",
    "8. Keyboard compositions": "^8\\.?$",
    "9. Lute compositions": "^9\\.?$",
    "10. Chamber music": "^10\\.?$",
    "11. Orchestral works": "^11\\.?$",
    "12. Canons": "^12\\.?$",
    "13. Late contrapuntal works": "^13\\.?$",
    "I. Fragments / Lost Works (Anh. I)": "^I$",
    "II. Doubtful Authenticity (Anh. II)": "^II$",
    "III. Spurious Works (Anh. III)": "^III$"
}

def load_data(filename="bach_bwv_catalog.csv"):
    try:
        df = pd.read_csv(filename)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.fillna("") 
        return df
    except FileNotFoundError:
        messagebox.showerror("Error", f"Could not find {filename}")
        return None

class BWVExplorerApp:
    def __init__(self, root, df):
        self.root = root
        self.root.title("BWV Catalog Graphical Explorer")
        self.root.geometry("1200x750")
        
        try:
            self.root.iconbitmap("bwv.ico")
        except Exception:
            pass
            
        self.df = df
        self.filter_entries = {}
        
        self.setup_ui()
        self.populate_tree(self.df)

    def setup_ui(self):
        # 1. High-Level Category Filter (Column 2a)
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text="BWV Chapter (Column 2a):", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.chapter_var = tk.StringVar()
        self.chapter_dropdown = ttk.Combobox(
            top_frame, 
            textvariable=self.chapter_var,
            values=list(CHAPTER_LEGEND.keys()),
            width=45,
            state="readonly"
        )
        self.chapter_dropdown.current(0)
        self.chapter_dropdown.pack(side=tk.LEFT, padx=5)
        self.chapter_dropdown.bind("<<ComboboxSelected>>", lambda event: self.execute_search())

        # 2. Dynamic Text Filters
        filter_frame = ttk.LabelFrame(self.root, text="Filter by Field (Supports exact text, Concepts, or Regex)")
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        search_columns = [col for col in self.df.columns if col.lower() != '2a']
        
        for i, col in enumerate(search_columns):
            row = i // 4
            grid_col = (i % 4) * 2
            
            ttk.Label(filter_frame, text=f"{col}:").grid(row=row, column=grid_col, padx=5, pady=5, sticky=tk.E)
            entry = ttk.Entry(filter_frame, width=22)
            entry.grid(row=row, column=grid_col+1, padx=5, pady=5, sticky=tk.W)
            
            entry.bind('<Return>', lambda event: self.execute_search())
            self.filter_entries[col] = entry

        # 3. Action Buttons & Status
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Native ttk styles apply the ttkbootstrap accent colors safely
        ttk.Button(btn_frame, text="Apply Filters", style="success.TButton", command=self.execute_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Filters", style="secondary.TButton", command=self.reset_data).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(btn_frame, text=f"Total entries: {len(self.df)}", font=("Helvetica", 10, "italic"))
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # 4. Data Table (Treeview)
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=list(self.df.columns), show='headings')
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for col in self.df.columns:
            self.tree.heading(col, text=col)
            width = 300 if "title" in col.lower() or "name" in col.lower() else 120
            self.tree.column(col, width=width, anchor=tk.W)

    def populate_tree(self, dataframe):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for index, row in dataframe.iterrows():
            self.tree.insert("", tk.END, values=list(row))
            
        self.status_label.config(text=f"Showing: {len(dataframe)} entries")

    def execute_search(self):
        mask = pd.Series([True] * len(self.df), index=self.df.index)
        
        selected_chapter = self.chapter_var.get()
        chapter_pattern = CHAPTER_LEGEND.get(selected_chapter, "")
        
        if chapter_pattern and '2a' in self.df.columns:
            col_mask = self.df['2a'].astype(str).str.contains(chapter_pattern, regex=True, na=False)
            mask = mask & col_mask

        for col, entry in self.filter_entries.items():
            query = entry.get().strip().lower()
            if query:
                pattern = CONCEPT_MAP.get(query, query)
                try:
                    col_mask = self.df[col].astype(str).str.contains(pattern, flags=re.IGNORECASE, regex=True)
                    mask = mask & col_mask
                except re.error:
                    messagebox.showwarning("Regex Error", f"Invalid regular expression in column '{col}'.")
                    return
        
        filtered_df = self.df[mask]
        self.populate_tree(filtered_df)

    def reset_data(self):
        self.chapter_dropdown.current(0)
        for entry in self.filter_entries.values():
            entry.delete(0, tk.END)
        self.populate_tree(self.df)

if __name__ == "__main__":
    data = load_data()
    if data is not None:
        root = tb.Window(themename="darkly")
        app = BWVExplorerApp(root, data)
        root.mainloop()