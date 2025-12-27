import streamlit as st
import pandas as pd
from lexer import Lexer, LexerError, Token
from parser import parse_sql, ParseError
from semantic import SemanticAnalyzer


st.set_page_config(page_title="SQL Compiler - Phase 1, 2 & 3", layout="wide")
st.title("SQL Compiler - Lexical, Syntax & Semantic Analysis")

# Tabs for different phases
tab1, tab2, tab3, tab4 = st.tabs(["Input & Tokens", "Parse Tree", "Semantic Analysis", "Analysis Summary"])

uploaded_file = st.file_uploader("Upload SQL File", type=['sql'])

if uploaded_file is not None:
    text = uploaded_file.read().decode('utf-8')
    
    st.subheader("Input SQL Code")
    st.code(text, language='sql')
    
    # ==================== PHASES 1 & 2: LEXICAL & SYNTAX ANALYSIS ====================
    parse_tree, lexer_errors, parser_errors = parse_sql(text)
    
    # Get tokens for display (optional, but good for Tab 1)
    lexer = Lexer(text)
    tokens = []
    while True:
        try:
            t = lexer.get_next_token()
            tokens.append(t)
            if t.type == 'EOF': break
        except: break 

    # ==================== PHASE 3: SEMANTIC ANALYSIS ====================
    semantic_success = False
    semantic_errors = []
    symbol_table = None
    
    if parse_tree and not parser_errors:
        analyzer = SemanticAnalyzer()
        semantic_success, semantic_errors, symbol_table = analyzer.analyze(parse_tree)
    
    # ==================== TAB 1: TOKENS ====================
    with tab1:
        st.subheader("Lexical Analysis Results")
        
        # Display tokens table
        st.subheader("Tokens")
        if tokens and len(tokens) > 1:  # More than just EOF token
            token_data = {
                'Token Type': [token.type for token in tokens[:-1]],  # Exclude EOF
                'Lexeme': [token.value for token in tokens[:-1]],
                'Line': [token.line for token in tokens[:-1]],
                'Column': [token.column for token in tokens[:-1]]
            }
            df = pd.DataFrame(token_data)
            st.dataframe(df, width='stretch')
        else:
            st.info("No tokens found")
        
        # Display lexer errors
        st.subheader("Lexical Errors")
        if lexer_errors:
            for error in lexer_errors:
                st.error(str(error))
        else:
            st.success("✓ No lexical errors found!")
    
    # ==================== TAB 2: PARSE TREE ====================
    with tab2:
        st.subheader("Syntax Analysis Results")
        
        if parser_errors:
            st.warning(f"⚠ Found {len(parser_errors)} syntax error(s):")
            for error in parser_errors:
                st.error(str(error))
        else:
            st.success("✓ No syntax errors found!")
        
        if parse_tree:
            # Tree visualization options
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                tree_view = st.radio(
                    "Tree View Style",
                    ["Visual Tree", "JSON Structure"],
                    horizontal=True
                )
            
            if tree_view == "Visual Tree":
                st.subheader("Parse Tree (Interactive)")
                tree_lines = parse_tree.to_visual_string()
                tree_visual = "\n".join(tree_lines)
                st.code(tree_visual, language="text")
                
            else:  # JSON Structure
                st.subheader("Parse Tree (JSON Format)")
                
                def tree_to_dict(node):
                    """Convert parse tree to dictionary for JSON serialization"""
                    return {
                        "type": node.node_type.value,
                        "value": node.value,
                        "line": node.line,
                        "column": node.column,
                        "children": [tree_to_dict(child) for child in node.children]
                    }
                
                tree_dict = tree_to_dict(parse_tree)
                st.json(tree_dict)
            
            # Tree statistics
            with st.expander("Tree Statistics"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Nodes", parse_tree.get_node_count())
                with col2:
                    st.metric("Tree Depth", parse_tree.get_depth())
                with col3:
                    st.metric("Terminal Nodes", parse_tree.get_terminal_count())
                with col4:
                    st.metric("Non-Terminal Nodes", parse_tree.get_non_terminal_count())
        else:
            st.error("Failed to generate parse tree due to critical parsing errors.")
    
    # ==================== TAB 3: SEMANTIC ANALYSIS ====================
    with tab3:
        st.subheader("Semantic Analysis Results")
        
        if not parse_tree or parser_errors:
             st.info("Fix syntax errors to proceed to semantic analysis.")
        else:
            if semantic_success:
                st.success("✓ Semantic Analysis Successful. Query is logically valid.")
                
                # Symbol Table Dump
                if symbol_table and symbol_table.tables:
                    st.subheader("Symbol Table")
                    for table_name, info in symbol_table.tables.items():
                        with st.expander(f"Table: {table_name}", expanded=True):
                            cols_data = []
                            for col_name, col_info in info.columns.items():
                                cols_data.append({
                                    "Column": col_name,
                                    "Type": col_info.data_type,
                                    "Constraints": ", ".join(col_info.constraints)
                                })
                            st.table(pd.DataFrame(cols_data))
                else:
                    st.info("Symbol Table is empty (no tables created).")

            else:
                st.error(f"Found {len(semantic_errors)} semantic error(s):")
                for err in semantic_errors:
                    st.error(err)

    # ==================== TAB 4: ANALYSIS SUMMARY ====================
    with tab4:
        st.subheader("Compilation Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Tokens", len([t for t in tokens if t.type != 'EOF']))
            st.metric("Lexical Errors", len(lexer_errors))
        
        with col2:
            st.metric("Syntax Errors", len(parser_errors))
            if parse_tree:
                st.metric("Parse Tree Nodes", parse_tree.get_node_count())
        
        with col3:
            if lexer_errors or parser_errors:
                status = "✗ Failed (Syntax/Lexical)"
            elif semantic_errors:
                status = "✗ Failed (Semantic)"
            else:
                status = "✓ Success"
            st.metric("Compilation Status", status)
        
        # Token Statistics
        st.subheader("Token Statistics")
        if tokens:
            token_types = {}
            for token in tokens[:-1]:  # Exclude EOF
                token_types[token.type] = token_types.get(token.type, 0) + 1
            
            stats_data = {
                'Token Type': list(token_types.keys()),
                'Count': list(token_types.values())
            }
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, width='stretch')
            
            # Bar chart
            st.bar_chart(stats_df.set_index('Token Type'))
        
        # Error Summary
        if parser_errors:
            st.subheader("Syntax Error Details")
            error_data = {
                'Line': [error.line for error in parser_errors],
                'Column': [error.column for error in parser_errors],
                'Message': [error.message for error in parser_errors],
                'Expected': [error.expected or '-' for error in parser_errors],
                'Found': [error.found or '-' for error in parser_errors]
            }
            error_df = pd.DataFrame(error_data)
            st.dataframe(error_df, width='stretch')
