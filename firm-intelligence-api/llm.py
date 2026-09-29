
#how we call the model (nothing knows about fastapi )

#api burnt at end of day 
#dont close (set on session)

import os
import anthropic

from anthropic import APIStatusError, APITimeoutError,RateLimitError

from pydantic import BaseModel, Field

import time

MODEL = "claude-haiku-4-5-20251001"

#the sdk defualt are max retry 2 ,600 second timeout
#overwritten here as descision

client = anthropic.Anthropic(
    api_key = os.environ["ANTHROPIC_API_KEY"],
    timeout=30.0,
    max_retries=3,

)


#the prompt and where the rules live 

#RULES GO IN SYSTEM
#DATA GOES IN USER 

SYSTEM_PROMPT = (
    "You are a legal market analyst writing for an insititutional audience."
    "Use British English. Use only the figures given to you"
    "Never invent numbers,rankings or facts that are not in data provided"
)

def build_prompt(firm:dict) -> str:
    return ( 
        f"summarise this law firm in two short paragraphs.\n\n"
        f"Jurisdiction: {firm['jurisdiction']}\n"
        f"Revenue: {firm['revenue_usd_m']}\n"
        f"Lawyers: {firm['lawyers']}\n"
        f"Equity Partners: {firm['equity_partners']}\n"

    )


#The Call (reurns response.content[0].text which has response)
def summarise_firm(firm:dict) -> dict:
    #one LLM call...return the text pluse what it costs to get
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(firm)}],
    )
    return {
        "id":firm["id"],
        "name": firm["name"],
        "summary": response.content[0].text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reoson": response.stop_reason,
    }


#messages.count_tokens tell you how big a request is WITHOUT SENDING IT ...seperete much cheaper endpoint
def estimate_input_tokens(firm:dict) -> int:
    """Count tokens before sending.costs"""
    counted = client.messages.count_tokens(
        model=MODEL,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(firm)}]
    )
    return counted.input_tokens

def stream_firm_summary(firm:dict):
    """ Yields text chunks as they arrive ...rather than waiting for whole response."""
    with client.messages.stream(
        model=MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(firm)}],
    ) as stream:
        for text in stream.text_stream:
            yield text


class FirmAnalysis(BaseModel):
    """validation- The shape we require back,it is not suggestion to model ,it is a contract""" 
    tier: str = Field(description="One of: magic circle,national and boutique")
    # strengths 
    strengths: list[str] = Field(max_length=3)
    # risks 
    risks: list[str] = Field(max_length=3)
    # #headcount_effeciency 
    headcount_efficiency: str = Field(description="high,medium or low")



def analyse_firm(firm: dict) -> dict:
    """Structured output. The response is validated against the FirmAnalsyis... or it fails """
    response = client.messages.parse(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(firm)}],
        output_format= FirmAnalysis, 
    )

    #not free text returned ?based on schema 
    analysis = response.content[0].parsed_output

    return {
        "id":firm["id"],
        "name": firm["name"],
        "analysis": analysis,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }


#Add the generation step (RAG - retrivel augmented generation)
# Retrieval finds documents...RAGS third letter  is to generate- turn those documents into answers. 

GROUNDED_SYSTEM_PROMPT = (
    "You are a legal market analyst. Answer using ONLY the context provided"
    "Cite the document id in square brackets after each claim , like [doc-001]."
    " If the context does not contain the answer , say exactly: "
    "'The provided documents do not answer the question.'"
    "Never use knowledge from outside the context. Use British English. No em dash charecters."
)


#KEY TAKEAWAY
#notice where context goes...
#rules in system 
#data in user 
def answer_from_context( question:str , context: str) -> dict:
    """Answers strictly from retrived context....the G in RAG"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=GROUNDED_SYSTEM_PROMPT,
        messages=[{
            "role":"user",
            "content":f"Content \n\n{context}\n\n Question: {question}",
        }],
    )
    return {
        "answer": response.content[0].text,
        #input and output tokens ,
        "input_tokens": response.usage.input_tokens, 
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,

    }

#



#challenege task w3 d1 near afternoon

#Ask Claude for a function that:

# retries an Anthropic API call with exponential backoff
#- logs how much that call cost, in dollars

#Copy what it gives you. Do not run it yet.


#def retry_with_backoff(func, max_retries=3, initial_delay=1.0, backoff_multiplier=2.0, model=MODEL):
#    """Retry function with exponential backoff and log cost in USD."""
#    pricing = {
#        "claude-haiku-4-5-20251001": {"input": 0.0008, "output": 0.004},
#        "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
#        "claude-opus-4-6": {"input": 0.015, "output": 0.075},
#    }
#    
#    last_error = None
#    for attempt in range(max_retries + 1):
#        try:
#            result = func()
#            
#            # Calculate cost
#            p = pricing.get(model, pricing["claude-haiku-4-5-20251001"])
#            cost = (result["input_tokens"] * p["input"] + result["output_tokens"] * p["output"]) / 1000
#            result["cost_usd"] = cost
#            
#            if attempt > 0:
#                print(f"✓ Succeeded on attempt {attempt + 1}")
#            print(f"  Tokens: {result['input_tokens']} input + {result['output_tokens']} output | Cost: ${cost:.6f}")
#            return result
#            
#        except (APITimeoutError, RateLimitError, APIStatusError) as e:
#            last_error = e
#            if attempt == max_retries:
#                print(f"✗ Failed after {max_retries + 1} attempts: {e}")
#                raise
#            delay = initial_delay * (backoff_multiplier ** attempt)
#            print(f"⚠ Attempt {attempt + 1} failed. Retrying in {delay:.1f}s...")
#            time.sleep(delay)