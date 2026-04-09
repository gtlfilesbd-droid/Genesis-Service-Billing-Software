# BillSoft — Service Billing Management System

Django + PostgreSQL দিয়ে তৈরি সম্পূর্ণ Service Billing Management System।

---

## ✅ Features

- **Login System** — Secure authentication
- **Role-Based Permissions** — Admin Panel থেকে প্রতিটি user-এর permission আলাদাভাবে set করুন
- **Client Management** — Client, Agreement ও Service manage করুন
- **Dynamic Bill Generation** — Agreement থেকে auto-load করে bill তৈরি
- **Invoice Export** — PDF, Excel (.xlsx), CSV, HTML Print
- **Reports & Analytics** — Monthly revenue chart, status breakdown, top clients
- **Dashboard** — Real-time summary cards

---

## 🚀 Installation & Setup

### 1. Project folder-এ যান
```bash
cd billing_project
```

### 2. Virtual environment তৈরি করুন
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### 3. Dependencies install করুন
```bash
pip install -r requirements.txt
```

### 4. PostgreSQL Database তৈরি করুন
```sql
-- PostgreSQL-এ লগইন করুন
psql -U postgres

-- Database ও user তৈরি করুন
CREATE DATABASE billing_db;
CREATE USER billing_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE billing_db TO billing_user;
\q
```

### 5. Settings configure করুন
`billing_system/settings.py` ফাইলে DATABASES section আপডেট করুন:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'billing_db',
        'USER': 'billing_user',
        'PASSWORD': 'your_strong_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 6. Migrations run করুন
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Superuser তৈরি করুন
```bash
python manage.py createsuperuser
```

### 8. Server চালু করুন
```bash
python manage.py runserver
```

Browser-এ যান: **http://127.0.0.1:8000**

---

## 🔐 User Permissions Setup (Admin Panel)

1. **http://127.0.0.1:8000/admin/** এ যান
2. **Users** section-এ user select করুন
3. **Permissions & Profile** section-এ নিচের permissions set করুন:

| Permission | কাজ |
|---|---|
| `can_add_client` | নতুন client যোগ করতে পারবে |
| `can_edit_client` | Client edit করতে পারবে |
| `can_delete_client` | Client delete করতে পারবে |
| `can_generate_bill` | Bill তৈরি করতে পারবে |
| `can_edit_bill` | Bill edit ও mark paid করতে পারবে |
| `can_view_reports` | Reports page দেখতে পারবে |
| `can_export_reports` | CSV/Excel export করতে পারবে |

> **Note:** Superuser সব কিছু করতে পারে, permission দরকার নেই।

---

## 📁 Project Structure

```
billing_project/
├── manage.py
├── requirements.txt
├── billing_system/          # Main project (settings, urls, views)
│   ├── settings.py
│   ├── urls.py
│   ├── views.py             # Dashboard view
│   └── templates/
│       ├── base.html        # Sidebar + Navbar
│       ├── dashboard/
│       ├── bills/
│       ├── clients/
│       ├── reports/
│       └── registration/
├── accounts/                # Login, logout, profile, UserProfile model
├── clients/                 # Client, Agreement, Service models
├── billing/                 # Bill, BillItem models + PDF/Excel export
└── reports/                 # Analytics, CSV/Excel export
```

---

## 📦 Bill Export Formats

| Format | URL | Package |
|---|---|---|
| PDF | `/billing/<id>/pdf/` | `weasyprint` |
| HTML Print | `/billing/<id>/print/` | Built-in |
| Excel | `/billing/<id>/excel/` | `openpyxl` |
| CSV (bulk) | `/reports/export/csv/` | Built-in |
| Excel (bulk) | `/reports/export/excel/` | `openpyxl` |

---

## 🛠 Troubleshooting

**WeasyPrint install error (Windows):**
WeasyPrint requires GTK libraries on Windows. Alternative:
```bash
pip install reportlab  # lighter alternative
```
Or use the HTML print view instead.

**psycopg2 error:**
```bash
pip install psycopg2-binary
```

**Static files not loading:**
```bash
python manage.py collectstatic
```
