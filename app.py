import streamlit as st

def main():
    st.title("My First Streamlit App")
    
    # Add a header
    st.header("Welcome!")
    
    # Add some text
    st.write("This is a simple Streamlit application.")
    
    # Add a simple interactive element
    name = st.text_input("Enter your name:")
    if name:
        st.write(f"Hello, {name}!")
    
    # Add a slider
    age = st.slider("How old are you?", 0, 100, 25)
    st.write(f"You are {age} years old")

if __name__ == "__main__":
    main() 