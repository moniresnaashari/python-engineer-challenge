# Recipe Recommendation API

## Overview

This project implements a GenAI-powered recipe recommendation API using FastAPI, PostgreSQL with pgvector, OpenAI GPT-4o, and Retrieval Augmented Generation (RAG). The system retrieves similar recipes from a dataset using vector similarity search and uses GPT-4o to generate personalized recipe recommendations.

## How to Run the Application

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- OpenAI API key

### Setup Instructions

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Start the PostgreSQL database:**
   ```bash
   docker-compose up -d
   ```

3. **Create environment variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=postgresql+asyncpg://pipeline:pipeline-pass@localhost:5432/challenge
   ```

4. **Start the application:**
   ```bash
   uv run uvicorn src.whats_for_dinner.main:app --reload
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## Solution Architecture

The system uses a layered architecture with clear separation of concerns:

```text
Client Request
    ↓
FastAPI (API Layer)
    ↓
RecipeService (Business Logic)
    ↓
RAG Pipeline (Haystack 2.x)
    ↓
RecipeRepository (Data Access)
    ↓
PostgreSQL + pgvector (Storage)
    ↓
OpenAI GPT-4o (Embeddings & Generation)
```

### Key Components

- **API Layer**: FastAPI endpoints for recipe recommendations and health checks
- **Business Logic**: Recipe service orchestrating the recommendation process
- **RAG Pipeline**: Haystack 2.x pipeline for embedding generation and vector similarity search
- **Data Access**: Repository pattern for database operations
- **Storage**: PostgreSQL for recipe text, pgvector for embeddings

### Data Flow

1. User submits ingredients via POST `/recommend_recipe`
2. RecipeService loads recipe data into Haystack document store
3. System generates embeddings for user ingredients
4. Vector similarity search finds 3 most similar recipes
5. GPT-4o generates personalized recipe using RAG context
6. Formatted recipe returned as response

## Assumptions Made

### Data Format
- Recipe files follow format: Title, "Ingredients:", ingredients list, "Instructions:", steps
- Text files are UTF-8 encoded
- Recipe dataset located in `data/recipes/` directory

### Performance & Scaling
- Recipe text stored in PostgreSQL (main database)
- Embeddings generated on-demand via Haystack pipeline
- Vector similarity limited to top 3 results for context control
- Single database commit per ingestion batch

### External Dependencies
- Active OpenAI API key with sufficient credits required
- Network connectivity for OpenAI API calls
- PostgreSQL database with pgvector extension

### Business Logic
- Re-ingestion skipped if recipes already exist
- Recipe generation temperature set to 0.7 for creativity
- Uses text-embedding-3-small (1536 dimensions)
- GPT-4o model for high-quality recipe generation

## API Usage Examples

### Recipe Recommendation

**Request:**
```bash
curl -X POST "http://localhost:8000/recommend_recipe" \
     -H "Content-Type: application/json" \
     -d '{"ingredients": "chicken, rice, vegetables"}'
```

**Response:**
```json
{
  "recipe": "# Chicken and Vegetable Rice Bowl\n\n## Ingredients\n- 2 chicken breasts...",
  "source_recipes": ["Chicken Fried Rice", "Vegetable Stir Fry", "Rice Pilaf"]
}
```

### With Optional Image Analysis

**Request:**
```bash
curl -X POST "http://localhost:8000/recommend_recipe" \
     -H "Content-Type: application/json" \
     -d '{
       "ingredients": "tomatoes, basil, cheese",
       "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
     }'
```

### Health Check

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Interactive Documentation

Visit `http://localhost:8000/docs` for Swagger UI or `http://localhost:8000/redoc` for ReDoc documentation.

## Development Commands

```bash
# Run tests
uv run pytest