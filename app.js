// ===== CATEGORIES =====
const CATS = [
    { id: 'role_fit', label: '역할 적합성', icon: '🎯', color: 'blue' },
    { id: 'technical_depth', label: '기술 역량', icon: '⚙️', color: 'purple' },
    { id: 'execution_ownership', label: '실행 & 오너십', icon: '🚀', color: 'indigo' },
    { id: 'communication', label: '소통 & 협업', icon: '💬', color: 'teal' },
    { id: 'risk_flags', label: '위험 신호 검증', icon: '⚠️', color: 'amber' }
];

// ===== QUESTIONS =====
// Questions are loaded from scenario files (scenario-alex.js, etc.)
let questions = [];

// ===== SCENARIOS =====
const scenarios = {};
function registerScenario(id, data) { scenarios[id] = data; }

// ===== STATE =====
let state = { currentTab:'view-intel', scores:{}, fuScores:{}, keywordsChecked:{}, scenario:'alex', selectedQuestions:[], interviewPhase:'select', expandedQuestions: new Set() };
let charts = {};

function currentScenario() { return scenarios[state.scenario] || scenarios[Object.keys(scenarios)[0]]; }

function switchScenario(id) {
    state.scenario = id;
    state.scores = {};
    state.fuScores = {};
    state.keywordsChecked = {};
    state.selectedQuestions = [];
    state.interviewPhase = 'select';
    state.expandedQuestions = new Set();
    const sc = currentScenario();
    if (sc) { questions = sc.questions || []; }

    // Update header
    if (sc) {
        document.getElementById('header-name').textContent = sc.candidate.name;
        document.getElementById('header-role').textContent = sc.candidate.role;
        document.getElementById('header-context').textContent = sc.candidate.company_context;
    }
    renderSidebar();
    renderScenarioSelector();
    renderIntel();
    renderAnalysis();
    renderDecision();
    renderQuestionSelector();
    renderStepper();
    renderSideNav();
    renderQuestions();
    updateScores();
    switchTab(state.currentTab);
}

function renderScenarioSelector() {}

// ===== QUESTION SELECTION PHASE =====
function getQuestionTime(q) { return q.difficulty==='Hard'?7:q.difficulty==='Medium'?5:3; }

function renderQuestionSelector() {
    const el = document.getElementById('question-select-phase');
    if (!el) return;
    const totalTime = state.selectedQuestions.reduce((sum, id) => {
        const q = questions.find(x => x.id === id);
        return sum + (q ? getQuestionTime(q) : 0);
    }, 0);
    const selCount = state.selectedQuestions.length;

    let html = `
    <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-6">
        <div class="flex items-center justify-between mb-4">
            <div>
                <h2 class="text-xl font-bold text-slate-800">질문 선택</h2>
                <p class="text-sm text-slate-500 mt-1">인터뷰에 사용할 질문을 선택하세요. 총 ${questions.length}개 중 원하는 질문만 골라 진행할 수 있습니다.</p>
            </div>
            <div class="text-right">
                <div class="text-2xl font-bold text-blue-600">${selCount}개 선택</div>
                <div class="text-sm text-slate-500">예상 시간: <strong class="text-blue-600">~${totalTime}분</strong></div>
            </div>
        </div>
        <div class="flex gap-2 mb-4">
            <button onclick="selectAllQuestions(true)" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-medium text-slate-600 transition">전체 선택</button>
            <button onclick="selectAllQuestions(false)" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-medium text-slate-600 transition">전체 해제</button>
            <button onclick="selectRecommendedSet()" class="px-3 py-1.5 bg-blue-100 hover:bg-blue-200 rounded-lg text-xs font-medium text-blue-700 transition">추천 세트 (~75분)</button>
        </div>
    </div>`;

    CATS.forEach(cat => {
        const catQuestions = questions.filter(q => q.category === cat.id);
        if (!catQuestions.length) return;
        const catSelected = catQuestions.filter(q => state.selectedQuestions.includes(q.id)).length;

        html += `<div class="mb-6">
            <div class="flex items-center gap-2 mb-3 pb-2 border-b-2 border-${cat.color}-200">
                <span class="text-lg">${cat.icon}</span>
                <h3 class="text-base font-bold text-slate-800">${cat.label}</h3>
                <span class="text-xs text-slate-400">${catSelected}/${catQuestions.length} 선택</span>
            </div>
            <div class="space-y-3">`;

        catQuestions.forEach(q => {
            const isSelected = state.selectedQuestions.includes(q.id);
            const time = getQuestionTime(q);
            const diffColor = q.difficulty==='Hard'?'red':q.difficulty==='Medium'?'amber':'emerald';
            html += `
            <div class="rounded-xl border-2 cursor-pointer transition-all overflow-hidden ${isSelected?'border-blue-400 bg-blue-50/30 shadow-sm':'border-slate-200 bg-white hover:border-slate-300'}">
                <div onclick="toggleQuestionSelect(${q.id})" class="p-4 ${q.is_risk?'bg-amber-50/50':''}">
                    <div class="flex items-start justify-between mb-2">
                        <div class="flex items-center gap-2 flex-wrap">
                            <div class="w-5 h-5 rounded border-2 flex items-center justify-center text-xs shrink-0 ${isSelected?'border-blue-500 bg-blue-500 text-white':'border-slate-300 bg-white'}">${isSelected?'✓':''}</div>
                            <span class="px-1.5 py-0.5 bg-${diffColor}-100 text-${diffColor}-700 text-[10px] font-bold rounded">${q.difficulty}</span>
                            ${q.is_risk?'<span class="px-1.5 py-0.5 bg-amber-200 text-amber-800 text-[10px] font-bold rounded uppercase">⚠ 위험 신호 검증</span>':''}
                            ${q.skills_assessed&&q.skills_assessed.length?q.skills_assessed.map(s=>`<span class="skill-badge">${s}</span>`).join(''):''}
                        </div>
                        <span class="text-xs text-slate-400 shrink-0">⏱ ~${time}분</span>
                    </div>
                    <h3 class="text-sm font-bold text-slate-800 mb-1">${q.title}</h3>
                    ${q.jd_competency_link?`<div class="text-xs text-blue-600 mb-1">📌 JD 연결: ${q.jd_competency_link}</div>`:''}
                    ${q.generation_rationale?`<div class="text-xs text-slate-400 italic mb-2">${q.generation_rationale}</div>`:''}
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                        <div class="text-xs"><span class="font-bold text-blue-600">왜 중요:</span> <span class="text-slate-600">${q.why_matters}</span></div>
                        <div class="text-xs"><span class="font-bold text-emerald-600">이런 답변을:</span> <span class="text-slate-600">${q.listen_for}</span></div>
                    </div>
                    <div class="mt-2 p-2 bg-slate-50 rounded border border-slate-100">
                        <p class="text-xs text-slate-700">"<strong>${q.question_text}</strong>"</p>
                    </div>
                </div>
            </div>`;
        });

        html += `</div></div>`;
    });

    html += `
    <div class="sticky bottom-0 bg-slate-50 pt-4 pb-2 border-t border-slate-200 mt-4">
        <button onclick="startInterview()" ${selCount===0?'disabled':''} class="w-full py-3 rounded-xl font-bold text-white text-sm transition ${selCount>0?'bg-blue-600 hover:bg-blue-700 shadow-lg':'bg-slate-300 cursor-not-allowed'}">
            인터뷰 시작 (${selCount}개 질문, ~${totalTime}분)
        </button>
    </div>`;

    el.innerHTML = html;
}

function toggleQuestionSelect(qId) {
    const idx = state.selectedQuestions.indexOf(qId);
    if (idx >= 0) state.selectedQuestions.splice(idx, 1);
    else state.selectedQuestions.push(qId);
    renderQuestionSelector();
}

function selectAllQuestions(select) {
    state.selectedQuestions = select ? questions.map(q => q.id) : [];
    renderQuestionSelector();
}

