import asyncio
from typing import Optional

import jwt
import streamlit as st
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.oauth2 import OAuth2Token
from streamlit_local_storage import LocalStorage
from .consts import TOKEN_COOKIE, EMAIL_COOKIE
from jwcrypto import jwk
import requests

testing_mode = st.secrets.get("testing_mode", False)


client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
redirect_url = (
    st.secrets["redirect_url_test"] if testing_mode else st.secrets["redirect_url"]
)

client = GoogleOAuth2(client_id=client_id, client_secret=client_secret)

@st.cache_data(ttl=60 * 60 * 24)
def get_jwks():
    return requests.get("https://www.googleapis.com/oauth2/v3/certs").json()


def decode_user(token: str):
    keys = get_jwks()["keys"]
    for key in keys:
        pem = jwk.JWK(**key).export_to_pem()
        try:
            
            decoded_token = jwt.decode(
                token,
                pem,
                algorithms=[key["alg"]],
                audience=client_id,  # Google OAuth2 Client ID
                issuer="https://accounts.google.com",
            )
            return decoded_token
        except jwt.exceptions.InvalidTokenError:
            continue
    return None

def decode_user_without_validate(token: str):
    decoded_data = jwt.decode(jwt=token, options={"verify_signature": False})

    return decoded_data

async def get_authorization_url(client: GoogleOAuth2, redirect_url: str) -> str:
    authorization_url = await client.get_authorization_url(
        redirect_url,
        scope=["email"],
        extras_params={"access_type": "offline"},
    )
    return authorization_url


def markdown_button(
    url: str, text: Optional[str] = None, color="#FD504D", sidebar: bool = True
):
    markdown = st.sidebar.markdown if sidebar else st.markdown

    markdown(
        f"""
    <a href="{url}" >
        <div style="
            display: inline-flex;
            -webkit-box-align: center;
            align-items: center;
            -webkit-box-pack: center;
            justify-content: center;
            font-weight: 400;
            padding: 0.25rem 0.75rem;
            border-radius: 0.25rem;
            margin: 0px;
            line-height: 1.6;
            width: auto;
            user-select: none;
            background-color: {color};
            color: rgb(255, 255, 255);
            border: 1px solid rgb(255, 75, 75);
            text-decoration: none;
            ">
            {text}
        </div>
    </a>
    """,
        unsafe_allow_html=True,
    )


async def get_access_token(
    client: GoogleOAuth2, redirect_url: str, code: str
) -> OAuth2Token:
    token = await client.get_access_token(code, redirect_url)
    return token


def get_access_token_from_query_params(
    client: GoogleOAuth2, redirect_url: str
) -> OAuth2Token:
    query_params = st.query_params.to_dict()
    code = query_params["code"]
    token = asyncio.run(
        get_access_token(client=client, redirect_url=redirect_url, code=code)
    )
    # Clear query params
    st.query_params.clear()
    return token


def show_login_button(
    text: Optional[str] = "Login with Google", color="#FD504D", sidebar: bool = True
):
    authorization_url = asyncio.run(
        get_authorization_url(client=client, redirect_url=redirect_url)
    )
    markdown_button(authorization_url, text, color, sidebar)


def get_logged_in_user_email(get_from_local_storage,
            set_to_local_storage,) -> Optional[str]:
    if EMAIL_COOKIE in st.session_state:
        return st.session_state[EMAIL_COOKIE]
    
    token_cookie = get_from_local_storage(TOKEN_COOKIE)
    if token_cookie is not None and token_cookie != "" and TOKEN_COOKIE in token_cookie:
        user_info = decode_user(token=token_cookie[TOKEN_COOKIE])
        if user_info is not None:
            st.session_state[EMAIL_COOKIE] = user_info["email"]
            return user_info["email"]

    try:
        token_from_params = get_access_token_from_query_params(client, redirect_url)
    except KeyError:
        return None
    user_info = decode_user_without_validate(token=token_from_params["id_token"])
    set_to_local_storage(TOKEN_COOKIE, token_from_params["id_token"])
    st.session_state[EMAIL_COOKIE] = user_info["email"]
    

    return user_info["email"]