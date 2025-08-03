default:
	@echo 'Targets:'
	@echo '  run'
	@echo '  deploy'

run:
	uv run current-weather-nws2.py --latitude 39.747222 --longitude -84.536389

deploy:
	cp current-weather-nws2.py ~/bin/current-weather-nws2
