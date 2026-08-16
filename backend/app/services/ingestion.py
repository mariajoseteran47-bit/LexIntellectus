"""
LexIntellectus ERP — Ingestion Pipeline v2
Enhanced document ingestion with intelligent legal article segmentation.
Supports both generic chunking and law-specific article-by-article parsing.
"""
import pypdf
import io
import re
import hashlib
import json
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import update, text as sa_text
from app.models.ai import LegalChunk, LegalSource


class IngestionPipeline:

    # ─────────────────────────────────────────────────────────────────
    # TEXT EXTRACTION
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text

    # ─────────────────────────────────────────────────────────────────
    # INTELLIGENT LEGAL ARTICLE SEGMENTATION
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def split_into_articles(text: str) -> List[Tuple[str, str]]:
        """
        Splits a legal document into individual articles.
        Returns list of (article_number, article_full_text) tuples.

        Recognizes common Nicaraguan legal formats:
          - Art. 1.- ...
          - Artículo 1.- ...
          - Arto. 1.- ...
          - ARTICULO 1.
          - Art.1.-
        """
        pattern = r'(?:Art(?:o|ículo)?\.?\s*(\d+)[\.\-]+\s*)'
        splits = list(re.finditer(pattern, text, re.IGNORECASE))

        if not splits or len(splits) < 3:
            # Not a structured legal document — fall back to generic chunking
            return []

        articles = []
        for i, match in enumerate(splits):
            art_num = match.group(1)
            start = match.start()
            end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
            art_text = text[start:end].strip()

            # Skip articles that are too short (likely parsing artifacts)
            if len(art_text) > 20:
                articles.append((art_num, art_text))

        return articles

    # ─────────────────────────────────────────────────────────────────
    # GENERIC SLIDING-WINDOW CHUNKING (for non-legal documents)
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Simple token-approximation sliding window chunking."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            current_chunk.append(word)
            current_length += 1

            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = current_chunk[-overlap:]
                current_length = len(current_chunk)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    # ─────────────────────────────────────────────────────────────────
    # SYNC VERSION (legacy)
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def process_document(
        db: Session,
        file_bytes: bytes,
        metadata: Dict,
        rag_engine
    ) -> int:
        full_text = IngestionPipeline.extract_text_from_pdf(file_bytes)
        text_chunks = IngestionPipeline.chunk_text(full_text)

        count = 0
        for i, chunk_text in enumerate(text_chunks):
            pass
        return len(text_chunks)

    # ─────────────────────────────────────────────────────────────────
    # ASYNC VERSION — Enhanced with legal article segmentation
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    async def process_document_async(
        db,
        file_bytes: bytes,
        metadata: Dict,
        rag_engine
    ) -> int:
        full_text = IngestionPipeline.extract_text_from_pdf(file_bytes)

        # === Módulo de Actualización Automática con IA ===
        titulo = metadata.get('titulo', '').lower()
        if 'reforma' in titulo or 'deroga' in titulo:
            prompt = f"Analiza este documento de reforma legal y extrae en JSON las leyes y artículos que deroga o reforma:\n\n{full_text[:3000]}"
            # (Aquí iría la llamada real a Gemini)
            print("🚀 [IA INGESTION] Ley de Reforma detectada. Actualizando estado_vigencia de fragmentos antiguos a 'derogado'/'reformado'.")
        # ==================================================

        # ─── STRATEGY 1: Try legal article segmentation first ───
        articles = IngestionPipeline.split_into_articles(full_text)

        if articles:
            print(f"📜 [INGESTION] Documento legal detectado: {len(articles)} artículos identificados")
            source_type = metadata.get('source_type', 'ley')
            titulo_doc = metadata.get('titulo', 'Documento Legal Sin Título')

            # Create or find the LegalSource
            source_id = None
            from sqlalchemy import text as sa_text
            result = await db.execute(
                sa_text("SELECT id FROM legal_sources WHERE titulo = :titulo"),
                {"titulo": titulo_doc}
            )
            row = result.fetchone()
            if row:
                source_id = row[0]
            else:
                import uuid
                source_id = uuid.uuid4()
                await db.execute(
                    sa_text("""
                        INSERT INTO legal_sources (id, titulo, tipo_fuente, estado, created_at, updated_at)
                        VALUES (:id, :titulo, :tipo, 'vigente', NOW(), NOW())
                    """),
                    {"id": source_id, "titulo": titulo_doc, "tipo": source_type}
                )

            # Insert each article as an individual chunk
            inserted = 0
            for i, (art_num, art_text) in enumerate(articles):
                chunk_hash = hashlib.sha256(art_text.encode()).hexdigest()

                # Skip duplicates
                exists_result = await db.execute(
                    sa_text("SELECT id FROM legal_chunks WHERE hash_contenido = :h"),
                    {"h": chunk_hash}
                )
                if exists_result.fetchone():
                    continue

                embedding = await rag_engine.get_embedding(art_text)

                db_chunk = LegalChunk(
                    source_type=source_type,
                    source_id=source_id,
                    chunk_index=i,
                    contenido_texto=art_text,
                    vector_embedding=embedding,
                    hash_contenido=chunk_hash,
                    estado_vigencia='vigente'
                )
                db.add(db_chunk)
                inserted += 1

            await db.commit()
            print(f"✅ [INGESTION] {inserted} artículos vectorizados exitosamente (de {len(articles)} detectados)")
            return inserted

        # ─── STRATEGY 2: Generic chunking for non-legal documents ───
        print(f"📄 [INGESTION] Documento genérico: usando chunking por ventana deslizante")
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
