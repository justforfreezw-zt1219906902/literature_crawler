#!/bin/bash

set -e

echo "Running migrations"
flask db upgrade

echo "Running app"
python app.py


