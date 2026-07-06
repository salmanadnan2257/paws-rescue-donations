# Paws Rescue Donations

A Django 4.2 web app for tracking donations at a pet rescue, built for a faculty-supervised Khidmat community-service project at Habib University. Rescue staff log in with an email and password, record donations against individual pets, filter and export the records, and see running totals on a dashboard. There is no public-facing side: the whole app sits behind an admin login.

## Why it exists

Small rescues usually track donations in a spreadsheet. That breaks down once several people are entering records: no access control, no consistent fields, no easy way to answer "how much has Bella received this month". This app replaces the spreadsheet with a single database and a login, while staying simple enough to run on a free hosting tier.

## Features

- Email/password login with a custom user model (no usernames, no public signup)
- Donation CRUD with donor contact info, pet name, amount, currency, payment method, reference number, and notes
- Filtering by donor or pet name, date range, payment method, currency, and amount range
- Sorting by date or amount, paginated at 20 rows per page
- Dashboard analytics: all-time total, filtered total, and top 5 pets by donation amount (within the current filters)
- CSV export of the currently filtered result set
- Admin user management from the web UI (create admins, delete any admin but yourself)
- `create_initial_admin` management command that bootstraps the first admin from environment variables

## Architecture

Two Django apps under `apps/`:

- `accounts`: custom `User` model (UUID primary key, email as `USERNAME_FIELD`, managed by a custom `UserManager`), login/logout views, and the admin-management views. All protected views require `is_staff`.
- `donations`: the `Donation` model plus dashboard, CRUD, and CSV export views. Filtering is a plain Django form (`DonationFilterForm`) whose cleaned data drives queryset filters in `dashboard_view`. The dashboard stores the filtered donation IDs in the session so the export view can reproduce the same result set.

Everything is server-rendered with Django templates on a Bootstrap 5 base layout. `settings.py` reads configuration from environment variables via python-dotenv, uses PostgreSQL when `DATABASE_URL` is set and SQLite otherwise, and serves static files through Whitenoise. A `Procfile` runs Gunicorn for platforms like Render or Railway.

## Setup

