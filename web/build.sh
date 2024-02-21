#!/bin/bash

cd ragnroll_web
poetry self add poetry-dotenv-plugin
poetry install
poetry run reflex init
