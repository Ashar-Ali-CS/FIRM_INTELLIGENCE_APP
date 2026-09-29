
from fastapi import FastAPI
from routers import firms, people,reports,insights,knowledge,agent


app = FastAPI(title ="Firm intelligence API")


#wiring from routers folder into the fastapi app (after imports of files from router above)
app.include_router(firms.router)
app.include_router(people.router)
app.include_router(reports.router)
app.include_router(insights.router) #llm insights added
app.include_router(knowledge.router) #embeddings stuff
app.include_router(agent.router)

@app.get("/health")
def health():
    return {"status": "ok"}