function selectRecommendedSet() {
    state.selectedQuestions = [];
    CATS.forEach(cat => {
        const catQs = questions.filter(q => q.category === cat.id);
        catQs.slice(0, 3).forEach(q => state.selectedQuestions.push(q.id));
    });
    renderQuestionSelector();
}

function startInterview() {
    if (state.selectedQuestions.length === 0) return;
    state.interviewPhase = 'interview';
    showInterviewPhase();
    renderStepper();
    renderSideNav();
    renderQuestions();
    updateScores();
}

function backToSelect() {
    const hasScores = Object.keys(state.scores).length > 0;
    if (hasScores && !confirm('채점 데이터가 초기화됩니다. 질문 선택 화면으로 돌아가시겠습니까?')) return;
    state.scores = {};
    state.fuScores = {};
    state.keywordsChecked = {};
    state.interviewPhase = 'select';
    showInterviewPhase();
    renderQuestionSelector();
}

function showInterviewPhase() {
    const selectEl = document.getElementById('question-select-phase');
    const interviewEl = document.getElementById('question-interview-phase');
    if (state.interviewPhase === 'select') {
        selectEl.style.display = '';
        interviewEl.style.display = 'none';
    } else {
        selectEl.style.display = 'none';
        interviewEl.style.display = '';
    }
}

function getActiveQuestions() {
    if (state.selectedQuestions.length === 0) return questions;
    return questions.filter(q => state.selectedQuestions.includes(q.id));
}

