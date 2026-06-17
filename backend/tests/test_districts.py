def test_list_districts(client):
    response = client.get("/districts")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 1
    assert rows[0]["district"] == "Test District"


def test_filter_districts_by_state(client):
    response = client.get("/districts", params={"state": "Test State"})
    assert response.status_code == 200
    rows = response.json()
    assert all(row["state"] == "Test State" for row in rows)


def test_get_district_detail(client):
    listing = client.get("/districts").json()
    district_id = listing[0]["id"]
    response = client.get(f"/districts/{district_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == district_id
    assert len(payload["demographics"]) >= 1
