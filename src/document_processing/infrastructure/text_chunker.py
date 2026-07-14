"""Text chunker adapter for splitting text into searchable chunks."""


class TextChunkerService:
    """Splits text into chunks with configurable size and overlap."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def chunk_text(self, text: str) -> list[tuple[str, int | None]]:
        """Split text into chunks by sentences, with optional page numbers.

        Returns a list of (chunk_text, page_number) tuples.
        Page numbers are not tracked since pypdf doesn't provide page metadata
        at the sentence level.
        """
        if not text or not text.strip():
            return []

        chunks: list[tuple[str, int | None]] = []
        current_chunk: list[str] = []
        current_length = 0

        paragraphs = text.split("\n\n")
        for paragraph in paragraphs:
            sentences = self._split_sentences(paragraph)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                if current_length + len(sentence) > self._chunk_size and current_chunk:
                    chunks.append((" ".join(current_chunk), None))
                    overlap_text = self._get_overlap(current_chunk, self._chunk_overlap)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_length = len(overlap_text) if overlap_text else 0

                current_chunk.append(sentence)
                current_length += len(sentence)

        if current_chunk:
            chunks.append((" ".join(current_chunk), None))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        import re

        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap(self, chunk: list[str], overlap_chars: int) -> str:
        """Get the last N characters from a chunk for overlap."""
        text = " ".join(chunk)
        if len(text) <= overlap_chars:
            return text
        return text[-overlap_chars:]
