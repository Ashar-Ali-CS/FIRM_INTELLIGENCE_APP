


from fastapi import APIRouter, HTTPException


from anthropic import APIStatusError, APITimeoutError, RateLimitError

import agent 


router = APIRouter(prefix = "/agent", tags=["agent"])



@router.post("/ask")
def ask(question:str):
    """ask agent question"""
    try:
        result = agent.ask_with_tools(question)
        return result 
    except APITimeoutError:
            raise HTTPException(status_code=504, detail="AI Agent  timed out")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="AI Agent rate limited")
    except APIStatusError:
        raise HTTPException(status_code=502, detail="AI Agent  unavailable")


