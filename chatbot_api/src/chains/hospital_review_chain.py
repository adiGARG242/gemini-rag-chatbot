# chatbot_api/src/chains/hospital_review_chain.py
import os
import dotenv

# make sure environment variables are loaded
dotenv.load_dotenv()

from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
)
from langchain.chains import RetrievalQA
from langchain.prompts import (
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)

HOSPITAL_QA_MODEL = os.getenv("HOSPITAL_QA_MODEL", "gemini-1.5-flash")
EMBED_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/text-embedding-004")

# Build Neo4j vector index-backed retriever over Review nodes (same fields as article)
review_vector_store = Neo4jVector.from_existing_graph(
    embedding=GoogleGenerativeAIEmbeddings(model=EMBED_MODEL),
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE"),
    index_name="reviews",
    node_label="Review",
    text_node_properties=[
        "physician_name",
        "patient_name",
        "text",
        "hospital_name",
    ],
    embedding_node_property="embedding",
)

# Prompt closely mirrors the tutorial’s intent and structure
review_template = """You are a helpful assistant that answers questions about patient experiences at hospitals.
Use ONLY the following patient reviews as context. When helpful, include concrete details (patient/physician/hospital names).
If the reviews don’t contain the answer, say you don’t know.

Context:
{context}

User question:
{question}
"""

system_msg = SystemMessagePromptTemplate(
    prompt=PromptTemplate(input_variables=["context"], template=review_template)
)
human_msg = HumanMessagePromptTemplate.from_template("{question}")
review_prompt = ChatPromptTemplate.from_messages([system_msg, human_msg])

qa_llm = ChatGoogleGenerativeAI(
    model=HOSPITAL_QA_MODEL,
    temperature=0.2,
)

reviews_vector_chain = RetrievalQA.from_chain_type(
    llm=qa_llm,
    chain_type="stuff",
    retriever=review_vector_store.as_retriever(search_kwargs={"k": 12}),
    chain_type_kwargs={"prompt": review_prompt},
)
