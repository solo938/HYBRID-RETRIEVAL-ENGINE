# BM25
# BM25 with Qdrant Edge

[BM25](/documentation/search/text-search/index.md#bm25) (Best Matching 25) is a popular sparse-vector ranking algorithm for full-text search. Qdrant Edge includes a built-in BM25 embedder, so you can run keyword search without an internet connection or external embedding service.

The BM25 embedder is compatible with server-side BM25: vectors produced by the Qdrant Edge embedder use the same token IDs and scoring formula as Qdrant Server's [text search](/documentation/search/text-search/index.md#bm25) pipeline. You can initialize an Edge Shard from a server snapshot and query it with locally produced BM25 vectors without re-indexing.

In Python, use the `Bm25` and `Bm25Config` classes. In Rust, use `EdgeBm25` and `EdgeBm25Config` from the `qdrant_edge::bm25_embed` module.

## Configure a Sparse Vector

To get started with BM25, create an Edge Shard with a sparse vector field and `Modifier.Idf`. The IDF modifier enables inverse document frequency weighting, which is required for BM25 scoring:


```python
from qdrant_edge import (
    EdgeConfig,
    EdgeShard,
    EdgeSparseVectorParams,
    Modifier,
)

config = EdgeConfig(
    sparse_vectors={"text": EdgeSparseVectorParams(modifier=Modifier.Idf)},
)

shard = EdgeShard.create(SHARD_DIRECTORY, config)
```

```rust
let config = EdgeConfigBuilder::new()
    .sparse_vector("text", EdgeSparseVectorParamsBuilder::new()
        .modifier(Modifier::Idf)
        .build())
    .build();

let shard = EdgeShard::new(Path::new(SHARD_DIRECTORY), config)?;
```


## Create a BM25 Embedder

Instantiate a BM25 embedder with a language setting. The embedder applies stemming and stopword filtering for the specified language:


```python
from qdrant_edge import Bm25, Bm25Config

bm25 = Bm25(Bm25Config(language="english"))
```

```rust
let bm25 = EdgeBm25::new(EdgeBm25Config {
    language: Some("english".to_string()),
    ..Default::default()
})?;
```


`Bm25Config` accepts the following parameters:

| Parameter | Description |
|---|---|
| `language` | Language for stemming and stopwords (for example, `"english"`, `"german"`). Defaults to `None`, which falls back to English stemming and stopwords. |
| `k` | Term frequency saturation parameter. Default: `1.2`. |
| `b` | Document length normalization factor. Default: `0.75`. |
| `avg_len` | Expected average document length in tokens. Default: `256`. |
| `lowercase` | Convert tokens to lowercase before embedding. Default: `true`. |
| `ascii_folding` | Normalize accented characters to ASCII equivalents. Default: `false`. |
| `stemmer` | Override the stemming algorithm. |
| `stopwords` | Override the stopword list. |
| `tokenizer` | Tokenizer used to break down text into individual tokens (words). Can be `"prefix"`, `"whitespace"`, `"word"`, or `"multilingual"`. Default: `"word"`. |
| `min_token_len` | Minimum token length to include. |
| `max_token_len` | Maximum token length to include. |

For a full description of each parameter, see [Configuring BM25 Parameters](/documentation/search/text-search/index.md#configuring-bm25-parameters).

## Embed and Upsert Documents

Use `embed_document` to generate a sparse vector for each document, then upsert the points. Call `optimize` after bulk inserts to build the sparse index:


```python
from qdrant_edge import Point, UpdateOperation

shard.update(UpdateOperation.upsert_points([
    Point(1, {"text": bm25.embed_document("the quick brown fox")}, {"title": "Article 1"}),
    Point(2, {"text": bm25.embed_document("a lazy dog sleeps")},   {"title": "Article 2"}),
    Point(3, {"text": bm25.embed_document("foxes are clever")},    {"title": "Article 3"}),
]))
shard.optimize()
```

```rust
let docs = [
    (1u64, "the quick brown fox", "Article 1"),
    (2,    "a lazy dog sleeps",   "Article 2"),
    (3,    "foxes are clever",    "Article 3"),
];

let points = docs.iter().map(|(id, text, title)| {
    PointStruct::new(
        *id,
        Vectors::new_named([("text", bm25.embed_document(text))]),
        json!({ "title": title }),
    ).into()
}).collect();

shard.update(UpdateOperation::PointOperation(
    PointOperations::UpsertPoints(PointInsertOperations::PointsList(points)),
))?;
shard.optimize()?;
```


## Query

Use `embed_query` to generate a sparse vector for the query text, then query the shard:


```python
from qdrant_edge import Query, QueryRequest

query_vector = bm25.embed_query("clever fox")

results = shard.query(QueryRequest(
    query=Query.Nearest(query_vector, using="text"),
    limit=3,
    with_payload=True,
))
```

```rust
let query_vector = bm25.embed_query("clever fox");

let results = shard.query(QueryRequest {
    prefetches: vec![],
    query: Some(ScoringQuery::Vector(QueryEnum::Nearest(NamedQuery {
        query: VectorInternal::from(query_vector),
        using: Some("text".to_string()),
    }))),
    filter: None,
    score_threshold: None,
    limit: 3,
    offset: 0,
    params: None,
    with_vector: WithVector::Bool(false),
    with_payload: WithPayloadInterface::Bool(true),
})?;
```


Always use `embed_query` for query text and `embed_document` for document text. Using the wrong function produces incorrect results, since BM25 applies different term weighting depending on the input type.
