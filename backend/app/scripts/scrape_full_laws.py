"""
LexIntellectus ERP - Scraper Masivo de Leyes Nicaragüenses
Descarga textos legales completos de múltiples fuentes oficiales y alternativas,
los segmenta artículo por artículo, y los indexa en pgvector.

Fuentes soportadas:
  1. legislacion.asamblea.gob.ni (Digesto Jurídico Oficial)
  2. digesto.asamblea.gob.ni
  3. PDFs locales subidos por el usuario

Uso:
  docker exec -t lexintellectus-api python -m app.scripts.scrape_full_laws
"""

import asyncio
import re
import uuid
import hashlib
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import httpx

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://lexintellectus:lexintellectus_dev_2026@postgres:5432/lexintellectus"

# ─────────────────────────────────────────────────────────────────────
# REGISTRY OF NICARAGUAN LAWS WITH KNOWN URLS
# ─────────────────────────────────────────────────────────────────────
LAWS_REGISTRY = [
    {
        "titulo": "Código Civil de la República de Nicaragua (Cuarta Edición Oficial 2019)",
        "tipo": "ley",
        "urls": [
            "http://legislacion.asamblea.gob.ni/normaweb.nsf/b3c6607d7285514f06257a070058b88f/b495200256191b7e062584d300645607?OpenDocument",
            "http://digesto.asamblea.gob.ni/iunp/docspdf/gacetas/2019/12/g236.pdf",
        ]
    },
    {
        "titulo": "Código de Familia de Nicaragua (Ley 870)",
        "tipo": "ley",
        "urls": [
            "http://legislacion.asamblea.gob.ni/normaweb.nsf/($All)/BF20230A44CCE90E06257D400064BAA7?OpenDocument",
        ]
    },
    {
        "titulo": "Código Penal de la República de Nicaragua (Ley 641)",
        "tipo": "ley",
        "urls": [
            "http://legislacion.asamblea.gob.ni/normaweb.nsf/($All)/5C6133EBF4E8B1B1062573080056D09C?OpenDocument",
        ]
    },
    {
        "titulo": "Ley General de los Registros Públicos (Ley 698)",
        "tipo": "ley",
        "urls": [
            "http://legislacion.asamblea.gob.ni/normaweb.nsf/($All)/B2A81CC82CF37D2006257673005E1C5A?OpenDocument",
        ]
    },
    {
        "titulo": "Código de Comercio de la República de Nicaragua",
        "tipo": "ley",
        "urls": [
            "http://legislacion.asamblea.gob.ni/normaweb.nsf/($All)/D06E1582B649AC13062572340075E94A?OpenDocument",
        ]
    },
    {
        "titulo": "Ley del Notariado de la República de Nicaragua",
        "tipo": "ley",
        "urls": [
            "http://legislacion.asamblea.gob.ni/normaweb.nsf/($All)/E50CFB5C08B4E5FE0625724A006162A9?OpenDocument",
        ]
    },
    {
        "titulo": "Código Procesal Civil de Nicaragua (Ley 902)",
        "tipo": "ley",
        "urls": [
            "http://legislacion.asamblea.gob.ni/normaweb.nsf/($All)/51A0DADE0A48B5FA0625808D006D82CF?OpenDocument",
        ]
    },
    {
        "titulo": "Código Procesal Penal de Nicaragua (Ley 406)",
        "tipo": "ley",
        "urls": [
            "http://legislacion.asamblea.gob.ni/normaweb.nsf/($All)/5EB5F629016016CE062570A100583561?OpenDocument",
        ]
    },
]


def get_deterministic_embedding(content: str) -> List[float]:
    """Generates a deterministic 3072-dim vector embedding based on content hash."""
    val = int(hashlib.md5(content.encode("utf-8")).hexdigest(), 16) % 100 / 1000.0
    return [val] * 3072


def embedding_to_pgvector_literal(embedding: List[float]) -> str:
    return "[" + ",".join(str(v) for v in embedding) + "]"


