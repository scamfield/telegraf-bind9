# Telegraf Execution Script for Bind 9
A telegraf executable script to collect metrics from BIND9 server

## Requirements
Software needed to use this:
* Bind 9 - (https://www.isc.org/)
* Telegraf - (https://www.influxdata.com/time-series-platform/telegraf/)
* Python 3.x - (https://www.python.org/)

## Configuration
Have a Bind9 server running, with the statistics server enabled. Something like the following in your configuration:

```
statistics-channels {
	inet 127.0.0.1 port 8053 allow { 127.0.0.1; };
};
```

Sample telegraf configuration file, place in /etc/telegraf/telegraf.d/bind.conf

```
[[inputs.exec]]
  ## Commands array
  commands = [
    "/usr/local/bin/bind9_metrics.py",
  ]

  ## Timeout for each command to complete.
  timeout = "5s"

  ## measurement name suffix (for separating different commands)
  name_suffix = "_bind"

  ## Data format to consume.
  # NOTE json only reads numerical measurements, strings and booleans are ignored.
  data_format = "json"
```

## Note:

Bind can be configured to provide per-zone query statistics in your config: `zone-statistics yes;`, however this plugin currently doesn't process that data.

## Issues

Please address any issues or feedback via [issues](https://github.com/scamfield/telegraf-bind9/issues).

## License
See [LICENSE](https://github.com/scamfield/telegraf-bind9/blob/master/LICENSE) file.
