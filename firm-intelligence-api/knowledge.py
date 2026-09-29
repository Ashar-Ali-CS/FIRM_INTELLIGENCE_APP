
"""Embedding and retrival mechanics...nothing in here will know about FastAPI"""

import math

import os

import voyageai

from documents import DOCUMENTS


EMBED_MODEL = "voyage-3-lite"

voyage = voyageai.Client(
    api_key=os.environ["VOYAGE_API_KEY"],
    max_retries=3,
    timeout = 3
)

# the in memory index .... a list of dicts (exactly like FIRMS lasr week.)
INDEX: list[dict] = []

def embed_texts(texts: list[str] ,  input_type: str)-> tuple[list[list[float]]]:
    #embed a batch
    # input type tells voyage wheter these are docs or query (done differently by voyage) 
    result = voyage.embed(texts=texts,model=EMBED_MODEL, input_type=input_type)
  
    #returns the vectors and token count (can see cost)
    return result.embeddings, result.total_tokens



#calculating cosine similary for under hood , building index - then chroma which does automaticly 

def cosine_similarity(a:list[float], b: list[float]) -> float:
    """How close are two vectors in direction,ignoring length
    1.0 identical direection
    0.0 means unreleted
    -1.0 opposite
    """

    dot = sum(x * y for x, y in zip(a,b))

    norm_a =  math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    return dot / (norm_a * norm_b) 


def build_index( ) -> int:
    """ Embed every document once and hold the vectors in memory """
    INDEX.clear() #clears previsious for starting to stop duplicate
    texts = [doc["body"] for doc in DOCUMENTS]

    vectors, tokens = embed_texts(texts, input_type ="document")

    for doc , vector in zip(DOCUMENTS, vectors):
        INDEX.append({
            "id": doc["id"],
            "title": doc["title"],
            "text": doc["body"],
            "vector": vector
        })

    return tokens #(token cost)


#search functionality (takes input and searches meaningfull doc)
def search(question: str, top_k: int=3) -> list[dict]:
    """ Embed the question ...then score it against everything in the index """

    #guardrail - check index is not empty 
    if not INDEX:
        raise RuntimeError("Index is empty call - build_index() first ")

    query_vectors, _  = embed_texts([question], input_type="query")

    query_vector =  query_vectors[0]

    scored = [
        {
            "id": entry["id"],
            "title": entry["title"],
            "text": entry["text"],
            "score": cosine_similarity(query_vector, entry["vector"] ) 
        }
        for entry in INDEX
    ]

    #sorting them by best matched 
    scored.sort(key=lambda item:item["score"], reverse=True)

    return scored[:top_k]




