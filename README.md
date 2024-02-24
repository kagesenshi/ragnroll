# RAG'n'roll

Retrieval Augmented Generation API & Backoffice UI

## Features

Working:

- Ask question against your Neo4j graph using natural language & langchain

Working, but backend API only:
- If the langchain query generator could not give the right answer, teach the 
  engine how to query answers to a specific question by giving it the cypher
  query

TODO:
- Answer to questions with data visualization

## Installing

This whole repository is built with VSCode Devcontainer with docker-compose. Load
it up using VSCode and the build process should be automatic.

Tested on Fedora 39

## Starting up

`launch.json` have been configured with 2 tasks, one to run Web UI and another
to run the FastAPI Backend.

## Access points

- `http://localhost:3000` - Reflex Web UI
- `http://localhost:8000` - Reflex Websocket
- `http://localhost:5000/docs` - FastAPI Backend
- `http://localhost;7474` - Neo4j browser
