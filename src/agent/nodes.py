from pydantic import BaseModel, Field
from agent.state import AgentState
from agent.utils import get_database_schema
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from sqlalchemy import text, inspect
from database.database import *
from database.models import *       
from typing import Literal
from langgraph.types import interrupt, Command

base_url = "http://127.0.0.1:11434/"
model = 'codellama:7b'


class GetCurrentUser(BaseModel):
    current_user: str = Field(
        description="The name of the current user based on the provided user ID."
    )

def get_current_user(state: AgentState, config: RunnableConfig):
    print("Retrieving the current user based on user ID.")
    user_id = config["configurable"].get("current_user_id", None)
    if not user_id:
        state["current_user"] = "User not found"
        print("No user ID provided in the configuration.")
        return state

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == int(user_id)).first()
        if user:
            state["current_user"] = user.name
            print(f"Current user set to: {state['current_user']}")
        else:
            state["current_user"] = "User not found"
            print("User not found in the database.")
    except Exception as e:
        state["current_user"] = "Error retrieving user"
        print(f"Error retrieving user: {str(e)}")
    finally:
        session.close()
    return state

class CheckRelevance(BaseModel):
    relevance: str = Field(
        description="Indicates whether the question is related to the database schema. 'order' or 'not_relevant' or 'menu'."
    )

def check_relevance(state: AgentState, config: RunnableConfig):
    question = state["question"]
    schema = get_database_schema(engine)
    print(f"Checking relevance of the question: {question}")
    system = """You are an assistant that determines whether a given question is related to the following database schema.

Schema:
{schema}

Respond with only "order" or "not_relevant" or "menu".
""".format(schema=schema)
    human = f"Question: {question}"
    check_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", human),
        ]
    )
    llm = ChatOllama(
    base_url=base_url,
    model = model,
    temperature = 0,
)
    structured_llm = llm.with_structured_output(CheckRelevance)
    relevance_checker = check_prompt | structured_llm
    relevance = relevance_checker.invoke({})
    state["relevance"] = relevance.relevance
    print(f"Relevance determined: {state['relevance']}")
    return state

class ConvertToSQL(BaseModel):
    sql_query: str = Field(
        description="The SQL query corresponding to the user's natural language question."
    )

def convert_nl_to_sql(state: AgentState, config: RunnableConfig):
    question = state["question"]
    current_user = state["current_user"]
    schema = get_database_schema(engine)
    print(f"Converting question to SQL for user '{current_user}': {question}")
    if state["relevance"].lower() == "order":
        system = """You are an assistant that converts natural language questions into SQL queries based on the following schema:

    {schema}

    The current user is '{current_user}'. Ensure that all query-related data is scoped to this user.

    Provide only the SQL query without any explanations. Alias columns appropriately to match the expected keys in the result.

    For example, alias 'food.name' as 'food_name' and 'food.price' as 'price'.
    """.format(schema=schema, current_user=current_user)
        convert_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Question: {question}"),
            ]
        )
        llm = ChatOllama(
        base_url=base_url,
        model = model,
        temperature = 0,
    )
        structured_llm = llm.with_structured_output(ConvertToSQL)
        sql_generator = convert_prompt | structured_llm
        result = sql_generator.invoke({"question": question})
        state["sql_query"] = result.sql_query
        print(f"Generated SQL query: {state['sql_query']}")
        return state
    else :
        print(f"Converting menu-related question to SQL: {question}")
        system = """You are an assistant that converts natural language questions about the menu into SQL queries based on the following schema:
    {schema}
    Provide only the SQL query without any explanations. Use only the "food" table, as the customer only wants to see the menu.
    Alias columns appropriately to match the expected keys in the result. For example, alias 'food.name' as 'food_name', 'food.price' as 'price', and 'food.description' as 'food_description'.

    """.format(schema=schema)
        convert_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Question: {question}"),
            ]
        )
        llm = ChatOllama(
        base_url=base_url,
        model = model,
        temperature = 0,
    )
        structured_llm = llm.with_structured_output(ConvertToSQL)
        sql_generator = convert_prompt | structured_llm
        result = sql_generator.invoke({"question": question})
        state["sql_query"] = result.sql_query
        print(f"Generated SQL query for menu: {state['sql_query']}")
        return state
   

