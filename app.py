from flask import Flask, request, abort
from prometheus_client import start_http_server, Summary, CollectorRegistry, generate_latest
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import json
import os
import requests

app = Flask(__name__)

STATE_URL = 'https://alexa.amazon.co.uk/api/phoenix/state'

HEADERS = {
    # Pretend we are an Alexa iOS app.
    "User-Agent": "AppleWebKit PitanguiBridge/2.2.454039.0-[HARDWARE=iPhone8_1][SOFTWARE=14.4][DEVICE=iPhone]",
}

# Metric name prefix.
PREFIX = 'amazon_air_monitor'


def cookies():
    at_acbuk = os.getenv('AT_ACBUK')
    ubid_acbuk = os.getenv('UBID_ACBUK')
    if not at_acbuk or not ubid_acbuk:
        raise RuntimeError(
            "please set AT_ACBUK and UBID_ACBUK environment variables")
    return {'at-acbuk': at_acbuk, 'ubid-acbuk': ubid_acbuk}


def get_air_monitor_state(id):
    resp = requests.post(STATE_URL, headers=HEADERS, cookies=cookies(), json={
        "stateRequests": [{"entityId": id, "entityType": "APPLIANCE"}]
    })
    if resp.status_code != 200:
        raise RuntimeError("unexpected response from amazon, code %d: %s" % (
            resp.status_code, resp.text))
    j = resp.json()

    if 'errors' in j and j['errors']:
        raise RuntimeError("got an error from amazon: %s" % j['errors'])
    if 'error' in j['deviceStates'][0] and j['deviceStates'][0]['error']:
        raise RuntimeError("got error in deviceStates: %s" % resp.text)
    if 'capabilityStates' not in j['deviceStates'][0]:
        raise RuntimeError("expected capabilityStates, got %s" % resp.text)

    capabilities = {}
    for cap in j['deviceStates'][0]['capabilityStates']:
        capj = json.loads(cap)
        capabilities[capj['instance']] = capj['value']
    return capabilities


class AirMonitorCollector(object):
    def __init__(self, id):
        self.id = id

    def collect(self):
        caps = get_air_monitor_state(self.id)
        if '3' in caps:
            units = caps['3']['scale'].lower()
            m = GaugeMetricFamily(
                "%s_temperature_%s" % (PREFIX, units), "Temperature")
            m.add_metric([], caps['3']['value'])
            yield m
        if '4' in caps:
            m = GaugeMetricFamily("%s_humidity_percent" % PREFIX, "Humidity")
            m.add_metric([], caps['4'])
            yield m
        if '5' in caps:
            m = GaugeMetricFamily(
                "%s_voc_score" % PREFIX, "Volatile Organic Compound score")
            m.add_metric([], caps['5'])
            yield m
        if '6' in caps:
            m = GaugeMetricFamily(
                "%s_particulate_matter_ug_m3" % PREFIX,
                "Particulate Matter in micrograms per cubic meter")
            m.add_metric([], caps['6'])
            yield m
        if '8' in caps:
            m = GaugeMetricFamily(
                "%s_carbon_monoxide_ppm" % PREFIX,
                "Carbon Monoxide parts per million")
            m.add_metric([], caps['8'])
            yield m
        if '9' in caps:
            m = GaugeMetricFamily(
                "%s_quality_score" % PREFIX, "Air quality score")
            m.add_metric([], caps['9'])
            yield m


@app.route("/air_monitor")
def hello_world():
    if "id" not in request.args:
        return "Expected `id` parameter with device id", 400
    try:
        registry = CollectorRegistry()
        registry.register(AirMonitorCollector(request.args['id']))
        return generate_latest(registry)
    except RuntimeError as e:
        return str(e), 500


if __name__ == "__main__":
    # check that environment variables are set.
    cookies()
    app.run()
