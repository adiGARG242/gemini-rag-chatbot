import os
import dotenv
from langchain.agents import Tool, AgentType, initialize_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# Import the two chains
from chatbot_api.src.chains.hospital_review_chain import reviews_vector_chain
from chatbot_api.src.chains.hospital_cypher_chain import hospital_cypher_chain

dotenv.load_dotenv()

HOSPITAL_QA_MODEL = os.getenv("HOSPITAL_QA_MODEL", "gemini-1.5-flash")

# Wrap chains as tools
review_tool = Tool(
    name="HospitalReviewQA",
    func=reviews_vector_chain.run,
    description="Answer questions about patient reviews and experiences.",
)

cypher_tool = Tool(
    name="HospitalGraphQA",
    func=hospital_cypher_chain.run,   # ✅ now uses the full chain
    description="Answer questions using hospital graph data: hospitals, patients, visits, physicians, etc.",
)

# Main LLM (used for reasoning about which tool to use)
qa_llm = ChatGoogleGenerativeAI(
    model=HOSPITAL_QA_MODEL,
    temperature=0.2,
)

# Build the agent
rag_agent = initialize_agent(
    tools=[review_tool, cypher_tool],
    llm=qa_llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,  # shows reasoning and tool calls in console
)
