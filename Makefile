pep8:
	flake8 courriers --ignore=E501,E127,E128,E124

test:
	coverage run --branch --source=courriers manage.py test courriers
	coverage report --omit=courriers/test* --omit=courriers/migrations/*

release:
	python setup.py sdist register upload -s
