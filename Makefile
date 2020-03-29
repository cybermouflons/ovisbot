
setupenv:
	@python tools/setupenv.py

docker-run:
	@docker-compose up 

# Python Code Style
reformat:
	python -m black `git ls-files "*.py"`
