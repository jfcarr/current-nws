default:
	@echo 'Targets:'
	@echo '  run			-- Just latitude and longitude'
	@echo '  run-s			-- Include station ID'
	@echo '  run-detail		-- Show details for first two forecast periods'
	@echo '  run-nplat		-- Conditions and forecast for North Platte'
	@echo '  run-alert      -- Show only one alert'
	@echo '  help'
	@echo '  deploy'

run:
	uv run current-weather-nws2.py --latitude 39.747222 --longitude -84.536389

run-s:
	uv run current-weather-nws2.py --latitude 39.747222 --longitude -84.536389 --stationid KMGY

run-detail:
	uv run current-weather-nws2.py --latitude 39.747222 --longitude -84.536389 --stationid KMGY --detailcount 2

run-nplat:
	uv run current-weather-nws2.py --latitude 41.131538 --longitude -100.821226 --detailcount 2

run-alert:
	uv run current-weather-nws2.py --latitude 39.747222 --longitude -84.536389 --stationid KMGY --alertcount 1

help:
	uv run current-weather-nws2.py --help

deploy:
	cp current-weather-nws2.py ~/bin/current-weather-nws2
