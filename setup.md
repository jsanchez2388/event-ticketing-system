# Event Ticketing System

COMP 642 project implementing an event ticketing platform using FastAPI and PostgreSQL.

The current version supports:

- User and Admin account creation
- Secure login/logout
- Password hashing with bcrypt
- Email validation
- PostgreSQL hosted with Neon
- Event browsing
- Event detail pages
- Ticket inventory
- Ticket purchasing
- Demo wallet balances
- User purchase history
- SQL transaction handling
- SQL injection protection through parameterized queries
- CSRF protection for POST forms
- FastAPI REST endpoints
- Postman / Swagger API testing

MongoDB and Redis are planned as the next phases of the project.

---

# Project Structure

```text
event-ticketing-system/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── security.py
│   │
│   ├── database/
│   │   └── postgres.py
│   │
│   ├── routers/
│   │   ├── events.py
│   │   ├── analytics.py
│   │   ├── web.py
│   │   ├── auth.py
│   │   └── account.py
│   │
│   ├── services/
│   │   ├── event_service.py
│   │   ├── analytics_service.py
│   │   ├── web_service.py
│   │   ├── auth_service.py
│   │   ├── account_service.py
│   │   └── purchase_service.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── events.html
│   │   ├── event_detail.html
│   │   ├── signup.html
│   │   ├── login.html
│   │   └── account.html
│   │
│   └── static/
│       └── css/
│           └── style.css
│
├── sql/
│   ├── schema.sql
│   ├── sample_data.sql
│   ├── queries.sql
│   └── purchase_transaction.sql
│
├── mongo/
├── redis_demo/
├── experiments/
├── requirements.txt
├── .gitignore
└── README.md
