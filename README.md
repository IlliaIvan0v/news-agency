# News Agency

A Django application for tracking newspapers, topics, and editors
responsible for each published issue.

## Features

- Newspaper management
- Topic management
- Editor management
- Multiple topics and publishers
- Authentication and registration
- Role-based permissions
- Search, filtering, and pagination
- Automated tests

## Installation

```bash
git clone <repository-url>
cd news-agency

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver