# Hybrid Search# Hybrid Search Using Qdrant Cloud Inference

| Time: 30 min | Level: Intermediate |
| --- | ----------- |

In this tutorial, we'll walkthrough building a **hybrid semantic search engine** using Qdrant Cloud's built-in [inference](/documentation/cloud/inference/index.md) capabilities. You'll learn how to:
- Automatically embed your data using [cloud Inference](/documentation/cloud/inference/index.md) without needing to run local models,
- Combine dense semantic embeddings with [sparse BM25 keywords](/documentation/tutorials-basics/reranking-hybrid-search/index.md),  and
- Perform hybrid search using  [Reciprocal Rank Fusion (RRF)](/documentation/search/hybrid-queries/index.md) to retrieve the most relevant results.

## Initialize the Client
Initialize the Qdrant client after creating a [Qdrant Cloud account](/documentation/cloud/index.md) and a [dedicated paid cluster](/documentation/cloud/create-cluster/index.md). Set `cloud_inference` to `True` to enable [cloud inference](/documentation/cloud/inference/index.md). 


```python
from qdrant_client import QdrantClient

client = QdrantClient(
    "xyz-example.cloud-region.cloud-provider.cloud.qdrant.io",
    api_key="<paste-your-api-key-here>",
    cloud_inference=True,
    timeout=30,
)
```

```typescript
import {QdrantClient} from "@qdrant/js-client-rest";

const client = new QdrantClient({
    url: 'https://xyz-example.qdrant.io:6333',
    apiKey: '<paste-your-api-key-here>',
});
```

```rust
use qdrant_client::Qdrant;

let client = Qdrant::from_url("https://xyz-example.qdrant.io:6334")
    .api_key("<paste-your-api-key-here>")
    .build()
    .unwrap();
```

```java
import io.qdrant.client.QdrantClient;
import io.qdrant.client.QdrantGrpcClient;

QdrantClient client =
      new QdrantClient(
        QdrantGrpcClient.newBuilder("xyz-example.qdrant.io", 6334, true)
        .withApiKey("<paste-your-api-key-here>")
        .build());
```

```csharp
using Qdrant.Client;

var client = new QdrantClient(
  host: "xyz-example.cloud-region.cloud-provider.cloud.qdrant.io",
  https: true,
  apiKey: "<paste-your-api-key-here>"
);
```

```go
import "github.com/qdrant/go-client/qdrant"

client, err := qdrant.NewClient(&qdrant.Config{
	Host:   "xyz-example.cloud-region.cloud-provider.cloud.qdrant.io",
	Port:   6334,
	APIKey: "<paste-your-api-key-here>",
	UseTLS: true,
})
```


## Create a Collection
Qdrant stores vectors and associated metadata in collections. A collection requires vector parameters to be set during creation. In this case, let's set up a collection using `BM25` for sparse vectors and `all-minilm-l6-v2` for dense vectors. BM25 uses the Inverse Document Frequency to reduce the weight of common terms that appear in many documents while boosting the importance of rare terms that are more discriminative for retrieval. Qdrant will handle the calculations of the IDF term if we enable that in the configuration of the `bm25_sparse_vector` named sparse vector.


```python
from qdrant_client import QdrantClient, models

client.create_collection(
    collection_name="{collection_name}",
    vectors_config={
        "dense_vector": models.VectorParams(
            size=384,
            distance=models.Distance.COSINE
        )
    },
    sparse_vectors_config={
        "bm25_sparse_vector": models.SparseVectorParams(
            modifier=models.Modifier.IDF # Enable Inverse Document Frequency
        )
    }
)
```

```typescript
client.createCollection("{collection_name}", {
  vectors: {
    dense_vector: { size: 384, distance: "Cosine" },
  },
  sparse_vectors: {
    bm25_sparse_vector: {
      modifier: "idf" // Enable Inverse Document Frequency
    }
  }
});
```

