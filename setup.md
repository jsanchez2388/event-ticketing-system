# Event Ticketing System - Localhost Walkthrough

This guide covers using the EventHub website on localhost: creating an account,
buying a ticket, the local URLs, and what to do when something does not work.

It assumes the project is already installed. For installation - cloning, the
virtual environment, `pip install`, the `.env` file, and loading the databases -
follow [README.md](README.md).

---

# Before You Start

Complete the Setup and Database initialization steps in [README.md](README.md).
In short:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

cp .env.example .env           # then fill in your own values
```

`.env.example` documents every variable the application reads and marks which
ones are required. `POSTGRES_CONNECTION_STRING`, `MONGO_URI`, `MONGO_DB` and
`SESSION_SECRET` have no defaults. `ADMIN_SIGNUP_CODE` is required to register
an administrator account.

Start Redis, load PostgreSQL, then load MongoDB:

```bash
docker compose up -d                   # Redis on localhost:6379

psql "$POSTGRES_CONNECTION_STRING" -f sql/schema.sql
psql "$POSTGRES_CONNECTION_STRING" -f sql/seed.sql
psql "$POSTGRES_CONNECTION_STRING" -f sql/purchase_tickets.sql

python -m mongo.seed_event_content
python -m mongo.indexes
```

`sql/schema.sql` drops every ticketing table before recreating them. Check which
database your connection string points at before running it.

MongoDB and Redis are both optional at runtime, so the site still starts when
either is missing - the features that depend on them just go quiet. See
Troubleshooting below if event pages look empty or trending stays blank.

Start the server:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/site
```

Leave that terminal window open while using the website.

---

# Seeded Accounts

`sql/seed.sql` creates five accounts that can sign in immediately, so you do
not have to register one to test a purchase:

```text
maya.lopez@example.com     admin      wallet $1000.00
jordan.kim@example.com     customer   wallet $2500.00
avery.patel@example.com    customer   wallet  $500.00
noah.garcia@example.com    customer   wallet  $500.00
emma.nguyen@example.com    customer   wallet  $500.00
```

All five use the password `Comp642Demo!`.

These are sample accounts for local development. Delete them before any
deployment that is reachable from the internet.

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

# 1. Create an Account

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

# 2. Login

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

# 3. My Account

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

# 4. Buy a Ticket

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

# 5. Example Purchase

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

# 6. Test the PostgreSQL Connection

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

# 7. FastAPI API Documentation

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
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
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
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
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

## Event Pages Have No Speakers, Schedule or Reviews

The PostgreSQL fields appear but the MongoDB content does not, which means Mongo
is unreachable or the collection is empty. The site degrades quietly here
instead of raising an error.

Check that `.env` contains both:

```env
MONGO_URI=
MONGO_DB=
```

Then load the documents:

```bash
python -m mongo.seed_event_content
python -m mongo.indexes
```

Restart FastAPI after changing `.env`.

---

## Trending Is Empty, or Nothing Is Ever Cached

Redis is not running. Start it:

```bash
docker compose up -d
```

It should be listening on `localhost:6379`, which matches the defaults in
`.env.example`. Set `REDIS_HOST` and `REDIS_PORT` if it runs somewhere else.
Both the event cache and the trending sorted set depend on Redis.

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
venv/
__pycache__/
```
