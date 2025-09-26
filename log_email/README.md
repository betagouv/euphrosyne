# Django External Email Log Admin

This Django app provides a **read-only email log interface** in the Django admin, using an external email provider (e.g., Mailjet, Sendgrid). It allows you to view sent emails and their details without storing any email data in your database.

---

## Features

- **Read-only admin list view** of emails retrieved via an API
- **Custom “ChangeView”** for email details, fetched live from the provider
- **Provider-agnostic architecture**: swap out Mailjet for another service easily
- **No database storage**: all data comes from the API on demand
- **Supports pagination and basic admin list display** using a fake QuerySet

---

## Architecture

### Models

- `EmailLog` – proxy model (`managed = False`) representing an email record.

### QuerySet Wrapper

- `EmailLogQuerySet` – a **faux QuerySet** that wraps a list of emails fetched from the provider.
  - Implements `__iter__`, `__len__`, `count()`, `filter()`, `order_by()`, and `_clone()`.
  - Provides a minimal `.query` attribute to satisfy Django admin expectations.

### Providers

- `BaseEmailProvider` – interface defining `list_messages`.
- `MailjetProvider` – concrete implementation for Mailjet API.

### Admin

- `EmailLogAdmin` – custom admin using `EmailLogQuerySet` for list display.
- `get_changelist_instance` is overridden to inject the fake queryset.

---

## Installation

1. Add the app to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'log_email',
]
```

2. For now, provider credentials are set using Django email environment variables : `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD` :

```python
MAILJET_API_KEY = "your_api_key"
MAILJET_SECRET_KEY = "your_secret"
```

3. Run the server and navigate to the Django admin to see the email log.

---

## Usage

### List view

- Displays a read-only list of emails with columns: `subject`, `to`, `status`, `date`.

---

## Extending to other providers

1. Create a new provider class implementing `BaseEmailProvider`.
2. Implement `list_messages` and `get_message`.
3. Add it to the factory in `emails/providers/__init__.py`.
4. TODO : Update `EMAIL_PROVIDER` in `settings.py` with the new provider.

---
