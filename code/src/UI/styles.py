# --- Integration Notes & Stubs ---
# These styles are designed to work with:
# - GeminiAgent.process_query(user_input): returns SQL and explanation
# - SQLValidator.validate_query(sql): returns safety check results
# - DatabaseManager.get_query_results_with_metadata(sql): returns data
# - Streamlit session state for conversation history
# - Error boundaries for API failures
# - Rate limiting and retry logic

# Example integration stub (to be used in UI components):
def process_banking_query(user_input, agent, validator, db_manager):
    import streamlit as st
    try:
        # Rate limiting logic (simple example)
        if st.session_state.get('last_query_time'):
            import time
            elapsed = time.time() - st.session_state['last_query_time']
            if elapsed < 2:
                st.warning('Please wait before sending another query.')
                return None
        st.session_state['last_query_time'] = __import__('time').time()

        agent_result = agent.process_query(user_input)
        sql = agent_result.get('sql')
        explanation = agent_result.get('explanation')
        if not sql:
            st.error(explanation or 'No SQL generated.')
            return None
        validation = validator.validate_query(sql)
        if not validation.get('valid', False):
            st.error(validation.get('message', 'SQL validation failed.'))
            if 'suggestion' in validation:
                st.info(validation['suggestion'])
            return None
        results = db_manager.get_query_results_with_metadata(sql)
        # Save to session state history
        history = st.session_state.get('chat_history', [])
        history.append({'user': user_input, 'sql': sql, 'explanation': explanation, 'results': results})
        st.session_state['chat_history'] = history
        return {'sql': sql, 'explanation': explanation, 'results': results, 'validation': validation}
    except Exception as e:
        st.error(f'An error occurred: {e}')
        return None
# styles.py - Custom CSS and theme functions for Banking Streamlit App

# --- Color Scheme ---
PRIMARY = "#2563eb"  # Modern blue-600 - more subtle than before
SECONDARY = "#3b82f6"  # blue-500 - softer secondary
ACCENT = "#6366f1"  # indigo-500 - subtle accent color
BACKGROUND = "#fefefe"  # Near white with warmth
CARD_BG = "#ffffff"  # Pure white cards
TEXT_PRIMARY = "#334155"  # slate-700 - softer than black
TEXT_SECONDARY = "#64748b"  # slate-500
SUCCESS = "#10b981"  # emerald-500 - friendlier green
ERROR = "#ef4444"  # red-500 - less harsh red
WARNING = "#f59e0b"  # amber-500 - warmer warning

