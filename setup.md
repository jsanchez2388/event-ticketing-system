# Event Ticketing System - Localhost Website Setup

This guide explains how to download the project from GitHub and run the EventHub website locally.

The website runs using:

- FastAPI
- PostgreSQL / Neon
- Jinja2 HTML templates
- Python
- Uvicorn

Once setup is complete, the website will run at:

```text
http://127.0.0.1:8000/site
```

---

# 1. Clone the GitHub Repository

Open Terminal and run:

```bash
git clone https://github.com/jsanchez2388/event-ticketing-system.git
```

Enter the project folder:

```bash
cd event-ticketing-system
```

---

# 2. Create a Python Virtual Environment

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS:

```bash
source .venv/bin/activate
```

When activated, the Terminal should show something similar to:

```text
(.venv)
```

Example:

```text
(.venv) user@Mac event-ticketing-system %
```

---

# 3. Install the Required Python Packages

Run:

```bash
pip install -r requirements.txt
```

The project currently uses packages including:

```text
fastapi
uvicorn[standard]
psycopg2-binary
python-dotenv
jinja2
python-multipart
bcrypt
itsdangerous
email-validator
pymongo
redis
```

You do not need to install each package individually if:

```bash
pip install -r requirements.txt
```

completes successfully.

---

# 4. Create the `.env` File

The `.env` file is not stored on GitHub because it contains private information.

Create it in the root of the project:

```bash
touch .env
```

The project folder should look similar to:

```text
event-ticketing-system/
├── app/
├── sql/
├── mongo/
├── redis_demo/
├── requirements.txt
├── README.md
└── .env
```

Open `.env` and add:

```env
POSTGRES_CONNECTION_STRING=YOUR_NEON_POSTGRESQL_CONNECTION_STRING

SESSION_SECRET=YOUR_PRIVATE_SESSION_SECRET

ADMIN_SIGNUP_CODE=YOUR_ADMIN_CODE
```

Example:

```env
POSTGRES_CONNECTION_STRING=postgresql://username:password@hostname/neondb?sslmode=require

SESSION_SECRET=my-long-private-session-secret

ADMIN_SIGNUP_CODE=COMP642ADMIN2026
```

Do not upload the `.env` file to GitHub.

---

# 5. Get the Neon PostgreSQL Connection String

The application requires a PostgreSQL database.

Open your Neon account and select the project database.

Copy the PostgreSQL connection string.

It should look similar to:

```text
postgresql://username:password@ep-example.us-west-2.aws.neon.tech/neondb?sslmode=require
```

Place the connection string in:

```env
POSTGRES_CONNECTION_STRING=
```

inside `.env`.

Example:

```env
POSTGRES_CONNECTION_STRING=postgresql://username:password@hostname/neondb?sslmode=require
```

---

# 6. Set Up the PostgreSQL Database

If the Neon database is already populated for the project, this step can be skipped.

If you are creating a new database, use the Neon SQL Editor and run the SQL files in this order:

```text
1. sql/schema.sql
2. sql/sample_data.sql
3. sql/purchase_transaction.sql
```

The first file creates the relational schema.

The second file inserts the sample event data.

The third file creates the ticket purchase transaction.

The database contains tables including:

```text
users
venues
events
ticket_types
orders
order_items
payments
event_categories
event_category_map
```

---

# 7. Start the Local FastAPI Server

Make sure you are inside the project directory:

```bash
cd event-ticketing-system
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

If successful, Terminal should display something similar to:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Leave this Terminal window open while using the website.

---

# 8. Open the EventHub Website

Open a web browser.

Go to:

```text
http://127.0.0.1:8000/site
```

This opens the main EventHub page.

You should see the events stored in PostgreSQL.

---

# 9. Create an Account

Open:

```text
http://127.0.0.1:8000/site/signup
```

The signup page allows two account types:

```text
User
Admin
```

A new User receives a demo wallet balance of:

```text
$500.00
```

A new Admin receives:

```text
$1,000.00
```

Admin registration requires the code stored in:

```env
ADMIN_SIGNUP_CODE=
```

---

# 10. Login

Open:

```text
http://127.0.0.1:8000/site/login
```

Enter the email and password used during account creation.

After logging in, the user should be redirected to:

```text
http://127.0.0.1:8000/site/account
```

---

# 11. My Account

The My Account page is available at:

```text
http://127.0.0.1:8000/site/account
```

The page displays:

- User name
- Email
- Account type
- Account status
- Wallet balance
- Purchased tickets
- Order numbers
- Ticket quantities
- Ticket prices
- Payment information

A user must be logged in before accessing this page.

If the user is not logged in, FastAPI redirects them to:

```text
/site/login
```

---

# 12. Buy a Ticket

Open:

```text
http://127.0.0.1:8000/site
```

Select:

```text
View Event
```

The event page displays:

- Event name
- Venue
- Date
- Time
- Ticket type
- Ticket price
- Remaining ticket inventory
- Minimum purchase quantity
- Maximum purchase quantity

Choose the number of tickets and click:

```text
Buy
```

The application will:

```text
Check the user
      ↓
Check wallet balance
      ↓
Check ticket inventory
      ↓
Check purchase limits
      ↓
Create an order
      ↓
Create an order item
      ↓
