import streamlit as st
from neo4j import GraphDatabase

URI = st.secrets["NEO4J_URI"]
AUTH = (st.secrets["NEO4J_USERNAME"], st.secrets["NEO4J_PASSWORD"])

st.logo("gallery/logo.png")
st.title(":clipboard: NTT Com DD Sales Qualification Tool")

def set_stage(stage):
    st.session_state["stage"] = stage

if "stage" not in st.session_state:
    st.session_state["stage"] = "1-challenge"

placeholder = st.empty()
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
if st.session_state["stage"] == "1-challenge":
    with placeholder.container():
        challenges = ["North", "East", "South", "West"]
        st.markdown("##### Are you facing any challenges in the following area of your IT infrastructure?")
        selection = st.pills("Choose as many as you like", challenges, selection_mode="multi")
        st.text("")
        st.button("Next", on_click=set_stage, args=["2-requirement"])
elif st.session_state["stage"] == "2-requirement":
    with placeholder.container():
        requirements = ["North", "East", "South", "West"]
        st.markdown("##### Do you face?")
        st.text("")
        st.button("Get recommendation", type="primary", on_click=set_stage, args=["3-recommendation"])
        st.button("Back", on_click=set_stage, args=["1-challenge"])
elif st.session_state["stage"] == "3-recommendation":
    with placeholder.container():
        st.button("Start again", on_click=set_stage, args=["1-challenge"])