def split_into_articles(full_text: str) -> List[Tuple[str, str]]:
    """
    Splits a full law text into individual articles.
    Returns list of (article_number, article_text) tuples.

    Handles formats like:
      - Art. 1.- ...
      - Artículo 1.- ...
      - Arto. 1.- ...
      - Art. 1. ...
      - ARTICULO 1.-
    """
    # Regex to match article starts
    pattern = r'(?:Art(?:o|ículo)?\.?\s*(\d+)[\.\-]+\s*)'
    
    splits = list(re.finditer(pattern, full_text, re.IGNORECASE))
    
    if not splits:
        # If no articles found, return the entire text as one chunk
        return [("0", full_text)]
    
    articles = []
    for i, match in enumerate(splits):
        art_num = match.group(1)
        start = match.start()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(full_text)
        art_text = full_text[start:end].strip()
        
        # Skip articles that are too short (likely parsing artifacts)
        if len(art_text) > 20:
            articles.append((art_num, art_text))
    
    return articles


async def fetch_law_text(urls: List[str]) -> Optional[str]:
    """
    Attempts to fetch the full text of a law from multiple URLs with resilient fallback.
    Returns the raw text content, or None if all sources fail.
    """
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*"
        },
        verify=False  # Some gov sites have expired certificates
    ) as client:
        for url in urls:
            try:
                print(f"    📡 Intentando: {url[:80]}...")
                response = await client.get(url)
                if response.status_code == 200:
                    content = response.text
                    # Basic HTML tag stripping for raw text extraction
                    # Remove script and style blocks
                    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    # Replace <br> and </p> with newlines
                    content = re.sub(r'<br\s*/?>|</p>|</div>|</li>', '\n', content, flags=re.IGNORECASE)
                    # Remove all remaining HTML tags
                    content = re.sub(r'<[^>]+>', '', content)
                    # Decode HTML entities
                    content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                    content = content.replace('&nbsp;', ' ').replace('&quot;', '"')
                    # Collapse multiple whitespace
                    content = re.sub(r'\n{3,}', '\n\n', content)
                    content = content.strip()
                    
                    if len(content) > 500:  # Minimum viable content
                        print(f"    ✅ Obtenido: {len(content):,} caracteres")
                        return content
                    else:
                        print(f"    ⚠️ Contenido demasiado corto ({len(content)} chars), probando siguiente fuente...")
                else:
                    print(f"    ❌ HTTP {response.status_code}")
            except Exception as e:
                print(f"    ❌ Error: {type(e).__name__}: {str(e)[:80]}")
    
    return None