Reduce ticket inventory
      ↓
Reduce wallet balance
      ↓
Create payment
      ↓
Complete purchase
```

After the purchase, the user is redirected to:

```text
/site/account
```

The new ticket should appear under:

```text
My Tickets
```

---

# 13. Example Purchase

A new normal User begins with:

```text
$500.00
```

If the user purchases one ticket costing:

```text
$125.00
```

their new wallet balance becomes:

```text
$375.00
```

The purchase will also appear in the user's account.

---

# 14. Test the PostgreSQL Connection

Open:

```text
http://127.0.0.1:8000/health/database
```

A successful database connection should return JSON similar to:

```json
{
    "status": "ok",
    "postgresql": "connected",
    "database": "neondb"
}
```

If this endpoint fails, check the:

```env
POSTGRES_CONNECTION_STRING=
```

value inside `.env`.

---

# 15. FastAPI API Documentation

FastAPI automatically creates interactive API documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

The Swagger page can be used to test the API endpoints.

---

# Important Local URLs

## Website

```text
http://127.0.0.1:8000/site
```

## Sign Up

```text
http://127.0.0.1:8000/site/signup
```

## Login

```text
http://127.0.0.1:8000/site/login
```

## My Account

```text
http://127.0.0.1:8000/site/account
```

## API Documentation

```text
http://127.0.0.1:8000/docs
```

## PostgreSQL Health Check

```text
http://127.0.0.1:8000/health/database
```

---

# Running the Project Again Later

After the initial setup, you do not need to recreate the virtual environment each time.

Open Terminal.

Enter the project folder:

```bash
cd event-ticketing-system
```

Activate the existing environment:

```bash
source .venv/bin/activate
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/site
```

---

# Updating the Local Project

If another team member updates the GitHub repository, stop FastAPI using:

```text
Control + C
```

Then run:

```bash
git pull origin main
```

If `requirements.txt` changed, run:

```bash
pip install -r requirements.txt
```

Then restart FastAPI:

```bash
uvicorn app.main:app --reload
```

---

# Stopping the Website

In the Terminal window running FastAPI, press:

```text
Control + C
```

This stops the localhost server.

To exit the Python virtual environment:

```bash
deactivate
```

---

# Troubleshooting

## Website Says `{"detail":"Not Found"}`

Make sure FastAPI is running:

```bash
uvicorn app.main:app --reload
```

Then check:

```text
http://127.0.0.1:8000/docs
```

Confirm that the website routes appear.

---

## Browser Says It Cannot Connect

FastAPI is probably not running.

Start it with:

```bash
uvicorn app.main:app --reload
```

Then reload:

```text
http://127.0.0.1:8000/site
```

---

## PostgreSQL Connection Error

Check `.env`.

Make sure:

```env
POSTGRES_CONNECTION_STRING=
```

contains the correct Neon PostgreSQL connection string.

After changing `.env`, restart FastAPI.

---

## `ModuleNotFoundError`

Make sure the virtual environment is active:

```bash
source .venv/bin/activate
```

Then reinstall the requirements:

```bash
pip install -r requirements.txt
```

---

## Signup Does Not Work

Make sure the PostgreSQL `users` table contains:

```text
role
wallet_balance
```

The valid roles are:

```text
user
admin
```

Also make sure:

```env
ADMIN_SIGNUP_CODE=
```

exists if creating an Admin account.

---

## Admin Signup Says Invalid Code

Check:

```text
.env
```

and verify:

```env
ADMIN_SIGNUP_CODE=YOUR_CODE
```

Restart FastAPI after changing `.env`.

---

## My Account Redirects to Login

The user is not currently logged in.

Open:

```text
http://127.0.0.1:8000/site/login
```

and log in.

---

## Ticket Purchase Fails

Possible reasons include:

```text
Not enough wallet balance
Not enough ticket inventory
Quantity exceeds maximum purchase
Quantity is below minimum purchase
User is not logged in
Invalid CSRF token
```

Check the FastAPI Terminal output for additional information.

---

# Security Notes

The localhost website currently includes:

```text
bcrypt password hashing
email validation
parameterized SQL
SQL injection protection
CSRF protection
signed sessions
role validation
wallet balance validation
transactional ticket purchasing
```

Passwords are not stored as plain text.

Database queries use parameterized SQL rather than directly inserting user input into SQL commands.

POST forms including:

```text
Signup
Login
Logout
Ticket Purchase
```

use CSRF tokens.

---

# Important Security Warning

Never commit the following to GitHub:

```text
.env
POSTGRES_CONNECTION_STRING
database passwords
SESSION_SECRET
ADMIN_SIGNUP_CODE
GitHub personal access tokens
```

The `.gitignore` file should contain:

```text
.env
.venv/
__pycache__/
```

---

# Quick Start

After cloning the repository, the basic setup is:

```bash
cd event-ticketing-system

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

touch .env
```

Add the required values to `.env`:

```env
POSTGRES_CONNECTION_STRING=YOUR_NEON_CONNECTION_STRING
SESSION_SECRET=YOUR_PRIVATE_SECRET
ADMIN_SIGNUP_CODE=YOUR_ADMIN_CODE
```

Then run:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/site
```

The EventHub localhost website should now be running.
