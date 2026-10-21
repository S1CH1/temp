import requests

# --- Config : à adapter ---
KC = "http://localhost:8080"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"
REALM = "sandbox-api"


def get_token():
    r = requests.post(f"{KC}/realms/master/protocol/openid-connect/token", data={
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": ADMIN_USER,
        "password": ADMIN_PASSWORD,
    })
    return r.json()["access_token"]


def headers():
    return {"Authorization": "Bearer " + get_token()}


def create_realm():
    r = requests.post(f"{KC}/admin/realms", headers=headers(),
                      json={"realm": REALM, "enabled": True})
    print("create realm", r.status_code)


def create_client(client_id):
    r = requests.post(f"{KC}/admin/realms/{REALM}/clients", headers=headers(), json={
        "clientId": client_id,
        "publicClient": False,
        "redirectUris": ["http://localhost:5001/*"],
        "attributes": {"post.logout.redirect.uris": "http://localhost:5001/*"},
    })
    print("create client", r.status_code)


def get_client_secret(client_id):
    clients = requests.get(f"{KC}/admin/realms/{REALM}/clients", headers=headers(),
                           params={"clientId": client_id}).json()
    uuid = clients[0]["id"]
    return requests.get(f"{KC}/admin/realms/{REALM}/clients/{uuid}/client-secret",
                        headers=headers()).json()["value"]


def create_user(username, password):
    r = requests.post(f"{KC}/admin/realms/{REALM}/users", headers=headers(), json={
        "username": username,
        "enabled": True,
        "email": f"{username}@test.local",
        "emailVerified": True,
        "firstName": username,
        "lastName": "Test",
        "credentials": [{"type": "password", "value": password, "temporary": False}],
    })
    print("create user", username, r.status_code)


def create_role(name):
    r = requests.post(f"{KC}/admin/realms/{REALM}/roles", headers=headers(), json={"name": name})
    print("create role", name, r.status_code)


def give_role(username, role_name):
    user = requests.get(f"{KC}/admin/realms/{REALM}/users", headers=headers(),
                        params={"username": username, "exact": "true"}).json()[0]
    role = requests.get(f"{KC}/admin/realms/{REALM}/roles/{role_name}", headers=headers()).json()
    r = requests.post(f"{KC}/admin/realms/{REALM}/users/{user['id']}/role-mappings/realm",
                      headers=headers(), json=[role])
    print("give role", role_name, "to", username, r.status_code)


def list_users():
    users = requests.get(f"{KC}/admin/realms/{REALM}/users", headers=headers()).json()
    for u in users:
        print(" -", u["username"])


def delete_realm():
    r = requests.delete(f"{KC}/admin/realms/{REALM}", headers=headers())
    print("delete realm", r.status_code)


if __name__ == "__main__":
    create_realm()
    create_client("flask-app")
    print("secret :", get_client_secret("flask-app"))
    create_user("alice", "alice")
    create_role("app-admin")
    give_role("alice", "app-admin")
    list_users()
    # delete_realm()
