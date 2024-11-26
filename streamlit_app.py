import streamlit as st
from neo4j import GraphDatabase

URI = st.secrets["NEO4J_URI"]
AUTH = (st.secrets["NEO4J_USERNAME"], st.secrets["NEO4J_PASSWORD"])

st.set_page_config(
    page_title="NTT Com DD Sales Tool",
    page_icon="gallery/favicon.ico",
    layout="wide"
)

st.logo("gallery/logo.png")
st.title(":clipboard: NTT Com DD Sales Qualification Tool")
st.text("")
st.text("")

def set_stage(stage):
    st.session_state["stage"] = stage

def get_requirements(stage, selection):
    if len(selection) == 0:
        st.warning("No selection is made. Please select at least 1 challenge to proceed.", icon="⚠️")
    else:
        set_stage(stage)
        st.session_state["selection"] = selection

if "stage" not in st.session_state:
    st.session_state["stage"] = "1-challenge"

placeholder = st.empty()
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    try:
        if st.session_state["stage"] == "1-challenge":
            with placeholder.container():
                # challenges = ["North", "East", "South", "West"]
                records, summary, keys = driver.execute_query(
                    "MATCH (c:Challenge) RETURN collect(c.name) as name",
                    database_="neo4j",
                )
                st.markdown("#### Are you facing any challenges in the following area of your IT infrastructure?")
                selection = st.pills("Choose as many as you like", records[0]["name"], selection_mode="multi")
                st.text("")
                st.button("Next", on_click=get_requirements, args=["2-requirement", selection])
        elif st.session_state["stage"] == "2-requirement":
            with placeholder.container():
                requirements = st.session_state["selection"]
                st.text(requirements)
                st.write(requirements)
                st.markdown("#### Do you face?")
                st.text("")
                st.button("Get recommendation", type="primary", on_click=set_stage, args=["3-recommendation"])
                st.button("Back", on_click=set_stage, args=["1-challenge"])
        elif st.session_state["stage"] == "3-recommendation":
            with placeholder.container():
                st.button("Start again", on_click=set_stage, args=["1-challenge"])
    except Exception as e:
        st.exception(e)
