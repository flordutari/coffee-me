# Coffee me.

## Video demo
https://youtu.be/oYOhYqqFTrc
## Description
Is a corwdfunding platform to accept support from people that likes what you do.
Built in Flask(Python), SQL, JS, HTML, CSS
## Utilities
You'll be able to:
- Create an account
- Post details about your job
- Receive coffees as a way of monetize your service

## Routes
|Method|URL|Description|
|---|---|---|
GET | /login | redirects to '/' if user logged in. Renders '/login'
POST | /login | redirects to '/' if user logged in
GET | /signup| redirects to '/' if user logged in. Renders '/signup'
POST | /signup| redirects to '/' if user logged in
POST | /logout | logout user
GET | / | renders the homepage
GET | /projects | list all projects
GET | /project-:id | render a specific project
GET | /my-project | redirects to '/my-project'
POST | /my-project | create new project
POST | /buy-coffee | buy a coffee

## Tables

```
User table
- id: int
- name: varchar
- surname: varchar
- password: varchar
- coffees: int
- cash: int
```
```
Project table
- id: int
- user_id: int
- title: varchar
- description: varchar
- image: varchar
- coffees: int
```
```
Transaction table
- id: int
- user_id: int
- project_id: int
- created_at: date
- coffees: int
- coffee_price: int
- coffee_price_curr: varchar
```

## Links
Github: https://github.com/flordutari/coffee-me