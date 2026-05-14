# Recipe Recommendation API

## Overview

This project implements a GenAI-powered recipe recommendation API using:

- FastAPI
- PostgreSQL + pgvector
- OpenAI GPT-4o
- Retrieval Augmented Generation (RAG)

The system retrieves similar recipes from the dataset using vector similarity search and uses GPT-4o to generate a final recipe recommendation.

---

# Architecture

```text
Client
  |
FastAPI
  |
RecipeService
  |
RecipeRepository
  |
Postgres + pgvector
  |
OpenAI GPT-4o
```

For simplicity and readability, embeddings are generated sequentially.
Batch embedding generation would significantly improve ingestion throughput in production.