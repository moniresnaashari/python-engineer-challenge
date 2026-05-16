from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder, OpenAIDocumentEmbedder
from haystack.components.generators import OpenAIGenerator  
from haystack.components.builders import PromptBuilder
from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore
from haystack_integrations.components.retrievers.pgvector import PgvectorEmbeddingRetriever
from haystack import Document
from haystack.utils import Secret
from typing import List

from whats_for_dinner.core.config import settings
from whats_for_dinner.models.recipe import Recipe
from whats_for_dinner.domain.exceptions import RecipeGenerationError


class RecipeRAGPipeline:
    """Haystack 2.x RAG Pipeline for recipe recommendations."""
    
    def __init__(self):
        # Use PostgreSQL with pgvector for document storage
        # Convert SQLAlchemy-style URL to pure PostgreSQL connection string
        db_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
        self.document_store = PgvectorDocumentStore(
            connection_string=Secret.from_token(db_url),
            embedding_dimension=1536,  # OpenAI text-embedding-3-small dimension
            vector_function="cosine_similarity",
            recreate_table=False,  # Don't recreate, use existing data if available
            table_name="recipe_documents"
        )
        self.pipeline = self._build_pipeline()
        self._recipes_loaded = False
    
    def _build_pipeline(self) -> Pipeline:
        """Build the RAG pipeline with Haystack components."""
        
        # Create components
        text_embedder = OpenAITextEmbedder(
            api_key=Secret.from_token(settings.openai_api_key),
            model="text-embedding-3-small"
        )
        
        retriever = PgvectorEmbeddingRetriever(
            document_store=self.document_store,
            top_k=3
        )
        
        prompt_builder = PromptBuilder(
            template="""
Create a recipe recommendation based on the user's ingredients.

User ingredients:
{{ ingredients }}

Reference recipes:
{% for document in documents %}
Recipe: {{ document.meta.title }}

Ingredients: {{ document.meta.ingredients }}

Instructions: {{ document.content }}

{% endfor %}

Requirements:
- Return Markdown formatted output
- Prefer ingredients explicitly provided by the user
- You may adapt ideas from the reference recipes
- If additional ingredients are needed, clearly mark them as optional
- Keep instructions concise and practical
- Include:
  - recipe title
  - ingredients
  - step-by-step instructions
- Do not invent unrealistic ingredients
""",
            required_variables=["ingredients", "documents"]
        )
        
        generator = OpenAIGenerator(
            api_key=Secret.from_token(settings.openai_api_key),
            model="gpt-4o",
            generation_kwargs={
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )
        
        # Build pipeline
        pipeline = Pipeline()
        pipeline.add_component("text_embedder", text_embedder)
        pipeline.add_component("retriever", retriever)
        pipeline.add_component("prompt_builder", prompt_builder)
        pipeline.add_component("llm", generator)
        
        # Connect components
        pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        pipeline.connect("retriever.documents", "prompt_builder.documents")
        pipeline.connect("prompt_builder.prompt", "llm.prompt")
        
        return pipeline
    
    async def load_recipes(self, recipes: List[Recipe]) -> None:
        """Load recipes into the document store with embeddings."""
        if self._recipes_loaded or self.document_store.count_documents() > 0:
            self._recipes_loaded = True
            return
            
        documents = []
        for recipe in recipes:
            # Use instructions as content, store title/ingredients in metadata
            doc = Document(
                content=recipe.instructions,
                meta={
                    "title": recipe.title,
                    "ingredients": recipe.ingredients,
                    "recipe_id": recipe.id
                }
            )
            documents.append(doc)
        
        # Embed documents
        embedder = OpenAIDocumentEmbedder(
            api_key=Secret.from_token(settings.openai_api_key),
            model="text-embedding-3-small"
        )
        
        # Process documents to add embeddings
        embedded_docs = embedder.run(documents=documents)
        
        # Write to document store
        self.document_store.write_documents(embedded_docs["documents"])
        self._recipes_loaded = True
    
    def are_recipes_loaded(self) -> bool:
        """Check if recipes are loaded in the pipeline."""
        return self._recipes_loaded or self.document_store.count_documents() > 0

    async def recommend_recipe(self, ingredients: str) -> str:
        """Generate recipe recommendation using the RAG pipeline."""
        
        if not ingredients.strip():
            raise RecipeGenerationError("Ingredients cannot be empty")
            
        try:
            result = self.pipeline.run({
                "text_embedder": {"text": ingredients},
                "prompt_builder": {"ingredients": ingredients}
            })
            
            # Extract the generated response
            if "llm" in result and "replies" in result["llm"] and result["llm"]["replies"]:
                response = result["llm"]["replies"][0]
                if not response or not response.strip():
                    raise RecipeGenerationError("Generated response is empty")
                return response
            else:
                raise RecipeGenerationError("No response generated by pipeline")
        except Exception as e:
            if isinstance(e, RecipeGenerationError):
                raise
            raise RecipeGenerationError(f"Pipeline execution failed: {str(e)}") from e


# Global pipeline instance
_pipeline_instance = None

def get_rag_pipeline() -> RecipeRAGPipeline:
    """Get or create the global RAG pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RecipeRAGPipeline()
    return _pipeline_instance