async def ingest_law_articles(
    session: AsyncSession,
    source_id,
    tipo: str,
    articles: List[Tuple[str, str]]
) -> int:
    """Ingests a list of (article_number, article_text) tuples into pgvector."""
    inserted = 0
    for i, (art_num, art_text) in enumerate(articles):
        chunk_hash = hashlib.sha256(art_text.encode("utf-8")).hexdigest()
        
        # Check if chunk already exists
        exists_result = await session.execute(
            text("SELECT id FROM legal_chunks WHERE hash_contenido = :h"),
            {"h": chunk_hash}
        )
        if exists_result.fetchone():
            continue
        
        embedding = get_deterministic_embedding(art_text)
        emb_literal = embedding_to_pgvector_literal(embedding)
        
        chunk_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO legal_chunks
                    (id, source_type, source_id, chunk_index, contenido_texto,
                     vector_embedding, hash_contenido, estado_vigencia, created_at, updated_at)
                VALUES
                    (:id, :stype, :sid, :idx, :contenido,
                     CAST(:emb AS vector), :hash, 'vigente', NOW(), NOW())
            """),
            {
                "id": chunk_id,
                "stype": tipo,
                "sid": source_id,
                "idx": i,
                "contenido": art_text,
                "emb": emb_literal,
                "hash": chunk_hash,
            }
        )
        inserted += 1
    
    return inserted


async def scrape_and_ingest():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 70)
    print("🏛️  LEXINTELLECTUS — SCRAPER MASIVO DE LEYES DE NICARAGUA")
    print("=" * 70)
    print(f"   Leyes registradas para descarga: {len(LAWS_REGISTRY)}")
    print()

    total_sources_created = 0
    total_articles_inserted = 0
    successful_laws = []
    failed_laws = []

    async with async_session() as session:
        for law in LAWS_REGISTRY:
            title = law["titulo"]
            tipo = law["tipo"]
            urls = law["urls"]

            print(f"\n📘 Procesando: {title}")
            print(f"   Fuentes disponibles: {len(urls)}")

            # Check if source already exists
            result = await session.execute(
                text("SELECT id FROM legal_sources WHERE titulo = :titulo"),
                {"titulo": title}
            )
            source_row = result.fetchone()

            if source_row:
                source_id = source_row[0]
                print(f"   📎 Fuente ya existe en BD (id: {str(source_id)[:8]}...)")
            else:
                source_id = uuid.uuid4()
                await session.execute(
                    text("""
                        INSERT INTO legal_sources (id, titulo, tipo_fuente, estado, created_at, updated_at)
                        VALUES (:id, :titulo, :tipo, 'vigente', NOW(), NOW())
                    """),
                    {"id": source_id, "titulo": title, "tipo": tipo}
                )
                total_sources_created += 1

            # Attempt to fetch the full text
            full_text = await fetch_law_text(urls)

            if full_text:
                # Split into articles
                articles = split_into_articles(full_text)
                print(f"   📄 Artículos detectados: {len(articles)}")

                # Ingest
                inserted = await ingest_law_articles(session, source_id, tipo, articles)
                total_articles_inserted += inserted
                print(f"   ✅ Artículos nuevos indexados: {inserted}")
                successful_laws.append((title, len(articles), inserted))
            else:
                print(f"   ⛔ No se pudo obtener el texto. El servidor puede estar caído.")
                print(f"      Alternativa: Suba el PDF manualmente vía POST /api/v1/ai/ingest")
                failed_laws.append(title)

        await session.commit()

        # Final summary
        total_sources = await session.execute(text("SELECT COUNT(*) FROM legal_sources"))
        total_chunks = await session.execute(text("SELECT COUNT(*) FROM legal_chunks"))

        print(f"\n{'=' * 70}")
        print(f"📊 RESUMEN FINAL DE SCRAPING")
        print(f"{'=' * 70}")
        
        if successful_laws:
            print(f"\n  ✅ LEYES DESCARGADAS E INDEXADAS EXITOSAMENTE:")
            for title, detected, inserted in successful_laws:
                print(f"     • {title}: {detected} artículos detectados, {inserted} nuevos indexados")
        
        if failed_laws:
            print(f"\n  ⛔ LEYES NO ACCESIBLES (servidor caído o bloqueado):")
            for title in failed_laws:
                print(f"     • {title}")
            print(f"\n  💡 INSTRUCCIONES PARA LEYES FALLIDAS:")
            print(f"     1. Descargue el PDF de la ley desde otra fuente (ej. Scribd, Google)")
            print(f"     2. Súbalo usando el endpoint: POST /api/v1/ai/ingest")
            print(f"        curl -X POST http://localhost:8000/api/v1/ai/ingest \\")
            print(f"          -H 'Authorization: Bearer <token>' \\")
            print(f"          -F 'file=@codigo_civil.pdf' \\")
            print(f"          -F 'source_type=ley'")

        print(f"\n  📈 TOTALES EN BASE DE DATOS:")
        print(f"     Fuentes Legales:          {total_sources.scalar()}")
        print(f"     Fragmentos Vectoriales:    {total_chunks.scalar()}")
        print(f"     Nuevos en esta ejecución:  {total_articles_inserted} artículos")
        print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(scrape_and_ingest())
