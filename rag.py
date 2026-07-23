"""
RAG layer: retrieves relevant government schemes from schemes.json
based on a user's question, using vector similarity (ChromaDB).
"""

import json
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


def load_schemes(path="schemes.json"):
    with open(path, "r") as f:
        return json.load(f)


def build_scheme_vectorstore(schemes):
    docs = []
    for s in schemes:
        text = (
            f"Scheme: {s['name']}\n"
            f"Category: {s['category']}\n"
            f"Eligibility: {s['eligibility']}\n"
            f"Benefit: {s['benefit']}\n"
            f"Documents required: {', '.join(s['documents'])}\n"
            f"How to apply: {s['how_to_apply']}"
        )
        docs.append(Document(page_content=text, metadata={"id": s["id"], "source": s["source"]}))

    embeddings = OpenAIEmbeddings()
    vectordb = Chroma.from_documents(docs, embeddings, collection_name="civic_schemes")
    return vectordb


def retrieve_relevant_schemes(vectordb, query, k=3):
    results = vectordb.similarity_search(query, k=k)
    return results
