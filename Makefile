
setupenv:
	@python tools/setupenv.py

docker-run:
	@docker-compose up 

# Python Code Style
reformat:
	python -m black `git ls-files "*.py"`
# stylecheck:
# 	$(PYTHON) -m black --check `git ls-files "*.py"`
# stylediff:
# 	$(PYTHON) -m black --check --diff `git ls-files "*.py"`

# Translations
# gettext:
# 	$(PYTHON) -m redgettext --command-docstrings --verbose --recursive redbot --exclude-files "redbot/pytest/**/*"
# upload_translations:
# 	crowdin upload sources
# download_translations:
# 	crowdin download

# Dependencies
# bumpdeps:
# 	$(PYTHON) tools/bumpdeps.py

# Development environment
# newenv:
# 	$(PYTHON) -m venv --clear .venv
# 	.venv/bin/pip install -U pip setuptools
# 	$(MAKE) syncenv
# syncenv:
# 	.venv/bin/pip install -Ur ./tools/dev-requirements.txt

# Changelog check
# checkchangelog:
# 	bash tools/check_changelog_entries.sh
# 	$(PYTHON) -m towncrier --draft

# // install command
# 	// install dev requirements.txt
# 	// install precommits