"""API-Tests für Testverwaltung und Auswertung (/api/tests)."""


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_test_returns_access_code(client):
    response = client.post(
        "/api/tests", json={"title": "Deutsch Lesetest", "description": ""}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Deutsch Lesetest"
    assert len(data["access_code"]) == 8
    assert data["items"] == []


def test_create_test_rejects_empty_title(client):
    response = client.post("/api/tests", json={"title": ""})
    assert response.status_code == 422


def test_list_tests(client, sample_test):
    response = client.get("/api/tests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_test["id"]
    assert data[0]["title"] == "Mathe Basis"
    assert data[0]["item_count"] == 2


def test_get_test_not_found(client):
    response = client.get("/api/tests/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Test nicht gefunden"


def test_add_items_and_get_test(client, sample_test):
    assert len(sample_test["items"]) == 2
    assert sample_test["items"][0]["position"] == 1
    assert sample_test["items"][1]["position"] == 2
    assert sample_test["items"][0]["question"] == "Was ist 1/2 + 1/4?"


def test_add_item_rejects_invalid_correct_option(client, sample_test):
    response = client.post(
        f"/api/tests/{sample_test['id']}/items",
        json={"question": "Kaputt?", "options": ["a", "b"], "correct_option": 5},
    )
    assert response.status_code == 422


def test_add_item_rejects_single_option(client, sample_test):
    response = client.post(
        f"/api/tests/{sample_test['id']}/items",
        json={"question": "Nur eine Option?", "options": ["a"], "correct_option": 0},
    )
    assert response.status_code == 422


def test_add_item_to_missing_test(client):
    response = client.post(
        "/api/tests/9999/items",
        json={"question": "?", "options": ["a", "b"], "correct_option": 0},
    )
    assert response.status_code == 404


def test_results_empty(client, sample_test):
    response = client.get(f"/api/tests/{sample_test['id']}/results")
    assert response.status_code == 200
    data = response.json()
    assert data["max_score"] == 2
    assert data["attempts"] == []
    assert data["submitted_count"] == 0
    assert data["average_score"] is None


def test_results_aggregation(client, sample_test):
    code = sample_test["access_code"]
    items = sample_test["items"]

    # Durchlauf 1: beide Fragen richtig -> Score 2
    attempt1 = client.post("/api/attempts", json={"access_code": code}).json()
    client.patch(
        f"/api/attempts/{attempt1['id']}/answers",
        json={"item_id": items[0]["id"], "selected_option": 0},
    )
    client.patch(
        f"/api/attempts/{attempt1['id']}/answers",
        json={"item_id": items[1]["id"], "selected_option": 1},
    )
    client.post(f"/api/attempts/{attempt1['id']}/submit")

    # Durchlauf 2: eine Frage richtig -> Score 1
    attempt2 = client.post("/api/attempts", json={"access_code": code}).json()
    client.patch(
        f"/api/attempts/{attempt2['id']}/answers",
        json={"item_id": items[0]["id"], "selected_option": 0},
    )
    client.post(f"/api/attempts/{attempt2['id']}/submit")

    # Durchlauf 3: gestartet, nicht abgeschlossen
    client.post("/api/attempts", json={"access_code": code})

    data = client.get(f"/api/tests/{sample_test['id']}/results").json()
    assert data["submitted_count"] == 2
    assert data["average_score"] == 1.5
    assert data["score_distribution"] == {"2": 1, "1": 1}
    assert len(data["attempts"]) == 3
    unfinished = [a for a in data["attempts"] if a["submitted_at"] is None]
    assert len(unfinished) == 1
    assert unfinished[0]["score"] is None
