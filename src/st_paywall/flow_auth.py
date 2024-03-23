import streamlit as st
import urllib.parse
from pyflowcl import FlowAPI
from pyflowcl.utils import genera_parametros
import requests

def get_api_key() -> str:
    testing_mode = st.secrets.get("testing_mode", True)
    return (
        st.secrets["flow_api_key_test"]
        if testing_mode
        else st.secrets["flow_api_key"]
    )

def get_api_secret() -> str:
    testing_mode = st.secrets.get("testing_mode", True)
    return (
        st.secrets["flow_secret_key_test"]
        if testing_mode
        else st.secrets["flow_secret_key"]
    )

def get_endpoint() -> str:
    testing_mode = st.secrets.get("testing_mode", True)
    return (
        'sandbox.flow.cl'
        if testing_mode
        else 'www.flow.cl'
    )


def redirect_button(
    text: str,
    customer_email: str,
    color="#FD504D",
    payment_provider: str = "flow",
):
    print('customer email: {}'.format(customer_email))
    encoded_email = urllib.parse.quote(customer_email)

    if payment_provider == "flow":
        if st.sidebar.button(text, type="primary"):

            api_key = get_api_key()
            api_secret = get_api_secret()
            endpoint = get_endpoint()
            api = FlowAPI(api_key=api_key, api_secret=api_secret)
            parametros = {
                "apiKey": api.api_key,
                "planId": "Document text finder subscription",
                "customerId": customer_email,
            }
            parametros_customer = {
                "apiKey": api.api_key,
                "name": customer_email,
                "email": customer_email,
                "externalId": customer_email,
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            create_customer = requests.post("https://{}/api{}".format(endpoint, '/customer/create'), data=genera_parametros(parametros_customer, api.api_secret), headers=headers)
            pago = requests.post("https://{}/api{}".format(endpoint, '/subscription/create'), data=genera_parametros(parametros, api.api_secret), headers=headers)
            print(create_customer.json())
            print(pago.json())
            #pago = api.objetos.call_subscription_create(parameters=genera_parametros(parametros, api.api_secret))
    elif payment_provider == "bmac":
        button_url = f"{st.secrets['bmac_link']}"
    else:
        raise ValueError("payment_provider must be 'flow' or 'bmac'")


def is_active_subscriber(email: str) -> bool:
    api_key = get_api_key()
    api_secret = get_api_secret()
    endpoint = get_endpoint()
    api = FlowAPI(api_key=api_key, api_secret=api_secret)
    parametros = {
        "apiKey": api.api_key,
        "planId": "Document text finder subscription",
    }
    subscriptions = requests.get("https://{}/api{}".format(endpoint, '/subscription/list'), params=genera_parametros(parametros, api.api_secret))
    #subscriptions = api.objetos.call_subscription_list(parameters=genera_parametros(parametros, api.api_secret))
    print(subscriptions.json())
    print(subscriptions.json()['data'])
    print(len(subscriptions.json()['data']) > 0)
    if subscriptions is not None and len(subscriptions.json()['data']) > 0:
        next(x for x in subscriptions.json()['data'] if x["id"] == 1 )
        # TODO verify if is paid subscription with customer email
        return True
    else:
        return False