# --- 1. Get Custom CSS ---
def get_custom_css():
    return f"""
    <style>
    /* Base styles for responsive design */
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }}
    
    /* Remove fixed heights that cause scrollbars */
    .stApp > div {{
        overflow-x: hidden;
    }}
    
    /* Responsive design */
    body {{ 
        background: {BACKGROUND}; 
        color: {TEXT_PRIMARY}; 
        font-family: 'Roboto', 'Arial', sans-serif;
        overflow-x: hidden;
    }}
    
    /* Header styling with gradient */
    .bank-header {{ 
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%); 
        color: #fff; 
        padding: 1.5rem 2rem; 
        border-radius: 12px; 
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.15);
    }}
    
    /* Card styling with softer shadows */
    .bank-card {{ 
        background: {CARD_BG}; 
        box-shadow: 0 4px 16px rgba(0,0,0,0.06); 
        border-radius: 16px; 
        padding: 2rem; 
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0,0,0,0.03);
        transition: all 0.3s ease;
    }}
    
    .bank-card:hover {{
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }}
    
    /* Button improvements with subtle gradients */
    .stButton > button {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {SECONDARY} 100%); 
        color: #fff; 
        border-radius: 10px; 
        padding: 0.75rem 1.5rem; 
        border: none; 
        transition: all 0.3s ease;
        width: 100%;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
    }}
    
    .stButton > button:hover {{ 
        background: linear-gradient(135deg, {SECONDARY} 0%, {ACCENT} 100%); 
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3);
    }}
    
    /* Text area improvements with subtle borders */
    .stTextArea > div > div > textarea {{
        border-radius: 12px;
        border: 2px solid rgba(37, 99, 235, 0.1);
        padding: 1rem;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }}
    
    .stTextArea > div > div > textarea:focus {{
        border-color: {PRIMARY};
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }}
    
    /* Dataframe improvements */
    .stDataFrame {{ 
        border-radius: 8px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        overflow: hidden;
    }}
    
    /* Tab improvements with gradients */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        padding: 0.5rem;
        background: rgba(37, 99, 235, 0.03);
        border-radius: 12px;
        margin-bottom: 1rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: {CARD_BG};
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        font-weight: 500;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(37, 99, 235, 0.05);
        transform: translateY(-1px);
    }}
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }}
    
    /* Metric styling with subtle gradients */
    .metric-container {{
        background: linear-gradient(135deg, {CARD_BG} 0%, rgba(37, 99, 235, 0.02) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid {PRIMARY};
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }}
    
    /* Expander improvements with smooth animations */
    .streamlit-expanderHeader {{
        background: linear-gradient(135deg, {BACKGROUND} 0%, rgba(37, 99, 235, 0.01) 100%);
        border-radius: 10px;
        padding: 0.75rem;
        transition: all 0.3s ease;
        border: 1px solid rgba(0,0,0,0.03);
    }}
    
    .streamlit-expanderHeader:hover {{
        background: rgba(37, 99, 235, 0.03);
        transform: translateY(-1px);
    }}
    
    /* Success/error message improvements with modern styling */
    .stSuccess {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.03) 100%);
        border-left: 4px solid {SUCCESS};
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
    }}
    
    .stError {{
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(239, 68, 68, 0.03) 100%);
        border-left: 4px solid {ERROR};
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(245, 158, 11, 0.03) 100%);
        border-left: 4px solid {WARNING};
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1);
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(37, 99, 235, 0.03) 100%);
        border-left: 4px solid {PRIMARY};
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
    }}
    
    /* Query card hover effects */
    .query-card {{
        transition: all 0.3s ease;
    }}
    
    .query-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.15);
    }}
    
    /* Execute button specific styling */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {SUCCESS} 0%, #059669 100%);
        color: white;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35);
    }}
    
    /* Remove scrollbars - better responsive design */
    .main .block-container {{
        overflow-x: hidden;
        max-width: 100%;
    }}
    
    /* Mobile responsive improvements */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }}
        
        .bank-header {{
            padding: 1rem;
        }}
        
        .bank-card {{
            padding: 1rem;
        }}
    }}
    
    .stWarning {{
        background: rgba(217, 119, 6, 0.1);
        border-left: 4px solid {WARNING};
        border-radius: 8px;
        padding: 1rem;
    }}
    
    /* Remove unnecessary scrollbars and improve container management */
    .element-container {{
        overflow: visible !important;
    }}
    
    .main .block-container {{
        max-width: 100% !important;
        padding-left: 5rem;
        padding-right: 5rem;
    }}
    
    /* Streamlit specific fixes */
    .stApp {{
        overflow-x: hidden;
    }}
    
    section[data-testid="stSidebar"] {{
        width: 0 !important;
        min-width: 0 !important;
    }}
    
    /* Tab content areas */
    .stTabs [data-baseweb="tab-panel"] {{
        padding: 1rem 0;
        overflow: visible;
    }}
    
    /* Better spacing for dataframes */
    .stDataFrame > div {{
        max-height: 70vh;
        overflow-y: auto;
        border-radius: 8px;
    }}
    
    /* Responsive breakpoints */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        
        .bank-header, .bank-card {{
            padding: 1rem;
            border-radius: 8px;
        }}
        
        .stButton > button {{
            font-size: 0.9rem;
            padding: 0.4rem 1rem;
        }}
        
        /* Stack columns on mobile */
        .row-widget.stHorizontal {{
            flex-direction: column;
        }}
    }}
    
    @media (max-width: 480px) {{
        .main .block-container {{
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        
        .bank-header {{
            padding: 0.8rem;
            font-size: 1.2rem;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            padding: 0.4rem 0.8rem;
            font-size: 0.9rem;
        }}
        
        /* Make text areas smaller on mobile */
        .stTextArea > div > div > textarea {{
            min-height: 80px;
        }}
    }}
    
    @media (min-width: 1200px) {{
        .main .block-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
    }}
    
    /* Loading animation */
    .bank-loading {{ 
        display: inline-block; 
        width: 24px; 
        height: 24px; 
        border: 3px solid {ACCENT}; 
        border-radius: 50%; 
        border-top-color: {PRIMARY}; 
        animation: spin 0.8s linear infinite; 
    }}
    
    @keyframes spin {{ 
        to {{ transform: rotate(360deg); }} 
    }}
    
    /* Sidebar improvements */
    .css-1d391kg {{
        padding: 1rem;
    }}
    
    /* Footer styling */
    .footer {{
        background: {BACKGROUND};
        padding: 1rem;
        text-align: center;
        color: {TEXT_SECONDARY};
        border-top: 1px solid rgba(0,0,0,0.1);
        margin-top: 2rem;
    }}
    </style>
    """

