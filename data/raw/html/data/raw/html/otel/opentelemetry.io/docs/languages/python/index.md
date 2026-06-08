# Python

> <img width="35" class="img-initial otel-icon" src="/img/logos/32x32/Python_SDK.svg" alt="Python"> A language-specific implementation of OpenTelemetry in Python.

---

LLMS index: [llms.txt](/llms.txt)

---


Welcome to the OpenTelemetry Python documentation. This section introduces
how to use OpenTelemetry with Python to generate and collect telemetry data
such as metrics, logs, and traces using the OpenTelemetry API and SDKs.

These pages are intended to help you get started and understand the current
capabilities and status of OpenTelemetry Python.

## Status and Releases

The current status of the major functional components for OpenTelemetry
Python is as follows:

| Traces              | Metrics              | Logs              |
| ------------------- | -------------------- | ----------------- |
| [Stable](/docs/specs/otel/versioning-and-stability/#stable) | [Stable](/docs/specs/otel/versioning-and-stability/#stable) | [Development](/docs/specs/otel/versioning-and-stability/#development) |

For releases, including the [latest release][], see [Releases][]. 

[latest release]:
  <https://github.com/open-telemetry/opentelemetry-python/releases/latest>
[Releases]:
  <https://github.com/open-telemetry/opentelemetry-python/releases>


## Version support

OpenTelemetry-Python supports Python 3.9 and higher.

## Installation

The API and SDK packages are available on PyPI, and can be installed via pip:

```sh
pip install opentelemetry-api
pip install opentelemetry-sdk
```

In addition, there are several extension packages which can be installed
separately as:

```sh
pip install opentelemetry-exporter-{exporter}
pip install opentelemetry-instrumentation-{instrumentation}
```

These are for exporter and instrumentation libraries respectively. The Jaeger,
Zipkin, Prometheus, OTLP and OpenCensus Exporters can be found in the
[exporter](https://github.com/open-telemetry/opentelemetry-python/blob/main/exporter/)
directory of the repository. Instrumentations and additional exporters can be
found in the contrib repository
[instrumentation](https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation)
and
[exporter](https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/exporter)
directories.

## Extensions

To find related projects like exporters, instrumentation libraries, tracer
implementations, etc., visit the [Registry](/ecosystem/registry/?s=python).

### Installing Cutting-edge Packages

There is some functionality that has not yet been released to PyPI. In that
situation, you may want to install the packages directly from the repository.
This can be done by cloning the repository and doing an
[editable install](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs):

```sh
git clone https://github.com/open-telemetry/opentelemetry-python.git
cd opentelemetry-python
pip install -e ./opentelemetry-api -e ./opentelemetry-sdk -e ./opentelemetry-semantic-conventions
```

## Repositories and benchmarks

- Main repository: [opentelemetry-python][]
- Contrib repository: [opentelemetry-python-contrib][]

[opentelemetry-python]: https://github.com/open-telemetry/opentelemetry-python
[opentelemetry-python-contrib]:
  https://github.com/open-telemetry/opentelemetry-python-contrib

---

Section pages:

- [Getting Started by Example](/docs/languages/python/getting-started/): Get telemetry for your app in less than 5 minutes!
- [Instrumentation](/docs/languages/python/instrumentation/): Manual instrumentation for OpenTelemetry Python
- [Using instrumentation libraries](/docs/languages/python/libraries/)
- [Exporters](/docs/languages/python/exporters/): Process and export your telemetry data
- [Propagation](/docs/languages/python/propagation/): Context propagation for the Python SDK
- [Cookbook](/docs/languages/python/cookbook/)
- [OpenTelemetry Distro](/docs/languages/python/distro/)
- [Using mypy](/docs/languages/python/mypy/)
- [Benchmarks](/docs/languages/python/benchmarks/)
- [API reference](/docs/languages/python/api/)
- [Examples](/docs/languages/python/examples/)
- [Registry](/docs/languages/python/registry/): Instrumentation libraries, exporters and other useful components for OpenTelemetry Python
