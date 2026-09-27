const API = "http://127.0.0.1:8000";
let currentFindings = [];
let selectedFinding = null;

const demoContract = `EMPLOYMENT AGREEMENT

1. POSITION
The Employee will serve as a Software Developer. The Employee may be assigned additional duties as reasonably required by the Company.

2. COMPENSATION
The Employee will receive a monthly salary of INR 45,000, payable on the last working day of each month.

3. PROBATION
The first six months of employment will constitute a probation period.

4. NOTICE AND TERMINATION
During probation, either party may terminate this agreement with 7 days written notice. After probation, the Employee must provide 90 days written notice before resignation. The Company may terminate employment immediately for serious misconduct.

5. NON-COMPETE
For a period of 24 months after termination, the Employee agrees not to work for, provide services to, or hold an interest in any business that competes with the Company within India.

6. INTELLECTUAL PROPERTY
All inventions, software, designs, documents, ideas, improvements, and other work product created by the Employee during employment or relating in any way to the Company's business will be the exclusive property of the Company.

7. CONFIDENTIALITY
The Employee shall not disclose confidential information during employment or after termination.

8. AUTOMATIC RENEWAL
This agreement will automatically renew for successive one-year periods unless either party provides written notice at least 60 days before the end of the current term.

9. LIABILITY
The Employee agrees to indemnify the Company for any losses, claims, costs, damages, and expenses arising from the Employee's acts or omissions.

10. GOVERNING LAW
This agreement will be governed by the laws applicable in the jurisdiction selected by the Company.`;

document.getElementById("fileInput").addEventListener("change", e => {
  const file = e.target.files[0];
  if (file) analyzeText(file.name, file.text());
});

function loadDemo() { analyzeText("Demo_Employment_Agreement.txt", Promise.resolve(demoContract)); }

async function analyzeText(name, textPromise) {
  try {
    const text = await textPromise;
    showLoading();
    const res = await fetch(`${API}/analyze`, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({filename:name, text})
    });
    if (!res.ok) throw new Error("Backend unavailable");
    const data = await res.json();
    renderResults(data);
  } catch (err) {
    alert("Start the FastAPI backend first.\\n\\n" + err.message);
    resetApp();
  }
}

function showLoading() {
  uploadView.classList.add("hidden");
  resultsView.classList.add("hidden");
  loadingView.classList.remove("hidden");
  let p = 0;
  const steps = [
    ["Reading contract...", "Parsing document structure"],
    ["Finding risk patterns...", "Scanning clauses for red flags"],
    ["Investigating context...", "Connecting risk with surrounding clauses"],
    ["Writing report...", "Converting findings into plain language"]
  ];
  let i=0;
  const timer=setInterval(()=>{
    p=Math.min(100,p+25); progressBar.style.width=p+"%";
    if(i<4){ loadingTitle.textContent=steps[i][0]; loadingStep.textContent=steps[i][1]; document.getElementById("step"+(i+1)).classList.add("done"); i++; }
    if(p>=100) clearInterval(timer);
  },450);
}

function renderResults(data) {
  setTimeout(()=>{
    loadingView.classList.add("hidden");
    resultsView.classList.remove("hidden");
    document.getElementById("contractName").textContent=data.filename;
    document.getElementById("totalClauses").textContent=data.summary.total_clauses;
    document.getElementById("highCount").textContent=data.summary.high;
    document.getElementById("mediumCount").textContent=data.summary.medium;
    document.getElementById("lowCount").textContent=data.summary.low;
    document.getElementById("engineBadge").textContent=data.engine;
    currentFindings=data.findings;
    findingsList.innerHTML=currentFindings.map((f,i)=>`
      <div class="finding" onclick="openFinding(${i})">
        <div class="finding-top"><div class="finding-title">${escapeHtml(f.title)}</div><span class="risk risk-${f.risk.toLowerCase()}">${f.risk}</span></div>
        <div class="finding-text">${escapeHtml(f.summary)}</div>
        <div class="finding-meta">Clause ${f.clause_number} · ${escapeHtml(f.category)}</div>
      </div>`).join("");
    traceList.innerHTML=data.trace.map((t,i)=>`
      <div class="trace"><div class="trace-icon">${i+1}</div><div><b>${escapeHtml(t.step)}</b><span>${escapeHtml(t.detail)}</span></div></div>`).join("");
  },400);
}

function openFinding(i){
  selectedFinding=currentFindings[i];
  const f=selectedFinding;
  modalContent.innerHTML=`
    <p class="eyebrow">CLAUSE ${f.clause_number} · ${escapeHtml(f.category.toUpperCase())}</p>
    <h2>${escapeHtml(f.title)} <span class="risk risk-${f.risk.toLowerCase()}">${f.risk}</span></h2>
    <div class="quote">${escapeHtml(f.excerpt)}</div>
    <div class="detail-grid">
      <div class="detail-box"><b>Why flagged</b><span>${escapeHtml(f.why_flagged)}</span></div>
      <div class="detail-box"><b>Potential concern</b><span>${escapeHtml(f.potential_concern)}</span></div>
      <div class="detail-box"><b>Agent recommendation</b><span>${escapeHtml(f.recommendation)}</span></div>
      <div class="detail-box"><b>Confidence</b><span>${escapeHtml(f.confidence)}</span></div>
    </div>`;
  askAnswer.classList.add("hidden"); askInput.value=""; detailModal.classList.remove("hidden");
}
function closeModal(){detailModal.classList.add("hidden")}
async function askAgent(){
  if(!selectedFinding) return;
  const q=askInput.value.trim(); if(!q)return;
  askAnswer.classList.remove("hidden"); askAnswer.textContent="Agent is investigating...";
  try{
    const r=await fetch(`${API}/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q,finding:selectedFinding})});
    const d=await r.json(); askAnswer.textContent=d.answer;
  }catch(e){askAnswer.textContent="The agent could not reach the backend."}
}
function resetApp(){location.reload()}
function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
