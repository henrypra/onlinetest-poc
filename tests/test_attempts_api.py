"""API-Tests für die Testdurchführung (/api/attempts)."""


def test_start_attempt_with_valid_code(client, sample_test):
    response = client.post(
        "/api/attempts", json={"access_code": sample_test["access_code"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["test_title"] == "Mathe Basis"
    assert len(data["items"]) == 2
    assert data["answers"] == []
    assert data["submitted_at"] is None
    # Sicherheitskritisch: Teilnehmer:innen dürfen die Lösung nicht sehen.
    for item in data["items"]:
        assert "correct_option" not in item


def test_start_attempt_code_is_case_insensitive(client, sample_test):
    code = sample_test["access_code"].lower()
    response = client.post("/api/attempts", json={"access_code": f"  {code} "})
    assert response.status_code == 201


def test_start_attempt_with_invalid_code(client):
    response = client.post("/api/attempts", json={"access_code": "FALSCH99"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Ungültiger Zugangscode"


def test_save_answer_and_resume(client, sample_test):
    attempt = client.post(
        "/api/attempts", json={"access_code": sample_test["access_code"]}
    ).json()
    item_id = attempt["items"][0]["id"]

    response = client.patch(
        f"/api/attempts/{attempt['id']}/answers",
        json={"item_id": item_id, "selected_option": 2},
    )
    assert response.status_code == 200

    # Antwort überschreiben (Zwischenspeicherung ist idempotent pro Frage)
    client.patch(
        f"/api/attempts/{attempt['id']}/answers",
        json={"item_id": item_id, "selected_option": 0},
    )

    # Wiedereinstieg: gespeicherte Antworten kommen mit
    resumed = client.get(f"/api/attempts/{attempt['id']}").json()
    assert resumed["answers"] == [{"item_id": item_id, "selected_option": 0}]


def test_save_answer_rejects_foreign_item(client, sample_test):
    other = client.post("/api/tests", json={"title": "Anderer Test"}).json()
    foreign_item = client.post(
        f"/api/tests/{other['id']}/items",
        json={"question": "?", "options": ["a", "b"], "correct_option": 0},
    ).json()

    attempt = client.post(
        "/api/attempts", json={"access_code": sample_test["access_code"]}
    ).json()
    response = client.patch(
        f"/api/attempts/{attempt['id']}/answers",
        json={"item_id": foreign_item["id"], "selected_option": 0},
    )
    assert response.status_code == 404


def test_save_answer_rejects_invalid_option(client, sample_test):
    attempt = client.post(
        "/api/attempts", json={"access_code": sample_test["access_code"]}
    ).json()
    response = client.patch(
        f"/api/attempts/{attempt['id']}/answers",
        json={"item_id": attempt["items"][0]["id"], "selected_option": 99},
    )
    assert response.status_code == 422


def test_submit_scores_correctly(client, sample_test):
    attempt = client.post(
        "/api/attempts", json={"access_code": sample_test["access_code"]}
    ).json()
    items = attempt["items"]

    # Frage 1 richtig (Option 0), Frage 2 falsch (Option 0 statt 1)
    client.patch(
        f"/api/attempts/{attempt['id']}/answers",
        json={"item_id": items[0]["id"], "selected_option": 0},
    )
    client.patch(
        f"/api/attempts/{attempt['id']}/answers",
        json={"item_id": items[1]["id"], "selected_option": 0},
    )

    response = client.post(f"/api/attempts/{attempt['id']}/submit")
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 1
    assert data["max_score"] == 2
    assert data["submitted_at"] is not None


def test_submit_twice_is_rejected(client, sample_test):
    attempt = client.post(
        "/api/attempts", json={"access_code": sample_test["access_code"]}
    ).json()
    client.post(f"/api/attempts/{attempt['id']}/submit")

    response = client.post(f"/api/attempts/{attempt['id']}/submit")
    assert response.status_code == 409


def test_answer_after_submit_is_rejected(client, sample_test):
    attempt = client.post(
        "/api/attempts", json={"access_code": sample_test["access_code"]}
    ).json()
    client.post(f"/api/attempts/{attempt['id']}/submit")

    response = client.patch(
        f"/api/attempts/{attempt['id']}/answers",
        json={"item_id": attempt["items"][0]["id"], "selected_option": 0},
    )
    assert response.status_code == 409


def test_attempt_not_found(client):
    assert client.get("/api/attempts/9999").status_code == 404
    assert client.post("/api/attempts/9999/submit").status_code == 404
