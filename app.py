"""
Civic AI Companion
-------------------
A GenAI + Agentic AI civic platform: chat with an AI about government
schemes (RAG-grounded, with an eligibility-checking tool), file civic
complaints (auto-categorized by an LLM), and track complaint status.

Rebuilt independently using a Python/Streamlit/SQLite/LangChain stack
(inspired by the "Nagrik AI" concept, implemented with different tools).

Run:
    streamlit run app.py
"""

import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor

from db import init_db, file_complaint, get_complaint
from rag import load_schemes, build_scheme_vectorstore, retrieve_relevant_schemes

init_db()


# ---------- Tools for the chat agent ----------

@tool
def check_eligibility(scheme_name: str, user_details: str) -> str:
    """Check if a user is likely eligible for a named government scheme,
    given details they've shared (age, occupation, income level, land ownership etc).
    Use this only after retrieving the scheme's eligibility criteria."""
    # In a full version this would run structured rule checks.
    # Kept simple here: the LLM reasons over criteria text it already retrieved.
    return (
        f"Compare the user's details ({user_details}) against the eligibility "
        f"criteria you retrieved for {scheme_name}, and state clearly whether "
        f"they likely qualify, likely don't qualify, or need to check further."
    )


def build_chat_agent(vectordb):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def search_schemes(query: str) -> str:
        results = retrieve_relevant_schemes(vectordb, query, k=3)
        return "\n\n---\n\n".join(
            f"{r.page_content}\nSource: {r.metadata['source']}" for r in results
        )

    from langchain_core.tools import Tool
    search_tool = Tool(
        name="search_schemes",
        func=search_schemes,
        description="Search the government schemes knowledge base for relevant schemes. "
                    "Always use this before answering questions about schemes or eligibility.",
    )

    tools = [search_tool, check_eligibility]

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are Nagrik Sahayak, a helpful civic assistant for Indian citizens. "
         "Use search_schemes to find relevant government schemes before answering. "
         "Use check_eligibility when the user gives personal details and asks if they qualify. "
         "Always mention required documents and cite the official source link. "
         "Keep answers simple and in plain language - avoid bureaucratic jargon. "
         "If you don't find a relevant scheme, say so honestly."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


def categorize_complaint(description: str, llm: ChatOpenAI) -> str:
    prompt = (
        "Classify this civic complaint's urgency as exactly one word: "
        "'Critical', 'Medium', or 'Low'. Critical = safety/health risk "
        "(e.g. open manhole, gas leak, live wire). Medium = affects daily life "
        "but not immediately dangerous (e.g. garbage not collected, broken streetlight). "
        "Low = minor/cosmetic issue.\n\n"
        f"Complaint: {description}\n\nRespond with only the single category word."
    )
    response = llm.invoke(prompt)
    category = response.content.strip()
    return category if category in ("Critical", "Medium", "Low") else "Medium"


# ---------- Streamlit UI ----------

def main():
    st.set_page_config(page_title="Civic AI Companion", page_icon="🏛️")
    st.title("🏛️ Civic AI Companion")
    st.caption("GenAI civic assistant - chat about schemes, file & track complaints")

    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    tab1, tab2, tab3 = st.tabs(["💬 Ask about schemes", "📝 File a complaint", "🔍 Track complaint"])

    # --- Tab 1: Chat / RAG + tool-calling agent ---
    with tab1:
        if not api_key:
            st.info("Add your OpenAI API key in the sidebar to start.")
        else:
            if "vectordb" not in st.session_state:
                with st.spinner("Loading schemes knowledge base..."):
                    schemes = load_schemes()
                    st.session_state.vectordb = build_scheme_vectorstore(schemes)
                    st.session_state.chat_agent = build_chat_agent(st.session_state.vectordb)

            question = st.text_input(
                "Ask about government schemes",
                placeholder="e.g. I'm a farmer earning less than 2 lakh a year, what schemes can I get?",
            )
            if question:
                with st.spinner("Thinking..."):
                    result = st.session_state.chat_agent.invoke({"input": question})
                    st.write(result["output"])

    # --- Tab 2: File a complaint ---
    with tab2:
        st.subheader("Report a civic issue")
        description = st.text_area("Describe the issue")
        location = st.text_input("Location")
        if st.button("Submit complaint"):
            if not api_key:
                st.error("Add your OpenAI API key in the sidebar first.")
            elif not description or not location:
                st.error("Please fill in both fields.")
            else:
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                category = categorize_complaint(description, llm)
                complaint_id = file_complaint(description, location, category)
                st.success(f"Complaint filed. Your tracking ID: **{complaint_id}**")
                st.write(f"Auto-categorized urgency: **{category}**")

    # --- Tab 3: Track complaint ---
    with tab3:
        st.subheader("Track your complaint")
        complaint_id = st.text_input("Enter complaint ID")
        if st.button("Check status"):
            complaint = get_complaint(complaint_id.strip().upper())
            if complaint:
                st.write(f"**Status:** {complaint['status']}")
                st.write(f"**Category:** {complaint['category']}")
                st.write(f"**Location:** {complaint['location']}")
                st.write(f"**Description:** {complaint['description']}")
                st.write(f"**Filed at:** {complaint['filed_at']}")
            else:
                st.error("No complaint found with that ID.")


if __name__ == "__main__":
    main()
