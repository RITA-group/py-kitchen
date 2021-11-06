# py-kitchen
Python backend for RITA project

## Run locally
Currently, dev server connects to the actual Firestore.
So for this to work service account json should exist locally. In order to do that add `secrets` folder and add
`service-account-key.json` which you obtained from you Firebase account. After that just run:

`docker-compose up --build`

## Dev env
For development and running tests install packages from `dev-requirements.txt`

## Run all tests
Running tests doesn't require Firestore connection. After installing `dev-requirements.txt` just run:

`python -m pytest`
