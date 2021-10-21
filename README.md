# py-kitchen
Python backend for RITA project

## Run locally
Currently, it connects to the actual Firestore.
So for this to work service account json should exist locally.

`docker-compose up --build`

## Dev env
For development and running tests install packages from `dev-requirements.txt`

## Run all tests
`python -m pytest`

## Change version
`bump2version fix`