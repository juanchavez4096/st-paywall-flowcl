import streamlit as st
from .google_auth import get_logged_in_user_email, show_login_button
from .flow_auth import is_active_subscriber, redirect_button
from .buymeacoffee_auth import get_bmac_payers
from .consts import EMAIL_COOKIE, SUBSCRIBED_COOKIE, TOKEN_COOKIE
from streamlit_javascript import st_javascript
import time
import json
payment_provider = st.secrets.get("payment_provider", "flow")

def remove_from_local_storage(k):
    st_javascript(
        f"localStorage.removeItem('{k}');"
    )
    time.sleep(0.5) 

def get_from_local_storage(k):
    v = st_javascript(f"JSON.parse(localStorage.getItem('{k}'));")
    time.sleep(0.6) 
    return v or {}


def set_to_local_storage(k, v):
    jdata = json.dumps({k: v})
    st_javascript(
        f"localStorage.setItem('{k}', JSON.stringify({jdata}));"
    )
    time.sleep(0.6) 

def add_auth(
    required: bool = True,
    login_button_text: str = "Login with Google",
    login_button_color: str = "#FD504D",
    login_sidebar: bool = True,
):
    if required:
        require_auth(
            login_button_text=login_button_text,
            login_sidebar=login_sidebar,
            login_button_color=login_button_color,
            get_from_local_storage=get_from_local_storage,
            set_to_local_storage=set_to_local_storage,
        )
    else:
        optional_auth(
            login_button_text=login_button_text,
            login_sidebar=login_sidebar,
            login_button_color=login_button_color,
            get_from_local_storage=get_from_local_storage,
            set_to_local_storage=set_to_local_storage,
        )


def require_auth(
    get_from_local_storage,
    set_to_local_storage,
    login_button_text: str = "Login with Google",
    login_button_color: str = "#FD504D",
    login_sidebar: bool = True,
):
    user_email = get_logged_in_user_email(get_from_local_storage,
    set_to_local_storage,)

    if not user_email:
        show_login_button(
            text=login_button_text, color=login_button_color, sidebar=login_sidebar
        )
        st.stop()
    if payment_provider == "flow":
        is_subscriber = user_email and is_active_subscriber(user_email)
    elif payment_provider == "bmac":
        is_subscriber = user_email and user_email in get_bmac_payers()
    else:
        raise ValueError("payment_provider must be 'stripe' or 'bmac'")

    if not is_subscriber:
        redirect_button(
            text="Subscribe now!",
            customer_email=user_email,
            payment_provider=payment_provider,
        )
        st.session_state[SUBSCRIBED_COOKIE] = False
        st.stop()
    elif is_subscriber:
        st.session_state[SUBSCRIBED_COOKIE] = True

    if st.sidebar.button("Logout", type="primary"):
        del st.session_state[EMAIL_COOKIE]
        del st.session_state[SUBSCRIBED_COOKIE]
        remove_from_local_storage(TOKEN_COOKIE)
        st.rerun()


def optional_auth(
    get_from_local_storage,
    set_to_local_storage,
    login_button_text: str = "Login with Google",
    login_button_color: str = "#FD504D",
    login_sidebar: bool = True,
):
    user_email = get_logged_in_user_email(get_from_local_storage,
    set_to_local_storage)
    if payment_provider == "flow":
        is_subscriber = user_email and is_active_subscriber(user_email)
    elif payment_provider == "bmac":
        is_subscriber = user_email and user_email in get_bmac_payers()
    else:
        raise ValueError("payment_provider must be 'stripe' or 'bmac'")

    if not user_email:
        show_login_button(
            text=login_button_text, color=login_button_color, sidebar=login_sidebar
        )
        st.session_state[EMAIL_COOKIE] = ""
        st.sidebar.markdown("")
    if not is_subscriber and user_email:
        redirect_button(
            text="Subscribe now!", customer_email=user_email, payment_provider=payment_provider
        )
        st.sidebar.markdown("")
        st.session_state[SUBSCRIBED_COOKIE] = False

    elif is_subscriber:
        st.session_state[SUBSCRIBED_COOKIE] = True
    if user_email is not None and user_email != "":
        if st.sidebar.button("Logout", type="primary"):
            del st.session_state[EMAIL_COOKIE]
            del st.session_state[SUBSCRIBED_COOKIE]
            remove_from_local_storage(TOKEN_COOKIE)
            st.rerun()
