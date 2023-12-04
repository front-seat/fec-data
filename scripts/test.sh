#!/bin/sh

pre-commit run --all-files
npm run test-ci
python -m unittest discover -s server
