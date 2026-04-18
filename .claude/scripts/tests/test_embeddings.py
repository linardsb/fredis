"""Tests for embeddings helpers — avoids loading the 80MB FastEmbed model."""

from __future__ import annotations

import inspect

import numpy as np

from embeddings import bytes_to_embedding, embed_batch, embedding_to_bytes


def test_embed_batch_default_is_256() -> None:
    sig = inspect.signature(embed_batch)
    assert sig.parameters["batch_size"].default == 256


def test_embedding_serialization_roundtrip() -> None:
    original = np.arange(384, dtype=np.float32) / 384.0
    restored = bytes_to_embedding(embedding_to_bytes(original))
    assert restored.shape == original.shape
    assert restored.dtype == np.float32
    assert np.allclose(original, restored)


def test_embed_batch_empty_returns_empty() -> None:
    assert embed_batch([]) == []
