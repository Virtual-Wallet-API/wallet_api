"""
Test runner for Virtual Wallet API business logic tests.
Discovers and runs all test cases with coverage reporting.
"""
import sys
import unittest
import os
from io import StringIO
import coverage
import importlib

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestResult:
    """Custom test result class to track test statistics."""

    def __init__(self):
        self.tests_run = 0
        self.failures = []
        self.errors = []
        self.skipped = []
        self.success_count = 0

    def add_test(self, test_name, status, details=None):
        self.tests_run += 1
        if status == 'PASS':
            self.success_count += 1
        elif status == 'FAIL':
            self.failures.append((test_name, details))
        elif status == 'ERROR':
            self.errors.append((test_name, details))
        elif status == 'SKIP':
            self.skipped.append((test_name, details))


def discover_tests():
    """Discover all test modules in the tests directory."""
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir='tests',
        pattern='test_*.py',
        top_level_dir='.'
    )
    return test_suite


def run_tests_with_coverage():
    """Run tests with coverage measurement."""
    # Initialize coverage
    cov = coverage.Coverage(
        source=['app.business'],  # Only measure business logic coverage
        omit=[
            '*/test*',
            '*/venv/*',
            '*/env/*',
            '*/__pycache__/*'
        ]
    )
    cov.start()

    try:
        # Discover and run tests
        test_suite = discover_tests()

        # Create a test runner with verbose output
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=2,
            descriptions=True,
            failfast=False
        )

        # Run the tests
        result = runner.run(test_suite)

        # Stop coverage measurement
        cov.stop()
        cov.save()

        # Print test results
        print("=" * 70)
        print("VIRTUAL WALLET API - BUSINESS LOGIC TEST RESULTS")
        print("=" * 70)
        print(stream.getvalue())

        # Print test summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")

        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")

        # Print detailed failure information
        if result.failures:
            print("\n" + "=" * 70)
            print("FAILURES")
            print("=" * 70)
            for test, traceback in result.failures:
                print(f"\nFAIL: {test}")
                print("-" * 50)
                print(traceback)

        if result.errors:
            print("\n" + "=" * 70)
            print("ERRORS")
            print("=" * 70)
            for test, traceback in result.errors:
                print(f"\nERROR: {test}")
                print("-" * 50)
                print(traceback)

        # Print coverage report
        print("\n" + "=" * 70)
        print("COVERAGE REPORT")
        print("=" * 70)

        # Generate coverage report
        coverage_stream = StringIO()
        cov.report(file=coverage_stream, show_missing=True)
        print(coverage_stream.getvalue())

        # Generate HTML coverage report
        try:
            cov.html_report(directory='tests/coverage_html')
            print(f"\nHTML coverage report generated in: tests/coverage_html/index.html")
        except Exception as e:
            print(f"Could not generate HTML report: {e}")

        # Return success/failure status
        return len(result.failures) == 0 and len(result.errors) == 0

    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_specific_test_class(test_class_name):
    """Run a specific test class."""
    try:
        # Map test class names to module names
        class_to_module = {
            'TestUserAuthService': 'test_user_auth',
            'TestUserAdminService': 'test_user_admin',
            'TestAdminService': 'test_user_admin',
            'TestUserContacts': 'test_user_contacts',
            'TestTransactionService': 'test_transaction_service',
            'TestTransactionNotificationService': 'test_transaction_notifications',
            'TestRecurringService': 'test_recurring_service',
            'TestWithdrawalService': 'test_withdrawal_service',
            'TestTransactionValidators': 'test_transaction_validators',
            'TestCategoryService': 'test_category_service',
            'TestCategoryValidators': 'test_category_validators',
            'TestDepositService': 'test_payment_deposit',
            'TestCardService': 'test_payment_card',
            'TestStripeService': 'test_stripe_service'
        }

        if test_class_name not in class_to_module:
            print(f"❌ Test class '{test_class_name}' not found in mapping.")
            return False

        module_name = class_to_module[test_class_name]

        # Import the module
        module = importlib.import_module(f'tests.{module_name}')

        # Get the test class
        test_class = getattr(module, test_class_name)

        # Create a test suite containing only this class
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)

        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ Error running test class {test_class_name}: {e}")
        return False


def run_specific_test_method(test_class_name, test_method_name):
    """Run a specific test method."""
    try:
        # Map test class names to module names
        class_to_module = {
            'TestUserAuthService': 'test_user_auth',
            'TestUserAdminService': 'test_user_admin',
            'TestAdminService': 'test_user_admin',
            'TestUserContacts': 'test_user_contacts',
            'TestTransactionService': 'test_transaction_service',
            'TestTransactionNotificationService': 'test_transaction_notifications',
            'TestRecurringService': 'test_recurring_service',
            'TestWithdrawalService': 'test_withdrawal_service',
            'TestTransactionValidators': 'test_transaction_validators',
            'TestCategoryService': 'test_category_service',
            'TestCategoryValidators': 'test_category_validators',
            'TestDepositService': 'test_payment_deposit',
            'TestCardService': 'test_payment_card',
            'TestStripeService': 'test_stripe_service'
        }

        if test_class_name not in class_to_module:
            print(f"❌ Test class '{test_class_name}' not found in mapping.")
            return False

        module_name = class_to_module[test_class_name]

        # Import the module
        module = importlib.import_module(f'tests.{module_name}')

        # Get the test class
        test_class = getattr(module, test_class_name)

        # Create a test suite with specific method
        test_suite = unittest.TestSuite()
        test_suite.addTest(test_class(test_method_name))

        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ Error running test method {test_class_name}.{test_method_name}: {e}")
        return False


def main():
    """Main entry point for test runner."""
    if len(sys.argv) == 1:
        # Run all tests with coverage
        success = run_tests_with_coverage()
    elif len(sys.argv) == 2:
        # Run specific test class
        test_class = sys.argv[1]
        success = run_specific_test_class(test_class)
    elif len(sys.argv) == 3:
        # Run specific test method
        test_class = sys.argv[1]
        test_method = sys.argv[2]
        success = run_specific_test_method(test_class, test_method)
    else:
        print("Usage:")
        print("  python test_runner.py                           # Run all tests")
        print("  python test_runner.py TestClassName            # Run specific test class")
        print("  python test_runner.py TestClassName test_method # Run specific test method")
        return False
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 