# ResidentDesk

ResidentDesk is a Flask-based apartment and flat management web app.
It provides separate workflows for admins and flat owners, including flat assignment, receipt upload, payment tracking, and profile management.

## Features

- Role-based login flow (`admin` and `flatowner`)
- Admin dashboard with summary metrics and recent uploads
- Manage flat owners (create and delete accounts)
- Manage flats and assign owners
- Upload monthly PDF receipts
- Track payment status by flat and billing period
- Flat owner dashboard with payment history and profile update

## Tech Stack

- Python 3
- Flask
- Flask-Session
- SQLite (`database.db`)
- HTML/CSS templates in `src/templates` and `src/static/styles`

## Project Structure

```text
ResidentDesk/
|-- main.py
|-- requirements.txt
|-- database.db
|-- vercel.json
`-- src/
    |-- __init__.py
    |-- routes.py
    |-- admin.py
    |-- flatOwner.py
    |-- utils.py
    |-- static/
    |   |-- receipts/
    |   `-- styles/
    `-- templates/
        |-- adminScreens/
        `-- flatownerScreens/
```

## Getting Started

### 1. Clone and enter the project

```powershell
git clone https://github.com/MuhammadFauzan98/ResidentDesk.git
cd ResidentDesk
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables (optional but recommended)

Create a `.env` file in the project root:

```env
SECRET_KEY=replace-with-a-strong-secret
```

If `SECRET_KEY` is not provided, the app uses a built-in development fallback.

### 5. Run the app

```powershell
python main.py
```

Open: `http://localhost:5000`

## Main Routes

- `/` - landing page
- `/login` - login form
- `/logout` - end session
- `/admin-dashboard` - admin dashboard
- `/manage-owners` - owner management
- `/manage-flats` - flat management
- `/upload-receipts` - receipt upload
- `/track-payments` - payment tracking
- `/dashboard` - flat owner dashboard
- `/payment-history` - flat owner payment history
- `/announcements` - flat owner announcements
- `/profile` - flat owner profile

## Deployment

The project includes `vercel.json` configured for Python deployment on Vercel.

## Notes

- Uploaded receipts are stored under `src/static/receipts`.
- The current implementation compares passwords directly (no hashing).
- `database.db` is used as the default local database file.
