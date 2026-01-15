from __future__ import annotations
import random
import csv
import time
import json
import os
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt

# --- Imports από τα δικά μας modules ---
from src.pastry.network import PastryNetwork
from src.chord.chord_network import ChordNetwork
from src.common.hash_utils import key_for_title, normalize_title
from src.pastry.local_index import MovieRecord

# --- Helper ---
def key_id_hex_from_title(title: str) -> str:
    return f"{key_for_title(title, bits=128):032x}"

def load_real_movies(limit: int) -> List[MovieRecord]:
    # Χρησιμοποίησε το r μπροστά για να διαβαστούν σωστά τα backslashes
    dataset_folder = Path(r"C:\Users\HP\OneDrive\Έγγραφα\GitHub\dhts-2025\movies_dataset_cleaned")
    csv_path = dataset_folder / "data_movies_clean.csv" 

    movies: List[MovieRecord] = []
    
    if not csv_path.exists():
        print(f"[WARNING] Dataset not found at {csv_path}. Please check path.")
        return []

    print(f"-> Loading movies from: {csv_path}")
    
    # ΑΝΟΙΓΜΑ ΜΕ ΕΡΩΤΗΜΑΤΙΚΟ (;) ΓΙΑ ΕΛΛΗΝΙΚΟ CSV
    with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=';')  # <--- Η ΣΗΜΑΝΤΙΚΗ ΑΛΛΑΓΗ
        
        for i, row in enumerate(reader):
            if i >= limit: break
            
            # Καθαρισμός και πεζά γράμματα
            clean_row = {str(k).lower().strip(): v for k, v in row.items() if k is not None}
            
            # Εύρεση τίτλου
            title = clean_row.get("title") or clean_row.get("original_title")
            
            if not title:
                continue

            try:
                # Δημιουργία εγγραφής
                rec = MovieRecord(
                    movie_id=str(clean_row.get("id", i)),
                    title=title.strip(),
                    popularity=float(clean_row.get("popularity", 0) or 0),
                    vote_average=float(clean_row.get("vote_average", 0) or 0),
                    runtime=int(float(clean_row.get("runtime", 0) or 0))
                )
                movies.append(rec)
            except Exception:
                continue
                
    print(f"[OK] Loaded {len(movies)} movies from real dataset.")
    return movies

