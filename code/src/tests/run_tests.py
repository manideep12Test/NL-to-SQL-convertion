"""Test configuration and runner script."""
import os
import sys
import subprocess
import coverage
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def run_unit_tests():
    """Run all unit tests."""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    unit_test_dir = Path(__file__).parent / "unit"
    
    # Run pytest with coverage for unit tests
    cmd = [
        sys.executable, "-m", "pytest", 
        str(unit_test_dir),
        "-v",
        "--tb=short",
        "--cov=Agent",
        "--cov=db", 
        "--cov=UI",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/unit",
        "--junitxml=test-results/unit-tests.xml"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running unit tests: {e}")
        return False

def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    integration_test_dir = Path(__file__).parent / "integration"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(integration_test_dir),
        "-v",
        "--tb=short",
        "--junitxml=test-results/integration-tests.xml"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running integration tests: {e}")
        return False

def run_e2e_tests():
    """Run end-to-end tests."""
    print("\n" + "=" * 60)
    print("RUNNING END-TO-END TESTS")
    print("=" * 60)
    
    e2e_test_dir = Path(__file__).parent / "e2e"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(e2e_test_dir),
        "-v",
        "--tb=short",
        "--junitxml=test-results/e2e-tests.xml",
        "-k", "not test_performance"  # Skip performance tests by default
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running e2e tests: {e}")
        return False

def run_performance_tests():
    """Run performance tests separately."""
    print("\n" + "=" * 60)
    print("RUNNING PERFORMANCE TESTS")
    print("=" * 60)
    
    e2e_test_dir = Path(__file__).parent / "e2e"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(e2e_test_dir / "test_performance.py"),
        "-v",
        "--tb=short",
        "--junitxml=test-results/performance-tests.xml"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running performance tests: {e}")
        return False

def create_test_directories():
    """Create necessary test directories."""
    test_dirs = [
        Path(__file__).parent / "test-results",
        Path(__file__).parent.parent / "htmlcov"
    ]
    
    for directory in test_dirs:
        directory.mkdir(exist_ok=True)

def generate_coverage_report():
    """Generate comprehensive coverage report."""
    print("\n" + "=" * 60)
    print("GENERATING COVERAGE REPORT")
    print("=" * 60)
    
    try:
        # Create coverage object
        cov = coverage.Coverage()
        cov.load()
        
        # Generate reports
        print("\nCoverage Summary:")
        cov.report()
        
        # Generate HTML report
        html_dir = Path(__file__).parent.parent / "htmlcov" / "complete"
        cov.html_report(directory=str(html_dir))
        print(f"\nDetailed HTML report generated at: {html_dir}")
        
        # Generate XML report for CI/CD
        xml_file = Path(__file__).parent / "test-results" / "coverage.xml"
        cov.xml_report(outfile=str(xml_file))
        print(f"XML coverage report generated at: {xml_file}")
        
    except Exception as e:
        print(f"Error generating coverage report: {e}")

def run_code_quality_checks():
    """Run code quality checks."""
    print("\n" + "=" * 60)
    print("RUNNING CODE QUALITY CHECKS")
    print("=" * 60)
    
    # Check if flake8 is available
    try:
        # Run flake8 for code style
        print("Running flake8...")
        flake8_cmd = [sys.executable, "-m", "flake8", "--max-line-length=120", "--ignore=E501,W503", "Agent"]
        result = subprocess.run(flake8_cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("✓ Code style check passed")
        else:
            print("⚠ Code style issues found:")
            print(result.stdout)
    except FileNotFoundError:
        print("flake8 not available, skipping code style check")
    
    # Check if bandit is available for security
    try:
        print("\nRunning bandit for security check...")
        bandit_cmd = [sys.executable, "-m", "bandit", "-r", "Agent", "-f", "txt"]
        result = subprocess.run(bandit_cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("✓ Security check passed")
        else:
            print("⚠ Security issues found:")
            print(result.stdout)
    except FileNotFoundError:
        print("bandit not available, skipping security check")

def main():
    """Main test runner function."""
    print("Banking NL-to-SQL Application - Test Suite")
    print("=" * 60)
    
    # Create necessary directories
    create_test_directories()
    
    # Track test results
    results = {
        "unit": False,
        "integration": False,
        "e2e": False,
        "performance": False
    }
    
    # Run all test suites
    try:
        results["unit"] = run_unit_tests()
        results["integration"] = run_integration_tests()
        results["e2e"] = run_e2e_tests()
        
        # Ask user if they want to run performance tests (they take longer)
        run_perf = input("\nRun performance tests? (y/N): ").lower().startswith('y')
        if run_perf:
            results["performance"] = run_performance_tests()
        
        # Generate coverage report
        generate_coverage_report()
        
        # Run code quality checks
        run_quality = input("\nRun code quality checks? (y/N): ").lower().startswith('y')
        if run_quality:
            run_code_quality_checks()
        
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        return False
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len([k for k, v in results.items() if v is not False])
    passed_tests = len([k for k, v in results.items() if v is True])
    
    for test_type, passed in results.items():
        if passed is not False:  # Test was run
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{test_type.upper():12} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
    
    if all(result for result in results.values() if result is not False):
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
