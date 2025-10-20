import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from Agent.gemini_agent import GeminiAgent
from Agent.sql_validator import SQLValidator
from data.database_manager import DatabaseManager
from UI.components import render_header, render_database_explorer

# --- Load environment variables ---
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Session State Initialization ---
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "database_connection_status": "Disconnected",
        "ai_agent_status": "Inactive", 
        "error_messages": [],
        "query_results": [],
        "clarifications": {},
        "conversation_context": {}
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Initialize session state
init_session_state()

# --- Cache expensive operations ---
@st.cache_resource
def get_database_manager():
    """Initialize and cache the database manager"""
    return DatabaseManager()

@st.cache_resource
def get_ai_agent():
    """Initialize and cache the AI agent"""
    if not GOOGLE_API_KEY:
        st.error("🚨 Google API key not found! Please set the GOOGLE_API_KEY environment variable.")
        st.stop()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "data", "banking.db")
    return GeminiAgent(db_path=db_path, api_key_env="GOOGLE_API_KEY")

@st.cache_resource
def get_sql_validator():
    """Initialize and cache the SQL validator"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "data", "banking.db")
    return SQLValidator(db_path=db_path)

def create_charts_from_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze DataFrame and create appropriate charts based on data types and patterns.
    Returns a dictionary with chart recommendations and chart objects.
    """
    if df.empty or len(df.columns) < 2:
        return {"suitable": False, "message": "Data not suitable for charting (empty or insufficient columns)"}
    
    # Analyze column types
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    charts = {}
    recommendations = []
    
    # Chart 1: Bar chart for categorical vs numeric data
    if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        
        # Aggregate data if there are too many unique values
        if df[cat_col].nunique() > 20:
            top_categories = df.groupby(cat_col)[num_col].sum().nlargest(15)
            chart_data = top_categories.reset_index()
            chart_data.columns = [cat_col, num_col]
        else:
            chart_data = df.groupby(cat_col)[num_col].sum().reset_index()
        
        bar_chart = px.bar(
            chart_data, 
            x=cat_col, 
            y=num_col,
            title=f"{num_col} by {cat_col}",
            labels={cat_col: cat_col.replace('_', ' ').title(), num_col: num_col.replace('_', ' ').title()}
        )
        bar_chart.update_layout(xaxis_tickangle=-45, height=400, font=dict(family="Poppins"), title_font_size=16)
        charts["bar"] = bar_chart
        recommendations.append(f"Bar chart: {num_col} by {cat_col}")
    
    # Chart 2: Line chart for time series data
    if len(datetime_cols) >= 1 and len(numeric_cols) >= 1:
        date_col = datetime_cols[0]
        num_col = numeric_cols[0]
        
        time_data = df.groupby(df[date_col].dt.date)[num_col].sum().reset_index()
        time_data.columns = [date_col, num_col]
        
        line_chart = px.line(
            time_data, x=date_col, y=num_col, title=f"{num_col} Over Time",
            labels={date_col: "Date", num_col: num_col.replace('_', ' ').title()}
        )
        line_chart.update_layout(height=400, font=dict(family="Poppins"), title_font_size=16)
        charts["line"] = line_chart
        recommendations.append(f"Time series: {num_col} over time")
    
    # Chart 3: Pie chart for categorical distribution
    if len(categorical_cols) >= 1:
        cat_col = categorical_cols[0]
        
        if len(numeric_cols) >= 1:
            pie_data = df.groupby(cat_col)[numeric_cols[0]].sum()
        else:
            pie_data = df[cat_col].value_counts()
        
        if len(pie_data) > 10:
            pie_data = pie_data.nlargest(10)
        
        pie_chart = px.pie(values=pie_data.values, names=pie_data.index, title=f"Distribution by {cat_col}")
        pie_chart.update_layout(height=400, font=dict(family="Poppins"), title_font_size=16)
        charts["pie"] = pie_chart
        recommendations.append(f"Distribution: {cat_col}")
    
    # Chart 4: Histogram for numeric distribution
    if len(numeric_cols) >= 1:
        num_col = numeric_cols[0]
        histogram = px.histogram(df, x=num_col, title=f"Distribution of {num_col}",
                                labels={num_col: num_col.replace('_', ' ').title()})
        histogram.update_layout(height=400, font=dict(family="Poppins"), title_font_size=16)
        charts["histogram"] = histogram
        recommendations.append(f"Histogram: {num_col} distribution")
    
    # Chart 5: Scatter plot for numeric relationships
    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        scatter = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}",
                           labels={x_col: x_col.replace('_', ' ').title(), y_col: y_col.replace('_', ' ').title()})
        scatter.update_layout(height=400, font=dict(family="Poppins"), title_font_size=16)
        charts["scatter"] = scatter
        recommendations.append(f"Scatter plot: {y_col} vs {x_col}")
    
    return {
        "suitable": len(charts) > 0,
        "charts": charts,
        "recommendations": recommendations,
        "message": f"Found {len(charts)} suitable chart types for your data"
    }

