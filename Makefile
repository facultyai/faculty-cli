.PHONY: release clean

release: lint
	# bdist_wheel requires 'wheel' package from PyPI
	python setup.py sdist bdist_wheel
	twine upload dist/*

clean:
	$(RM) -r build dist sml.egg-info

lint:
	python -m compileall sml
	flake8 sml
	mypy sml || true