```rust
use qdrant_client::qdrant::{
    CreateCollectionBuilder, Distance, Modifier, SparseVectorParamsBuilder,
    SparseVectorsConfigBuilder, VectorParamsBuilder, VectorsConfigBuilder,
};

let mut vector_config = VectorsConfigBuilder::default();
vector_config.add_named_vector_params(
    "dense_vector",
    VectorParamsBuilder::new(384, Distance::Cosine),
);

let mut sparse_vectors_config = SparseVectorsConfigBuilder::default();
sparse_vectors_config.add_named_vector_params(
    "bm25_sparse_vector",
    SparseVectorParamsBuilder::default().modifier(Modifier::Idf), // Enable Inverse Document Frequency
);

client
    .create_collection(
        CreateCollectionBuilder::new("{collection_name}")
            .vectors_config(vector_config)
            .sparse_vectors_config(sparse_vectors_config),
    )
    .await?;
```

```java
import io.qdrant.client.grpc.Collections.CreateCollection;
import io.qdrant.client.grpc.Collections.Distance;
import io.qdrant.client.grpc.Collections.Modifier;
import io.qdrant.client.grpc.Collections.SparseVectorConfig;
import io.qdrant.client.grpc.Collections.SparseVectorParams;
import io.qdrant.client.grpc.Collections.VectorParams;
import io.qdrant.client.grpc.Collections.VectorParamsMap;
import io.qdrant.client.grpc.Collections.VectorsConfig;
import java.util.Map;

client
    .createCollectionAsync(
        CreateCollection.newBuilder()
            .setCollectionName("{collection_name}")
            .setVectorsConfig(
                VectorsConfig.newBuilder()
                    .setParamsMap(
                        VectorParamsMap.newBuilder()
                            .putAllMap(
                                Map.of(
                                    "dense_vector",
                                    VectorParams.newBuilder()
                                        .setSize(384)
                                        .setDistance(Distance.Cosine)
                                        .build())))
                    .build())
            .setSparseVectorsConfig(
                SparseVectorConfig.newBuilder()
                    .putMap(
                        "bm25_sparse_vector",
                        SparseVectorParams.newBuilder()
                            .setModifier(Modifier.Idf)
                            .build()))
            .build())
    .get();
```

```csharp
await client.CreateCollectionAsync(
  collectionName: "{collection_name}",
  vectorsConfig: new VectorParamsMap
  {
      Map = {
      ["dense_vector"] = new VectorParams {
        Size = 384, Distance = Distance.Cosine
      },
    }
  },
  sparseVectorsConfig: new SparseVectorConfig
  {
      Map = {
        ["bm25_sparse_vector"] = new() {
    	  Modifier = Modifier.Idf,  // Enable Inverse Document Frequency
  		}
    }
  }
);
```

```go
client.CreateCollection(context.Background(), &qdrant.CreateCollection{
	CollectionName: "{collection_name}",
	VectorsConfig: qdrant.NewVectorsConfigMap(
		map[string]*qdrant.VectorParams{
			"dense_vector": {
				Size:     384,
				Distance: qdrant.Distance_Cosine,
			},
		}),
	SparseVectorsConfig: qdrant.NewSparseVectorsConfig(
		map[string]*qdrant.SparseVectorParams{
			"bm25_sparse_vector": {
				Modifier: qdrant.Modifier_Idf.Enum(),
			},
		},
	),
})
```


## Add Data
Now you can add sample documents, their associated metadata, and a point id for each. Here's a sample of the [miriad/miriad-4.4M](https://huggingface.co/datasets/miriad/miriad-4.4M) dataset:

