from flask import Flask, redirect, session
from authlib.integrations.flask_client import OAuth

# --- Config : à adapter ---
KEYCLOAK = "http://localhost:8080/realms/sandbox-api"
CLIENT_ID = "flask-app"
CLIENT_SECRET = "COLLE_ICI_LE_SECRET_AFFICHE_PAR_kc_admin.py"
APP = "http://localhost:5001"

app = Flask(__name__)
app.secret_key = "dev"

oauth = OAuth(app)
oauth.register(
    name="keycloak",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url=KEYCLOAK + "/.well-known/openid-configuration",
    client_kwargs={"scope": "openid profile email"},
)


@app.route("/")
def home():
    user = session.get("user")
    if not user:
        return '<a href="/login">Se connecter</a>'
    return f"Bonjour {user['preferred_username']} ! <a href='/logout'>Se déconnecter</a><pre>{user}</pre>"

@app.route("/")
def home():
    user = session.get("user")
    if not user:
        return '<a href="/login">Se connecter</a>'
    return (f"Bonjour {user['preferred_username']} !<br>"
            f"Tes rôles : {get_roles()}<br>"
            f"<a href='/admin'>Page admin</a> | <a href='/logout'>Se déconnecter</a>")


@app.route("/admin")
def admin():
    if "app-admin" not in get_roles():
        return "⛔ Accès refusé : il te faut le rôle app-admin", 403
    return "✅ Bienvenue dans la zone admin"

@app.route("/login")
def login():
    return oauth.keycloak.authorize_redirect(APP + "/callback")


@app.route("/callback")
def callback():
    token = oauth.keycloak.authorize_access_token()
    session["user"] = token["userinfo"]
    session["id_token"] = token["id_token"]
    return redirect("/")


@app.route("/logout")
def logout():
    id_token = session.pop("id_token", "")
    session.clear()
    return redirect(
        f"{KEYCLOAK}/protocol/openid-connect/logout"
        f"?id_token_hint={id_token}&post_logout_redirect_uri={APP}/"
    )


app.run(port=5001, debug=True)
