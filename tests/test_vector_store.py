from unittest.mock import MagicMock, patch

from app import vector_store


def test_upsert_vectors_generates_ids_and_calls_client():
    fake_client = MagicMock()
    with patch("app.vector_store._client", return_value=fake_client):
        ids = vector_store.upsert_vectors(
            "test_collection",
            vectors=[[0.1, 0.2], [0.3, 0.4]],
            payloads=[{"a": 1}, {"a": 2}],
        )

    assert len(ids) == 2
    assert len(set(ids)) == 2  # unique
    fake_client.upsert.assert_called_once()
    call_kwargs = fake_client.upsert.call_args.kwargs
    assert call_kwargs["collection_name"] == "test_collection"
    assert len(call_kwargs["points"]) == 2


def test_upsert_vectors_raises_on_length_mismatch():
    import pytest

    with pytest.raises(ValueError):
        vector_store.upsert_vectors("test_collection", vectors=[[0.1]], payloads=[])


def test_ensure_collection_skips_creation_if_exists():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = True

    with patch("app.vector_store._client", return_value=fake_client):
        vector_store.ensure_collection("test_collection", vector_size=384)

    fake_client.create_collection.assert_not_called()


def test_ensure_collection_creates_if_missing():
    fake_client = MagicMock()
    fake_client.collection_exists.return_value = False

    with patch("app.vector_store._client", return_value=fake_client):
        vector_store.ensure_collection("test_collection", vector_size=384)

    fake_client.create_collection.assert_called_once()