| qa_id              | paper_id | question                                              | year | venue                                | specialty    | passage_text                                          |
|--------------------|----------|-------------------------------------------------------|------|--------------------------------------|--------------|--------------------------------------------------------|
| 38_77498699_0_1    | 77498699 | What are the clinical features of relapsing polychondritis? | 2006 | Internet Journal of Otorhinolaryngology | Rheumatology | A 45-year-old man presented with painful swelling...  |
| 38_77498699_0_2    | 77498699 | What treatments are available for relapsing polychondritis? | 2006 | Internet Journal of Otorhinolaryngology | Rheumatology | Patient showed improvement after treatment with...     |
| 38_88124321_0_3    | 88124321 | How is Takayasu arteritis diagnosed?                  | 2015 | Journal of Autoimmune Diseases        | Rheumatology | A 32-year-old woman with fatigue and limb pain...      |

We won't ingest all the entries from the dataset, but for demo purposes, just take the first hundred ones:


```python
from qdrant_client.http.models import PointStruct, Document
from datasets import load_dataset
import uuid

dense_model = "sentence-transformers/all-minilm-l6-v2"

bm25_model = "qdrant/bm25"

ds = load_dataset("miriad/miriad-4.4M", split="train[0:100]")

points = []

for idx, item in enumerate(ds):
    passage = item["passage_text"]

    point = PointStruct(
        id=uuid.uuid4().hex,  # use unique string ID
        payload=item,
        vector={
            "dense_vector": Document(
                text=passage,
                model=dense_model
            ),
            "bm25_sparse_vector": Document(
                text=passage,
                model=bm25_model
            )
        }
    )
    points.append(point)

client.upload_points(
    collection_name="{collection_name}", 
    points=points, 
    batch_size=8
)
```

```typescript
import { randomUUID } from "crypto";

const denseModel = "sentence-transformers/all-minilm-l6-v2";
const bm25Model = "qdrant/bm25";
// NOTE: loadDataset is a user-defined function.
// Implement it to handle dataset loading as needed.
const dataset = loadDataset("miriad/miriad-4.4M", "train[0:100]");

const points = dataset.map((item) => {
  const passage = item.passage_text;

  return {
    id: randomUUID().toString(),
    vector: {
      dense_vector: {
        text: passage,
        model: denseModel,
      },
      bm25_sparse_vector: {
        text: passage,
        model: bm25Model,
      },
    },
  };
});

await client.upsert("{collection_name}", { points });
```

```rust
use qdrant_client::qdrant::{
    Document, NamedVectors, PointStruct, UpsertPointsBuilder,
};
use qdrant_client::Payload;
use uuid::Uuid;

let dense_model = "sentence-transformers/all-minilm-l6-v2";
let bm25_model = "qdrant/bm25";
// NOTE: load_dataset is a user-defined function.
// Implement it to handle dataset loading as needed.
let dataset: Vec<_> = load_dataset("miriad/miriad-4.4M", "train[0:100]");

let points: Vec<PointStruct> = dataset
    .iter()
    .map(|item| {
        let passage = item["passage_text"].as_str().unwrap();
        let vectors = NamedVectors::default()
            .add_vector(
                "dense_vector",
                Document::new(passage, dense_model),
            )
            .add_vector(
                "bm25_sparse_vector",
                Document::new(passage, bm25_model),
            );
        let payload = Payload::try_from(item.clone()).unwrap();
        PointStruct::new(Uuid::new_v4().to_string(), vectors, payload)
    })
    .collect();

client
    .upsert_points(UpsertPointsBuilder::new("{collection_name}", points))
    .await?;
```

```java
import static io.qdrant.client.PointIdFactory.id;
import static io.qdrant.client.VectorFactory.vector;
import static io.qdrant.client.VectorsFactory.namedVectors;

import io.qdrant.client.grpc.Points.Document;
import io.qdrant.client.grpc.Points.PointStruct;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

String denseModel = "sentence-transformers/all-minilm-l6-v2";
String bm25Model = "qdrant/bm25";
// NOTE: loadDataset is a user-defined function.
// Implement it to handle dataset loading as needed.
List<Map<String, String>> dataset = loadDataset("miriad/miriad-4.4M", "train[0:100]");
List<PointStruct> points = new ArrayList<>();

for (Map<String, String> item : dataset) {
  String passage = item.get("passage_text");
  PointStruct point =
      PointStruct.newBuilder()
          .setId(id(UUID.randomUUID()))
          .setVectors(
              namedVectors(
                  Map.of(
                      "dense_vector",
                      vector(
                          Document.newBuilder().setText(passage).setModel(denseModel).build()),
                      "bm25_sparse_vector",
                      vector(
                          Document.newBuilder().setText(passage).setModel(bm25Model).build()))))
          .build();
  points.add(point);
}

client.upsertAsync("{collection_name}", points).get();
```

