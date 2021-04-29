PACKAGE=xworkflows

SRC_DIR=src/$(PACKAGE)
TESTS_DIR=tests
DOC_DIR=docs

# Use current python binary instead of system default.
COVERAGE = python $(shell which coverage)
FLAKE8 = flake8

all: default


default:


clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -path '*/__pycache__/*' -delete
	find . -type d -empty -delete
	@rm -rf tmp_test/


setup-dev:
	pip install --upgrade pip setuptools
	pip install --upgrade -e .[dev,doc]
	pip freeze

release:
	fullrelease

.PHONY: all default clean setup-dev release

testall:
	tox


test:
	python -W default -m unittest discover --top-level-directory . --verbose $(TESTS_DIR)

.PHONY: test testall

lint: flake8 check_manifest

check_manifest:
	check-manifest

# Note: we run the linter in two runs, because our __init__.py files has specific warnings we want to exclude
flake8:
	$(FLAKE8) --exclude $(SRC_DIR)/__init__.py $(SRC_DIR)
	$(FLAKE8) --ignore F401 $(SRC_DIR)/__init__.py

.PHONY: lint check_manifest flake8

coverage:
	$(COVERAGE) erase
	$(COVERAGE) run "--include=$(SRC_DIR)/*.py,$(TESTS_DIR)/*.py" --branch setup.py test
	$(COVERAGE) report "--include=$(SRC_DIR)/*.py,$(TESTS_DIR)/*.py"
	$(COVERAGE) html "--include=$(SRC_DIR)/*.py,$(TESTS_DIR)/*.py"

coverage-xml-report: coverage
	$(COVERAGE) xml "--include=$(SRC_DIR)/*.py,$(TESTS_DIR)/*.py"

docs:
	$(MAKE) -C $(DOC_DIR) html


.PHONY: coverage docs
