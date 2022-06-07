# solarview s0 to mqtt agent

Python script which polls a solarview s0-fb instance, converts the response to extensive JSON and publishes it to an mqtt broker.

Mostly based on the offical maxcom protocol description from Solarmax which s0-fb also uses

## Features:
- Valid JSON with parameter description, converted and original Values.
- Automatic checksum and length calculation 
- Compatible with Python 3+
- Parameters are set with environment variables
- Exception Handling without exiting
- Docker Image available

## dependencies

paho-mqtt  (https://pypi.org/project/paho-mqtt/)
