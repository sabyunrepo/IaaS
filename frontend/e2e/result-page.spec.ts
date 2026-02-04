import { test, expect } from '@playwright/test'

/**
 * ResultPage E2E Tests
 * 4-Tab UI (v2) 구조 테스트: Intel Brief → Deep Analysis → Live Interview → Decision
 */

test.describe('ResultPage - 4 Tab UI', () => {
  // Mock API response for v2 format
  const mockV2Response = {
    job_id: 'test-job-123',
    generated_at: new Date().toISOString(),
    output_language: 'ko',
    candidate_summary: {
      name: '홍길동',
      current_title: '시니어 백엔드 개발자',
      years_experience: 5,
      key_skills: ['Python', 'FastAPI', 'PostgreSQL'],
      education: '서울대학교 컴퓨터공학과',
      key_achievements: ['대규모 API 설계', '성능 최적화 50% 개선'],
    },
    intel: {
      jd_summary: {
        title: '백엔드 개발자',
        subtitle: '핀테크 스타트업',
        requirements: [
          { text: 'Python 3년 이상', desc: '백엔드 개발 경험', matched: true },
          { text: 'FastAPI 경험', desc: 'REST API 개발', matched: true },
        ],
        success_metrics: ['API 응답시간 100ms 이하', '테스트 커버리지 80%'],
      },
      competencies: [
        {
          name: 'Python 개발',
          match: 'strong',
          match_label: '강점',
          desc: 'Python 기반 백엔드 개발 능력',
          why: 'FastAPI 서비스 개발에 필수',
          color: 'emerald',
          icon: '✅',
        },
        {
          name: 'DB 설계',
          match: 'match',
          match_label: '일치',
          desc: '데이터베이스 스키마 설계',
          why: 'PostgreSQL 기반 서비스 운영',
          color: 'green',
          icon: '✅',
        },
      ],
      github: {
        contributions: 1234,
        repos: 45,
        main_languages: 'Python, TypeScript',
        tech_match: '높음',
        tech_match_note: 'JD 요구 기술과 높은 일치도',
        tenure_pattern: '안정적',
        tenure_note: '평균 2.5년 재직',
        activity_gap: null,
        chart_data: [50, 60, 45, 80, 90, 100, 75, 85, 95, 88, 92, 78],
      },
      linkedin: [
        { company: 'ABC 테크', role: '시니어 개발자', period: '2022-현재' },
        { company: 'XYZ 스타트업', role: '개발자', period: '2019-2022' },
      ],
      linkedin_warning: null,
    },
    analysis: {
      radar_candidate: [85, 80, 75, 70, 65],
      radar_required: [80, 75, 70, 75, 60],
      engineering_dna: [
        { label: '테스트 커버리지', value: 82, display: '82%', color: 'emerald', note: '우수', tooltip: '단위 테스트 커버리지' },
        { label: '코드 리뷰 참여', value: 90, display: '90%', color: 'emerald', note: '우수', tooltip: 'PR 리뷰 참여율' },
        { label: '문서화', value: 65, display: '65%', color: 'amber', note: '보통', tooltip: 'README 및 API 문서화' },
      ],
      risk_flags: [],
      skill_table: [
        { skill: 'Python', candidate: 'Python 3.11', type: 'exact', evidence: 'GitHub', confidence: 95 },
        { skill: 'FastAPI', candidate: 'FastAPI', type: 'exact', evidence: '이력서', confidence: 90 },
        { skill: 'PostgreSQL', candidate: 'PostgreSQL', type: 'exact', evidence: 'GitHub', confidence: 85 },
      ],
      overall_match: 82,
    },
    questions: [
      {
        id: 'q1',
        title: '첫 90일 우선순위',
        category: 'behavioral',
        difficulty: 'mid',
        question_text: '입사 후 첫 90일 동안 어떤 우선순위로 업무를 진행하시겠습니까?',
        why_matters: '온보딩 역량과 전략적 사고력 평가',
        listen_for: '체계적 접근, 팀 협업, 비즈니스 이해',
        answer_keywords: [
          { keyword: '온보딩', importance: 'must', explanation: '체계적 적응 계획' },
          { keyword: '팀 이해', importance: 'good_to_have', explanation: '협업 중시' },
        ],
        scenarios: [
          { level: 'Expert', score: 20, text: '구체적 90일 계획 제시', depth_expectations: '주차별 목표 명확' },
          { level: 'Mid', score: 12, text: '기본적인 계획 제시', depth_expectations: '일반적 접근' },
          { level: 'Low', score: 5, text: '모호한 답변', depth_expectations: '구체성 부족' },
        ],
        follow_ups: [
          {
            id: 'q1-f1',
            trigger: 'Expert',
            question_text: '예상되는 어려움과 대응 전략은?',
            why_matters: '문제 해결 능력',
            listen_for: '사전 대비, 리스크 관리',
            good: { text: '구체적 리스크 식별', score: 8 },
            poor: { text: '문제 인식 부족', score: 2 },
          },
        ],
        terminology: [],
        interviewer_note: {
          business_interpretation: '신규 입사자의 전략적 사고력을 평가합니다',
          daily_analogy: '새 집으로 이사했을 때 정착 계획과 비슷합니다',
          level_expectation: '시니어: 구체적 실행계획, 주니어: 학습 의지',
        },
        is_risk: false,
      },
      {
        id: 'q2',
        title: 'API 설계 경험',
        category: 'technical',
        difficulty: 'hard',
        question_text: '대규모 트래픽을 처리하는 API를 설계한 경험을 설명해주세요.',
        why_matters: '기술적 깊이와 실무 경험 평가',
        listen_for: '확장성, 캐싱, 로드밸런싱',
        answer_keywords: [
          { keyword: '캐싱', importance: 'must', explanation: '성능 최적화' },
          { keyword: '로드밸런싱', importance: 'good_to_have', explanation: '트래픽 분산' },
        ],
        scenarios: [
          { level: 'Expert', score: 25, text: '구체적 아키텍처 설명', depth_expectations: '수치 기반 성능 개선' },
          { level: 'Mid', score: 15, text: '일반적 접근 설명', depth_expectations: '기본 개념 이해' },
          { level: 'Low', score: 5, text: '경험 부족', depth_expectations: '이론적 지식만' },
        ],
        follow_ups: [],
        terminology: [
          { term: 'CDN', definition: 'Content Delivery Network, 콘텐츠 전송 네트워크' },
        ],
        interviewer_note: {
          business_interpretation: '실제 프로덕션 경험을 검증합니다',
          daily_analogy: '고속도로 톨게이트 병목 해결과 비슷합니다',
          level_expectation: '시니어: 직접 설계 경험, 주니어: 학습 경험',
        },
        is_risk: false,
      },
    ],
    decision: {
      summary: {
        experience: '5년',
        jd_match: '높음',
        level: '시니어',
        strengths: ['Python 전문성', 'API 설계 경험', '팀 협업 능력'],
        concerns: ['프론트엔드 경험 부족', '대기업 경험 없음'],
      },
      interviewer_guide: {
        interview_flow: '기술 심층 → 행동 면접 → 문화 적합성',
        time_allocation: { '기술 심층': '40분', '행동 면접': '15분', '문화 적합성': '5분' },
        resume_based_tips: [
          { section: '경력', insight: 'API 설계 경험 심층 확인', question_link: 'Q2 참조' },
        ],
        cover_letter_insights: [],
        red_flags_to_watch: ['기술 깊이 부족 시 추가 검증'],
        positive_signals: ['구체적 수치 기반 답변', '팀 협업 사례'],
      },
      jd_competency_map: [
        { competency: 'Python 개발', weight: 0.3, related_questions: [2] },
        { competency: '시스템 설계', weight: 0.25, related_questions: [2] },
        { competency: '팀 협업', weight: 0.2, related_questions: [1] },
      ],
    },
    category_weights: {
      technical: 0.4,
      behavioral: 0.3,
      cultural: 0.15,
      problem_solving: 0.15,
    },
    interviewer_guide: {
      preparation: '이력서 기반 질문 준비',
      time_per_question: '5분',
      evaluation_criteria: '구체성, 논리성, 실무 경험',
    },
    full_glossary: [
      { term: 'API', definition: 'Application Programming Interface' },
      { term: 'CDN', definition: 'Content Delivery Network' },
    ],
    metadata: {
      version: 'v2',
      generated_by: 'test',
    },
  }

  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/jobs/test-job-123/result**', async (route) => {
      const url = route.request().url()
      if (url.includes('version=v2') || !url.includes('version=')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockV2Response),
        })
      } else {
        // v1 fallback (simplified)
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockV2Response,
            intel: undefined,
            analysis: undefined,
            decision: undefined,
          }),
        })
      }
    })

    // Navigate to result page
    await page.goto('/result/test-job-123')
  })

  test('4개 탭이 모두 표시되어야 함', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle')

    // Check all 4 tabs are visible
    await expect(page.getByRole('tab', { name: /intel brief/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /deep analysis/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /live interview/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /decision/i })).toBeVisible()
  })

  test('Intel Brief 탭 - JD 요약 및 역량 매칭 표시', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // Click Intel Brief tab (should be default)
    const intelTab = page.getByRole('tab', { name: /intel brief/i })
    await intelTab.click()

    // Check JD summary content
    await expect(page.getByText('백엔드 개발자')).toBeVisible()
    await expect(page.getByText('핀테크 스타트업')).toBeVisible()

    // Check competency matching
    await expect(page.getByText('Python 개발')).toBeVisible()
    await expect(page.getByText('강점')).toBeVisible()

    // Check GitHub chart data exists
    await expect(page.locator('svg').first()).toBeVisible()
  })

  test('Deep Analysis 탭 - 레이더 차트 및 스킬 테이블 표시', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // Click Deep Analysis tab
    const analysisTab = page.getByRole('tab', { name: /deep analysis/i })
    await analysisTab.click()

    // Check overall match score
    await expect(page.getByText('82%')).toBeVisible()

    // Check radar chart exists (SVG)
    await expect(page.locator('svg').first()).toBeVisible()

    // Check engineering DNA items
    await expect(page.getByText('테스트 커버리지')).toBeVisible()
    await expect(page.getByText('코드 리뷰 참여')).toBeVisible()

    // Check skill table
    await expect(page.getByText('Python 3.11')).toBeVisible()
    await expect(page.getByText('FastAPI')).toBeVisible()
  })

  test('Live Interview 탭 - 질문 선택 및 채점 UI', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // Click Live Interview tab
    const interviewTab = page.getByRole('tab', { name: /live interview/i })
    await interviewTab.click()

    // Check question selection phase
    await expect(page.getByText('첫 90일 우선순위')).toBeVisible()
    await expect(page.getByText('API 설계 경험')).toBeVisible()

    // Click on first question to select
    const firstQuestion = page.getByText('첫 90일 우선순위')
    await firstQuestion.click()

    // Check question details are shown
    await expect(page.getByText('입사 후 첫 90일 동안')).toBeVisible()
  })

  test('Decision 탭 - 채용 추천 및 가이드 표시', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // Click Decision tab
    const decisionTab = page.getByRole('tab', { name: /decision/i })
    await decisionTab.click()

    // Check candidate summary
    await expect(page.getByText('5년')).toBeVisible()
    await expect(page.getByText('높음')).toBeVisible()
    await expect(page.getByText('시니어')).toBeVisible()

    // Check strengths and concerns
    await expect(page.getByText('Python 전문성')).toBeVisible()
    await expect(page.getByText('프론트엔드 경험 부족')).toBeVisible()

    // Check interviewer guide
    await expect(page.getByText('기술 심층 → 행동 면접 → 문화 적합성')).toBeVisible()
  })

  test('탭 간 전환이 올바르게 작동해야 함', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // Navigate through all tabs
    const tabs = [
      { name: /intel brief/i, content: '백엔드 개발자' },
      { name: /deep analysis/i, content: '테스트 커버리지' },
      { name: /live interview/i, content: '첫 90일 우선순위' },
      { name: /decision/i, content: 'Python 전문성' },
    ]

    for (const tab of tabs) {
      await page.getByRole('tab', { name: tab.name }).click()
      await expect(page.getByText(tab.content)).toBeVisible()
    }
  })

  test('후보자 정보가 헤더에 표시되어야 함', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // Check candidate info in header
    await expect(page.getByText('홍길동')).toBeVisible()
    await expect(page.getByText('시니어 백엔드 개발자')).toBeVisible()
  })

  test('JSON 내보내기 버튼이 작동해야 함', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // Find and click export button
    const exportButton = page.getByRole('button', { name: /export|내보내기|json/i })

    if (await exportButton.isVisible()) {
      // Set up download handler
      const downloadPromise = page.waitForEvent('download')
      await exportButton.click()
      const download = await downloadPromise

      // Verify download started
      expect(download.suggestedFilename()).toContain('.json')
    }
  })
})

