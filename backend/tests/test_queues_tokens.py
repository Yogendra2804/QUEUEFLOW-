"""
Queue and token operation tests — covers all queue operations.
"""


def _create_queue(auth_client, name="Test Queue"):
    r = auth_client.post("/api/queues/", json={"name": name, "description": "desc"})
    assert r.status_code == 201
    return r.json()


def _add_person(auth_client, queue_id, name="Alice"):
    r = auth_client.post(
        f"/api/queues/{queue_id}/tokens/",
        json={"person_name": name, "person_phone": "9999"},
    )
    assert r.status_code == 201
    return r.json()


# ── Queue tests ───────────────────────────────────────────────────────────────

def test_create_queue(auth_client):
    q = _create_queue(auth_client)
    assert q["name"] == "Test Queue"
    assert q["waiting_count"] == 0


def test_list_queues_empty(auth_client):
    r = auth_client.get("/api/queues/")
    assert r.status_code == 200
    assert r.json() == []


def test_multiple_queues(auth_client):
    _create_queue(auth_client, "Q1")
    _create_queue(auth_client, "Q2")
    r = auth_client.get("/api/queues/")
    assert len(r.json()) == 2


def test_cross_manager_isolation(client, manager_data):
    # register two managers
    client.post("/api/auth/register", json=manager_data)
    r1 = client.post("/api/auth/login", json={"email": manager_data["email"], "password": manager_data["password"]})
    token1 = r1.json()["access_token"]

    client.post("/api/auth/register", json={"email": "other@x.com", "password": "secret123", "full_name": "Other"})
    r2 = client.post("/api/auth/login", json={"email": "other@x.com", "password": "secret123"})
    token2 = r2.json()["access_token"]

    # manager 1 creates a queue
    r = client.post("/api/queues/", json={"name": "M1Q"}, headers={"Authorization": f"Bearer {token1}"})
    queue_id = r.json()["id"]

    # manager 2 tries to access it
    r = client.get(f"/api/queues/{queue_id}", headers={"Authorization": f"Bearer {token2}"})
    assert r.status_code == 403


def test_delete_queue(auth_client):
    q = _create_queue(auth_client)
    r = auth_client.delete(f"/api/queues/{q['id']}")
    assert r.status_code == 204
    r2 = auth_client.get(f"/api/queues/{q['id']}")
    assert r2.status_code == 404


# ── Token tests ───────────────────────────────────────────────────────────────

def test_register_person(auth_client):
    q = _create_queue(auth_client)
    t = _add_person(auth_client, q["id"])
    assert t["token_number"] == 1
    assert t["position"] == 1
    assert t["status"] == "waiting"


def test_sequential_token_numbers(auth_client):
    q = _create_queue(auth_client)
    t1 = _add_person(auth_client, q["id"], "Alice")
    t2 = _add_person(auth_client, q["id"], "Bob")
    t3 = _add_person(auth_client, q["id"], "Carol")
    assert t1["token_number"] == 1
    assert t2["token_number"] == 2
    assert t3["token_number"] == 3


def test_fifo_positions(auth_client):
    q = _create_queue(auth_client)
    _add_person(auth_client, q["id"], "A")
    _add_person(auth_client, q["id"], "B")
    r = auth_client.get(f"/api/queues/{q['id']}/tokens/")
    tokens = r.json()
    assert tokens[0]["position"] == 1
    assert tokens[1]["position"] == 2


def test_call_next(auth_client):
    q = _create_queue(auth_client)
    _add_person(auth_client, q["id"], "A")
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/call-next")
    assert r.status_code == 200
    assert r.json()["status"] == "serving"


def test_call_next_empty_queue(auth_client):
    q = _create_queue(auth_client)
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/call-next")
    assert r.status_code == 404


def test_call_next_blocks_while_serving(auth_client):
    q = _create_queue(auth_client)
    _add_person(auth_client, q["id"], "A")
    _add_person(auth_client, q["id"], "B")
    auth_client.post(f"/api/queues/{q['id']}/tokens/call-next")
    # second call-next should fail while someone is being served
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/call-next")
    assert r.status_code == 400


def test_complete_token(auth_client):
    q = _create_queue(auth_client)
    _add_person(auth_client, q["id"], "A")
    cn = auth_client.post(f"/api/queues/{q['id']}/tokens/call-next").json()
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/{cn['id']}/complete")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_complete_non_serving_fails(auth_client):
    q = _create_queue(auth_client)
    t = _add_person(auth_client, q["id"], "A")
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/{t['id']}/complete")
    assert r.status_code == 400


def test_cancel_waiting(auth_client):
    q = _create_queue(auth_client)
    t = _add_person(auth_client, q["id"], "A")
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/{t['id']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_cancel_already_completed(auth_client):
    q = _create_queue(auth_client)
    _add_person(auth_client, q["id"], "A")
    cn = auth_client.post(f"/api/queues/{q['id']}/tokens/call-next").json()
    auth_client.post(f"/api/queues/{q['id']}/tokens/{cn['id']}/complete")
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/{cn['id']}/cancel")
    assert r.status_code == 400


def test_positions_reindex_after_cancel(auth_client):
    q = _create_queue(auth_client)
    t1 = _add_person(auth_client, q["id"], "A")
    _add_person(auth_client, q["id"], "B")
    _add_person(auth_client, q["id"], "C")
    # cancel the first one
    auth_client.post(f"/api/queues/{q['id']}/tokens/{t1['id']}/cancel")
    r = auth_client.get(f"/api/queues/{q['id']}/tokens/")
    tokens = r.json()
    # B and C should now be at positions 1 and 2
    assert tokens[0]["position"] == 1
    assert tokens[1]["position"] == 2


def test_move_up(auth_client):
    q = _create_queue(auth_client)
    _add_person(auth_client, q["id"], "A")
    t2 = _add_person(auth_client, q["id"], "B")
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/{t2['id']}/move-up")
    assert r.status_code == 200
    # B should now be at position 1
    updated = {t["id"]: t for t in r.json()}
    assert updated[t2["id"]]["position"] == 1


def test_move_up_at_front_fails(auth_client):
    q = _create_queue(auth_client)
    t1 = _add_person(auth_client, q["id"], "A")
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/{t1['id']}/move-up")
    assert r.status_code == 400


def test_move_down(auth_client):
    q = _create_queue(auth_client)
    t1 = _add_person(auth_client, q["id"], "A")
    _add_person(auth_client, q["id"], "B")
    r = auth_client.post(f"/api/queues/{q['id']}/tokens/{t1['id']}/move-down")
    assert r.status_code == 200
    updated = {t["id"]: t for t in r.json()}
    assert updated[t1["id"]]["position"] == 2


def test_analytics_endpoint(auth_client):
    r = auth_client.get("/api/analytics/")
    assert r.status_code == 200
    data = r.json()
    assert "total_queues" in data
    assert "queue_analytics" in data


def test_analytics_with_data(auth_client):
    q = _create_queue(auth_client)
    _add_person(auth_client, q["id"], "A")
    cn = auth_client.post(f"/api/queues/{q['id']}/tokens/call-next").json()
    auth_client.post(f"/api/queues/{q['id']}/tokens/{cn['id']}/complete")
    r = auth_client.get("/api/analytics/")
    assert r.status_code == 200
    data = r.json()
    assert data["total_queues"] == 1
    assert len(data["queue_analytics"]) == 1
    qa = data["queue_analytics"][0]
    assert qa["completed_tokens"] == 1
