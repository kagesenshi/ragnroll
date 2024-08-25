#!/bin/bash

cd ragnroll
poetry self add poetry-dotenv-plugin
poetry install
poetry run reflex init
