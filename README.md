# Coderr – Backend

REST API for **Coderr**, a freelancer platform for developers.
Business users publish offers with three packages (basic, standard,
premium), customers order these packages and review the business users.

This repository contains **only the backend**. The frontend (Vanilla JS)
is provided separately by the Developer Akademie and talks to this API.

Built with **Django** and **Django REST Framework**, using token
authentication.

## Live demo

| Part      | URL                                            | Hosting        |
|-----------|------------------------------------------------|----------------|
| Frontend  | <https://coderr.dimit.cc>                      | Namecheap      |
| API       | <https://milosdimi2.pythonanywhere.com/api/>   | PythonAnywhere |

Log in with one of the [guest accounts](#guest-login) or register your own
account. The live API uses its own database, separate from any local
installation.

---

## Table of contents

- [Live demo](#live-demo)
- [Tech stack](#tech-stack)
- [Requirements](#requirements)
- [Installation](#installation)
- [Run the server](#run-the-server)
- [Connect the frontend](#connect-the-frontend)
- [Guest login](#guest-login)
- [Authentication](#authentication)
- [API endpoints](#api-endpoints)
- [Permissions](#permissions)
- [Special notes](#special-notes)
- [Run the tests](#run-the-tests)
- [Project structure](#project-structure)

---

## Tech stack

| Package               | Purpose                                     |
|-----------------------|---------------------------------------------|
| Django                | Web framework, ORM, admin                   |
| djangorestframework   | REST API, serializers, token auth           |
| django-filter         | Query parameter filters for lists           |
| django-cors-headers   | Allows requests from the frontend           |
| Pillow                | Image uploads (profile pictures, offers)    |
| coverage              | Test coverage report                        |
| pycodestyle           | PEP 8 check                                 |

Exact versions are listed in [`requirements.txt`](requirements.txt).

## Requirements

- Python **3.12 or newer** (developed with Python 3.14)
- Git

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/milosdimi/coderr-backend.git
```

```bash
cd coderr-backend
```

**2. Create a virtual environment**

```bash
python -m venv env
```

**3. Activate the virtual environment** (choose your system)

Windows:

```bash
env\Scripts\activate
```

macOS / Linux:

```bash
source env/bin/activate
```

**4. Install the dependencies**

```bash
pip install -r requirements.txt
```

**5. Create the database** (this also creates the two guest users)

```bash
python manage.py migrate
```

**6. Optional: create an admin account for `/admin/`**

```bash
python manage.py createsuperuser
```

The SQLite database (`db.sqlite3`) and uploaded files (`media/`) are
**not** part of the repository. The database is created locally by
`python manage.py migrate`.

## Run the server

```bash
python manage.py runserver
```

- API: <http://127.0.0.1:8000/api/>
- Admin panel: <http://127.0.0.1:8000/admin/>

### Environment variables (deployment)

Locally nothing has to be set. On a server the following environment
variables configure the project (lists are comma separated):

| Variable                       | Local default                                   | Example on a server               |
|--------------------------------|-------------------------------------------------|-----------------------------------|
| `DJANGO_SECRET_KEY`            | development key (insecure)                      | a long random string              |
| `DJANGO_DEBUG`                 | `True`                                          | `False`                           |
| `DJANGO_ALLOWED_HOSTS`         | `127.0.0.1,localhost`                           | `coderr-api.example.com`          |
| `DJANGO_CORS_ALLOWED_ORIGINS`  | `http://127.0.0.1:5500,http://localhost:5500`   | `https://coderr.example.com`      |
| `DJANGO_CSRF_TRUSTED_ORIGINS`  | empty                                           | `https://coderr-api.example.com`  |

On the server also run `python manage.py collectstatic` once, so the
admin panel gets its CSS and JavaScript. Uploaded images are stored in
`media/` and served under `/media/`; Django serves them itself only while
`DEBUG` is `True`, so on a server `/media/` has to be mapped to the
`media/` folder in the web server settings.

## Connect the frontend

1. Start this backend (see above). The frontend expects the API at
   `http://127.0.0.1:8000/api/` (see `shared/scripts/config.js` in the
   frontend).
2. Open the frontend project in VS Code and start `index.html` with the
   **Live Server** extension.
3. CORS is enabled for `http://127.0.0.1:5500` and `http://localhost:5500`
   (the default Live Server addresses). If your Live Server uses another
   port, set `DJANGO_CORS_ALLOWED_ORIGINS` (see the table above).

## Guest login

The frontend has two guest login buttons. The matching users (with their
profiles) are created automatically by a data migration when you run
`python manage.py migrate`:

| Type     | Username | Password   |
|----------|----------|------------|
| Customer | `andrey` | `asdasd`   |
| Business | `kevin`  | `asdasd24` |

## Authentication

Registration and login return a token. Protected requests must send it
in the `Authorization` header:

```
Authorization: Token <your-token>
```

Requests to protected endpoints without a valid token are answered with
`401 Unauthorized`.

## API endpoints

All endpoints start with `/api/`.

### Authentication

| Method | Endpoint         | Description                                          |
|--------|------------------|------------------------------------------------------|
| POST   | `/registration/` | Create a customer or business account, returns a token |
| POST   | `/login/`        | Log in with username and password                    |

### Profiles

| Method | Endpoint               | Description                                 |
|--------|------------------------|---------------------------------------------|
| GET    | `/profile/{user_id}/`  | Profile of a user                           |
| PATCH  | `/profile/{user_id}/`  | Update the own profile (incl. picture)      |
| GET    | `/profiles/business/`  | All business profiles                       |
| GET    | `/profiles/customer/`  | All customer profiles                       |

### Offers

| Method | Endpoint                  | Description                                     |
|--------|---------------------------|-------------------------------------------------|
| GET    | `/offers/`                | Paginated offer list with filters (see below)   |
| POST   | `/offers/`                | Create an offer with exactly three details      |
| GET    | `/offers/{id}/`           | Single offer                                    |
| PATCH  | `/offers/{id}/`           | Update an offer and/or single details           |
| DELETE | `/offers/{id}/`           | Delete an offer with its details                |
| GET    | `/offerdetails/{id}/`     | Single offer detail (package)                   |

Query parameters of `GET /offers/`:

| Parameter           | Description                                                  |
|---------------------|--------------------------------------------------------------|
| `creator_id`        | Only offers of this user                                     |
| `min_price`         | Offers whose cheapest package costs at least this value      |
| `max_delivery_time` | Offers whose fastest package is delivered within these days  |
| `search`            | Searches in `title` and `description`                        |
| `ordering`          | `updated_at`, `-updated_at`, `min_price`, `-min_price`       |
| `page`, `page_size` | Pagination, 6 offers per page by default                     |

### Orders

| Method | Endpoint                                     | Description                                  |
|--------|----------------------------------------------|----------------------------------------------|
| GET    | `/orders/`                                   | Orders of the user (as customer or business) |
| POST   | `/orders/`                                   | Order an offer detail (`offer_detail_id`)    |
| PATCH  | `/orders/{id}/`                              | Change the status of an order                |
| GET    | `/order-count/{business_user_id}/`           | Number of orders in progress                 |
| GET    | `/completed-order-count/{business_user_id}/` | Number of completed orders                   |

Allowed status values: `in_progress`, `completed`, `cancelled`.

### Reviews

| Method | Endpoint          | Description                                              |
|--------|-------------------|----------------------------------------------------------|
| GET    | `/reviews/`       | Reviews, filter `business_user_id`, `reviewer_id`; `ordering` by `updated_at` or `rating` |
| POST   | `/reviews/`       | Review a business user (rating 1–5)                      |
| PATCH  | `/reviews/{id}/`  | Change rating and/or description                         |
| DELETE | `/reviews/{id}/`  | Delete a review                                          |

### Platform statistics

| Method | Endpoint       | Description                                                     |
|--------|----------------|-----------------------------------------------------------------|
| GET    | `/base-info/`  | Number of reviews, average rating, business profiles and offers |

## Permissions

| Action                                  | Allowed for                               |
|-----------------------------------------|-------------------------------------------|
| Registration, login                     | everyone                                  |
| Offer list, base info                   | everyone (no login needed)                |
| All other endpoints                     | logged-in users only                      |
| Update a profile                        | the profile owner only                    |
| Create an offer                         | business users only                       |
| Update / delete an offer                | the offer creator only                    |
| Create an order                         | customer users only                       |
| Update the status of an order           | the business user of the order only       |
| Create a review                         | customer users only, once per business    |
| Update / delete a review                | the reviewer only                         |

Status codes follow the documentation: `400` invalid data, `401` not
logged in, `403` no permission, `404` object not found.

## Special notes

- **Login with username:** users log in with their username. Emails are
  unique as well and are stored in lower case.
- **User id in URLs:** `/profile/{user_id}/`, `creator_id`,
  `business_user`, `customer_user` and `reviewer` always use the id of the
  Django user, not the id of the profile.
- **Empty profile fields** (`first_name`, `last_name`, `location`, `tel`,
  `description`, `working_hours`) are returned as `""`, never as `null`.
- **Exactly three details per offer:** creating an offer requires one
  detail of each type `basic`, `standard` and `premium`. `revisions: -1`
  means unlimited revisions, `delivery_time_in_days` must be at least 1,
  the price may be sent as number or string.
- **Updating offer details:** details are identified by their
  `offer_type`; their ids stay the same. Details that are not sent stay
  unchanged.
- **`min_price` and `min_delivery_time`** are not stored but calculated
  from the details for every request, so filters and ordering are always
  correct.
- **Orders are a copy:** an order copies title, price, features etc. of
  the ordered offer detail, so it stays the same when the offer changes
  later.
- **Only the documented fields can be changed:** an order accepts only
  `status`, a review only `rating` and `description`; other fields return
  `400`.
- **Duplicate reviews:** a second review of the same customer for the same
  business user returns `400`.
- **Images** (`file` of a profile, `image` of an offer) are uploaded with
  `PATCH` as `multipart/form-data` and returned as absolute URLs.
- **Only documented methods:** updates are done with `PATCH`; `PUT`, and
  methods that are not documented (e.g. `DELETE /orders/{id}/`), return
  `405`.
- **Outdated tokens:** registration, login and base info ignore the
  `Authorization` header, so an old token in the browser cannot block
  them.

## Run the tests

**Run all tests**

```bash
python manage.py test
```

**Measure the coverage** (run the tests first, then show the report)

```bash
coverage run manage.py test
```

```bash
coverage report
```

**PEP 8 check** (migrations are generated by Django and excluded)

```bash
python -m pycodestyle --exclude=env,migrations .
```

The test suite covers every endpoint including the error cases and
reaches **100 % coverage**. The coverage settings are in `.coveragerc`.

## Project structure

```
coderr-backend/
├── core/                    # project settings and central URL routing
├── auth_app/                # registration, login and user profiles
│   ├── api/                 # serializers, views, urls, permissions
│   ├── migrations/          # incl. data migration for the guest users
│   ├── models.py            # UserProfile
│   └── tests/               # incl. helpers.py shared by all apps
├── offers_app/              # offers and offer details
│   ├── api/                 # serializers, views, urls, permissions,
│   │                        # filters, pagination
│   ├── models.py            # Offer, OfferDetail
│   └── tests/
├── orders_app/              # orders and order counts
│   ├── api/
│   ├── models.py            # Order
│   └── tests/
├── reviews_app/             # reviews
│   ├── api/                 # incl. filters
│   ├── models.py            # Review
│   └── tests/
├── base_info_app/           # platform statistics (no own models)
│   ├── api/
│   └── tests/
├── manage.py
├── requirements.txt
└── .coveragerc
```