test.describe('ResultPage - v1 Fallback', () => {
  const mockV1Response = {
    job_id: 'test-job-v1',
    questions: [
      {
        id: 'q1',
        topic: '기술 질문',
        category: 'technical',
        difficulty: 'mid',
        question_text: '테스트 질문입니다.',
        why_matters: '테스트 이유',
        listen_for: '테스트 항목',
        evaluation_scenarios: {
          expert: { text: '전문가 답변', score: 20 },
          mid: { text: '중급 답변', score: 12 },
          low: { text: '초급 답변', score: 5 },
        },
        follow_up_questions: [],
        terminology: [],
      },
    ],
    candidate_summary: {
      name: 'v1 후보자',
      current_title: '개발자',
      years_experience: 3,
    },
    interviewer_guide: {
      preparation: '준비 사항',
    },
    full_glossary: [],
    metadata: { version: 'v1' },
  }

  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/jobs/test-job-v1/result**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockV1Response),
      })
    })

    await page.goto('/result/test-job-v1')
  })

  test('v1 데이터로 fallback 탭 구조가 표시되어야 함', async ({ page }) => {
    await page.waitForLoadState('networkidle')

    // v1 format should show fallback tabs
    await expect(page.getByRole('tab', { name: /questions|질문/i })).toBeVisible()
  })
})

test.describe('ResultPage - 로딩 및 에러 상태', () => {
  test('로딩 상태가 표시되어야 함', async ({ page }) => {
    // Delay the response to see loading state
    await page.route('**/api/v1/jobs/*/result**', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ questions: [] }),
      })
    })

    await page.goto('/result/test-job-loading')

    // Check for loading indicator
    await expect(page.getByText(/loading|로딩|불러오는/i)).toBeVisible()
  })

  test('에러 상태가 표시되어야 함', async ({ page }) => {
    await page.route('**/api/v1/jobs/*/result**', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Job not found' }),
      })
    })

    await page.goto('/result/non-existent-job')
    await page.waitForLoadState('networkidle')

    // Check for error message
    await expect(page.getByText(/error|에러|오류|찾을 수 없|not found/i)).toBeVisible()
  })
})
