# Weather-To-Do_List
# :sparkles: Welcome to Weather To-Do List :sparkles:
View the live project here: 

Stay organised with a to‑do list that adapts to the weather. This app combines your tasks with real‑time forecasts so you can plan smarter, avoid surprises, and make the most of every day. Whether it’s sunshine, rain, or anything in between, your schedule adjusts automatically to keep you on track.

##
## :scroll:Table of Contents:scroll:  
- [User Experience (UX)](UX)
- [Features](Features)
- [Design](Design)
- [Technologies Used](T)
- [Testing](T)
- [Deployment](D)
- [Credits](C)

User Experience 

- :white_check_mark: User Stories :white_check_mark:


# :chart_with_upwards_trend: Wireframe Diagram :chart_with_upwards_trend:
<img width="3342" height="1443" alt="image" src="https://github.com/user-attachments/assets/455b4789-5199-4266-b4ad-97447e9a4fbe" />


# :newspaper: Entity Relationship Diagram (ERD) :newspaper:
<img width="2688" height="1398" alt="image" src="https://github.com/user-attachments/assets/70519142-8b3b-4da5-a9ea-9ebb917932c8" />


# WeatherToDoList

WeatherToDoList is a Django web app that combines:

- user authentication
- a live weather search experience for cities worldwide
- a calendar-backed task manager for any day of the year
- task categories, status tracking, CRUD operations, sharing, and email reminders

## Stack

- Django
- HTML, CSS, JavaScript
- PostgreSQL
- Open-Meteo geocoding and forecast APIs

## Features

- :white_check_mark:Sign up, log in, and log out with Django authentication
- :white_check_mark:Save user emails in the database through Django's user model
- :white_check_mark:Create, read, update, delete, and share tasks
- :white_check_mark:Organize tasks by `work`, `personal`, `shopping`, `business`, and `wish list`
- :white_check_mark:Mark tasks as `in progress` or `done`
- :white_check_mark:Configure recurring tasks (daily/weekly/monthly/yearly)
- :white_check_mark:Browse tasks on a monthly calendar and inspect a selected day
- :white_check_mark:Upload and remove file attachments per task
- :white_check_mark:Search for cities globally with autocomplete
- :white_check_mark:Display animated weather scenes for clear, cloudy, rain, snow, storm, and mist conditions
- :white_check_mark:Send share invite emails with accept/decline workflow and scheduled task reminder emails

## Install and run

Create and activate a virtual environment if needed, then install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file at the project root (you can copy from `.env.example`).
Django now auto-loads `.env`, so you do not need to prefix DB variables on every command.

Run the app:

```bash
python manage.py runserver
```

## Move Existing SQLite Data To PostgreSQL

If you have existing data in `WeatherToDoList/db.sqlite3`, migrate it to PostgreSQL with the steps below.

1. Create a PostgreSQL database (example name: `weather_todo_db`).
2. Add your PostgreSQL values to `.env`:

```bash
DB_NAME=weather_todo_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

3. Export data from SQLite:

```bash
DATABASE_URL="sqlite:///WeatherToDoList/db.sqlite3" python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > data.json
```

4. Run migrations against PostgreSQL:

```bash
python manage.py migrate
```

5. Import the exported data into PostgreSQL:

```bash
python manage.py loaddata data.json
```






























