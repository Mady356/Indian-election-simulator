def test_list_constituencies(client):
    response = client.get("/constituencies")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 1
    assert rows[0]["constituency"] == "Test Constituency"


def test_filter_constituencies_by_party_winner(client):
    response = client.get(
        "/constituencies",
        params={"party_winner": "BJP", "year": 2024},
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 1


def test_get_constituency_detail(client):
    listing = client.get("/constituencies").json()
    constituency_id = listing[0]["id"]
    response = client.get(f"/constituencies/{constituency_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == constituency_id
    assert len(payload["districts"]) >= 1
    assert len(payload["election_history"]) >= 1


def test_get_constituency_results(client):
    listing = client.get("/constituencies").json()
    constituency_id = listing[0]["id"]
    response = client.get(f"/constituencies/{constituency_id}/results")
    assert response.status_code == 200
    payload = response.json()
    assert "2024" in payload["results"]
