def test_create_task_success(client, auth_headers):
    """Geçerli token ile task oluşturma."""

    payload = {
        "title": "Pytest Automation Task",
        "done": False,
    }

    response = client.post(
        "/tasks",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == payload["title"]
    assert data["done"] is False
    assert "id" in data
    assert "owner" in data


def test_get_all_tasks(client, auth_headers):
    """Görevleri listeleyen endpoint testi."""

    create_response = client.post(
        "/tasks",
        json={
            "title": "First task",
            "done": False,
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/tasks",
        headers=auth_headers,
    )

    assert response.status_code == 200

    tasks = response.json()

    assert isinstance(tasks, list)
    assert len(tasks) == 1
    assert tasks[0]["title"] == "First task"


def test_create_task_endpoint_without_token(client):
    """Token olmadan task oluşturma denemesi."""

    payload = {
        "title": "Unauthorized Task",
        "done": False,
    }

    response = client.post(
        "/tasks",
        json=payload,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"