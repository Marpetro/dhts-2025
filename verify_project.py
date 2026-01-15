#!/usr/bin/env python3
"""
DHTS 2025 - Project Verification & Diagnostics
Run this script to verify the entire project is working correctly.
"""
import sys
import os

def test_imports():
    """Test all critical imports."""
    print("\n" + "="*70)
    print("TESTING IMPORTS")
    print("="*70)
    
    tests = [
        ("Pastry Network", lambda: __import__('src.pastry.network', fromlist=['PastryNetwork'])),
        ("Chord Network", lambda: __import__('src.chord.chord_network', fromlist=['ChordNetwork'])),
        ("Metrics Logger", lambda: __import__('src.common.metrics', fromlist=['MetricsLogger'])),
        ("Hash Utils", lambda: __import__('src.common.hash_utils', fromlist=['key_for_title'])),
        ("Local Index", lambda: __import__('src.pastry.local_index', fromlist=['LocalIndex', 'MovieRecord'])),
        ("Data Loader", lambda: __import__('src.common.data_loader', fromlist=['load_movies'])),
        ("Plots", lambda: __import__('src.analysis.plots', fromlist=['load_metrics'])),
    ]
    
    passed = 0
    for name, import_fn in tests:
        try:
            import_fn()
            print(f"  [OK] {name:30s} - Imported successfully")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name:30s} - {str(e)[:40]}")
    
    return passed == len(tests)

def test_pastry():
    """Test Pastry operations."""
    print("\n" + "="*70)
    print("TESTING PASTRY NETWORK")
    print("="*70)
    
    try:
        from src.pastry.network import PastryNetwork
        from src.pastry.local_index import MovieRecord
        
        net = PastryNetwork()
        net.build(5)
        print("  [OK] build()")
        
        m = MovieRecord("1", "Test Movie", 5.0, 7.0, 120)
        key_id = "00000000000000000000000000000001"
        key_str = "test movie"
        
        node_id, hops = net.insert(key_id, key_str, m)
        print(f"  [OK] insert() - hops={hops}")
        
        values, hops = net.get_values(key_id, key_str)
        assert values, "Values should not be empty"
        print(f"  [OK] get_values() - hops={hops}")
        
        existed, hops = net.delete(key_id, key_str)
        assert existed, "Key should have existed"
        print(f"  [OK] delete() - hops={hops}")
        
        result = net.lookup(key_id)
        print(f"  [OK] lookup() - hops={result.hops}")
        
        new_node_id = "ffffffffffffffffffffffffffffffff"
        join_hops = net.join_node(new_node_id)
        print(f"  [OK] join_node() - hops={join_hops}")
        
        net.leave_node(new_node_id)
        print(f"  [OK] leave_node()")
        
        return True
    except Exception as e:
        print(f"  [FAIL] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_chord():
    """Test Chord operations."""
    print("\n" + "="*70)
    print("TESTING CHORD NETWORK")
    print("="*70)
    
    try:
        from src.chord.chord_network import ChordNetwork
        from src.pastry.local_index import MovieRecord
        
        net = ChordNetwork()
        net.build(5)
        print("  [OK] build()")
        
        m = MovieRecord("1", "Test Movie", 5.0, 7.0, 120)
        key_id = "00000000000000000000000000000001"
        key_str = "test movie"
        
        node_id, hops = net.insert(key_id, key_str, m)
        print(f"  [OK] insert() - hops={hops}")
        
        value, hops = net.get_values(key_id, key_str)
        assert value, "Value should not be empty"
        print(f"  [OK] get_values() - hops={hops}")
        
        existed, hops = net.delete(key_id, key_str)
        assert existed, "Key should have existed"
        print(f"  [OK] delete() - hops={hops}")
        
        node_id, hops = net.lookup(key_id)
        print(f"  [OK] lookup() - hops={hops}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_structure():
    """Test file structure."""
    print("\n" + "="*70)
    print("TESTING FILE STRUCTURE")
    print("="*70)
    
    required_files = [
        "src/__init__.py",
        "src/analysis/__init__.py",
        "src/chord/__init__.py",
        "src/common/__init__.py",
        "src/experiments/__init__.py",
        "src/pastry/__init__.py",
        "src/analysis/plots.py",
        "src/chord/chord_network.py",
        "src/chord/chord_node.py",
        "src/common/data_loader.py",
        "src/common/hash_utils.py",
        "src/common/metrics.py",
        "src/experiments/run_pastry.py",
        "src/pastry/local_index.py",
        "src/pastry/network.py",
        "src/pastry/node.py",
        "final_experiment.py",
        "run_experiments.py",
        "README.md",
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
            print(f"  [FAIL] {f:40s} - NOT FOUND")
        else:
            print(f"  [OK] {f:40s} - Found")
    
    return len(missing) == 0

def main():
    """Run all verification tests."""
    print("\n")
    print("=" * 70)
    print(" " * 15 + "DHTS 2025 - PROJECT VERIFICATION")
    print("=" * 70)
    
    results = []
    
    results.append(("File Structure", test_structure()))
    results.append(("Imports", test_imports()))
    results.append(("Pastry Operations", test_pastry()))
    results.append(("Chord Operations", test_chord()))
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name:30s} [{status}]")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("  *** ALL TESTS PASSED - PROJECT IS READY! ***")
        print("="*70)
        return 0
    else:
        print("  *** SOME TESTS FAILED - CHECK ABOVE FOR DETAILS ***")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
