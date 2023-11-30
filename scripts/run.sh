#!/bin/sh

# Run the application
export LITESTAR_APP=server.web:app
litestar run --reload
