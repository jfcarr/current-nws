SCRIPT_BASE_NAME = current_weather_nws
SCRIPT_NAME = $(SCRIPT_BASE_NAME).py

default:
	@echo 'Targets:'
	@echo '  run            -- Just latitude and longitude'
	@echo '  run-s          -- Include station ID'
	@echo '  run-detail     -- Show details for first two forecast periods'
	@echo '  run-hourly     -- Show hourly forecast'
	@echo '  run-nplat      -- Conditions and forecast for North Platte'
	@echo '  run-alert      -- Show only one alert'
	@echo '  run-width      -- Override maximum text width'
	@echo '  run-stations   -- List station IDs'
	@echo '  run-stations-f -- List station IDs, filtered'
	@echo '  run-indent     -- Override wrapped text indent'
	@echo '  help'
	@echo '  deploy'

run:
	uv run $(SCRIPT_NAME) --latitude 39.747222 --longitude -84.536389

run-s:
	uv run $(SCRIPT_NAME) --latitude 39.747222 --longitude -84.536389 --stationid KDAY

run-detail:
	uv run $(SCRIPT_NAME) --latitude 39.747222 --longitude -84.536389 --stationid KMGY --detailcount 2

run-hourly:
	uv run $(SCRIPT_NAME) --latitude 39.747222 --longitude -84.536389 --stationid KDAY --hourlycount 12 --hourlyinterval 3 --hourlyshowday 

run-nplat:
	uv run $(SCRIPT_NAME) --latitude 41.131538 --longitude -100.821226 --detailcount 2

run-alert:
	uv run $(SCRIPT_NAME) --latitude 39.747222 --longitude -84.536389 --stationid KMGY --alertcount 1 --alertdetail --alertexpiration

run-width:
	uv run $(SCRIPT_NAME) --latitude 39.747222 --longitude -84.536389 --stationid KMGY --maxwidth 70

run-stations:
	uv run $(SCRIPT_NAME) --stations

run-stations-f:
	uv run $(SCRIPT_NAME) --stations --stationfilter dayton

run-indent:
	uv run $(SCRIPT_NAME) --latitude 39.747222 --longitude -84.536389 --stationid KMGY --indent 1

help:
	uv run $(SCRIPT_NAME) --help

deploy:
	cp $(SCRIPT_NAME) ~/bin/$(SCRIPT_BASE_NAME)
