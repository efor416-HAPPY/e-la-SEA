# -*- coding: utf-8 -*-
"""
Native Test Runner
Runs the unit tests without external dependencies like pytest.
"""

import sys
import os
import io

# Force stdout/stderr to use UTF-8 encoding to prevent CP949 encoding crashes on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Adjust path to find backend package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.tests.test_backend import (
    test_firewall_whitelist,
    test_safety_gate_pii,
    test_safety_gate_command_injection,
    test_language_detection,
    test_3tier_memory_operations,
    test_cosine_similarity,
    test_agent_bus_dispatch,
    test_microkernel_integration,
    test_socket_layer_operations
)

class TempPath:
    def __init__(self, path):
        self.path = path
    def __truediv__(self, other):
        p = os.path.join(self.path, other)
        return p

def run():
    print("Running ARA AI Native Unit Test Suite...")
    
    # 1. Firewall Whitelist
    try:
        test_firewall_whitelist()
        print("  [OK] test_firewall_whitelist: Passed")
    except AssertionError as e:
        print("  [FAIL] test_firewall_whitelist: Failed", e)
        sys.exit(1)

    # 2. Safety Gate PII
    try:
        test_safety_gate_pii()
        print("  [OK] test_safety_gate_pii: Passed")
    except AssertionError as e:
        print("  [FAIL] test_safety_gate_pii: Failed", e)
        sys.exit(1)

    # 3. Safety Gate Command Injection
    try:
        test_safety_gate_command_injection()
        print("  [OK] test_safety_gate_command_injection: Passed")
    except AssertionError as e:
        print("  [FAIL] test_safety_gate_command_injection: Failed", e)
        sys.exit(1)

    # 4. Language Detection
    try:
        test_language_detection()
        print("  [OK] test_language_detection: Passed")
    except AssertionError as e:
        print("  [FAIL] test_language_detection: Failed", e)
        sys.exit(1)

    # 5. 3-Tier Memory Operations
    import tempfile
    import gc
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            test_3tier_memory_operations(TempPath(tmpdir))
            print("  [OK] test_3tier_memory_operations: Passed")
        except AssertionError as e:
            print("  [FAIL] test_3tier_memory_operations: Failed", e)
            sys.exit(1)
        finally:
            gc.collect()

    # 6. Cosine Similarity
    try:
        test_cosine_similarity()
        print("  [OK] test_cosine_similarity: Passed")
    except AssertionError as e:
        print("  [FAIL] test_cosine_similarity: Failed", e)
        sys.exit(1)

    # 7. Agent Bus Dispatch
    try:
        test_agent_bus_dispatch()
        print("  [OK] test_agent_bus_dispatch: Passed")
    except AssertionError as e:
        print("  [FAIL] test_agent_bus_dispatch: Failed", e)
        sys.exit(1)

    # 8. Microkernel Integration
    try:
        test_microkernel_integration()
        print("  [OK] test_microkernel_integration: Passed")
    except AssertionError as e:
        print("  [FAIL] test_microkernel_integration: Failed", e)
        sys.exit(1)

    # 9. Socket Layer Operations
    try:
        test_socket_layer_operations()
        print("  [OK] test_socket_layer_operations: Passed")
    except AssertionError as e:
        print("  [FAIL] test_socket_layer_operations: Failed", e)
        sys.exit(1)

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run()
