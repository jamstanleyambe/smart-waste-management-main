import streamlit as st
@st.fragment(run_every=0.5)
def test_func():
    st.write("Live data")
