import streamlit as st
import pandas as pd
from lexer import Lexer, LexerError, Token
from parser import parse_sql, ParseError


def count_nodes(node):
    """Count total nodes in parse tree"""
    count = 1
    for child in node.children:
        count += count_nodes(child)
    return count


st.set_page_config(page_title="SQL Compiler - Phases 1 & 2", layout="wide")
st.title("SQL Compiler - Lexical Analyzer & Syntax Analyzer")

# Tabs for different phases
tab1, tab2, tab3 = st.tabs(["Input & Tokens", "Parse Tree", "Analysis Summary"])

uploaded_file = st.file_uploader("Upload SQL File", type=['sql'])

if uploaded_file is not None:
    text = uploaded_file.read().decode('utf-8')
    
    st.subheader("Input SQL Code")
    st.code(text, language='sql')
    
    # ==================== PHASE 1: LEXICAL ANALYSIS ====================
    lexer = Lexer(text)
    tokens = []
    lexer_errors = []
    
    while True:
        try:
            token = lexer.get_next_token()
            if token.type == 'EOF':
                tokens.append(token)
                break
            tokens.append(token)
        except LexerError as e:
            lexer_errors.append(str(e))
            if lexer.current_char is not None:
                lexer.advance()
            else:
                break
        except Exception as e:
            lexer_errors.append(f"Unexpected error: {str(e)}")
            if lexer.current_char is not None:
                lexer.advance()
            else:
                break
    
    # ==================== PHASE 2: SYNTAX ANALYSIS ====================
    parse_tree, lex_errors, parser_errors = parse_sql(text)
    
    # ==================== TAB 1: TOKENS ====================
    with tab1:
        st.subheader("Lexical Analysis Results")
        
        # Display tokens table
        st.subheader("Tokens")
        if tokens and tokens[-1].type != 'EOF':
            token_data = {
                'Token Type': [token.type for token in tokens[:-1]],
                'Lexeme': [token.value for token in tokens[:-1]],
                'Line': [token.line for token in tokens[:-1]],
                'Column': [token.column for token in tokens[:-1]]
            }
            df = pd.DataFrame(token_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No tokens found")
        
        # Display lexer errors
        st.subheader("Lexical Errors")
        if lexer_errors:
            for error in lexer_errors:
                st.error(error)
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
                    ["Visual Tree", "Text Tree", "JSON Structure"],
                    horizontal=True
                )
            
            if tree_view == "Visual Tree":
                st.subheader("Parse Tree (Interactive)")
                
                def render_tree_visual(node, level=0, prefix="", is_last_sibling=True):
                    """Render interactive collapsible tree with proper ASCII formatting"""
                    # Get node label
                    if node.value:
                        label = f"{node.node_type.value}: '{node.value}'"
                    else:
                        label = node.node_type.value
                    
                    # Add location info
                    location = ""
                    if node.line or node.column:
                        if node.line and node.column:
                            location = f" (Line {node.line}, Col {node.column})"
                        elif node.line:
                            location = f" (Line {node.line})"
                    
                    # Build current node line
                    if level == 0:
                        tree_lines = [f"🌳 {label}{location}"]
                    else:
                        connector = "└── " if is_last_sibling else "├── "
                        tree_lines = [f"{prefix}{connector}{label}{location}"]
                    
                    # Recursively add children
                    for i, child in enumerate(node.children):
                        is_last_child = (i == len(node.children) - 1)
                        if level == 0:
                            child_prefix = ""
                        else:
                            extension = "    " if is_last_sibling else "│   "
                            child_prefix = prefix + extension
                        
                        child_lines = render_tree_visual(child, level + 1, child_prefix, is_last_child)
                        tree_lines.extend(child_lines)
                    
                    return tree_lines
                
                tree_lines = render_tree_visual(parse_tree)
                tree_visual = "\n".join(tree_lines)
                st.code(tree_visual, language="text")
                
            elif tree_view == "Text Tree":
                st.subheader("Parse Tree (Detailed)")
                tree_str = parse_tree.to_string()
                st.code(tree_str, language="text")
                
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
                
                def count_tree_depth(node):
                    """Calculate tree depth"""
                    if not node.children:
                        return 1
                    return 1 + max(count_tree_depth(child) for child in node.children)
                
                def count_terminal_nodes(node):
                    """Count terminal nodes"""
                    count = 1 if node.node_type.value == "Terminal" else 0
                    for child in node.children:
                        count += count_terminal_nodes(child)
                    return count
                
                def count_non_terminal_nodes(node):
                    """Count non-terminal nodes"""
                    count = 1 if node.node_type.value != "Terminal" else 0
                    for child in node.children:
                        count += count_non_terminal_nodes(child)
                    return count
                
                with col1:
                    st.metric("Total Nodes", count_nodes(parse_tree))
                with col2:
                    st.metric("Tree Depth", count_tree_depth(parse_tree))
                with col3:
                    st.metric("Terminal Nodes", count_terminal_nodes(parse_tree))
                with col4:
                    st.metric("Non-Terminal Nodes", count_non_terminal_nodes(parse_tree))
        else:
            st.error("Failed to generate parse tree due to critical parsing errors.")
    
    # ==================== TAB 3: ANALYSIS SUMMARY ====================
    with tab3:
        st.subheader("Compilation Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Tokens", len([t for t in tokens if t.type != 'EOF']))
            st.metric("Lexical Errors", len(lexer_errors))
        
        with col2:
            st.metric("Syntax Errors", len(parser_errors))
            if parse_tree:
                st.metric("Parse Tree Nodes", count_nodes(parse_tree))
        
        with col3:
            status = "✓ Success" if not lexer_errors and not parser_errors else "✗ Failed"
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
            st.dataframe(stats_df, use_container_width=True)
            
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
            st.dataframe(error_df, use_container_width=True)
