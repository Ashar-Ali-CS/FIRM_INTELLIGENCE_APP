



from fastapi import APIRouter, HTTPException


from pydantic import BaseModel,Field

from anthropic import APIStatusError, APITimeoutError, RateLimitError

import knowledge_store as knowledge 

import llm 

#our relevence floor
#below this we treat retrived context as not actually relevent
RELEVENCE_FLOOR = 0.40


#create your router 

router = APIRouter(prefix = "/knowledge", tags=["knowledge"])





# create your class (QUESTION) using base model with 2 field (question and top_k)

class Question(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=3, gt=0,le=8)



#use prefix knowledge in curl to run - 
#it is POST becuase POST creates something but at higher level POST does something (not like get) - like action

@router.post("/index")
def rebuild_index():
    """Embed the corpus. Costs tokens....so it is a deliberate POST,rather than automatic"""
    tokens =  knowledge.build_index()
    return {"indexed": knowledge.count(), "embedding_tokens": tokens}


@router.post("/search")
def search(q: Question):
    """ Retreival only , no model call or generated text etc - only what was found"""
    try:
        return {"question": q.question, "results": knowledge.search(q.question,q.top_k)}
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


# function behaviour
# refusal happens before model is called not after

# why 200 and not 404 for a refusal?: becuase the request was valid but service handled it correctly and 
# "we have no relevent documents" is real answer 

# sources...
# this makes our answer checkable...without it a client has an answer/para that they have to trust ...
#with it they can open the doc-004 (or other) and verify the claim themselves 

# same error mapping as before 
#504,429, 502 ....never 500. 


@router.post("/ask")
def ask(q: Question):
    """ Retrieve, then LLM answer using only what was retrieved....or refuse"""

    #20 lines of code - RAG pipeline for the api , link to chroma tommarow 

    # 1. Retrieve
    #same call as "/knowledge/search "
    try:
        hits = knowledge.search( q.question, q.top_k ) 
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e) ) 


    
    # 2. Filter, and decide whether to make a call to the model at all
    # (compare against our RELEVENCE_FLOOR )
    usable = [hit for hit in hits if hit["score"] >= RELEVENCE_FLOOR ]
    if not usable:
        return {
            "question": q.question,
            "answer": None,
            "refused": True,
            "reason": " No document in the corpus is relevent to that question.",
            "sources": []
        }

    # 3. Build context ,generate the answer 

    context = "\n\n".join(f"[{h['id']}] {h['title']}\n{h['text']}" for h in usable)

    try:
        result = llm.answer_from_context(q.question, context)
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="Answer provider timed out")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="Answer provider rate limited")
    except APIStatusError:
        raise HTTPException(status_code=502, detail="Answer provider unavailable")

    # 4. Return the succesfull answer 
    return {
        "question":q.question,
        "answer": result["answer"],
        "refused": False,
        "sources": [ {"id": h["id"], "title": h["title"], "score": round(h["score"],3)} for h in usable ],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "stop_reason": result["stop_reason"],
    }


























