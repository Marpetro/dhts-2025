import matplotlib.pyplot as plt
import random
import csv
import time
import numpy as np
from pathlib import Path
from typing import List, Dict

# Imports
from src.pastry.network import PastryNetwork
from src.chord.chord_network import ChordNetwork
from src.common.hash_utils import key_for_title, normalize_title
from src.pastry.local_index import MovieRecord

# --- Helper Functions ---
def key_id_hex_from_title(title: str) -> str:
    return f"{key_for_title(title, bits=128):032x}"

def load_real_movies(limit: int) -> List[MovieRecord]:
    # Βεβαιώσου ότι το path είναι σωστό
    dataset_folder = Path(r"C:\Users\HP\OneDrive\Έγγραφα\GitHub\dhts-2025\movies_dataset_cleaned")
    csv_path = dataset_folder / "data_movies_clean.csv" 
    
    movies = []
    if not csv_path.exists():
        print(f"⚠️ Δεν βρέθηκε το αρχείο: {csv_path}")
        return []

    with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=';') # Ελληνικό CSV
        for i, row in enumerate(reader):
            if i >= limit: break
            clean_row = {str(k).lower().strip(): v for k, v in row.items() if k is not None}
            title = clean_row.get("title") or clean_row.get("original_title")
            if not title: continue
            try:
                movies.append(MovieRecord(
                    movie_id=str(clean_row.get("id", i)),
                    title=title.strip(),
                    popularity=float(clean_row.get("popularity", 0) or 0),
                    vote_average=float(clean_row.get("vote_average", 0) or 0),
                    runtime=int(float(clean_row.get("runtime", 0) or 0))
                ))
            except: continue
    print(f"✅ Loaded {len(movies)} movies.")
    return movies

def run_full_experiment():
    # 1. Ρυθμίσεις Πειράματος
    NODE_COUNTS = [50, 100, 200, 500]  # Διαφορετικά μεγέθη δικτύου
    N_KEYS = 1000                      # Ταινίες για Insert
    
    movies = load_real_movies(N_KEYS)
    if not movies: return

    # Δομές για αποθήκευση αποτελεσμάτων (Average Hops)
    results = {
        'pastry': {'insert': [], 'lookup': [], 'delete': [], 'join': []},
        'chord':  {'insert': [], 'lookup': [], 'delete': [], 'join': []}
    }

    print(f"\n🚀 Ξεκινάει το Πλήρες Πείραμα (Insert, Lookup, Delete, Join)...")

    for n_nodes in NODE_COUNTS:
        print(f"\n{'='*40}")
        print(f"  Testing Network Size: N = {n_nodes}")
        print(f"{'='*40}")
        
        # --- PASTRY TEST ---
        print(f"-> Running Pastry...")
        net_p = PastryNetwork()
        net_p.build(n_nodes)
        
        # A. Insert Hops
        hops_ins = 0
        for m in movies:
            key_id = key_id_hex_from_title(m.title)
            # Η insert στο Pastry επιστρέφει Tuple (node_id, hops), οπότε το unpack δουλεύει
            _, h = net_p.insert(key_id, normalize_title(m.title), m)
            hops_ins += h
        results['pastry']['insert'].append(hops_ins / len(movies))

        # B. Lookup Hops
        sample = random.sample(movies, min(100, len(movies)))
        hops_look = 0
        for m in sample:
            # Η get_values στο Pastry επιστρέφει Tuple (values, hops), οπότε το unpack δουλεύει
            _, h = net_p.get_values(key_id_hex_from_title(m.title), normalize_title(m.title))
            hops_look += h
        results['pastry']['lookup'].append(hops_look / len(sample))

        # C. Delete Hops (Simulated via Lookup)
        hops_del = 0
        for m in sample:
            # ΔΙΟΡΘΩΣΗ: Η lookup επιστρέφει αντικείμενο LookupResult, όχι tuple
            res_obj = net_p.lookup(key_id_hex_from_title(m.title)) 
            hops_del += res_obj.hops  # Παίρνουμε το πεδίο .hops
        results['pastry']['delete'].append(hops_del / len(sample))

        # D. Node Join Hops (Simulated)
        new_id = key_id_hex_from_title(f"NewNode_{n_nodes}")
        # ΔΙΟΡΘΩΣΗ: Η lookup επιστρέφει αντικείμενο LookupResult
        res_obj = net_p.lookup(new_id) 
        results['pastry']['join'].append(res_obj.hops)


        # --- CHORD TEST ---
        print(f"-> Running Chord...")
        net_c = ChordNetwork(m=128)
        net_c.build(n_nodes)
        
        # A. Insert Hops
        hops_ins = 0
        for m in movies:
            key_id = key_id_hex_from_title(m.title)
            res = net_c.insert(key_id, normalize_title(m.title), m)
            # Στο Chord επιστρέφουμε tuple (node_id, hops) ή αντικείμενο ανάλογα την υλοποίηση
            # Με βάση το προηγούμενο fix, επιστρέφει tuple.
            h = res[1] if isinstance(res, tuple) else res
            hops_ins += h
        results['chord']['insert'].append(hops_ins / len(movies))

        # B. Lookup Hops
        hops_look = 0
        for m in sample:
            res = net_c.get_values(key_id_hex_from_title(m.title), normalize_title(m.title))
            h = res[1] if isinstance(res, tuple) else res
            hops_look += h
        results['chord']['lookup'].append(hops_look / len(sample))

        # C. Delete Hops
        hops_del = 0
        for m in sample:
            res = net_c.delete(key_id_hex_from_title(m.title), normalize_title(m.title))
            h = res[1] if isinstance(res, tuple) else res
            hops_del += h
        results['chord']['delete'].append(hops_del / len(sample))

        # D. Node Join Hops
        new_id = key_id_hex_from_title(f"NewNode_{n_nodes}")
        res = net_c.lookup(new_id)
        h_join = res[1] if isinstance(res, tuple) else res
        results['chord']['join'].append(h_join)

    # --- PLOTTING ---
    create_plots(NODE_COUNTS, results)

def create_plots(x_values, data):
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('DHT Protocol Comparison: Pastry vs Chord', fontsize=16)
    
    operations = ['insert', 'lookup', 'delete', 'join']
    titles = ['Insert Key', 'Lookup Key', 'Delete Key', 'Node Join']
    
    for i, op in enumerate(operations):
        ax = axs[i//2, i%2]
        
        # Pastry Line
        ax.plot(x_values, data['pastry'][op], marker='o', label='Pastry', color='blue', linewidth=2)
        # Chord Line
        ax.plot(x_values, data['chord'][op], marker='s', label='Chord', color='red', linewidth=2, linestyle='--')
        
        ax.set_title(f'{titles[i]} Performance')
        ax.set_xlabel('Number of Nodes (N)')
        ax.set_ylabel('Average Hops')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Create results directory if it doesn't exist
    import os
    os.makedirs("results", exist_ok=True)
    
    out_path = "results/final_comparison_all_ops.png"
    plt.savefig(out_path, dpi=300)
    print(f"\n[OK] Plot saved to: {out_path}")
    plt.show()

if __name__ == "__main__":
    run_full_experiment()