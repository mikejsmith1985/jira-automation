"""
Test for Issue #45: Cascading traceback errors causing infinite hangs

Problem:
- Feedback submission hangs on "Submitting..."
- Log export hangs on "Exporting logs..."
- PRB validation opens new tab showing "file not found: modern-ui.html"

Root Cause:
- OSError: [Errno 22] Invalid argument when trying to print tracebacks
- traceback.print_exc() fails because sys.stderr is invalid in frozen PyInstaller app
- Error handlers try to print the exception → fails → tries to handle THAT → infinite loop
- Server thread crashes but UI keeps waiting for response

Solution:
- Replace all traceback.print_exc() calls with safe_print(traceback.format_exc())
- Use logging.error() instead of print() for errors
- Ensure all exception handlers have fallback that doesn't rely on stderr/stdout
"""

import sys
import traceback
import logging
import io

def test_traceback_printing():
    """Test that traceback printing works in frozen environment"""
    print("\n=== Testing Traceback Printing ===")
    
    # Simulate PyInstaller environment where sys.stderr might be None
    original_stderr = sys.stderr
    
    try:
        # Test 1: Normal traceback printing
        print("\nTest 1: Normal traceback printing")
        try:
            1 / 0
        except Exception as e:
            try:
                traceback.print_exc()
                print("✓ traceback.print_exc() worked")
            except OSError as oe:
                print(f"✗ traceback.print_exc() FAILED: {oe}")
        
        # Test 2: With broken stderr
        print("\nTest 2: With broken stderr (simulates frozen app)")
        sys.stderr = None
        try:
            1 / 0
        except Exception as e:
            try:
                traceback.print_exc()
                print("✓ traceback.print_exc() worked with None stderr")
            except Exception as te:
                print(f"✗ traceback.print_exc() FAILED: {type(te).__name__}: {te}")
        
        # Test 3: Safe alternative using format_exc()
        print("\nTest 3: Safe alternative using format_exc()")
        sys.stderr = None
        try:
            1 / 0
        except Exception as e:
            try:
                tb_str = traceback.format_exc()
                print("✓ traceback.format_exc() worked!")
                print(f"  Got {len(tb_str)} chars of traceback")
            except Exception as te:
                print(f"✗ traceback.format_exc() FAILED: {te}")
        
        # Test 4: Using logging (recommended)
        print("\nTest 4: Using logging.error (recommended)")
        sys.stderr = None
        logging.basicConfig(level=logging.ERROR)
        try:
            1 / 0
        except Exception as e:
            try:
                logging.error("Test exception", exc_info=True)
                print("✓ logging.error() worked!")
            except Exception as te:
                print(f"✗ logging.error() FAILED: {te}")
        
    finally:
        sys.stderr = original_stderr
    
    print("\n=== Recommendation ===")
    print("Replace:")
    print("  traceback.print_exc()")
    print("With:")
    print("  logging.error('Error message', exc_info=True)")
    print("OR:")
    print("  safe_print(traceback.format_exc())")

if __name__ == '__main__':
    test_traceback_printing()
