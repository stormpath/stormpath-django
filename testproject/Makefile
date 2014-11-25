SETTINGS=--settings=testproject.settings
MANAGE=coverage run --source=django_stormpath manage.py

test:
	$(MANAGE) test $(SETTINGS) testapp && coverage html
