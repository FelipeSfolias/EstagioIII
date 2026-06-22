.PHONY: test coverage

test:
	python manage.py test apps.core.tests apps.accounts.tests --verbosity=2

coverage:
	coverage run --source=apps manage.py test apps.core.tests apps.accounts.tests
	coverage report -m
