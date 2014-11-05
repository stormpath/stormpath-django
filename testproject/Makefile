SETTINGS=--settings=testproject.settings
MANAGE=coverage run --source=stormpath_django manage.py

test:
	$(MANAGE) test $(SETTINGS) testapp && coverage html
