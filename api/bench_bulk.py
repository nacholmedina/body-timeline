"""Bench: old (6 sequential calls) vs new (1 bulk call) for create + edit.

Uses Flask's in-process test client, so this measures end-to-end app latency
(routing + JWT decode + RBAC + DB commit) without network jitter — which is
exactly what the parallel-vs-bulk improvement targets, since network RTT
masks request-count differences less consistently.

Run: python bench_bulk.py
"""
import os
import statistics
import time

os.environ.setdefault("JWT_SECRET_KEY", "bench-secret")

from app import create_app
from app.extensions import db
from app.models.user import User, Profile


def make_app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "bench-secret",
        "STORAGE_BACKEND": "local",
        "STORAGE_LOCAL_PATH": "/tmp/bt-bench-uploads",
        "FRONTEND_URL": "http://localhost:5173",
    })
    with app.app_context():
        db.create_all()
        u = User(
            email="bench@bt.app",
            first_name="B",
            last_name="B",
            role="patient",
            email_verified=True,
        )
        u.set_password("Bench123!")
        db.session.add(u)
        db.session.flush()
        db.session.add(Profile(user_id=u.id))
        db.session.commit()
    return app


def auth_headers(client):
    r = client.post("/api/v1/auth/login", json={"email": "bench@bt.app", "password": "Bench123!"})
    return {"Authorization": f"Bearer {r.get_json()['access_token']}"}


METRIC_ENDPOINTS = [
    ("/api/v1/body-fat-logs", "body_fat_pct", 18.5),
    ("/api/v1/muscle-mass-logs", "muscle_mass_kg", 65.0),
    ("/api/v1/waist-measurements", "waist_cm", 82.0),
    ("/api/v1/hips-measurements", "hips_cm", 98.0),
    ("/api/v1/neck-measurements", "neck_cm", 38.0),
]


def old_create(client, headers, recorded_at):
    """Mirror the old frontend: weigh-in POST + 5 separate metric POSTs.
    Sequentially because the test client is single-threaded — but that's the
    same behavior the original frontend had before the Promise.all fix."""
    t0 = time.perf_counter()
    r = client.post(
        "/api/v1/weigh-ins",
        headers=headers,
        json={"weight_kg": 75.0, "recorded_at": recorded_at},
    )
    assert r.status_code == 201
    for url, field, value in METRIC_ENDPOINTS:
        r = client.post(
            url,
            headers=headers,
            json={field: value, "recorded_at": recorded_at},
        )
        assert r.status_code == 201, (url, r.get_json())
    return time.perf_counter() - t0


def new_create(client, headers, recorded_at):
    """One bulk POST."""
    t0 = time.perf_counter()
    r = client.post(
        "/api/v1/weigh-ins",
        headers=headers,
        json={
            "weight_kg": 75.0,
            "recorded_at": recorded_at,
            "body_metrics": {
                "body_fat_pct": 18.5,
                "muscle_mass_kg": 65.0,
                "waist_cm": 82.0,
                "hips_cm": 98.0,
                "neck_cm": 38.0,
            },
        },
    )
    assert r.status_code == 201
    return time.perf_counter() - t0


def bench(label, fn, client, headers, n=30):
    times = []
    base = int(time.time())
    # warm-up (JIT-ish, flask import caches, sqlite startup) — discard
    fn(client, headers, f"2099-01-01T00:00:{0:02d}+00:00")
    for i in range(n):
        # Unique recorded_at so we always insert (no UPSERT collisions)
        ra = f"2050-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T{base % 24:02d}:00:{i % 60:02d}+00:00"
        times.append(fn(client, headers, ra))
    mean_ms = statistics.mean(times) * 1000
    median_ms = statistics.median(times) * 1000
    p95_ms = sorted(times)[int(0.95 * len(times))] * 1000
    print(f"{label:>10}: mean={mean_ms:6.2f}ms  median={median_ms:6.2f}ms  p95={p95_ms:6.2f}ms  (n={n})")
    return mean_ms


def main():
    app = make_app()
    client = app.test_client()
    headers = auth_headers(client)

    print("Create flow (weigh-in + 5 body metrics):")
    old_mean = bench("OLD x6", old_create, client, headers)
    new_mean = bench("NEW x1", new_create, client, headers)
    speedup = old_mean / new_mean
    saved = old_mean - new_mean
    print(f"\n=> NEW is {speedup:.2f}x faster on average ({saved:.2f}ms saved per save)")


if __name__ == "__main__":
    main()
