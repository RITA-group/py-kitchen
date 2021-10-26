

def test_health(guest):
    response = guest.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_instructor_health(instructor_one):
    response = instructor_one.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