# --- 2. Apply Banking Theme ---
def apply_banking_theme():
    import streamlit as st
    st.markdown(get_custom_css(), unsafe_allow_html=True)

# --- 3. Chat Message Styles ---
def chat_message_styles():
    return f"""
    <style>
    .bank-message-user {{ background: {PRIMARY}; color: #fff; border-radius: 18px 18px 4px 18px; text-align: right; margin: 0.5rem 0; padding: 0.75rem 1.25rem; max-width: 70%; float: right; clear: both; }}
    .bank-message-assistant {{ background: {BACKGROUND}; color: {TEXT_PRIMARY}; border-radius: 18px 18px 18px 4px; text-align: left; margin: 0.5rem 0; padding: 0.75rem 1.25rem; max-width: 70%; float: left; clear: both; }}
    .bank-timestamp {{ color: {TEXT_SECONDARY}; font-size: 0.85rem; margin-top: 0.25rem; }}
    .bank-typing {{ animation: blink 1s infinite; color: {ACCENT}; }}
    @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} 100% {{ opacity: 1; }} }}
    .bank-code-block {{ background: #222; color: #fff; border-radius: 8px; padding: 0.5rem 1rem; font-family: 'Fira Mono', 'Consolas', monospace; margin: 0.5rem 0; }}
    </style>
    """

# --- 4. Sidebar Styles ---
def sidebar_styles():
    return f"""
    <style>
    .bank-sidebar {{ background: {CARD_BG}; border-radius: 12px; box-shadow: 0 2px 8px #0001; padding: 1rem; }}
    .bank-badge {{ background: {SECONDARY}; color: #fff; border-radius: 12px; padding: 0.25rem 0.75rem; font-size: 0.85rem; }}
    .bank-status-success {{ color: {SUCCESS}; }}
    .bank-status-error {{ color: {ERROR}; }}
    .bank-status-warning {{ color: {WARNING}; }}
    .bank-btn-group button {{ margin-right: 0.5rem; }}
    .bank-sidebar-section {{ margin-bottom: 1rem; }}
    .bank-sidebar-section:hover {{ box-shadow: 0 2px 8px {ACCENT}; }}
    </style>
    """

# --- 5. Table Styles ---
def table_styles():
    return f"""
    <style>
    .bank-table {{ width: 100%; border-collapse: collapse; }}
    .bank-table th {{ background: {ACCENT}; color: #fff; font-weight: 600; padding: 0.75rem; }}
    .bank-table td {{ background: {CARD_BG}; color: {TEXT_PRIMARY}; padding: 0.75rem; }}
    .bank-table tr:nth-child(even) {{ background: {BACKGROUND}; }}
    .bank-table tr:hover {{ background: {ACCENT}; color: #fff; }}
    .bank-currency {{ font-family: 'Fira Mono', 'Consolas', monospace; color: {PRIMARY}; }}
    .bank-date {{ color: {TEXT_SECONDARY}; }}
    </style>
    """

# --- Utility: Apply All Styles ---
def apply_all_styles():
    import streamlit as st
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    st.markdown(chat_message_styles(), unsafe_allow_html=True)
    st.markdown(sidebar_styles(), unsafe_allow_html=True)
    st.markdown(table_styles(), unsafe_allow_html=True)

# --- Accessibility Helper ---
def apply_accessibility():
    import streamlit as st
    st.markdown('<div aria-label="Banking NL-to-SQL UI" tabindex="0"></div>', unsafe_allow_html=True)
