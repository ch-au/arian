#!/usr/bin/env python3
"""
Test runner script for the Negotiation POC.

This script provides an easy way to run tests with different configurations
and generate coverage reports.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for Negotiation POC")
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--unit-only", 
        action="store_true", 
        help="Run only unit tests (skip integration tests)"
    )
    parser.add_argument(
        "--integration-only", 
        action="store_true", 
        help="Run only integration tests"
    )
    parser.add_argument(
        "--fast", 
        action="store_true", 
        help="Skip slow tests"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--file", 
        type=str, 
        help="Run tests from specific file"
    )
    parser.add_argument(
        "--test", 
        type=str, 
        help="Run specific test function"
    )
    
    args = parser.parse_args()
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    print(f"📁 Working directory: {project_dir}")
    
    # Build pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        pytest_cmd.append("-v")
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd.extend([
            "--cov=negotiation_poc",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add test selection
    if args.unit_only:
        pytest_cmd.extend(["-m", "unit"])
    elif args.integration_only:
        pytest_cmd.extend(["-m", "integration"])
    
    # Skip slow tests if requested
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])
    
    # Run specific file or test
    if args.file:
        pytest_cmd.append(f"tests/{args.file}")
    elif args.test:
        pytest_cmd.extend(["-k", args.test])
    
    # Run the tests
    success = run_command(
        pytest_cmd, 
        "Running tests"
    )
    
    if not success:
        print("\n❌ Tests failed!")
        sys.exit(1)
    
    # Generate coverage report if requested
    if args.coverage:
        print("\n📊 Coverage report generated:")
        print("  - HTML report: htmlcov/index.html")
        print("  - XML report: coverage.xml")
        print("  - Terminal report shown above")
    
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    main()
