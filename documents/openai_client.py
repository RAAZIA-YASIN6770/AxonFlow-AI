"""
OpenAI Client for AxonFlow AI
Handles embeddings and chat completions
"""

from openai import OpenAI
from typing import List, Dict, Optional
from django.conf import settings


class OpenAIClient:
    """Client for OpenAI API operations"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.api_key = settings.OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError("OpenAI API key must be set in settings")
        
        self.client = OpenAI(api_key=self.api_key)
        self.embedding_model = "text-embedding-ada-002"
        self.chat_model = "gpt-3.5-turbo"
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding vector for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (list of floats)
        """
        try:
            # Truncate text if too long (max 8191 tokens for ada-002)
            if len(text) > 8000:
                text = text[:8000]
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            raise Exception(f"Error creating embedding: {str(e)}")
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Process in batches to avoid rate limits
            batch_size = 20
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Truncate each text
                batch = [text[:8000] if len(text) > 8000 else text for text in batch]
                
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            raise Exception(f"Error creating batch embeddings: {str(e)}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ):
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            stream: Whether to stream response
            
        Returns:
            Response text or stream object
        """
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response
            else:
                return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error in chat completion: {str(e)}")
    
    def generate_rag_response(
        self,
        query: str,
        context_chunks: List[str],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate RAG response using retrieved context
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant text chunks
            conversation_history: Previous messages in conversation
            
        Returns:
            AI-generated response
        """
        try:
            # Build context from chunks
            context = "\n\n".join([
                f"[Context {i+1}]: {chunk}" 
                for i, chunk in enumerate(context_chunks)
            ])
            
            # Create system prompt
            system_prompt = f"""You are AxonFlow AI, an intelligent document assistant. 
You help users understand and extract information from their uploaded documents.

Use the following context from the user's documents to answer their question.
If the answer is not in the context, say so clearly.
Always cite which context section you used for your answer.

Context:
{context}
"""
            
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Generate response
            response = self.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response
            
        except Exception as e:
            raise Exception(f"Error generating RAG response: {str(e)}")
