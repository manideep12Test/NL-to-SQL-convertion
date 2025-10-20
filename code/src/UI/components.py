import streamlit as st
import plotly.express as px
from datetime import datetime
from typing import List, Dict, Any
from Agent.gemini_agent import GeminiAgent
from Agent.sql_validator import SQLValidator

# --- GeminiAgent and SQLValidator Integration ---
def process_user_query(user_input: str, db_path: str, agent: GeminiAgent = None, validator: SQLValidator = None):
    """
    Integrates GeminiAgent and SQLValidator for banking queries.
    Returns: dict with SQL, explanation, confidence, result, error
    """
    if agent is None:
        agent = GeminiAgent(db_path)
    if validator is None:
        validator = SQLValidator(db_path)
    agent_response = agent.process_query(user_input)
    sql = agent_response.get("sql")
    if not sql:
        return {"error": agent_response.get("explanation", "No SQL generated.")}
    validation = validator.validate_query(sql)
    if not validation.get("valid", False):
        return {"error": validation.get("message", "SQL validation failed."), "suggestion": validation.get("suggestion", "")}
    return {
        "sql": sql,
        "explanation": agent_response.get("explanation"),
        "confidence": agent_response.get("confidence"),
        "result": agent_response.get("result"),
        "validation": validation
    }


# --- UI Styling Constants ---
BANKING_BLUE = "#0055A4"
BANKING_GRAY = "#F5F7FA"
BANKING_WHITE = "#FFFFFF"
BANKING_FONT = "Roboto, Arial, sans-serif"

__all__ = [
    "render_chat_interface",
    "apply_custom_styles",
    "render_header",
    "render_sidebar",
    "render_database_explorer",
    "render_query_results",
    "render_sample_queries"
]

# --- 1. Enhanced Header with Beautiful Styling ---
def render_header(db_status="Disconnected", ai_status="Inactive", has_errors=False):
    # Create status badge classes
    db_badge_class = "status-connected" if db_status == "Connected" else "status-disconnected"
    ai_badge_class = "status-connected" if ai_status == "Active" else "status-disconnected"
    system_badge_class = "status-disconnected" if has_errors else "status-connected"
    system_text = "Issues" if has_errors else "OK"
    
    # CSS styles
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        .bank-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem 1.5rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }
        
        .bank-header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: rotate(45deg);
            animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
            100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
        }
        
        .bank-header h1 {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 2.5rem;
            color: white;
            margin: 0;
            display: flex;
            align-items: center;
            position: relative;
            z-index: 2;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .bank-header .emoji {
            font-size: 3rem;
            margin-right: 1rem;
            filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));
        }
        
        .bank-header .subtitle {
            font-family: 'Poppins', sans-serif;
            font-weight: 300;
            font-size: 1rem;
            color: rgba(255,255,255,0.9);
            margin-left: auto;
            text-align: right;
            line-height: 1.2;
            position: relative;
            z-index: 2;
        }
        
        .bank-header .subtitle .highlight {
            font-weight: 600;
            color: #FFD700;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }
        
        .status-indicators {
            display: flex;
            justify-content: flex-end;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        
        .status-badge {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 20px;
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            font-weight: 600;
            backdrop-filter: blur(15px);
            transition: all 0.3s ease;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        
        .status-connected {
            color: #ffffff;
            border-color: rgba(255, 255, 255, 0.4);
            background: rgba(0, 0, 0, 0.6);
        }
        
        .status-disconnected {
            color: #ffffff;
            border-color: rgba(255, 255, 255, 0.4);
            background: rgba(0, 0, 0, 0.6);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .bank-header h1 {
                font-size: 2rem;
                flex-direction: column;
                text-align: center;
            }
            .bank-header .subtitle {
                margin-left: 0;
                margin-top: 0.5rem;
                text-align: center;
            }
            .bank-header .emoji {
                margin-right: 0;
                margin-bottom: 0.5rem;
            }
            .status-indicators {
                justify-content: center;
                gap: 0.5rem;
            }
            .status-badge {
                font-size: 0.8rem;
                padding: 0.4rem 0.8rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    # HTML content with status indicators
    header_html = f"""
        <div class='bank-header'>
            <h1>
                <span class='emoji'>🏦</span>
                AI-Powered Financial Query System
                <div class='subtitle'>
                    <div class='highlight'>Natural Language to SQL Conversion</div>                   
                </div>
            </h1>
            <div class='status-indicators'>
                <span class='status-badge {db_badge_class}'>
                    🗄️ DB: {db_status}
                </span>
                <span class='status-badge {ai_badge_class}'>
                    🤖 AI: {ai_status}
                </span>
                <span class='status-badge {system_badge_class}'>
                    ⚡ System: {system_text}
                </span>
            </div>
        </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)

# --- 2. Deprecated Chat Interface (replaced with main interface) ---
# This function is kept for backward compatibility but no longer used
def render_chat_interface():
    st.info("🔄 This interface has been modernized! Please use the main Query Assistant tab.")
    
# --- 3. Deprecated Sidebar (replaced with tabs) ---  
# This function is kept for backward compatibility but no longer used
def render_sidebar(db_manager=None):
    st.info("🔄 Sidebar content has been moved to dedicated tabs for better user experience.")

# --- 4. Database Explorer ---
def render_database_explorer(db_manager=None):
    if not db_manager:
        st.warning("Database manager not available")
        return
        
    st.markdown("Explore your banking database structure and sample data")
    
    try:
        tables = db_manager.get_tables()
        if not tables:
            st.info("No tables found in database")
            return
            
        # Use selectbox for table selection instead of tabs to save space
        selected_table = st.selectbox("📋 Select Table", tables, key="table_selector")
        
        if selected_table:
            # Create two columns for better layout
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"#### 📄 {selected_table.title()} - Structure")
                try:
                    columns_info = db_manager.get_table_columns(selected_table)
                    if isinstance(columns_info, list) and columns_info:
                        # Create a more compact table display
                        for col_info in columns_info[:10]:  # Limit to first 10 columns
                            if isinstance(col_info, dict):
                                st.write(f"• **{col_info.get('name', 'Unknown')}** ({col_info.get('type', 'Unknown')})")
                            else:
                                st.write(f"• {col_info}")
                        if len(columns_info) > 10:
                            st.write(f"... and {len(columns_info) - 10} more columns")
                    else:
                        st.dataframe(columns_info, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading columns: {e}")
            
            with col2:
                st.markdown(f"#### 📊 {selected_table.title()} - Sample Data")
                try:
                    sample_data = db_manager.get_sample_data(selected_table, limit=5)
                    if hasattr(sample_data, 'empty') and not sample_data.empty:
                        st.dataframe(sample_data, use_container_width=True)
                    else:
                        st.info("No sample data available")
                except Exception as e:
                    st.error(f"Error loading sample data: {e}")
            
            # Table statistics
            try:
                row_count = db_manager.get_row_count(selected_table)
                st.metric(f"📈 Total Records in {selected_table.title()}", f"{row_count:,}")
            except Exception as e:
                st.write(f"Row count unavailable: {e}")
                
    except Exception as e:
        st.error(f"Error accessing database: {e}")

# --- 5. Query Results ---
def render_query_results(results: List[Dict[str, Any]], sql: str):
    st.markdown("## 📊 Query Results")
    
    # SQL Query in an expandable section
    with st.expander("🔍 View SQL Query", expanded=False):
        st.code(sql, language="sql")
    
    # Results display
    if results:
        st.markdown(f"**Found {len(results)} rows**")
        
        # Download option
        if results:
            import pandas as pd
            df = pd.DataFrame(results)
            csv = df.to_csv(index=False)
            st.download_button(
                "💾 Download CSV",
                data=csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # Results display
    if results:
        # Show results in a responsive table
        st.markdown("### 📄 Data")
        import pandas as pd
        df = pd.DataFrame(results)
        
        # Limit columns shown if too many
        if len(df.columns) > 8:
            st.info(f"Showing first 8 columns out of {len(df.columns)} total columns")
            st.dataframe(df.iloc[:, :8], use_container_width=True, height=400)
            
            with st.expander("🔍 View All Columns"):
                st.dataframe(df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True, height=400)
        
        # Charts section - only show if data is suitable
        if len(results) > 1:
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_columns) >= 1:
                with st.expander("📈 Quick Charts", expanded=False):
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        if len(numeric_columns) >= 1:
                            # Simple bar chart
                            if px:
                                try:
                                    fig = px.bar(
                                        df.head(10),  # Limit to first 10 rows
                                        x=df.columns[0], 
                                        y=numeric_columns[0],
                                        title=f"{numeric_columns[0]} by {df.columns[0]}"
                                    )
                                    fig.update_layout(height=300)
                                    st.plotly_chart(fig, use_container_width=True)
                                except:
                                    st.info("Chart data not suitable for visualization")
                    
                    with chart_col2:
                        if len(numeric_columns) >= 2:
                            # Scatter plot if we have 2+ numeric columns
                            if px:
                                try:
                                    fig = px.scatter(
                                        df.head(20),  # Limit to first 20 rows
                                        x=numeric_columns[0], 
                                        y=numeric_columns[1],
                                        title=f"{numeric_columns[1]} vs {numeric_columns[0]}"
                                    )
                                    fig.update_layout(height=300)
                                    st.plotly_chart(fig, use_container_width=True)
                                except:
                                    st.info("Chart data not suitable for visualization")
    else:
        st.info("💡 No results found for this query. Try modifying your search criteria.")

# --- 6. Sample Queries ---
def render_sample_queries(return_list=False):
    # Enhanced queries for Financial Analysts and Customer Service Representatives
    queries = [
        # Customer Service Representative Queries
        "Show me all transactions for customer with last name 'Smith' in the last 30 days",
        "What is the current account balance for customer John Smith?",
        "Find all transactions over $500 that might be disputed",
        "List all customers with account balances below $100",
        "Show recent deposit and withdrawal history for savings accounts",
        
        # Financial Analyst Queries  
        "What is the total transaction volume by month for the last 6 months?",
        "Show the top 10 customers by total account balance",
        "Find all high-value transactions above $5000 for risk analysis",
        "What is the average transaction amount by transaction type?",
        "Show daily transaction trends for the last 2 weeks",
        "List all accounts with suspicious activity patterns (multiple large withdrawals)",
        
        # Business Intelligence Queries
        "What are the most common transaction types and their frequencies?",
        "Show account growth trends - new accounts opened per month",
        "Find customers with the highest transaction frequency",
        "What is the distribution of account balances across all customers?",
        
        # Quick Access Queries
        "Show me today's transaction summary",
        "List all transactions over $1000 from this week",
        "Find all grocery and retail spending this month",
        "What are the total deposits vs withdrawals for this quarter?"
    ]
    if return_list:
        return queries
    
    # Organize queries by category with improved layout - NO NESTED TABS
    categories = {
        "🏛️ Customer Service": queries[0:5],
        "📊 Financial Analysis": queries[5:11], 
        "📈 Business Intelligence": queries[11:15],
        "⚡ Quick Access": queries[15:19]
    }
    
    # Use expandable sections instead of nested tabs
    for i, (category, category_queries) in enumerate(categories.items()):
        with st.expander(f"{category} ({len(category_queries)} queries)", expanded=(i==0)):
            st.markdown("*Click any query to select it*")
            
            for j, query in enumerate(category_queries):
                # Use expander for long queries to save space
                if len(query) > 80:
                    with st.expander(f"Query {j+1}: {query[:60]}..."):
                        st.write(query)
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if st.button("✅ Select This Query", key=f"{category}_{j}_select", type="primary"):
                                st.session_state["selected_query"] = query
                                st.success("🎯 Query Selected! Switch to '🏦 Query Assistant' tab to execute.")
                                st.rerun()
                        with col2:
                            if st.button("🚀 Execute Now", key=f"{category}_{j}_exec"):
                                st.session_state["selected_query"] = query
                                st.session_state["execute_immediately"] = True
                                st.info("🔄 Executing query...")
                                st.rerun()
                else:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button(f"📄 {query}", key=f"{category}_{j}", help="Click to select this query"):
                            st.session_state["selected_query"] = query
                            st.success("🎯 Query Selected! Switch to '🏦 Query Assistant' tab to execute.")
                            st.rerun()
                    with col2:
                        if st.button("🚀", key=f"{category}_{j}_quick", help="Execute immediately"):
                            st.session_state["selected_query"] = query
                            st.session_state["execute_immediately"] = True
                            st.info("🔄 Executing query...")
                            st.rerun()
    
    # Show global selection status and instructions
    st.markdown("---")
    if st.session_state.get("selected_query"):
        selected_query = st.session_state["selected_query"]
        st.markdown("### 🎯 Currently Selected Query")
        st.success(f"📝 **Selected:** {selected_query[:100]}{'...' if len(selected_query) > 100 else ''}")
        
        # Clear instructions and action buttons
        st.markdown("#### 👆 **Next Steps:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.info("**Option 1:** Click the '🏦 Query Assistant' tab above to execute your query")
        
        with col2:
            if st.button("🚀 Execute Query Now", type="primary", help="Execute the selected query immediately"):
                # Handle immediate execution
                st.session_state["execute_immediately"] = True
                st.info("🔄 Executing your query...")
                st.rerun()
        
        with col3:
            if st.button("❌ Clear", help="Clear the selected query"):
                st.session_state["selected_query"] = None
                st.rerun()
    else:
        st.info("💡 **Tip:** Click any query above to select it, then switch to the '🏦 Query Assistant' tab to execute it!")
    
    # No return value needed - using session state

# --- Styling Helper ---
def apply_custom_styles():
    st.markdown(f"""
        <style>
        body {{ font-family: {BANKING_FONT}; background: {BANKING_GRAY}; }}
        .stButton>button {{ background: {BANKING_BLUE}; color: {BANKING_WHITE}; border-radius:8px; }}
        .stButton>button:hover {{ background: #003366; }}
        .stDataFrame {{ border-radius:8px; box-shadow:0 2px 8px #0001; }}
        </style>
    """, unsafe_allow_html=True)

# --- Error Boundary ---
def render_error_boundary(error: Exception):
    st.error(f"An error occurred: {error}")
    st.write("Please try again or contact support.")

# --- Accessibility Helper ---
def apply_accessibility():
    st.markdown('<div aria-label="Banking NL-to-SQL UI" tabindex="0"></div>', unsafe_allow_html=True)
