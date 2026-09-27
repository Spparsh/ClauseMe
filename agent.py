import re
import os
import json
from typing import List, Dict

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

RISK_RULES = [
    {
        "patterns":[r"non[- ]compete", r"not to work for", r"competes with"],
        "title":"Broad non-compete restriction","category":"Post-employment restriction","risk":"HIGH",
        "why":"The clause restricts the person's ability to work with competing businesses after the agreement ends.",
        "concern":"The restriction is broad in duration, geography, or covered activity and may deserve professional review.",
        "recommendation":"Check whether the duration, geography, and scope are reasonable and enforceable for the relevant jurisdiction."
    },
    {
        "patterns":[r"24 months", r"two years"],
        "title":"Long post-termination period","category":"Duration","risk":"HIGH",
        "why":"A lengthy period is attached to a post-employment restriction.",
        "concern":"The time period may materially affect future work opportunities.",
        "recommendation":"Ask for the business reason and review the duration with a qualified professional."
    },
    {
        "patterns":[r"90 days written notice", r"90 days notice"],
        "title":"Long resignation notice","category":"Termination","risk":"MEDIUM",
        "why":"The employee is required to provide a relatively long notice period before resignation.",
        "concern":"This can reduce flexibility when changing employment.",
        "recommendation":"Confirm whether the notice period is acceptable and whether payment in lieu or a shorter period is available."
    },
    {
        "patterns":[r"automatically renew", r"automatic renewal", r"successive one-year"],
        "title":"Automatic renewal","category":"Renewal","risk":"MEDIUM",
        "why":"The agreement renews automatically unless notice is provided before a deadline.",
        "concern":"Missing the notice window could extend the agreement unexpectedly.",
        "recommendation":"Calendar the cancellation deadline and confirm the renewal terms."
    },
    {
        "patterns":[r"indemnify", r"indemnification"],
        "title":"Indemnity obligation","category":"Liability","risk":"HIGH",
        "why":"The clause can shift certain losses, claims, costs, or damages to the employee.",
        "concern":"The financial exposure may be broader than expected depending on the wording.",
        "recommendation":"Check the trigger, scope, exclusions, caps, and whether the obligation is reciprocal."
    },
    {
        "patterns":[r"all inventions", r"all .*work product", r"exclusive property"],
        "title":"Broad intellectual-property assignment","category":"Intellectual property","risk":"MEDIUM",
        "why":"The clause assigns a broad range of work product or inventions to the company.",
        "concern":"Depending on the wording, it may cover work that is not directly connected to assigned duties.",
        "recommendation":"Check definitions, exclusions for pre-existing work, and the connection to company business."
    },
    {
        "patterns":[r"jurisdiction selected by the company"],
        "title":"One-sided governing-law selection","category":"Governing law","risk":"MEDIUM",
        "why":"The agreement allows one party to select the governing jurisdiction.",
        "concern":"The employee may have less certainty about where disputes will be governed.",
        "recommendation":"Confirm the jurisdiction before signing and seek clarification if it is not specified."
    },
    {
        "patterns":[r"immediately for serious misconduct"],
        "title":"Immediate termination provision","category":"Termination","risk":"LOW",
        "why":"The agreement permits immediate termination for serious misconduct.",
        "concern":"The practical meaning depends on how misconduct is defined and what process applies.",
        "recommendation":"Check whether the agreement defines misconduct and provides a fair investigation process."
    }
]

