import streamlit as st

st.set_page_config(
    page_title="Legia Warszawa",
    layout="wide",
)
st.markdown(
    """
    <style>
    .main {
        max-width: 85%;  /* Adjust this value for more or less width */
        margin: 0 auto;  /* Center the content */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Custom CSS for vertical centering
st.markdown(
    """
    <style>
    .custom-title {
        font-size: 80px;  /* Adjust font size as needed */
        font-weight: bold;  /* Optional: make the text bold */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 3])
with col1:
    st.image("resources/legia.ico")
with col2:
    # st.title("Legia Warszawa match reports")
    st.markdown(
        '<div class="centered"><h1 class="custom-title">Legia Warszawa</h1></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    "<h2>Select analysis type from the options available in the sidebar on the left.</h2>",
    unsafe_allow_html=True,
)


st.sidebar.success("Select an analysis above.")
