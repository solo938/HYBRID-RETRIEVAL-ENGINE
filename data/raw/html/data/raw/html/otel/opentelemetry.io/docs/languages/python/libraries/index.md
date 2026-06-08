# Using instrumentation libraries

LLMS index: [llms.txt](/llms.txt)

---

When you develop an app, you might use third-party libraries and frameworks to
accelerate your work. If you then instrument your app using OpenTelemetry, you
might want to avoid spending additional time to manually add traces, logs, and
metrics to the third-party libraries and frameworks you use.

Many libraries and frameworks already support OpenTelemetry or are supported
through OpenTelemetry
[instrumentation](/docs/concepts/instrumentation/libraries/), so that they can
generate telemetry you can export to an observability backend.

If you are instrumenting an app or service that use third-party libraries or
frameworks, follow these instructions to learn how to use natively instrumented
libraries and instrumentation libraries for your dependencies.

## Use natively instrumented libraries

If a library comes with OpenTelemetry support by default, you can get traces,
metrics, and logs emitted from that library by adding and setting up the
OpenTelemetry SDK with your app.

The library might require some additional configuration for the instrumentation.
Go to the documentation for that library to learn more.


- [Elasticsearch Python Client](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/opentelemetry.html)






> [!IMPORTANT] Help wanted
>
> If you are aware of a Python library that has OpenTelemetry natively
> integrated, [let us know][new-issue].



[new-issue]:
  https://github.com/open-telemetry/opentelemetry.io/issues/new/choose



## Use instrumentation libraries

If a library does not ship with native OpenTelemetry support, you can use
[instrumentation libraries](/docs/specs/otel/glossary/#instrumentation-library)
to generate telemetry data for a library or framework.

For example,
[the instrumentation library for HTTPX](https://pypi.org/project/opentelemetry-instrumentation-httpx/)
automatically creates [spans](/docs/concepts/signals/traces/#spans) based on
HTTP requests.

## Setup

You can install each instrumentation library separately using pip. For example:

```sh
pip install opentelemetry-instrumentation-{instrumented-library}
```

In the previous example, `{instrumented-library}` is the name of the
instrumentation.

To install a development version, clone or fork the
`opentelemetry-python-contrib` repository and run the following command to do an
editable installation:

```sh
pip install -e ./instrumentation/opentelemetry-instrumentation-{integration}
```

After installation, you will need to initialize the instrumentation library.
Each library typically has its own way to initialize.

## Example with HTTPX instrumentation

Here's how you can instrument HTTP requests made using the `httpx` library.

First, install the instrumentation library using pip:

```sh
pip install opentelemetry-instrumentation-httpx
```

Next, use the instrumentor to automatically trace requests from all clients:

```python
import httpx
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

url = "https://some.url/get"
HTTPXClientInstrumentor().instrument()

with httpx.Client() as client:
     response = client.get(url)

async with httpx.AsyncClient() as client:
     response = await client.get(url)
```

### Turn off instrumentations

If needed, you can uninstrument specific clients or all clients using the
`uninstrument_client` method. For example:

```python
import httpx
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

HTTPXClientInstrumentor().instrument()
client = httpx.Client()

# Uninstrument a specific client
HTTPXClientInstrumentor.uninstrument_client(client)

# Uninstrument all clients
HTTPXClientInstrumentor().uninstrument()
```

## Available instrumentation libraries

A full list of instrumentation libraries produced by OpenTelemetry is available
from the [opentelemetry-python-contrib][] repository.

You can also find more instrumentations available in the
[registry](/ecosystem/registry/?language=python&component=instrumentation).

## Next steps

After you have set up instrumentation libraries, you might want to add your own
[instrumentation](/docs/languages/python/instrumentation) to your code, to
collect custom telemetry data.

You might also want to configure an appropriate exporter to
[export your telemetry data](/docs/languages/python/exporters) to one or more
telemetry backends.

You can also check the
[Zero-code instrumentation for Python](/docs/zero-code/python/).

[opentelemetry-python-contrib]:
  https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation#readme
