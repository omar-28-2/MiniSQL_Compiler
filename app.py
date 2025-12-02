import streamlit as st
import pandas as pd
from lexer import Lexer, Token

st.title("Phase 1 SQL Lexer")

uploaded_file = st.file_uploader("Upload SQL File", type=['sql'])

if uploaded_file is not None:
    text = uploaded_file.read().decode('utf-8')
    
    st.subheader("Input SQL Code")
    st.code(text, language='sql')
    
    lexer = Lexer(text)
    tokens = []
    errors = []
    
    while True:
        try:
            token = lexer.get_next_token()
            if token.type == 'EOF':
                break
            tokens.append(token)
        except Exception as e:
            errors.append(str(e))
            if lexer.current_char is not None:
                lexer.advance()
            else:
                break
    
    # Display tokens table
    st.subheader("Tokens")
    if tokens:
        token_data = {
            'Token Type': [token.type for token in tokens],
            'Lexeme': [token.value for token in tokens],
            'Line': [token.line for token in tokens],
            'Column': [token.column for token in tokens]
        }
        df = pd.DataFrame(token_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No tokens found")
    
    # Display errors
    st.subheader("Errors")
    if errors:
        for error in errors:
            st.error(error)
    else:
        st.success("No errors found")
