# Exporters

> Process and export your telemetry data

---

LLMS index: [llms.txt](/llms.txt)

---

Send telemetry to the [OpenTelemetry Collector](/docs/collector/) to make sure
it's exported correctly. Using the Collector in production environments is a
best practice. To visualize your telemetry, export it to a backend such as
[Jaeger](https://jaegertracing.io/), [Zipkin](https://zipkin.io/),
[Prometheus](https://prometheus.io/), or a
[vendor-specific](/ecosystem/vendors/) backend.



## Available exporters

The registry contains a [list of exporters for Python][reg].





Among exporters, [OpenTelemetry Protocol (OTLP)][OTLP] exporters are designed
with the OpenTelemetry data model in mind, emitting OTel data without any loss
of information. Furthermore, many tools that operate on telemetry data support
OTLP (such as [Prometheus][], [Jaeger][], and most [vendors][]), providing you
with a high degree of flexibility when you need it. To learn more about OTLP,
see [OTLP Specification][OTLP].

[Jaeger]: /blog/2022/jaeger-native-otlp/
[OTLP]: /docs/specs/otlp/
[Prometheus]:
  https://prometheus.io/docs/prometheus/2.55/feature_flags/#otlp-receiver
[reg]: </ecosystem/registry/?component=exporter&language=python>
[vendors]: /ecosystem/vendors/



This page covers the main OpenTelemetry Python exporters and how to set
them up.





> [!NOTE]
>
> If you use [zero-code instrumentation](</docs/zero-code/python>),
> you can learn how to set up exporters by following the
> [Configuration Guide](</docs/zero-code/python/configuration/>).





## OTLP

### Collector Setup

> [!NOTE]
>
> If you have a OTLP collector or backend already set up, you can skip this
> section and [setup the OTLP exporter dependencies](#otlp-dependencies) for
> your application.

To try out and verify your OTLP exporters, you can run the collector in a docker
container that writes telemetry directly to the console.

In an empty directory, create a file called `collector-config.yaml` with the
following content:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
exporters:
  debug:
    verbosity: detailed
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
    metrics:
      receivers: [otlp]
      exporters: [debug]
    logs:
      receivers: [otlp]
      exporters: [debug]
```

Now run the collector in a docker container:

```shell
docker run -p 4317:4317 -p 4318:4318 --rm -v $(pwd)/collector-config.yaml:/etc/otelcol/config.yaml otel/opentelemetry-collector
```

This collector is now able to accept telemetry via OTLP. Later you may want to
[configure the collector](/docs/collector/configuration) to send your telemetry
to your observability backend.




## Dependencies {#otlp-dependencies}

If you want to send telemetry data to an OTLP endpoint (like the
[OpenTelemetry Collector](#collector-setup), [Jaeger](#jaeger) or
[Prometheus](#prometheus)), you can choose between two different protocols to
transport your data:

- [HTTP/protobuf](https://pypi.org/project/opentelemetry-exporter-otlp-proto-http/)
- [gRPC](https://pypi.org/project/opentelemetry-exporter-otlp-proto-grpc/)

Start by installing the respective exporter packages as a dependency for your
project:

   <ul class="nav nav-tabs" id="tabs-1" role="tablist">
  <li class="nav-item">
      <button class="nav-link active"
          id="tabs-01-00-tab" data-bs-toggle="tab" data-bs-target="#tabs-01-00" role="tab"
          data-td-tp-persist="http/proto" aria-controls="tabs-01-00" aria-selected="true">
        HTTP/Proto
      </button>
    </li><li class="nav-item">
      <button class="nav-link"
          id="tabs-01-01-tab" data-bs-toggle="tab" data-bs-target="#tabs-01-01" role="tab"
          data-td-tp-persist="grpc" aria-controls="tabs-01-01" aria-selected="false">
        gRPC
      </button>
    </li>
</ul>

<div class="tab-content" id="tabs-1-content">
    <div class="tab-body tab-pane fade show active"
        id="tabs-01-00" role="tabpanel" aria-labelled-by="tabs-01-00-tab" tabindex="1">
        <div class="highlight"><pre tabindex="0" class="chroma"><code class="language-shell" data-lang="shell"><span class="line"><span class="cl">pip install opentelemetry-exporter-otlp-proto-http
</span></span></code></pre></div>
    </div>
    <div class="tab-body tab-pane fade"
        id="tabs-01-01" role="tabpanel" aria-labelled-by="tabs-01-01-tab" tabindex="1">
        <div class="highlight"><pre tabindex="0" class="chroma"><code class="language-shell" data-lang="shell"><span class="line"><span class="cl">pip install opentelemetry-exporter-otlp-proto-grpc
</span></span></code></pre></div>
    </div>
</div>


## Usage

Next, configure the exporter to point at an OTLP endpoint in your code.

   <ul class="nav nav-tabs" id="tabs-2" role="tablist">
  <li class="nav-item">
      <button class="nav-link active"
          id="tabs-02-00-tab" data-bs-toggle="tab" data-bs-target="#tabs-02-00" role="tab"
          data-td-tp-persist="http/proto" aria-controls="tabs-02-00" aria-selected="true">
        HTTP/Proto
      </button>
    </li><li class="nav-item">
      <button class="nav-link"
          id="tabs-02-01-tab" data-bs-toggle="tab" data-bs-target="#tabs-02-01" role="tab"
          data-td-tp-persist="grpc" aria-controls="tabs-02-01" aria-selected="false">
        gRPC
      </button>
    </li>
</ul>

<div class="tab-content" id="tabs-2-content">
    <div class="tab-body tab-pane fade show active"
        id="tabs-02-00" role="tabpanel" aria-labelled-by="tabs-02-00-tab" tabindex="2">
        <div class="highlight"><pre tabindex="0" class="chroma"><code class="language-python" data-lang="python"><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.resources</span> <span class="kn">import</span> <span class="n">SERVICE_NAME</span><span class="p">,</span> <span class="n">Resource</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry</span> <span class="kn">import</span> <span class="n">trace</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.exporter.otlp.proto.http.trace_exporter</span> <span class="kn">import</span> <span class="n">OTLPSpanExporter</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.trace</span> <span class="kn">import</span> <span class="n">TracerProvider</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.trace.export</span> <span class="kn">import</span> <span class="n">BatchSpanProcessor</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry</span> <span class="kn">import</span> <span class="n">metrics</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.exporter.otlp.proto.http.metric_exporter</span> <span class="kn">import</span> <span class="n">OTLPMetricExporter</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.metrics</span> <span class="kn">import</span> <span class="n">MeterProvider</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.metrics.export</span> <span class="kn">import</span> <span class="n">PeriodicExportingMetricReader</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="c1"># Service name is required for most backends</span>
</span></span><span class="line"><span class="cl"><span class="n">resource</span> <span class="o">=</span> <span class="n">Resource</span><span class="o">.</span><span class="n">create</span><span class="p">(</span><span class="n">attributes</span><span class="o">=</span><span class="p">{</span>
</span></span><span class="line"><span class="cl">    <span class="n">SERVICE_NAME</span><span class="p">:</span> <span class="s2">&#34;your-service-name&#34;</span>
</span></span><span class="line"><span class="cl"><span class="p">})</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">tracerProvider</span> <span class="o">=</span> <span class="n">TracerProvider</span><span class="p">(</span><span class="n">resource</span><span class="o">=</span><span class="n">resource</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">processor</span> <span class="o">=</span> <span class="n">BatchSpanProcessor</span><span class="p">(</span><span class="n">OTLPSpanExporter</span><span class="p">(</span><span class="n">endpoint</span><span class="o">=</span><span class="s2">&#34;&lt;traces-endpoint&gt;/v1/traces&#34;</span><span class="p">))</span>
</span></span><span class="line"><span class="cl"><span class="n">tracerProvider</span><span class="o">.</span><span class="n">add_span_processor</span><span class="p">(</span><span class="n">processor</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">trace</span><span class="o">.</span><span class="n">set_tracer_provider</span><span class="p">(</span><span class="n">tracerProvider</span><span class="p">)</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">reader</span> <span class="o">=</span> <span class="n">PeriodicExportingMetricReader</span><span class="p">(</span>
</span></span><span class="line"><span class="cl">    <span class="n">OTLPMetricExporter</span><span class="p">(</span><span class="n">endpoint</span><span class="o">=</span><span class="s2">&#34;&lt;traces-endpoint&gt;/v1/metrics&#34;</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">meterProvider</span> <span class="o">=</span> <span class="n">MeterProvider</span><span class="p">(</span><span class="n">resource</span><span class="o">=</span><span class="n">resource</span><span class="p">,</span> <span class="n">metric_readers</span><span class="o">=</span><span class="p">[</span><span class="n">reader</span><span class="p">])</span>
</span></span><span class="line"><span class="cl"><span class="n">metrics</span><span class="o">.</span><span class="n">set_meter_provider</span><span class="p">(</span><span class="n">meterProvider</span><span class="p">)</span>
</span></span></code></pre></div>
    </div>
    <div class="tab-body tab-pane fade"
        id="tabs-02-01" role="tabpanel" aria-labelled-by="tabs-02-01-tab" tabindex="2">
        <div class="highlight"><pre tabindex="0" class="chroma"><code class="language-python" data-lang="python"><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.resources</span> <span class="kn">import</span> <span class="n">SERVICE_NAME</span><span class="p">,</span> <span class="n">Resource</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry</span> <span class="kn">import</span> <span class="n">trace</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.exporter.otlp.proto.grpc.trace_exporter</span> <span class="kn">import</span> <span class="n">OTLPSpanExporter</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.trace</span> <span class="kn">import</span> <span class="n">TracerProvider</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.trace.export</span> <span class="kn">import</span> <span class="n">BatchSpanProcessor</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry</span> <span class="kn">import</span> <span class="n">metrics</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.exporter.otlp.proto.grpc.metric_exporter</span> <span class="kn">import</span> <span class="n">OTLPMetricExporter</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.metrics</span> <span class="kn">import</span> <span class="n">MeterProvider</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.metrics.export</span> <span class="kn">import</span> <span class="n">PeriodicExportingMetricReader</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="c1"># Service name is required for most backends</span>
</span></span><span class="line"><span class="cl"><span class="n">resource</span> <span class="o">=</span> <span class="n">Resource</span><span class="o">.</span><span class="n">create</span><span class="p">(</span><span class="n">attributes</span><span class="o">=</span><span class="p">{</span>
</span></span><span class="line"><span class="cl">    <span class="n">SERVICE_NAME</span><span class="p">:</span> <span class="s2">&#34;your-service-name&#34;</span>
</span></span><span class="line"><span class="cl"><span class="p">})</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">tracerProvider</span> <span class="o">=</span> <span class="n">TracerProvider</span><span class="p">(</span><span class="n">resource</span><span class="o">=</span><span class="n">resource</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">processor</span> <span class="o">=</span> <span class="n">BatchSpanProcessor</span><span class="p">(</span><span class="n">OTLPSpanExporter</span><span class="p">(</span><span class="n">endpoint</span><span class="o">=</span><span class="s2">&#34;your-endpoint-here&#34;</span><span class="p">))</span>
</span></span><span class="line"><span class="cl"><span class="n">tracerProvider</span><span class="o">.</span><span class="n">add_span_processor</span><span class="p">(</span><span class="n">processor</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">trace</span><span class="o">.</span><span class="n">set_tracer_provider</span><span class="p">(</span><span class="n">tracerProvider</span><span class="p">)</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">reader</span> <span class="o">=</span> <span class="n">PeriodicExportingMetricReader</span><span class="p">(</span>
</span></span><span class="line"><span class="cl">    <span class="n">OTLPMetricExporter</span><span class="p">(</span><span class="n">endpoint</span><span class="o">=</span><span class="s2">&#34;localhost:5555&#34;</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">meterProvider</span> <span class="o">=</span> <span class="n">MeterProvider</span><span class="p">(</span><span class="n">resource</span><span class="o">=</span><span class="n">resource</span><span class="p">,</span> <span class="n">metric_readers</span><span class="o">=</span><span class="p">[</span><span class="n">reader</span><span class="p">])</span>
</span></span><span class="line"><span class="cl"><span class="n">metrics</span><span class="o">.</span><span class="n">set_meter_provider</span><span class="p">(</span><span class="n">meterProvider</span><span class="p">)</span>
</span></span></code></pre></div>
    </div>
</div>


## Console

To debug your instrumentation or see the values locally in development, you can
use exporters writing telemetry data to the console (stdout).

The `ConsoleSpanExporter` and `ConsoleMetricExporter` are included in the
`opentelemetry-sdk` package.

```python
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter

# Service name is required for most backends,
# and although it's not necessary for console export,
# it's good to set service name anyways.
resource = Resource.create(attributes={
    SERVICE_NAME: "your-service-name"
})

tracerProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(ConsoleSpanExporter())
tracerProvider.add_span_processor(processor)
trace.set_tracer_provider(tracerProvider)

reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meterProvider)
```

> [!NOTE]
>
> There are temporality presets for each instrumentation kind. These presets can
> be set with the environment variable
> `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE`, for example:
>
> ```sh
> export OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE="DELTA"
> ```
>
> The default value for `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE` is
> `"CUMULATIVE"`.
>
> The available values and their corresponding settings for this environment
> variable are:
>
> - `CUMULATIVE`
>   - `Counter`: `CUMULATIVE`
>   - `UpDownCounter`: `CUMULATIVE`
>   - `Histogram`: `CUMULATIVE`
>   - `ObservableCounter`: `CUMULATIVE`
>   - `ObservableUpDownCounter`: `CUMULATIVE`
>   - `ObservableGauge`: `CUMULATIVE`
> - `DELTA`
>   - `Counter`: `DELTA`
>   - `UpDownCounter`: `CUMULATIVE`
>   - `Histogram`: `DELTA`
>   - `ObservableCounter`: `DELTA`
>   - `ObservableUpDownCounter`: `CUMULATIVE`
>   - `ObservableGauge`: `CUMULATIVE`
> - `LOWMEMORY`
>   - `Counter`: `DELTA`
>   - `UpDownCounter`: `CUMULATIVE`
>   - `Histogram`: `DELTA`
>   - `ObservableCounter`: `CUMULATIVE`
>   - `ObservableUpDownCounter`: `CUMULATIVE`
>   - `ObservableGauge`: `CUMULATIVE`
>
> Setting `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE` to any other value
> than `CUMULATIVE`, `DELTA` or `LOWMEMORY` will log a warning and set this
> environment variable to `CUMULATIVE`.

## Jaeger

### Backend Setup {#jaeger-backend-setup}

[Jaeger](https://www.jaegertracing.io/) natively supports OTLP to receive trace
data. You can run Jaeger in a docker container with the UI accessible on port
16686 and OTLP enabled on ports 4317 and 4318:

```shell
docker run --rm \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

### Usage {#jaeger-usage}

Now following the instruction to setup the [OTLP exporters](#otlp-dependencies).


## Prometheus

To send your metric data to [Prometheus](https://prometheus.io/), you can
either:

- [Enable Prometheus' OTLP Receiver](https://prometheus.io/docs/guides/opentelemetry/#enable-the-otlp-receiver)
  and use the [OTLP exporter](#otlp) (best practice), or
- Use the Prometheus exporter, a `MetricReader` that starts an HTTP server that
  collects metrics and serializes to Prometheus text format on request.

### Backend setup {#prometheus-setup}

To run a Prometheus server backend and begin scraping metrics, see the
[Prometheus getting started guide](https://prometheus.io/docs/prometheus/latest/getting_started/).

To enable the OTLP Receiver, see the
[Prometheus guide for enabling the OTLP Receiver](https://prometheus.io/docs/guides/opentelemetry/#enable-the-otlp-receiver).


## Dependencies {#prometheus-dependencies}

Install the
[exporter package](https://pypi.org/project/opentelemetry-exporter-prometheus/)
as a dependency for your application:

```sh
pip install opentelemetry-exporter-prometheus
```

Update your OpenTelemetry configuration to use the exporter and to send data to
your Prometheus backend:

```python
from prometheus_client import start_http_server

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Service name is required for most backends
resource = Resource.create(attributes={
    SERVICE_NAME: "your-service-name"
})

# Start Prometheus client
start_http_server(port=9464, addr="localhost")
# Initialize PrometheusMetricReader which pulls metrics from the SDK
# on-demand to respond to scrape requests
reader = PrometheusMetricReader()
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)
```

With the above you can access your metrics at <http://localhost:9464/metrics>.
Prometheus or an OpenTelemetry Collector with the Prometheus receiver can scrape
the metrics from this endpoint.

## Zipkin

### Backend Setup {#zipkin-setup}

> [!NOTE]
>
> If you have Zipkin or a Zipkin-compatible backend already set up, you can skip
> this section and setup the
> [Zipkin exporter dependencies](#zipkin-dependencies) for your application.

You can run [Zipkin](https://zipkin.io/) on in a Docker container by executing
the following command:

```shell
docker run --rm -d -p 9411:9411 --name zipkin openzipkin/zipkin
```


## Dependencies {#zipkin-dependencies}

To send your trace data to [Zipkin](https://zipkin.io/), you can choose between
two different protocols to transport your data:

- [HTTP/protobuf](https://pypi.org/project/opentelemetry-exporter-zipkin-proto-http/)
- [Thrift](https://pypi.org/project/opentelemetry-exporter-zipkin-json/)

Install the exporter package as a dependency for your application:

   <ul class="nav nav-tabs" id="tabs-6" role="tablist">
  <li class="nav-item">
      <button class="nav-link active"
          id="tabs-06-00-tab" data-bs-toggle="tab" data-bs-target="#tabs-06-00" role="tab"
          data-td-tp-persist="http/proto" aria-controls="tabs-06-00" aria-selected="true">
        HTTP/Proto
      </button>
    </li><li class="nav-item">
      <button class="nav-link"
          id="tabs-06-01-tab" data-bs-toggle="tab" data-bs-target="#tabs-06-01" role="tab"
          data-td-tp-persist="thrift" aria-controls="tabs-06-01" aria-selected="false">
        Thrift
      </button>
    </li>
</ul>

<div class="tab-content" id="tabs-6-content">
    <div class="tab-body tab-pane fade show active"
        id="tabs-06-00" role="tabpanel" aria-labelled-by="tabs-06-00-tab" tabindex="6">
        <div class="highlight"><pre tabindex="0" class="chroma"><code class="language-shell" data-lang="shell"><span class="line"><span class="cl">pip install opentelemetry-exporter-zipkin-proto-http
</span></span></code></pre></div>
    </div>
    <div class="tab-body tab-pane fade"
        id="tabs-06-01" role="tabpanel" aria-labelled-by="tabs-06-01-tab" tabindex="6">
        <div class="highlight"><pre tabindex="0" class="chroma"><code class="language-shell" data-lang="shell"><span class="line"><span class="cl">pip install opentelemetry-exporter-zipkin-json
</span></span></code></pre></div>
    </div>
</div>


Update your OpenTelemetry configuration to use the exporter and to send data to
your Zipkin backend:

   <ul class="nav nav-tabs" id="tabs-7" role="tablist">
  <li class="nav-item">
      <button class="nav-link active"
          id="tabs-07-00-tab" data-bs-toggle="tab" data-bs-target="#tabs-07-00" role="tab"
          data-td-tp-persist="http/proto" aria-controls="tabs-07-00" aria-selected="true">
        HTTP/Proto
      </button>
    </li><li class="nav-item">
      <button class="nav-link"
          id="tabs-07-01-tab" data-bs-toggle="tab" data-bs-target="#tabs-07-01" role="tab"
          data-td-tp-persist="thrift" aria-controls="tabs-07-01" aria-selected="false">
        Thrift
      </button>
    </li>
</ul>

<div class="tab-content" id="tabs-7-content">
    <div class="tab-body tab-pane fade show active"
        id="tabs-07-00" role="tabpanel" aria-labelled-by="tabs-07-00-tab" tabindex="7">
        <div class="highlight"><pre tabindex="0" class="chroma"><code class="language-python" data-lang="python"><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry</span> <span class="kn">import</span> <span class="n">trace</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.exporter.zipkin.proto.http</span> <span class="kn">import</span> <span class="n">ZipkinExporter</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.trace</span> <span class="kn">import</span> <span class="n">TracerProvider</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.trace.export</span> <span class="kn">import</span> <span class="n">BatchSpanProcessor</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.resources</span> <span class="kn">import</span> <span class="n">SERVICE_NAME</span><span class="p">,</span> <span class="n">Resource</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">resource</span> <span class="o">=</span> <span class="n">Resource</span><span class="o">.</span><span class="n">create</span><span class="p">(</span><span class="n">attributes</span><span class="o">=</span><span class="p">{</span>
</span></span><span class="line"><span class="cl">    <span class="n">SERVICE_NAME</span><span class="p">:</span> <span class="s2">&#34;your-service-name&#34;</span>
</span></span><span class="line"><span class="cl"><span class="p">})</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">zipkin_exporter</span> <span class="o">=</span> <span class="n">ZipkinExporter</span><span class="p">(</span><span class="n">endpoint</span><span class="o">=</span><span class="s2">&#34;http://localhost:9411/api/v2/spans&#34;</span><span class="p">)</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">provider</span> <span class="o">=</span> <span class="n">TracerProvider</span><span class="p">(</span><span class="n">resource</span><span class="o">=</span><span class="n">resource</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">processor</span> <span class="o">=</span> <span class="n">BatchSpanProcessor</span><span class="p">(</span><span class="n">zipkin_exporter</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">provider</span><span class="o">.</span><span class="n">add_span_processor</span><span class="p">(</span><span class="n">processor</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">trace</span><span class="o">.</span><span class="n">set_tracer_provider</span><span class="p">(</span><span class="n">provider</span><span class="p">)</span>
</span></span></code></pre></div>
    </div>
    <div class="tab-body tab-pane fade"
        id="tabs-07-01" role="tabpanel" aria-labelled-by="tabs-07-01-tab" tabindex="7">
        <div class="highlight"><pre tabindex="0" class="chroma"><code class="language-python" data-lang="python"><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry</span> <span class="kn">import</span> <span class="n">trace</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.exporter.zipkin.json</span> <span class="kn">import</span> <span class="n">ZipkinExporter</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.trace</span> <span class="kn">import</span> <span class="n">TracerProvider</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.trace.export</span> <span class="kn">import</span> <span class="n">BatchSpanProcessor</span>
</span></span><span class="line"><span class="cl"><span class="kn">from</span> <span class="nn">opentelemetry.sdk.resources</span> <span class="kn">import</span> <span class="n">SERVICE_NAME</span><span class="p">,</span> <span class="n">Resource</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">resource</span> <span class="o">=</span> <span class="n">Resource</span><span class="o">.</span><span class="n">create</span><span class="p">(</span><span class="n">attributes</span><span class="o">=</span><span class="p">{</span>
</span></span><span class="line"><span class="cl">    <span class="n">SERVICE_NAME</span><span class="p">:</span> <span class="s2">&#34;your-service-name&#34;</span>
</span></span><span class="line"><span class="cl"><span class="p">})</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">zipkin_exporter</span> <span class="o">=</span> <span class="n">ZipkinExporter</span><span class="p">(</span><span class="n">endpoint</span><span class="o">=</span><span class="s2">&#34;http://localhost:9411/api/v2/spans&#34;</span><span class="p">)</span>
</span></span><span class="line"><span class="cl">
</span></span><span class="line"><span class="cl"><span class="n">provider</span> <span class="o">=</span> <span class="n">TracerProvider</span><span class="p">(</span><span class="n">resource</span><span class="o">=</span><span class="n">resource</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">processor</span> <span class="o">=</span> <span class="n">BatchSpanProcessor</span><span class="p">(</span><span class="n">zipkin_exporter</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">provider</span><span class="o">.</span><span class="n">add_span_processor</span><span class="p">(</span><span class="n">processor</span><span class="p">)</span>
</span></span><span class="line"><span class="cl"><span class="n">trace</span><span class="o">.</span><span class="n">set_tracer_provider</span><span class="p">(</span><span class="n">provider</span><span class="p">)</span>
</span></span></code></pre></div>
    </div>
</div>


## Custom exporters

Finally, you can also write your own exporter. For more information, see the
[SpanExporter Interface in the API documentation](https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.export.html#opentelemetry.sdk.trace.export.SpanExporter).

## Batching span and log records

The OpenTelemetry SDK provides a set of default span and log record processors,
that allow you to either emit spans one-by-on ("simple") or batched. Using
batching is recommended, but if you do not want to batch your spans or log
records, you can use a simple processor instead as follows:


```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

processor = SimpleSpanProcessor(OTLPSpanExporter(endpoint="your-endpoint-here"))
```