Requires Python 3.9+.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit the values
python manage.py migrate
python manage.py create_initial_admin
python manage.py runserver
```

Open http://localhost:8000 and log in with the credentials you put in `.env` (`INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD`). With `DATABASE_URL` empty the app uses a local SQLite file, which is fine for development.

Run the tests with:

```bash
python manage.py test
```

Eleven tests cover auth redirects, admin creation and self-deletion protection, donation CRUD, filtering, amount validation, and the CSV export.

## Usage

- Add donations from the dashboard's "Add Donation" button. Donor name, pet name, and amount are required; phone, email, reference number, and notes are optional.
- Filter with the sidebar form. Totals and the top-pets panel update to match the filters.
- "Export CSV" downloads whatever the current filters show.
- The "Admins" page lists staff users and lets you add or remove them. You can't delete your own account.

## Deployment

The repo is set up for a Gunicorn-based host (Render, Railway, or similar) with a managed PostgreSQL database.

Build step: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
Start command: `gunicorn paws_rescue.wsgi`

Set these environment variables (see `.env.example` for descriptions): `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `DATABASE_URL`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD`. Run `python manage.py create_initial_admin` once after the first deploy. With `DEBUG=False` the app forces HTTPS and secure cookies, so it needs to run behind TLS.

## License

MIT, see `LICENSE`.

## Challenges

- Production security settings broke the whole test suite. With `DEBUG=False`, `SECURE_SSL_REDIRECT` turned every test-client request into a 301 to https, and the Whitenoise manifest storage raised errors because tests never run `collectstatic`. Fixed with a `TESTING = 'test' in sys.argv` flag in `settings.py` that skips the security block and swaps in Django's plain `StaticFilesStorage` during test runs.
- The dashboard's top-5-pets panel was built from `Donation.objects.all()`, so it ignored whatever filters the user had applied and contradicted the filtered total shown next to it. The fix aggregates over the already-filtered `donations` queryset instead (`values('pet_name').annotate(Sum, Count)` in `dashboard_view`), so the panel now answers "top pets within this filter".
- `assertNotContains(response, 'Max')` failed on a page that genuinely had no donation for the pet Max, because the filter form's "Max Amount" label contained the substring. Resolved by renaming the labels to "Amount From" and "Amount To" so no form text collides with test data. The test still asserts on page text, which is fragile; see below.
- Filtering had to work with every combination of seven optional inputs. Each filter is applied only when its cleaned value is present, with an explicit `is not None` check for the amount bounds so a legitimate `0` isn't skipped, and `currency__iexact` so "pkr" and "PKR" match the same rows.
- Dropping usernames meant rebuilding the auth plumbing. `User` subclasses `AbstractBaseUser` + `PermissionsMixin` with a UUID primary key and `USERNAME_FIELD = 'email'`, so Django's default manager (which expects a `username` argument) no longer fit. A custom `UserManager` reimplements `create_user`/`create_superuser` to take `email`, normalise it, and force `is_staff`/`is_superuser` on superusers, wired up through `AUTH_USER_MODEL = 'accounts.User'`. The catch, visible in the tests, is that `Client.login()` still expects the keyword `username=`, so the tests pass the email as `username='admin@test.com'`.
- CSV export needed to reproduce exactly what the dashboard showed after filtering, but the export link is a plain GET with no form state. The working compromise stores the filtered donation IDs in the session on each dashboard render and reads them back in `export_csv_view`. It works, but it's the weakest part of the design (see the next two sections).

## What I learned

- Gate production-only settings on an explicit test flag, not just `DEBUG`. `manage.py test` doesn't set `DEBUG=True`, so anything conditioned only on `not DEBUG` (SSL redirects, manifest static storage) silently applies to the test client too.
- `ManifestStaticFilesStorage` and friends depend on a build step. Any code path that hits `{% static %}` will crash in tests or fresh checkouts unless `collectstatic` ran or the storage backend is swapped.
- Aggregate off the queryset you already filtered. Building analytics from a fresh `objects.all()` next to a filtered list is an easy way to ship numbers that disagree with the table beside them.
- `assertContains`/`assertNotContains` match raw substrings across the entire HTML response, chrome included. Either keep test fixture strings out of the UI's vocabulary or assert on structured data instead of page text.
- A custom user model with `USERNAME_FIELD = 'email'` has to be in place before the first migration. Swapping it later means rebuilding the migration history, so it's a decision to make on day one.
- Sessions are a poor transport for query state. Persisting filtered IDs per request grows the session with the table and desynchronizes from the database; re-deriving the queryset from the query string is the pattern I'd reach for next time.

## What I'd do differently

- Drop the session-based CSV export. The dashboard writes every filtered donation ID into the session, which grows without bound as records accumulate and goes stale if data changes between page load and export. The export view should re-apply the filter form to the query string instead.
- Use `django-filter` or at least a shared helper for filtering. `dashboard_view` applies seven filters field by field, and the export view can't reuse any of it.
- Make the tests assert on data, not page text. One test failed because `assertNotContains(response, 'Max')` matched the "Max Amount" form label; I had to rename the label to "Amount To" to keep the test honest. Asserting on the queryset or on specific table cells would avoid that class of false positive.
- Split settings into base/dev/prod modules. Right now production security flags are gated on `DEBUG` plus a `'test' in sys.argv` check, which works but is fragile.
- Add database indexes on `donation_date` and `pet_name`. Both drive the default ordering and the top-pets aggregation, and neither is indexed.
- Record who entered each donation. `Donation` has no foreign key to `User`, so there's no audit trail, and deletes are hard deletes.
- Validate `currency` against a choice list. It's a free-text field defaulting to PKR, so typos ("pkr", "Rs") would silently split the totals.
