"""
Agentic RAG with LangChain
===========================
An agent that has access to multiple tools:
  1. A retriever tool  — searches a small in-memory FAISS vector store
  2. A web-search tool — falls back to Tavily web search
  3. A calculator tool  — does basic math

The agent autonomously decides WHICH tool to call based on the question.

Install deps:
    pip install langchain langchain-openai langchain-community \
                faiss-cpu tavily-python

Set env vars:
    export OPENAI_API_KEY="sk-..."
    export TAVILY_API_KEY="tvly-..."     # optional, for web search
"""

from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.prebuilt import create_react_agent

# ── 1. Build a tiny vector store from raw docs ──────────────────────

docs = [
    "LangChain is a framework for building LLM-powered applications. "
    "It provides tools, chains, and agents to connect language models to data.",

    "Retrieval Augmented Generation (RAG) grounds LLM responses in external "
    "knowledge by retrieving relevant documents before generating an answer.",

    "Agents in LangChain use an LLM to decide which tools to call and in what "
    "order. They loop until the task is complete, making them more flexible than chains.",

    "FAISS is a library for efficient similarity search. LangChain integrates "
    "with FAISS to create fast, local vector stores for retrieval.",

    "Python was created by Guido van Rossum and first released in 1991. "
    "It emphasizes code readability and simplicity.",
]

splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = splitter.create_documents(docs)

vectorstore = FAISS.from_documents(chunks, OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# ── 2. Define tools ─────────────────────────────────────────────────

@tool
def search_knowledge_base(query: str) -> str:
    """Search the internal knowledge base for information about
    LangChain, RAG, agents, FAISS, or Python."""
    results = retriever.invoke(query)
    if not results:
        return "No relevant documents found."
    return "\n\n".join(doc.page_content for doc in results)


@tool
def web_search(query: str) -> str:
    """Search the web for current / real-time information
    that is NOT in the knowledge base."""
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        search = TavilySearchResults(max_results=2)
        results = search.invoke(query)
        return str(results)
    except Exception as e:
        return f"Web search unavailable: {e}"


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Example: '2 + 2' or '100 / 7'."""
    try:
        result = eval(expression, {"__builtins__": {}})  # restricted eval
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# ── 3. Create the agent ─────────────────────────────────────────────

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_react_agent(
    model=llm,
    tools=[search_knowledge_base, web_search, calculator],
    state_modifier=(
        "You are a helpful research assistant. "
        "Use the knowledge base tool FIRST for questions about LangChain, "
        "RAG, agents, FAISS, or Python. "
        "Use web search ONLY when the knowledge base has no answer. "
        "Use the calculator for any math. "
        "Always cite which tool you used."
    ),
)

# ── 4. Helper to query the agent ─────────────────────────────────────

def ask(question: str) -> str:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    return result["messages"][-1].content


if __name__ == "__main__":
    for q in [
        "What is RAG and how does it work?",
        "What is 1024 * 768?",
        "Who won the latest Nobel Prize in Physics?",
    ]:
        print(f"\nQ: {q}\nA: {ask(q)}\n")
