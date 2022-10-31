
PYTHON := python3

.PHONY: all smarttune
all: smarttune

smarttune:
	$(PYTHON) setup.py bdist_wheel
	cp dist/*.whl ./