```csharp
var denseModel = "sentence-transformers/all-minilm-l6-v2";
var bm25Model = "qdrant/bm25";
// NOTE: LoadDataset is a user-defined function.
// Implement it to handle dataset loading as needed.
var dataset = LoadDataset("miriad/miriad-4.4M", "train[0:100]");
var points = new List<PointStruct>();

foreach (var item in dataset)
{
    var passage = item["passage_text"].ToString();

    var point = new PointStruct
    {
        Id = Guid.NewGuid(),
        Vectors = new Dictionary<string, Vector>
        {
            ["dense_vector"] = new Document
            {
                Text = passage,
                Model = denseModel
            },
            ["bm25_sparse_vector"] = new Document
            {
                Text = passage,
                Model = bm25Model
            }
        },
    };

    points.Add(point);
}

await client.UpsertAsync(
    collectionName: "{collectionName}",
    points: points
);
```

```go
denseModel := "sentence-transformers/all-minilm-l6-v2"
bm25Model := "qdrant/bm25"
// NOTE: loadDataset is a user-defined function.
// Implement it to handle dataset loading as needed.
dataset := loadDataset("miriad/miriad-4.4M", "train[0:100]")
points := make([]*qdrant.PointStruct, 0, 100)

for _, item := range dataset {
	passage := item["passage_text"]
	point := &qdrant.PointStruct{
		Id: qdrant.NewID(uuid.New().String()),
		Vectors: qdrant.NewVectorsMap(map[string]*qdrant.Vector{
			"dense_vector": qdrant.NewVectorDocument(&qdrant.Document{
				Text:  passage,
				Model: denseModel,
			}),
			"bm25_sparse_vector": qdrant.NewVectorDocument(&qdrant.Document{
				Text:  passage,
				Model: bm25Model,
			}),
		}),
	}
	points = append(points, point)
}
_, err = client.Upsert(context.Background(), &qdrant.UpsertPoints{
	CollectionName: "{collection_name}",
	Points:         points,
})
```

## Set Up Input Query
Create a sample query:


```python
query_text = "What is relapsing polychondritis?"
```

```typescript
let query_text = "What is relapsing polychondritis?";
```

```rust
let query_text = "What is relapsing polychondritis?";
```

```java
String queryText = "What is relapsing polychondritis?";
```

```csharp
var queryText = "What is relapsing polychondritis?";
```

```go
queryText := "What is relapsing polychondritis?"
```


