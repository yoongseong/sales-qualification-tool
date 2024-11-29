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

def get_requirements(stage):
    if len(st.session_state["challenge_answer_mem"]) == 0:
        st.warning("No selection is made. Please select at least 1 challenge to proceed.", icon="⚠️")
    else:
        st.session_state["challenge_answer"] = st.session_state["challenge_answer_mem"]
        set_stage(stage)

# def get_recommendation(stage, answer_set):
def get_recommendation(stage):
    # if len(answer_set) == 0:
    #     st.warning("No selection is made. Please answer at least 1 question to proceed.", icon="⚠️")
    # else:       
    # st.text(st.session_state["requirement_answer"]) 
    for key in st.session_state["requirement_answer"].keys():
        st.session_state["requirement_answer"][key] = st.session_state[key]

    # for v in st.session_state["requirement_answer"].values():
    #     st.text(type(v))
    #     st.text(type("None"))
    if all(v is None for v in st.session_state["requirement_answer"].values()):
        st.warning("No selection is made. Please answer at least 1 question to proceed.", icon="⚠️")
    else:
        set_stage(stage)
        # st.session_state["answer_set"] = answer_set
    # st.text(st.session_state["answer_set"])
    # st.text(answer_set)

if "stage" not in st.session_state:
    st.session_state["stage"] = "1-challenge"

if "challenge_answer" not in st.session_state:
    st.session_state["challenge_answer"] = []

if "challenge_answer_mem" not in st.session_state:
    st.session_state["challenge_answer_mem"] = []

if "requirement_answer" not in st.session_state:
    st.session_state["requirement_answer"] = {}

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
                with st.form("challenge_form", clear_on_submit=False, border=False):
                    st.markdown("#### Are you facing any challenges in the following area of your IT infrastructure?")
                    selection = st.pills(
                        "Choose as many as you like", 
                        records[0]["name"],
                        key="challenge_answer_mem",
                        selection_mode="multi")
                    st.text("")
                    st.form_submit_button("Next", on_click=get_requirements, args=["2-requirement"])
                    # st.button("Next", on_click=get_requirements, args=["2-requirement", selection])
        elif st.session_state["stage"] == "2-requirement":
            with placeholder.container():
                records, summary, keys = driver.execute_query(
                    """
                    MATCH (r:Requirement)<-[:INTRODUCE]-(c:Challenge)
                    WHERE c.name IN $requirements
                    RETURN DISTINCT properties(r) as requirement
                    """, 
                    requirements=st.session_state["challenge_answer"], 
                    database_="neo4j",
                )

                requirement_list = [r["requirement"] for r in records]
                for r in requirement_list:
                    st.session_state["requirement_answer"].update({r["reqId"]: "None"})

                with st.form("requirement_form", border=False):
                    question_no = 1
                    # answer_set = {}
                    for r in requirement_list:
                        # answer_set[r["reqId"]] = r["reqId"]
                        st.markdown(f'#### {question_no}. {r["question"]}')
                        # answer_set[r["reqId"]] = st.radio(
                        # key_var = r["reqId"]
                        st.radio(
                            r["question"], 
                            ["Yes", "No"],
                            index=None,
                            key=r["reqId"],
                            horizontal=True, 
                            label_visibility="collapsed"
                        )
                        st.text("")
                        question_no += 1
                    st.form_submit_button("Get recommendation", type="primary", on_click=get_recommendation, args=["3-recommendation"])
                    # submit = st.form_submit_button("Get recommendation", type="primary")
                    st.form_submit_button("Back", on_click=set_stage, args=["1-challenge"])

                # if submit:
                #     get_recommendation("3-recommendation", answer_set)
        elif st.session_state["stage"] == "3-recommendation":
            with placeholder.container():
                st.text(st.session_state["requirement_answer"])
                st.button("Start again", on_click=set_stage, args=["1-challenge"])
    except Exception as e:
        st.exception(e)
