# News Agency

Internal issue-tracking system for a news agency.

## Check it out!

[News Agency deployed to Render]([https://your-app.onrender.com](https://news-agency-5h0w.onrender.com))

## Installation

Python 3.11+ must already be installed.

```bash
git clone https://github.com/IlliaIvan0v/news-agency.git
cd news-agency

python -m venv venv
source venv/bin/activate    # Linux/macOS
# venv\Scripts\activate     # Windows

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Features

- Custom Redactor model
- Newspaper management
- Topic management
- Multiple responsible editors
- Multiple topics per newspaper
- Authentication & registration
- Password change
- Search and filtering
- Pagination
- Role-based permissions
- Dashboard statistics

