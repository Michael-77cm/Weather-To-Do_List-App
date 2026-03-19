# Weather-To-Do_List
# :sparkles: Welcome to Weather To-Do List :sparkles:
:point_right: View the live project here: :point_right: https://weather-to-do-list-e7b16ee62076.herokuapp.com/
<img width="3297" height="1671" alt="image" src="https://github.com/user-attachments/assets/c8070ac2-9539-400c-a78b-4468b145250f" />


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

---
***
___


#
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

## Features (User Stories)
As a user of the site I should be able to: 

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

:point_right: Link to Kanban board of Userstories: :point_right: https://github.com/users/Michael-77cm/projects/5 :point_left:

Once a task is successful created, this notification pops up at this top of the screen: 
<img width="2886" height="153" alt="image" src="https://github.com/user-attachments/assets/a085a778-4260-4ef5-bb49-6aae96917d1b" />
Once a task is successfully edited, this notication pops up at the top of the screen: 
<img width="2838" height="141" alt="image" src="https://github.com/user-attachments/assets/be4eb028-4a17-4c2d-a90e-0666a2756e19" />
Once you try to delete a task, this notication pops up at the top of the screen: 
<img width="500" height="255" alt="image" src="https://github.com/user-attachments/assets/5433df75-6972-4849-a7f4-580147a1dacf" />

Once a task is completely deleted, this notification pops up at the top of the screen: 
<img width="2832" height="141" alt="image" src="https://github.com/user-attachments/assets/70667d53-d0f5-4f5f-83d0-6ed344c3d679" />


User Experience 
- :white_check_mark: User Stories :white_check_mark:

## Design 
# :chart_with_upwards_trend: Wireframe Diagram :chart_with_upwards_trend:
<img width="3342" height="1443" alt="image" src="https://github.com/user-attachments/assets/455b4789-5199-4266-b4ad-97447e9a4fbe" />


# :newspaper: Entity Relationship Diagram (ERD) :newspaper:
<img width="2688" height="1398" alt="image" src="https://github.com/user-attachments/assets/70519142-8b3b-4da5-a9ea-9ebb917932c8" />



## Deployment and how to deploy
The project is currently deployed on Heroku, you can find it by following the link below: :point_down:
:point_down: :point_down: :point_down: :point_down:

:point_right:(https://weather-to-do-list-e7b16ee62076.herokuapp.com/) :point_left:



Cloning and Setting Up Locally
Follow these steps to clone the repository and set it up on your local machine:

Clone the Repository:

Open your terminal and run:
git clone https://github.com/Michael-77cm/Weather-To-Do_List.git 
cd weather-to-do_List

Set Up a Virtual Environment:
Create and activate a virtual environment:
- python -m venv .venv
- source venv/bin/activate  # On Windows: venv\Scripts\activate

Install Dependencies:
Install the required Python packages:
- pip install -r requirements.txt

Set Up Environment Variables:
- Create a .env file in the root directory and add the following:
- SECRET_KEY=your-secret-key
- DATABASE_URL=sqlite:///db.sqlite3  # Or your database URL
- DEBUG=True

Run Migrations:
Apply database migrations:
- python manage.py migrate

Run the Development Server:
Start the Django development server:
- python manage.py runserver

Access the App:

Open your browser and go to:
- http://127.0.0.1:8000/
Your app is now running locally!

## Credit 
In putting together this project 
AI was used for putting together the base structure of code and troubleshooting code errors. 

Author
Michael Bello

GitHub: https://github.com/Michael-77cm/ 























