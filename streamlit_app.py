import streamlit as st
import pandas as pd
from neo4j import GraphDatabase

# Retrieve from secrets.toml
URI = st.secrets["NEO4J_URI"]
AUTH = (st.secrets["NEO4J_USERNAME"], st.secrets["NEO4J_PASSWORD"])

st.set_page_config(
    page_title="NTT Com DD Sales Tool",
    page_icon="gallery/favicon.ico",
    layout="wide"
)

def load_bundle(locale):
    # Load in the text bundle and filter by language locale.
    df = pd.read_csv("text_bundle.csv")
    df = df.query(f"locale == '{locale}'")

    # Create and return a dictionary of key/values.
    lang_dict = {df.key.to_list()[i]:df.value.to_list()[i] for i in range(len(df.key.to_list()))}
    return lang_dict

# lang_dict = load_bundle(lang_options[locale])

with st.sidebar:
    lang_options = {
        "English (US)":"en_US",
        "日本語":"ja_JP"
    }

    st.subheader("Language")
    locale = st.radio(label="Select from below:", options=list(lang_options.keys()))    
    lang_dict = load_bundle(lang_options[locale])


st.logo("gallery/logo.png")
# st.title(":clipboard: NTT Com DD Sales Qualification Tool")
st.title(f":clipboard: {lang_dict['title']}")
st.text("")
st.text("")


def set_stage(stage):
    st.session_state["stage"] = stage

def get_requirements(stage):
    if len(st.session_state["challenge_answer_mem"]) == 0:
        st.warning(lang_dict["s1_warning"], icon="⚠️")
    else:
        # Store the challenge answer into another permanent variable to prevent it is lost after page rerun
        st.session_state["challenge_answer"] = st.session_state["challenge_answer_mem"]
        set_stage(stage)

# def get_recommendation(stage, answer_set):
def get_recommendation(stage):
    # if len(answer_set) == 0:
    #     st.warning("No selection is made. Please answer at least 1 question to proceed.", icon="⚠️")
    # else:       
    # st.text(st.session_state["requirement_answer"]) 
    # Here the reqId is used as key, and it has been linked to radio button key to capture the answer
    # Example: {"1": "Yes", "2": "No"}
    for key in st.session_state["requirement_answer"].keys():
        st.session_state["requirement_answer"][key] = st.session_state[key]

    # for v in st.session_state["requirement_answer"].values():
    #     st.text(type(v))
    #     st.text(type("None"))
    if all(v is None for v in st.session_state["requirement_answer"].values()):
        st.warning(lang_dict["s2_warning"], icon="⚠️")
    else:
        set_stage(stage)
        # st.session_state["answer_set"] = answer_set
    # st.text(st.session_state["answer_set"])
    # st.text(answer_set)

# if "language" not in st.session_state:
#     st.session_state["language"] = "en"
    
if "stage" not in st.session_state:
    st.session_state["stage"] = "1-challenge"

# Create another variable to store the challenge_answer_mem
# throughout the session
if "challenge_answer" not in st.session_state:
    st.session_state["challenge_answer"] = []

# This variable to linked to challenge selection pill and
# may get reset when the page is rerun
if "challenge_answer_mem" not in st.session_state:
    st.session_state["challenge_answer_mem"] = []

# This dictionary variable is used to store the yes/no answer of all the requirements
if "requirement_answer" not in st.session_state:
    st.session_state["requirement_answer"] = {}

