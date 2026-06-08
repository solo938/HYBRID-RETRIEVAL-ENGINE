# Optimize Throughput
# Optimize FastEmbed Throughput

By default, FastEmbed processes documents sequentially in the main processing thread. To optimize throughput, FastEmbed supports processing documents in parallel. 

When parallel processing is enabled, FastEmbed splits a dataset across multiple workers, each running an independent copy of the embedding model. Internally, documents are split into batches and put on a shared input queue. Each batch is then processed by one of the workers, put on a shared output queue, and then collected and reordered to match the original input order.

To configure FastEmbed for parallel processing, use the following parameters:

- `parallel`: the number of workers.
  - When set to `None` (default), the embedding model runs in the main process.
  - When set to `0`, FastEmbed detects the number of available CPU cores and parallelizes across that many workers.
  - When set to `1` or higher, FastEmbed uses the specified number of workers.
- Batch size: the number of documents that each worker processes in each batch. Adjusting this to balance memory usage and processing speed. Lower it if you're running out of memory during local inference. Raise it to improve throughput if you have plenty of memory and are processing large document sets.

  To configure the batch size, use:
  - `batch_size`: stand-alone FastEmbed parameter for batch processing. Defaults to `256` for text and `16` for images.
  - `local_inference_batch_size`: Qdrant Client parameter for batch processing. Defaults to `8`.
- `lazy_load`: set to `True` to avoid loading the embedding model until it's needed for inference. Enabling lazy loading prevents loading the model in the main process when using multiple workers, which saves memory and reduces startup time.

## Parallelize FastEmbed with the Qdrant Client

When using FastEmbed with Qdrant Client, specify the `local_inference_batch_size` parameter when initializing the client to configure the batch size. For example:


```python
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    local_inference_batch_size=256,  # FastEmbed batch size
)
```


Next, when creating points, set `lazy_load` to `True` in the inference object to avoid loading the embedding model in the main process:


```python
point = models.PointStruct(
    id=1,
    vector=models.Document(
        text="The text to embed",
        model="BAAI/bge-small-en-v1.5",
        options={
            "lazy_load": True,
        },
    )
)
```


When using [`fastembed-gpu`](https://qdrant.github.io/fastembed/examples/FastEmbed_GPU/), also set `cuda` to `True` to enable GPU acceleration:


```python
point = models.PointStruct(
    id=1,
    vector=models.Document(
        text="The text to embed",
        model="BAAI/bge-small-en-v1.5",
        options={
            "lazy_load": True,
            "cuda": True,
        },
    )
)
```


Finally, when uploading points, set the `parallel` parameter to the desired number of workers:


```python
client.upload_points(
    collection_name=COLLECTION_NAME,
    points=points,
    parallel=4    # use 4 workers to process documents in parallel
)
```


## Parallelize Standalone FastEmbed

When using FastEmbed as a standalone library, first enable lazy loading of the embedding model:


```python
model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    lazy_load=True,       # don't load the model until first embed call
)
```


FastEmbed supports [distributing the workload across multiple GPU devices](https://qdrant.github.io/fastembed/examples/FastEmbed_GPU/). To enable this:
-  Install `fastembed-gpu`.
- Set `cuda` to `True` to enable GPU acceleration.
- Configure `device_ids` with a list of GPU device IDs to assign workers to. For example, `device_ids=[0, 1]` assigns workers to GPUs 0 and 1. If not specified, FastEmbed will assign all workers to the default GPU device.


```python
model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    lazy_load=True,       # don't load the model until first embed call
    cuda=True,            # enable GPU acceleration
    device_ids=[0, 1],    # spread workers across GPUs 0 and 1
)
```


When generating embeddings, set the batch size with `batch_size` and the number of workers with `parallel`:


```python
embeddings = list(model.embed(docs, batch_size=256, parallel=4))
```
