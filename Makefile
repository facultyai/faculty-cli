.PHONY: release clean

release: lint
	# bdist_wheel requires 'wheel' package from PyPI
	python setup.py sdist bdist_wheel
	twine upload dist/*

clean:
	$(RM) -r build dist faculty_cli.egg-info

lint:
	python -m compileall faculty_cli
	flake8 faculty_cli