def run_test_logic():
    # Ρυθμίσεις
    N_NODES = 100
    N_KEYS = 1000  # Πόσες ταινίες να φορτώσουμε
    
    # 1. Φόρτωση Δεδομένων
    movies = load_real_movies(N_KEYS)
    if not movies:
        print("[ERROR] No movies loaded. Exiting.")
        return

    # Αποτελέσματα για αποθήκευση JSON (όπως στο test.py)
    final_results = {}

    for protocol in ["PASTRY", "CHORD"]:
        print(f"\n{'='*60}")
        print(f"STARTING TEST FOR: {protocol}")
        print(f"{'='*60}")

        # Initialization
        if protocol == "PASTRY":
            net = PastryNetwork()
        else:
            net = ChordNetwork(m=128)

        # --- NODES JOIN (BUILD) ---
        print("\n################ NODES JOIN ################")
        print(f"Building network with {N_NODES} nodes...")
        net.build(N_NODES)
        print("-> Network Built Successfully.")

        # --- KEYS INSERTION ---
        print("\n################ KEYS INSERTION ################")
        print(f"Inserting {len(movies)} movies...")
        
        start_time = time.perf_counter()
        insert_hops_total = 0
        
        for m in movies:
            key_id = key_id_hex_from_title(m.title)
            key_str = normalize_title(m.title)
            
            # Κλήση της insert (στο Pastry επιστρέφει tuple, στο Chord ίσως επιστρέφει hops)
            # Προσαρμογή ανάλογα με την υλοποίησή σου
            if protocol == "PASTRY":
                _, h = net.insert(key_id, key_str, m)
                insert_hops_total += h
            else:
                # Υποθέτουμε ότι το Chord insert επιστρέφει (node_id, hops) ή hops
                # Αν έχεις αλλάξει το ChordNetwork να επιστρέφει hops:
                res = net.insert(key_id, key_str, m) 
                # Αν το Chord επιστρέφει tuple (node, hops), πάρε το [1]
                hops = res[1] if isinstance(res, tuple) else res
                insert_hops_total += hops

        duration = time.perf_counter() - start_time
        avg_insert_hops = insert_hops_total / len(movies)
        print(f"-> Inserted {len(movies)} keys.")
        print(f"-> Avg Hops per Insert: {avg_insert_hops:.2f}")
        print(f"-> Time taken: {duration:.2f}s")
        
        final_results[f"{protocol}_Insert_Hops"] = avg_insert_hops

        # --- KEYS LOOKUP ---
        print("\n################ KEYS LOOKUP ################")
        # Δοκιμάζουμε 100 τυχαίες αναζητήσεις
        sample_size = 100
        sample = random.sample(movies, min(sample_size, len(movies)))
        
        lookup_hops_total = 0
        success_count = 0
        
        for m in sample:
            key_id = key_id_hex_from_title(m.title)
            key_str = normalize_title(m.title)
            
            if protocol == "PASTRY":
                vals, h = net.get_values(key_id, key_str)
                if vals: success_count += 1
                lookup_hops_total += h
            else:
                # Chord Lookup
                vals, h = net.get_values(key_id, key_str)
                # Προσοχή: στο Chord αν επιστρέφει None ή κενό
                if vals: success_count += 1
                lookup_hops_total += h

        avg_lookup_hops = lookup_hops_total / len(sample)
        print(f"-> Looked up {len(sample)} keys.")
        print(f"-> Avg Hops per Lookup: {avg_lookup_hops:.2f}")
        print(f"-> Success Rate: {success_count}/{len(sample)}")
        
        final_results[f"{protocol}_Lookup_Hops"] = avg_lookup_hops
        final_results[f"{protocol}_Success"] = success_count

    # Αποθήκευση σε JSON όπως στο test.py
    with open("results/ComparisonResults.json", "w") as f:
        json.dump(final_results, f, indent=4)
    
    print("\n[OK] Tests Completed. Results saved to results/ComparisonResults.json")

def create_comparison_plot(results_dict):
    """
    Create a comparison plot from results dictionary.
    """
    os.makedirs("results", exist_ok=True)
    
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Pastry vs Chord - Insert & Lookup Hops', fontsize=14)
    
    # Extract data
    pastry_insert = results_dict.get("PASTRY_Insert_Hops", 0)
    pastry_lookup = results_dict.get("PASTRY_Lookup_Hops", 0)
    chord_insert = results_dict.get("CHORD_Insert_Hops", 0)
    chord_lookup = results_dict.get("CHORD_Lookup_Hops", 0)
    
    # Plot 1: Insert Hops
    ax1 = axs[0]
    protocols = ['Pastry', 'Chord']
    insert_hops = [pastry_insert, chord_insert]
    colors = ['blue', 'red']
    ax1.bar(protocols, insert_hops, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    ax1.set_ylabel('Average Hops')
    ax1.set_title('Insert Operation - Average Hops')
    ax1.grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(insert_hops):
        ax1.text(i, v + 0.1, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # Plot 2: Lookup Hops
    ax2 = axs[1]
    lookup_hops = [pastry_lookup, chord_lookup]
    ax2.bar(protocols, lookup_hops, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    ax2.set_ylabel('Average Hops')
    ax2.set_title('Lookup Operation - Average Hops')
    ax2.grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(lookup_hops):
        ax2.text(i, v + 0.1, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    out_path = "results/comparison_results.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Comparison plot saved to: {out_path}")
    plt.close()

if __name__ == "__main__":
    run_test_logic()
    
    # Load results and create plot
    try:
        with open("results/ComparisonResults.json", "r") as f:
            results = json.load(f)
        create_comparison_plot(results)
    except Exception as e:
        print(f"[ERROR] Could not create plot: {e}")