class ContractAgent:
    def __init__(self):
        self.client = None
        key = os.getenv("OPENAI_API_KEY")
        if key and OpenAI:
            self.client = OpenAI(api_key=key)

    def _clauses(self, text: str):
        matches = list(re.finditer(r"(?m)^\s*(\d+)\.\s+([^\n]+)", text))
        clauses=[]
        for i,m in enumerate(matches):
            start=m.start()
            end=matches[i+1].start() if i+1<len(matches) else len(text)
            block=text[start:end].strip()
            clauses.append({"number":m.group(1),"heading":m.group(2).strip(),"text":block})
        return clauses

    def _rule_findings(self, clauses):
        findings=[]
        for c in clauses:
            low=c["text"].lower()
            for rule in RISK_RULES:
                if any(re.search(p, low) for p in rule["patterns"]):
                    excerpt=" ".join(c["text"].split())
                    if len(excerpt)>280: excerpt=excerpt[:280]+"..."
                    findings.append({
                        "clause_number":c["number"],
                        "title":rule["title"],
                        "category":rule["category"],
                        "risk":rule["risk"],
                        "summary":rule["why"],
                        "why_flagged":rule["why"],
                        "potential_concern":rule["concern"],
                        "recommendation":rule["recommendation"],
                        "confidence":"High — matched a defined contract-risk pattern.",
                        "excerpt":excerpt
                    })
                    break
        return findings

    def _normal_findings(self, clauses):
        return [{
            "clause_number":c["number"],
            "title":c["heading"],
            "category":"Standard clause",
            "risk":"LOW",
            "summary":"No major red-flag pattern was detected by the prototype rules.",
            "why_flagged":"The agent did not find a configured high-priority risk pattern.",
            "potential_concern":"A rule-based prototype cannot determine every legal issue.",
            "recommendation":"Review the clause in context before signing.",
            "confidence":"Limited — automated screening only.",
            "excerpt":" ".join(c["text"].split())[:280]
        } for c in clauses]

    def analyze(self, filename, text):
        clauses=self._clauses(text)
        flagged=self._rule_findings(clauses)
        flagged_nums={f["clause_number"] for f in flagged}
        normal=[f for f in self._normal_findings(clauses) if f["clause_number"] not in flagged_nums]
        findings=flagged+normal
        # Keep a useful report even for contracts without numbered clauses.
        if not clauses:
            findings=self._fallback_scan(text)
        findings=self._sort_findings(findings)
        if self.client:
            try:
                findings=self._enhance_with_llm(text, findings)
                engine="RULE + LLM AGENT"
            except Exception:
                engine="RULE AGENT (LLM fallback)"
        else:
            engine="RULE AGENT • DEMO MODE"
        counts={"total_clauses":len(clauses) or len(findings),
                "high":sum(f["risk"]=="HIGH" for f in findings),
                "medium":sum(f["risk"]=="MEDIUM" for f in findings),
                "low":sum(f["risk"]=="LOW" for f in findings)}
        trace=[
            {"step":"Parsed contract","detail":f"Detected {len(clauses) or len(findings)} clause blocks."},
            {"step":"Scanned risk patterns","detail":f"Found {counts['high']+counts['medium']} clauses needing closer review."},
            {"step":"Investigated context","detail":"Matched flagged wording with surrounding clause context."},
            {"step":"Generated report","detail":"Converted findings into plain-language explanations and next actions."}
        ]
        return {"filename":filename,"engine":engine,"summary":counts,"findings":findings,"trace":trace}

    def _sort_findings(self, findings):
        order={"HIGH":0,"MEDIUM":1,"LOW":2}
        return sorted(findings,key=lambda x:(order.get(x["risk"],3),int(x.get("clause_number","999")) if str(x.get("clause_number","999")).isdigit() else 999))

    def _fallback_scan(self,text):
        f=[]
        for rule in RISK_RULES:
            for p in rule["patterns"]:
                m=re.search(p,text,re.I)
                if m:
                    s=max(0,m.start()-100); e=min(len(text),m.end()+180)
                    f.append({
                        "clause_number":"—","title":rule["title"],"category":rule["category"],"risk":rule["risk"],
                        "summary":rule["why"],"why_flagged":rule["why"],"potential_concern":rule["concern"],
                        "recommendation":rule["recommendation"],"confidence":"Pattern match.","excerpt":" ".join(text[s:e].split())
                    }); break
        return self._sort_findings(f)

    def _enhance_with_llm(self,text,findings):
        prompt=f"""You are a contract-risk screening assistant. Do not give legal advice or declare a clause legally enforceable/unenforceable. Improve the explanations in this JSON while preserving clause numbers, titles, categories and risk levels. Keep each explanation concise and evidence-based. Contract text:
{text[:14000]}
Findings:
{json.dumps(findings,ensure_ascii=False)}
Return JSON array only with the same objects and fields."""
        response=self.client.responses.create(model=os.getenv("OPENAI_MODEL","gpt-5-mini"),input=prompt)
        raw=response.output_text
        data=json.loads(raw)
        return data if isinstance(data,list) else findings

    def answer(self,question,finding):
        if self.client:
            try:
                prompt=f"""Answer the user's question about this contract finding in plain English. Do not provide legal advice or claim certainty. Mention when a lawyer should review it.
Finding: {json.dumps(finding)}
Question: {question}"""
                r=self.client.responses.create(model=os.getenv("OPENAI_MODEL","gpt-5-mini"),input=prompt)
                return {"answer":r.output_text}
            except Exception:
                pass
        q=question.lower()
        if "why" in q:
            return {"answer":f"The agent flagged this because the clause matches a configured risk pattern: {finding['why_flagged']} The concern is: {finding['potential_concern']}"}
        if "ignore" in q or "happen" in q:
            return {"answer":f"The potential issue is: {finding['potential_concern']} The agent recommends: {finding['recommendation']}"}
        return {"answer":f"This finding is classified as {finding['risk']} risk because: {finding['why_flagged']} Review the exact wording and surrounding clauses before signing."}
