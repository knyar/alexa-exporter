# Prometheus exporter for Amazon Smart Air Quality Monitor

This exporter uses private Amazon Alexa API to collect air quality measurements
reported by Amazon Smart Air Quality Monitor

## Running

### Getting Appliance ID

Visit https://alexa.amazon.co.uk/api/phoenix/group and identify the appliance
ID of your air monitor. It probably begins with "AAA_SonarCloudService_".

### Getting the Amazon session cookies

Since there is no public API available for collecting this data, we use a set
of browser session cookies to authenticate with Alexa API. Please treat these
cookies as secrets, since they give access to your Amazon account.

Visit https://alexa.amazon.co.uk/api/phoenix/group with developer tools enabled
in your browser and record the value of the following cookies:

- at-acbuk
- ubid-acbuk

### Installing dependencies

```bash
pip install pipenv
pipenv install
```

### Running the exporter

```bash
AT_ACBUK='at-acbuk-cookie-value' UBID_ACBUK='ubid-acbuk-cookie-value' pipenv run python app.py
```

### Testing

Before configuring the exporter as a Prometheus target, verify that metrics get
collected successfully by sending a request with your monitor's appliance ID
as an `id` URL parameter:

```bash
curl '127.0.0.1:5000/air_monitor?id=AAA_SonarCloudService_...'
```

### Configuring Prometheus

After you get the exporter running, you can add it as a Prometheus target.
For example:

```yaml
- job_name: alexa_exporter
  metrics_path: /air_monitor
  static_configs:
  - targets:
    - living_room,AAA_SonarCloudService_...
  relabel_configs:
  - source_labels: [__address__]
    regex: (.*),.*
    target_label: instance
    replacement: ${1}
  - source_labels: [__address__]
    regex: .*,(.*)
    target_label: __param_id
    replacement: ${1}
  - source_labels: []
    regex: .*
    target_label: __address__
    replacement: 127.0.0.1:5000
```
