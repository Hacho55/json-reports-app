#!/usr/bin/env python3
"""
Integrated test runner for JSON Reports Tools.
Runs both unit tests and integration tests.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_pytest():
    """Run pytest unit tests."""
    print("🧪 Running unit tests with pytest...")
    
    try:
        result = subprocess.run([
            "pipenv", "run", "pytest", "tests/", "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Unit tests passed!")
            return True
        else:
            print("❌ Unit tests failed!")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        return False


def run_integration_tests():
    """Run integration tests (scripts)."""
    print("\n🔧 Running integration tests...")
    
    tests = [
        ("scripts/test_conversion.py", "JSON Conversion"),
        ("scripts/test_validation.py", "Metrics Validation"),
        ("scripts/test_extraction.py", "Metrics Extraction")
    ]
    
    all_passed = True
    
    for test_file, description in tests:
        print(f"\n📋 Testing {description}...")
        
        try:
            result = subprocess.run([
                "pipenv", "run", "python", test_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {description} test passed!")
            else:
                print(f"❌ {description} test failed!")
                print(result.stdout)
                print(result.stderr)
                all_passed = False
                
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            all_passed = False
    
    return all_passed


def run_coverage():
    """Run tests with coverage report."""
    print("\n📊 Running tests with coverage...")
    
    try:
        result = subprocess.run([
            "pipenv", "run", "pytest", "tests/", "--cov=tools", "--cov-report=term-missing"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Coverage test completed!")
            return True
        else:
            print("❌ Coverage test failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running coverage: {e}")
        return False


def main():
    """Main test runner."""
    print("🚀 JSON Reports Tools - Test Suite")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Install dependencies if needed
    print("📦 Checking dependencies...")
    try:
        subprocess.run(["pipenv", "install", "--dev"], check=True)
        print("✅ Dependencies ready!")
    except subprocess.CalledProcessError:
        print("❌ Error installing dependencies")
        sys.exit(1)
    
    # Run tests
    unit_passed = run_pytest()
    integration_passed = run_integration_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   Unit Tests: {'✅ PASSED' if unit_passed else '❌ FAILED'}")
    print(f"   Integration Tests: {'✅ PASSED' if integration_passed else '❌ FAILED'}")
    
    if unit_passed and integration_passed:
        print("\n🎉 All tests passed!")
        
        # Ask if user wants coverage report
        try:
            response = input("\n📊 Would you like to see coverage report? (y/n): ")
            if response.lower() in ['y', 'yes']:
                run_coverage()
        except KeyboardInterrupt:
            print("\n👋 Test run completed!")
        
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 