# Coffee me

## Link to App

## Description
Is a corwdfunding platform to accept support from people that likes what you do.

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
GET | / | renders the homepage. if the user is not logged in, render access.
GET | /create-project | redirects to '/create-project'
POST | /create-project | create new project
POST | /buy-coffee | buy a coffee

## Tables

```
User table
- id: number
- username: text
- password: text
- coffees: number
- project: id
```
```
Project table
- id: number
- title: text
- description: text
- image: text
- coffees: number
```
```
Transaction table
- user_id: number
- creator: number
- created_at: date
- coffees: number
```

## Links
Github:
Slides: