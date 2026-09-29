


from fastapi import APIRouter,HTTPException, Header, Depends

from data import FIRMS
from pydantic import BaseModel ,Field


router = APIRouter(prefix="/firms",tags=["firms"])


_seen_keys: dict[str, dict] = {}







#decorator modifies the function (get is method,health is path)
#did this .venv/Scripts/python.exe -m uvicorn main:app --reload in one terminal 
#new terminal while other terminal runs it locally 
#can search the given http://.... /docs on goodle



#this is helper function to search for the firm 
def get_firm_or_404(firm_id: int) -> dict:
    for firm in FIRMS:
        if firm["id"] == firm_id:
            return firm
    raise HTTPException(status_code=404, detail=f"No firm with id {firm_id}")
    

#1.first descripe what you will accept (shape) 
#validation needded FastAPU using pydantic 
# (needed to import from pydantic basemodel(shepe it needs to accept) and field)
#inherits to become the basemodel
class NewFirm(BaseModel):
    #name,jurisdiction,revenue_usd_m,lawyers,equity_partners
    name: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=2,max_length=5)
    revenue_usd_m: float = Field(gt=0)
    #these two need to be greater than zero to avoid dived error
    #ensures it makes sense a firm cant have zero lawyers lol 
    lawyers: int = Field(gt=0)
    equity_partners: int = Field(gt=0)




#ENDPOINT 1
#it will always return everything
#so adding two optional query parameters 
@router.get("")
def list_firms(jurisdiction: str | None = None, min_revenue: float | None = None):
    results = FIRMS
    if jurisdiction is not None:
        results = [f for f in results if f["jurisdiction"] == jurisdiction]
    if min_revenue is not None:
        results = [f for f in results if f["revenue_usd_m"] >= min_revenue]
    return results



#ENDPOINT 2
# return one firm by Id, 200 if found 
#someone asks firm 99 , if not then 404 not found 
#raises http exception if firm does not exist from import of fastAPI
#usually sends from URL (sting but needs to be int ,fastAPI does it)
@router.get("/{firm_id}")
def get_firm(firm: dict = Depends(get_firm_or_404)):
    return firm



#ENDPOINT 3
#implmenting get firms benchamarks by firm ID 
#computes revenue per lawyer is total revenue diveded by fee-earner
#profit per equity partner assymes a 35% margin, then divides by number of equity
#both are pretty standrd law firm benchmarks ,like centllic
@router.get("/{firm_id}/benchmarks")
def get_benchmarks(firm: dict = Depends(get_firm_or_404)):
    revenue=firm["revenue_usd_m"]
    return {
        #id 
        "id":firm["id"],
        #name
        "name": firm["name"],
        #rev per lawyer 
        "revenue_per_lawyer_usd": round(revenue * 1_000_000 / firm["lawyers"]),
        #profit per ep 
        "profit_per_equity_partner": round(revenue * 1_000_000 * 0.35 / firm["equity_partners"] )
    }
    #  lawyers=firm["lawyers"]
    #  equity_partners=firm["equity_partners"]
    #  benchmarks=f"{revenue}, {lawyers}, {equity_partners}"
    #  return benchmarks


#need to control who can do this as well (post),right now controls shape



#ENDPOINT 4
# paramater annotaed with pydantic model means body 
# a plain int or str means URL or query parameter 
#201 means created 
#REWRITTEN
@router.post("",status_code=201)
def add_firm(new:NewFirm , idempotency_key: str | None = Header(default=None)):
    if idempotency_key is not None and idempotency_key in _seen_keys:
        return _seen_keys[idempotency_key]

    new_id = max(firm["id"] for firm in FIRMS) + 1 
    firm = {
        "id": new_id,
        "name": new.name,
        "jurisdiction":new.jurisdiction,
        "revenue_usd_m": new.revenue_usd_m,
        "lawyers": new.lawyers,
        "equity_partners": new.equity_partners
    }
    FIRMS.append(firm)
    if idempotency_key is not None:
        _seen_keys[idempotency_key]=firm
    return firm 





"""CHALLENGE 1 - replace a firm's data.

    Requirements:
      - Body is validated the same way as POST /firms (how did we do this before?).
      - Update `firm`'s fields *in place* so the change persists for later
        requests (the same idea as add_firm appending to FIRMS - mutate
        the existing dict, don't just return a new one).
      - Return the updated firm.
      - Status code 200 (the default - no status_code= needed).
    """



@router.put("/{firm_id}")
def update_firm(new:NewFirm,firm: dict = Depends(get_firm_or_404)):
    firm.update({
        "name": new.name,
        "jurisdiction": new.jurisdiction,
        "revenue_usd_m": new.revenue_usd_m,
        "lawyers": new.lawyers,
        "equity_partners": new.equity_partners
    })
    return firm 


"""CHALLENGE 2 - remove a firm.

Requirements:
    - `firm` is already looked up and guaranteed to exist.
    - Remove it from the FIRMS list.
    - Return nothing (a 204 response must have an empty body - a bare
    `return` is enough; FastAPI handles the rest because of
    status_code=204 above).
"""




@router.delete("/{firm_id}", status_code=204)
def delete_firm(firm: dict = Depends(get_firm_or_404)):
    FIRMS.remove(firm)
    return



