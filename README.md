## Neo4j Graph Database with Vector Search & LLM Integration

A comprehensive project that creates a Neo4j knowledge graph from job titles and skills data, generates vector embeddings for semantic search, and integrates with OpenAI LLMs for natural language querying.

### Overview

This project demonstrates:
- **Graph Database**: Building a knowledge graph with Neo4j (Titles → Skills relationships)
- **Vector Embeddings**: Generating 384-dimensional embeddings for semantic search
- **LLM Integration**: Converting natural language to Cypher queries via LangChain
- **Semantic Search**: Using vector similarity for skill discovery

### Architecture

```
Data Sources (CSV)
    ↓
create_graph.py → Neo4j Database
    ↓
create_embeddings.py → embeddings.csv
    ↓
create_search_index.py → Vector Index (384-dim, cosine similarity)
    ↓
    ├─ neo4j_qa.py (LLM → Cypher)
    └─ vector_search.py (Semantic Search)
```

### Technologies

- **Neo4j** (5.15.0): Graph database platform
- **LangChain** (0.1.0): LLM framework & chains
- **OpenAI**: LLM and embedding models
- **SentenceTransformers**: Local embedding model (all-MiniLM-L6-v2)
- **Pandas**: Data manipulation

### Setup

#### 1. Clone and Install

```bash
# Create conda environment
conda create --name neo4j-env python=3.9
conda activate neo4j-env

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Environment

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=sk-your-key  # For LLM features
```

### Pipeline Execution

#### Step 1: Create Graph Database

```python
# Edit src/main.py and uncomment 'create_graph'
python src/main.py
```

This:
- Loads job titles from CSV
- Loads skill descriptions and categories
- Creates `Title` and `Skill` nodes
- Creates `REQUIRES` relationships
- Applies category labels (Certification, SpecializedSkill)

#### Step 2: Generate Embeddings

```python
# Uncomment 'create_embeddings' in src/main.py
python src/main.py
```

This:
- Queries all skills with descriptions from Neo4j
- Generates 384-dimensional embeddings using SentenceTransformer
- Saves embeddings to `data/embeddings.csv`

#### Step 3: Create Vector Index

```python
# Uncomment 'create_search_index' in src/main.py
python src/main.py
```

This:
- Loads embeddings into Neo4j
- Creates vector index with cosine similarity
- Enables semantic search capabilities

#### Step 4: Query with Natural Language

```python
# Uncomment 'neo4j_qa' in src/main.py
python src/main.py
```

This enables schema-based Q&A:
- `"What skills are required for a Data Scientist?"`
- `"What titles require Python?"`
- `"List all certification skills"`

#### Step 5: Semantic Search

```python
# Uncomment 'vector_search' in src/main.py
python src/main.py
```

This enables semantic similarity search:
- `"Find skills related to machine learning and AI"`
- `"What skills are about cloud computing?"`

### Project Structure

```
.
├── README.md                      # This file
├── FILE_EXPLANATIONS.md           # Detailed file documentation
├── requirements.txt               # Python dependencies
├── .env.example                   # Configuration template
├── cypher_cmds.cyp                # Manual Cypher queries
├── data/
│   ├── embeddings.csv             # Generated embeddings
│   ├── skills_details.csv         # Skill descriptions & categories
│   └── titles_and_skills.csv      # Job titles & skill mappings
└── src/
    ├── main.py                    # Pipeline orchestrator
    ├── utils.py                   # Shared utilities & Neo4j helpers
    ├── create_graph.py            # Build knowledge graph
    ├── create_embeddings.py       # Generate embeddings
    ├── create_search_index.py     # Create vector index
    ├── neo4j_qa.py                # Schema-based QA
    └── vector_search.py           # Semantic search
```

### Key Features

#### Graph Structure

```
Title [name]
  ├─[:REQUIRES]─> Skill [name, description, id]
  │                  └─:Certification (label)
  │                  └─:SpecializedSkill (label)
```

#### Vector Search

- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Similarity**: Cosine distance
- **Speed**: Fast, no API calls required
- **Index**: `skillDescription`

#### LLM Integration

- **Model**: GPT-3.5-turbo
- **Framework**: LangChain
- **Approach**: Natural language → Cypher translation
- **Safety**: Input validation & parameter filtering

### Data Files

#### titles_and_skills.csv
- **Columns**: Title, Skills (pipe-separated), additional metadata
- **Source**: Job market data
- **Purpose**: Create Title nodes and REQUIRES relationships

#### skills_details.csv
- **Columns**: ID, Skill, Description, Category
- **Categories**: Certification, SpecializedSkill, Technical, Soft Skills
- **Purpose**: Create Skill nodes with descriptions

#### embeddings.csv (Generated)
- **Columns**: Skill, Embedding (JSON array)
- **Dimensions**: 384
- **Source**: SentenceTransformer embeddings
- **Purpose**: Vector search index

### Usage Examples

#### Python API

```python
# Create graph
import create_graph
create_graph.go()

# Query with natural language
import neo4j_qa
neo4j_qa.go()

# Semantic search
import vector_search
vector_search.go()
```

#### Cypher Queries

See `cypher_cmds.cyp` for manual query examples:

```cypher
# Find skills for a specific title
MATCH (t:Title)-[:REQUIRES]->(s:Skill) 
WHERE t.name = 'Data Scientist' 
RETURN s.name, s.description;

# Find titles that require a specific skill
MATCH (t:Title)-[:REQUIRES]->(s:Skill) 
WHERE s.name = 'Python' 
RETURN DISTINCT t.name;

# List all certification skills
MATCH (s:Skill:Certification) 
RETURN s.name;
```

### Troubleshooting

#### Connection Failed
```
Error: Failed to initialize Neo4j driver
Solution: 
- Verify NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
- Ensure database is running and accessible
- Check firewall/network settings
```

#### Missing API Key
```
Error: Missing OpenAI API key
Solution:
- Add OPENAI_API_KEY to .env
- Get key from https://platform.openai.com/api-keys
- Only needed for LLM features (neo4j_qa, vector_search)
```

#### Index Already Exists
```
Warning: Index already exists
Solution: This is normal - existing index will be reused
```

#### No Embeddings Found
```
Error: No embeddings were added
Solution:
- Ensure create_graph.py completed successfully
- Check embeddings.csv exists and is valid
- Verify skills have descriptions
```

### Performance Tips

1. **Graph Creation**: ~5-10 minutes for large datasets
2. **Embeddings**: ~2-5 minutes (CPU-based, parallelize if possible)
3. **Vector Index**: ~1-2 minutes
4. **Queries**: <1 second for Cypher, <2 seconds for semantic search

### Security Considerations

- Store `.env` securely, never commit to version control
- Rotate API keys regularly
- Use strong Neo4j passwords
- Restrict database access to trusted networks
- Validate user inputs before querying

### Contributing

Feel free to extend this project:
- Add more skill categories
- Implement custom embedding models
- Enhance LLM prompts for better Cypher generation
- Add graph visualization
- Implement fine-tuned models

### Further Reading

- [Neo4j Documentation](https://neo4j.com/docs/)
- [LangChain Guides](https://docs.langchain.com/)
- [OpenAI API Docs](https://platform.openai.com/docs/)
- [Graph Database Design Patterns](https://neo4j.com/docs/graph-data-science/current/)

### License

This project is provided as-is for educational purposes.

---

For detailed file documentation, see [FILE_EXPLANATIONS.md](FILE_EXPLANATIONS.md)