placeholder = st.empty()
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    try:
        if st.session_state["stage"] == "1-challenge":
            with placeholder.container():
                # Query Neo4j database to get the list of challenges
                records, summary, keys = driver.execute_query(
                    # "MATCH (c:Challenge) RETURN collect(c.name) as name",
                    "MATCH (c:Challenge) RETURN collect(properties(c)) as challenges",
                    database_="neo4j",
                )
                # Create this dictionary variable to store the challenge name and other language version
                option_map = {}
                # language_name = f'name_{st.session_state["language"]}'
                language_name = f"name_{lang_dict['language']}"
                for c in records[0]["challenges"]:
                    option_map.update({c["name"]: c[language_name]})
                # st.text(option_map)
                with st.form("challenge_form", clear_on_submit=False, border=False):
                    st.markdown(f"#### {lang_dict['s1_question']}")
                    selection = st.pills(
                        lang_dict['s1_pill_label'], 
                        options=option_map.keys(),
                        selection_mode="multi",
                        format_func=lambda option: option_map[option],
                        key="challenge_answer_mem"
                    )
                    st.text("")
                    st.form_submit_button(lang_dict['s1_button_label'], icon=":material/arrow_forward:", on_click=get_requirements, args=["2-requirement"])
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
                    # Initialize this dictionary variable to store the yes/no answer for each requirement
                    st.session_state["requirement_answer"].update({r["reqId"]: "None"})

                with st.form("requirement_form", border=False):
                    st.markdown(f"##### :red[:material/info: {lang_dict['s2_instruction']}]")
                    question_no = 1
                    # answer_set = {}
                    # Example of value = question_en
                    question_column_name = f"question_{lang_dict['language']}"
                    # Create this dictionary to be used in radio format_func to display 
                    # the option in the desired language
                    radio_options = {
                        "Yes": lang_dict["s2_radio_yes"],
                        "No": lang_dict["s2_radio_no"]
                    }
                    for r in requirement_list:
                        # answer_set[r["reqId"]] = r["reqId"]
                        st.markdown(f'#### {question_no}. {r[question_column_name]}')
                        # answer_set[r["reqId"]] = st.radio(
                        # key_var = r["reqId"]
                        st.radio(
                            r[question_column_name], 
                            ["Yes", "No"],
                            index=None,
                            format_func=lambda x: radio_options[x],
                            key=r["reqId"],
                            horizontal=True, 
                            label_visibility="collapsed"
                        )
                        st.text("")
                        question_no += 1
                    st.form_submit_button(lang_dict["s2_button_next"], type="primary", icon=":material/network_intelligence_update:", on_click=get_recommendation, args=["3-recommendation"])
                    # submit = st.form_submit_button("Get recommendation", type="primary")
                    st.form_submit_button(lang_dict["s2_button_back"], icon=":material/arrow_back:", on_click=set_stage, args=["1-challenge"])

                # if submit:
                #     get_recommendation("3-recommendation", answer_set)
        elif st.session_state["stage"] == "3-recommendation":
            with placeholder.container():
                reqIds = []
                # Gather all the requirement Ids that have been answered as "Yes"
                for key, value in st.session_state["requirement_answer"].items():
                    if value == "Yes":
                        reqIds.append(key)

                # Query Neo4j database to retrieve all the products that can solve the requirements
                records, summary, keys = driver.execute_query(
                    """
                    MATCH (p:Product)-[:SOLVE]->(r:Requirement)
                    WHERE r.reqId IN $requirement_ids
                    RETURN collect(DISTINCT properties(p)) as productList
                    """, 
                    requirement_ids=reqIds, 
                    database_="neo4j",
                )

                # Query Neo4j database to retreive the product and requirement ID that
                # is mandatory for the product to be recommended
                mandatory_products = {}
                records_mandatory, summary, keys = driver.execute_query(
                    """
                    MATCH (p:Product)-[s:SOLVE {isMandatory:true}]->(r:Requirement)
                    RETURN p.name as product_name, r.reqId as req_id
                    """,
                    database_="neo4j",
                )
                # Populate the dictionary to include the mandatory requirement ID and its product name
                for rec in records_mandatory:
                    # st.text(rec["product_name"])
                    # st.text(rec["req_id"])
                    mandatory_products.update({rec["req_id"]: rec["product_name"]})
                    
                # st.text(mandatory_products)
                

                st.subheader(lang_dict["s3_header"])
                # Example of value = url_en
                url_column_name = f"url_{lang_dict['language']}"
                for p in records[0]["productList"]:
                    # Need to make sure the product has met the mandatory requirement
                    # before it can be displayed in the recommendation list
                    for key, value in mandatory_products.items():
                        if value != p["name"]: 
                            # Product name has no mandatory requirement, so proceed to recommend
                            with st.expander(f'**{p["name"]}**'):
                                st.markdown(f'[{p["fullName"]}]({p[url_column_name]})')
                        else:
                            # Product name has mandatory requirement, so check if mandatory requirement ID
                            # is fulfilled
                            if key in reqIds:
                                with st.expander(f'**{p["name"]}**'):
                                    st.markdown(f'[{p["fullName"]}]({p[url_column_name]})')

                # st.text(records[0]["productList"])
                # st.text(records)
                st.text("")
                st.button(lang_dict["s3_button_label"], icon=":material/restart_alt:", on_click=set_stage, args=["1-challenge"])
    except Exception as e:
        st.exception(e)