def execute_sql(state: AgentState):
    sql_query = state["sql_query"].strip()
    session = SessionLocal()
    print(f"Executing SQL query: {sql_query}")
    try:
        result = session.execute(text(sql_query))
        if sql_query.lower().startswith("select"):
            rows = result.fetchall()
            columns = result.keys()
            if rows:
                if state["relevance"].lower() == "order":
                    header = ", ".join(columns)
                    state["query_rows"] = [dict(zip(columns, row)) for row in rows]
                    print(f"Raw SQL Query Result: {state['query_rows']}")
                    # Format the result for readability
                    data = "; ".join([f"{row.get('food_name', row.get('name'))} for ${row.get('price', row.get('food_price'))}" for row in state["query_rows"]])
                    formatted_result = f"{header}\n{data}"
                else:
                    header = ", ".join(columns)
                    state["query_rows"] = [dict(zip(columns, row)) for row in rows]
                    print(f"Raw SQL Query Result: {state['query_rows']}")
                    # Format the result for readability
                    data = "; ".join([f"{row.get('food_name', row.get('name'))} for ${row.get('price', row.get('food_price'))} description {row.get(('description'), row.get('food_description'))} " for row in state["query_rows"]])
                    formatted_result = f"{header}\n{data}"

            else:
                state["query_rows"] = []
                formatted_result = "No results found."
            state["query_result"] = formatted_result
            state["sql_error"] = False
            print("SQL SELECT query executed successfully.")
        else:
            session.commit()
            state["query_result"] = "The action has been successfully completed."
            state["sql_error"] = False
            print("SQL command executed successfully.")
    except Exception as e:
        state["query_result"] = f"Error executing SQL query: {str(e)}"
        state["sql_error"] = True
        print(f"Error executing SQL query: {str(e)}")
    finally:
        session.close()
    return state

def generate_human_readable_answer(state: AgentState):
    sql = state["sql_query"]
    result = state["query_result"]
    current_user = state["current_user"]
    query_rows = state.get("query_rows", [])
    sql_error = state.get("sql_error", False)
    print("Generating a human-readable answer.")
    system = """You are an assistant that converts SQL query results into clear, natural language responses without including any identifiers like order IDs. Start the response with a friendly greeting that includes the user's name.
    """
    if sql_error:
        # Directly relay the error message
        generate_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    f"""SQL Query:
{sql}

Result:
{result}

Formulate a clear and understandable error message in a single sentence, starting with 'Hello {current_user},' informing them about the issue."""
                ),
            ]
        )
    elif sql.lower().startswith("select"):
        if not query_rows:
            # Handle cases with no orders
            generate_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system),
                    (
                        "human",
                        f"""SQL Query:
{sql}

Result:
{result}
Formulate a clear and understandable answer to the original question in a single sentence, starting with 'Hello {current_user},' and mention that there are no orders found
."""
                    ),
                ]
            )
        elif state["relevance"].lower() == "order":
            # Handle displaying orders
            generate_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system),
                    (
                        "human",
                        f"""SQL Query:
{sql}

Result:
{result}

Formulate a clear and understandable answer to the original question in a single sentence, starting with 'Hello {current_user},' and list each item ordered along with its price. For example: 'Hello Bob, you have ordered Lasagne for $14.0 and Spaghetti Carbonara for $15.0.'"""
                    ),
                ]
            )
        else:
            # Handle displaying menu items
            generate_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system),
                    (
                        "human",
                        f"""SQL Query:
{sql}
Result:
{result}

Formulate a clear and understandable answer to the original question, starting with 'Hello {current_user},' and present the menu items along with their prices in a well-formatted table instead of a single sentence. For example:** **Hello Bob, here is the menu:**
 | Item                | Price  | Description                  |
 |---------------------|--------|------------------------------|
 | food_name           | price  | description                  | 
 | food_name           | price  | description                  |
'"""
                    ),
                ]
            )
    else:
        # Handle non-select queries
        generate_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    f"""SQL Query:
{sql}

Result:
{result}

Formulate a clear and understandable confirmation message in a single sentence, starting with 'Hello {current_user},' confirming that your request has been successfully processed."""
                ),
            ]
        )

    llm = ChatOllama(
    base_url=base_url,
    model = model,
    temperature = 0,
)
    human_response = generate_prompt | llm | StrOutputParser()
    answer = human_response.invoke({})
    state["query_result"] = answer
    print("Generated human-readable answer.")
    return state

