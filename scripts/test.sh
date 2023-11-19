#!/bin/sh

pre-commit run --all-files
python -m unittest discover -s server
