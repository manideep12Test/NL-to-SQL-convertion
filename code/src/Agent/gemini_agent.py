
# Required imports for banking NL-to-SQL agent using LangChain and Google Gemini
import os
import logging
import re
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import sqlite3

from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.agents import AgentType
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

class GeminiAgent:
    """
    GeminiAgent: Uses LangChain with Google Gemini Pro to convert natural language banking queries to SQL.
    Features:
    - Banking-specific prompt engineering with token optimization
    - Conversation history/context with smart compression
    - SQL validation
    - Robust error handling/logging
    - Structured responses
    - Token usage monitoring and optimization
    """
    # Optimized SYSTEM_PROMPT for token efficiency
    SYSTEM_PROMPT = """Expert SQL generator for banking DB. Convert NL to SELECT queries only.

Schema (use EXACT names):
customers(id,email,phone,address,first_name,last_name,date_of_birth,gender,national_id,created_at,updated_at,branch_id)
accounts(id,customer_id,account_number,type,balance,opened_at,interest_rate,status,branch_id,created_at,updated_at)
transactions(id,account_id,transaction_date,amount,type,description,status,created_at,updated_at,employee_id)
branches(id,name,address,city,state,zip_code,manager_id,created_at,updated_at)
employees(id,branch_id,name,email,phone,position,hire_date,salary,created_at,updated_at)

Rules:
1. SELECT only, end with LIMIT 1000
2. Use aliases: c(customers), a(accounts), t(transactions), e(employees), b(branches)
3. customers: first_name+last_name (NOT name), employees: name column exists
4. Date format: YYYY-MM-DD, use transaction_date for transactions
5. JOIN tables when needed, qualify ambiguous columns (t.type, a.type, etc.)
6. LIKE with % for name searches
"""
    
    def __init__(self, db_path: str, api_key_env: str = "GOOGLE_API_KEY"):
        self.logger = logging.getLogger("GeminiAgent")
        self.logger.setLevel(logging.INFO)
        self.conversation_history: List[Dict[str, Any]] = []
        self.token_usage_stats = {"total_tokens": 0, "queries_processed": 0}
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            raise ValueError(f"Google API key not found in environment variable: {api_key_env}")
        self.db_path = db_path
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}", sample_rows_in_table_info=3)
        
        # Use the current Gemini model name (as of 2025)
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash", 
                temperature=0.1, 
                convert_system_message_to_human=True, 
                google_api_key=self.api_key
            )
            self.model_name = "gemini-1.5-flash"
            self.logger.info("Successfully initialized with gemini-1.5-flash")
        except Exception as e:
            self.logger.warning(f"Failed with gemini-1.5-flash, trying gemini-1.5-pro: {e}")
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-pro", 
                    temperature=0.1, 
                    convert_system_message_to_human=True, 
                    google_api_key=self.api_key
                )
                self.model_name = "gemini-1.5-pro"
                self.logger.info("Successfully initialized with gemini-1.5-pro")
            except Exception as e2:
                self.logger.error(f"Failed with all model names: {e2}")
                raise RuntimeError(f"Failed to initialize Gemini model. Original error: {e}")
        
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            verbose=False,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            handle_parsing_errors=True,
            max_iterations=3
        )

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (approximate: 1 token ≈ 4 characters for English).
        """
        return len(text.split()) + len(text) // 4

    def get_relevant_schema(self, user_input: str) -> str:
        """
        Smart schema filtering based on query content to minimize tokens.
        Only includes tables that are likely relevant to the query.
        """
        user_lower = user_input.lower()
        
        # Table detection keywords
        table_keywords = {
            'customers': ['customer', 'client', 'name', 'email', 'phone', 'address', 'birth', 'gender'],
            'accounts': ['account', 'balance', 'saving', 'checking', 'credit', 'interest', 'opened'],
            'transactions': ['transaction', 'deposit', 'withdrawal', 'transfer', 'payment', 'amount', 'recent'],
            'employees': ['employee', 'staff', 'manager', 'position', 'hire', 'salary', 'work'],
            'branches': ['branch', 'office', 'location', 'city', 'state', 'zip']
        }
        
        # Detect relevant tables
        relevant_tables = set()
        for table, keywords in table_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                relevant_tables.add(table)
        
        # If no specific tables detected, include all (fallback)
        if not relevant_tables:
            relevant_tables = set(table_keywords.keys())
        
        # Add related tables based on common joins
        if 'accounts' in relevant_tables:
            relevant_tables.add('customers')  # accounts usually need customer info
        if 'transactions' in relevant_tables:
            relevant_tables.add('accounts')   # transactions need account info
        if 'employees' in relevant_tables:
            relevant_tables.add('branches')   # employees are linked to branches
            
        # Build optimized schema string
        schema_parts = []
        table_schemas = {
            'customers': 'customers(id,first_name,last_name,email,phone,branch_id)',
            'accounts': 'accounts(id,customer_id,type,balance,status,branch_id)',
            'transactions': 'transactions(id,account_id,transaction_date,amount,type,description,status)',
            'employees': 'employees(id,branch_id,name,position,salary)',
            'branches': 'branches(id,name,address,city,state)'
        }
        
        for table in sorted(relevant_tables):
            if table in table_schemas:
                schema_parts.append(table_schemas[table])
        
        return "Schema: " + ", ".join(schema_parts)

    def compress_context(self, context: Optional[Dict[str, Any]]) -> str:
        """
        Compress conversation context to minimize tokens while preserving key information.
        """
        if not context:
            return ""
            
        compressed_parts = []
        
        if context.get('previous_query'):
            compressed_parts.append(f"Prev: {context['previous_query'][:50]}...")
            
        if context.get('clarifications'):
            compressed_parts.append(f"User said: {context['clarifications'][:30]}...")
            
        return "Context: " + " | ".join(compressed_parts) if compressed_parts else ""

    def log_token_usage(self, prompt: str, response: str):
        """
        Log and track token usage for monitoring and optimization.
        """
        prompt_tokens = self.estimate_tokens(prompt)
        response_tokens = self.estimate_tokens(response)
        total_tokens = prompt_tokens + response_tokens
        
        self.token_usage_stats["total_tokens"] += total_tokens
        self.token_usage_stats["queries_processed"] += 1
        
        avg_tokens = self.token_usage_stats["total_tokens"] / self.token_usage_stats["queries_processed"]
        
        self.logger.info(f"Token usage - Prompt: {prompt_tokens}, Response: {response_tokens}, Total: {total_tokens}")
        self.logger.info(f"Running average: {avg_tokens:.1f} tokens per query")

    def process_query(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point: processes a user query, returns structured response.
        Now supports follow-up questions for ambiguity resolution.
        """
        self.logger.info(f"Processing query: {user_input}")
        self.conversation_history.append({"user": user_input})
        
        # First check if this query is ambiguous and needs clarification
        self.logger.info("Checking for ambiguity...")
        ambiguity_check = self.check_ambiguity(user_input, context)
        self.logger.info(f"Ambiguity check result: {ambiguity_check}")
        
        if ambiguity_check["is_ambiguous"]:
            self.logger.info("Query is ambiguous, returning clarification needed")
            response = {
                "type": "clarification_needed",
                "sql": None,
                "explanation": ambiguity_check["explanation"],
                "follow_up_questions": ambiguity_check["questions"],
                "confidence": 0.3,
                "result": None
            }
            self.conversation_history.append({"agent": response})
            return response
        
        self.logger.info("Query is clear, proceeding with SQL generation")
        # Proceed with normal SQL generation if not ambiguous
        sql_result = self.get_sql_from_nl(user_input, context)
        if sql_result["type"] == "success":
            validated_sql = self.validate_sql(sql_result["sql"])
            if validated_sql["type"] == "success":
                exec_result = self.validate_and_execute(validated_sql["sql"])
                response = {
                    "type": "success",
                    "sql": validated_sql["sql"],
                    "explanation": exec_result.get("explanation", ""),
                    "confidence": sql_result.get("confidence", 0.9),
                    "result": exec_result.get("result", [])
                }
            else:
                response = {
                    "type": "error",
                    "sql": sql_result["sql"],
                    "explanation": validated_sql["message"],
                    "confidence": 0.5,
                    "result": None
                }
        else:
            response = {
                "type": "error",
                "sql": None,
                "explanation": sql_result["message"],
                "confidence": 0.0,
                "result": None
            }
        self.conversation_history.append({"agent": response})
        return response

    def get_token_usage_stats(self) -> Dict[str, Any]:
        """
        Get current token usage statistics for monitoring and optimization.
        """
        if self.token_usage_stats["queries_processed"] == 0:
            return {
                "total_tokens": 0,
                "queries_processed": 0,
                "average_tokens_per_query": 0,
                "efficiency_rating": "No data"
            }
        
        avg_tokens = self.token_usage_stats["total_tokens"] / self.token_usage_stats["queries_processed"]
        
        # Rate efficiency based on average tokens per query
        if avg_tokens < 500:
            efficiency = "Excellent"
        elif avg_tokens < 800:
            efficiency = "Good"  
        elif avg_tokens < 1200:
            efficiency = "Fair"
        else:
            efficiency = "Poor"
            
        return {
            "total_tokens": self.token_usage_stats["total_tokens"],
            "queries_processed": self.token_usage_stats["queries_processed"],
            "average_tokens_per_query": round(avg_tokens, 1),
            "efficiency_rating": efficiency
        }

    def check_ambiguity(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check if a user query is ambiguous and generate clarifying questions.
        """
        # If we have ANY context (meaning user clicked "Continue with Query"), skip ambiguity check
        # This handles both cases: user provided clarifications OR user chose to proceed with defaults
        if context and "clarifications" in context:
            self.logger.info(f"Skipping ambiguity check - user clicked continue button. Clarifications: {context.get('clarifications', {})}")
            return {"is_ambiguous": False, "explanation": "Query enhanced with user clarifications or proceeding with smart defaults", "questions": []}
        
        # OPTIMIZED: Use simple rule-based check instead of AI for token efficiency
        self.logger.info(f"Checking ambiguity for: {user_input} (using optimized rule-based check)")
        return self._simple_ambiguity_check(user_input)
        
        # Original AI-powered check (commented out for testing)
        """
        try:
            self.logger.info(f"Checking ambiguity for: {user_input}")
            
            ambiguity_prompt = f\"\"\"
You are an expert banking assistant. Analyze this user query for ambiguity and determine if clarifying questions are needed.

You are an expert banking assistant. Analyze this user query for ambiguity and determine if clarifying questions are needed.

Banking Database Schema:
- customers: id, first_name, last_name, email, phone, address, date_of_birth, gender, national_id, branch_id
- accounts: id, customer_id, account_number, type (checking/savings/credit), balance, opened_at, interest_rate, status, branch_id
- transactions: id, account_id, type (deposit/withdrawal/transfer), amount, transaction_date, description, status, employee_id
- branches: id, name, address, city, state, zip_code, manager_id  
- employees: id, branch_id, name, email, phone, position, hire_date, salary

User Query: "{user_input}"

Context from previous conversation: {context or "None"}

Analyze if this query is ambiguous and needs clarification. Consider:
1. Missing time periods (e.g., "recent transactions" - how recent?)
2. Unclear amounts (e.g., "large transactions" - how large?)
3. Ambiguous names (e.g., "John" - which John?)
4. Missing account types (e.g., "my balance" - which account?)
5. Unclear transaction types
6. Vague location references

Respond in this exact JSON format:
{{
    "is_ambiguous": true/false,
    "explanation": "Brief explanation of why it's ambiguous or clear",
    "questions": ["Question 1?", "Question 2?", "Question 3?"]
}}

Only mark as ambiguous if clarification would significantly improve the query results.
\"\"\"

            self.logger.info("Calling LLM for ambiguity check...")
            response = self.llm.invoke(ambiguity_prompt)
            response_text = response.content.strip()
            self.logger.info(f"LLM response: {response_text}")
            
            # Try to parse JSON response
            import json
            try:
                if "```json" in response_text:
                    json_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_text = response_text.split("```")[1].strip()
                else:
                    json_text = response_text
                
                result = json.loads(json_text)
                
                # Validate the response structure
                if "is_ambiguous" in result and "explanation" in result and "questions" in result:
                    self.logger.info(f"AI ambiguity check result: {result}")
                    return result
                else:
                    # Fallback to no ambiguity if parsing fails
                    self.logger.warning("AI response missing required fields, falling back to simple check")
                    return self._simple_ambiguity_check(user_input)
                    
            except json.JSONDecodeError as e:
                # If JSON parsing fails, fall back to simple heuristics
                self.logger.warning(f"JSON parsing failed: {e}, falling back to simple check")
                return self._simple_ambiguity_check(user_input)
                
        except Exception as e:
            self.logger.warning(f"Ambiguity check failed: {e}, falling back to simple check")
            return self._simple_ambiguity_check(user_input)
        """

    def _simple_ambiguity_check(self, user_input: str) -> Dict[str, Any]:
        """
        Enhanced rule-based ambiguity detection with smart question prioritization.
        Returns only the most relevant questions, not all possible ones.
        """
        user_lower = user_input.lower()
        
        # Comprehensive ambiguity patterns with prioritized questions
        ambiguity_patterns = {
            # Time-related ambiguity (highest priority)
            "recent": {
                "questions": [
                    "How recent? (e.g., 'last 7 days', 'last month', 'this year')",
                    "Do you want the most recent items first?"
                ],
                "explanation": "I need to know what time period you consider 'recent'."
            },
            "old": {
                "questions": [
                    "How far back should I look? (e.g., '6 months ago', 'last year', 'older than 2 years')",
                    "Should I include closed/inactive records?"
                ],
                "explanation": "Please specify what time period you consider 'old'."
            },
            
            # Amount-related ambiguity
            "large": {
                "questions": [
                    "What amount would you consider large? (e.g., 'over $1,000', 'more than $10,000')",
                    "Are you looking at individual transactions or total amounts?"
                ],
                "explanation": "I need to know what dollar amount you consider 'large'."
            },
            "small": {
                "questions": [
                    "What's your threshold for small amounts? (e.g., 'under $100', 'less than $500')"
                ],
                "explanation": "Please specify what you consider a 'small' amount."
            },
            "high": {
                "questions": [
                    "What range do you consider high? (e.g., 'over $50,000', 'more than $100,000')"
                ],
                "explanation": "Please clarify what threshold you consider 'high'."
            },
            "low": {
                "questions": [
                    "What range do you consider low? (e.g., 'under $1,000', 'less than $5,000')"
                ],
                "explanation": "Please specify what you consider 'low' values."
            },
            
            # Customer identification ambiguity
            "john": {
                "questions": [
                    "Which John? (Please provide last name or customer ID)",
                    "Is this first name, last name, or part of the full name?"
                ],
                "explanation": "There may be multiple customers named John - I need more specific identification."
            },
            "smith": {
                "questions": [
                    "Which Smith? (Please provide first name or customer ID)"
                ],
                "explanation": "Smith is a common name - please provide more details for identification."
            },
            "my": {
                "questions": [
                    "Which account? (e.g., 'checking', 'savings', 'all accounts')"
                ],
                "explanation": "Please specify which of your accounts you're asking about."
            },
            
            # Quantity-related ambiguity
            "many": {
                "questions": [
                    "How many would you consider 'many'? (e.g., 'more than 10', 'over 50')"
                ],
                "explanation": "Please specify what quantity you consider 'many'."
            },
            "few": {
                "questions": [
                    "What number range is 'few' to you? (e.g., '1-5', 'less than 10')"
                ],
                "explanation": "Please clarify what you consider 'few' items."
            },
            
            # Transaction type ambiguity (lower priority)
            "transactions": {
                "questions": [
                    "What type of transactions? (e.g., 'all types', 'deposits only', 'withdrawals')"
                ],
                "explanation": "There are different types of transactions - please specify which ones you're interested in."
            }
        }
        
        # Find the most relevant ambiguity
        detected_ambiguity = None
        primary_term = None
        
        # Priority order: time terms first, then amounts, then others
        priority_terms = ["recent", "old", "large", "small", "high", "low", "my", "john", "smith", "many", "few", "transactions"]
        
        for term in priority_terms:
            if term in user_lower and term in ambiguity_patterns:
                detected_ambiguity = ambiguity_patterns[term]
                primary_term = term
                break
        
        # If ambiguity found, return only the most relevant questions
        if detected_ambiguity:
            return {
                "is_ambiguous": True,
                "explanation": detected_ambiguity["explanation"],
                "questions": detected_ambiguity["questions"][:2]  # Limit to 2 most important questions
            }
        
        # Additional context-based checks for very short queries
        word_count = len(user_input.split())
        if word_count <= 3 and not any(word in user_lower for word in ["show", "find", "list", "display"]):
            return {
                "is_ambiguous": True,
                "explanation": "Your query is quite brief - a bit more detail would help me give you better results.",
                "questions": [
                    "What specific information are you looking for?",
                    "Any particular time period or amount range?"
                ]
            }
        
        # No ambiguity detected
        return {"is_ambiguous": False, "explanation": "Query appears clear", "questions": []}

    def get_sql_from_nl(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Converts natural language to SQL using direct LLM approach for better reliability.
        Now supports context from previous conversation for better query resolution.
        Returns: {type, sql, message, confidence}
        """
        try:
            self.logger.info(f"Converting to SQL: {user_input}")
            
            # Use smart schema filtering instead of full schema
            relevant_schema = self.get_relevant_schema(user_input)
            
            # Compress context instead of including full details
            compressed_context = self.compress_context(context)
            
            # Build optimized prompt with token-efficient structure
            prompt_parts = [
                self.SYSTEM_PROMPT,
                relevant_schema,
                compressed_context,
                f"Q: {user_input}",
                "SQL:"
            ]
            
            # Filter out empty parts and join efficiently
            prompt = "\n".join(part for part in prompt_parts if part.strip())
            
            self.logger.info(f"Optimized prompt tokens (estimated): {self.estimate_tokens(prompt)}")
            
            # Use the LLM directly with optimized prompt
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Log token usage for monitoring
            self.log_token_usage(prompt, response_text)
            
            self.logger.info(f"Raw LLM Response: {response_text}")
            
            # Clean up the response to extract SQL
            sql_query = response_text.strip()
            
            # Remove code block markers if present
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].strip()
            
            self.logger.info(f"SQL after cleaning code blocks: {sql_query}")
            
            # Remove any extra text and find the SELECT statement
            lines = sql_query.split('\n')
            clean_lines = []
            found_select = False
            
            for line in lines:
                line = line.strip()
                if line.upper().startswith('SELECT'):
                    found_select = True
                    clean_lines.append(line)
                elif found_select and line:
                    # Continue collecting lines that are part of the SQL
                    if any(keyword in line.upper() for keyword in ['FROM', 'WHERE', 'JOIN', 'ON', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']):
                        clean_lines.append(line)
                    elif line.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
                        # Stop at next SQL statement
                        break
                    elif line and not line.startswith(('#', '//', '--')):
                        # Include non-comment lines
                        clean_lines.append(line)
            
            if clean_lines:
                sql_query = ' '.join(clean_lines)
            
            self.logger.info(f"SQL after extracting SELECT: {sql_query}")
            
            # Final cleanup - remove multiple spaces and ensure single line
            sql_query = ' '.join(sql_query.split()).strip().rstrip(';')
            
            self.logger.info(f"SQL after final cleanup: {sql_query}")
            
            # Validate that we have a proper SQL query
            if sql_query and sql_query.upper().startswith('SELECT'):
                # CRITICAL FIX: Replace any 'date' column references with 'transaction_date'
                # This is a safety net to catch any remaining incorrect column names
                # Be very careful not to replace SQL date functions like date('now')
                
                # First, let's see what we're working with
                self.logger.info(f"Original SQL before column fix: {sql_query}")
                
                # CRITICAL FIX: Handle column name corrections more precisely
                # This prevents date_of_birth from being corrupted to transaction_date_of_birth
                self.logger.info(f"Original SQL before column fix: {sql_query}")
                
                # Step 1: Temporarily protect date_of_birth and other compound date columns
                protected_columns = {
                    'date_of_birth': 'TEMP_PROTECT_DOB',
                    'birth_date': 'TEMP_PROTECT_BD',
                    'hire_date': 'TEMP_PROTECT_HD',
                    'opened_at': 'TEMP_PROTECT_OA'
                }
                
                # Protect compound date columns
                for original, placeholder in protected_columns.items():
                    sql_query = sql_query.replace(original, placeholder)
                
                # Step 2: Now safely replace standalone 'date' references with 'transaction_date'
                # Only replace when 'date' appears as a standalone column reference
                import re
                # Replace 'date' when it's a standalone word (not part of another word)
                sql_query = re.sub(r'\bdate\b', 'transaction_date', sql_query, flags=re.IGNORECASE)
                
                # Step 3: Restore protected columns
                for original, placeholder in protected_columns.items():
                    sql_query = sql_query.replace(placeholder, original)
                
                # Step 4: Preserve SQL date functions (fix any that got changed)
                sql_query = sql_query.replace("transaction_date('now'", "date('now'")
                sql_query = sql_query.replace("transaction_date(", "date(")
                sql_query = sql_query.replace("strftransaction_date(", "strfdate(")
                
                # Ensure it has a LIMIT clause for safety - but be smart about it
                if 'LIMIT' not in sql_query.upper():
                    sql_query = self._add_limit_safely(sql_query)
                
                self.logger.info(f"Generated SQL (after column fix): {sql_query}")
                return {"type": "success", "sql": sql_query, "confidence": 0.9}
            else:
                error_msg = f"Could not generate valid SQL query. LLM returned: {response_text[:200]}..."
                self.logger.error(error_msg)
                return {"type": "error", "message": error_msg, "confidence": 0.0}
                
        except Exception as e:
            self.logger.error(f"Error in get_sql_from_nl: {e}")
            
            # Check if it's a quota/API error and try fallback
            error_str = str(e).lower()
            if "quota" in error_str or "429" in error_str or "resourceexhausted" in error_str:
                # Try to match common patterns with predefined queries
                fallback_sql = self._get_fallback_query(user_input)
                if fallback_sql:
                    self.logger.info(f"Using fallback query due to API quota limit: {fallback_sql}")
                    return {"type": "success", "sql": fallback_sql, "confidence": 0.7}
            
            return {"type": "error", "message": f"SQL generation failed: {str(e)}", "confidence": 0.0}

    def _add_limit_safely(self, sql_query: str) -> str:
        """
        Safely add LIMIT clause to SQL query, handling complex queries properly.
        """
        sql_upper = sql_query.upper()
        sql_clean = sql_query.strip()
        
        # If it already has LIMIT, don't add another
        if 'LIMIT' in sql_upper:
            return sql_clean
        
        # Remove any trailing semicolons
        sql_clean = sql_clean.rstrip(';').strip()
        
        # Handle ORDER BY clauses specially
        if 'ORDER BY' in sql_upper:
            # Split at ORDER BY and add LIMIT after
            order_by_pos = sql_upper.find('ORDER BY')
            before_order = sql_query[:order_by_pos].strip()
            order_clause = sql_query[order_by_pos:].strip()
            return f"{before_order} {order_clause} LIMIT 1000"
        
        # For all other cases, just append LIMIT
        return f"{sql_clean} LIMIT 1000"

    def validate_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Validates SQL for banking schema, only allows SELECT, checks table names.
        Note: LIMIT is already handled in get_sql_from_nl method.
        """
        try:
            sql = sql_query.strip()
            sql_lower = sql.lower()
            
            # Check if it's a SELECT statement
            if not sql_lower.startswith("select"):
                return {"type": "error", "message": "Only SELECT operations are allowed"}
            
            # Check for dangerous operations
            write_ops = ["insert", "update", "delete", "drop", "alter", "create", "truncate"]
            if any(f" {op} " in f" {sql_lower} " for op in write_ops):
                return {"type": "error", "message": "Only SELECT operations are allowed"}
            
            # Check for valid table references
            valid_tables = ["customers", "accounts", "transactions", "branches", "employees"]
            if not any(table in sql_lower for table in valid_tables):
                return {"type": "error", "message": "Query must reference at least one valid table"}
            
            # Just return the SQL as-is since LIMIT is already handled
            return {"type": "success", "sql": sql}
        except Exception as e:
            self.logger.error(f"SQL validation error: {e}")
            return {"type": "error", "message": str(e)}

    def validate_and_execute(self, sql_query: str) -> Dict[str, Any]:
        """
        Executes validated SQL and returns results and explanation.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
            explanation = f"Executed SQL: {sql_query}"
            return {"result": result, "explanation": explanation}
        except Exception as e:
            self.logger.error(f"Execution error: {e}")
            return {"result": None, "explanation": str(e)}
        finally:
            try:
                conn.close()
            except:
                pass

    def get_context(self) -> Dict[str, Any]:
        """
        Returns current conversation context/history.
        """
        return {"history": self.conversation_history}

    def follow_up(self, user_input: str) -> Dict[str, Any]:
        """
        Handles follow-up questions using context.
        """
        context = self.get_context()
        prompt = f"{self.SYSTEM_PROMPT}\nPrevious: {context['history']}\nQ: {user_input}\nA:"
        return self.process_query(prompt)

    def _get_fallback_query(self, user_input: str) -> Optional[str]:
        """
        Provides fallback SQL queries when API is unavailable.
        Returns basic queries for common banking questions.
        """
        user_lower = user_input.lower()
        
        # Common banking query patterns with fallback SQL
        fallback_patterns = {
            "customers": "SELECT * FROM customers LIMIT 10",
            "accounts": "SELECT * FROM accounts LIMIT 10",
            "transactions": "SELECT * FROM transactions ORDER BY date DESC LIMIT 10",
            "balance": "SELECT c.name, a.type, a.balance FROM customers c JOIN accounts a ON c.id = a.customer_id ORDER BY a.balance DESC LIMIT 10",
            "recent": "SELECT t.*, c.name FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN customers c ON a.customer_id = c.id ORDER BY t.date DESC LIMIT 10",
            "high": "SELECT c.name, a.type, a.balance FROM customers c JOIN accounts a ON c.id = a.customer_id WHERE a.balance > 50000 ORDER BY a.balance DESC LIMIT 10",
            "employee": "SELECT e.*, b.name as branch_name FROM employees e JOIN branches b ON e.branch_id = b.id LIMIT 10",
            "branch": "SELECT * FROM branches LIMIT 10",
            "monthly": "SELECT strftime('%Y-%m', date) as month, COUNT(*) as transaction_count, SUM(amount) as total_amount FROM transactions GROUP BY strftime('%Y-%m', date) ORDER BY month DESC LIMIT 12",
            "average": "SELECT AVG(balance) as avg_balance, COUNT(*) as account_count FROM accounts",
        }
        
        # Try to match patterns
        for pattern, sql in fallback_patterns.items():
            if pattern in user_lower:
                return sql
        
        # Default fallback - show recent transactions
        return "SELECT t.*, c.name as customer_name FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN customers c ON a.customer_id = c.id ORDER BY t.date DESC LIMIT 10"

# Example usage:
# agent = GeminiAgent(db_path="../data/banking.db")
# result = agent.process_query("Show me all transactions from last week")
# print(result)
