import base64
import json

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


def get_roles():
    """Lit les rôles realm dans l'access_token (sans vérifier la signature, juste pour l'affichage)."""
    token = session.get("access_token")
    if not token:
        return []
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload))
    return data.get("realm_access", {}).get("roles", [])


@app.route("/")
def home():
    user = session.get("user")
    if not user:
        return '<a href="/login">Se connecter</a>'
    return (
        f"Bonjour {user['preferred_username']} !<br>"
        f"Tes rôles : {get_roles()}<br><br>"
        f"<a href='/admin'>Page admin</a> | "
        f"<a href='/reports'>Rapports</a> | "
        f"<a href='/logout'>Se déconnecter</a>"
    )


@app.route("/login")
def login():
    return oauth.keycloak.authorize_redirect(APP + "/callback")


@app.route("/callback")
def callback():
    token = oauth.keycloak.authorize_access_token()
    session["user"] = token["userinfo"]
    session["access_token"] = token["access_token"]
    session["id_token"] = token["id_token"]
    return redirect("/")


@app.route("/admin")
def admin():
    if "app-admin" not in get_roles():
        return "⛔ Accès refusé : il te faut le rôle app-admin. <a href='/'>Retour</a>", 403
    return "✅ Bienvenue dans la zone admin. <a href='/'>Retour</a>"


@app.route("/reports")
def reports():
    # view-reports n'est pas donné directement à alice : elle l'a via le composite app-admin
    if "view-reports" not in get_roles():
        return "⛔ Accès refusé : il te faut le rôle view-reports. <a href='/'>Retour</a>", 403
    return "📊 Voici les rapports. <a href='/'>Retour</a>"


@app.route("/logout")
def logout():
    id_token = session.get("id_token", "")
    session.clear()
    return redirect(
        f"{KEYCLOAK}/protocol/openid-connect/logout"
        f"?id_token_hint={id_token}&post_logout_redirect_uri={APP}/"
    )


app.run(port=5001, debug=True)
