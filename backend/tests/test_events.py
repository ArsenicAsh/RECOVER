import pytest_asyncio

import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domain.models.customer import Customer
from app.domain.models.event import Event
from app.domain.models.merchant import Merchant
from app.main import app


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def merchant(db_session: AsyncSession) -> Merchant:
    merchant = Merchant(
        name="Test Merchant",
        currency="INR",
    )

    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    return merchant


@pytest_asyncio.fixture
async def customer(
    db_session: AsyncSession,
    merchant: Merchant,
) -> Customer:
    customer = Customer(
        merchant_id=merchant.id,
        external_ref=f"cust-{uuid.uuid4()}",
        name="Test Customer",
        email="test@example.com",
    )

    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    return customer


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_valid_event_ingestion(
    client: AsyncClient,
    merchant: Merchant,
    customer: Customer,
):
    occurred_at = datetime(
        2026,
        8,
        30,
        18,
        0,
        tzinfo=timezone.utc,
    )

    payload = {
        "event_id": "evt-valid-001",
        "event_type": "payment.captured",
        "merchant_id": str(merchant.id),
        "customer_id": str(customer.id),
        "occurred_at": occurred_at.isoformat(),
        "source": "razorpay",
        "payload": {
            "amount": 10000,
            "currency": "INR",
        },
        "sequence_hint": 1,
    }

    response = await client.post("/events", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert body["event_id"] == "evt-valid-001"
    assert body["event_type"] == "payment.captured"
    assert body["merchant_id"] == str(merchant.id)
    assert body["customer_id"] == str(customer.id)
    assert body["source"] == "razorpay"
    assert body["payload"]["amount"] == 10000
    assert body["processed_at"] is None


@pytest.mark.asyncio
async def test_invalid_event_rejected(
    client: AsyncClient,
    merchant: Merchant,
):
    payload = {
        "event_id": "",
        "event_type": "payment.captured",
        "merchant_id": str(merchant.id),
        "occurred_at": "not-a-timestamp",
        "source": "razorpay",
        "payload": {},
        "unexpected_field": "should-be-rejected",
    }

    response = await client.post("/events", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_delivery_returns_original_event(
    client: AsyncClient,
    merchant: Merchant,
    customer: Customer,
):
    occurred_at = datetime(
        2026,
        8,
        30,
        18,
        30,
        tzinfo=timezone.utc,
    )

    payload = {
        "event_id": "evt-duplicate-001",
        "event_type": "payment.failed",
        "merchant_id": str(merchant.id),
        "customer_id": str(customer.id),
        "occurred_at": occurred_at.isoformat(),
        "source": "razorpay",
        "payload": {
            "reason": "insufficient_funds",
        },
    }

    first = await client.post("/events", json=payload)
    second = await client.post("/events", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200

    first_body = first.json()
    second_body = second.json()

    assert second_body["id"] == first_body["id"]
    assert second_body["received_at"] == first_body["received_at"]
    assert second_body["occurred_at"] == first_body["occurred_at"]
    assert second_body["processed_at"] is None


@pytest.mark.asyncio
async def test_occurred_at_is_preserved(
    client: AsyncClient,
    merchant: Merchant,
):
    occurred_at = datetime(
        2026,
        8,
        29,
        12,
        15,
        42,
        tzinfo=timezone.utc,
    )

    payload = {
        "event_id": "evt-time-001",
        "event_type": "order.created",
        "merchant_id": str(merchant.id),
        "occurred_at": occurred_at.isoformat(),
        "source": "shopify",
        "payload": {},
    }

    response = await client.post("/events", json=payload)

    assert response.status_code == 201

    body = response.json()

    returned_occurred_at = datetime.fromisoformat(
    body["occurred_at"].replace("Z", "+00:00")
    )

    assert returned_occurred_at == occurred_at


@pytest.mark.asyncio
async def test_received_at_is_recorded(
    client: AsyncClient,
    merchant: Merchant,
):
    payload = {
        "event_id": "evt-received-001",
        "event_type": "order.created",
        "merchant_id": str(merchant.id),
        "occurred_at": "2026-08-30T10:00:00+00:00",
        "source": "shopify",
        "payload": {},
    }

    response = await client.post("/events", json=payload)

    assert response.status_code == 201

    body = response.json()

    received_at = datetime.fromisoformat(body["received_at"])

    assert received_at.tzinfo is not None


@pytest.mark.asyncio
async def test_processed_at_remains_unset(
    client: AsyncClient,
    merchant: Merchant,
):
    payload = {
        "event_id": "evt-processing-001",
        "event_type": "order.created",
        "merchant_id": str(merchant.id),
        "occurred_at": "2026-08-30T10:00:00+00:00",
        "source": "shopify",
        "payload": {},
    }

    response = await client.post("/events", json=payload)

    assert response.status_code == 201
    assert response.json()["processed_at"] is None


@pytest.mark.asyncio
async def test_out_of_order_arrival_preserves_event_chronology(
    client: AsyncClient,
    merchant: Merchant,
):
    later = {
        "event_id": "evt-later",
        "event_type": "payment.captured",
        "merchant_id": str(merchant.id),
        "occurred_at": "2026-08-30T12:00:00+00:00",
        "source": "razorpay",
        "payload": {"position": "later"},
    }

    earlier = {
        "event_id": "evt-earlier",
        "event_type": "payment.authorized",
        "merchant_id": str(merchant.id),
        "occurred_at": "2026-08-30T11:00:00+00:00",
        "source": "razorpay",
        "payload": {"position": "earlier"},
    }

    first = await client.post("/events", json=later)
    second = await client.post("/events", json=earlier)

    assert first.status_code == 201
    assert second.status_code == 201

    first_event = first.json()
    second_event = second.json()

    first_occurred_at = datetime.fromisoformat(
    first_event["occurred_at"].replace("Z", "+00:00")
    )
    second_occurred_at = datetime.fromisoformat(
        second_event["occurred_at"].replace("Z", "+00:00")
    )

    assert first_occurred_at == datetime(
        2026, 8, 30, 12, 0, tzinfo=timezone.utc
    )

    assert second_occurred_at == datetime(
        2026, 8, 30, 11, 0, tzinfo=timezone.utc
    )

    assert first_event["received_at"] != second_event["received_at"]