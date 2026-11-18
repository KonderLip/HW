import pytest
from fastapi.testclient import TestClient

from main import app
from routers import moderation

client = TestClient(app)


@pytest.mark.parametrize(
    ("is_verified_seller", "images_qty", "expected"),
    [
        (True, 0, True),
        (True, 3, True),
        (False, 1, True),
        (False, 5, True),
        (False, 0, False),
    ],
)
def test_predict(is_verified_seller, images_qty, expected):
    response = client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": is_verified_seller,
            "item_id": 10,
            "name": "Test item",
            "description": "Description",
            "category": 2,
            "images_qty": images_qty,
        },
    )

    assert response.status_code == 200
    assert response.json() is expected


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "seller_id": "abc",
            "is_verified_seller": True,
            "item_id": 10,
            "name": "Test",
            "description": "Description",
            "category": 1,
            "images_qty": 1,
        },
        {
            "seller_id": 1,
            "is_verified_seller": True,
            "item_id": 10,
            "name": "Test",
            "description": "Description",
            "category": 1,
            "images_qty": -1,
        },
    ],
)
def test_predict_validation(payload):
    response = client.post("/predict", json=payload)

    assert response.status_code == 400


def test_predict_internal_error(monkeypatch):
    def broken_predict(*args, **kwargs):
        raise RuntimeError("Something went wrong")

    monkeypatch.setattr(
        moderation.service,
        "predict",
        broken_predict,
    )

    response = client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": True,
            "item_id": 10,
            "name": "Test",
            "description": "Description",
            "category": 1,
            "images_qty": 1,
        },
    )

    assert response.status_code == 500
