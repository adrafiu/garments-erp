# Buyer Management API

## Overview

The Buyer Management API manages buyer companies in the Garments ERP system.

**Base URL (development):**

`http://127.0.0.1:8000/api/buyers/`

**Technology:** Django, Django REST Framework, SQLite.

## Buyer Fields

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Unique buyer ID, generated automatically |
| `name` | String | Buyer company name; required and unique (case-insensitive) |
| `contact_person` | String | Buyer's contact person |
| `email` | Email | Buyer's email address |
| `phone` | String | Contact phone number |
| `address` | String | Buyer company address |
| `country` | String | Two-letter country code, e.g. `BD` |
| `is_active` | Boolean | Whether the buyer is active |
| `created_at` | DateTime | Automatically set when created |
| `updated_at` | DateTime | Automatically updated when saved |

Optional text fields can be left blank. `is_active` defaults to `true`.

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/buyers/` | List buyers |
| `POST` | `/api/buyers/` | Create a buyer |
| `GET` | `/api/buyers/{id}/` | Retrieve a buyer |
| `PUT` | `/api/buyers/{id}/` | Replace/update a buyer |
| `PATCH` | `/api/buyers/{id}/` | Partially update a buyer |
| `DELETE` | `/api/buyers/{id}/` | Delete a buyer |

## Create a Buyer

**Request**

`POST /api/buyers/`

Example JSON body:

```json
{
  "name": "ABC Fashion Ltd.",
  "contact_person": "Rahim Ahmed",
  "email": "buyer@example.com",
  "phone": "+8801712345678",
  "address": "Dhaka, Bangladesh",
  "country": "BD",
  "is_active": true
}
```

The `id`, `created_at`, and `updated_at` fields are generated automatically.

## List Buyers

**Request**

`GET /api/buyers/`

The response is paginated. Example:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "ABC Fashion Ltd.",
      "contact_person": "Rahim Ahmed",
      "email": "buyer@example.com",
      "phone": "+8801712345678",
      "address": "Dhaka, Bangladesh",
      "country": "BD",
      "is_active": true,
      "created_at": "2026-10-20T08:00:00Z",
      "updated_at": "2026-10-20T08:00:00Z"
    }
  ]
}
```

The example timestamps are illustrative; actual values depend on the database and timezone settings.

## Retrieve a Buyer

**Request**

`GET /api/buyers/1/`

Replace `1` with the buyer's actual ID.

## Update a Buyer

Use `PUT` to submit a complete update, or `PATCH` to change only selected fields.

**Example**

`PATCH /api/buyers/1/`

```json
{
  "phone": "+8801812345678",
  "is_active": false
}
```

## Delete a Buyer

**Request**

`DELETE /api/buyers/1/`

A successful deletion returns HTTP `204 No Content`.

## Search, Filtering and Ordering

### Search

Search by company name, contact person, or email.

`GET /api/buyers/?search=fashion`

### Filter by active status

`GET /api/buyers/?is_active=true`

### Filter by country

`GET /api/buyers/?country=BD`

### Order results

Sort alphabetically by name:

`GET /api/buyers/?ordering=name`

Show recently updated buyers first:

`GET /api/buyers/?ordering=-updated_at`

### Pagination

The default page size is 10 buyers.

`GET /api/buyers/?page=1`

You can combine supported search, filtering, ordering, and pagination parameters.

## Validation and Errors

- **HTTP 400 Bad Request:** Invalid input, invalid email, or duplicate company name.
- **HTTP 404 Not Found:** The requested buyer does not exist.
- **HTTP 204 No Content:** Buyer deleted successfully.

Company names are checked case-insensitively to prevent duplicates such as `ABC Fashion Ltd.` and `abc fashion ltd.`.

Example duplicate-name error:

```json
{
  "name": [
    "A buyer with this company name already exists."
  ]
}
```

## Development Notes

- Run the Django development server from the backend directory.
- The API currently uses SQLite for development.
- Authentication and production permissions must be configured before exposing this API publicly.
