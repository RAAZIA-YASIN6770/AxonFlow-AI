"""
PDF Processing Utilities for AxonFlow AI
Handles PDF text extraction and chunking for RAG system
"""

from pypdf import PdfReader
from typing import List, Dict
import re


class PDFProcessor:
    """Process PDF files for RAG system"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize PDF processor
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract all text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as string
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'"]+', '', text)
        
        return text.strip()
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            metadata: Additional metadata to include with each chunk
            
        Returns:
            List of dictionaries containing chunk text and metadata
        """
        chunks = []
        text_length = len(text)
        start = 0
        chunk_index = 0
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # If not at the end, try to break at sentence boundary
            if end < text_length:
                # Look for sentence ending punctuation
                sentence_end = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end)
                )
                
                if sentence_end > start:
                    end = sentence_end + 1
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_data = {
                    'text': chunk_text,
                    'chunk_index': chunk_index,
                    'start_char': start,
                    'end_char': end,
                }
                
                # Add additional metadata if provided
                if metadata:
                    chunk_data.update(metadata)
                
                chunks.append(chunk_data)
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start <= 0:
                start = end
        
        return chunks
    
    def process_pdf(self, pdf_path: str, document_id: int, document_title: str) -> List[Dict]:
        """
        Complete PDF processing pipeline
        
        Args:
            pdf_path: Path to PDF file
            document_id: Database ID of document
            document_title: Title of document
            
        Returns:
            List of processed chunks with metadata
        """
        # Extract text
        raw_text = self.extract_text(pdf_path)
        
        # Clean text
        cleaned_text = self.clean_text(raw_text)
        
        # Create metadata
        metadata = {
            'document_id': document_id,
            'document_title': document_title,
        }
        
        # Chunk text
        chunks = self.chunk_text(cleaned_text, metadata)
        
        return chunks


def extract_page_numbers(pdf_path: str) -> int:
    """
    Get total number of pages in PDF
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Number of pages
    """
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
