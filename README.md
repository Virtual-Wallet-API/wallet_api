# Virtual Wallet API

Virtual Wallet is a modern web application that enables users to manage their budget, send and receive money, and organize their finances with ease. The platform supports user-to-user transactions, virtual wallet management, credit/debit card integration, and robust administrative controls.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Database Setup](#database-setup)
  - [Running the Application](#running-the-application)
  - [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **User Registration & Authentication**
  - Register/login with username, email, phone, and strong password validation
  - Email verification and password reset
  - JWT-based authentication

- **Profile Management**
  - Update email, phone, password, and avatar (Cloudinary integration)
  - View and update profile (except username)

- **Cards & Payments**
  - Register, view, and delete credit/debit cards (Stripe integration)
  - Multiple cards per user
  - Personalized card design (planned)
  - Deposit and withdraw funds

- **Transactions**
  - Send/receive money between users
  - Transaction confirmation, approval, and decline
  - Recurring transactions with scheduler and notifications
  - Transaction history with advanced filtering, sorting, and pagination

- **Categories & Budgeting**
  - Create, update, and delete categories
  - Link transactions to categories
  - Category statistics and reports

- **Contacts**
  - Add/remove/search contacts by username, email, or phone
  - Transfer money to contacts

- **Admin Panel**
  - Approve/block/unblock/deactivate users
  - Promote users to admin
  - View all users and transactions with search, filtering, and pagination
  - Deny pending transactions

- **Notifications**
  - Email notifications for account and transaction events (Mailgun)
  - Recurring transaction failure alerts

- **Other**
  - Fully documented REST API (Swagger/OpenAPI)
  - Relational database with migrations
  - Unit and integration tests

---

## Tech Stack

- **Backend Framework:** FastAPI
- **Database:** SQLAlchemy ORM (supports PostgreSQL, MySQL, SQLite)
- **Migrations:** Alembic
- **Authentication:** JWT, OAuth2
- **Email:** Mailgun (via `requests`)
- **Payments:** Stripe
- **File Uploads:** Cloudinary (for avatars)
- **Scheduling:** APScheduler
- **Testing:** unittest, coverage, unittest-xml-reporting
- **Frontend:** Jinja2 templates (basic, optional)
- **Other Libraries:** Pydantic, python-dotenv, passlib, bcrypt, httpx, requests

---

## Architecture

- **app/**: Main application logic (models, business logic, API routes, schemas)
- **frontend/**: Jinja2 templates and static files for optional web frontend
- **sql/**: Database creation and population scripts, schema diagram
- **tests/**: Automated tests for all major features

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- (Recommended) Virtual environment tool (venv, virtualenv, etc.)
- Access to a relational database (PostgreSQL, MySQL, or SQLite for dev)
- Stripe and Mailgun accounts for payments and email notifications
- Cloudinary account for avatar uploads

### Installation

```bash
git clone https://github.com/yourusername/virtual-wallet-api.git
cd virtual-wallet-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with the following (example):

```
DATABASE_URL=postgresql://user:password@localhost:5432/virtualwallet
SECRET_KEY=your_jwt_secret
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
MAILGUN_API_KEY=your-mailgun-api-key
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### Database Setup

1. **Create the database schema:**

   ```bash
   python sql/create_db.py
   ```

2. **(Optional) Populate with sample data:**

   ```bash
   python sql/populate_db.py
   ```

3. **(Optional) View the schema diagram:**  
   See `sql/DBschema.png`.

### Running the Application

```bash
uvicorn main:app --reload
```

- The API will be available at: [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Running Tests

```bash
pip install -r requirements-test.txt
python -m unittest discover tests
# Or with coverage:
coverage run -m unittest discover tests
coverage report
```

---

## API Documentation

- **Interactive API docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

All endpoints, request/response models, and authentication flows are documented.

---

## Project Structure

```
.
├── app/
│   ├── api/           # API route definitions (v1)
│   ├── business/      # Business logic and services
│   ├── infrestructure/# Infrastructure (DB, auth, scheduler)
│   ├── models/        # SQLAlchemy ORM models
│   ├── schemas/       # Pydantic schemas
│   └── config.py      # Configuration
├── frontend/          # Jinja2 templates and static files (optional)
├── sql/               # DB scripts and schema diagram
├── tests/             # Unit and integration tests
├── main.py            # Application entry point
├── requirements.txt
├── requirements-test.txt
└── README.md
```

---

## Database Schema

- See `sql/DBschema.png` for a visual overview.
- To create the schema: `python sql/create_db.py`
- To populate with sample data: `python sql/populate_db.py`

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please follow best practices for REST API design, code style, and commit messages.

---

## License

This project is licensed under the MIT License.

---

**For any questions or support, please open an issue or contact the maintainer.**
