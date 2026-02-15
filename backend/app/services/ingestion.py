import pypdf
import io
import hashlib
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.ai import LegalChunk

class IngestionPipeline:
    
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        # Simple token approximation (4 chars = 1 token)
        # Better to use tiktoken, but let's do char based split for simplicity first or use simple logic
        # Implementation of sliding window
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += 1 # Rough token count
            
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                # Overlap: keep last 'overlap' words
                current_chunk = current_chunk[-overlap:]
                current_length = len(current_chunk)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    @staticmethod
    def process_document(
        db: Session, 
        file_bytes: bytes, 
        metadata: Dict, 
        rag_engine
    ) -> int:
        # 1. Extract
        full_text = IngestionPipeline.extract_text_from_pdf(file_bytes)
        
        # 2. Chunk
        text_chunks = IngestionPipeline.chunk_text(full_text)
        
        count = 0
        for i, chunk_text in enumerate(text_chunks):
            # 3. Embed (using passed engine to reuse client)
            # Make sure this is async context or handle appropriately. 
            # Ideally this method should be async.
            pass 
        return len(text_chunks)

    # Async version
    @staticmethod
    async def process_document_async(
        db, 
        file_bytes: bytes, 
        metadata: Dict, 
        rag_engine
    ) -> int:
        full_text = IngestionPipeline.extract_text_from_pdf(file_bytes)
        text_chunks = IngestionPipeline.chunk_text(full_text)
        
        for i, chunk_text in enumerate(text_chunks):
            embedding = await rag_engine.get_embedding(chunk_text)
            
            chunk_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
            
            # Upsert logic could be here, for now just insert
            db_chunk = LegalChunk(
                source_type=metadata.get('source_type', 'ley'),
                chunk_index=i,
                contenido_texto=chunk_text,
                vector_embedding=embedding,
                metadata_json=metadata,
                hash_contenido=chunk_hash
            )
            db.add(db_chunk)
            
        await db.commit()
        return len(text_chunks)
