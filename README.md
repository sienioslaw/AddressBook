# Q****a AdressBook Challenge

# Installing

`docker-compose up`

You may want to generate some user(s) and local data for API testings:

`docker-compose run web python manage.py createsuperuser`  
`docker-compose run web python manage.py generate_fake_addresses`

# Testing

`docker-compose run web python manage.py test`
