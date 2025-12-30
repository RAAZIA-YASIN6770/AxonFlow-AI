"""
Pinecone Vector Database Client for AxonFlow AI
Handles vector storage and semantic search
"""

from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Optional
from django.conf import settings
import time


class PineconeClient:
    """Client for Pinecone vector database operations"""
    
    def __init__(self):
        """Initialize Pinecone client"""
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENV
        
        if not self.api_key or not self.environment:
            raise ValueError("Pinecone API key and environment must be set in settings")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index_name = "axonflow-documents"
        self.dimension = 1536  # OpenAI ada-002 embedding dimension
        
    def create_index_if_not_exists(self):
        """Create Pinecone index if it doesn't exist"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            
            if self.index_name not in [idx.name for idx in existing_indexes]:
                # Create new index
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
                
                print(f"Created Pinecone index: {self.index_name}")
            else:
                print(f"Pinecone index already exists: {self.index_name}")
                
        except Exception as e:
            raise Exception(f"Error creating Pinecone index: {str(e)}")
    
    def get_index(self):
        """Get Pinecone index instance"""
        try:
            return self.pc.Index(self.index_name)
        except Exception as e:
            raise Exception(f"Error getting Pinecone index: {str(e)}")
    
    def upsert_vectors(self, vectors: List[Dict]):
        """
        Upload vectors to Pinecone
        
        Args:
            vectors: List of dictionaries with 'id', 'values', and 'metadata'
        """
        try:
            index = self.get_index()
            
            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                index.upsert(vectors=batch)
            
            print(f"Upserted {len(vectors)} vectors to Pinecone")
            
        except Exception as e:
            raise Exception(f"Error upserting vectors: {str(e)}")
    
    def query_vectors(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Query Pinecone for similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of matching results with metadata
        """
        try:
            index = self.get_index()
            
            # Query index
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            matches = []
            for match in results.matches:
                matches.append({
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata
                })
            
            return matches
            
        except Exception as e:
            raise Exception(f"Error querying vectors: {str(e)}")
    
    def delete_by_document_id(self, document_id: int):
        """
        Delete all vectors for a specific document
        
        Args:
            document_id: Document ID to delete
        """
        try:
            index = self.get_index()
            
            # Delete by metadata filter
            index.delete(
                filter={"document_id": {"$eq": document_id}}
            )
            
            print(f"Deleted vectors for document_id: {document_id}")
            
        except Exception as e:
            raise Exception(f"Error deleting vectors: {str(e)}")
    
    def delete_by_user_id(self, user_id: int):
        """
        Delete all vectors for a specific user
        
        Args:
            user_id: User ID to delete
        """
        try:
            index = self.get_index()
            
            # Delete by metadata filter
            index.delete(
                filter={"user_id": {"$eq": user_id}}
            )
            
            print(f"Deleted vectors for user_id: {user_id}")
            
        except Exception as e:
            raise Exception(f"Error deleting vectors: {str(e)}")
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        try:
            index = self.get_index()
            stats = index.describe_index_stats()
            return stats
        except Exception as e:
            raise Exception(f"Error getting stats: {str(e)}")
