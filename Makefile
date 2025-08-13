default:
	@echo 'Targets:'
	@echo '  run'
	@echo '  run-s'
	@echo '  help'
	@echo '  deploy'

run:
	uv run current-weather-nws2.py --latitude 39.747222 --longitude -84.536389

run-s:
	uv run current-weather-nws2.py --latitude 39.747222 --longitude -84.536389 --stationid KMGY

run-detail:
	uv run current-weather-nws2.py --latitude 39.747222 --longitude -84.536389 --stationid KMGY --detailcount 2

help:
	uv run current-weather-nws2.py --help

deploy:
	cp current-weather-nws2.py ~/bin/current-weather-nws2