class RewrittenQuestion(BaseModel):
    question: str = Field(description="The rewritten question.")

def regenerate_query(state: AgentState):
    question = state["question"]
    print("Regenerating the SQL query by rewriting the question.")
    system = """You are an assistant that reformulates an original question to enable more precise SQL queries. Ensure that all necessary details, such as table joins, are preserved to retrieve complete and accurate data.
    """
    rewrite_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                f"Original Question: {question}\nReformulate the question to enable more precise SQL queries, ensuring all necessary details are preserved.",
            ),
        ]
    )
    llm = ChatOllama(
    base_url=base_url,
    model = model,
    temperature = 0,
)
    structured_llm = llm.with_structured_output(RewrittenQuestion)
    rewriter = rewrite_prompt | structured_llm
    rewritten = rewriter.invoke({})
    state["question"] = rewritten.question
    state["attempts"] += 1
    print(f"Rewritten question: {state['question']}")
    return state

def generate_funny_response(state: AgentState):
    print("Generating a funny response for an unrelated question.")
    system = """You are an assistant who can help with ordering delicious food, and you politely explain that what the person is asking for isn’t related to the restaurant’s work..
    """
    human_message = state["question"]
    funny_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", human_message),
        ]
    )
    llm = ChatOllama(
    base_url=base_url,
    model = model,
    temperature = 0.8
)
    funny_response = funny_prompt | llm | StrOutputParser()
    message = funny_response.invoke({})
    state["query_result"] = message
    print("Generated funny response.")
    return state

def confirm_order(state: AgentState) -> Command[Literal["execute_sql", "cancel_order"]]:
    summary = 'Hello this is summay'
    return_to = interrupt({
        "question": "Do you want to confirm the order?",
        "options": ["Yes", "No"],
        "summary": summary,

    })
    

    if return_to == "Yes":
        print("User confirmed the order.")
        state['query_result'] = 'sefaresh shoma sabt shod'
        return Command(goto="execute_sql")
    else:
        print("User canceled the order.")
        state["query_result"] = "Order canceled."
        return Command(goto="cancel_order")
    
def cancel_order(state: AgentState):
    state["query_result"] = "Order canceled."
    print("Order has been canceled.")
    return state    

def end_max_iterations(state: AgentState):
    state["query_result"] = "Please try again."
    print("Maximum attempts reached. Ending the workflow.")
    return state

def relevance_router(state: AgentState):
    if state["relevance"].lower() == "order" or state["relevance"].lower() == "menu":
        return "convert_to_sql"
    else:
        return "generate_funny_response"
    
def confirm_router(state: AgentState):
    if state["relevance"].lower() == "order":
        return "confirm_order"
    else:
        return "execute_sql"
    
def check_attempts_router(state: AgentState):
    if state["attempts"] < 3:
        return "convert_to_sql"
    else:
        return "end_max_iterations"

def execute_sql_router(state: AgentState):
    if not state.get("sql_error", False):
        return "generate_human_readable_answer"
    else:
        return "regenerate_query"