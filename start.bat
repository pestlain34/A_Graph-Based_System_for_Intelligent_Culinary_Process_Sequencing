@echo off
echo Starting Flask server via pipenv...
pipenv run python -m flask --app myproject:app run --debug
pause