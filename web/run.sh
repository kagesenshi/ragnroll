#!/bin/bash

cd ragnroll_web
echo "WebUI will be running at http://localhost:3000"
echo "Websocket will be running at http://localhost:8000"
poetry run reflex run