## Run Vector Search
Here, you will ask a question that will allow you to retrieve semantically relevant results. The final results are obtained by reranking using [Reciprocal Rank Fusion](/documentation/search/hybrid-queries/index.md#hybrid-search).


```python
results = client.query_points(
    collection_name="{collection_name}",
    prefetch=[
        models.Prefetch(
            query=models.Document(
                text=query_text,
                model=dense_model
            ),
            using="dense_vector",
            limit=5
        ),
        models.Prefetch(
            query=models.Document(
                text=query_text,
                model=bm25_model
            ),
            using="bm25_sparse_vector",
            limit=5
        )
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=5,
    with_payload=True
)

print(results.points)
```

```typescript
const results = await client.query("{collection_name}", {
    prefetch: [
        {
            query: {
                text: queryText,
                model: denseModel,
            },
            using: "dense_vector",
        },
        {
            query: {
                text: queryText,
                model: bm25Model,
            },
            using: "bm25_sparse_vector",
        },
    ],
    query: {
        fusion: "rrf",
    },
});
```

```rust
use qdrant_client::qdrant::{Document, Fusion, PrefetchQueryBuilder, Query, QueryPointsBuilder};

let dense_prefetch = PrefetchQueryBuilder::default()
    .query(Query::new_nearest(Document::new(query_text, dense_model)))
    .using("dense_vector")
    .build();

let bm25_prefetch = PrefetchQueryBuilder::default()
    .query(Query::new_nearest(Document::new(query_text, bm25_model)))
    .using("bm25_sparse_vector")
    .build();

let query_request = QueryPointsBuilder::new("{collection_name}")
    .add_prefetch(dense_prefetch)
    .add_prefetch(bm25_prefetch)
    .query(Query::new_fusion(Fusion::Rrf))
    .with_payload(true)
    .build();

let results = client.query(query_request).await?;
```

```java
import static io.qdrant.client.QueryFactory.fusion;
import static io.qdrant.client.QueryFactory.nearest;

import io.qdrant.client.grpc.Points.Document;
import io.qdrant.client.grpc.Points.Fusion;
import io.qdrant.client.grpc.Points.PrefetchQuery;
import io.qdrant.client.grpc.Points.QueryPoints;

PrefetchQuery densePrefetch =
    PrefetchQuery.newBuilder()
        .setQuery(
            nearest(Document.newBuilder().setText(queryText).setModel(denseModel).build()))
        .setUsing("dense_vector")
        .build();

PrefetchQuery bm25Prefetch =
    PrefetchQuery.newBuilder()
        .setQuery(nearest(Document.newBuilder().setText(queryText).setModel(bm25Model).build()))
        .setUsing("bm25_sparse_vector")
        .build();

QueryPoints request =
    QueryPoints.newBuilder()
        .setCollectionName("{collection_name}")
        .addPrefetch(densePrefetch)
        .addPrefetch(bm25Prefetch)
        .setQuery(fusion(Fusion.RRF))
        .build();

client.queryAsync(request).get();
```

```csharp
await client.QueryAsync(
collectionName: "{collection_name}", prefetch: new List <PrefetchQuery> {
  new() {
    Query = new Document {
      Text = queryText,
      Model = bm25Model
    },
    Using = "bm25_sparse_vector",
    Limit = 5
  },
  new() {
    Query = new Document {
      Text = queryText,
      Model = denseModel
    },
    Using = "dense_vector",
    Limit = 5
  }
},
query: Fusion.Rrf,
limit: 5
);
```

```go
prefetch := []*qdrant.PrefetchQuery{
	{
		Query: qdrant.NewQueryDocument(&qdrant.Document{
			Text:  queryText,
			Model: bm25Model,
		}),
		Using: qdrant.PtrOf("bm25_sparse_vector"),
	},
	{
		Query: qdrant.NewQueryDocument(&qdrant.Document{
			Text:  queryText,
			Model: denseModel,
		}),
		Using: qdrant.PtrOf("dense_vector"),
	},
}

client.Query(context.Background(), &qdrant.QueryPoints{
	CollectionName: "{collection_name}",
	Prefetch:       prefetch,
	Query:          qdrant.NewQueryFusion(qdrant.Fusion_RRF),
})
```


The semantic search engine will retrieve the most similar result in order of relevance.
```markdown
[ScoredPoint(id='9968a760-fbb5-4d91-8549-ffbaeb3ebdba', 
version=0, score=14.545895, 
payload={'text': "Relapsing Polychondritis is a rare..."}, 
vector=None, shard_key=None, order_value=None)]
```

## Next Steps

Hybrid search result quality can be improved by reranking the results using a more expensive but higher quality model. Learn more in the [hybrid search with reranking tutorial](/documentation/tutorials-basics/reranking-hybrid-search/index.md).