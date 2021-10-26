
def test_instructor_profile(instructor_one):
    response = instructor_one.get("/api/v1/profile")
    assert response.status_code == 200
    assert response.json() == {
        'id': 'instructor_one',
        'display_name': 'Test Instructor One',
        'notification_token': None
    }


def test_student_profile(student_one):
    response = student_one.get("/api/v1/profile")
    assert response.status_code == 200
    assert response.json() == {
        'id': 'student_one',
        'display_name': 'Test Student One',
        'notification_token': None
    }


def test_no_auth_error(guest):
    response = guest.get("/api/v1/profile")
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not authenticated'}
