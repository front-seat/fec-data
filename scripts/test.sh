#!/bin/sh

pre-commit run --all
python -m unittest discover -s server
