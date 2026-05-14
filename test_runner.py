#!/usr/bin/env python3
"""NeuroForge Test Runner - Orchestrates complete test execution"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import subprocess
import json
from datetime import datetime
from typing import Dict, List, Tuple


class TestRunner:
    """Orchestrates test execution across all layers."""

    def __init__(self):
        self.results = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration_seconds": 0,
                "layers": {},
                "system_health": "UNKNOWN",
                "failures": []
            }
        }

    def run_test_layer(
        self,
        layer_name: str,
        test_paths: List[str]
    ) -> Tuple[bool, int, int, int]:
        """Run tests in a layer and return (success, passed, failed, skipped)."""

        print(f"\n{'='*70}")
        print(f"Running {layer_name.upper()} tests...")
        print(f"{'='*70}\n")

        total_passed = 0
        total_failed = 0
        total_skipped = 0
        layer_success = True

        for test_path in test_paths:
            if not Path(test_path).exists():
                print(f"⚠️  Test file not found: {test_path}")
                continue

            cmd = [
                "python", "-m", "pytest",
                test_path,
                "-v", "--tb=short", "--color=yes"
            ]

            print(f"\n📋 Running: {test_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Parse pytest output
            stdout = result.stdout

            # Count results
            if "passed" in stdout:
                for line in stdout.split("\n"):
                    if "passed" in line and ("failed" in line or "error" in line or "skipped" in line):
                        # Parse summary line
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if "passed" in part:
                                try:
                                    total_passed += int(parts[i - 1])
                                except (ValueError, IndexError):
                                    pass
                            elif "failed" in part:
                                try:
                                    failed_count = int(parts[i - 1])
                                    total_failed += failed_count
                                    layer_success = False
                                except (ValueError, IndexError):
                                    pass
                            elif "skipped" in part:
                                try:
                                    total_skipped += int(parts[i - 1])
                                except (ValueError, IndexError):
                                    pass

            if result.returncode != 0:
                layer_success = False
                print(f"❌ {test_path} FAILED")
                if result.stdout:
                    print(result.stdout[-500:])  # Last 500 chars
                self.results["test_run"]["failures"].append({
                    "test": test_path,
                    "error": result.stdout[-200:] if result.stdout else "Unknown error"
                })
            else:
                print(f"✅ {test_path} PASSED")

        return layer_success, total_passed, total_failed, total_skipped

    def run_unit_tests(self) -> bool:
        """Run all unit tests."""
        unit_tests = [
            "tests/unit/test_fsm.py",
            "tests/unit/test_state_manager.py",
            "tests/unit/test_validation_engine.py"
        ]

        success, passed, failed, skipped = self.run_test_layer("UNIT", unit_tests)

        self.results["test_run"]["layers"]["unit"] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }

        self.results["test_run"]["passed"] += passed
        self.results["test_run"]["failed"] += failed
        self.results["test_run"]["skipped"] += skipped

        return success

    def run_integration_tests(self) -> bool:
        """Run all integration tests."""
        integration_tests = [
            "tests/integration/test_fsm_state_integration.py"
        ]

        success, passed, failed, skipped = self.run_test_layer("INTEGRATION", integration_tests)

        self.results["test_run"]["layers"]["integration"] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }

        self.results["test_run"]["passed"] += passed
        self.results["test_run"]["failed"] += failed
        self.results["test_run"]["skipped"] += skipped

        return success

    def run_system_tests(self) -> bool:
        """Run all system tests."""
        system_tests = [
            "tests/system/test_e2e_happy_path.py"
        ]

        success, passed, failed, skipped = self.run_test_layer("SYSTEM", system_tests)

        self.results["test_run"]["layers"]["system"] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }

        self.results["test_run"]["passed"] += passed
        self.results["test_run"]["failed"] += failed
        self.results["test_run"]["skipped"] += skipped

        return success

    def run_failure_injection_tests(self) -> bool:
        """Run all failure injection tests."""
        failure_tests = [
            "tests/failure_injection/test_failure_injection.py"
        ]

        success, passed, failed, skipped = self.run_test_layer("FAILURE INJECTION", failure_tests)

        self.results["test_run"]["layers"]["failure_injection"] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }

        self.results["test_run"]["passed"] += passed
        self.results["test_run"]["failed"] += failed
        self.results["test_run"]["skipped"] += skipped

        return success

    def print_summary(self):
        """Print test results summary."""
        data = self.results["test_run"]

        print(f"\n{'='*70}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*70}\n")

        print(f"Timestamp: {data['timestamp']}")
        print(f"Total Tests: {data['passed'] + data['failed'] + data['skipped']}")
        print(f"✅ Passed: {data['passed']}")
        print(f"❌ Failed: {data['failed']}")
        print(f"⏭️  Skipped: {data['skipped']}")

        print(f"\n{'─'*70}")
        print("LAYER RESULTS")
        print(f"{'─'*70}\n")

        for layer, results in data["layers"].items():
            status = "✅ PASS" if results["failed"] == 0 else "❌ FAIL"
            print(
                f"{layer:20} {status:10} "
                f"({results['passed']} passed, {results['failed']} failed)"
            )

        print(f"\n{'─'*70}")

        # Determine overall health
        if data["failed"] == 0:
            data["system_health"] = "HEALTHY"
            print("🟢 SYSTEM HEALTH: HEALTHY\n")
        else:
            data["system_health"] = "UNHEALTHY"
            print("🔴 SYSTEM HEALTH: UNHEALTHY\n")

            print("FAILURES:")
            for failure in data["failures"][:5]:  # Show first 5
                print(f"  - {failure['test']}")

    def save_results(self, filename: str = "test_results.json"):
        """Save results to JSON file."""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📊 Results saved to: {filename}")

    def run_all(self, save_results: bool = True) -> bool:
        """Run all test layers in order."""
        import time

        start_time = time.time()

        print("🚀 NeuroForge Test Harness Starting\n")

        # Run tests in order
        unit_success = self.run_unit_tests()
        integration_success = self.run_integration_tests()
        system_success = self.run_system_tests()
        failure_success = self.run_failure_injection_tests()

        # Overall result
        overall_success = (
            unit_success and integration_success and
            system_success and failure_success
        )

        self.results["test_run"]["duration_seconds"] = time.time() - start_time

        self.print_summary()

        if save_results:
            self.save_results()

        return overall_success


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NeuroForge Test Runner")
    parser.add_argument(
        "--save-results",
        action="store_true",
        default=True,
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--layer",
        choices=["unit", "integration", "system", "failure"],
        help="Run specific test layer"
    )

    args = parser.parse_args()

    runner = TestRunner()

    if args.layer == "unit":
        success = runner.run_unit_tests()
    elif args.layer == "integration":
        success = runner.run_integration_tests()
    elif args.layer == "system":
        success = runner.run_system_tests()
    elif args.layer == "failure":
        success = runner.run_failure_injection_tests()
    else:
        success = runner.run_all(save_results=args.save_results)

    if args.layer:
        runner.print_summary()
        if args.save_results:
            runner.save_results()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
