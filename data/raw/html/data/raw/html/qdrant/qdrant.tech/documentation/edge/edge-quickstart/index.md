# Quickstart
# Qdrant Edge Quickstart

## Install Qdrant Edge

First, install the [Python Bindings for Qdrant Edge](https://pypi.org/project/qdrant-edge-py/) or the [Rust crate](https://crates.io/crates/qdrant-edge).

## Create a Storage Directory

A Qdrant Edge Shard stores its data in a local directory on disk. Create the directory if it doesn't exist yet:


```python
from pathlib import Path

SHARD_DIRECTORY = "./qdrant-edge-directory"

Path(SHARD_DIRECTORY).mkdir(parents=True, exist_ok=True)
```

```rust
const SHARD_DIRECTORY: &str = "./qdrant-edge-directory";

fs_err::create_dir_all(SHARD_DIRECTORY)?;
```


## Configure the Edge Shard

An Edge Shard is configured with a definition of the dense and sparse vectors that can be stored in the Edge Shard, similar to how you would configure a Qdrant collection.

Set up a configuration by creating an instance of `EdgeConfig`. For example:


```python
from qdrant_edge import (
    Distance,
    EdgeConfig,
    EdgeVectorParams,
)

VECTOR_NAME="my-vector"
VECTOR_DIMENSION=4

config = EdgeConfig(
    vectors={
        VECTOR_NAME: EdgeVectorParams(
            size=VECTOR_DIMENSION,
            distance=Distance.Cosine,
        )
    }
)
```

```rust
const VECTOR_NAME: &str = "my-vector";
const VECTOR_DIMENSION: usize = 4;

let config = EdgeConfigBuilder::new()
    .on_disk_payload(true)
    .vector(
        VECTOR_NAME,
        EdgeVectorParamsBuilder::new(VECTOR_DIMENSION, Distance::Cosine)
            .on_disk(true)
            .build(),
    )
    .build();
```


Qdrant Edge supports all Qdrant quantization methods: Scalar, Product, Binary, and TurboQuant. Configure quantization globally on `EdgeConfig.quantization_config` or override per-vector on `EdgeVectorParams.quantization_config`. See the [Quantization](/documentation/manage-data/quantization/index.md) guide for configuration details.

## Initialize the Edge Shard

Now you can create a new `EdgeShard` using `EdgeShard.create` (Python) or `EdgeShard::new` (Rust), passing the storage directory and configuration:


```python
from qdrant_edge import EdgeShard

edge_shard = EdgeShard.create(SHARD_DIRECTORY, config)
```

```rust
let edge_shard = EdgeShard::new(
    Path::new(SHARD_DIRECTORY),
    config,
)?;
```


Note that `create` and `new` will fail if the storage directory already contains data. To initialize an Edge Shard with existing data, see [Load Existing Edge Shard from Disk](#load-existing-edge-shard-from-disk).

## Work with Points

An Edge Shard has several methods to work with points. To add points, use the `update` method:


```python
from qdrant_edge import ( Point, UpdateOperation )

point = Point(
    id=1,
    vector={VECTOR_NAME: [0.1, 0.2, 0.3, 0.4]},
    payload={"color": "red"}
)

edge_shard.update(UpdateOperation.upsert_points([point]))
```

```rust
let points: Vec<PointStructPersisted> = vec![
    PointStruct::new(
        1u64,
        Vectors::new_named([(VECTOR_NAME, vec![0.1f32, 0.2, 0.3, 0.4])]),
        json!({"color": "red"}),
    )
    .into(),
];

edge_shard.update(UpdateOperation::PointOperation(
    PointOperations::UpsertPoints(
        PointInsertOperations::PointsList(points),
    ),
))?;
```


To retrieve a point by ID, use the `retrieve` method:


```python
records = edge_shard.retrieve(
    point_ids=[1],
    with_payload=True,
    with_vector=False
)
```

```rust
let retrieved = edge_shard.retrieve(
    &[PointId::NumId(1)],
    Some(WithPayloadInterface::Bool(true)),
    Some(WithVector::Bool(false)),
)?;
```


## Modify the Vector Schema

You can add or remove named vectors to an existing Edge Shard's schema. This is useful when migrating to a new embedding model or adding hybrid search to an Edge Shard that already contains data.

For example, to add a sparse vector for [BM25 keyword search](/documentation/edge/edge-bm25/index.md):


```python
from qdrant_edge import Modifier

edge_shard.update(UpdateOperation.create_sparse_vector(
    vector_name="text",
    modifier=Modifier.Idf,
))
```

```rust
edge_shard.update(UpdateOperation::VectorNameOperation(
    VectorNameOperations::CreateVectorName(CreateVectorName {
        vector_name: "text".to_string(),
        config: VectorNameConfig::sparse(SparseVectorConfig {
            modifier: Some(Modifier::Idf),
            datatype: None,
        }),
    }),
))?;
```


Existing points aren't automatically populated with the new vector. Re-upsert them to add their values for the new field.

To remove a named vector, use `UpdateOperation.delete_vector_name("text")` (Python) or `VectorNameOperations::DeleteVectorName` (Rust).

## Create a Payload Index

To optimize operations like [filtering](#filtering) and [faceting](#faceting) on payload fields, first create a payload index on the fields you plan to use with these operations:


```python
from qdrant_edge import PayloadSchemaType

edge_shard.update(UpdateOperation.create_field_index("color", PayloadSchemaType.Keyword))
```

```rust
edge_shard.update(UpdateOperation::FieldIndexOperation(
    FieldIndexOperations::CreateIndex(CreateIndex {
        field_name: "color".try_into().unwrap(),
        field_schema: Some(PayloadFieldSchema::FieldType(
            PayloadSchemaType::Keyword,
        )),
    }),
))?;
```


## Query Points

To query points in the Edge Shard, use the `query` method:


```python
from qdrant_edge import Query, QueryRequest

results = edge_shard.query(
    QueryRequest(
        query=Query.Nearest([0.2, 0.1, 0.9, 0.7], using=VECTOR_NAME),
        limit=10,
        with_vector=False,
        with_payload=True
    )
)
```

```rust
let results = edge_shard.query(QueryRequest {
    prefetches: vec![],
    query: Some(ScoringQuery::Vector(QueryEnum::Nearest(NamedQuery {
        query: vec![0.2f32, 0.1, 0.9, 0.7].into(),
        using: Some(VECTOR_NAME.to_string()),
    }))),
    filter: None,
    score_threshold: None,
    limit: 10,
    offset: 0,
    params: None,
    with_vector: WithVector::Bool(false),
    with_payload: WithPayloadInterface::Bool(true),
})?;
```


## Filter points

You can also filter points based on payload fields:


```python
from qdrant_edge import FieldCondition, Filter, MatchValue

results = edge_shard.query(
    QueryRequest(
        query=Query.Nearest([0.2, 0.1, 0.9, 0.7], using=VECTOR_NAME),
        filter=Filter(
            must=[
                FieldCondition(
                    key="color",
                    match=MatchValue(value="red"),
                )
            ]
        ),
        limit=10,
        with_vector=False,
        with_payload=True
    )
)
```

```rust
let filter = Filter {
    should: None,
    min_should: None,
    must: Some(vec![Condition::Field(FieldCondition::new_match(
        "color".try_into().unwrap(),
        Match::Value(MatchValue {
            value: ValueVariants::String("red".to_string()),
        }),
    ))]),
    must_not: None,
};

let results = edge_shard.query(QueryRequest {
    prefetches: vec![],
    query: Some(ScoringQuery::Vector(QueryEnum::Nearest(NamedQuery {
        query: vec![0.2f32, 0.1, 0.9, 0.7].into(),
        using: Some(VECTOR_NAME.to_string()),
    }))),
    filter: Some(filter),
    score_threshold: None,
    limit: 10,
    offset: 0,
    params: None,
    with_vector: WithVector::Bool(false),
    with_payload: WithPayloadInterface::Bool(true),
})?;
```


## Create Facets

To create facets on a payload field, use the `facet` method.


```python
from qdrant_edge import FacetRequest

facet_response = edge_shard.facet(FacetRequest(key="color", limit=10, exact=False))
```

```rust
let facet_response = edge_shard.facet(FacetRequest {
    key: "color".try_into().unwrap(),
    limit: 10,
    filter: None,
    exact: false,
})?;
```


## Optimize the Edge Shard

Optimization is the process of removing data marked for deletion, merging segments, and creating indexes. Qdrant Edge does not have a background optimizer. Instead, an application can call the `optimize` method to synchronously run optimization at a suitable time, such as during low-traffic periods or after a batch of updates.


```python
edge_shard.optimize()
```

```rust
edge_shard.optimize()?;
```


The optimizer can be configured using the `optimizers` parameter of `EdgeConfig` when initializing the Edge Shard. For example:


```python
from qdrant_edge import EdgeOptimizersConfig

config = EdgeConfig(
    vectors={
        VECTOR_NAME: EdgeVectorParams(
            size=VECTOR_DIMENSION,
            distance=Distance.Cosine,
        )
    },
    optimizers=EdgeOptimizersConfig(
        deleted_threshold=0.2,
        vacuum_min_vector_number=100,
        default_segment_number=2,
    ),
)
```

```rust
let config = EdgeConfigBuilder::new()
    .on_disk_payload(true)
    .vector(
        VECTOR_NAME,
        EdgeVectorParamsBuilder::new(VECTOR_DIMENSION, Distance::Cosine)
            .on_disk(true)
            .build(),
    )
    .optimizers(EdgeOptimizersConfig {
        deleted_threshold: Some(0.2),
        vacuum_min_vector_number: Some(100),
        default_segment_number: Some(2),
        ..Default::default()
    })
    .build();
```


## Close the Edge Shard

When shutting down your application, close the Edge Shard to ensure all data is flushed to disk. The data is persisted on disk and can be used to reopen the Edge Shard.


```python
edge_shard.close()
```

```rust
drop(edge_shard);
```


## Load Existing Edge Shard from Disk

After closing an Edge Shard, you can reopen it by loading its data and configuration from disk using the `load` method:


```python
edge_shard = EdgeShard.load(SHARD_DIRECTORY)
```

```rust
let edge_shard = EdgeShard::load(Path::new(SHARD_DIRECTORY), None)?;
```


## Custom WAL Size

Qdrant Edge uses a Write-Ahead Log (WAL) to record every update before it's applied to storage. The WAL file is pre-allocated to 32 MB by default, inflating backup sizes and OS storage reports. To reduce the size, set `wal_options` on `EdgeConfig` when calling `new` or `load`. WAL options are only available in Rust.

For example, to set the WAL size to 4 MB:


```rust
let config = EdgeConfigBuilder::new()
    .wal_options(WalOptions {
        segment_capacity: 4 * 1024 * 1024,
        ..Default::default()
    })
    .build();

let edge_shard = EdgeShard::load(Path::new(SHARD_DIRECTORY), Some(config))?;
```


## More Examples

The Qdrant GitHub repository contains examples of using the Qdrant Edge API in [Python](https://github.com/qdrant/qdrant/tree/dev/lib/edge/python/examples) and [Rust](https://github.com/qdrant/qdrant/tree/dev/lib/edge/publish/examples).