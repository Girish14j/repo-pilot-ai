from .embeddings import vector_store

def retrieve(query: str, topic: str = None, k: int = 3)-> str:
    """
    The main interface our agents use to retrieve relevant knowledge.
    
    Args:
        query: What the agent is looking for in natural language
               e.g. "SQL injection vulnerabilities in Python"
        topic: Optional filter to search only within a topic
               e.g. "owasp", "solid", "clean_architecture", "documentation"
        k:     How many chunks to retrieve (default 3)
    
    Returns:
        A single formatted string with all retrieved chunks,
        ready to be injected directly into a prompt.
    """

    # If a topic filter is provided, use metadata filtering
    # This narrows the search to only relevant documents
    if topic:
        results = vector_store.similarity_search(
            query,
            k=k,
            filter={"topic": topic} # chroma metadata filter
        )
    else:
        results = vector_store.similarity_search(query, k=k)

    if not results:
        return "No relevant Knowledge found."
    
    # Format the retrieved chunks into a single string for prompt injection

    formatted = []
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("principle") or doc.metadata.get("category") or doc.metadata.get("type", "")
        formatted.append(f"[Reference {i} - {source.upper()}]\n{doc.page_content}")

    return "\n\n".join(formatted)