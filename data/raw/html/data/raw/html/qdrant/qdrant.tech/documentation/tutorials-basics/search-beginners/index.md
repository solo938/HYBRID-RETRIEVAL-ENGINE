# Semantic Search 101
# Build a Semantic Search Engine in 5 Minutes

| Time: 5 - 15 min | Level: Beginner |  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://githubtocolab.com/qdrant/examples/blob/master/semantic-search-in-5-minutes/semantic_search_in_5_minutes.ipynb)   |
| --- | ----------- | ----------- |----------- |

> There are two versions of this tutorial:
>
> - The version on this page uses Qdrant Cloud. You'll deploy a cluster and generate vector embedding in the cloud using Qdrant Cloud's **forever free** tier (no credit card required). 
> - Alternatively, you can run Qdrant on your own machine. This requires you to manage your own cluster and vector embedding infrastructure. If you prefer this option, check out the [local deployment version of this tutorial](/documentation/tutorials-basics/search-beginners-local/index.md).

## Overview

If you are new to vector search engines, this tutorial is for you. In 5 minutes you will build a semantic search engine for science fiction books. After you set it up, you will ask the engine about an impending alien threat. Your creation will recommend books as preparation for a potential space attack.

If you are using Python, you can use [this Google Colab notebook](https://githubtocolab.com/qdrant/examples/blob/master/semantic-search-in-5-minutes/semantic_search_in_5_minutes.ipynb).

## 1. Create a Qdrant Cluster

If you do not already have a Qdrant cluster, follow these steps to create one:

1. Register for a [Qdrant Cloud account](https://cloud.qdrant.io) using your email, Google, or Github credentials.
1. Under **Create a Free Cluster**, enter a cluster name and select your preferred cloud provider and region.
1. Click **Create Free Cluster**.
1. Copy the **API key** when prompted and store it somewhere safe as it won’t be displayed again.
1. Copy the **Cluster Endpoint**. It should look something like `https://xxx.cloud.qdrant.io`.


## 2. Set up a Client Connection

First, install the Qdrant Client for your preferred programming language:


```python
qdrant-client
```
```typescript
qdrant/js-client-rest
```
```rust
qdrant-client
```
```java
io.qdrant:client
```
```csharp
Qdrant.Client
```
```go
github.com/qdrant/go-client
```

This library allows you to interact with Qdrant from code.

Next, create a client connection to your Qdrant cluster using the endpoint and API key.


```python
from qdrant_client import QdrantClient, models

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    cloud_inference=True
)
```

```typescript
const client = new QdrantClient({
    url: QDRANT_URL,
    apiKey: QDRANT_API_KEY,
});
```

```rust
let client = Qdrant::from_url(QDRANT_URL)
    .api_key(QDRANT_API_KEY)
    .build()?;
```

```java
QdrantClient client =
    new QdrantClient(
        QdrantGrpcClient.newBuilder(QDRANT_URL, 6334, true)
            .withApiKey(QDRANT_API_KEY)
            .build());
```

```csharp
var client = new QdrantClient(
	host: QDRANT_URL,
	port: 6334,
	https: true,
	apiKey: QDRANT_API_KEY
);
```

```go
client, err := qdrant.NewClient(&qdrant.Config{
	Host:   QDRANT_URL,
	APIKey: QDRANT_API_KEY,
	UseTLS: true,
})
```


Replace `QDRANT_URL` and `QDRANT_API_KEY` with the cluster endpoint and API key you obtained in the previous step. The `cloud_inference=True` parameter enables Qdrant Cloud's [inference](/documentation/inference/index.md) capabilities, allowing the cluster to generate vector embeddings without the need to manage your own embedding infrastructure. 

## 3. Create a Collection

All data in Qdrant is organized within [collections](/documentation/manage-data/collections/index.md). Since you're storing books, let's create a collection named `my_books`.


```python
COLLECTION_NAME="my_books"

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(
        size=384,  # Vector size is defined by used model
        distance=models.Distance.COSINE,
    ),
)
```

```typescript
const collectionName = "my_books";

await client.createCollection(collectionName, {
    vectors: {
        size: 384, // Vector size is defined by used model
        distance: "Cosine",
    },
});
```

```rust
let collection_name = "my_books";

client
    .create_collection(
        CreateCollectionBuilder::new(collection_name)
            .vectors_config(VectorParamsBuilder::new(384, Distance::Cosine)), // Vector size is defined by used model
    )
    .await?;
```

```java
String COLLECTION_NAME = "my_books";

client.createCollectionAsync(COLLECTION_NAME,
        VectorParams.newBuilder().setDistance(Distance.Cosine).setSize(384).build()).get();
```

```csharp
string COLLECTION_NAME = "my_books";

await client.CreateCollectionAsync(
	collectionName: COLLECTION_NAME,
	vectorsConfig: new VectorParams { Size = 384, Distance = Distance.Cosine }
);
```

```go
collectionName := "my_books"

client.CreateCollection(context.Background(), &qdrant.CreateCollection{
	CollectionName: collectionName,
	VectorsConfig: qdrant.NewVectorsConfig(&qdrant.VectorParams{
		Size:     384, // Vector size is defined by used model
		Distance: qdrant.Distance_Cosine,
	}),
})
```


- The `size` parameter defines the dimensionality of the vectors for the collection. 384 corresponds to the output dimensionality of the embedding model used in this tutorial.
- The `distance` parameter specifies the function used to measure the distance between two points.

## 4. Upload Data to the Cluster

The dataset consists of a list of science fiction books. Each entry has a name, author, publication year, and short description. 


```python
documents = [
    {
        "name": "The Time Machine",
        "description": "A man travels through time and witnesses the evolution of humanity.",
        "author": "H.G. Wells",
        "year": 1895,
    },
    {
        "name": "Ender's Game",
        "description": "A young boy is trained to become a military leader in a war against an alien race.",
        "author": "Orson Scott Card",
        "year": 1985,
    },
    {
        "name": "Brave New World",
        "description": "A dystopian society where people are genetically engineered and conditioned to conform to a strict social hierarchy.",
        "author": "Aldous Huxley",
        "year": 1932,
    },
    {
        "name": "The Hitchhiker's Guide to the Galaxy",
        "description": "A comedic science fiction series following the misadventures of an unwitting human and his alien friend.",
        "author": "Douglas Adams",
        "year": 1979,
    },
    {
        "name": "Dune",
        "description": "A desert planet is the site of political intrigue and power struggles.",
        "author": "Frank Herbert",
        "year": 1965,
    },
    {
        "name": "Foundation",
        "description": "A mathematician develops a science to predict the future of humanity and works to save civilization from collapse.",
        "author": "Isaac Asimov",
        "year": 1951,
    },
    {
        "name": "Snow Crash",
        "description": "A futuristic world where the internet has evolved into a virtual reality metaverse.",
        "author": "Neal Stephenson",
        "year": 1992,
    },
    {
        "name": "Neuromancer",
        "description": "A hacker is hired to pull off a near-impossible hack and gets pulled into a web of intrigue.",
        "author": "William Gibson",
        "year": 1984,
    },
    {
        "name": "The War of the Worlds",
        "description": "A Martian invasion of Earth throws humanity into chaos.",
        "author": "H.G. Wells",
        "year": 1898,
    },
    {
        "name": "The Hunger Games",
        "description": "A dystopian society where teenagers are forced to fight to the death in a televised spectacle.",
        "author": "Suzanne Collins",
        "year": 2008,
    },
    {
        "name": "The Andromeda Strain",
        "description": "A deadly virus from outer space threatens to wipe out humanity.",
        "author": "Michael Crichton",
        "year": 1969,
    },
    {
        "name": "The Left Hand of Darkness",
        "description": "A human ambassador is sent to a planet where the inhabitants are genderless and can change gender at will.",
        "author": "Ursula K. Le Guin",
        "year": 1969,
    },
    {
        "name": "The Three-Body Problem",
        "description": "Humans encounter an alien civilization that lives in a dying system.",
        "author": "Liu Cixin",
        "year": 2008,
    },
]
```

```typescript
const documents = [
    { name: "The Time Machine", description: "A man travels through time and witnesses the evolution of humanity.", author: "H.G. Wells", year: 1895 },
    { name: "Ender's Game", description: "A young boy is trained to become a military leader in a war against an alien race.", author: "Orson Scott Card", year: 1985 },
    { name: "Brave New World", description: "A dystopian society where people are genetically engineered and conditioned to conform to a strict social hierarchy.", author: "Aldous Huxley", year: 1932 },
    { name: "The Hitchhiker's Guide to the Galaxy", description: "A comedic science fiction series following the misadventures of an unwitting human and his alien friend.", author: "Douglas Adams", year: 1979 },
    { name: "Dune", description: "A desert planet is the site of political intrigue and power struggles.", author: "Frank Herbert", year: 1965 },
    { name: "Foundation", description: "A mathematician develops a science to predict the future of humanity and works to save civilization from collapse.", author: "Isaac Asimov", year: 1951 },
    { name: "Snow Crash", description: "A futuristic world where the internet has evolved into a virtual reality metaverse.", author: "Neal Stephenson", year: 1992 },
    { name: "Neuromancer", description: "A hacker is hired to pull off a near-impossible hack and gets pulled into a web of intrigue.", author: "William Gibson", year: 1984 },
    { name: "The War of the Worlds", description: "A Martian invasion of Earth throws humanity into chaos.", author: "H.G. Wells", year: 1898 },
    { name: "The Hunger Games", description: "A dystopian society where teenagers are forced to fight to the death in a televised spectacle.", author: "Suzanne Collins", year: 2008 },
    { name: "The Andromeda Strain", description: "A deadly virus from outer space threatens to wipe out humanity.", author: "Michael Crichton", year: 1969 },
    { name: "The Left Hand of Darkness", description: "A human ambassador is sent to a planet where the inhabitants are genderless and can change gender at will.", author: "Ursula K. Le Guin", year: 1969 },
    { name: "The Three-Body Problem", description: "Humans encounter an alien civilization that lives in a dying system.", author: "Liu Cixin", year: 2008 },
];
```

```rust
let documents = [
    ("The Time Machine", "A man travels through time and witnesses the evolution of humanity.", "H.G. Wells", 1895),
    ("Ender's Game", "A young boy is trained to become a military leader in a war against an alien race.", "Orson Scott Card", 1985),
    ("Brave New World", "A dystopian society where people are genetically engineered and conditioned to conform to a strict social hierarchy.", "Aldous Huxley", 1932),
    ("The Hitchhiker's Guide to the Galaxy", "A comedic science fiction series following the misadventures of an unwitting human and his alien friend.", "Douglas Adams", 1979),
    ("Dune", "A desert planet is the site of political intrigue and power struggles.", "Frank Herbert", 1965),
    ("Foundation", "A mathematician develops a science to predict the future of humanity and works to save civilization from collapse.", "Isaac Asimov", 1951),
    ("Snow Crash", "A futuristic world where the internet has evolved into a virtual reality metaverse.", "Neal Stephenson", 1992),
    ("Neuromancer", "A hacker is hired to pull off a near-impossible hack and gets pulled into a web of intrigue.", "William Gibson", 1984),
    ("The War of the Worlds", "A Martian invasion of Earth throws humanity into chaos.", "H.G. Wells", 1898),
    ("The Hunger Games", "A dystopian society where teenagers are forced to fight to the death in a televised spectacle.", "Suzanne Collins", 2008),
    ("The Andromeda Strain", "A deadly virus from outer space threatens to wipe out humanity.", "Michael Crichton", 1969),
    ("The Left Hand of Darkness", "A human ambassador is sent to a planet where the inhabitants are genderless and can change gender at will.", "Ursula K. Le Guin", 1969),
    ("The Three-Body Problem", "Humans encounter an alien civilization that lives in a dying system.", "Liu Cixin", 2008),
];
```

```java
List<Map<String, Value>> payloads = List.of(
    Map.of(
        "name", value("The Time Machine"),
        "description", value("A man travels through time and witnesses the evolution of humanity."),
        "author", value("H.G. Wells"),
        "year", value(1895)),
    Map.of(
        "name", value("Ender's Game"),
        "description",
            value("A young boy is trained to become a military leader in a war against an alien race."),
        "author", value("Orson Scott Card"),
        "year", value(1985)),
    Map.of(
        "name", value("Brave New World"),
        "description",
            value(
                "A dystopian society where people are genetically engineered and conditioned to conform to a strict social hierarchy."),
        "author", value("Aldous Huxley"),
        "year", value(1932)),
    Map.of(
        "name", value("The Hitchhiker's Guide to the Galaxy"),
        "description",
            value(
                "A comedic science fiction series following the misadventures of an unwitting human and his alien friend."),
        "author", value("Douglas Adams"),
        "year", value(1979)),
    Map.of(
        "name", value("Dune"),
        "description", value("A desert planet is the site of political intrigue and power struggles."),
        "author", value("Frank Herbert"),
        "year", value(1965)),
    Map.of(
        "name", value("Foundation"),
        "description",
            value(
                "A mathematician develops a science to predict the future of humanity and works to save civilization from collapse."),
        "author", value("Isaac Asimov"),
        "year", value(1951)),
    Map.of(
        "name", value("Snow Crash"),
        "description",
            value("A futuristic world where the internet has evolved into a virtual reality metaverse."),
        "author", value("Neal Stephenson"),
        "year", value(1992)),
    Map.of(
        "name", value("Neuromancer"),
        "description",
            value(
                "A hacker is hired to pull off a near-impossible hack and gets pulled into a web of intrigue."),
        "author", value("William Gibson"),
        "year", value(1984)),
    Map.of(
        "name", value("The War of the Worlds"),
        "description", value("A Martian invasion of Earth throws humanity into chaos."),
        "author", value("H.G. Wells"),
        "year", value(1898)),
    Map.of(
        "name", value("The Hunger Games"),
        "description",
            value("A dystopian society where teenagers are forced to fight to the death in a televised spectacle."),
        "author", value("Suzanne Collins"),
        "year", value(2008)),
    Map.of(
        "name", value("The Andromeda Strain"),
        "description", value("A deadly virus from outer space threatens to wipe out humanity."),
        "author", value("Michael Crichton"),
        "year", value(1969)),
    Map.of(
        "name", value("The Left Hand of Darkness"),
        "description",
            value(
                "A human ambassador is sent to a planet where the inhabitants are genderless and can change gender at will."),
        "author", value("Ursula K. Le Guin"),
        "year", value(1969)),
    Map.of(
        "name", value("The Three-Body Problem"),
        "description", value("Humans encounter an alien civilization that lives in a dying system."),
        "author", value("Liu Cixin"),
        "year", value(2008)));
```

```csharp
var payloads = new List<Dictionary<string, Value>>
{
	new() { ["name"] = "The Time Machine", ["description"] = "A man travels through time and witnesses the evolution of humanity.", ["author"] = "H.G. Wells", ["year"] = 1895 },
	new() { ["name"] = "Ender's Game", ["description"] = "A young boy is trained to become a military leader in a war against an alien race.", ["author"] = "Orson Scott Card", ["year"] = 1985 },
	new() { ["name"] = "Brave New World", ["description"] = "A dystopian society where people are genetically engineered and conditioned to conform to a strict social hierarchy.", ["author"] = "Aldous Huxley", ["year"] = 1932 },
	new() { ["name"] = "The Hitchhiker's Guide to the Galaxy", ["description"] = "A comedic science fiction series following the misadventures of an unwitting human and his alien friend.", ["author"] = "Douglas Adams", ["year"] = 1979 },
	new() { ["name"] = "Dune", ["description"] = "A desert planet is the site of political intrigue and power struggles.", ["author"] = "Frank Herbert", ["year"] = 1965 },
	new() { ["name"] = "Foundation", ["description"] = "A mathematician develops a science to predict the future of humanity and works to save civilization from collapse.", ["author"] = "Isaac Asimov", ["year"] = 1951 },
	new() { ["name"] = "Snow Crash", ["description"] = "A futuristic world where the internet has evolved into a virtual reality metaverse.", ["author"] = "Neal Stephenson", ["year"] = 1992 },
	new() { ["name"] = "Neuromancer", ["description"] = "A hacker is hired to pull off a near-impossible hack and gets pulled into a web of intrigue.", ["author"] = "William Gibson", ["year"] = 1984 },
	new() { ["name"] = "The War of the Worlds", ["description"] = "A Martian invasion of Earth throws humanity into chaos.", ["author"] = "H.G. Wells", ["year"] = 1898 },
	new() { ["name"] = "The Hunger Games", ["description"] = "A dystopian society where teenagers are forced to fight to the death in a televised spectacle.", ["author"] = "Suzanne Collins", ["year"] = 2008 },
	new() { ["name"] = "The Andromeda Strain", ["description"] = "A deadly virus from outer space threatens to wipe out humanity.", ["author"] = "Michael Crichton", ["year"] = 1969 },
	new() { ["name"] = "The Left Hand of Darkness", ["description"] = "A human ambassador is sent to a planet where the inhabitants are genderless and can change gender at will.", ["author"] = "Ursula K. Le Guin", ["year"] = 1969 },
	new() { ["name"] = "The Three-Body Problem", ["description"] = "Humans encounter an alien civilization that lives in a dying system.", ["author"] = "Liu Cixin", ["year"] = 2008 }
};
```

```go
documents := []map[string]any{
	{
		"name":        "The Time Machine",
		"description": "A man travels through time and witnesses the evolution of humanity.",
		"author":      "H.G. Wells",
		"year":        1895,
	},
	{
		"name":        "Ender's Game",
		"description": "A young boy is trained to become a military leader in a war against an alien race.",
		"author":      "Orson Scott Card",
		"year":        1985,
	},
	{
		"name":        "Brave New World",
		"description": "A dystopian society where people are genetically engineered and conditioned to conform to a strict social hierarchy.",
		"author":      "Aldous Huxley",
		"year":        1932,
	},
	{
		"name":        "The Hitchhiker's Guide to the Galaxy",
		"description": "A comedic science fiction series following the misadventures of an unwitting human and his alien friend.",
		"author":      "Douglas Adams",
		"year":        1979,
	},
	{
		"name":        "Dune",
		"description": "A desert planet is the site of political intrigue and power struggles.",
		"author":      "Frank Herbert",
		"year":        1965,
	},
	{
		"name":        "Foundation",
		"description": "A mathematician develops a science to predict the future of humanity and works to save civilization from collapse.",
		"author":      "Isaac Asimov",
		"year":        1951,
	},
	{
		"name":        "Snow Crash",
		"description": "A futuristic world where the internet has evolved into a virtual reality metaverse.",
		"author":      "Neal Stephenson",
		"year":        1992,
	},
	{
		"name":        "Neuromancer",
		"description": "A hacker is hired to pull off a near-impossible hack and gets pulled into a web of intrigue.",
		"author":      "William Gibson",
		"year":        1984,
	},
	{
		"name":        "The War of the Worlds",
		"description": "A Martian invasion of Earth throws humanity into chaos.",
		"author":      "H.G. Wells",
		"year":        1898,
	},
	{
		"name":        "The Hunger Games",
		"description": "A dystopian society where teenagers are forced to fight to the death in a televised spectacle.",
		"author":      "Suzanne Collins",
		"year":        2008,
	},
	{
		"name":        "The Andromeda Strain",
		"description": "A deadly virus from outer space threatens to wipe out humanity.",
		"author":      "Michael Crichton",
		"year":        1969,
	},
	{
		"name":        "The Left Hand of Darkness",
		"description": "A human ambassador is sent to a planet where the inhabitants are genderless and can change gender at will.",
		"author":      "Ursula K. Le Guin",
		"year":        1969,
	},
	{
		"name":        "The Three-Body Problem",
		"description": "Humans encounter an alien civilization that lives in a dying system.",
		"author":      "Liu Cixin",
		"year":        2008,
	},
}
```


Store each book as a [point](/documentation/manage-data/points/index.md) in the `my_books` collection, with each point consisting of a [unique ID](/documentation/manage-data/points/index.md#point-ids), a [vector](/documentation/manage-data/vectors/index.md) generated from the description, and a [payload](/documentation/manage-data/payload/index.md) containing the book's metadata:


```python
EMBEDDING_MODEL="sentence-transformers/all-minilm-l6-v2"

client.upload_points(
    collection_name=COLLECTION_NAME,
    points=[
        models.PointStruct(
            id=idx,
            vector=models.Document(
                text=doc["description"],
                model=EMBEDDING_MODEL
            ),
            payload=doc
        )
        for idx, doc in enumerate(documents)
    ],
)
```

```typescript
const embeddingModel = "sentence-transformers/all-minilm-l6-v2";

const points = documents.map((doc, idx) => ({
    id: idx,
    vector: {
        text: doc.description,
        model: embeddingModel,
    },
    payload: doc,
}));

await client.upsert(collectionName, { points });
```

```rust
let embedding_model = "sentence-transformers/all-minilm-l6-v2";

let points: Vec<PointStruct> = documents
    .iter()
    .enumerate()
    .map(|(idx, (name, description, author, year))| {
        PointStruct::new(
            idx as u64,
            Document::new(*description, embedding_model),
            [
                ("name", (*name).into()),
                ("description", (*description).into()),
                ("author", (*author).into()),
                ("year", (*year).into()),
            ],
        )
    })
    .collect();

client
    .upsert_points(UpsertPointsBuilder::new(collection_name, points))
    .await?;
```

```java
String EMBEDDING_MODEL = "sentence-transformers/all-minilm-l6-v2";

List<PointStruct> points = new ArrayList<>();

for (int idx = 0; idx < payloads.size(); idx++) {
    Map<String, Value> payload = payloads.get(idx);
    String description = payload.get("description").getStringValue();

    PointStruct point =
        PointStruct.newBuilder()
            .setId(id((long) idx))
            .setVectors(
                vectors(
                    vector(
                        Document.newBuilder()
                            .setText(description)
                            .setModel(EMBEDDING_MODEL)
                            .build())))
            .putAllPayload(payload)
            .build();

    points.add(point);
}

client.upsertAsync(COLLECTION_NAME, points).get();
```

```csharp
string EMBEDDING_MODEL = "sentence-transformers/all-minilm-l6-v2";

var points = new List<PointStruct>();

for (ulong idx = 0; idx < (ulong)payloads.Count; idx++)
{
	var payload = payloads[(int)idx];
	string description = payload["description"].StringValue;

	var point = new PointStruct
	{
		Id = idx,
		Vectors = new Document
		{
			Text = description,
			Model = EMBEDDING_MODEL
		},
		Payload = { payload }
	};

	points.Add(point);
}

await client.UpsertAsync(
	collectionName: COLLECTION_NAME,
	points: points
);
```

```go
embeddingModel := "sentence-transformers/all-minilm-l6-v2"

points := make([]*qdrant.PointStruct, len(documents))
for idx, doc := range documents {
	points[idx] = &qdrant.PointStruct{
		Id: qdrant.NewIDNum(uint64(idx)),
		Vectors: qdrant.NewVectorsDocument(&qdrant.Document{
			Text:  doc["description"].(string),
			Model: embeddingModel,
		}),
		Payload: qdrant.NewValueMap(doc),
	}
}

client.Upsert(context.Background(), &qdrant.UpsertPoints{
	CollectionName: collectionName,
	Points:         points,
})
```


This code tells Qdrant Cloud to use the `sentence-transformers/all-minilm-l6-v2` embedding model to generate vector embeddings from the book descriptions. This is one of the free models available on Qdrant Cloud. For a list of the available free and paid models, refer to the Inference tab of the Cluster Detail page in the Qdrant Cloud Console.

## 5. Query the Engine

Now that the data is stored in Qdrant, you can query it and receive semantically relevant results.


```python
hits = client.query_points(
    collection_name=COLLECTION_NAME,
    query=models.Document(
        text="alien invasion",
        model=EMBEDDING_MODEL
    ),
    limit=3,
).points

for hit in hits:
    print(hit.payload, "score:", hit.score)
```

```typescript
const queryResult = await client.query(collectionName, {
    query: {
        text: "alien invasion",
        model: embeddingModel,
    },
    limit: 3,
});

for (const hit of queryResult.points) {
    console.log(hit.payload, "score:", hit.score);
}
```

```rust
let query_result = client
    .query(
        QueryPointsBuilder::new(collection_name)
            .query(Query::new_nearest(Document::new(
                "alien invasion",
                embedding_model,
            )))
            .limit(3)
            .with_payload(true),
    )
    .await?;

for hit in query_result.result {
    println!("{:?} score: {}", hit.payload, hit.score);
}
```

```java
QueryPoints request =
    QueryPoints.newBuilder()
        .setCollectionName(COLLECTION_NAME)
        .setQuery(
            nearest(
                Document.newBuilder()
                    .setText("alien invasion")
                    .setModel(EMBEDDING_MODEL)
                    .build()))
        .setLimit(3)
        .build();

var hits = client.queryAsync(request).get();

for (var hit : hits) {
    System.out.println(hit.getPayloadMap() + " score: " + hit.getScore());
}
```

```csharp
var hits = await client.QueryAsync(
	collectionName: COLLECTION_NAME,
	query: new Document
	{
		Text = "alien invasion",
		Model = EMBEDDING_MODEL
	},
	limit: 3
);

foreach (var hit in hits)
{
	Console.WriteLine($"{hit.Payload} score: {hit.Score}");
}
```

```go
queryResult, err := client.Query(context.Background(), &qdrant.QueryPoints{
	CollectionName: collectionName,
	Query: qdrant.NewQueryDocument(&qdrant.Document{
		Text:  "alien invasion",
		Model: embeddingModel,
	}),
	Limit: qdrant.PtrOf(uint64(3)),
})

for _, hit := range queryResult {
	fmt.Println(hit.Payload, "score:", hit.Score)
}
```


This query uses the same embedding model to generate a vector for the query "alien invasion". The search engine then looks for the three most similar vectors in the collection and returns their payloads and similarity scores.

**Response:**

The search engine returns the three most relevant books related to an alien invasion. Each is assigned a score indicating its similarity to the query:

```text
{'name': 'The War of the Worlds', 'description': 'A Martian invasion of Earth throws humanity into chaos.', 'author': 'H.G. Wells', 'year': 1898} score: 0.570093257022374
{'name': "The Hitchhiker's Guide to the Galaxy", 'description': 'A comedic science fiction series following the misadventures of an unwitting human and his alien friend.', 'author': 'Douglas Adams', 'year': 1979} score: 0.5040468703143637
{'name': 'The Three-Body Problem', 'description': 'Humans encounter an alien civilization that lives in a dying system.', 'author': 'Liu Cixin', 'year': 2008} score: 0.45902943411768216
```

### Narrow down the Query

How about the most recent book from the early 2000s? Qdrant allows you to narrow down query results by applying a [filter](/documentation/search/filtering/index.md). To filter for books published after the year 2000, you can filter on the `year` field in the payload.

Before filtering on a payload field, create a [payload index](/documentation/manage-data/indexing/index.md#payload-index) for that field:


```python
client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="year",
    field_schema=models.PayloadSchemaType.INTEGER,
)
```

```typescript
await client.createPayloadIndex(collectionName, {
    field_name: "year",
    field_schema: "integer",
});
```

```rust
client
    .create_field_index(
        CreateFieldIndexCollectionBuilder::new(collection_name, "year", FieldType::Integer)
            .wait(true),
    )
    .await?;
```

```java
client
    .createPayloadIndexAsync(
        COLLECTION_NAME,
        "year",
        PayloadSchemaType.Integer,
        null,
        true,
        null,
        null)
    .get();
```

```csharp
await client.CreatePayloadIndexAsync(
	collectionName: COLLECTION_NAME,
	fieldName: "year",
	schemaType: PayloadSchemaType.Integer
);
```

```go
client.CreateFieldIndex(context.Background(), &qdrant.CreateFieldIndexCollection{
	CollectionName: collectionName,
	FieldName:      "year",
	FieldType:      qdrant.FieldType_FieldTypeInteger.Enum(),
})
```


In a production environment, create payload indexes before uploading data to get the maximum benefit from indexing.

Now you can apply a filter to the query:


```python
hits = client.query_points(
    collection_name=COLLECTION_NAME,
    query=models.Document(
        text="alien invasion",
        model=EMBEDDING_MODEL
    ),
    query_filter=models.Filter(
        must=[models.FieldCondition(key="year", range=models.Range(gte=2000))]
    ),
    limit=1,
).points

for hit in hits:
    print(hit.payload, "score:", hit.score)
```

```typescript
const queryResultFiltered = await client.query(collectionName, {
    query: {
        text: "alien invasion",
        model: embeddingModel,
    },
    filter: {
        must: [
            {
                key: "year",
                range: {
                    gte: 2000,
                },
            },
        ],
    },
    limit: 1,
});

for (const hit of queryResultFiltered.points) {
    console.log(hit.payload, "score:", hit.score);
}
```

```rust
let query_result_filtered = client
    .query(
        QueryPointsBuilder::new(collection_name)
            .query(Query::new_nearest(Document::new(
                "alien invasion",
                embedding_model,
            )))
            .filter(Filter::must([Condition::range(
                "year",
                Range {
                    gte: Some(2000.0),
                    ..Default::default()
                },
            )]))
            .limit(1)
            .with_payload(true),
    )
    .await?;

for hit in query_result_filtered.result {
    println!("{:?} score: {}", hit.payload, hit.score);
}
```

```java
QueryPoints filteredRequest =
    QueryPoints.newBuilder()
        .setCollectionName(COLLECTION_NAME)
        .setQuery(
            nearest(
                Document.newBuilder()
                    .setText("alien invasion")
                    .setModel(EMBEDDING_MODEL)
                    .build()))
        .setFilter(
            Filter.newBuilder()
                .addMust(range("year", Range.newBuilder().setGte(2000.0).build()))
                .build())
        .setLimit(1)
        .build();

var filteredHits = client.queryAsync(filteredRequest).get();

for (var hit : filteredHits) {
    System.out.println(hit.getPayloadMap() + " score: " + hit.getScore());
}
```

```csharp
var filteredHits = await client.QueryAsync(
	collectionName: COLLECTION_NAME,
	query: new Document
	{
		Text = "alien invasion",
		Model = EMBEDDING_MODEL
	},
	filter: new Filter
	{
		Must = { Range("year", new Qdrant.Client.Grpc.Range { Gte = 2000.0 }) }
	},
	limit: 1
);

foreach (var hit in filteredHits)
{
	Console.WriteLine($"{hit.Payload} score: {hit.Score}");
}
```

```go
queryResultFiltered, err := client.Query(context.Background(), &qdrant.QueryPoints{
	CollectionName: collectionName,
	Query: qdrant.NewQueryDocument(&qdrant.Document{
		Text:  "alien invasion",
		Model: embeddingModel,
	}),
	Filter: &qdrant.Filter{
		Must: []*qdrant.Condition{
			qdrant.NewRange("year", &qdrant.Range{
				Gte: qdrant.PtrOf(2000.0),
			}),
		},
	},
	Limit: qdrant.PtrOf(uint64(1)),
})

for _, hit := range queryResultFiltered {
	fmt.Println(hit.Payload, "score:", hit.Score)
}
```


**Response:**

The results have been narrowed down to one result from 2008:

```text
{'name': 'The Three-Body Problem', 'description': 'Humans encounter an alien civilization that lives in a dying system.', 'author': 'Liu Cixin', 'year': 2008} score: 0.45902943411768216
```

## Next Steps

Congratulations, you have just created your very first search engine! Trust us, the rest of Qdrant is not that complicated, either. For your next tutorial, try [building your own hybrid search service](/documentation/tutorials-basics/cloud-inference-hybrid-search/index.md) or take the free [Qdrant Essentials course](/course/essentials/index.md).