function exportTrainingData() {
    const sc = currentScenario();
    const activeQs = getActiveQuestions();
    const selectionPattern = {};
    CATS.forEach(cat => {
        const catAll = questions.filter(q => q.category === cat.id);
        const catSel = catAll.filter(q => state.selectedQuestions.includes(q.id));
        selectionPattern[cat.id] = { selected: catSel.length, total: catAll.length };
    });
    const scores = {};
    Object.entries(state.scores).forEach(([id, s]) => { scores[id] = { level: s.level, score: s.score }; });

    const main = Object.values(state.scores).reduce((a,b) => a + b.score, 0);
    const bonus = Object.values(state.fuScores).reduce((a,b) => a + b.score, 0);
    const total = main + bonus;
    const maxScore = activeQs.reduce((sum, q) => sum + Math.max(...q.scenarios.map(s=>s.score)), 0);
    const { ratio } = getWeightedScore();
    let recommendation = 'INCOMPLETE';
    if (Object.keys(state.scores).length >= Math.ceil(activeQs.length / 2)) {
        if (ratio >= 0.9) recommendation = 'STRONG_HIRE';
        else if (ratio >= 0.6) recommendation = 'HIRE';
        else if (ratio >= 0.35) recommendation = 'MAYBE';
        else recommendation = 'NO_HIRE';
    }

    const data = {
        candidate: state.scenario,
        candidate_name: sc ? sc.candidate.name : '',
        timestamp: new Date().toISOString(),
        total_questions: questions.length,
        selected_questions: state.selectedQuestions.slice().sort((a,b)=>a-b),
        deselected_questions: questions.map(q=>q.id).filter(id => !state.selectedQuestions.includes(id)).sort((a,b)=>a-b),
        selection_pattern: selectionPattern,
        scores,
        follow_up_scores: Object.assign({}, state.fuScores),
        total_score: total,
        max_score: maxScore,
        recommendation
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `training-data-${state.scenario}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function renderSidebar() {
    const el = document.getElementById('sidebar-candidates');
    if (!el) return;
    el.innerHTML = Object.entries(scenarios).map(([id, sc]) =>
        `<div onclick="switchScenario('${id}')" class="nav-item px-6 py-3 cursor-pointer ${state.scenario===id?'active':''}">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full ${state.scenario===id?'bg-blue-600 text-white':'bg-slate-200 text-slate-600'} flex items-center justify-center text-xs font-bold">${sc.candidate.initials}</div>
                <div>
                    <div class="text-sm font-bold text-slate-800">${sc.candidate.name}</div>
                    <div class="text-xs text-slate-400">${sc.candidate.role} · ${sc.candidate.experience}</div>
                </div>
            </div>
        </div>`
    ).join('');
}

// ===== DYNAMIC RENDER: INTEL =====
function renderIntel() {
    const sc = currentScenario();
    if (!sc) return;
    const intel = sc.intel;
    const el = document.getElementById('view-intel');
    const matchColorMap = {strong:'emerald',match:'emerald',partial:'amber',unknown:'amber',none:'red'};
    const matchIconMap = {strong:'✅',match:'✅',partial:'⚠️',unknown:'⚠️',none:'❌'};
    const matchBorderMap = {strong:'slate',match:'slate',partial:'amber',unknown:'amber',none:'red'};
    el.innerHTML = `
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-blue-50 p-4 rounded-lg border border-blue-100">
                    <div class="text-xs font-bold text-blue-600 uppercase mb-1">${intel.jd_summary.title}</div>
                    <div class="text-xs text-blue-500 mb-3">${intel.jd_summary.subtitle}</div>
                    <div class="text-xs font-bold text-blue-600 uppercase mb-2">핵심 요구사항</div>
                    <ul class="space-y-2 text-sm text-blue-900">
                        ${intel.jd_summary.requirements.map(r => `<li>${r.matched?'✅':'❌'} <strong>${r.text}</strong> — ${r.desc}</li>`).join('')}
                    </ul>
                </div>
                <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <div class="text-xs font-bold text-slate-500 uppercase mb-2">성공 지표 (첫 90일)</div>
                    <ul class="space-y-2 text-sm text-slate-700">
                        ${intel.jd_summary.success_metrics.map(m => `<li>• ${m}</li>`).join('')}
                    </ul>
                </div>
            </div>
            <div class="mt-4 pt-4 border-t border-slate-100">
                <div class="collapsible-toggle flex items-center gap-2 text-xs font-bold text-slate-500 uppercase cursor-pointer" onclick="toggleC(this)">
                    <span class="transform transition-transform">▶</span> 채용공고 원문 보기
                </div>
                <div class="collapsible-content mt-2">
                    <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 text-sm text-slate-600 leading-relaxed">${intel.jd_full}</div>
                </div>
            </div>
            <div class="mt-4">
                <div class="text-xs font-bold text-slate-500 uppercase mb-3">이 직무에 필요한 핵심 역량 <span class="font-normal text-slate-400">— 채용공고에서 추출한 필수 역량과 후보자 매칭 결과</span></div>
                <div class="space-y-2">
                    ${intel.competencies.map(c => `
                    <div class="p-3 bg-white rounded border border-${matchBorderMap[c.match]||'slate'}-200"><div class="flex items-start gap-2"><span class="text-${c.color}-500 mt-0.5">${matchIconMap[c.match]||'✅'}</span><div><div class="text-sm font-bold text-slate-700">${c.name} <span class="text-xs font-normal text-${c.color}-600">(${c.match_label})</span></div><div class="text-xs text-slate-500">${c.desc}</div><div class="text-xs text-blue-600 mt-1">📌 왜 필요한가: ${c.why}</div></div></div></div>`).join('')}
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 class="text-lg font-bold text-slate-800 mb-4">💻 GitHub 기여 활동</h2>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2">
                    <div class="h-40 w-full bg-slate-50 rounded border border-slate-200 p-2"><canvas id="chart-contribution"></canvas></div>
                    <div class="flex gap-4 mt-3 text-xs text-slate-500">
                        <span>기여: <strong>${intel.github.contributions}</strong></span><span>레포: <strong>${intel.github.repos}</strong></span><span>주 언어: <strong>${intel.github.main_languages}</strong></span>
                    </div>
                </div>
                <div class="space-y-3">
                    <div class="p-3 bg-slate-50 rounded border border-slate-200"><div class="text-xs font-bold text-slate-400 uppercase">기술스택 매칭</div><div class="text-sm font-bold text-emerald-600">${intel.github.tech_match}</div><div class="text-xs text-slate-500 mt-1">${intel.github.tech_match_note}</div></div>
                    <div class="p-3 bg-slate-50 rounded border border-slate-200"><div class="text-xs font-bold text-slate-400 uppercase">재직 패턴</div><div class="text-sm font-bold text-slate-800">${intel.github.tenure_pattern}</div><div class="text-xs text-amber-600 mt-1">${intel.github.tenure_note}</div></div>
                    <div class="p-3 bg-amber-50 rounded border border-amber-100"><div class="text-xs font-bold text-amber-600 uppercase">활동 공백</div><div class="text-sm font-bold text-amber-700">${intel.github.activity_gap}</div></div>
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 class="text-lg font-bold text-slate-800 mb-4">👤 LinkedIn 경력</h2>
            <div class="space-y-3">
                ${intel.linkedin.map((l,i) => `<div class="flex items-start gap-4 p-3 bg-slate-50 rounded-lg"><div class="w-10 h-10 rounded ${i===0?'bg-blue-100 text-blue-600':'bg-slate-100 text-slate-600'} flex items-center justify-center font-bold text-sm">${l.initial}</div><div><div class="text-sm font-bold">${l.title}</div><div class="text-xs text-slate-500">${l.company} · ${l.detail}</div></div></div>`).join('')}
            </div>
            <div class="mt-4 p-3 bg-amber-50 rounded border border-amber-100 text-xs text-amber-800">⚠ ${intel.linkedin_warning}</div>
        </div>`;
    setTimeout(renderCharts, 100);
}

// ===== DYNAMIC RENDER: ANALYSIS =====
function renderAnalysis() {
    const sc = currentScenario();
    if (!sc) return;
    const a = sc.analysis;
    const el = document.getElementById('view-analysis');
    const typeColors = {exact:'emerald',similar:'blue',partial:'amber',none:'red'};
    el.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h3 class="font-bold text-slate-800 mb-4">스킬 역량 vs 요구사항</h3>
                <div class="relative h-72"><canvas id="chart-radar"></canvas></div>
            </div>
            <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h3 class="font-bold text-slate-800 mb-4">Engineering DNA</h3>
                <div class="space-y-5">
                    ${a.engineering_dna.map(d => `<div><div class="flex justify-between text-sm mb-1"><span>${d.label}${d.tooltip?' <span class="text-slate-400 text-xs font-normal">('+d.tooltip+')</span>':''}</span><span class="font-bold text-${d.color}-600">${d.display}</span></div><div class="w-full bg-slate-100 rounded-full h-2"><div class="bg-${d.color}-500 h-2 rounded-full" style="width:${d.value}%"></div></div>${d.note?'<div class="text-xs text-slate-400 mt-1">'+d.note+'</div>':''}</div>`).join('')}
                </div>
                <div class="mt-6 p-4 bg-amber-50 rounded-lg border border-amber-100">
                    <div class="text-xs font-bold text-amber-700 uppercase mb-2">리스크 플래그</div>
                    <ul class="text-sm text-amber-800 space-y-1">
                        ${a.risk_flags.map(r => `<li>• <strong>${r.label}:</strong> ${r.detail}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="font-bold text-slate-800 mb-4">스킬 매칭 상세</h3>
            <table class="w-full text-sm">
                <thead><tr class="border-b border-slate-200"><th class="text-left py-2 text-slate-500">요구 스킬</th><th class="text-left py-2 text-slate-500">후보자</th><th class="text-left py-2 text-slate-500">유형</th><th class="text-left py-2 text-slate-500">증거</th><th class="text-right py-2 text-slate-500">신뢰도</th></tr></thead>
                <tbody>
                    ${a.skill_table.map((s,i) => `<tr class="${i<a.skill_table.length-1?'border-b border-slate-100':''}"><td class="py-2 font-medium">${s.skill}</td><td class="text-${(typeColors[s.type]||'slate')}-600 font-medium">${s.candidate}</td><td><span class="px-2 py-0.5 bg-${(typeColors[s.type]||'slate')}-100 text-${(typeColors[s.type]||'slate')}-700 rounded text-xs font-bold">${s.type}</span></td><td class="text-xs text-slate-500">${s.evidence}</td><td class="text-right font-bold">${s.confidence}%</td></tr>`).join('')}
                </tbody>
            </table>
            <div class="mt-4 flex items-center gap-3"><span class="text-sm text-slate-500">전체 매칭:</span><span class="text-2xl font-bold text-blue-600">${a.overall_match}%</span><div class="flex-1 bg-slate-100 rounded-full h-3"><div class="bg-blue-500 h-3 rounded-full" style="width:${a.overall_match}%"></div></div></div>
        </div>`;
    setTimeout(renderCharts, 100);
}

// ===== DYNAMIC RENDER: DECISION =====
function renderDecision() {
    const sc = currentScenario();
    if (!sc) return;
    const d = sc.decision;
    const g = d.interviewer_guide;
    const el = document.getElementById('view-decision');
    el.innerHTML = `
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="font-bold text-slate-800 mb-4">후보자 요약</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="text-center p-3 bg-slate-50 rounded-lg"><div class="text-2xl font-bold text-slate-800">${d.summary.experience}</div><div class="text-xs text-slate-500">경력</div></div>
                <div class="text-center p-3 bg-blue-50 rounded-lg"><div class="text-2xl font-bold text-blue-600">${d.summary.jd_match}</div><div class="text-xs text-blue-500">JD 매칭</div></div>
                <div class="text-center p-3 bg-slate-50 rounded-lg"><div class="text-2xl font-bold text-slate-800">${d.summary.level}</div><div class="text-xs text-slate-500">레벨</div></div>
                <div class="text-center p-3 bg-slate-50 rounded-lg" id="decision-score-card"><div class="text-2xl font-bold" id="decision-total">0</div><div class="text-xs text-slate-500">면접 점수</div></div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-4 bg-emerald-50 rounded-lg border border-emerald-100"><div class="text-xs font-bold text-emerald-700 uppercase mb-2">강점</div><ul class="text-sm text-emerald-800 space-y-1">${d.summary.strengths.map(s=>'<li>• '+s+'</li>').join('')}</ul></div>
                <div class="p-4 bg-amber-50 rounded-lg border border-amber-100"><div class="text-xs font-bold text-amber-700 uppercase mb-2">확인 필요</div><ul class="text-sm text-amber-800 space-y-1">${d.summary.concerns.map(c=>'<li>• '+c+'</li>').join('')}</ul></div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="font-bold text-slate-800 mb-4">카테고리별 점수</h3>
            <div id="category-scores" class="space-y-3"></div>
            <div class="mt-4 pt-4 border-t border-slate-100">
                <div class="flex justify-between text-sm mb-1"><span class="text-emerald-600 font-medium">꼬리질문 보너스</span><span class="font-bold text-emerald-600" id="cat-bonus">0</span></div>
                <div class="w-full bg-slate-100 rounded-full h-2"><div class="bg-emerald-400 h-2 rounded-full transition-all" id="cat-bonus-bar" style="width:0%"></div></div>
            </div>
        </div>
        ${g ? `
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="font-bold text-slate-800 mb-4">면접관 가이드 <span class="text-xs font-normal text-blue-500">— ${sc.candidate.name} 맞춤</span></h3>
            <div class="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
                <div class="text-xs font-bold text-blue-600 uppercase mb-2">면접 진행 흐름</div>
                <p class="text-sm text-blue-800">${g.interview_flow}</p>
                <div class="flex flex-wrap gap-2 mt-3">
                    ${Object.entries(g.time_allocation).map(([k,v]) => `<span class="px-2 py-1 bg-white rounded text-xs text-blue-700 font-medium">${k}: ${v}</span>`).join('')}
                </div>
            </div>
            ${g.resume_based_tips && g.resume_based_tips.length ? `
            <div class="mb-4">
                <div class="text-xs font-bold text-indigo-600 uppercase mb-2">이력서 기반 확인 포인트</div>
                <div class="space-y-2">
                    ${g.resume_based_tips.map(t => `<div class="p-3 bg-indigo-50 rounded border border-indigo-100"><div class="flex items-start gap-2"><span class="text-xs font-bold text-indigo-700 whitespace-nowrap">${t.area}</span><div class="text-xs text-indigo-800">${t.detail} <span class="text-indigo-400">[${t.source}]</span></div></div></div>`).join('')}
                </div>
            </div>` : ''}
            ${g.cover_letter_insights && g.cover_letter_insights.length ? `
            <div class="mb-4">
                <div class="text-xs font-bold text-purple-600 uppercase mb-2">커버레터 검증 포인트</div>
                <div class="space-y-2">
                    ${g.cover_letter_insights.map(c => `<div class="p-3 bg-purple-50 rounded border border-purple-100"><div class="text-xs"><span class="font-bold text-purple-700">주장:</span> ${c.claim}</div><div class="text-xs text-purple-600 mt-1">→ 확인 방법: ${c.verify_with}</div></div>`).join('')}
                </div>
            </div>` : ''}
            ${g.positive_signals&&g.positive_signals.length?`
            <div class="mb-4">
                <div class="text-xs font-bold text-emerald-600 uppercase mb-2">긍정 신호 탐색</div>
                <div class="space-y-2">
                    ${g.positive_signals.map(s => `<div class="p-3 bg-emerald-50 rounded border border-emerald-100 text-xs text-emerald-800">✨ ${s}</div>`).join('')}
                </div>
            </div>`:''}
            <div class="text-xs font-bold text-red-500 uppercase mb-2">주의 신호</div>
            <ul class="text-sm text-red-600 space-y-1">${g.red_flags_to_watch.map(r => '<li>🚩 '+r+'</li>').join('')}</ul>
        </div>` : ''}
        ${d.jd_competency_map&&d.jd_competency_map.length?`
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="font-bold text-slate-800 mb-4">JD 역량 달성도</h3>
            <div class="space-y-4">
                ${d.jd_competency_map.map(c => {
                    const relatedScores = c.related_questions.map(qid => state.scores[qid]).filter(Boolean);
                    const earned = relatedScores.reduce((a,b) => a + b.score, 0);
                    const activeQs = getActiveQuestions();
                    const maxPossible = c.related_questions.reduce((sum, qid) => {
                        const q = activeQs.find(x => x.id === qid);
                        return sum + (q ? Math.max(...q.scenarios.map(s=>s.score)) : 0);
                    }, 0);
                    const pct = maxPossible > 0 ? Math.round((earned / maxPossible) * 100) : 0;
                    return `<div>
                        <div class="flex justify-between text-sm mb-1">
                            <span class="text-slate-700 font-medium">${c.competency} <span class="text-xs text-slate-400">(가중치: ${Math.round(c.weight*100)}%)</span></span>
                            <span class="font-bold ${pct>=70?'text-emerald-600':pct>=40?'text-amber-600':'text-red-600'}">${earned} / ${maxPossible} (${pct}%)</span>
                        </div>
                        <div class="w-full bg-slate-100 rounded-full h-2">
                            <div class="${pct>=70?'bg-emerald-500':pct>=40?'bg-amber-500':'bg-red-500'} h-2 rounded-full transition-all" style="width:${pct}%"></div>
                        </div>
                        <div class="text-xs text-slate-400 mt-1">관련 질문: ${c.related_questions.map(id=>'Q'+id).join(', ')}</div>
                    </div>`;
                }).join('')}
            </div>
        </div>`:''}
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm" id="keyword-summary-card">
            <h3 class="font-bold text-slate-800 mb-2">키워드 달성 현황</h3>
            <p class="text-xs text-slate-400 mb-4">점수에는 반영되지 않습니다. 후보자가 핵심 용어를 얼마나 언급했는지 참고용으로 확인하세요.</p>
            <div class="grid grid-cols-2 gap-4">
                <div class="p-4 bg-red-50 rounded-lg border border-red-100 text-center"><div class="text-2xl font-bold text-red-600" id="kw-must-count">0 / 0</div><div class="text-xs text-red-500 font-medium">필수 키워드 확인</div></div>
                <div class="p-4 bg-blue-50 rounded-lg border border-blue-100 text-center"><div class="text-2xl font-bold text-blue-600" id="kw-good-count">0 / 0</div><div class="text-xs text-blue-500 font-medium">가산 키워드 확인</div></div>
            </div>
        </div>
        <div id="recommendation-card" class="p-8 rounded-xl border-2 border-slate-200 bg-slate-50 text-center">
            <div class="text-sm font-bold uppercase tracking-wider mb-2 text-slate-500" id="rec-label">채점 진행 중</div>
            <div class="text-3xl font-bold mb-2 text-slate-400" id="rec-text">면접을 완료해주세요</div>
            <div class="text-sm text-slate-400" id="rec-detail">질문을 채점하면 추천이 자동 업데이트됩니다.</div>
        </div>
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div class="flex items-center justify-between">
                <div>
                    <h3 class="font-bold text-slate-800">학습 데이터 내보내기</h3>
                    <p class="text-xs text-slate-500 mt-1">질문 선택/비선택 패턴과 채점 데이터를 JSON으로 내보냅니다. 질문 에이전트 파인튜닝에 활용할 수 있습니다.</p>
                </div>
                <button onclick="exportTrainingData()" class="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-bold transition flex items-center gap-2 shrink-0">Export Training Data</button>
            </div>
        </div>`;
}

// ===== INIT =====
window.onload = function() {
    // Register scenarios from external files
    if (window.scenarioAlex) registerScenario('alex', window.scenarioAlex);
    if (window.scenarioSarah) registerScenario('sarah', window.scenarioSarah);
    if (window.scenarioJames) registerScenario('james', window.scenarioJames);
    // Default to first available scenario
    const firstId = Object.keys(scenarios)[0] || 'alex';
    state.scenario = firstId;
    const sc = currentScenario();
    if (sc) {
        if (sc) { questions = sc.questions || []; }
        document.getElementById('header-name').textContent = sc.candidate.name;
        document.getElementById('header-role').textContent = sc.candidate.role;
        document.getElementById('header-context').textContent = sc.candidate.company_context;
    }
    renderTabs();
    renderSidebar();
    renderScenarioSelector();
    renderIntel();
    renderAnalysis();
    renderDecision();
    renderQuestionSelector();
    renderStepper();
    renderSideNav();
    renderQuestions();
    switchTab('view-intel');
    setupScrollSpy();
};

function renderStepper() {
    const activeQs = getActiveQuestions();
    const activeCats = CATS.filter(cat => activeQs.some(q => q.category === cat.id));
    document.getElementById('category-stepper').innerHTML = activeCats.map(cat =>
        `<div class="stepper-item px-3 py-1.5 rounded-full border border-slate-200 text-xs font-medium text-slate-500 cursor-pointer flex items-center gap-1" id="step-${cat.id}" onclick="scrollToSection('${cat.id}')">
            <span>${cat.icon}</span><span class="hidden sm:inline">${cat.label}</span>
        </div>`
    ).join('');
}

function renderSideNav() {
    const activeQs = getActiveQuestions();
    const activeCats = CATS.filter(cat => activeQs.some(q => q.category === cat.id));
    document.getElementById('section-side-nav').innerHTML = activeCats.map(cat => {
        const count = activeQs.filter(q => q.category === cat.id).length;
        return `<a href="#section-${cat.id}" onclick="event.preventDefault();scrollToSection('${cat.id}')" class="section-side-link block px-3 py-2 text-xs text-slate-500" id="side-${cat.id}">
            ${cat.icon} ${cat.label} <span class="text-slate-300">(${count})</span>
        </a>`;
    }).join('');
}

function scrollToSection(catId) {
    const el = document.getElementById('section-' + catId);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function setupScrollSpy() {
    const area = document.getElementById('content-area');
    area.addEventListener('scroll', () => {
        if (state.currentTab !== 'view-interview') return;
        let current = CATS[0].id;
        CATS.forEach(cat => {
            const el = document.getElementById('section-' + cat.id);
            if (el && el.getBoundingClientRect().top < 200) current = cat.id;
        });
        CATS.forEach(cat => {
            const side = document.getElementById('side-' + cat.id);
            const step = document.getElementById('step-' + cat.id);
            if (!side || !step) return;
            const isCurrent = cat.id === current;
            const catScored = getActiveQuestions().filter(q => q.category === cat.id).every(q => state.scores[q.id]);
            side.classList.toggle('active-nav', isCurrent);
            step.classList.toggle('active-step', isCurrent && !catScored);
            step.classList.toggle('done-step', catScored);
        });
    });
}

function renderTabs() {
    const tabs = [{id:'view-intel',label:'1. Intel Brief'},{id:'view-analysis',label:'2. Deep Analysis'},{id:'view-interview',label:'3. Live Interview'},{id:'view-decision',label:'4. Decision'}];
    document.getElementById('main-tabs').innerHTML = tabs.map(t =>
        `<button onclick="switchTab('${t.id}')" class="tab-btn py-4 text-sm font-medium text-slate-500 hover:text-slate-800 ${state.currentTab===t.id?'active':''}">${t.label}</button>`
    ).join('');
}

function switchTab(tabId) {
    state.currentTab = tabId;
    renderTabs();
    ['view-intel','view-analysis','view-interview','view-decision'].forEach(id => document.getElementById(id).classList.add('hidden'));
    document.getElementById(tabId).classList.remove('hidden');
    if (tabId === 'view-intel' || tabId === 'view-analysis') setTimeout(renderCharts, 100);
    if (tabId === 'view-interview') { showInterviewPhase(); if (state.interviewPhase === 'select') renderQuestionSelector(); }
    if (tabId === 'view-decision') { renderCategoryScores(); updateRecommendation(); renderKeywordSummary(); }
}

// ===== QUESTIONS =====
function toggleQuestion(qId) {
    if (state.expandedQuestions.has(qId)) {
        state.expandedQuestions.delete(qId);
    } else {
        state.expandedQuestions.add(qId);
    }
    const body = document.getElementById(`q-body-${qId}`);
    const icon = document.getElementById(`q-toggle-${qId}`);
    if (body) body.classList.toggle('open');
    if (icon) icon.classList.toggle('open');
}

function toggleAltPhrasings(qId) {
    const el = document.getElementById(`alt-phrasings-${qId}`);
    if (el) el.classList.toggle('open');
}

function renderQuestions() {
    const container = document.getElementById('questions-container');
    const activeQs = getActiveQuestions();
    let html = '';
    let qIndex = 0;

    CATS.forEach(cat => {
        const catQuestions = activeQs.filter(q => q.category === cat.id);
        if (!catQuestions.length) return;

        html += `<div class="mb-10" id="section-${cat.id}">
            <div class="flex items-center gap-3 mb-6 pb-3 border-b-2 border-${cat.color}-200">
                <span class="text-2xl">${cat.icon}</span>
                <h2 class="text-xl font-bold text-slate-800">${cat.label}</h2>
                <span class="text-sm text-slate-400">${catQuestions.length}문항</span>
                <span class="ml-auto text-sm font-bold text-${cat.color}-600" id="section-score-${cat.id}">0점</span>
            </div>
            <div class="space-y-8">`;

        catQuestions.forEach(q => {
            qIndex++;
            html += renderQuestion(q, qIndex, activeQs.length);
        });

        html += `</div></div>`;
    });

    container.innerHTML = html;
}

function renderQuestion(q, idx, totalCount) {
    const total = totalCount || getActiveQuestions().length;
    const isRisk = q.is_risk;
    const isExpanded = state.expandedQuestions.has(q.id);
    const isScored = !!state.scores[q.id];
    const filePathHtml = q.code_reference ? (q.code_reference.permalink
        ? `<a href="${q.code_reference.permalink}" target="_blank" class="text-green-400 hover:underline">${q.code_reference.file_path}</a>`
        : `<span class="text-green-400">${q.code_reference.file_path}</span>`) : '';

    return `
    <div class="bg-white rounded-xl border ${isRisk?'border-amber-200':'border-slate-200'} shadow-sm overflow-hidden" id="question-${q.id}">
        <!-- HEADER (always visible, clickable) -->
        <div class="q-header p-6 ${isRisk?'bg-amber-50/50':'bg-slate-50/50'}" onclick="toggleQuestion(${q.id})">
            <div class="flex justify-between items-start mb-2">
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="q-toggle-icon ${isExpanded?'open':''}" id="q-toggle-${q.id}">▶</span>
                    <span class="px-2 py-1 ${isRisk?'bg-amber-200 text-amber-800':'bg-slate-200 text-slate-700'} text-xs font-bold rounded uppercase tracking-wide">${isRisk?'⚠ 위험 신호 검증':CATS.find(c=>c.id===q.category).label}</span>
                    <span class="px-2 py-0.5 ${q.difficulty==='Hard'?'bg-red-100 text-red-700':q.difficulty==='Medium'?'bg-amber-100 text-amber-700':'bg-emerald-100 text-emerald-700'} text-xs font-bold rounded">${q.difficulty}</span>
                    ${q.skills_assessed&&q.skills_assessed.length?q.skills_assessed.map(s=>`<span class="skill-badge">${s}</span>`).join(''):''}
                    ${isScored?'<span class="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs font-bold rounded">✓ 채점됨</span>':''}
                </div>
                <div class="flex items-center gap-2"><span class="text-xs text-slate-300">⏱ ~${q.difficulty==='Hard'?7:q.difficulty==='Medium'?5:3}분</span><span class="text-xs text-slate-400 font-medium">Q${idx} / ${total}</span></div>
            </div>
            ${isRisk&&q.risk_source?`<div class="text-xs text-amber-600 mb-1 italic">탐지 근거: ${q.risk_source}</div>`:''}
            <h3 class="text-xl font-bold text-slate-800">${q.title}</h3>
            ${q.jd_competency_link?`<div class="text-xs text-blue-600 mt-1">📌 JD 연결: ${q.jd_competency_link}</div>`:''}
            ${q.generation_rationale?`<div class="text-xs text-slate-400 mt-1 italic">${q.generation_rationale}</div>`:''}
        </div>

        <!-- BODY (collapsible) -->
        <div class="q-body ${isExpanded?'open':''}" id="q-body-${q.id}">
            <div class="px-6 pb-2 pt-2 border-t border-slate-100">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                <div class="bg-white p-3 rounded border border-slate-200">
                    <div class="text-[10px] font-bold text-blue-600 uppercase mb-1">이 질문이 중요한 이유</div>
                    <p class="text-xs text-slate-700 leading-relaxed">${q.why_matters}</p>
                </div>
                <div class="bg-white p-3 rounded border border-slate-200">
                    <div class="text-[10px] font-bold text-emerald-600 uppercase mb-1">이런 답변을 들어보세요</div>
                    <p class="text-xs text-slate-700 leading-relaxed">${q.listen_for}</p>
                </div>
            </div>

            <div class="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <div class="text-[10px] font-bold text-slate-400 uppercase mb-1">질문 (그대로 읽어주세요)</div>
                <div class="mb-2 text-sm text-slate-500 italic">"${q.context_bridge}"</div>
                <p class="text-lg font-bold text-slate-900">"${q.question_text}"</p>
            </div>

            ${q.alternative_phrasings&&q.alternative_phrasings.length?`
            <div class="mt-3">
                <div class="flex items-center gap-2 text-xs font-bold text-slate-500 cursor-pointer" onclick="event.stopPropagation();toggleAltPhrasings(${q.id})">
                    <span class="transform transition-transform">▶</span> 다른 표현으로 물어보기 (${q.alternative_phrasings.length}개)
                </div>
                <div class="alt-phrasings mt-2" id="alt-phrasings-${q.id}"><div class="space-y-1 pl-4">
                    ${q.alternative_phrasings.map(p=>`<div class="text-sm text-slate-600 italic">"${p}"</div>`).join('')}
                </div></div>
            </div>`:''}

            ${q.code_reference?`
            <div class="mt-4 p-4 bg-slate-900 rounded-lg">
                <div class="text-[10px] font-bold text-slate-400 uppercase mb-2">📁 코드 참조 — 후보자의 실제 코드에서 발견</div>
                <div class="flex items-center gap-2 mb-2 text-xs text-slate-400 flex-wrap">
                    <span class="px-2 py-0.5 bg-slate-800 rounded text-slate-300">📦 ${q.code_reference.repo_name||'api-server'}</span>
                    <span>→</span>
                    ${filePathHtml}
                    ${q.code_reference.line_range?`<span class="text-yellow-400">${q.code_reference.line_range}</span>`:''}
                </div>
                <pre class="text-green-400 text-xs overflow-x-auto"><code>${q.code_reference.snippet}</code></pre>
                ${q.code_reference.plain_language_summary?`<div class="text-xs text-sky-300 mt-2 p-2 bg-slate-800 rounded">💡 <strong>쉬운 설명:</strong> ${q.code_reference.plain_language_summary}</div>`:''}
                <div class="text-xs text-slate-400 mt-1 italic">${q.code_reference.explanation}</div>
            </div>`:''}

            ${q.terminology&&q.terminology.length?`
            <div class="mt-4">
                <div class="collapsible-toggle flex items-center gap-2 text-xs font-bold text-slate-500 uppercase cursor-pointer" onclick="event.stopPropagation();toggleC(this)">
                    <span class="transform transition-transform">▶</span> 용어 설명 (${q.terminology.length}개)
                </div>
                <div class="collapsible-content mt-2"><div class="space-y-2">
                    ${q.terminology.map(t=>{
                        const def = t.definition || t.explanation;
                        const hasPL = t.plain_language && t.plain_language !== def;
                        return `<div class="p-2 bg-white rounded border border-slate-200 text-xs">
                            <span class="font-bold text-slate-800">${t.term}</span> <span class="text-slate-400">[${t.pronunciation}]</span>
                            <span class="text-slate-600 ml-1">${def}</span>
                            ${hasPL?`<div class="text-slate-500 mt-1 italic">쉬운 말로: ${t.plain_language}</div>`:''}
                            ${t.context?`<div class="text-blue-500 mt-1">맥락: ${t.context}</div>`:''}
                        </div>`;
                    }).join('')}
                </div></div>
            </div>`:''}
            </div>

            <div class="p-6">
                <div id="scoring-area-${q.id}">
                <div class="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">답변 채점 (클릭하세요)</div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    ${q.scenarios.map(s=>`
                    <div onclick="event.stopPropagation();rateAnswer(${q.id},'${s.level}',${s.score},'${q.category}')" id="q${q.id}-${s.level}" class="scenario-card bg-white p-4 rounded-lg">
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-sm font-bold ${s.level==='Expert'?'text-emerald-600':s.level==='Mid'?'text-amber-600':'text-red-600'}">${s.level==='Expert'?'🟢 우수':s.level==='Mid'?'🟡 보통':'🔴 미흡'}</span>
                            <span class="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-bold">${s.score>0?'+':''}${s.score}점</span>
                        </div>
                        <p class="text-sm text-slate-600">${s.text}</p>
                    </div>`).join('')}
                </div>

                <!-- Keywords (hidden until scored) -->
                ${q.answer_keywords&&q.answer_keywords.length?`
                <div class="mt-5" id="kw-section-${q.id}" style="display:none">
                    <div class="text-xs font-bold text-slate-400 uppercase mb-2">핵심 키워드 체크 <span class="font-normal text-slate-300">(답변에서 이 단어가 들리면 체크하세요 — 점수에는 반영되지 않고 참고용입니다)</span></div>
                    <div class="flex flex-wrap gap-2">
                        ${q.answer_keywords.map((k,ki)=>`
                        <span onclick="event.stopPropagation();toggleKeyword(${q.id},${ki})" id="kw-${q.id}-${ki}" class="kw-badge unchecked px-3 py-1 rounded-full text-xs font-medium border-2 ${k.importance==='must'?'border-red-300 bg-red-50 text-red-700':'border-blue-300 bg-blue-50 text-blue-700'}" title="${k.explanation}">
                            ${k.importance==='must'?'필수':'가산'} ${k.keyword}
                        </span>`).join('')}
                    </div>
                </div>`:''}

                <!-- Follow-ups (hidden until scored) -->
                <div class="mt-5" id="fu-section-${q.id}" style="display:none">
                    <div class="text-xs font-bold text-slate-400 uppercase mb-3">꼬리질문 <span class="font-normal text-slate-300">(위에서 선택한 답변 수준에 맞는 꼬리질문입니다)</span></div>
                    <div class="space-y-3">
                        ${q.follow_ups.map(fu => {
                            const triggerLabel = fu.trigger==='Expert'?'📗 우수 답변 시':fu.trigger==='Mid'?'📙 보통 답변 시':'📕 미흡 답변 시';
                            const triggerColor = fu.trigger==='Expert'?'emerald':fu.trigger==='Mid'?'amber':'red';
                            return `
                        <div class="fu-card p-4 rounded-lg border border-slate-200 bg-slate-50" id="fu-${fu.id}" data-trigger="${fu.trigger}">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="text-xs font-bold text-${triggerColor}-600 bg-${triggerColor}-100 px-2 py-0.5 rounded">${triggerLabel}</span>
                            </div>
                            <p class="text-sm font-bold text-slate-800 mb-2">"${fu.question_text}"</p>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
                                <div class="text-xs"><span class="font-bold text-blue-600">왜 중요:</span> ${fu.why_matters}</div>
                                <div class="text-xs"><span class="font-bold text-emerald-600">들어볼 것:</span> ${fu.listen_for}</div>
                            </div>
                            <div class="flex gap-2">
                                <button onclick="event.stopPropagation();rateFU('${fu.id}',${fu.good.score},'good','${q.category}')" id="fu-${fu.id}-good" class="flex-1 p-2 rounded border border-emerald-200 bg-emerald-50 text-xs hover:bg-emerald-100 transition">
                                    <span class="font-bold text-emerald-700">👍 좋은 답변</span> <span class="text-emerald-600">(+${fu.good.score})</span>
                                    <div class="text-emerald-600 mt-1">${fu.good.text}</div>
                                </button>
                                <button onclick="event.stopPropagation();rateFU('${fu.id}',${fu.poor.score},'poor','${q.category}')" id="fu-${fu.id}-poor" class="flex-1 p-2 rounded border border-red-200 bg-red-50 text-xs hover:bg-red-100 transition">
                                    <span class="font-bold text-red-700">👎 부족한 답변</span> <span class="text-red-600">(${fu.poor.score>=0?'+':''}${fu.poor.score})</span>
                                    <div class="text-red-600 mt-1">${fu.poor.text}</div>
                                </button>
                            </div>
                        </div>`;
                        }).join('')}
                    </div>
                </div>

                <!-- Interviewer Note (hidden until scored) -->
                <div class="mt-5" id="note-section-${q.id}" style="display:none">
                    <div class="collapsible-toggle flex items-center gap-2 text-xs font-bold text-slate-500 uppercase cursor-pointer" onclick="event.stopPropagation();toggleC(this)">
                        <span class="transform transition-transform">▶</span> 면접관 참고 노트
                    </div>
                    <div class="collapsible-content mt-2">
                        <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-4">
                            ${q.interviewer_note?`
                            <div>
                                <div class="text-[10px] font-bold text-indigo-600 uppercase mb-1">🔍 비개발자 관점 해석</div>
                                <p class="text-sm text-slate-700">${q.interviewer_note.business_interpretation}</p>
                            </div>
                            <div>
                                <div class="text-[10px] font-bold text-amber-600 uppercase mb-1">💡 일상 비유로 이해하기</div>
                                <p class="text-sm text-slate-600">${q.interviewer_note.daily_analogy}</p>
                            </div>
                            <div>
                                <div class="text-[10px] font-bold text-emerald-600 uppercase mb-1">📊 이 직급에서 기대하는 수준</div>
                                <p class="text-sm text-slate-600">${q.interviewer_note.level_expectation}</p>
                            </div>
                            `:''}
                            ${q.expected_answer.depth_expectations?`
                            <div>
                                <div class="text-[10px] font-bold text-purple-600 uppercase mb-1">🎯 답변 깊이 기대치</div>
                                <p class="text-sm text-slate-600">${q.expected_answer.depth_expectations}</p>
                            </div>`:''}
                            <div class="pt-3 border-t border-slate-200">
                                <div class="text-[10px] font-bold text-blue-600 uppercase mb-1">✅ 좋은 답변의 핵심 포인트</div>
                                <p class="text-sm text-slate-700">${q.expected_answer.core.replace(/\n/g,'<br>')}</p>
                            </div>
                            <div>
                                <div class="text-[10px] font-bold text-slate-500 uppercase mb-1">💬 이런 수준의 답변이 나오면 우수합니다</div>
                                <p class="text-sm text-slate-600 italic bg-white p-3 rounded border border-slate-200">"${q.expected_answer.example}"</p>
                            </div>
                        </div>
                    </div>
                </div>
                </div>
            </div>
        </div>
    </div>`;
}

// ===== INTERACTIONS =====
function toggleC(el) {
    const c = el.nextElementSibling;
    const a = el.querySelector('span');
    c.classList.toggle('open');
    a.style.transform = c.classList.contains('open') ? 'rotate(90deg)' : '';
}

function rateAnswer(qId, level, score, category) {
    state.scores[qId] = { score, level, category };
    ['Expert','Mid','Low'].forEach(l => {
        const el = document.getElementById(`q${qId}-${l}`);
        if (el) el.className = 'scenario-card bg-white p-4 rounded-lg opacity-40';
    });
    const cls = level==='Expert'?'selected-expert':level==='Mid'?'selected-mid':'selected-low';
    const sel = document.getElementById(`q${qId}-${level}`);
    if (sel) sel.className = `scenario-card p-4 rounded-lg ${cls} opacity-100`;

    // Show keyword section
    const kwSection = document.getElementById(`kw-section-${qId}`);
    if (kwSection) kwSection.style.display = '';

    // Show follow-up section and only matching follow-up
    const fuSection = document.getElementById(`fu-section-${qId}`);
    if (fuSection) {
        fuSection.style.display = '';
        fuSection.querySelectorAll('.fu-card').forEach(card => {
            const trigger = card.dataset.trigger;
            if (trigger === level || trigger === 'any') {
                card.style.display = '';
                card.classList.add('highlighted');
                card.style.borderLeftColor = level==='Expert'?'#10b981':level==='Mid'?'#f59e0b':'#ef4444';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Show interviewer note section
    const noteSection = document.getElementById(`note-section-${qId}`);
    if (noteSection) noteSection.style.display = '';

    // Auto-collapse scored question after a short delay
    setTimeout(() => {
        if (state.expandedQuestions.has(qId)) {
            state.expandedQuestions.delete(qId);
            const body = document.getElementById(`q-body-${qId}`);
            const icon = document.getElementById(`q-toggle-${qId}`);
            if (body) body.classList.remove('open');
            if (icon) icon.classList.remove('open');
        }
    }, 800);

    updateScores();
}

function rateFU(fuId, score, type, category) {
    state.fuScores[fuId] = { score, type, category };
    const goodEl = document.getElementById(`fu-${fuId}-good`);
    const poorEl = document.getElementById(`fu-${fuId}-poor`);
    if (type === 'good') {
        goodEl.style.boxShadow = '0 0 0 2px #10b981';
        goodEl.style.opacity = '1';
        poorEl.style.boxShadow = '';
        poorEl.style.opacity = '0.4';
    } else {
        poorEl.style.boxShadow = '0 0 0 2px #ef4444';
        poorEl.style.opacity = '1';
        goodEl.style.boxShadow = '';
        goodEl.style.opacity = '0.4';
    }
    updateScores();
}

function toggleKeyword(qId, ki) {
    const key = `${qId}-${ki}`;
    state.keywordsChecked[key] = !state.keywordsChecked[key];
    const el = document.getElementById(`kw-${qId}-${ki}`);
    if (state.keywordsChecked[key]) {
        el.classList.remove('unchecked');
        el.classList.add('checked');
        el.style.opacity = '1';
        el.style.boxShadow = '0 0 0 2px currentColor';
    } else {
        el.classList.remove('checked');
        el.classList.add('unchecked');
        el.style.opacity = '0.6';
        el.style.boxShadow = '';
    }
}

function updateScores() {
    const activeQs = getActiveQuestions();
    const mainTotal = Object.values(state.scores).reduce((a,b) => a + b.score, 0);
    const bonusTotal = Object.values(state.fuScores).reduce((a,b) => a + b.score, 0);
    const maxTotal = activeQs.reduce((sum, q) => sum + Math.max(...q.scenarios.map(s=>s.score)), 0);
    document.getElementById('total-score').innerHTML = `${mainTotal} <span class="text-sm text-slate-300 font-normal">/ ${maxTotal}</span>`;
    document.getElementById('bonus-score').textContent = bonusTotal >= 0 ? `+${bonusTotal}` : bonusTotal;

    // Section scores
    CATS.forEach(cat => {
        const catMain = Object.values(state.scores).filter(s => s.category === cat.id).reduce((a,b) => a + b.score, 0);
        const catBonus = Object.values(state.fuScores).filter(s => s.category === cat.id).reduce((a,b) => a + b.score, 0);
        const el = document.getElementById(`section-score-${cat.id}`);
        if (el) el.textContent = `${catMain}점${catBonus?` (+${catBonus})`:''}`;
    });

    if (document.getElementById('decision-total')) {
        const { ratio } = getWeightedScore();
        const pct = Math.round(ratio * 100);
        document.getElementById('decision-total').innerHTML = `${mainTotal + bonusTotal} <span class="text-xs font-normal text-slate-400">(${pct}%)</span>`;
        const scoreCard = document.getElementById('decision-score-card');
        if (scoreCard) scoreCard.className = `text-center p-3 rounded-lg ${ratio>=0.9?'bg-emerald-50':ratio>=0.6?'bg-blue-50':ratio>=0.35?'bg-amber-50':'bg-red-50'}`;
    }
    // Progress bar
    const answered = Object.keys(state.scores).length;
    const pLabel = document.getElementById('progress-label');
    const pBar = document.getElementById('progress-bar');
    const pTime = document.getElementById('progress-time');
    if (pLabel) pLabel.textContent = `${answered} / ${activeQs.length} 질문 채점 완료`;
    if (pBar) pBar.style.width = `${activeQs.length>0?Math.round(answered/activeQs.length*100):0}%`;
    if (pTime) {
        const remaining = activeQs.filter(q => !state.scores[q.id]);
        const mins = remaining.reduce((a,q) => a + (q.difficulty==='Hard'?7:q.difficulty==='Medium'?5:3), 0);
        pTime.textContent = remaining.length ? `예상 잔여: ~${mins}분` : '✅ 완료!';
    }
}

// ===== TAB 4: DECISION =====
function getWeightedScore() {
    const sc = currentScenario();
    const weights = sc && sc.category_weights ? sc.category_weights : null;
    const activeQs = getActiveQuestions();
    if (!weights) {
        // Fallback: simple ratio
        const total = Object.values(state.scores).reduce((a,b) => a + b.score, 0)
            + Object.values(state.fuScores).reduce((a,b) => a + b.score, 0);
        const max = activeQs.reduce((sum, q) => sum + Math.max(...q.scenarios.map(s=>s.score)), 0);
        return { ratio: max > 0 ? total / max : 0, weights: null };
    }
    let weightedSum = 0;
    let weightTotal = 0;
    CATS.forEach(cat => {
        const w = weights[cat.id] || 0;
        const catQs = activeQs.filter(q => q.category === cat.id);
        if (!catQs.length) return;
        const earned = Object.values(state.scores).filter(s => s.category === cat.id).reduce((a,b) => a + b.score, 0);
        const catBonus = Object.values(state.fuScores).filter(s => s.category === cat.id).reduce((a,b) => a + b.score, 0);
        const max = catQs.reduce((sum, q) => sum + Math.max(...q.scenarios.map(s=>s.score)), 0);
        const catRatio = max > 0 ? (earned + catBonus) / max : 0;
        weightedSum += catRatio * w;
        weightTotal += w;
    });
    return { ratio: weightTotal > 0 ? weightedSum / weightTotal : 0, weights };
}

function renderCategoryScores() {
    const container = document.getElementById('category-scores');
    if (!container) return;
    const activeQs = getActiveQuestions();
    const sc = currentScenario();
    const weights = sc && sc.category_weights ? sc.category_weights : {};
    const maxScores = {};
    activeQs.forEach(q => { const max = Math.max(...q.scenarios.map(s=>s.score)); maxScores[q.category] = (maxScores[q.category]||0) + max; });
    container.innerHTML = CATS.map(cat => {
        const earned = Object.values(state.scores).filter(s=>s.category===cat.id).reduce((a,b)=>a+b.score,0);
        const max = maxScores[cat.id]||1;
        const pct = Math.max(0, Math.round((earned/max)*100));
        const w = weights[cat.id];
        const weightLabel = w ? ` <span class="text-xs text-slate-400 font-normal">(가중치 ${Math.round(w*100)}%)</span>` : '';
        return `<div><div class="flex justify-between text-sm mb-1"><span class="text-slate-600">${cat.icon} ${cat.label}${weightLabel}</span><span class="font-bold">${earned} / ${max}</span></div><div class="w-full bg-slate-100 rounded-full h-2"><div class="bg-${cat.color}-500 h-2 rounded-full transition-all" style="width:${pct}%"></div></div></div>`;
    }).join('');

    const bonus = Object.values(state.fuScores).reduce((a,b)=>a+b.score,0);
    document.getElementById('cat-bonus').textContent = bonus >= 0 ? `+${bonus}` : bonus;
    document.getElementById('cat-bonus-bar').style.width = `${Math.min(100, Math.max(0, (bonus/50)*100))}%`;
}

function updateRecommendation() {
    const activeQs = getActiveQuestions();
    const main = Object.values(state.scores).reduce((a,b)=>a+b.score,0);
    const bonus = Object.values(state.fuScores).reduce((a,b)=>a+b.score,0);
    const total = main + bonus;
    const answered = Object.keys(state.scores).length;
    const card = document.getElementById('recommendation-card');
    const label = document.getElementById('rec-label');
    const text = document.getElementById('rec-text');
    const detail = document.getElementById('rec-detail');

    const { ratio } = getWeightedScore();
    const pctDisplay = Math.round(ratio * 100);
    if (answered < Math.ceil(activeQs.length / 2)) {
        card.className='p-8 rounded-xl border-2 border-slate-200 bg-slate-50 text-center';
        label.textContent=`${answered}/${activeQs.length} 질문 채점 완료`; label.className='text-sm font-bold uppercase tracking-wider mb-2 text-slate-500';
        text.textContent='면접을 완료해주세요'; text.className='text-3xl font-bold mb-2 text-slate-400';
        detail.textContent=`최소 ${Math.ceil(activeQs.length/2)}개 이상 채점하면 추천이 표시됩니다.`;
    } else if (ratio >= 0.9) {
        card.className='p-8 rounded-xl border-2 border-emerald-300 bg-emerald-50 text-center';
        label.textContent='STRONG HIRE'; label.className='text-sm font-bold uppercase tracking-wider mb-2 text-emerald-600';
        text.textContent='강력 추천'; text.className='text-3xl font-bold mb-2 text-emerald-700';
        detail.textContent=`총점 ${total}점 (가중 ${pctDisplay}%). 핵심 역량과 리더십 잠재력이 모두 우수합니다. 빠른 의사결정을 권장합니다.`;
    } else if (ratio >= 0.6) {
        card.className='p-8 rounded-xl border-2 border-blue-300 bg-blue-50 text-center';
        label.textContent='HIRE'; label.className='text-sm font-bold uppercase tracking-wider mb-2 text-blue-600';
        text.textContent='채용 추천'; text.className='text-3xl font-bold mb-2 text-blue-700';
        detail.textContent=`총점 ${total}점 (가중 ${pctDisplay}%). 전반적으로 역량이 충분합니다. 약점 영역에 대한 보완 계획을 확인하세요.`;
    } else if (ratio >= 0.35) {
        card.className='p-8 rounded-xl border-2 border-amber-300 bg-amber-50 text-center';
        label.textContent='MAYBE'; label.className='text-sm font-bold uppercase tracking-wider mb-2 text-amber-600';
        text.textContent='추가 검토 필요'; text.className='text-3xl font-bold mb-2 text-amber-700';
        detail.textContent=`총점 ${total}점 (가중 ${pctDisplay}%). 일부 강점이 있으나 주요 역량에서 부족함이 있습니다. 2차 면접을 고려하세요.`;
    } else {
        card.className='p-8 rounded-xl border-2 border-red-300 bg-red-50 text-center';
        label.textContent='NO HIRE'; label.className='text-sm font-bold uppercase tracking-wider mb-2 text-red-600';
        text.textContent='채용 비추천'; text.className='text-3xl font-bold mb-2 text-red-700';
        detail.textContent=`총점 ${total}점 (가중 ${pctDisplay}%). 핵심 역량이 요구 수준에 미달합니다.`;
    }
}

// ===== KEYWORD SUMMARY =====
function renderKeywordSummary() {
    let mustTotal=0, mustChecked=0, goodTotal=0, goodChecked=0;
    const activeQs = getActiveQuestions();
    activeQs.forEach(q => {
        if (!q.answer_keywords) return;
        q.answer_keywords.forEach((k,ki) => {
            if (k.importance==='must') { mustTotal++; if (state.keywordsChecked[`${q.id}-${ki}`]) mustChecked++; }
            else { goodTotal++; if (state.keywordsChecked[`${q.id}-${ki}`]) goodChecked++; }
        });
    });
    const m = document.getElementById('kw-must-count');
    const g = document.getElementById('kw-good-count');
    if (m) m.textContent = `${mustChecked} / ${mustTotal}`;
    if (g) g.textContent = `${goodChecked} / ${goodTotal}`;
}

// ===== CHARTS =====
function renderCharts() {
    if(charts['contribution']) charts['contribution'].destroy();
    if(charts['radar']) charts['radar'].destroy();
    const sc = currentScenario();
    const chartData = sc ? sc.intel.github.chart_data : [12,19,3,5,2,3,45,60,55,40,25,30];
    const radarCandidate = sc ? sc.analysis.radar_candidate : [90,85,40,80,85];
    const radarRequired = sc ? sc.analysis.radar_required : [80,80,60,70,70];
    const ctx1 = document.getElementById('chart-contribution');
    if(ctx1) {
        charts['contribution'] = new Chart(ctx1, {
            type:'bar', data:{ labels:['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'],
            datasets:[{label:'Commits',data:chartData,backgroundColor:ctx=>ctx.raw<5?'#fca5a5':'#93c5fd',borderRadius:2}]},
            options:{maintainAspectRatio:false,scales:{x:{display:false},y:{display:false}},plugins:{legend:{display:false}}}
        });
    }
    const ctx2 = document.getElementById('chart-radar');
    if(ctx2) {
        charts['radar'] = new Chart(ctx2, {
            type:'radar', data:{labels:['Backend','System Design','DevOps','Leadership','Product Sense'],
            datasets:[{label:'후보자',data:radarCandidate,backgroundColor:'rgba(37,99,235,0.2)',borderColor:'#2563eb',pointBackgroundColor:'#2563eb'},
                      {label:'요구수준',data:radarRequired,borderColor:'#94a3b8',borderDash:[5,5],fill:false,pointRadius:0}]},
            options:{maintainAspectRatio:false}
        });
    }
}
