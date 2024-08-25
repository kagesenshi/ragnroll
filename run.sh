#!/bin/bash

cd ragnroll
echo "WebUI will be running at http://localhost:3000"
echo "Websocket will be running at http://localhost:8000"
poetry run reflex run
