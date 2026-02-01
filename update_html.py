#!/usr/bin/env python3
"""
Updates index.html with the requested enhancements
"""

with open('/Users/byeonsanghun/goinfre/verdict/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Find and replace the Interview tab section
old_interview_section = '''            <!-- TAB 3: LIVE INTERVIEW -->
            <div id="view-interview" class="fade-in hidden">
                <div class="bg-indigo-50 border-l-4 border-indigo-500 p-4 rounded-r-lg mb-6">
                    <h3 class="text-sm font-bold text-indigo-900 uppercase">비개발자 면접관을 위한 안내</h3>
                    <p class="text-sm text-indigo-800 mt-1">개발 용어를 모르셔도 됩니다. 각 질문의 <strong>"이 질문이 중요한 이유"</strong>와 <strong>"이런 답변을 들어보세요"</strong>를 참고하세요. 질문을 그대로 읽어주시면 됩니다. 답변 후 해당하는 수준을 클릭하면 <strong>맞춤 꼬리질문</strong>이 자동으로 표시됩니다.</p>
                </div>
                <div id="questions-container"></div>
            </div>'''

new_interview_section = '''            <!-- TAB 3: LIVE INTERVIEW -->
            <div id="view-interview" class="fade-in hidden">
                <div class="bg-indigo-50 border-l-4 border-indigo-500 p-4 rounded-r-lg mb-6">
                    <h3 class="text-sm font-bold text-indigo-900 uppercase">비개발자 면접관을 위한 안내</h3>
                    <p class="text-sm text-indigo-800 mt-1">개발 용어를 모르셔도 됩니다. 각 질문의 <strong>"이 질문이 중요한 이유"</strong>와 <strong>"이런 답변을 들어보세요"</strong>를 참고하세요. 질문을 그대로 읽어주시면 됩니다. 답변 후 해당하는 수준을 클릭하면 <strong>맞춤 꼬리질문</strong>이 자동으로 표시됩니다.</p>
                </div>

                <!-- Progress Bar -->
                <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm mb-6">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-sm font-bold text-slate-700" id="progress-text">0/10 질문 채점 완료</span>
                        <span class="text-xs text-slate-500">예상 소요: <span id="total-estimated-time">~60분</span></span>
                    </div>
                    <div class="w-full bg-slate-200 rounded-full h-3">
                        <div id="progress-bar" class="bg-blue-500 h-3 rounded-full transition-all duration-300" style="width:0%"></div>
                    </div>
                </div>

                <!-- Interview Flow Stepper -->
                <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm mb-6">
                    <div class="flex items-center justify-between gap-4" id="interview-stepper">
                        <div class="stepper-item flex-1 text-center py-2 px-3 rounded border-2 border-slate-300 text-xs font-medium transition-all cursor-pointer" onclick="scrollToCategory('role_fit')">
                            🎯 역할 적합성
                        </div>
                        <div class="stepper-item flex-1 text-center py-2 px-3 rounded border-2 border-slate-300 text-xs font-medium transition-all cursor-pointer" onclick="scrollToCategory('technical_depth')">
                            ⚙️ 기술 역량
                        </div>
                        <div class="stepper-item flex-1 text-center py-2 px-3 rounded border-2 border-slate-300 text-xs font-medium transition-all cursor-pointer" onclick="scrollToCategory('execution_ownership')">
                            🚀 실행력
                        </div>
                        <div class="stepper-item flex-1 text-center py-2 px-3 rounded border-2 border-slate-300 text-xs font-medium transition-all cursor-pointer" onclick="scrollToCategory('communication')">
                            💬 소통
                        </div>
                        <div class="stepper-item flex-1 text-center py-2 px-3 rounded border-2 border-slate-300 text-xs font-medium transition-all cursor-pointer" onclick="scrollToCategory('risk_flags')">
                            ⚠️ 위험 신호
                        </div>
                    </div>
                </div>

                <div class="flex gap-6">
                    <!-- Main Content -->
                    <div class="flex-1" id="questions-container"></div>

                    <!-- Right Side Navigation -->
                    <div class="w-48">
                        <div class="section-side-nav">
                            <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                                <div class="text-xs font-bold text-slate-400 uppercase mb-3">카테고리</div>
                                <div class="space-y-2" id="side-nav-links">
                                    <!-- Will be populated by JS -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>'''

content = content.replace(old_interview_section, new_interview_section)

# 2. Update Decision tab score card section
old_decision_score = '''                        <div class="text-center p-3 bg-slate-50 rounded-lg" id="decision-score-card"><div class="text-2xl font-bold" id="decision-total">0</div><div class="text-xs text-slate-500">면접 점수</div></div>'''

new_decision_score = '''                        <div class="text-center p-3 bg-slate-50 rounded-lg transition-all" id="decision-score-card"><div class="text-2xl font-bold" id="decision-total">0</div><div class="text-xs text-slate-500">면접 점수</div></div>'''

content = content.replace(old_decision_score, new_decision_score)

# 3. Add keyword summary to Decision tab - find the category scores section and add after it
old_cat_scores_section = '''                <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h3 class="font-bold text-slate-800 mb-4">카테고리별 점수</h3>
                    <div id="category-scores" class="space-y-3"></div>
                    <div class="mt-4 pt-4 border-t border-slate-100">
                        <div class="flex justify-between text-sm mb-1"><span class="text-emerald-600 font-medium">꼬리질문 보너스</span><span class="font-bold text-emerald-600" id="cat-bonus">0</span></div>
                        <div class="w-full bg-slate-100 rounded-full h-2"><div class="bg-emerald-400 h-2 rounded-full transition-all" id="cat-bonus-bar" style="width:0%"></div></div>
                    </div>
                </div>'''

new_cat_scores_section = '''                <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h3 class="font-bold text-slate-800 mb-4">카테고리별 점수</h3>
                    <div id="category-scores" class="space-y-3"></div>
                    <div class="mt-4 pt-4 border-t border-slate-100">
                        <div class="flex justify-between text-sm mb-1"><span class="text-emerald-600 font-medium">꼬리질문 보너스</span><span class="font-bold text-emerald-600" id="cat-bonus">0</span></div>
                        <div class="w-full bg-slate-100 rounded-full h-2"><div class="bg-emerald-400 h-2 rounded-full transition-all" id="cat-bonus-bar" style="width:0%"></div></div>
                    </div>
                    <div class="mt-4 pt-4 border-t border-slate-100">
                        <div class="text-xs font-bold text-slate-400 uppercase mb-2">키워드 확인 현황</div>
                        <div class="flex gap-4 text-sm">
                            <span class="text-red-600 font-medium">필수 키워드: <strong id="kw-must-count">0/0</strong></span>
                            <span class="text-blue-600 font-medium">가산 키워드: <strong id="kw-bonus-count">0/0</strong></span>
                        </div>
                    </div>
                </div>'''

content = content.replace(old_cat_scores_section, new_cat_scores_section)

# Write updated content
with open('/Users/byeonsanghun/goinfre/verdict/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML structure updated successfully!")