class BankingApp:
    def __init__(self):
        self.db_manager = get_database_manager()
        self.agent = get_ai_agent()
        self.sql_validator = get_sql_validator()
        self.logger = logging.getLogger("BankingApp")
        
        # Update connection status
        if self.db_manager.test_connection():
            st.session_state["database_connection_status"] = "Connected"
            st.session_state["ai_agent_status"] = "Active"
        else:
            st.session_state["database_connection_status"] = "Disconnected"

    def handle_user_query(self, user_input, context=None):
        """Process user query and store results in session state, now with follow-up support"""
        try:
            # Create a history entry with timestamp
            query_entry = {
                "query": user_input,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # Get AI agent result with context
            agent_result = self.agent.process_query(user_input, context)
            result_type = agent_result.get("type", "error")
            sql = agent_result.get("sql")
            explanation = agent_result.get("explanation")
            confidence = agent_result.get("confidence")
            
            # Handle clarification needed case
            if result_type == "clarification_needed":
                follow_up_questions = agent_result.get("follow_up_questions", [])
                result = {
                    "type": "clarification_needed",
                    "explanation": explanation,
                    "follow_up_questions": follow_up_questions,
                    "confidence": confidence,
                    "original_query": user_input
                }
                st.session_state["last_query_result"] = result
                query_entry.update(result)
                st.session_state["query_results"].append(query_entry)
                return
            
            # Handle error cases
            if not sql or result_type == "error":
                error_msg = explanation or "Could not generate SQL query"
                
                # Check for specific error types
                if "quota" in error_msg.lower() or "429" in error_msg:
                    error_msg = "🚫 Google API quota exceeded (50 requests/day limit reached). Please try again tomorrow or upgrade your API plan."
                    suggestion = "The free tier allows 50 requests per day. Consider upgrading to a paid plan for unlimited usage."
                elif "api" in error_msg.lower() and "key" in error_msg.lower():
                    error_msg = "🔑 API key issue detected"
                    suggestion = "Please check your Google API key configuration."
                else:
                    suggestion = "Please try rephrasing your question or provide more specific details."
                
                result = {"error": error_msg, "suggestion": suggestion}
                st.session_state["last_query_result"] = result
                query_entry.update(result)
                st.session_state["query_results"].append(query_entry)
                return
            
            # Validate SQL for security
            try:
                validation_result = self.sql_validator.validate_query(sql)
                is_safe = validation_result.get("safe", True) and validation_result.get("valid", True)
                
                # Use the corrected SQL from validator if available
                if "sql" in validation_result:
                    sql = validation_result["sql"]
                    self.logger.info(f"Using corrected SQL from validator: {sql}")
                
                if not is_safe:
                    result = {
                        "error": f"Security validation failed: {validation_result.get('message', 'Unknown validation error')}",
                        "suggestion": "Please rephrase your query to avoid potentially harmful SQL patterns.",
                        "sql": sql
                    }
                    # Reset tab to Data View as default for new query results
                    if "selected_data_tab" in st.session_state:
                        del st.session_state["selected_data_tab"]
                    st.session_state["last_query_result"] = result
                    query_entry.update(result)
                    st.session_state["query_results"].append(query_entry)
                    return
            except Exception as validation_error:
                self.logger.warning(f"SQL validation failed with error: {validation_error}")
            
            # Execute SQL query
            try:
                # Start timing the database execution
                start_time = time.time()
                db_result_df = self.db_manager.execute_query(sql)
                execution_time = time.time() - start_time
                
                if db_result_df is not None and not db_result_df.empty:
                    data = db_result_df.to_dict('records')
                    result = {
                        "sql": sql,
                        "data": data,
                        "explanation": explanation,
                        "confidence": confidence,
                        "row_count": len(data),
                        "execution_time": execution_time,
                        "status": "success"
                    }
                else:
                    result = {
                        "sql": sql,
                        "data": [],
                        "explanation": explanation,
                        "message": "Query executed successfully but returned no results.",
                        "row_count": 0,
                        "execution_time": execution_time,
                        "status": "success"
                    }
                
                # Reset tab to Data View as default for new query results
                if "selected_data_tab" in st.session_state:
                    del st.session_state["selected_data_tab"]
                    
                st.session_state["last_query_result"] = result
                query_entry.update(result)
                st.session_state["query_results"].append(query_entry)
                
            except Exception as db_error:
                result = {
                    "error": f"Database execution failed: {str(db_error)}",
                    "sql": sql,
                    "suggestion": "Please check your query syntax or try a different approach.",
                    "status": "error"
                }
                # Reset tab to Data View as default for new query results
                if "selected_data_tab" in st.session_state:
                    del st.session_state["selected_data_tab"]
                st.session_state["last_query_result"] = result
                query_entry.update(result)
                st.session_state["query_results"].append(query_entry)
                
        except Exception as e:
            result = {
                "error": f"Unexpected error: {str(e)}",
                "suggestion": "Please try again or contact support if the problem persists.",
                "status": "error"
            }
            # Reset tab to Data View as default for new query results
            if "selected_data_tab" in st.session_state:
                del st.session_state["selected_data_tab"]
            st.session_state["last_query_result"] = result
            query_entry = {
                "query": user_input,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            query_entry.update(result)
            st.session_state["query_results"].append(query_entry)

    def render_compact_sample_queries(self):
        """Render sample queries with working functionality - simple approach"""
        sample_queries = [
            "Show me all customers with account balances over $50,000",
            "List the top 5 customers by total transaction amount", 
            "Find all transactions over $10,000 in the last 30 days",
            "Show customers who haven't made transactions recently",
            "Display the average account balance by customer age group",
            "List all employees and their branch information",
            "Show monthly transaction trends for this year",
            "Find customers with multiple account types"
        ]
        
        # Debug info
        if st.session_state.get("debug_last_clicked"):
            st.success(f"✅ Last clicked: {st.session_state['debug_last_clicked']}")
        
        # Simple Streamlit buttons that definitely work
        for i, query in enumerate(sample_queries):
            display_text = query[:52] + "..." if len(query) > 52 else query
            
            if st.button(f"📝 {display_text}", key=f"query_btn_{i}_{hash(query)}", use_container_width=True):
                # Set the query in session state for the text area to pick up
                st.session_state["populate_query"] = query
                st.session_state["query_selected"] = True
                st.session_state["debug_last_clicked"] = query
                
                # Force rerun to update the UI
                st.rerun()

    def render_styles(self):
        """Render all CSS styles in one place"""
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
            
            /* Global styles */
            .main .block-container {
                padding: 2rem 1rem;
                font-family: 'Poppins', sans-serif;
            }
            
            section[data-testid="stSidebar"] { display: none; }
            
            /* Enhanced tab styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 4px;
                background: linear-gradient(90deg, #f8f9fa, #e9ecef);
                padding: 4px;
                border-radius: 10px;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.08);
                margin-bottom: 1.5rem;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 45px;
                background: white;
                border-radius: 6px;
                color: #495057;
                font-weight: 600;
                font-size: 14px;
                border: 1px solid #e2e8f0;
                transition: all 0.2s ease;
                font-family: 'Poppins', sans-serif;
                padding: 0 1.2rem;
                min-width: 140px;
                text-align: center;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background: #f8f9fa;
                border-color: #667eea;
                transform: translateY(-1px);
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: 1px solid #667eea;
                box-shadow: 0 3px 8px rgba(102, 126, 234, 0.3);
                font-weight: 700;
            }
            
            /* Section headers */
            .stMarkdown h3 {
                font-family: 'Poppins', sans-serif;
                font-weight: 600;
                font-size: 1.3rem;
                color: #2d3748;
                border-bottom: 2px solid;
                border-image: linear-gradient(90deg, #667eea, #764ba2) 1;
                padding-bottom: 0.3rem;
                margin: 0.5rem 0;
            }
            
            /* Enhanced button styling - for main submit button only (exclude first column) */
            div[data-testid="column"]:not(:first-child) .stButton > button,
            .stButton > button:not([data-testid*="query_btn"]) {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                font-family: 'Poppins', sans-serif;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
            
            div[data-testid="column"]:not(:first-child) .stButton > button:hover,
            .stButton > button:not([data-testid*="query_btn"]):hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            
            .sample-query-info {
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
                border: 1px solid rgba(102, 126, 234, 0.15);
                border-radius: 6px;
                padding: 0.6rem;
                margin-top: 0.8rem;
                text-align: center;
                font-size: 12px;
                font-style: italic;
                color: #667eea;
                font-weight: 500;
            }
            
            /* Enhanced input styling */
            .stTextArea > div > div > textarea {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-family: 'Poppins', sans-serif;
                transition: border-color 0.3s ease;
                font-size: 14px;
                line-height: 1.5;
            }
            
            .stTextArea > div > div > textarea:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            /* Compact layout improvements */
            .main .block-container .element-container { margin-bottom: 0.5rem; }
            .stColumn { padding: 0 0.5rem; }
            .stColumn:first-child { padding-left: 0; }
            .stColumn:last-child { padding-right: 0; }
            
            /* Force small font for sample query buttons - highest specificity */
            div[data-testid="stVerticalBlock"] div[data-testid="column"]:first-child button,
            div[data-testid="column"]:first-child button[kind="secondary"] {
                font-size: 8px !important;
                font-family: 'Poppins', sans-serif !important;
            }
            
            /* Compact spacing for sample query buttons */
            div[data-testid="column"]:first-child .stButton {
                margin: 0 0 1px 0 !important;
                padding: 0 !important;
            }
            
            div[data-testid="column"]:first-child .element-container {
                margin: 0 0 1px 0 !important;
                padding: 0 !important;
            }
            
            /* Progress bar styling */
            .stProgress > div > div > div > div {
                background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
                background-size: 200% 100%;
                animation: shimmer 2s infinite;
            }
            
            @keyframes shimmer {
                0% { background-position: -200% 0; }
                100% { background-position: 200% 0; }
            }
            
            /* FINAL OVERRIDE: Force styling on sample query buttons - MUST BE LAST */
            .stApp div[data-testid="column"]:first-child button,
            .stApp div[data-testid="column"]:first-child .stButton button,
            .stApp div[data-testid="column"]:first-child .stButton > button {
                font-size: 13px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                background-color: #667eea !important;
                color: #ffffff !important;
                border: 1px solid #5a67d8 !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25) !important;
                font-weight: 500 !important;
                padding: 0.5rem 0.8rem !important;
                margin-bottom: 6px !important;
            }
            
            /* Use CSS specificity hack */
            html body .stApp div[data-testid="column"]:first-child button {
                font-size: 8px !important;
            }
            </style>
            
            <script>
            // Force font size change via JavaScript after DOM loads
            function forceSmallFonts() {
                const buttons = document.querySelectorAll('div[data-testid="column"]:first-child button');
                buttons.forEach(button => {
                    button.style.fontSize = '8px';
                    button.style.fontFamily = 'Poppins, sans-serif';
                });
            }
            
            // Run immediately and on DOM changes
            forceSmallFonts();
            setTimeout(forceSmallFonts, 100);
            setTimeout(forceSmallFonts, 500);
            setTimeout(forceSmallFonts, 1000);
            
            // Observer for dynamic content
            const observer = new MutationObserver(forceSmallFonts);
            observer.observe(document.body, { childList: true, subtree: true });
            </script>
            """, unsafe_allow_html=True)

    def render_query_execution_ui(self, col_query):
        """Render the query execution interface"""
        with col_query:
            st.markdown("### 💬 Ask your banking question")
            st.info("🆕 **New:** I can now ask follow-up questions to clarify ambiguous queries! Try asking 'Show me recent transactions' or 'Find large transactions'.")
            
            # Handle query population and clearing
            query_value = ""
            if st.session_state.get("clear_timestamp"):
                query_value = ""
                st.session_state["clear_timestamp"] = None
            elif st.session_state.get("populate_query"):
                query_value = st.session_state["populate_query"]
                st.session_state["populate_query"] = None
            else:
                query_value = st.session_state.get("main_query_input", "")
            
            user_input = st.text_area(
                "Type your question in natural language...",
                value=query_value,
                key="main_query_input",
                height=120,
                placeholder="e.g., Show me all transactions over $1000 from last month"
            )
            
            col_execute, col_clear = st.columns([3, 1])
            with col_execute:
                if st.button("🚀 Execute Query", key="btn_execute", type="primary", width="stretch"):
                    if user_input.strip():
                        self.execute_query_with_progress(user_input)
                    else:
                        st.warning("Please enter a query first.")
            with col_clear:
                if st.button("🗑️ Clear", key="clear_input", width="stretch"):
                    st.session_state["clear_timestamp"] = datetime.now().timestamp()
                    # Clear query results section as well
                    if "last_query_result" in st.session_state:
                        del st.session_state["last_query_result"]
                    if "selected_data_tab" in st.session_state:
                        del st.session_state["selected_data_tab"]
                    st.rerun()
            
            # Display results
            self.render_query_results()

    def execute_query_with_progress(self, user_input):
        """Execute query with progress indicators"""
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        
        try:
            progress_bar = progress_placeholder.progress(0)
            
            # Step 1
            status_placeholder.info("🔄 **Step 1/4:** Analyzing your question...")
            progress_bar.progress(25)
            time.sleep(0.5)
            
            # Step 2
            status_placeholder.info("🤖 **Step 2/4:** Generating SQL with AI...")
            progress_bar.progress(50)
            time.sleep(0.5)
            
            # Step 3
            status_placeholder.info("🔒 **Step 3/4:** Validating SQL security...")
            progress_bar.progress(75)
            time.sleep(0.3)
            
            # Step 4
            status_placeholder.info("📊 **Step 4/4:** Executing query...")
            progress_bar.progress(90)
            
            # Execute the actual query
            self.handle_user_query(user_input, context=None)
            
            progress_bar.progress(100)
            status_placeholder.success("✅ **Query executed successfully!**")
            time.sleep(0.8)
            
            # Clear the status messages
            status_placeholder.empty()
            progress_placeholder.empty()
            
        except Exception as e:
            status_placeholder.error(f"❌ **Error:** {str(e)}")
            progress_placeholder.empty()
            
        st.rerun()

    def render_query_results(self):
        """Render query results section"""
        if not st.session_state.get("last_query_result"):
            return
            
        st.markdown("---")
        st.markdown("### 📊 Query Results")
        result = st.session_state["last_query_result"]
        
        if "error" in result:
            st.error(f"❌ {result['error']}")
            if "suggestion" in result:
                st.info(f"💡 Suggestion: {result['suggestion']}")
                
        elif result.get("type") == "clarification_needed":
            self.render_clarification_interface(result)
            
        else:
            # Success case - Display results
            if result.get("sql"):
                with st.expander("⚙️ Generated SQL", expanded=False):
                    st.code(result["sql"], language="sql")
            
            if result.get("data") is not None:
                self.render_data_visualization(result)
                # Success message moved to component function
            else:
                st.info("Query executed successfully but returned no data.")

    def render_clarification_interface(self, result):
        """Render the clarification interface for ambiguous queries"""
        st.warning("🤔 **Your query needs clarification to provide accurate results.**")
        st.write(f"**Original Query:** {result.get('original_query', '')}")
        st.write(f"**Issue:** {result.get('explanation', '')}")
        
        st.markdown("### 💬 Please help clarify:")
        follow_up_questions = result.get("follow_up_questions", [])
        
        if not follow_up_questions:
            st.write("Please try rephrasing your question with more specific details.")
            return
            
        st.markdown("**I need a bit more information to give you the best results:**")
        st.info("💡 **Tip:** You can answer any or all questions below. Even partial information helps!")
        
        if "clarifications" not in st.session_state:
            st.session_state.clarifications = {}
        
        with st.form("clarification_form", clear_on_submit=False):
            clarifications = {}
            answered_count = 0
            
            # Show first 2 questions
            questions_to_show = min(len(follow_up_questions), 2)
            
            for i in range(questions_to_show):
                question = follow_up_questions[i]
                st.write(f"**{i+1}.** {question}")
                
                answer = st.text_input(
                    f"Your answer (optional):",
                    key=f"clarification_{i}",
                    placeholder="Leave blank if not applicable or skip...",
                    help="This question is optional - provide as much or as little detail as you'd like",
                    value=""
                )
                
                if answer and answer.strip():
                    clarifications[f"Q{i+1}"] = f"{question} Answer: {answer.strip()}"
                    answered_count += 1
                
                if i < questions_to_show - 1:
                    st.markdown("---")
            
            # Show additional questions in expandable section
            if len(follow_up_questions) > questions_to_show:
                with st.expander("📋 Additional clarifications (optional)", expanded=False):
                    for i in range(questions_to_show, len(follow_up_questions)):
                        question = follow_up_questions[i]
                        st.write(f"**{i+1}.** {question}")
                        
                        answer = st.text_input(
                            f"Your answer (optional):",
                            key=f"clarification_extra_{i}",
                            placeholder="Optional - skip if not relevant...",
                            help="This is completely optional",
                            value=""
                        )
                        
                        if answer and answer.strip():
                            clarifications[f"Q{i+1}"] = f"{question} Answer: {answer.strip()}"
                            answered_count += 1
            
            st.markdown("---")
            
            # Show current status
            total_questions = len(follow_up_questions)
            if answered_count > 0:
                st.success(f"✅ You've provided {answered_count}/{total_questions} clarifications")
            else:
                st.info("💭 No clarifications provided - that's perfectly fine! I'll use smart defaults.")
            
            submitted = st.form_submit_button(
                f"🚀 Continue with Query ({answered_count}/{total_questions} clarifications)", 
                type="primary")
            
            if answered_count == 0:
                st.caption("💡 Click the button above to proceed with smart defaults")
            else:
                st.caption(f"✨ Click to process your query with {answered_count} clarification(s)")
            
            if submitted:
                self.process_clarified_query(result, clarifications, answered_count)

    def process_clarified_query(self, result, clarifications, answered_count):
        """Process a query with clarifications"""
        st.balloons()
        
        context = {
            "previous_query": result.get("original_query", ""),
            "clarifications": clarifications if clarifications else {},
            "additional_info": f"User provided {answered_count} clarifications" if answered_count > 0 else "User chose to proceed with original query"
        }
        
        st.session_state.clarifications = clarifications
        original_query = result.get("original_query", "")
        
        if original_query:
            with st.spinner("🔄 Processing your query..."):
                if clarifications:
                    clarification_text = '; '.join(clarifications.values())
                    enhanced_query = f"{original_query}. Additional context: {clarification_text}"
                else:
                    enhanced_query = f"{original_query}. Use reasonable defaults for any ambiguous terms."
                
                if "last_query_result" in st.session_state:
                    del st.session_state["last_query_result"]
                
                try:
                    self.handle_user_query(enhanced_query, context)
                    
                    if "last_query_result" in st.session_state:
                        new_result = st.session_state["last_query_result"]
                        if isinstance(new_result, dict) and new_result.get("type") == "clarification_needed":
                            new_result.pop("type", None)
                            new_result.pop("follow_up_questions", None)
                            st.session_state["last_query_result"] = new_result
                    
                    st.success("✅ Query processed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing query: {e}")
        else:
            st.error("❌ No original query found to process")

    def render_data_visualization(self, result):
        """Render data visualization with tabs for data and graphs"""
        if result.get("data") and len(result["data"]) > 0:
            # Success message with execution time
            execution_time = result.get("execution_time", 0)
            row_count = len(result["data"])
            st.success(f"✅ Query returned {row_count} rows in {execution_time:.3f}s")
            
            # Reset to Data View tab for new query results
            if "current_tab" not in st.session_state:
                st.session_state.current_tab = "Data View"
            
            # Create tabs for Data View and Graph View (Data View first = default)
            data_tab, graph_tab = st.tabs(["📊 Data View", "📈 Graph View"])
            
            with data_tab:
                # Display the data in a clean table
                import pandas as pd
                df = pd.DataFrame(result["data"])
                st.dataframe(df, width="stretch")
            
            with graph_tab:
                # Check if data is suitable for visualization
                chart_analysis = create_charts_from_data(df)
                
                if chart_analysis["suitable"]:
                    st.markdown("**🎨 Available Visualizations:**")
                    
                    chart_tabs = []
                    chart_names = []
                    
                    chart_mapping = {
                        "bar": "📊 Bar Chart",
                        "line": "📈 Line Chart", 
                        "pie": "🥧 Pie Chart",
                        "histogram": "📋 Histogram",
                        "scatter": "⚡ Scatter Plot"
                    }
                    
                    for chart_type, chart_title in chart_mapping.items():
                        if chart_type in chart_analysis["charts"]:
                            chart_tabs.append(chart_title)
                            chart_names.append(chart_type)
                    
                    if chart_tabs:
                        chart_sub_tabs = st.tabs(chart_tabs)
                        for i, (tab, chart_name) in enumerate(zip(chart_sub_tabs, chart_names)):
                            with tab:
                                st.plotly_chart(chart_analysis["charts"][chart_name], width="stretch")
                else:
                    st.info("📋 This data is not suitable for visualization.")
                    st.markdown("**💡 For better charts, try queries that return:**")
                    st.markdown("- Numerical values (amounts, counts, averages)")
                    st.markdown("- Categories (customer types, account types)")
                    st.markdown("- Time-based data (dates, months)")
                    st.markdown("- Multiple columns for comparisons")
            
        else:
            # No data case - show execution time
            execution_time = result.get("execution_time", 0)
            st.info(f"Query executed successfully but returned no data (executed in {execution_time:.3f}s)")

    def render_history_tab(self):
        """Render the history tab"""
        col_title, col_clear_history = st.columns([3, 1])
        with col_title:
            st.markdown("### 📝 Query History")
        with col_clear_history:
            if st.button("🗑️ Clear History", key="clear_history"):
                st.session_state["query_results"] = []
                st.success("History cleared!")
                st.rerun()
        
        if not st.session_state.get("query_results"):
            st.info("No query history yet. Execute some queries to see them here!")
            return
            
        total_queries = len(st.session_state['query_results'])
        successful_queries = len([q for q in st.session_state['query_results'] if q.get('status') == 'success'])
        failed_queries = total_queries - successful_queries
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Queries", total_queries)
        with col2:
            st.metric("✅ Successful", successful_queries)
        with col3:
            st.metric("❌ Failed", failed_queries)
        
        st.markdown("---")
        
        # Show last 10 queries in reverse order (most recent first)
        recent_queries = list(reversed(st.session_state["query_results"][-10:]))
        
        for i, query_result in enumerate(recent_queries):
            status_icon = "✅" if query_result.get("status") == "success" else "❌"
            query_text = query_result.get('query', 'Unknown')[:60]
            timestamp = query_result.get('timestamp', 'Unknown time')
            
            with st.expander(f"{status_icon} **Query #{len(st.session_state['query_results']) - i}** - {query_text}... | {timestamp}"):
                st.markdown("**🤔 Original Question:**")
                st.write(f"_{query_result.get('query', 'Unknown')}_")
                
                if query_result.get('sql'):
                    st.markdown("**⚙️ Generated SQL:**")
                    st.code(query_result['sql'], language="sql")
                
                if query_result.get('explanation'):
                    st.markdown("**🔍 Explanation:**")
                    st.write(query_result['explanation'])
                
                if query_result.get("status") == "success":
                    row_count = query_result.get('row_count', 0)
                    st.success(f"✅ **Success:** Returned {row_count} rows")
                    
                    if query_result.get('data') and len(query_result['data']) > 0:
                        st.markdown("**📊 Sample Results:**")
                        sample_data = query_result['data'][:3]
                        st.dataframe(sample_data, width="stretch")
                        if len(query_result['data']) > 3:
                            st.caption(f"... and {len(query_result['data']) - 3} more rows")
                else:
                    if query_result.get('error'):
                        st.error(f"❌ **Error:** {query_result['error']}")
                    if query_result.get('suggestion'):
                        st.info(f"💡 **Suggestion:** {query_result['suggestion']}")
                
                st.caption(f"🕒 Executed at: {timestamp}")

    def run(self):
        # Page config
        st.set_page_config(
            page_title="AI-Powered Financial Query System",
            page_icon="🏦",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Render styles
        self.render_styles()
        
        # Enhanced Header with integrated status indicators
        db_status = st.session_state['database_connection_status']
        ai_status = st.session_state['ai_agent_status'] 
        has_errors = bool(st.session_state["error_messages"])
        render_header(db_status, ai_status, has_errors)
        
        # Main tabs
        main_tab, history_tab, explorer_tab = st.tabs(["🏦 Query Assistant", "📝 History", "🗃️ Database"])
        
        with main_tab:
            # Create a three-column layout with visible vertical separator
            col_samples, col_separator, col_query = st.columns([1.5, 0.1, 3.5])
            
            with col_samples:
                st.markdown("### 📋 Quick Start")
                st.markdown('<p style="font-size: 13px; color: #6b7280; margin-bottom: 0.5rem;"><em>💡 Click any query to populate the main text area</em></p>', unsafe_allow_html=True)
                self.render_compact_sample_queries()
            
            with col_separator:
                # Create an elegant, fine vertical separator that extends with content
                st.markdown("""
                    <div style="
                        height: 100vh;
                        max-height: 800px;
                        width: 1px;
                        background: linear-gradient(180deg, #667eea, #764ba2, #667eea);
                        margin: 10px auto;
                        border-radius: 1px;
                        box-shadow: 0 0 3px rgba(102, 126, 234, 0.2);
                        position: relative;
                        overflow: hidden;
                    ">
                        <div style="
                            position: absolute;
                            top: 0;
                            left: 0;
                            right: 0;
                            height: 100%;
                            background: linear-gradient(180deg, transparent, rgba(255,255,255,0.3), transparent);
                            animation: moveVertical 4s infinite;
                        "></div>
                    </div>
                    <style>
                    @keyframes moveVertical {
                        0% { transform: translateY(-100%); }
                        100% { transform: translateY(100%); }
                    }
                    </style>
                """, unsafe_allow_html=True)
            
            self.render_query_execution_ui(col_query)
        
        with history_tab:
            self.render_history_tab()
        
        with explorer_tab:
            st.markdown("### 🗃️ Database Schema")
            render_database_explorer(self.db_manager)

# --- Main Application ---
if __name__ == "__main__":
    app = BankingApp()
    app.run()
