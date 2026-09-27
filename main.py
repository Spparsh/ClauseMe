from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import ContractAgent

app = FastAPI(title="ContractRedFlag API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ContractAgent()

class AnalyzeRequest(BaseModel):
    filename: str
    text: str

class AskRequest(BaseModel):
    question: str
    finding: dict

@app.get("/")
def root():
    return {"name":"ContractRedFlag API","status":"online"}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return agent.analyze(req.filename, req.text)

@app.post("/ask")
def ask(req: AskRequest):
    return agent.answer(req.question, req.finding)
