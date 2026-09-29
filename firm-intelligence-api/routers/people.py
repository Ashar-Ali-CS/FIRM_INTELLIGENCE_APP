

from fastapi import Depends,HTTPException,APIRouter
from pydantic import BaseModel ,Field

from data import PEOPLE
from routers.firms import get_firm_or_404


router = APIRouter(prefix="/people", tags=["people"])




class NewPerson(BaseModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    firm_id: int 


def get_person_or_404(person_id:int) -> dict:
    for person in PEOPLE:
        if person["id"] == person_id:
            return person
    raise HTTPException(status_code=404, detail=f"No person with id {person_id}")

@router.get("")
def list_people(firm_id:int | None=None):
    if firm_id is None:
        return PEOPLE
    return [p for p in PEOPLE if p["firm_id"]==firm_id]

#END Wednessday 


#get_person - by person id?
@router.get("/{person_id}")
def get_person(person:dict = Depends(get_person_or_404)):
    return person 

#add_person -need firm id of course to add to 
#have depnds in the body not header ,as new persons firm id would not be in header (but in body)
@router.post("", status_code=201)
def add_person(new: NewPerson):
    get_firm_or_404(new.firm_id) #raises 404 if (new persons) firm doesnt exist ,cant do in depends
    new_id = max(person["id"] for person in PEOPLE) + 1
    person = {
        "id": new_id,
        "name": new.name,
        "role": new.role,
        "firm_id": new.firm_id,
    }
    PEOPLE.append(person) 
    return person 


