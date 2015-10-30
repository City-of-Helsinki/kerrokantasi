
# Requirements

 - Python 3.4
 - Django 1.8.5
 - django-modeltranslation (http://django-modeltranslation.readthedocs.org)
 - Django REST framework (http://www.django-rest-framework.org/)
 - munigeo (https://github.com/City-of-Helsinki/munigeo)
 - django-reversion (http://django-reversion.readthedocs.org)

# Install

## Prepare virtualenv

     virtualenv -p /usr/bin/python3 ~/.virtualenvs/
     workon kerrokantasi

## Install required packages

Install all required packages with pip command:

     pip install -r requirements.txt

# Testing

 - pytest
 - pytest-django
