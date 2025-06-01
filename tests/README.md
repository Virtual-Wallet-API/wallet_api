# Virtual Wallet API - Testing Infrastructure

This directory contains comprehensive unit tests for the Virtual Wallet API business logic layer using Python's `unittest` framework with proper mocking practices.

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── base_test.py               # Base test class with common utilities
├── test_runner.py             # Test runner with coverage reporting
├── test_user_auth.py          # User authentication service tests
├── test_user_admin.py         # Admin service tests
├── test_transaction_service.py # Transaction service tests
├── test_category_service.py   # Category service tests
├── test_payment_deposit.py    # Payment deposit service tests
├── requirements-test.txt      # Testing dependencies
└── README.md                  # This file
```

## 🎯 Coverage Focus

The tests focus exclusively on the **business logic layer** (`app.business`) to ensure:
- Core business rules are properly implemented
- Error handling works correctly
- Database operations are properly mocked
- Service methods behave as expected

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### 2. Run All Tests with Coverage

```bash
python tests/test_runner.py
```

### 3. Run Specific Test Class

```bash
python tests/test_runner.py TestUserAuthService
```

### 4. Run Specific Test Method

```bash
python tests/test_runner.py TestUserAuthService test_register_success
```

## 📊 Coverage Reports

The test runner generates both console and HTML coverage reports:

- **Console Report**: Displayed after test execution
- **HTML Report**: Generated in `tests/coverage_html/index.html`

Target: **60%+ coverage** for the business logic layer as specified in requirements.

## 🔧 Test Architecture

### BaseTestCase (`base_test.py`)

Common utilities for all test cases:

- **Mock Factories**: Pre-configured mock objects for users, transactions, cards, etc.
- **Database Mocking**: Utilities for mocking SQLAlchemy sessions and queries
- **Assertion Helpers**: Custom assertions for database operations
- **Decorators**: Common mocking decorators for authentication and database

### Key Testing Principles

1. **Complete Isolation**: Each test is completely isolated with fresh mocks
2. **Database Mocking**: All database operations are mocked, no real database connections
3. **External Service Mocking**: All external services (Stripe, email, etc.) are mocked
4. **Comprehensive Coverage**: Tests cover success paths, error cases, and edge conditions
5. **Clear Test Structure**: Arrange-Act-Assert pattern for readable tests

### Example Test Structure

```python
def test_create_transaction_success(self):
    """Test successful transaction creation."""
    # Arrange
    mock_validate_user.return_value = self.receiver
    transaction_data = TransactionCreate(...)
    
    # Act
    result = TransactionService.create_pending_transaction(...)
    
    # Assert
    self.assert_db_add_called_with_type(Transaction)
    self.assert_db_operations_called(add=True, commit=True, refresh=True)
```

## 📋 Test Categories

### User Authentication Tests (`test_user_auth.py`)
- User registration (success/failure scenarios)
- Login authentication (various user states)
- Password management
- User status verification
- Permission checks

### Admin Service Tests (`test_user_admin.py`)
- Admin verification
- User status updates (approve/block/deactivate)
- User search and pagination
- Transaction management
- User promotion to admin

### Transaction Service Tests (`test_transaction_service.py`)
- Transaction creation and validation
- Transaction lifecycle (confirm/accept/decline/cancel)
- Transaction history and filtering
- Error handling and rollback scenarios
- Recurring transactions

### Category Service Tests (`test_category_service.py`)
- Category CRUD operations
- Search and pagination
- Validation and error handling
- Category statistics
- Transaction relationship handling

### Payment Service Tests (`test_payment_deposit.py`)
- Deposit retrieval and filtering
- Search by date/amount/status
- Pagination and statistics
- Error handling for invalid parameters

## 🔍 Running Tests in IDE

Most IDEs can run these tests directly:

**PyCharm/IntelliJ:**
- Right-click on test file/method → "Run"
- Use the testing tab for visual test results

**VS Code:**
- Install Python Test Explorer extension
- Tests will appear in the testing sidebar

**Command Line (Individual Tests):**
```bash
python -m unittest tests.test_user_auth.TestUserAuthService.test_register_success
```

## 📈 Coverage Goals

Current test coverage targets:

- **User Services**: 80%+ coverage
- **Transaction Services**: 75%+ coverage  
- **Payment Services**: 70%+ coverage
- **Category Services**: 75%+ coverage
- **Overall Business Logic**: 60%+ coverage (requirement met)

## 🐛 Debugging Tests

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Mock Failures**: Check that all external dependencies are properly mocked
3. **Database Errors**: Verify database session mocking is correct

### Debug Mode

Add this to any test for debugging:

```python
import pdb; pdb.set_trace()  # Add breakpoint
```

## 🔄 Continuous Integration

These tests are designed to run in CI/CD environments:

- No external dependencies (database, APIs, file system)
- Fast execution (all operations mocked)
- Clear pass/fail reporting
- Coverage metrics for quality gates

## 📚 Best Practices

1. **Test Names**: Use descriptive names that explain the scenario
2. **Test Documentation**: Include docstrings explaining the test purpose
3. **Mock Scope**: Mock at the lowest level possible (service calls, not internal logic)
4. **Error Testing**: Always test both success and failure scenarios
5. **Edge Cases**: Test boundary conditions and edge cases
6. **Maintenance**: Keep tests updated when business logic changes

## 🤝 Contributing

When adding new business logic:

1. Write tests for the new functionality
2. Ensure tests follow the existing patterns
3. Maintain the coverage threshold
4. Update this README if adding new test categories

---

**Note**: These tests specifically target the business logic layer only. API endpoint testing, integration testing, and end-to-end testing should be implemented separately. 