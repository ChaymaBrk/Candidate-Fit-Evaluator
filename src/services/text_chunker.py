import re
from typing import List, Dict, Any, Tuple
import logging
import asyncio

logger = logging.getLogger(__name__)

class TextChunker:
    """Service for chunking text into semantic segments with CV support (English/French)"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        # Common CV section headings in English and French
        self.section_headings = [
            "experience", "work experience", "professional experience", 
            "education", "formation académique", "formation",
            "skills", "compétences techniques", "compétences", 
            "projects", "projets", "publications",
            "languages", "langues", "certifications", 
            "interests", "centres d'intérêt", "summary",
            "rèsumè", "objective", "connaissances"
        ]
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into semantic chunks preserving CV structure"""
        # Clean while preserving newlines for structure
        text = self._clean_text(text)
        
        # Split into sections using common headings
        sections = self._split_into_sections(text)
        
        chunks = []
        for section in sections:
            # Skip empty sections
            if not section.strip():
                continue
            # Split section content into sentences
            sentences = self._split_into_sentences(section)
            # Build chunks within section boundaries
            chunks.extend(self._build_chunks(sentences))
        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean while preserving newlines and CV structure"""
        # Replace tabs and multi-spaces (keep single newlines)
        text = re.sub(r'[ \t]+', ' ', text)
        # Preserve hyphenated words and bullet points
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\n\(\)]', '', text)
        # Collapse consecutive newlines
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        return text.strip()

    def _split_into_sections(self, text: str) -> List[str]:
        """Split text using common CV section headings"""
        # Build regex pattern for headings (case-insensitive)
        pattern = r'(?:\n|^)\s*([\w\s]+)\s*\n'
        sections = []
        last_idx = 0
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            header = match.group(1).strip().lower()
            if header in self.section_headings:
                # Add content before header as section
                if match.start() > last_idx:
                    sections.append(text[last_idx:match.start()])
                # Start new section with header
                sections.append(match.group().strip() + '\n')  # Preserve header
                last_idx = match.end()
        
        # Add remaining text
        if last_idx < len(text):
            sections.append(text[last_idx:])
        return sections

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using multilingual punctuation"""
        # Split on punctuation followed by whitespace OR newline
        sentences = re.split(r'(?<=[.!?])\s+|\n\s*', text)
        # Remove empty sentences and clean
        return [s.strip() for s in sentences if s.strip()]

    def _build_chunks(self, sentences: List[str]) -> List[str]:
        """Build chunks from sentences respecting chunk_size and overlap"""
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
            # Finalize chunk if adding sentence exceeds size
            if len(test_chunk) > self.chunk_size and current_chunk:
                chunks.append(current_chunk)
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = f"{overlap_text} {sentence}".strip()
            else:
                current_chunk = test_chunk
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _get_overlap_text(self, text: str) -> str:
        """Extract trailing words for overlap context"""
        words = text.split()
        return " ".join(words[-self.overlap:]) if len(words) > self.overlap else text

