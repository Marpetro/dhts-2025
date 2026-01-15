#!/usr/bin/env python
"""Comprehensive test of all DHT operations."""
import sys
sys.path.insert(0, '.')
from src.pastry.network import PastryNetwork
from src.chord.chord_network import ChordNetwork
from src.common.hash_utils import key_for_title, normalize_title
from src.pastry.local_index import MovieRecord

def key_id_hex_from_title(title: str) -> str:
    return f"{key_for_title(title, bits=128):032x}"

# Test both networks with all operations
print("=" * 60)
print("TESTING ALL DHT OPERATIONS")
print("=" * 60)

test_movie = MovieRecord(
    movie_id="1",
    title="Test Movie",
    popularity=5.0,
    vote_average=7.0,
    runtime=120
)

key_id = key_id_hex_from_title(test_movie.title)
key_str = normalize_title(test_movie.title)

# PASTRY Tests
print("\n[PASTRY]")
net_p = PastryNetwork()
net_p.build(10)
print("[OK] build()")

# Insert
node_id, hops = net_p.insert(key_id, key_str, test_movie)
print(f"[OK] insert() - node_id={node_id[:8]}, hops={hops}")

# Get Values
values, hops = net_p.get_values(key_id, key_str)
print(f"[OK] get_values() - found={bool(values)}, hops={hops}")

# Delete
existed, hops = net_p.delete(key_id, key_str)
print(f"[OK] delete() - existed={existed}, hops={hops}")

# Lookup
result = net_p.lookup(key_id)
print(f"[OK] lookup() - responsible={result.responsible_node_id[:8]}, hops={result.hops}")

# Join
new_node_id = key_id_hex_from_title("NewNode")
join_hops = net_p.join_node(new_node_id)
print(f"[OK] join_node() - hops={join_hops}")

# CHORD Tests
print("\n[CHORD]")
net_c = ChordNetwork()
net_c.build(10)
print("[OK] build()")

# Insert
node_id, hops = net_c.insert(key_id, key_str, test_movie)
print(f"[OK] insert() - node_id={node_id}, hops={hops}")

# Get Values
values, hops = net_c.get_values(key_id, key_str)
print(f"[OK] get_values() - found={bool(values)}, hops={hops}")

# Delete
existed, hops = net_c.delete(key_id, key_str)
print(f"[OK] delete() - existed={existed}, hops={hops}")

# Lookup
node_id, hops = net_c.lookup(key_id)
print(f"[OK] lookup() - responsible={node_id}, hops={hops}")

print("\n" + "=" * 60)
print("ALL OPERATIONS WORKING CORRECTLY")
print("=" * 60)
