from unittest.mock import MagicMock, patch

import numpy as np

from app.resume import embeddings


def test_embed_texts_returns_one_vector_per_input():
    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

    embeddings._get_model.cache_clear()
    with patch("app.resume.embeddings._get_model", return_value=fake_model):
        result = embeddings.embed_texts(["text one", "text two"])

    assert len(result) == 2
    fake_model.encode.assert_called_once_with(["text one", "text two"], convert_to_numpy=True)


def test_embed_texts_empty_list_short_circuits_without_loading_model():
    with patch("app.resume.embeddings._get_model") as mock_get_model:
        result = embeddings.embed_texts([])

    assert result == []
    mock_get_model.assert_not_called()


def test_embed_text_single_string():
    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([[0.1, 0.2]])

    embeddings._get_model.cache_clear()
    with patch("app.resume.embeddings._get_model", return_value=fake_model):
        result = embeddings.embed_text("single text")

    assert result == [0.1, 0.2]
