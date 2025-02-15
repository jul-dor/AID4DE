import streamlit as st

# Titel und Beschreibung
st.title("Event Data Exploration 4 Domain Experts")
st.write("Hi! How ready are you to check the representativeness of your event data?")

# Slider
zahl = st.slider("Scale from 1 to 100", 1, 100, 50)
st.write(f"You have chosen {zahl}.")

# Eingabe-Feld
name = st.text_input("Do you have further input for me?")

# Button
if st.button("Say Hello!"):
    st.write(f"Hello, {name}!")