"""

Ashar Ali@Ashars-laptop MINGW64 ~
$ curl -X POST http://127.0.0.1:8000/knowledge/index

$ curl -X POST http://127.0.0.1:8000/knowledge/search -H "Content-Type: application/json"   -d '{"question":"Which firm works in energy and infrastructure?"}'
{"question":"Which firm works in energy and infrastructure?","results":[{"id":"doc-003","title":"Okonkwo Bell — Strategy Briefing","text":"Okonkwo Bell is a boutique with a deliberately narrow focus. The firm has built a reputation in energy and infrastructure work, particularly projects with a development finance element. It is not trying to be a full-service firm and hasturned away work outside its core areas. Headcount has grown slowly and deliberately. The firm's leadership has been explicit that it does not intend to merge, and has declined at least two approaches in the past three years.","score":0.4445349244383033},{"id":"doc-001","title":"Harding & Voss — Market Position Note","text":"Harding & Voss remains one of the stronger mid-tier performers in the UK market. Revenue growth has been steady rather than spectacular, and the firm has resisted the temptation to chase headline lateral hires. Its disputes practice is widely regarded as the strongest part of the business, particularly in commercial litigation and international arbitration. The corporate team is competent but has not won a significant mandate outside the UK in the last eighteen months. Partner retention is good. The firm does notoperate in the United States and has no plans to open there.","score":0.23587258414890355},{"id":"doc-004","title":"Sandoval Kerr — Risk and Compliance Summary","text":"Sandoval Kerr has invested heavily in its conflicts and compliance function following a difficult period two years ago. The firm's matter intake process now requires sign-off from a dedicated risk partner for any engagement above a defined threshold. Professional indemnity arrangements were renegotiated at the last renewal. There are no outstanding regulatory matters. The firm reports no material claims in the current period.","score":0.20053045608681558}]}
Ashar Ali@Ashars-laptop MINGW64 ~
$ curl -X POST http://127.0.0.1:8000/knowledge/search -H "Content-Type: application/json"   -d '{"question":"Which firm operates in US?"}'
{"question":"Which firm operates in US?","results":[{"id":"doc-001","title":"Harding & Voss — Market Position Note","text":"Harding & Voss remains one of the stronger mid-tier performers in the UK market. Revenue growth has been steady rather than spectacular, and the firm has resisted the temptation to chase headline lateral hires. Its disputes practice is widely regarded as the strongest part of the business, particularly in commercial litigation and international arbitration. The corporate team is competent but has not won a significant mandate outside the UK in the last eighteen months. Partner retention is good. The firm does not operate in the United States and has no plans to open there.","score":0.35892222235245114},{"id":"doc-003","title":"Okonkwo Bell — Strategy Briefing","text":"Okonkwo Bell is a boutique with a deliberately narrow focus. The firm has built a reputation in energy and infrastructure work, particularly projects with a development finance element. It is not trying to be a full-service firm and has turned away work outside its core areas. Headcount has grown slowly and deliberately. The firm's leadership has been explicit that it does not intend to merge, and has declined at least two approaches in the past three years.","score":0.3235920795208762},{"id":"doc-005","title":"Lindqvist Partners — APAC Expansion Review","text":"Lindqvist Partners has grown its Singapore office faster than any other part of the business. The firm's APAC strategy leans on relationships with Nordic corporates operating in the region rather than on local market share. This has produced a profitable but narrow practice. The Tokyo office has underperformed against its original business case and is under review. Matter reference LP-2291 covers the internal assessment of that review and is not for external circulation.","score":0.281081181814475}]}
Ashar Ali@Ashars-laptop MINGW64 ~
$ curl -X POST http://127.0.0.1:8000/knowledge/search -H "Content-Type: application/json"   -d '{"question":"Which firm has regulation and complience problem?"}'
{"question":"Which firm has regulation and complience problem?","results":[{"id":"doc-004","title":"Sandoval Kerr — Risk and Compliance Summary","text":"Sandoval Kerr has invested heavily in its conflicts and compliance function following a difficult period two years ago. The firm's matter intake process now requires sign-off from a dedicated risk partner for any engagement above a defined threshold. Professional indemnity arrangements were renegotiated at the last renewal. There are no outstanding regulatory matters. The firm reports no material claims in the current period.","score":0.3536781375685397},{"id":"doc-007","title":"Jurisdiction Note — EU Practice Rights","text":"Firms operating across EU member states continue to navigate divergent requirements on practice rights and establishment. The position for UK-qualified lawyers has not returned to the pre-2021 arrangement. Firms with a registered EU presence are largely unaffected. Those servicing EU clients from London face more friction, particularly in regulated advisory work. Reference EUPR-14 sets out the current position per jurisdiction.","score":0.297300533855991},{"id":"doc-003","title":"Okonkwo Bell — Strategy Briefing","text":"Okonkwo Bell is a boutique with a deliberately narrow focus. The firm has built a reputation in energy and infrastructure work, particularly projects with a development finance element. It is not trying to be a full-service firm and has turned away work outside its core areas. Headcount has grown slowly and deliberately. The firm's leadership has been explicit that it does not intend to merge, and has declined at least two approaches in the past three years.","score":0.2851057408604647}]}
Ashar Ali@Ashars-laptop MINGW64 ~
$

"""










