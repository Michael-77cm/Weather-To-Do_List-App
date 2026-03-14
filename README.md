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
- SQLite
- Open-Meteo geocoding and forecast APIs

## Features

- Sign up, log in, and log out with Django authentication
- Save user emails in the database through Django's user model
- Create, read, update, delete, and share tasks
- Organize tasks by `work`, `personal`, `shopping`, `business`, and `wish list`
- Mark tasks as `in progress` or `done`
- Configure recurring tasks (daily/weekly/monthly/yearly)
- Browse tasks on a monthly calendar and inspect a selected day
- Upload and remove file attachments per task
- Search for cities globally with autocomplete
- Display animated weather scenes for clear, cloudy, rain, snow, storm, and mist conditions
- Send share invite emails with accept/decline workflow and scheduled task reminder emails

## Install and run

Create and activate a virtual environment if needed, then install dependencies:

```bash
pip install -r requirements.txt






























