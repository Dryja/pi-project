# Project for web and mobile programming classes

Built in Flask. Redis as a database + RabbitMQ for tasking thumbnails generating.

## How to run
Install Redis and RabbitMQ. Get Python3 and check config.cfg (fill your values).

Installing packages:
```
pipenv install 
```
Running  uwsgi on dev:
```
uwsgi dev.ini
```

To compile sass install Ruby and Sass. 
I used Node package Purifycss to remove unneeded css. 