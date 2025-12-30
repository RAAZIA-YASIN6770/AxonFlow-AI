"""
Document Processing Tasks for AxonFlow AI
Handles async processing of uploaded documents
"""

from .models import Document
from .utils import PDFProcessor
from .openai_client import OpenAIClient
from .pinecone_client import PineconeClient
import logging

logger = logging.getLogger(__name__)


def process_document(document_id: int):
    """
    Process uploaded document: extract text, chunk, embed, and store in Pinecone
    
    Args:
        document_id: ID of document to process
    """
    try:
        # Get document
        document = Document.objects.get(id=document_id)
        
        # Update status to processing
        document.processing_status = Document.Status.PROCESSING
        document.save()
        
        logger.info(f"Starting processing for document {document_id}: {document.title}")
        
        # Initialize processors
        pdf_processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
        openai_client = OpenAIClient()
        pinecone_client = PineconeClient()
        
        # Ensure Pinecone index exists
        pinecone_client.create_index_if_not_exists()
        
        # Process PDF
        logger.info(f"Extracting and chunking PDF: {document.file.path}")
        chunks = pdf_processor.process_pdf(
            pdf_path=document.file.path,
            document_id=document.id,
            document_title=document.title
        )
        
        logger.info(f"Created {len(chunks)} chunks from document")
        
        # Create embeddings for all chunks
        logger.info("Generating embeddings...")
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = openai_client.create_embeddings_batch(chunk_texts)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Prepare vectors for Pinecone
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector = {
                'id': f"doc_{document.id}_chunk_{i}",
                'values': embedding,
                'metadata': {
                    'document_id': document.id,
                    'document_title': document.title,
                    'user_id': document.user.id,
                    'chunk_index': chunk['chunk_index'],
                    'text': chunk['text'],
                    'start_char': chunk['start_char'],
                    'end_char': chunk['end_char'],
                }
            }
            vectors.append(vector)
        
        # Upload to Pinecone
        logger.info("Uploading vectors to Pinecone...")
        pinecone_client.upsert_vectors(vectors)
        
        # Update document status to completed
        document.processing_status = Document.Status.COMPLETED
        document.error_message = None
        document.save()
        
        logger.info(f"Successfully processed document {document_id}")
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        
        # Update document status to failed
        try:
            document = Document.objects.get(id=document_id)
            document.processing_status = Document.Status.FAILED
            document.error_message = str(e)
            document.save()
        except:
            pass


def delete_document_vectors(document_id: int):
    """
    Delete all vectors associated with a document from Pinecone
    
    Args:
        document_id: ID of document whose vectors to delete
    """
    try:
        pinecone_client = PineconeClient()
        pinecone_client.delete_by_document_id(document_id)
        logger.info(f"Deleted vectors for document {document_id}")
        
    except Exception as e:
        logger.error(f"Error deleting vectors for document {document_id}: {str(e)}")


def reprocess_document(document_id: int):
    """
    Reprocess a document (delete old vectors and process again)
    
    Args:
        document_id: ID of document to reprocess
    """
    try:
        # Delete old vectors
        delete_document_vectors(document_id)
        
        # Process again
        process_document(document_id)
        
    except Exception as e:
        logger.error(f"Error reprocessing document {document_id}: {str(e)}")
