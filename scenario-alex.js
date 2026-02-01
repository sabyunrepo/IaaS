window.scenarioAlex = {
  candidate: {
    name: 'Alex Chen',
    initials: 'A',
    role: 'CTO Candidate',
    company_context: 'Series A FinTech',
    experience: '7년',
    jd_match: '78%',
    level: '시니어',
    current_title: 'Engineering Lead'
  },
  category_weights: {
    role_fit: 0.25,
    technical_depth: 0.20,
    execution_ownership: 0.20,
    communication: 0.20,
    risk_flags: 0.15
  },
  intel: {
    jd_summary: {
      title: 'Chief Technology Officer (최고기술책임자)',
      subtitle: 'Series A FinTech Startup · 금융 기술 스타트업',
      requirements: [
        {
          text: 'FastAPI/Python',
          desc: '서버(뒷단 시스템)를 만드는 프로그래밍 도구',
          matched: true
        },
        {
          text: 'MSA 설계 경험',
          desc: '하나의 큰 프로그램을 작은 독립 프로그램들로 나눠본 경험',
          matched: true
        },
        {
          text: 'AWS & Kubernetes 운영',
          desc: '클라우드 서버 환경을 관리하고 자동화한 경험',
          matched: true
        },
        {
          text: '팀 리더십',
          desc: '8~15명의 개발자를 이끌어본 경험',
          matched: true
        }
      ],
      success_metrics: ['오래된 시스템을 안정적으로 운영 가능한 상태로 만들기', '경험 많은 개발자 3명 채용 완료', '새 기능을 고객에게 전달하는 시간을 절반으로 줄이기']
    },
    jd_full: '<p class="font-bold text-slate-700 mb-2">[ 채용 배경 ]</p><p>저희 FinTech(금융+기술) 스타트업은 Series A 투자(초기 대규모 투자)를 유치하고 빠르게 성장 중입니다. 현재 모든 기능이 하나의 큰 프로그램에 몰려 있어(모놀리스), 새 기능 추가와 문제 해결이 점점 느려지고 있습니다. 이 시스템을 현대화하고 8~15명 규모의 개발팀을 이끌 CTO를 찾고 있습니다.</p><p class="font-bold text-slate-700 mb-2 mt-4">[ 주요 업무 ]</p><ul class="space-y-1 ml-4"><li>• <strong>기술 전략 수립:</strong> 회사의 기술 방향을 결정하고 실행 계획을 세움</li><li>• <strong>팀 빌딩 및 채용:</strong> 우수한 개발자를 뽑고 팀을 성장시킴</li><li>• <strong>제품 아키텍처 설계:</strong> 서비스의 전체 구조를 설계하고 기술적 의사결정을 내림</li><li>• <strong>인프라 현대화:</strong> 서버·배포·모니터링 환경을 자동화하고 안정화</li><li>• <strong>보안 컴플라이언스(SOC2):</strong> 고객 데이터 보호를 증명하는 국제 인증 획득</li></ul><p class="font-bold text-slate-700 mb-2 mt-4">[ 자격 요건 ]</p><ul class="space-y-1 ml-4"><li>• 소프트웨어 개발 경력 7년 이상</li><li>• Python/FastAPI로 서버 시스템을 만들어본 전문성</li><li>• 큰 프로그램을 작은 서비스들로 나눠본 경험 (MSA 전환)</li><li>• AWS 클라우드와 Kubernetes(서버 자동 관리 도구) 운영 경험</li><li>• 개발팀을 이끌어본 리더십 경험</li></ul><p class="font-bold text-slate-700 mb-2 mt-4">[ 우대 사항 ]</p><ul class="space-y-1 ml-4"><li>• 금융 서비스 도메인 경험</li><li>• SOC2/ISO27001 등 보안 인증 획득 경험</li><li>• IaC(코드로 서버 환경을 관리하는 방식) 경험</li><li>• 스타트업 초기 멤버 또는 CTO 경험</li></ul>',
    competencies: [
      {
        name: '백엔드 시스템 설계',
        match: 'strong',
        match_label: '후보자: 강한 매칭',
        desc: '서버(뒷단 시스템)를 설계하고 만드는 능력입니다. 쉽게 말해, 사용자가 앱에서 버튼을 누르면 뒤에서 데이터를 처리해주는 시스템을 만드는 것입니다. 많은 사용자가 동시에 사용해도 멈추지 않고 안정적으로 작동해야 합니다.',
        why: '금융 서비스는 결제·송금 등 실시간 처리가 핵심이므로, 안정적인 서버 시스템 설계가 필수입니다.',
        color: 'emerald',
        icon: '✅'
      },
      {
        name: '시스템 현대화 (모놀리스 → MSA)',
        match: 'match',
        match_label: '후보자: 매칭',
        desc: '오래된 하나의 큰 프로그램을 작은 독립 프로그램들로 나누는 작업입니다. 비유하면, 모든 부서가 한 건물에 있는 회사를 각 부서가 독립 사무실을 가진 구조로 바꾸는 것입니다. 한 부서에 문제가 생겨도 다른 부서는 정상 운영됩니다.',
        why: '현재 시스템이 모놀리스여서 기능 하나를 수정하면 전체를 다시 배포해야 하고, 이 과정이 점점 느려지고 있습니다.',
        color: 'emerald',
        icon: '✅'
      },
      {
        name: '클라우드 인프라 운영 (AWS, Kubernetes)',
        match: 'partial',
        match_label: '후보자: 부분 매칭 — AWS 경험 있으나 K8s 증거 부족',
        desc: '회사의 서비스가 돌아가는 가상 서버 환경을 관리하는 능력입니다. AWS는 아마존이 제공하는 클라우드 서비스(자체 서버 없이 인터넷으로 서버를 빌려 사용), Kubernetes(쿠버네티스)는 여러 서버를 자동으로 관리해주는 도구입니다.',
        why: '사용자가 갑자기 늘어도 서버가 자동으로 늘어나고, 장애 시 자동 복구되는 환경이 필요합니다.',
        color: 'amber',
        icon: '⚠️'
      },
      {
        name: 'IaC (Infrastructure as Code, 코드로 인프라 관리)',
        match: 'unknown',
        match_label: '후보자: 미확인',
        desc: '서버 환경 설정을 사람이 하나씩 클릭하는 대신, 코드(텍스트 파일)로 작성해서 자동으로 실행하는 방식입니다. 마치 요리 레시피를 적어두면 누구든 같은 요리를 만들 수 있는 것처럼, 서버 환경도 코드로 적어두면 항상 동일한 환경을 빠르게 만들 수 있습니다. 대표 도구로 Terraform(테라폼), Ansible(앤서블) 등이 있습니다.',
        why: '수동으로 서버를 설정하면 실수가 생기고, 환경이 제각각이 됩니다. 코드로 관리하면 실수 없이 동일한 환경을 반복 생성할 수 있습니다.',
        color: 'amber',
        icon: '⚠️'
      },
      {
        name: '보안 컴플라이언스 (SOC2)',
        match: 'none',
        match_label: '후보자: 증거 없음',
        desc: '고객의 개인정보와 금융 데이터를 안전하게 보호하고 있음을 공인된 기관에서 인증받는 것입니다. 금융 서비스에서는 법적으로 필수인 경우가 많으며, 이 인증이 없으면 대기업 고객과 계약이 어렵습니다.',
        why: '금융 서비스 특성상 고객 데이터 보호 인증(SOC2)은 사업 확장의 전제 조건입니다. 후보자에게 이 경험이 확인되지 않았습니다.',
        color: 'red',
        icon: '❌'
      },
      {
        name: '팀 리더십 (8~15명 규모)',
        match: 'partial',
        match_label: '후보자: 부분 매칭 — 4~6명 경험',
        desc: '개발자들을 채용하고, 업무를 나누고, 성장을 돕고, 팀의 방향을 잡아주는 능력입니다.',
        why: '빠르게 성장하는 스타트업에서 팀을 2~3배로 키우면서도 개발 속도와 품질을 유지해야 합니다.',
        color: 'emerald',
        icon: '✅'
      }
    ],
    github: {
      contributions: 342,
      repos: 23,
      main_languages: 'TS, Python, Go',
      tech_match: '높음 (Python, AWS)',
      tech_match_note: 'K8s 증거 부족',
      tenure_pattern: '평균 2.3년',
      tenure_note: '⚠ 최근 짧은 재직',
      activity_gap: 'Q2 2024',
      chart_data: [12, 19, 3, 5, 2, 3, 45, 60, 55, 40, 25, 30]
    },
    linkedin: [
      {
        initial: 'T',
        title: 'Engineering Lead',
        company: 'TechStartup Inc.',
        detail: '2년 · 4-6명 리드 · 제품 2개 런칭'
      },
      {
        initial: 'M',
        title: 'Senior Engineer',
        company: 'MidSize Corp',
        detail: '3년'
      },
      {
        initial: 'B',
        title: 'Software Engineer',
        company: 'BigTech Co.',
        detail: '2년'
      }
    ],
    linkedin_warning: 'CTO/VP 타이틀 경험 없음 · MBA 언급되나 상세 불명'
  },
  analysis: {
    radar_candidate: [90, 85, 40, 80, 85],
    radar_required: [80, 80, 60, 70, 70],
    engineering_dna: [
      {
        label: '테스트 커버리지',
        value: 82,
        display: '82%',
        color: 'emerald'
      },
      {
        label: '문서화 품질',
        value: 90,
        display: '우수',
        color: 'blue'
      },
      {
        label: 'IaC',
        value: 5,
        display: '미확인',
        color: 'red',
        note: 'Terraform, Ansible 같은 자동화 도구 사용 흔적이 GitHub에서 발견되지 않았습니다',
        tooltip: '서버 환경을 코드 파일로 관리하는 방식 — 수동 설정 대신 자동화 스크립트로 서버를 만들고 관리'
      }
    ],
    risk_flags: [
      {
        label: '이력 공백',
        detail: '2023.11 - 2024.02 (3개월)'
      },
      {
        label: '특정 도구 의존',
        detail: '남이 만든 도구(라이브러리)에 지나치게 의존하여, 도구 없이 직접 문제를 해결하는 능력이 불확실'
      },
      {
        label: '팀 규모 갭',
        detail: '경험 4-6명 → 요구 8-15명'
      }
    ],
    skill_table: [
      {
        skill: 'Python/FastAPI',
        candidate: 'Python, FastAPI',
        type: 'exact',
        evidence: 'GitHub: api-server',
        confidence: 95
      },
      {
        skill: 'MSA',
        candidate: 'Microservices',
        type: 'similar',
        evidence: '이력서: MSA 전환 리드',
        confidence: 80
      },
      {
        skill: 'AWS',
        candidate: 'AWS',
        type: 'exact',
        evidence: 'GitHub: terraform',
        confidence: 90
      },
      {
        skill: 'Kubernetes',
        candidate: 'Docker',
        type: 'partial',
        evidence: 'K8s manifest 없음',
        confidence: 40
      },
      {
        skill: '팀 리더십 8-15명',
        candidate: '4-6명 경험',
        type: 'partial',
        evidence: 'LinkedIn',
        confidence: 55
      },
      {
        skill: 'SOC2',
        candidate: '—',
        type: 'none',
        evidence: '증거 없음',
        confidence: 0
      }
    ],
    overall_match: 78
  },
  decision: {
    summary: {
      experience: '7년',
      jd_match: '78%',
      level: '시니어',
      strengths: ['Python/FastAPI 전문성 (높은 매칭)', '제품 0→1 런칭 경험 2회', '테스트 커버리지 82%', '문서화 품질 우수'],
      concerns: ['K8s 실무 경험 수준', '팀 규모 확장 전략', '이력 공백기 사유', 'SOC2 컴플라이언스 이해도']
    },
    interviewer_guide: {
      resume_based_tips: [
        {
          area: '이력 공백',
          detail: '2023.11-2024.02 기간 3개월 공백. 이전 직장 퇴사와 관련이 있을 수 있습니다. 비난이 아닌 확인 톤으로 자연스럽게 물어보세요.',
          source: '이력서'
        },
        {
          area: 'K8s 경험',
          detail: '이력서에 "클라우드 인프라 운영"이라고 했지만 GitHub에 Kubernetes 관련 코드(manifest, Helm chart)가 없습니다. Docker는 사용하지만 K8s는 실무 수준이 아닐 수 있습니다.',
          source: '이력서 vs GitHub 불일치'
        },
        {
          area: '팀 규모',
          detail: '최대 4-6명 리드 경험인데, 이 역할은 8-15명 관리가 필요합니다. 규모 확장 전략을 구체적으로 물어보세요.',
          source: '이력서 vs JD 갭'
        },
        {
          area: 'MBA',
          detail: '이력서에 MBA 과정 언급이 있지만 상세 내용이 없습니다. 완료했는지, 관련 경험이 있는지 확인하세요.',
          source: 'LinkedIn'
        }
      ],
      cover_letter_insights: [
        {
          claim: '모놀리스에서 MSA로 전환을 리드한 경험',
          verify_with: 'Q4(모놀리스→MSA) 답변에서 구체적 역할과 결과 확인'
        },
        {
          claim: '팀을 키우면서 문화를 만들어본 경험',
          verify_with: 'Q10(팀 규모 확장) 답변에서 구체적 방법론 확인'
        },
        {
          claim: '기술과 비즈니스를 연결하는 소통 능력',
          verify_with: 'Q8(비기술 소통) 답변에서 실제 비유와 번역 능력 확인'
        }
      ],
      interview_flow: '편안하게 시작(CTO 비전) → 기술 깊이 확인 → 리더십 경험 → 소통 능력 → 위험 신호 확인',
      time_allocation: {
        role_fit: '10분',
        technical: '20분',
        execution: '15분',
        communication: '10분',
        risk: '5분'
      },
      red_flags_to_watch: ['구체적 수치 없이 추상적 답변만 하는 경우', '실패 경험을 전혀 인정하지 않는 경우', '기술 유행만 쫓고 비즈니스 관점이 없는 경우', '팀보다 개인 기여를 강조하는 경우'],
      positive_signals: [
        '모놀리스→MSA 전환 시 단계적 접근(Strangler Fig 패턴 등)을 언급',
        '팀 규모 확장 시 프로세스 변화(스프린트, 코드 리뷰 기준)를 구체적으로 설명',
        '기술 결정의 비즈니스 임팩트를 수치로 설명',
        '실패 경험을 솔직히 공유하고 교훈을 도출',
        'K8s 경험 부족을 인정하되 학습 계획을 제시'
      ]
    },
    jd_competency_map: [
      {
        competency: 'MSA 설계 경험',
        weight: 0.8,
        related_questions: [4, 5, 6]
      },
      {
        competency: 'FastAPI/Python 전문성',
        weight: 0.7,
        related_questions: [2, 3, 5]
      },
      {
        competency: 'AWS & Kubernetes 운영',
        weight: 0.6,
        related_questions: [6, 7]
      },
      {
        competency: '팀 리더십 (8-15명)',
        weight: 0.9,
        related_questions: [10, 11, 12]
      },
      {
        competency: 'SOC2 보안 컴플라이언스',
        weight: 0.5,
        related_questions: [14, 15]
      }
    ]
  },
  questions: [
    {
      id: 1,
      category: 'role_fit',
      difficulty: 'Medium',
      title: '첫 90일 우선순위',
      question_text: 'CTO로서 첫 90일 동안 가장 집중하실 3가지 우선순위는 무엇이며, 그것들을 어떤 순서로 실행하시겠습니까?',
      context_bridge: '현재 저희는 8명의 엔지니어를 채용해야 하고, 제품 로드맵도 밀려있습니다.',
      why_matters: '초기 스타트업 CTO는 코딩·채용·전략 사이에서 균형을 잡아야 합니다. 불확실한 상황에서 우선순위를 정하는 능력을 테스트합니다.',
      listen_for: '기술적 부채 해결보다 "비즈니스 목표"와 "팀 빌딩"의 조화를 말하는지 확인하세요.',
      code_reference: null,
      terminology: [
        {
          term: 'Technical Debt',
          pronunciation: '테크니컬 뎃',
          explanation: '빨리 만들기 위해 대충 짠 코드가 나중에 문제를 일으키는 것. "빚"처럼 갚아야 합니다.',
          definition: '빨리 만들기 위해 대충 짠 코드가 나중에 문제를 일으키는 것. "빚"처럼 갚아야 합니다.',
          plain_language: '빨리 만들기 위해 대충 짠 코드가 나중에 문제를 일으키는 것. "빚"처럼 갚아야 합니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Roadmap',
          pronunciation: '로드맵',
          explanation: '제품이 앞으로 어떻게 발전할지 그린 계획표입니다.',
          definition: '제품이 앞으로 어떻게 발전할지 그린 계획표입니다.',
          plain_language: '제품이 앞으로 어떻게 발전할지 그린 계획표입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'CTO',
          pronunciation: '씨티오',
          explanation: 'Chief Technology Officer. 회사의 기술 전략과 개발팀을 총괄하는 최고 기술 책임자입니다.'
        },
        {
          term: 'Architecture',
          pronunciation: '아키텍처',
          explanation: '시스템의 전체 설계 구조. 건물의 설계도처럼 프로그램을 어떻게 구성할지 정한 것입니다.'
        },
        {
          term: 'Deploy',
          pronunciation: '디플로이',
          explanation: '배포. 작성한 코드를 실제 서버에 올려서 사용자가 쓸 수 있게 하는 작업입니다.'
        },
        {
          term: 'Bottleneck',
          pronunciation: '보틀넥',
          explanation: '병목 지점. 물이 병의 좁은 입구에서 막히듯, 시스템에서 가장 느린 부분을 말합니다.'
        },
        {
          term: '1:1 Meeting',
          pronunciation: '원온원 미팅',
          explanation: '관리자와 팀원이 둘이서만 하는 개인 면담. 솔직한 피드백과 고민을 나누는 시간입니다.'
        },
        {
          term: 'Code Repository',
          pronunciation: '코드 레포지토리',
          explanation: '코드 저장소. Git 같은 시스템으로 코드를 보관하고 버전을 관리하는 곳입니다.'
        },
        {
          term: 'Infrastructure',
          pronunciation: '인프라스트럭처',
          explanation: '인프라. 서버, 데이터베이스, 네트워크 등 프로그램이 돌아가기 위한 기반 시설입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '팀 진단',
          importance: 'must',
          explanation: '현재 팀의 역량과 구조를 먼저 파악해야 올바른 의사결정이 가능'
        },
        {
          keyword: '단계적 접근',
          importance: 'must',
          explanation: '한 번에 모든 것을 바꾸려는 것은 리스크가 높음'
        },
        {
          keyword: '비즈니스 목표 연결',
          importance: 'good_to_have',
          explanation: '기술 결정이 비즈니스 성과로 연결되어야 함'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: '현재 팀과 아키텍처 진단(2주) → 핵심 채용 및 병목 해결(1달) → 장기 로드맵 수립 순으로 단계적 접근을 제시함.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '열심히 코딩해서 밀린 기능을 빨리 개발하겠다고 함. (IC 마인드셋)',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '구체적 계획 없이 상황 봐서 결정하겠다고 함.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q1-f1',
          trigger: 'Expert',
          question_text: '진단 결과 팀의 핵심 역량이 부족하다면, 외부 채용과 내부 육성 중 어떤 기준으로 선택하시겠습니까?',
          why_matters: '리더의 인재 전략을 확인합니다. 단기 성과와 장기 팀 건강의 균형 감각이 중요합니다.',
          listen_for: '상황별 기준(시급성, 역할, 시장 상황)을 구분하는지 확인하세요.',
          good: {
            text: '역할의 시급성과 내부 성장 가능성을 구분하여 답변. 핵심 포지션은 외부 채용, 나머지는 내부 육성이라는 원칙 제시.',
            score: 8
          },
          poor: {
            text: '무조건 채용 또는 무조건 육성이라고 답변.',
            score: 0
          }
        },
        {
          id: 'q1-f2',
          trigger: 'Mid',
          question_text: '코딩에 집중하겠다고 하셨는데, 채용과 전략은 누가 담당하게 되나요?',
          why_matters: 'IC 마인드셋에서 리더십으로 전환할 준비가 되어있는지 확인합니다.',
          listen_for: '역할 전환에 대한 인식이 있는지, 위임 계획이 있는지 확인하세요.',
          good: {
            text: '리더십 역할의 중요성을 인식하고 수정된 답변을 제시함.',
            score: 5
          },
          poor: {
            text: '여전히 코딩이 최우선이라고 주장함.',
            score: -3
          }
        },
        {
          id: 'q1-f3',
          trigger: 'Low',
          question_text: '예를 들어, 팀의 배포가 주 1회밖에 안 되고 버그가 많은 상황이라면 무엇부터 하시겠습니까?',
          why_matters: '구체적 시나리오를 주어 문제 해결 과정을 다시 확인합니다.',
          listen_for: '구체적 상황에서 논리적으로 우선순위를 세울 수 있는지 확인하세요.',
          good: {
            text: '시나리오에 맞춰 구체적 우선순위를 제시함.',
            score: 5
          },
          poor: {
            text: '여전히 막연한 답변.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "이 사람이 혼란스러운 상황에서 체계적으로 일을 정리할 수 있는가"를 보는 것입니다. 좋은 CTO는 기술만 아는 게 아니라, 회사의 비즈니스 목표와 기술을 연결할 수 있어야 합니다.',
        daily_analogy: '새로 부임한 학교 교장이 첫 학기에 할 일을 정하는 것과 비슷합니다. 좋은 교장은 먼저 선생님들과 면담하고(팀 진단), 급한 시설 문제를 고치고(병목 해결), 그 후에 장기 교육 계획을 세웁니다(로드맵). 나쁜 교장은 계획 없이 눈앞의 일만 처리합니다.',
        level_expectation: 'CTO 수준에서는 "먼저 현재 상태를 파악하고, 우선순위를 정하고, 단계별로 실행한다"는 체계적 접근이 필수입니다. 단순히 "열심히 하겠다"가 아니라 구체적인 시간표와 기준이 있어야 합니다.'
      },
      expected_answer: {
        core: '• 1단계 (1~2주): 팀원 전원 1:1 면담 + 코드·인프라 직접 점검으로 현재 상태 파악\n• 2단계 (3~6주): 가장 급한 채용(시니어 개발자)과 서비스 병목 해결 동시 진행\n• 3단계 (7~12주): CEO와 함께 6개월 기술 로드맵 수립 및 이사회 발표',
        example: '첫 2주는 팀원 8명 전원과 1:1 미팅을 합니다. "가장 불편한 점이 뭔가요?", "배포할 때 가장 오래 걸리는 게 뭔가요?" 같은 질문으로 현장의 진짜 문제를 파악합니다. 동시에 코드 저장소와 서버 구조를 직접 확인합니다. 3주째부터 두 가지를 병행합니다. 하나는 시니어 개발자 채용 — 제 네트워크와 채용 플랫폼을 동시에 활용합니다. 다른 하나는 배포 시간이 3시간 걸리는 문제처럼, 팀 전체가 매일 겪는 가장 큰 병목을 해결합니다. 6주째에는 파악한 데이터를 바탕으로 CEO와 6개월 기술 로드맵을 만들어 이사회에 발표합니다. 이때 "이 투자가 비즈니스에 어떤 효과를 주는지"를 숫자로 보여줍니다.',
        key_points: ['단계적 접근', '팀 진단 우선', '비즈니스-기술 연결']
      },
      jd_competency_link: 'JD 요구사항: "기술 전략 수립 및 팀 빌딩" → CTO로서의 리더십과 비전 검증',
      generation_rationale: '후보자의 이력서에 "Engineering Lead" 경험이 있어 CTO 역할 적합성을 검증',
      skills_assessed: ['leadership', 'strategy'],
      alternative_phrasings: ['CTO로서 첫 90일 동안 가장 집중하실 3가지 우선순위는 무엇이며, 그것들을 어떤 순서로 실행하시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 2,
      category: 'role_fit',
      difficulty: 'Easy',
      title: '핸즈온 vs 리더십 균형',
      question_text: '코드를 직접 작성하는 것과 리더십/전략에 집중하는 것의 균형을 어떻게 잡으시겠습니까?',
      context_bridge: '이 역할은 초기에 40-50% 핸즈온 코딩이 필요하지만, 팀이 커지면서 리더십 비중이 높아져야 합니다.',
      why_matters: 'CTO 역할은 유연성이 핵심입니다. 상황에 맞게 역할을 전환할 수 있는지 확인합니다.',
      listen_for: '개인적 선호에 대한 솔직한 성찰과, 회사 필요에 따라 적응할 수 있는 능력을 확인하세요.',
      code_reference: null,
      terminology: [
        {
          term: 'IC (Individual Contributor)',
          pronunciation: '아이씨',
          explanation: '팀을 관리하지 않고 개인으로 기술 기여를 하는 역할입니다.',
          definition: '팀을 관리하지 않고 개인으로 기술 기여를 하는 역할입니다.',
          plain_language: '팀을 관리하지 않고 개인으로 기술 기여를 하는 역할입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Code Review',
          pronunciation: '코드 리뷰',
          explanation: '다른 사람이 작성한 코드를 검토해서 실수나 개선점을 찾아주는 것. 품질 관리의 핵심입니다.',
          definition: '다른 사람이 작성한 코드를 검토해서 실수나 개선점을 찾아주는 것. 품질 관리의 핵심입니다.',
          plain_language: '다른 사람이 작성한 코드를 검토해서 실수나 개선점을 찾아주는 것. 품질 관리의 핵심입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Hands-on',
          pronunciation: '핸즈온',
          explanation: '직접 손으로 작업하는 것. 관리만 하지 않고 실제로 코드를 작성하는 것을 말합니다.'
        },
        {
          term: 'Leadership',
          pronunciation: '리더십',
          explanation: '팀을 이끄는 능력. 방향을 제시하고, 결정하고, 사람들을 동기부여하는 역할입니다.'
        },
        {
          term: 'Leverage',
          pronunciation: '레버리지',
          explanation: '지렛대 효과. 리더가 팀원 10명을 잘 이끌면 혼자 코딩하는 것보다 10배 이상 효과를 낼 수 있습니다.'
        },
        {
          term: 'Mentoring',
          pronunciation: '멘토링',
          explanation: '경험 있는 사람이 초보자에게 지식과 경험을 전달하며 성장을 돕는 것입니다.'
        },
        {
          term: 'Architecture Review',
          pronunciation: '아키텍처 리뷰',
          explanation: '시스템 설계를 검토하고 큰 그림에서 문제가 없는지 확인하는 회의입니다.'
        },
        {
          term: 'Scalability',
          pronunciation: '스케일러빌리티',
          explanation: '확장성. 사용자나 데이터가 늘어나도 시스템이 잘 동작할 수 있는 능력입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '단계별 비율 변화',
          importance: 'must',
          explanation: '팀 규모에 따라 코딩 비율이 달라져야 함을 인식'
        },
        {
          keyword: '레버리지',
          importance: 'good_to_have',
          explanation: '리더는 개인 코딩보다 팀을 통한 곱하기 효과가 더 큼'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: '회사 단계별 비율 변화를 인지하고, 구체적 전환 기준(팀 규모, 제품 안정성)을 제시.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '코딩도 좋아하고 리더십도 할 수 있다고 일반적으로 답변.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '코딩만 하고 싶다거나 관리만 하겠다고 극단적 답변.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q2-f1',
          trigger: 'Expert',
          question_text: '팀이 15명으로 커졌을 때, 본인이 직접 코드 리뷰를 하는 것과 리뷰 문화를 만드는 것 중 어떤 것이 더 효과적일까요?',
          why_matters: '규모 확장 시 리더의 역할 전환 깊이를 확인합니다.',
          listen_for: '시스템/문화를 만드는 것이 개인 기여보다 중요하다는 인식.',
          good: {
            text: '리뷰 문화와 가이드라인을 만드는 것이 확장 가능하다고 답변.',
            score: 8
          },
          poor: {
            text: '본인이 모든 코드를 리뷰해야 한다고 주장.',
            score: 0
          }
        },
        {
          id: 'q2-f2',
          trigger: 'Mid',
          question_text: '구체적으로 팀이 몇 명일 때 코딩 비율을 줄이기 시작하시겠습니까?',
          why_matters: '추상적 답변을 구체화하여 실질적 계획이 있는지 확인.',
          listen_for: '숫자와 기준을 제시하는지.',
          good: {
            text: '7-10명 기준, 30% 이하로 줄이겠다 등 구체적 답변.',
            score: 5
          },
          poor: {
            text: '잘 모르겠다, 상황에 따라 다르다.',
            score: -2
          }
        },
        {
          id: 'q2-f3',
          trigger: 'Low',
          question_text: '그렇다면 CTO의 가장 중요한 역할은 무엇이라고 생각하시나요?',
          why_matters: '역할에 대한 기본 이해를 재확인.',
          listen_for: '기술 비전, 팀 빌딩, 비즈니스 연결 중 최소 하나.',
          good: {
            text: '역할에 대한 균형 잡힌 이해를 보여줌.',
            score: 5
          },
          poor: {
            text: '코딩이 가장 중요하다고 답변.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "상황에 따라 역할을 유연하게 바꿀 수 있는 사람인지"를 확인합니다. 초기 스타트업에서는 직접 개발도 해야 하지만, 팀이 커지면 사람을 키우고 방향을 잡는 일이 더 중요해집니다.',
        daily_analogy: '식당 사장이 처음에는 직접 요리도 하지만, 직원이 늘면 메뉴 기획과 직원 교육에 집중하는 것과 같습니다. 계속 요리만 하면 가게를 키울 수 없고, 처음부터 관리만 하면 음식 품질을 모릅니다.',
        level_expectation: 'CTO 수준에서는 "팀 규모별로 내 역할이 어떻게 달라져야 하는지" 구체적 숫자(예: 10명 이상이면 코딩 30% 이하)와 전환 기준을 제시할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 초기(~10명): 60% 직접 개발, 40% 리더십 — 핵심 설계를 직접 잡으면서 팀 문화를 세움\n• 중기(10~20명): 30% 개발, 70% 리더십 — 코드 리뷰와 멘토링 중심으로 전환\n• 핵심 전환 기준: 팀이 스스로 결정하고 실행할 수 있는 수준이 되면 점차 넘김',
        example: '저는 팀 규모에 따라 의식적으로 역할을 조절합니다. 지금 8명이라면 초기에는 핵심 아키텍처 코드를 직접 작성하면서 코딩 표준을 보여줍니다. 하지만 팀이 12명을 넘으면 제가 모든 코드를 리뷰하는 건 병목이 됩니다. 그때부터는 리뷰 가이드라인을 문서화하고, 시니어 개발자들이 리뷰를 주도하게 합니다. 이전 회사에서 팀이 6명에서 14명으로 커질 때, 제 코딩 비율을 70%에서 25%로 줄였습니다. 대신 1:1 미팅, 아키텍처 리뷰, 채용에 시간을 썼더니 팀 전체 생산성이 2배 올랐습니다.',
        key_points: ['상황별 유연성', '자기인식', '팀 성장 전환']
      },
      jd_competency_link: 'JD 요구사항: "기술 전략 수립 및 팀 빌딩" → CTO로서의 리더십과 비전 검증',
      generation_rationale: '후보자의 이력서에 "Engineering Lead" 경험이 있어 CTO 역할 적합성을 검증',
      skills_assessed: ['leadership', 'strategy'],
      alternative_phrasings: ['코드를 직접 작성하는 것과 리더십/전략에 집중하는 것의 균형을 어떻게 잡으시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 3,
      category: 'technical_depth',
      difficulty: 'Hard',
      title: '실시간 결제 알림 시스템 설계',
      question_text: '초당 10,000건의 트랜잭션을 처리하면서 99.99% 가용성을 보장하는 실시간 결제 알림 시스템을 어떻게 설계하시겠습니까?',
      context_bridge: '저희 플랫폼은 결제 서비스를 운영하는데, 실시간 알림이 핵심 기능입니다.',
      why_matters: '실제 기술적 깊이와 복잡한 분산 시스템 설계 능력을 테스트합니다.',
      listen_for: '체계적 접근, 트레이드오프 인식, 운영 현실에 대한 이해. 기술 이름 나열만으로는 부족합니다.',
      code_reference: {
        repo_name: 'alexchen/api-server',
        file_path: 'src/notifications/handler.py',
        line_range: 'L23-L31',
        snippet: 'async def process_notification(event: PaymentEvent):\n    async with kafka_producer() as producer:\n        await producer.send(\n            topic=\'payment-notifications\',\n            value=event.serialize()\n        )',
        explanation: '후보자 GitHub에서 발견된 알림 처리 코드. Kafka라는 메시지 전달 시스템을 사용하고 있습니다.',
        plain_language_summary: '이 코드는 결제가 일어나면 알림을 보내는 부분입니다. 메시지를 하나씩 직접 보내는 대신, Kafka라는 "우편 시스템"에 맡겨서 대량의 알림을 빠르고 안전하게 전달합니다. 후보자가 이런 대량 처리 방식을 알고 사용하고 있다는 증거입니다.',
        permalink: 'https://github.com/alexchen/project/blob/main/src/example.py'
      },
      terminology: [
        {
          term: 'Kafka',
          pronunciation: '카프카',
          explanation: '대량의 메시지를 빠르게 전달하는 우편 시스템입니다. 발송인과 수신인 사이에서 메시지를 안전하게 전달합니다.',
          definition: '대량의 메시지를 빠르게 전달하는 우편 시스템입니다. 발송인과 수신인 사이에서 메시지를 안전하게 전달합니다.',
          plain_language: '대량의 메시지를 빠르게 전달하는 우편 시스템입니다. 발송인과 수신인 사이에서 메시지를 안전하게 전달합니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: '99.99% Uptime',
          pronunciation: '포나인',
          explanation: '1년 중 약 52분만 중단되는 수준의 안정성입니다.',
          definition: '1년 중 약 52분만 중단되는 수준의 안정성입니다.',
          plain_language: '1년 중 약 52분만 중단되는 수준의 안정성입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Circuit Breaker',
          pronunciation: '서킷 브레이커',
          explanation: '연쇄 장애를 막기 위해 문제가 생긴 부분을 자동으로 차단하는 안전장치입니다.'
        },
        {
          term: 'TPS (Transactions Per Second)',
          pronunciation: '티피에스',
          explanation: '초당 처리 건수. 1초에 몇 개의 작업을 처리할 수 있는지 나타내는 성능 지표입니다.'
        },
        {
          term: 'Event-Driven Architecture',
          pronunciation: '이벤트 드리븐 아키텍처',
          explanation: '사건(이벤트)이 발생하면 반응하는 방식의 시스템 설계. 결제가 일어나면 → 알림을 보낸다 같은 흐름입니다.'
        },
        {
          term: 'DLQ (Dead Letter Queue)',
          pronunciation: '디엘큐',
          explanation: '처리 실패한 메시지들을 모아두는 별도의 보관함. 나중에 다시 처리하거나 원인을 분석합니다.'
        },
        {
          term: 'Message Queue',
          pronunciation: '메시지 큐',
          explanation: '메시지 대기열. 우체통처럼 메시지를 임시로 보관했다가 순서대로 처리하는 시스템입니다.'
        },
        {
          term: 'Failover',
          pronunciation: '페일오버',
          explanation: '주 시스템이 고장나면 자동으로 예비 시스템으로 전환하는 것. 무중단 서비스의 핵심 기술입니다.'
        },
        {
          term: 'Monitoring',
          pronunciation: '모니터링',
          explanation: '시스템의 상태를 실시간으로 감시하는 것. 문제가 생기면 즉시 알림을 받을 수 있습니다.'
        },
        {
          term: 'Alerting',
          pronunciation: '얼러팅',
          explanation: '시스템에 문제가 발생하면 자동으로 담당자에게 알림을 보내는 기능입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '이벤트 기반 아키텍처',
          importance: 'must',
          explanation: '실시간 대량 처리에 필수적인 패턴'
        },
        {
          keyword: 'Kafka / 메시지 큐',
          importance: 'must',
          explanation: '10K TPS 처리에 적합한 기술'
        },
        {
          keyword: 'Circuit Breaker',
          importance: 'good_to_have',
          explanation: '장애 격리 인식을 보여줌'
        },
        {
          keyword: 'DLQ (Dead Letter Queue)',
          importance: 'good_to_have',
          explanation: '실패 메시지 재처리 전략'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 25,
          text: 'Kafka + 이벤트 소싱 + Circuit Breaker + 멀티 리전 failover 포함 체계적 아키텍처 제시. 모니터링과 alerting도 언급.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 12,
          text: '메시지 전달 시스템(Kafka)은 알고 있지만, 시스템이 고장났을 때 어떻게 대처할지, 사용자가 갑자기 늘어날 때 어떻게 확장할지에 대한 계획이 부족합니다.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '가장 기본적인 방식(하나하나 직접 확인하는 방식)을 제안합니다. 초당 1만 건을 처리해야 하는 규모에 대한 이해가 부족합니다.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q3-f1',
          trigger: 'Expert',
          question_text: 'Kafka 클러스터 자체가 장애가 나면 어떻게 대응하시겠습니까?',
          why_matters: '메시지 브로커 의존성에 대한 깊은 이해를 확인합니다.',
          listen_for: '멀티 클러스터, fallback 큐, 로컬 버퍼링 등 구체적 전략.',
          good: {
            text: '멀티 리전 클러스터 + 로컬 WAL 버퍼링 + alerting 전략 제시.',
            score: 10
          },
          poor: {
            text: 'Kafka는 잘 안 죽는다고 답변.',
            score: 0
          }
        },
        {
          id: 'q3-f2',
          trigger: 'Mid',
          question_text: '만약 일부 알림이 누락되면 어떻게 탐지하고 복구하시겠습니까?',
          why_matters: '장애 복구 전략의 구체성을 확인합니다.',
          listen_for: '모니터링, DLQ, 재처리 로직 등.',
          good: {
            text: 'consumer lag 모니터링 + DLQ + 재처리 배치 언급.',
            score: 5
          },
          poor: {
            text: '로그를 확인하겠다 정도의 답변.',
            score: -3
          }
        },
        {
          id: 'q3-f3',
          trigger: 'Low',
          question_text: '동시에 많은 요청이 들어오면 데이터베이스에 직접 쓰는 것과 메시지 큐를 사용하는 것의 차이가 무엇인가요?',
          why_matters: '기본적인 비동기 처리 개념 이해를 확인.',
          listen_for: '동기/비동기 차이, 병목 지점에 대한 기본 이해.',
          good: {
            text: 'DB 병목 vs 큐의 버퍼링 효과를 설명.',
            score: 5
          },
          poor: {
            text: '차이를 설명하지 못함.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "실제로 대규모 시스템을 설계해본 경험이 있는지"를 확인합니다. 결제 알림이 1초라도 늦거나 누락되면 고객 불만과 매출 손실로 직결됩니다.',
        daily_analogy: '우체국에 비유하면, 편지 1만 통을 동시에 보내야 하는 상황입니다. 좋은 답변은 "자동 분류기로 우편번호별로 나누고, 배달 차량을 여러 대 투입하고, 배달 실패한 건은 별도 보관함에 모아 재배달한다"처럼 체계적입니다. 나쁜 답변은 "우체부 한 명이 다 배달한다"입니다.',
        level_expectation: 'CTO 수준에서는 단순히 기술 이름을 나열하는 게 아니라, "왜 이 기술을 선택했는지", "문제가 생기면 어떻게 대응하는지", "시스템을 어떻게 감시하는지"까지 포함해야 합니다.'
      },
      expected_answer: {
        core: '• 메시지 전달: Kafka(대량 메시지 전달 시스템)로 초당 1만 건 처리\n• 순서 보장: 같은 사용자의 알림은 순서가 뒤바뀌지 않도록 설계\n• 장애 대응: 문제 발생 시 자동 차단(Circuit Breaker) + 실패한 알림 별도 보관 후 재시도(DLQ)\n• 감시: 알림 지연 시간을 실시간으로 추적하고 이상 발생 시 즉시 알림',
        example: '저는 이전 회사에서 비슷한 시스템을 구축했습니다. 핵심 설계는 이렇습니다. 결제가 발생하면 Kafka라는 메시지 전달 시스템에 알림을 등록합니다. 처리 서버를 10대로 나눠서 동시에 처리하되, 같은 사용자의 알림은 항상 같은 서버가 처리하여 순서를 보장합니다. 만약 외부 알림 서비스(SMS, 이메일)가 응답하지 않으면, Circuit Breaker가 자동으로 해당 경로를 차단해서 전체 시스템이 멈추는 것을 방지합니다. 실패한 알림은 DLQ(별도 보관함)에 모아두었다가 5분마다 자동으로 재시도합니다. 그리고 Grafana 대시보드로 알림 지연 시간, 실패율, 처리량을 실시간 모니터링합니다. 이 구조로 실제 블랙프라이데이 때 평소 3배 트래픽을 무중단으로 처리했습니다.',
        key_points: ['이벤트 기반', '장애 격리', '수평 확장', '모니터링']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['초당 10,000건의 트랜잭션을 처리하면서 99.99% 가용성을 보장하는 실시간 결제 알림 시스템을 어떻게 설계하시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 4,
      category: 'technical_depth',
      difficulty: 'Medium',
      title: '모놀리스 → MSA 전환 판단',
      question_text: '현재의 모놀리식 구조를 마이크로서비스로 전환해야 할지 결정하는 기준은 무엇이며, 전환한다면 위험을 어떻게 최소화하시겠습니까?',
      context_bridge: '저희 시스템은 모놀리식인데, 트래픽이 늘면서 배포가 느려지고 있습니다.',
      why_matters: '너무 이르게 MSA를 도입하다 실패하는 스타트업이 많습니다. 유행보다 실용성을 중시하는지 확인합니다.',
      listen_for: 'MSA의 단점(복잡도, 운영 비용)을 인지하는지. "Strangler Fig Pattern" 같은 점진적 전략을 언급하면 좋습니다.',
      code_reference: null,
      terminology: [
        {
          term: 'Monolith',
          pronunciation: '모놀리스',
          explanation: '모든 기능이 하나의 큰 프로그램에 합쳐진 구조입니다.',
          definition: '모든 기능이 하나의 큰 프로그램에 합쳐진 구조입니다.',
          plain_language: '모든 기능이 하나의 큰 프로그램에 합쳐진 구조입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Microservices (MSA)',
          pronunciation: '마이크로서비스',
          explanation: '기능별로 작은 프로그램들을 나눠서 각각 독립적으로 배포하는 방식입니다.',
          definition: '기능별로 작은 프로그램들을 나눠서 각각 독립적으로 배포하는 방식입니다.',
          plain_language: '기능별로 작은 프로그램들을 나눠서 각각 독립적으로 배포하는 방식입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Strangler Fig Pattern',
          pronunciation: '스트랭글러 피그 패턴',
          explanation: '기존 시스템을 한번에 바꾸지 않고 새 시스템이 점점 대체하는 전략입니다.'
        },
        {
          term: 'CI/CD',
          pronunciation: '씨아이 씨디',
          explanation: 'Continuous Integration/Deployment. 코드 변경을 자동으로 테스트하고 배포하는 시스템입니다.'
        },
        {
          term: 'Domain Boundary',
          pronunciation: '도메인 바운더리',
          explanation: '업무 영역의 경계. 결제 기능, 회원 기능처럼 서로 다른 기능을 구분하는 선입니다.'
        },
        {
          term: 'Feature Flag',
          pronunciation: '피처 플래그',
          explanation: '기능 플래그. 코드는 배포하되 스위치로 켜고 끌 수 있게 만든 것. 점진적 출시에 유용합니다.'
        },
        {
          term: 'Distributed Tracing',
          pronunciation: '디스트리뷰티드 트레이싱',
          explanation: '여러 서비스에 걸친 요청의 흐름을 추적하는 기술. MSA에서 문제 원인을 찾는 데 필수입니다.'
        },
        {
          term: 'Service Mesh',
          pronunciation: '서비스 메시',
          explanation: '마이크로서비스들 간의 통신을 관리하고 감시하는 인프라 계층입니다.'
        },
        {
          term: 'Traffic',
          pronunciation: '트래픽',
          explanation: '서비스를 이용하는 사용자 수나 요청 양. 도로의 차량 흐름에 비유할 수 있습니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: 'Strangler Fig Pattern',
          importance: 'must',
          explanation: '점진적 전환의 핵심 전략'
        },
        {
          keyword: '도메인 경계',
          importance: 'must',
          explanation: '어디를 먼저 분리할지 판단하는 기준'
        },
        {
          keyword: '인프라 성숙도',
          importance: 'good_to_have',
          explanation: 'MSA 전에 CI/CD, 모니터링이 갖춰져야 함'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 25,
          text: '도메인 경계 명확하고 독립 배포가 빈번한 모듈부터 점진적 분리. 인프라 성숙도 선행 강조.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 12,
          text: '"요즘 다들 하니까"라는 식으로 유행을 따르는 답변. 왜 우리 회사에 필요한지 구체적 이유가 없습니다.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 5,
          text: '마이크로서비스가 무엇인지 정확히 설명하지 못하거나, 단순히 "서버를 여러 개로 나누는 것"이라고만 이해하고 있습니다.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q4-f1',
          trigger: 'Expert',
          question_text: '모놀리스를 유지하면서도 배포 속도를 개선할 방법이 있다면 무엇이 있을까요?',
          why_matters: 'MSA가 유일한 해법이 아님을 아는지 확인.',
          listen_for: '모듈화, 기능 플래그, 병렬 빌드 등 대안적 접근.',
          good: {
            text: '모놀리스 내 모듈화 + 기능 플래그 + 빌드 최적화 등 대안 제시.',
            score: 8
          },
          poor: {
            text: '모놀리스면 무조건 느릴 수밖에 없다고 답변.',
            score: 0
          }
        },
        {
          id: 'q4-f2',
          trigger: 'Mid',
          question_text: 'MSA 도입 시 가장 큰 위험은 무엇이라고 생각하시나요?',
          why_matters: 'MSA의 현실적 단점을 인지하는지 확인.',
          listen_for: '운영 복잡도, 분산 트랜잭션, 디버깅 어려움 등.',
          good: {
            text: '구체적 위험(분산 트레이싱, 데이터 일관성)을 언급.',
            score: 5
          },
          poor: {
            text: '위험은 크지 않다, 잘 하면 된다.',
            score: -3
          }
        },
        {
          id: 'q4-f3',
          trigger: 'Low',
          question_text: '그렇다면 하나의 큰 프로그램(모놀리스)의 장점은 무엇이 있을까요?',
          why_matters: '기본 아키텍처 이해도를 재확인.',
          listen_for: '단순성, 배포 용이성, 디버깅 편의성 등.',
          good: {
            text: '모놀리스의 장점을 이해하고 설명.',
            score: 5
          },
          poor: {
            text: '장점이 없다고 답변.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "유행을 무조건 따르는 사람인지, 상황에 맞는 판단을 하는 사람인지"를 확인합니다. MSA 전환은 비용이 크므로, 정말 필요한지 냉정하게 판단하는 것이 중요합니다.',
        daily_analogy: '자동차 비유: 현재 차(모놀리스)가 느리다고 무조건 새 차(MSA)를 사는 게 아니라, 먼저 엔진오일을 갈거나 타이어를 교체하는 것이 더 나을 수 있습니다. 새 차가 필요하더라도 한번에 바꾸지 않고, 부품을 하나씩 교체하면서 운행을 멈추지 않는 전략이 좋습니다.',
        level_expectation: 'CTO 수준에서는 "MSA의 단점(운영 복잡도 증가, 디버깅 어려움, 팀 간 소통 비용)"을 명확히 알고, "우리 회사에 정말 필요한지" 구체적 기준을 제시할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 전환 기준: "배포를 주 1회밖에 못 하고 있는가?", "한 팀이 고친 코드가 다른 팀 기능을 자주 망가뜨리는가?"\n• 전략: Strangler Fig Pattern — 기존 시스템을 유지하면서 새 시스템을 옆에 하나씩 만들어 점진적으로 교체\n• 선행 조건: 자동 배포 시스템(CI/CD)과 모니터링이 먼저 갖춰져야 함',
        example: '무조건 MSA로 가자는 것은 위험합니다. 먼저 "왜 느린지"를 정확히 분석합니다. 이전 회사에서는 배포가 주 1회, 3시간 걸렸고, 결제팀이 고친 코드가 회원 기능을 자주 망가뜨리는 상황이었습니다. 이때 저는 세 가지 기준으로 전환을 결정했습니다: ①배포 빈도가 비즈니스 요구보다 느린가, ②팀 간 코드 충돌이 잦은가, ③장애가 전체로 퍼지는가. 전환은 Strangler Fig 패턴으로 가장 변경이 잦은 결제 모듈부터 분리했고, 6개월에 걸쳐 점진적으로 진행했습니다. 하지만 전환 전에 반드시 자동 배포(CI/CD)와 모니터링을 먼저 구축했습니다. 이것 없이 MSA로 가면 장애 원인을 찾을 수가 없습니다.',
        key_points: ['실용적 판단', '점진적 전환', '선행 조건 인식']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['현재의 모놀리식 구조를 마이크로서비스로 전환해야 할지 결정하는 기준은 무엇이며, 전환한다면 위험을 어떻게 최소화하시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 5,
      category: 'execution_ownership',
      difficulty: 'Medium',
      title: '불완전한 정보 하의 기술 결정',
      question_text: '정보가 불완전하고 시간 압박이 있는 상황에서 중요한 기술적 결정을 내려야 했던 경험을 말씀해주세요.',
      context_bridge: '스타트업에서는 항상 정보가 부족한 상황에서 빠르게 결정해야 합니다.',
      why_matters: '불확실성 속 의사결정 능력을 테스트합니다.',
      listen_for: '"충분한" 정보만 모아 판단하는 체계적 접근과 결과에 대한 책임감.',
      code_reference: null,
      terminology: [
        {
          term: 'Trade-off',
          pronunciation: '트레이드오프',
          explanation: '하나를 얻기 위해 다른 것을 포기해야 하는 선택 상황입니다.',
          definition: '하나를 얻기 위해 다른 것을 포기해야 하는 선택 상황입니다.',
          plain_language: '하나를 얻기 위해 다른 것을 포기해야 하는 선택 상황입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Reversible Decision',
          pronunciation: '리버서블 디시전',
          explanation: '되돌릴 수 있는 결정. 나중에 바꿀 수 있으면 빠르게 결정해도 됩니다.',
          definition: '되돌릴 수 있는 결정. 나중에 바꿀 수 있으면 빠르게 결정해도 됩니다.',
          plain_language: '되돌릴 수 있는 결정. 나중에 바꿀 수 있으면 빠르게 결정해도 됩니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Irreversible Decision',
          pronunciation: '이리버서블 디시전',
          explanation: '되돌릴 수 없는 결정. 데이터베이스 선택 같은 것은 바꾸기 어려워 신중해야 합니다.'
        },
        {
          term: 'Framework',
          pronunciation: '프레임워크',
          explanation: '프로그램을 만들 때 기본 뼈대를 제공하는 도구. 집을 지을 때 기본 설계도 같은 것입니다.'
        },
        {
          term: 'Migration',
          pronunciation: '마이그레이션',
          explanation: '시스템이나 데이터를 한 환경에서 다른 환경으로 옮기는 작업. 이사와 비슷합니다.'
        },
        {
          term: 'MVP (Minimum Viable Product)',
          pronunciation: '엠브이피',
          explanation: '최소 기능만 갖춘 제품. 완벽하지 않아도 핵심 가치를 전달하고 피드백을 받을 수 있습니다.'
        },
        {
          term: 'Pivot',
          pronunciation: '피봇',
          explanation: '방향 전환. 계획이 잘못되었다고 판단하면 빠르게 다른 방향으로 바꾸는 것입니다.'
        },
        {
          term: 'Metric',
          pronunciation: '메트릭',
          explanation: '측정 지표. 성공 여부를 판단하기 위해 숫자로 측정하는 기준입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '가역적/비가역적 구분',
          importance: 'must',
          explanation: '되돌릴 수 있는 결정과 없는 결정을 다르게 접근해야 함'
        },
        {
          keyword: '70% 규칙',
          importance: 'good_to_have',
          explanation: 'Jeff Bezos의 원칙: 70% 정보면 결정하라'
        },
        {
          keyword: '회귀 계획',
          importance: 'good_to_have',
          explanation: '결정이 틀렸을 때 돌아갈 수 있는 Plan B'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: '구체적 사례와 함께 결정 프레임워크 제시. 가역/비가역 구분, 70% 정보 원칙 등.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '경험은 있으나 체계적 프레임워크보다 직감 의존.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '구체적 사례 없음. 결정을 다른 사람에게 미루는 답변.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q5-f1',
          trigger: 'Expert',
          question_text: '그 결정이 틀렸다는 것을 언제, 어떻게 알 수 있었나요? 그때 어떻게 대처하셨습니까?',
          why_matters: '결정 이후 피드백 루프와 수정 능력을 확인.',
          listen_for: '사전에 정한 검증 기준, 빠른 피봇, 팀 커뮤니케이션.',
          good: {
            text: '사전 메트릭 설정 + 빠른 피봇 경험을 구체적으로 공유.',
            score: 8
          },
          poor: {
            text: '결정이 틀린 적이 없다고 답변.',
            score: -3
          }
        },
        {
          id: 'q5-f2',
          trigger: 'Mid',
          question_text: '직감으로 결정하신다면, 그 직감이 틀릴 때는 어떻게 하시나요?',
          why_matters: '직감 의존의 한계를 인식하는지 확인.',
          listen_for: '직감 + 데이터의 조합, 빠른 실험 등.',
          good: {
            text: '직감으로 시작하되 데이터로 검증하는 프로세스 설명.',
            score: 5
          },
          poor: {
            text: '직감이 대체로 맞다고 주장.',
            score: 0
          }
        },
        {
          id: 'q5-f3',
          trigger: 'Low',
          question_text: '만약 DB를 PostgreSQL과 MongoDB 중 선택해야 한다면, 어떤 기준으로 결정하시겠습니까?',
          why_matters: '구체적 시나리오에서 의사결정 과정을 유도.',
          listen_for: '데이터 구조, 쿼리 패턴, 일관성 요구 등 기준.',
          good: {
            text: '사용 패턴에 따른 합리적 기준 제시.',
            score: 5
          },
          poor: {
            text: '둘 다 좋다, 아무거나.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "완벽한 정보가 없는 상황에서도 결정을 내릴 수 있는 사람인지"를 확인합니다. 스타트업에서는 항상 정보가 부족한데, 결정을 미루면 기회를 놓칩니다.',
        daily_analogy: '비 올 확률 60%일 때 우산을 가져갈지 결정하는 것과 비슷합니다. 좋은 리더는 "비가 와도 되돌아올 수 있는 거리면 우산 없이 가고, 먼 거리면 가져간다"처럼 되돌릴 수 있는지(가역성)를 기준으로 빠르게 판단합니다.',
        level_expectation: 'CTO 수준에서는 "이 결정을 잘못해도 되돌릴 수 있는가?"를 구분하고, 되돌릴 수 있는 결정은 빠르게, 되돌릴 수 없는 결정은 신중하게 하는 프레임워크가 있어야 합니다.'
      },
      expected_answer: {
        core: '• 상황: 구체적인 기술 결정 사례 (무엇을, 왜, 어떤 제약 하에서)\n• 판단 기준: 되돌릴 수 있는 결정인지 아닌지(가역성) 먼저 판단\n• 프로세스: 핵심 정보만 빠르게 수집(70% 정보면 결정) → 선택지 비교 → 결정 + 잘못될 경우 되돌아갈 계획\n• 결과: 결정에 대한 책임과 그로부터 배운 것',
        example: '이전 회사에서 데이터베이스를 PostgreSQL과 MongoDB 중 선택해야 했는데, 일주일 안에 결정해야 했습니다. 완벽한 분석은 불가능했지만, 3일간 핵심 질문 3개만 분석했습니다: ①우리 데이터가 표 형태(정형)인가 자유 형태(비정형)인가, ②복잡한 검색이 많은가, ③팀이 어떤 기술에 익숙한가. 결과적으로 데이터의 80%가 정형이고 팀이 SQL에 익숙해서 PostgreSQL을 선택했습니다. 동시에 "만약 성능이 안 나오면 3개월 내 전환할 수 있도록" 데이터 접근 부분을 교체 가능하게 설계했습니다. 결과적으로 올바른 선택이었고, 이 경험으로 "되돌릴 수 있는 결정은 70% 정보로 빠르게 내리자"는 원칙을 갖게 됐습니다.',
        key_points: ['체계적 프레임워크', '가역성 판단', '결과 오너십']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['정보가 불완전하고 시간 압박이 있는 상황에서 중요한 기술적 결정을 내려야 했던 경험을 말씀해주세요.', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 6,
      category: 'execution_ownership',
      difficulty: 'Medium',
      title: '엔지니어링 메트릭 설정',
      question_text: '엔지니어링 팀 메트릭을 어떻게 설정하고 추적하시겠습니까? 첫 6개월 동안 어떤 지표를 도입하시겠습니까?',
      context_bridge: '현재 저희는 엔지니어링 생산성이나 품질을 측정하는 지표가 없습니다.',
      why_matters: '측정 철학과 선행/후행 지표 구분 능력을 확인합니다.',
      listen_for: '생산성과 품질 지표의 균형, 게이밍 리스크 인식.',
      code_reference: null,
      terminology: [
        {
          term: 'DORA Metrics',
          pronunciation: '도라 메트릭스',
          explanation: '소프트웨어 팀 효율성을 측정하는 4가지 핵심 지표: 배포 빈도, 변경 리드타임, 복구 시간, 실패율.',
          definition: '소프트웨어 팀 효율성을 측정하는 4가지 핵심 지표: 배포 빈도, 변경 리드타임, 복구 시간, 실패율.',
          plain_language: '소프트웨어 팀 효율성을 측정하는 4가지 핵심 지표: 배포 빈도, 변경 리드타임, 복구 시간, 실패율.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Leading Indicator',
          pronunciation: '리딩 인디케이터',
          explanation: '미래 결과를 예측하는 지표. 예: 코드 리뷰 속도 → 배포 속도 예측.',
          definition: '미래 결과를 예측하는 지표. 예: 코드 리뷰 속도 → 배포 속도 예측.',
          plain_language: '미래 결과를 예측하는 지표. 예: 코드 리뷰 속도 → 배포 속도 예측.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Deployment Frequency',
          pronunciation: '디플로이먼트 프리퀀시',
          explanation: '배포 빈도. 코드를 얼마나 자주 실제 서비스에 반영하는지 나타내는 지표입니다.'
        },
        {
          term: 'Lead Time',
          pronunciation: '리드 타임',
          explanation: '변경 리드타임. 코드를 작성한 후 실제 사용자에게 전달되기까지 걸리는 시간입니다.'
        },
        {
          term: 'MTTR (Mean Time To Recovery)',
          pronunciation: '엠티티알',
          explanation: '평균 복구 시간. 장애가 발생했을 때 정상화하기까지 걸리는 시간입니다.'
        },
        {
          term: 'Change Failure Rate',
          pronunciation: '체인지 페일러 레이트',
          explanation: '변경 실패율. 배포한 것 중 문제가 생겨 되돌려야 하는 비율입니다.'
        },
        {
          term: 'Baseline',
          pronunciation: '베이스라인',
          explanation: '기준선. 개선하기 전의 현재 상태를 측정한 것. 비교 기준이 됩니다.'
        },
        {
          term: 'Gaming',
          pronunciation: '게이밍',
          explanation: '지표 조작. 실제 개선 없이 숫자만 좋아 보이게 만드는 부정적 행위입니다.'
        },
        {
          term: 'Commit',
          pronunciation: '커밋',
          explanation: '코드 변경사항을 저장소에 기록하는 것. 저장 버튼을 누르는 것과 비슷합니다.'
        },
        {
          term: 'Bug',
          pronunciation: '버그',
          explanation: '프로그램의 오류나 결함. 의도와 다르게 동작하는 문제를 말합니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: 'DORA Metrics',
          importance: 'must',
          explanation: '업계 표준 엔지니어링 지표'
        },
        {
          keyword: '베이스라인 측정',
          importance: 'must',
          explanation: '현재 상태를 먼저 파악해야 개선 가능'
        },
        {
          keyword: '게이밍 방지',
          importance: 'good_to_have',
          explanation: '지표를 조작하는 행위에 대한 인식'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: 'DORA 기반 + 팀 상황 커스터마이즈. 게이밍 방지와 지표 한계도 인식.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '코드를 얼마나 자주 올렸는지(커밋 수)처럼 "행동 횟수"만 측정하려 합니다. 실제 결과물의 품질이나 고객에게 전달되는 속도 같은 "성과 지표"가 빠져 있습니다.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '지표 불필요하다거나 특별한 계획 없음.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q6-f1',
          trigger: 'Expert',
          question_text: '팀원이 DORA 메트릭에 반발한다면 어떻게 설득하시겠습니까?',
          why_matters: '리더십과 변화 관리 능력을 확인.',
          listen_for: '팀 합의 프로세스, 목적 공유, 점진적 도입.',
          good: {
            text: '팀과 함께 목표를 설정하고 측정의 목적을 투명하게 공유.',
            score: 8
          },
          poor: {
            text: '리더가 정하면 따라야 한다.',
            score: 0
          }
        },
        {
          id: 'q6-f2',
          trigger: 'Mid',
          question_text: '커밋 수가 높은데 버그도 많은 개발자가 있다면 어떻게 평가하시겠습니까?',
          why_matters: '단일 지표의 한계를 인식하는지 확인.',
          listen_for: '다면 평가, 품질 지표와의 조합.',
          good: {
            text: '활동 지표와 품질 지표를 함께 봐야 한다는 인식.',
            score: 5
          },
          poor: {
            text: '커밋이 많으면 열심히 하는 것.',
            score: -3
          }
        },
        {
          id: 'q6-f3',
          trigger: 'Low',
          question_text: '팀이 잘 하고 있는지 어떻게 알 수 있을까요? 지표 없이 어떻게 판단하시나요?',
          why_matters: '측정의 필요성을 재인식시키기 위한 질문.',
          listen_for: '결국 무언가를 측정해야 한다는 인식.',
          good: {
            text: '측정의 필요성을 인정하고 간단한 지표라도 제시.',
            score: 5
          },
          poor: {
            text: '느낌으로 안다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "팀이 잘 하고 있는지를 어떻게 객관적으로 측정할 수 있는가"를 확인합니다. 감으로 판단하는 것이 아니라 데이터로 확인하는 능력이 중요합니다.',
        daily_analogy: '건강검진과 비슷합니다. 혈압, 혈당 같은 핵심 수치를 정기적으로 측정하면 건강 문제를 조기에 발견할 수 있습니다. 개발팀도 "배포 빈도", "장애 복구 시간" 같은 핵심 수치를 측정해야 문제를 일찍 발견합니다.',
        level_expectation: 'CTO 수준에서는 업계 표준 지표(DORA Metrics)를 알고, 이를 회사 상황에 맞게 조정하며, 지표를 속이는 행위(게이밍)에 대한 대비도 있어야 합니다.'
      },
      expected_answer: {
        core: '• 첫 달: 현재 상태 측정(베이스라인) — 지금 배포가 얼마나 자주 되는지, 장애 복구에 얼마나 걸리는지 파악\n• 핵심 지표: DORA 4가지 — ①배포 빈도 ②코드 작성부터 배포까지 걸리는 시간 ③장애 복구 시간 ④배포 후 문제 발생률\n• 주의: 지표를 속이는 행위(예: 의미 없는 코드를 올려 커밋 수만 늘리기) 방지, 팀과 합의해서 도입',
        example: '첫 달은 현재 상태를 정확히 측정하는 데 씁니다. 지금 배포가 주 몇 회인지, 코드 작성부터 고객에게 전달되기까지 며칠 걸리는지, 장애가 나면 복구에 몇 시간 걸리는지를 숫자로 파악합니다. 그 다음 DORA Metrics 중 "배포 빈도"와 "변경 리드타임"부터 팀과 함께 목표를 세웁니다. 이전 회사에서는 배포 빈도를 주 1회에서 일 2회로 개선했고, 이를 위해 자동화 테스트를 먼저 구축했습니다. 중요한 건 지표를 위에서 강제하지 않는 것입니다. 팀과 함께 "왜 이 수치를 측정하는지" 공유하고, 측정 결과를 투명하게 공개해서 개선 방향을 같이 정합니다.',
        key_points: ['DORA 기반', '베이스라인 측정', '게이밍 인식']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['엔지니어링 팀 메트릭을 어떻게 설정하고 추적하시실 건가요? 첫 6개월 동안 어떤 지표를 도입하시겠습니까에 대해 설명해 주시겠습니까?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 7,
      category: 'communication',
      difficulty: 'Medium',
      title: 'CEO와의 일정 갈등',
      question_text: 'CEO가 핵심 고객을 위해 6주 안에 대형 기능을 약속하고 싶어합니다. 팀은 10주가 필요하다고 추정합니다. 이 대화를 어떻게 진행하시겠습니까?',
      context_bridge: '비즈니스 요구와 기술 현실 사이의 갈등은 CTO의 일상입니다.',
      why_matters: '비즈니스-엔지니어링 긴장에서 건설적 문제해결 능력을 테스트합니다.',
      listen_for: '단순 거부도, 무조건 수용도 아닌, 창의적 문제해결과 명확한 커뮤니케이션.',
      code_reference: null,
      terminology: [
        {
          term: 'MVP',
          pronunciation: '엠브이피',
          explanation: '최소 기능만 갖춘 첫 번째 버전. 완벽하지 않아도 핵심 가치를 전달합니다.',
          definition: '최소 기능만 갖춘 첫 번째 버전. 완벽하지 않아도 핵심 가치를 전달합니다.',
          plain_language: '최소 기능만 갖춘 첫 번째 버전. 완벽하지 않아도 핵심 가치를 전달합니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Scope',
          pronunciation: '스코프',
          explanation: '구현할 기능의 범위. 범위를 줄이면 시간을 절약할 수 있습니다.',
          definition: '구현할 기능의 범위. 범위를 줄이면 시간을 절약할 수 있습니다.',
          plain_language: '구현할 기능의 범위. 범위를 줄이면 시간을 절약할 수 있습니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Deadline',
          pronunciation: '데드라인',
          explanation: '마감 기한. 작업을 끝내야 하는 최종 시간입니다.'
        },
        {
          term: 'Scope Negotiation',
          pronunciation: '스코프 네고시에이션',
          explanation: '범위 협상. 시간이 부족하면 기능을 줄이거나 우선순위를 조정하는 협의입니다.'
        },
        {
          term: 'Release',
          pronunciation: '릴리스',
          explanation: '제품이나 기능을 사용자에게 공개하는 것. 출시와 같은 의미입니다.'
        },
        {
          term: 'Quality',
          pronunciation: '퀄리티',
          explanation: '품질. 제품의 완성도, 안정성, 사용자 만족도를 나타냅니다.'
        },
        {
          term: 'Burnout',
          pronunciation: '번아웃',
          explanation: '탈진, 소진. 과도한 업무로 정신적, 육체적으로 지치는 상태입니다.'
        },
        {
          term: 'Risk',
          pronunciation: '리스크',
          explanation: '위험. 계획대로 되지 않을 가능성이나 문제가 발생할 수 있는 요소입니다.'
        },
        {
          term: 'Stakeholder',
          pronunciation: '스테이크홀더',
          explanation: '이해관계자. CEO, 투자자, 고객처럼 프로젝트에 영향을 받거나 영향을 주는 사람입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '범위 협상 (Scope negotiation)',
          importance: 'must',
          explanation: '일정 vs 범위 트레이드오프를 제시해야 함'
        },
        {
          keyword: 'MVP 제안',
          importance: 'must',
          explanation: '핵심 기능만 먼저 전달하는 대안'
        },
        {
          keyword: '비즈니스 목표 이해',
          importance: 'good_to_have',
          explanation: 'CEO의 동기를 먼저 파악'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: '6주 MVP 범위를 제안하고 나머지를 2차 릴리스로 분리. CEO 목표를 존중하면서 리스크 투명 공유.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '야근해서 맞추겠다거나 무조건 안 된다고 거부.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: 'CEO와의 대화를 회피하거나 거짓으로 약속.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q7-f1',
          trigger: 'Expert',
          question_text: 'CEO가 범위 축소를 거부하고 전체 기능을 6주에 원한다면 최종적으로 어떻게 하시겠습니까?',
          why_matters: '갈등 상황에서의 최종 의사결정과 원칙을 확인.',
          listen_for: '데이터 기반 설득, 리스크 문서화, 최종 결정 수용 but 리스크 기록.',
          good: {
            text: '리스크를 문서화하고 CEO가 최종 결정하되 품질 타협의 결과를 투명하게 공유.',
            score: 8
          },
          poor: {
            text: 'CEO가 원하면 무조건 따르겠다.',
            score: 0
          }
        },
        {
          id: 'q7-f2',
          trigger: 'Mid',
          question_text: '야근으로 해결한다면 팀의 번아웃 위험은 어떻게 관리하시겠습니까?',
          why_matters: '지속가능성과 팀 관리 의식.',
          listen_for: '번아웃 인식, 대안적 접근, 팀 보호.',
          good: {
            text: '단기적 해결임을 인지하고 보상/휴식 계획 포함.',
            score: 5
          },
          poor: {
            text: '스타트업이니까 당연히 야근해야 한다.',
            score: -3
          }
        },
        {
          id: 'q7-f3',
          trigger: 'Low',
          question_text: '만약 약속한 기한에 기능을 못 만들면 어떤 결과가 생길까요?',
          why_matters: '결과에 대한 인식과 책임감.',
          listen_for: '비즈니스 영향 이해, 선제적 커뮤니케이션.',
          good: {
            text: '고객 신뢰 손상과 비즈니스 영향을 구체적으로 인지.',
            score: 5
          },
          poor: {
            text: '그때 가서 생각하겠다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "비즈니스 요구와 기술 현실 사이에서 창의적으로 문제를 해결할 수 있는가"를 확인합니다. 무조건 "안 됩니다"도, 무조건 "하겠습니다"도 좋은 답이 아닙니다.',
        daily_analogy: '결혼식 케이크 주문과 비슷합니다. 3단 케이크를 원하는데 시간이 부족하면, "못 합니다"가 아니라 "2단으로 먼저 만들고 결혼식 당일에 꼭대기 장식을 추가하겠습니다"처럼 핵심은 지키면서 범위를 조절하는 제안이 좋습니다.',
        level_expectation: 'CTO 수준에서는 먼저 CEO가 왜 6주를 원하는지(고객 약속? 투자자 발표?) 이유를 파악하고, 핵심 기능만 추려서 6주 안에 전달하는 대안을 제시할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 1단계: CEO에게 "왜 6주인가" 비즈니스 이유를 먼저 파악\n• 2단계: 기능을 "반드시 필요"와 "있으면 좋음"으로 분류\n• 3단계: 핵심 기능만 6주에 전달(MVP) + 나머지는 4주 후 2차 전달 제안\n• 4단계: "6주에 전체를 하면 이런 위험이 있습니다"를 데이터로 투명하게 공유',
        example: '먼저 CEO와 30분 미팅을 잡고 "6주가 중요한 이유가 뭔가요?"를 물어봅니다. 예를 들어 핵심 고객 데모가 있다면, 그 데모에 꼭 필요한 기능 3개만 추립니다. 이전 회사에서 비슷한 상황이 있었는데, CEO는 12가지 기능을 원했지만 실제로 고객이 보고 싶어하는 건 3가지였습니다. "핵심 3가지를 6주에 완벽하게, 나머지 9가지를 이후 4주에 전달하겠다"고 제안했고, CEO도 납득했습니다. 동시에 "만약 전체를 6주에 하면, 품질 저하로 데모 중 오류가 날 확률이 높다"는 리스크를 구체적으로 공유했습니다.',
        key_points: ['비즈니스 이해', '범위 협상', '투명한 커뮤니케이션']
      },
      jd_competency_link: 'JD 요구사항: "팀 리더십 8~15명 규모" → 비기술 이해관계자와의 소통 검증',
      generation_rationale: '후보자의 팀 규모 경험(4-6명)이 요구(8-15명)보다 작아 소통 역량 확인 필요',
      skills_assessed: ['communication', 'leadership'],
      alternative_phrasings: [
        'CEO가 핵심 고객을 위해 6주 안에 대형 기능을 약속하고 싶어합니다. 팀은 10주가 필요하다고 추정합니다. 이 대화를 어떻게 진행하시겠습니까에 대해 설명해 주시실 건가요?',
        '이 주제에 대한 경험이나 생각을 공유해 주세요.'
      ]
    },
    {
      id: 8,
      category: 'communication',
      difficulty: 'Easy',
      title: '비기술 이해관계자와의 소통',
      question_text: '기술적 트레이드오프를 비기술적인 이사회 멤버나 투자자에게 어떻게 설명하시나요?',
      context_bridge: 'CTO는 기술과 비즈니스 세계를 연결해야 합니다.',
      why_matters: '기술-비즈니스 소통 능력은 CTO의 핵심 역량입니다.',
      listen_for: '비유 사용, 비즈니스 임팩트 중심 설명, 정확성을 잃지 않는 단순화.',
      code_reference: null,
      terminology: [
        {
          term: 'Trade-off',
          pronunciation: '트레이드오프',
          explanation: '하나를 얻으면 다른 하나를 포기해야 하는 상황. 속도와 품질, 비용과 성능 같은 선택입니다.',
          definition: '하나를 얻으면 다른 하나를 포기해야 하는 상황. 속도와 품질, 비용과 성능 같은 선택입니다.',
          plain_language: '하나를 얻으면 다른 하나를 포기해야 하는 상황. 속도와 품질, 비용과 성능 같은 선택입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Stakeholder',
          pronunciation: '스테이크홀더',
          explanation: '이해관계자. 투자자, 이사회, CEO처럼 회사의 결정에 영향을 받는 사람들입니다.',
          definition: '이해관계자. 투자자, 이사회, CEO처럼 회사의 결정에 영향을 받는 사람들입니다.',
          plain_language: '이해관계자. 투자자, 이사회, CEO처럼 회사의 결정에 영향을 받는 사람들입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Technical Debt',
          pronunciation: '테크니컬 뎃',
          explanation: '기술 부채. 빨리 만들려고 대충 짠 코드가 나중에 더 큰 문제를 만드는 것입니다.'
        },
        {
          term: 'Server',
          pronunciation: '서버',
          explanation: '24시간 켜져 있는 컴퓨터. 사용자 요청을 받아 처리하고 응답을 돌려줍니다.'
        },
        {
          term: 'Database',
          pronunciation: '데이터베이스',
          explanation: '데이터를 체계적으로 저장하고 관리하는 시스템. 전자 도서관과 비슷합니다.'
        },
        {
          term: 'API',
          pronunciation: '에이피아이',
          explanation: 'Application Programming Interface. 프로그램끼리 대화하는 방법. 레스토랑 메뉴판처럼 선택지를 제공합니다.'
        },
        {
          term: 'Cloud',
          pronunciation: '클라우드',
          explanation: '인터넷으로 빌려 쓰는 컴퓨터 자원. 직접 서버를 사지 않고 AWS 같은 곳에서 빌립니다.'
        },
        {
          term: 'Scalability',
          pronunciation: '스케일러빌리티',
          explanation: '확장성. 사용자가 10배 늘어나도 시스템이 버틸 수 있는 능력입니다.'
        },
        {
          term: 'Performance',
          pronunciation: '퍼포먼스',
          explanation: '성능. 시스템이 얼마나 빠르고 효율적으로 동작하는지를 나타냅니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '비유 활용',
          importance: 'must',
          explanation: '기술 개념을 일상적 비유로 변환해야 함'
        },
        {
          keyword: '비즈니스 임팩트',
          importance: 'must',
          explanation: '"이것이 매출/비용에 어떤 영향"으로 번역'
        },
        {
          keyword: '청중 맞춤',
          importance: 'good_to_have',
          explanation: '투자자, 이사회, CEO 각각 다르게'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 15,
          text: '구체적 비유와 비즈니스 언어로 설명하는 실제 예시 제시. 청중에 따라 수준 조절.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 8,
          text: '설명하려 노력하지만 기술 용어를 많이 사용.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '"기술적인 부분은 믿어주세요"라거나 설명 포기.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q8-f1',
          trigger: 'Expert',
          question_text: '이사회에서 "왜 기술 부채 해결에 2개월을 써야 하는가"라는 질문을 받으면 어떻게 답하시겠습니까?',
          why_matters: '추상적 기술 개념의 비즈니스 가치 설득력.',
          listen_for: '비용 절감, 개발 속도 향상 등 구체적 비즈니스 메트릭.',
          good: {
            text: '기술 부채의 비용을 숫자로 환산(개발 속도 30% 저하 → 매출 영향)하여 설명.',
            score: 8
          },
          poor: {
            text: '기술적으로 필요하니까라고 답변.',
            score: 0
          }
        },
        {
          id: 'q8-f2',
          trigger: 'Mid',
          question_text: '방금 답변에서 사용하신 기술 용어를 저(비개발자)에게 다시 설명해주실 수 있나요?',
          why_matters: '실시간으로 청중 수준에 맞출 수 있는지.',
          listen_for: '즉석에서 비유로 전환하는 능력.',
          good: {
            text: '즉시 비유나 일상 언어로 재설명.',
            score: 5
          },
          poor: {
            text: '같은 기술 용어로 반복 설명.',
            score: -2
          }
        },
        {
          id: 'q8-f3',
          trigger: 'Low',
          question_text: '기술을 모르는 사람에게 "서버"가 무엇인지 설명한다면 어떻게 하시겠습니까?',
          why_matters: '가장 기본적인 설명 능력 확인.',
          listen_for: '일상적 비유로의 변환 시도.',
          good: {
            text: '"24시간 편의점 같은 컴퓨터" 등 비유 시도.',
            score: 5
          },
          poor: {
            text: '서버는 서버라고 답변.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "기술을 모르는 사람에게 기술적 상황을 이해시킬 수 있는가"를 확인합니다. CTO는 개발팀과 경영진 사이의 통역사입니다.',
        daily_analogy: '의사가 환자에게 진단 결과를 설명하는 것과 같습니다. "좌측 대퇴골 골절입니다"라고 하면 환자는 모릅니다. "왼쪽 허벅지뼈가 부러졌고, 6주 깁스하면 완치됩니다"라고 해야 합니다. 기술 용어를 일상 언어로 바꾸는 능력이 핵심입니다.',
        level_expectation: 'CTO 수준에서는 같은 내용이라도 듣는 사람(투자자, CEO, 이사회)에 따라 설명 방식을 바꿀 수 있어야 합니다. 투자자에게는 "수익에 미치는 영향"으로, CEO에게는 "경쟁사 대비 전략"으로 번역합니다.'
      },
      expected_answer: {
        core: '• 원칙 1: 기술 용어를 일상 비유로 바꿔서 설명\n• 원칙 2: 항상 "이것이 매출/비용/고객에 어떤 영향인지"로 번역\n• 원칙 3: 듣는 사람(투자자/CEO/이사회)에 따라 설명 수준 조절',
        example: '기술 부채를 이사회에 설명할 때 이렇게 합니다: "지금 우리 개발팀이 새 기능을 만드는 데 시간의 40%를 쓰고, 60%를 과거의 임시방편 코드를 수습하는 데 씁니다. 이건 낡은 공장에서 기계 수리에 시간을 빼앗기는 것과 같습니다. 2개월간 공장을 정비하면, 이후 새 기능 개발 속도가 2배가 됩니다. 비용으로 환산하면, 지금 매달 개발자 인건비의 60%가 수리에 들어가고 있는데, 정비 후에는 30%로 줄어듭니다." 이렇게 항상 숫자와 비즈니스 영향으로 번역합니다.',
        key_points: ['비유 활용', '비즈니스 임팩트', '청중 맞춤']
      },
      jd_competency_link: 'JD 요구사항: "팀 리더십 8~15명 규모" → 비기술 이해관계자와의 소통 검증',
      generation_rationale: '후보자의 팀 규모 경험(4-6명)이 요구(8-15명)보다 작아 소통 역량 확인 필요',
      skills_assessed: ['communication', 'leadership'],
      alternative_phrasings: ['기술적 트레이드오프를 비기술적인 이사회 멤버나 투자자에게 어떻게 설명하시나요에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 9,
      category: 'risk_flags',
      difficulty: 'Easy',
      title: 'GitHub 활동 공백 확인',
      is_risk: true,
      risk_source: 'GitHub 활동 분석에서 Q2 2024 기간 커밋 거의 없음 탐지',
      question_text: '지난 1년간 GitHub 활동에 공백이 있는 기간이 보입니다. 해당 기간에 어떤 활동을 하고 계셨는지 말씀해주실 수 있나요?',
      context_bridge: '프로필 검토 중 Q2 2024에 GitHub 활동이 거의 없는 것을 확인했습니다.',
      why_matters: '프로필 리뷰에서 발견된 우려 사항을 직접 확인합니다. 솔직함과 자기인식을 테스트합니다.',
      listen_for: '방어적/변명하는 태도 vs 재충전/학습 등 목적 있는 시간이었는지.',
      code_reference: null,
      terminology: [
        {
          term: 'GitHub',
          pronunciation: '깃허브',
          explanation: '개발자들이 코드를 저장하고 공유하는 플랫폼. 포트폴리오이자 협업 도구입니다.',
          definition: '개발자들이 코드를 저장하고 공유하는 플랫폼. 포트폴리오이자 협업 도구입니다.',
          plain_language: '개발자들이 코드를 저장하고 공유하는 플랫폼. 포트폴리오이자 협업 도구입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Commit',
          pronunciation: '커밋',
          explanation: '코드 변경사항을 저장소에 기록하는 것. 작업 흔적이 모두 남습니다.',
          definition: '코드 변경사항을 저장소에 기록하는 것. 작업 흔적이 모두 남습니다.',
          plain_language: '코드 변경사항을 저장소에 기록하는 것. 작업 흔적이 모두 남습니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Burnout',
          pronunciation: '번아웃',
          explanation: '극심한 탈진 상태. 과로와 스트레스로 정신적, 육체적으로 지쳐 일을 할 수 없는 상태입니다.'
        },
        {
          term: 'Open Source',
          pronunciation: '오픈소스',
          explanation: '소스 코드를 공개하여 누구나 사용하고 수정할 수 있는 프로젝트입니다.'
        },
        {
          term: 'Side Project',
          pronunciation: '사이드 프로젝트',
          explanation: '개인적으로 진행하는 프로젝트. 회사 업무 외에 학습이나 실험 목적으로 만듭니다.'
        },
        {
          term: 'Self-care',
          pronunciation: '셀프케어',
          explanation: '자기 관리. 번아웃 예방을 위해 휴식, 운동, 취미 등으로 자신을 돌보는 것입니다.'
        },
        {
          term: 'Work-life Balance',
          pronunciation: '워크라이프 밸런스',
          explanation: '일과 삶의 균형. 과도한 업무로 개인 생활이 무너지지 않도록 조절하는 것입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '솔직한 설명',
          importance: 'must',
          explanation: '회피하지 않고 투명하게 답변하는 것이 핵심'
        },
        {
          keyword: '그 기간의 성장',
          importance: 'good_to_have',
          explanation: '공백 기간에도 학습/성장이 있었다면 긍정적'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 15,
          text: '번아웃 관리나 개인 프로젝트 등 솔직하고 건설적인 설명.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 8,
          text: '개인 사정이라고 짧게 얼버무림.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: -10,
          text: '답변 회피하거나 앞뒤가 안 맞는 설명.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q9-f1',
          trigger: 'Expert',
          question_text: '번아웃을 경험하셨다면, 이 역할에서 번아웃을 예방하기 위해 어떤 전략을 가지고 계신가요?',
          why_matters: '자기 관리 능력과 지속가능성을 확인.',
          listen_for: '구체적 예방 전략, 팀에도 적용할 수 있는 인식.',
          good: {
            text: '개인 루틴 + 팀 차원 예방 전략(온콜 로테이션 등) 모두 언급.',
            score: 8
          },
          poor: {
            text: '이제는 괜찮다고만 답변.',
            score: 0
          }
        },
        {
          id: 'q9-f2',
          trigger: 'Mid',
          question_text: '개인 사정이라고 하셨는데, 그 기간에 기술적으로 무언가 학습하신 것이 있다면 공유해주실 수 있나요?',
          why_matters: '공백 기간의 성장을 확인. 솔직함에 추가 기회 부여.',
          listen_for: '구체적 학습 내용이 있는지.',
          good: {
            text: '구체적 학습(새 언어, 기술 서적 등)을 공유.',
            score: 5
          },
          poor: {
            text: '특별히 없다.',
            score: 0
          }
        },
        {
          id: 'q9-f3',
          trigger: 'Low',
          question_text: '혹시 이 기간에 다른 곳에서 일을 하고 계셨거나, 이력서에 기재되지 않은 활동이 있으신가요?',
          why_matters: '정합성 검증. 비난이 아닌 확인.',
          listen_for: '일관된 답변인지, 추가 정보 제공 의지.',
          good: {
            text: '솔직하게 추가 맥락 제공.',
            score: 5
          },
          poor: {
            text: '답변 거부 또는 모순.',
            score: -5
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "후보자가 솔직한 사람인지, 그리고 어려운 시기를 어떻게 관리하는지"를 확인합니다. 공백 자체가 문제가 아니라, 그에 대한 태도와 설명이 중요합니다.',
        daily_analogy: '이력서의 공백 기간은 마치 여행 중 경유지와 같습니다. 목적 있는 경유(휴식, 학습, 개인 프로젝트)는 오히려 긍정적이지만, 설명을 회피하거나 앞뒤가 안 맞으면 신뢰 문제가 됩니다.',
        level_expectation: 'CTO 수준에서는 번아웃 경험이 있다면, 그것을 어떻게 극복했고, 앞으로 본인과 팀의 번아웃을 어떻게 예방할지까지 이야기할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 공백 사유를 솔직하게 설명 (회피하지 않음)\n• 그 기간에 무엇을 했는지 (학습, 프로젝트, 재충전 등)\n• 그 경험이 현재에 어떻게 도움이 되는지 연결',
        example: '솔직히 말씀드리면, 이전 회사에서 2년간 매주 60시간 이상 일하면서 번아웃이 왔습니다. 3개월간 의도적으로 쉬면서 두 가지를 했습니다. 하나는 Go 언어를 배워서 개인 프로젝트를 만들었고, 다른 하나는 번아웃의 원인을 분석했습니다. 돌아보니 "모든 결정을 혼자 내리려 했던 것"이 핵심 원인이었습니다. 이 경험 덕분에 지금은 의식적으로 위임하고, 팀에서도 온콜 로테이션과 주당 근무 시간 상한을 설정합니다. 번아웃 예방은 개인이 아니라 조직 차원에서 관리해야 한다는 것을 직접 경험으로 배웠습니다.',
        key_points: ['솔직함', '성장 마인드셋', '건설적 활용']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['지난 1년간 GitHub 활동에 공백이 있는 기간이 보입니다. 해당 기간에 어떤 활동을 하고 계셨는지 말씀해주실 수 있나요에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 10,
      category: 'risk_flags',
      difficulty: 'Hard',
      title: '팀 규모 확장 역량',
      is_risk: true,
      risk_source: 'LinkedIn 분석에서 최대 리드 경험 4-6명으로 확인. JD 요구 8-15명과 갭.',
      question_text: '4-6명의 팀을 리드한 경험이 있으신데, 이 역할은 15명 이상의 팀을 관리해야 합니다. 이 점프를 할 수 있다고 확신하시는 이유는 무엇인가요?',
      context_bridge: '이력서를 보면 최대 6명까지 리드한 경험이 있으십니다.',
      why_matters: '경험 갭을 직접 확인합니다. 자기인식과 성장 마인드셋을 테스트합니다.',
      listen_for: '갭에 대한 솔직한 인정, 극복할 구체적 계획, 전이 가능한 경험.',
      code_reference: null,
      terminology: [
        {
          term: 'Span of Control',
          pronunciation: '스팬 오브 컨트롤',
          explanation: '한 관리자가 직접 관리하는 팀원 수. 일반적으로 7-10명이 효과적입니다.',
          definition: '한 관리자가 직접 관리하는 팀원 수. 일반적으로 7-10명이 효과적입니다.',
          plain_language: '한 관리자가 직접 관리하는 팀원 수. 일반적으로 7-10명이 효과적입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Engineering Manager (EM)',
          pronunciation: '엔지니어링 매니저',
          explanation: '개발팀 관리자. 기술적 판단과 팀원 관리를 함께하는 중간 관리자입니다.',
          definition: '개발팀 관리자. 기술적 판단과 팀원 관리를 함께하는 중간 관리자입니다.',
          plain_language: '개발팀 관리자. 기술적 판단과 팀원 관리를 함께하는 중간 관리자입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Tech Lead',
          pronunciation: '테크 리드',
          explanation: '기술 리더. 팀의 기술적 방향을 제시하고 어려운 문제를 해결하는 시니어 개발자입니다.'
        },
        {
          term: 'Squad',
          pronunciation: '스쿼드',
          explanation: '작은 자율 팀. 5-7명으로 구성되어 특정 기능이나 제품을 독립적으로 개발합니다.'
        },
        {
          term: 'Delegation',
          pronunciation: '델리게이션',
          explanation: '위임. 리더가 모든 일을 직접 하지 않고 팀원에게 권한과 책임을 나눠주는 것입니다.'
        },
        {
          term: '1:1',
          pronunciation: '원온원',
          explanation: '관리자와 팀원이 둘이서만 하는 정기 미팅. 피드백과 성장을 위한 개인 면담입니다.'
        },
        {
          term: 'Org Chart',
          pronunciation: '오그 차트',
          explanation: '조직도. 회사의 보고 체계와 팀 구조를 나타내는 도표입니다.'
        },
        {
          term: 'People Management',
          pronunciation: '피플 매니지먼트',
          explanation: '인사 관리. 채용, 평가, 성장 지원, 갈등 해결 등 사람과 관련된 업무를 관리하는 것입니다.'
        },
        {
          term: 'Mentoring',
          pronunciation: '멘토링',
          explanation: '멘토링. 경험 있는 사람이 후배에게 조언하고 성장을 돕는 것입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '갭 인정',
          importance: 'must',
          explanation: '6명→15명은 질적으로 다른 도전임을 인지'
        },
        {
          keyword: '계층화 전략',
          importance: 'must',
          explanation: 'EM/Tech Lead 채용으로 중간 관리 레이어 구축'
        },
        {
          keyword: '스쿼드 구조',
          importance: 'good_to_have',
          explanation: '5-6명 단위로 자율적 팀 분리'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: '갭을 솔직히 인정하고, 중간 관리자 채용 + 팀 구조화 + 외부 멘토링 등 구체적 전략 제시.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '자신감은 있지만 구체적 전략 부족. "잘 할 수 있다" 일반론.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: -5,
          text: '갭을 인정하지 않거나, 15명 관리가 6명과 같다고 주장.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q10-f1',
          trigger: 'Expert',
          question_text: '첫 번째로 채용할 Engineering Manager의 자격 요건과 면접 질문은 무엇이 될까요?',
          why_matters: '팀 빌딩의 구체성과 실행력.',
          listen_for: '구체적 자격 요건, 면접 기준, 문화 적합성.',
          good: {
            text: '기술적 깊이 + 피플 매니지먼트 경험 + 문화 적합성 등 구체적 기준.',
            score: 10
          },
          poor: {
            text: '좋은 사람이면 된다.',
            score: 0
          }
        },
        {
          id: 'q10-f2',
          trigger: 'Mid',
          question_text: '15명을 관리할 때 6명과 가장 크게 달라지는 점은 무엇이라고 생각하시나요?',
          why_matters: '규모 확장의 현실적 도전을 이해하는지.',
          listen_for: '소통 오버헤드, 위임 필요성, 프로세스 변화.',
          good: {
            text: '소통 비용 증가, 1:1 한계, 중간 레이어 필요성 언급.',
            score: 5
          },
          poor: {
            text: '크게 다르지 않다.',
            score: -3
          }
        },
        {
          id: 'q10-f3',
          trigger: 'Low',
          question_text: '6명을 리드할 때 가장 어려웠던 점은 무엇이었고, 어떻게 해결하셨나요?',
          why_matters: '현재 수준에서의 리더십 경험이라도 확인.',
          listen_for: '구체적 어려움과 해결 과정.',
          good: {
            text: '구체적 사례와 학습 포인트 공유.',
            score: 5
          },
          poor: {
            text: '어려운 점이 없었다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "경험의 부족함을 인정하면서도, 극복할 구체적 계획이 있는지"를 확인합니다. 자신감과 현실 인식의 균형이 핵심입니다.',
        daily_analogy: '4인 밴드를 이끌던 사람이 15인 오케스트라를 지휘하는 것과 비슷합니다. 밴드에서는 멤버와 직접 소통하지만, 오케스트라에서는 파트 리더(바이올린, 관악기 등)를 세우고 그들을 통해 운영해야 합니다. 모든 단원에게 직접 지시하려 하면 오히려 혼란스러워집니다.',
        level_expectation: 'CTO 수준에서는 "이 갭이 있다"는 것을 솔직히 인정하면서, "중간 관리자(Engineering Manager)를 채용하고, 5~6명씩 소규모 팀으로 나누고, 외부 멘토링을 받겠다"는 구체적인 극복 전략이 있어야 합니다.'
      },
      expected_answer: {
        core: '• 갭 인정: 6명을 관리하는 것과 15명을 관리하는 것은 완전히 다른 일임을 인정\n• 핵심 전략: 경험 있는 Engineering Manager(팀장급)를 2명 채용하여 중간 관리 계층 구축\n• 팀 구조: 5~6명씩 소규모 자율팀(스쿼드)으로 나누어 각 팀이 독립적으로 결정하고 실행\n• 보완: 경험 있는 외부 CTO 코치에게 월 2회 멘토링 받기',
        example: '솔직히 말씀드리면, 6명과 15명은 다른 차원의 도전입니다. 6명일 때는 모든 사람과 매일 대화할 수 있지만, 15명이면 불가능합니다. 제 전략은 세 가지입니다. 첫째, 입사 첫 달에 경험 있는 Engineering Manager 2명을 채용합니다. 이 분들이 각각 5~6명의 개발자를 직접 관리합니다. 저는 EM들과 주 2회 미팅하고, 기술 방향성과 팀 간 조율에 집중합니다. 둘째, 팀을 기능별 스쿼드로 나눕니다. 결제팀, 사용자팀처럼요. 각 스쿼드가 자기 영역에서 독립적으로 결정하고 배포할 수 있게 합니다. 셋째, 50명 이상 조직을 경험한 CTO 선배에게 월 2회 멘토링을 받을 계획입니다.',
        key_points: ['솔직한 인정', '계층화 전략', '자율 조직']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: [
        '4-6명의 팀을 리드한 경험이 있으신데, 이 역할은 15명 이상의 팀을 관리해야 합니다. 이 점프를 할 수 있다고 확신하시는 이유는 무엇인가요에 대해 설명해 주시실 건가요?',
        '이 주제에 대한 경험이나 생각을 공유해 주세요.'
      ]
    },
    {
      id: 11,
      category: 'role_fit',
      difficulty: 'Easy',
      title: 'CTO vs VP Engineering 역할 구분',
      question_text: 'CTO와 VP of Engineering의 역할 차이를 어떻게 이해하고 계시며, 이 포지션에서 본인이 더 강점을 발휘할 수 있는 영역은 어디라고 생각하시나요?',
      context_bridge: '저희 회사는 아직 VP Engineering이 없어서 CTO가 두 역할을 모두 수행해야 합니다.',
      why_matters: 'CTO 역할에 대한 정확한 이해가 있어야 올바른 우선순위를 잡을 수 있습니다. 기술 비전과 팀 운영을 구분하는지 확인합니다.',
      listen_for: '두 역할의 차이를 명확히 이해하고, 초기 스타트업에서 두 역할을 겸해야 하는 현실을 인식하는지 확인하세요.',
      code_reference: null,
      terminology: [
        {
          term: 'CTO',
          pronunciation: '씨티오',
          explanation: 'Chief Technology Officer. 기술 비전과 전략을 담당하는 최고 기술 책임자입니다.',
          definition: 'Chief Technology Officer. 기술 비전과 전략을 담당하는 최고 기술 책임자입니다.',
          plain_language: 'Chief Technology Officer. 기술 비전과 전략을 담당하는 최고 기술 책임자입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'VP of Engineering',
          pronunciation: '브이피 오브 엔지니어링',
          explanation: '엔지니어링 부사장. 개발팀의 일상 운영, 채용, 프로세스를 관리하는 역할입니다.',
          definition: '엔지니어링 부사장. 개발팀의 일상 운영, 채용, 프로세스를 관리하는 역할입니다.',
          plain_language: '엔지니어링 부사장. 개발팀의 일상 운영, 채용, 프로세스를 관리하는 역할입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Technical Vision',
          pronunciation: '테크니컬 비전',
          explanation: '기술 비전. 회사가 앞으로 어떤 기술 방향으로 나아갈지 그리는 큰 그림입니다.'
        },
        {
          term: 'People Management',
          pronunciation: '피플 매니지먼트',
          explanation: '사람 관리. 채용, 평가, 성장 지원, 갈등 해결 등 팀원과 관련된 모든 업무입니다.'
        },
        {
          term: 'Strategy',
          pronunciation: '스트래터지',
          explanation: '전략. 장기적 목표를 달성하기 위한 계획과 방법론입니다.'
        },
        {
          term: 'Execution',
          pronunciation: '엑서큐션',
          explanation: '실행. 전략을 실제로 행동에 옮기는 것입니다.'
        },
        {
          term: 'Board',
          pronunciation: '보드',
          explanation: '이사회. 회사의 주요 의사결정을 감독하고 승인하는 최고 의결 기관입니다.'
        },
        {
          term: 'Stakeholder',
          pronunciation: '스테이크홀더',
          explanation: '이해관계자. 회사의 결정에 영향을 받거나 영향을 주는 사람들입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '역할 구분 인식',
          importance: 'must',
          explanation: 'CTO는 기술 비전/전략, VPE는 팀 운영/프로세스라는 차이를 알아야 함'
        },
        {
          keyword: '겸임 현실 인식',
          importance: 'must',
          explanation: '초기 스타트업에서 두 역할을 동시에 수행해야 하는 현실 이해'
        },
        {
          keyword: 'VP Engineering 채용 계획',
          importance: 'good_to_have',
          explanation: '팀이 커지면 VPE를 별도로 채용해야 한다는 장기 관점'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 15,
          text: 'CTO는 기술 비전과 외부 소통, VPE는 팀 운영과 프로세스라는 구분을 명확히 하고, 초기에는 겸임하되 팀 규모에 따라 VPE 채용 시점을 제시.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 8,
          text: '역할 차이를 대략 알지만, 초기 스타트업에서 어떻게 겸임할지 구체적 계획이 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '두 역할의 차이를 구분하지 못하거나, CTO가 코딩만 하면 된다고 생각.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q11-f1',
          trigger: 'Expert',
          question_text: 'VP Engineering을 채용한다면 어떤 시점에, 어떤 기준으로 채용하시겠습니까?',
          why_matters: '장기적 조직 설계 능력을 확인합니다.',
          listen_for: '팀 규모 기준, 본인의 시간 배분 문제, 채용 기준.',
          good: {
            text: '15명 이상일 때, 팀 운영에 70% 이상 시간을 쓰게 되면 채용한다는 구체적 기준 제시.',
            score: 8
          },
          poor: {
            text: '필요하면 뽑겠다는 막연한 답변.',
            score: 0
          }
        },
        {
          id: 'q11-f2',
          trigger: 'Mid',
          question_text: '초기에 두 역할을 겸임할 때 가장 먼저 희생되기 쉬운 영역은 무엇이라고 생각하시나요?',
          why_matters: '겸임의 현실적 어려움에 대한 인식.',
          listen_for: '기술 비전이나 팀 케어 중 하나가 소홀해질 수 있다는 자기인식.',
          good: {
            text: '구체적 위험 영역을 인식하고 대비 방안 제시.',
            score: 5
          },
          poor: {
            text: '다 잘 할 수 있다고 답변.',
            score: -2
          }
        },
        {
          id: 'q11-f3',
          trigger: 'Low',
          question_text: 'CTO가 하루에 하는 일을 시간대별로 설명해주실 수 있나요?',
          why_matters: '역할에 대한 기본적 이해를 재확인.',
          listen_for: '코딩 외에 미팅, 전략, 채용 등 다양한 업무 인식.',
          good: {
            text: '다양한 업무를 시간대별로 나눠서 설명.',
            score: 5
          },
          poor: {
            text: '하루 종일 코딩한다고 답변.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "이 사람이 CTO 역할의 범위를 정확히 이해하고 있는가"를 확인합니다. CTO는 단순히 가장 실력 좋은 개발자가 아니라, 기술로 회사의 비즈니스를 성장시키는 사람입니다.',
        daily_analogy: '축구팀에 비유하면, CTO는 감독(전략과 비전)이고 VP Engineering은 코치(선수 훈련과 일상 관리)입니다. 작은 팀에서는 감독이 코치 역할도 하지만, 팀이 커지면 분리해야 합니다.',
        level_expectation: 'CTO 수준에서는 두 역할의 차이를 명확히 알고, 회사 단계에 따라 자신의 역할이 어떻게 변해야 하는지 로드맵을 가지고 있어야 합니다.'
      },
      expected_answer: {
        core: '• CTO: 기술 비전, 아키텍처 방향, 외부 소통(이사회/투자자), 기술 전략\n• VP Engineering: 팀 일상 운영, 채용 프로세스, 개발 프로세스, 성과 관리\n• 초기 스타트업: CTO가 둘 다 겸임하되, 15명 이상이면 VPE 별도 채용 필요',
        example: 'CTO와 VP Engineering은 다른 역할입니다. CTO는 "우리가 어떤 기술을 써야 하는가"를 결정하고, 이사회와 투자자에게 기술 전략을 설명합니다. VP Engineering은 "개발팀이 효율적으로 일하도록" 프로세스를 만들고 사람을 관리합니다. 지금 8명 규모에서는 제가 둘 다 해야 합니다. 하지만 15명이 넘으면 팀 운영에만 하루 6시간이 필요해져서, 기술 비전을 생각할 시간이 없어집니다. 그 시점에 VP Engineering을 채용하고, 저는 기술 전략과 외부 소통에 집중할 계획입니다.',
        key_points: ['역할 구분', '겸임 현실', 'VPE 채용 시점']
      },
      jd_competency_link: 'JD 요구사항: "기술 전략 수립 및 팀 빌딩" → CTO로서의 리더십과 비전 검증',
      generation_rationale: '후보자의 이력서에 "Engineering Lead" 경험이 있어 CTO 역할 적합성을 검증',
      skills_assessed: ['leadership', 'strategy'],
      alternative_phrasings: [
        'CTO와 VP of Engineering의 역할 차이를 어떻게 이해하고 계시며, 이 포지션에서 본인이 더 강점을 발휘할 수 있는 영역은 어디라고 생각하시나요에 대해 설명해 주시실 건가요?',
        '이 주제에 대한 경험이나 생각을 공유해 주세요.'
      ]
    },
    {
      id: 12,
      category: 'role_fit',
      difficulty: 'Medium',
      title: '이사회/투자자 커뮤니케이션',
      question_text: 'Series A 투자를 받은 후, 이사회에 기술 전략을 분기별로 보고해야 합니다. 첫 번째 보고에서 어떤 내용을 어떤 형식으로 발표하시겠습니까?',
      context_bridge: '저희는 최근 Series A를 마감했고, 투자자들이 기술 로드맵에 대해 궁금해합니다.',
      why_matters: 'CTO는 기술팀의 대변인으로 비기술적 이해관계자와 효과적으로 소통해야 합니다. 이사회 보고 경험이나 준비도를 확인합니다.',
      listen_for: '비즈니스 언어로 기술을 번역하는 능력, 데이터 기반 보고, 투자자 관점의 핵심 메트릭.',
      code_reference: null,
      terminology: [
        {
          term: 'Series A',
          pronunciation: '시리즈 에이',
          explanation: '스타트업의 첫 번째 대규모 투자 라운드. 보통 수십억 원 규모로, 제품과 팀을 본격적으로 키우는 단계입니다.',
          definition: '스타트업의 첫 번째 대규모 투자 라운드. 보통 수십억 원 규모로, 제품과 팀을 본격적으로 키우는 단계입니다.',
          plain_language: '스타트업의 첫 번째 대규모 투자 라운드. 보통 수십억 원 규모로, 제품과 팀을 본격적으로 키우는 단계입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Board Meeting',
          pronunciation: '보드 미팅',
          explanation: '이사회 회의. 투자자와 경영진이 모여 회사의 주요 성과와 방향을 논의합니다.',
          definition: '이사회 회의. 투자자와 경영진이 모여 회사의 주요 성과와 방향을 논의합니다.',
          plain_language: '이사회 회의. 투자자와 경영진이 모여 회사의 주요 성과와 방향을 논의합니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'KPI',
          pronunciation: '케이피아이',
          explanation: 'Key Performance Indicator. 핵심 성과 지표. 목표 달성 여부를 측정하는 숫자입니다.'
        },
        {
          term: 'Runway',
          pronunciation: '런웨이',
          explanation: '활주로. 현재 자금으로 회사가 운영할 수 있는 기간입니다. "런웨이 18개월"이면 18개월 버틸 수 있다는 뜻입니다.'
        },
        {
          term: 'Burn Rate',
          pronunciation: '번 레이트',
          explanation: '자금 소진 속도. 매달 쓰는 비용입니다. 이것이 높으면 런웨이가 짧아집니다.'
        },
        {
          term: 'ROI',
          pronunciation: '알오아이',
          explanation: 'Return on Investment. 투자 대비 수익률. 투자한 만큼 이익이 나오는지 측정합니다.'
        },
        {
          term: 'Technical Roadmap',
          pronunciation: '테크니컬 로드맵',
          explanation: '기술 로드맵. 앞으로 6~12개월간 어떤 기술 과제를 어떤 순서로 수행할지 그린 계획표입니다.'
        },
        {
          term: 'Milestone',
          pronunciation: '마일스톤',
          explanation: '이정표. 프로젝트의 주요 달성 목표. 여기까지 완료되면 다음 단계로 넘어갑니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '비즈니스 임팩트 중심',
          importance: 'must',
          explanation: '기술 지표가 아니라 매출, 고객, 비용 절감 등 비즈니스 언어로 보고해야 함'
        },
        {
          keyword: '마일스톤 기반 로드맵',
          importance: 'must',
          explanation: '구체적 달성 목표와 일정을 제시해야 투자자가 진행 상황을 판단 가능'
        },
        {
          keyword: '리스크 투명 공유',
          importance: 'good_to_have',
          explanation: '좋은 소식만이 아니라 위험 요소도 솔직히 공유하는 것이 신뢰 구축'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: '비즈니스 KPI 중심 보고 구조 제시. 기술 투자의 ROI를 숫자로 환산하고 리스크도 투명하게 포함.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '보고해야 한다는 것은 아는데 구체적 포맷이나 비즈니스 언어 번역이 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '이사회 보고 경험이 없고 준비 방법도 모름. 기술 용어로만 나열.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q12-f1',
          trigger: 'Expert',
          question_text: '투자자가 "경쟁사 대비 기술적 우위가 무엇인가"라고 물으면 어떻게 답하시겠습니까?',
          why_matters: '기술을 경쟁 우위로 프레이밍하는 능력.',
          listen_for: '경쟁사 분석, 차별화 포인트, 방어 가능한 기술 자산.',
          good: {
            text: '구체적 기술 차별점을 비즈니스 가치로 연결하여 설명.',
            score: 8
          },
          poor: {
            text: '우리 기술이 더 좋다는 일반적 답변.',
            score: 0
          }
        },
        {
          id: 'q12-f2',
          trigger: 'Mid',
          question_text: '기술 로드맵을 슬라이드 3장으로 요약해야 한다면 어떤 내용을 넣으시겠습니까?',
          why_matters: '핵심 정보를 압축하는 능력.',
          listen_for: '현재 상태, 목표, 실행 계획의 3단계 구조.',
          good: {
            text: '현황-목표-실행을 각 1장씩 간결하게 구성.',
            score: 5
          },
          poor: {
            text: '기술 아키텍처 다이어그램으로 채우겠다고 답변.',
            score: -2
          }
        },
        {
          id: 'q12-f3',
          trigger: 'Low',
          question_text: '투자자가 가장 알고 싶어하는 것은 무엇이라고 생각하시나요?',
          why_matters: '투자자 관점에 대한 기본 이해.',
          listen_for: '돈(ROI), 성장 속도, 리스크 관리.',
          good: {
            text: '투자 대비 수익과 성장 가능성이라고 답변.',
            score: 5
          },
          poor: {
            text: '기술의 우수성이라고 답변.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "이 사람이 투자자와 효과적으로 소통할 수 있는가"를 확인합니다. 투자자는 기술 자체가 아니라 기술이 비즈니스에 주는 가치를 알고 싶어합니다.',
        daily_analogy: '병원 원장이 이사회에 보고할 때 "MRI 3T 장비의 gradient coil이..."라고 하면 안 되고, "새 장비로 진단 정확도가 20% 올라서 환자 재방문율이 줄었습니다"라고 해야 하는 것과 같습니다.',
        level_expectation: 'CTO 수준에서는 기술 투자를 비즈니스 수치로 환산하고, 투자자가 관심 있는 포맷(KPI, 마일스톤, 리스크)으로 보고할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 보고 구조: ①지난 분기 성과(KPI 기반) ②다음 분기 계획(마일스톤) ③리스크와 대응 방안\n• 핵심 원칙: 모든 기술 지표를 비즈니스 언어로 번역\n• 형식: 슬라이드 10장 이내, 숫자와 차트 중심',
        example: '첫 이사회 보고는 3파트로 구성합니다. 파트1: "현재 상태" — 배포 빈도가 주 1회에서 주 3회로 개선되어 고객 요청 반영 속도가 3배 빨라졌습니다. 파트2: "다음 분기 목표" — SOC2 인증 준비 착수, 시니어 개발자 2명 채용, 핵심 결제 모듈 안정화. 각 목표에 완료 기준과 날짜를 명시합니다. 파트3: "리스크" — Kubernetes 운영 경험이 팀에 부족하여 외부 컨설팅을 병행할 계획입니다. 비용은 월 500만원이지만 장애 리스크를 80% 줄일 수 있습니다. 이렇게 모든 기술 이야기를 비용, 시간, 고객 영향으로 번역합니다.',
        key_points: ['비즈니스 언어', '구조화된 보고', '리스크 투명성']
      },
      jd_competency_link: 'JD 요구사항: "기술 전략 수립 및 팀 빌딩" → CTO로서의 리더십과 비전 검증',
      generation_rationale: '후보자의 이력서에 "Engineering Lead" 경험이 있어 CTO 역할 적합성을 검증',
      skills_assessed: ['leadership', 'strategy'],
      alternative_phrasings: [
        'Series A 투자를 받은 후, 이사회에 기술 전략을 분기별로 보고해야 합니다. 첫 번째 보고에서 어떤 내용을 어떤 형식으로 발표하시겠습니까에 대해 설명해 주시실 건가요?',
        '이 주제에 대한 경험이나 생각을 공유해 주세요.'
      ]
    },
    {
      id: 13,
      category: 'role_fit',
      difficulty: 'Hard',
      title: '엔지니어링 문화 구축',
      question_text: '빠르게 성장하는 스타트업에서 엔지니어링 문화를 처음부터 만들어야 한다면, 어떤 원칙을 세우고 어떻게 정착시키시겠습니까?',
      context_bridge: '저희는 8명에서 15명으로 팀을 키울 예정인데, 지금 문화를 잘 세워야 나중에 흔들리지 않습니다.',
      why_matters: '팀이 빠르게 커질 때 문화가 없으면 혼란이 옵니다. 문화를 의도적으로 설계하고 실행할 수 있는지 확인합니다.',
      listen_for: '추상적 가치가 아닌 구체적 행동과 제도로 문화를 정착시키는 방법론.',
      code_reference: null,
      terminology: [
        {
          term: 'Engineering Culture',
          pronunciation: '엔지니어링 컬처',
          explanation: '엔지니어링 문화. 개발팀이 공유하는 일하는 방식, 가치관, 행동 규범입니다.',
          definition: '엔지니어링 문화. 개발팀이 공유하는 일하는 방식, 가치관, 행동 규범입니다.',
          plain_language: '엔지니어링 문화. 개발팀이 공유하는 일하는 방식, 가치관, 행동 규범입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Postmortem',
          pronunciation: '포스트모템',
          explanation: '사후 분석. 장애나 실패 후 원인을 분석하고 재발 방지책을 만드는 회의입니다. 비난이 아닌 학습이 목적입니다.',
          definition: '사후 분석. 장애나 실패 후 원인을 분석하고 재발 방지책을 만드는 회의입니다. 비난이 아닌 학습이 목적입니다.',
          plain_language: '사후 분석. 장애나 실패 후 원인을 분석하고 재발 방지책을 만드는 회의입니다. 비난이 아닌 학습이 목적입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Blameless Culture',
          pronunciation: '블레이밀리스 컬처',
          explanation: '비난 없는 문화. 실수한 사람을 탓하지 않고, 시스템과 프로세스를 개선하는 데 집중하는 문화입니다.'
        },
        {
          term: 'Code Review',
          pronunciation: '코드 리뷰',
          explanation: '동료가 작성한 코드를 검토하고 피드백하는 과정. 품질과 학습을 동시에 달성합니다.'
        },
        {
          term: 'On-call',
          pronunciation: '온콜',
          explanation: '장애 발생 시 즉시 대응하는 당번 제도. 교대로 담당합니다.'
        },
        {
          term: 'Tech Talk',
          pronunciation: '테크 톡',
          explanation: '팀 내 기술 발표. 새로 배운 기술이나 경험을 공유하는 시간입니다.'
        },
        {
          term: 'Onboarding',
          pronunciation: '온보딩',
          explanation: '새 팀원이 빠르게 적응할 수 있도록 돕는 입사 초기 프로그램입니다.'
        },
        {
          term: 'Retrospective',
          pronunciation: '레트로스펙티브',
          explanation: '회고. 일정 기간의 작업을 돌아보며 잘한 점과 개선할 점을 논의하는 미팅입니다.'
        },
        {
          term: 'Documentation',
          pronunciation: '도큐멘테이션',
          explanation: '문서화. 코드, 설계, 프로세스 등을 글로 기록하여 누구나 이해할 수 있게 하는 것입니다.'
        },
        {
          term: 'Psychological Safety',
          pronunciation: '사이콜로지컬 세이프티',
          explanation: '심리적 안전감. 팀에서 실수해도 비난받지 않고 자유롭게 의견을 말할 수 있는 환경입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '구체적 행동/제도',
          importance: 'must',
          explanation: '추상적 가치가 아닌 실제 실행할 수 있는 제도와 행동이 있어야 함'
        },
        {
          keyword: '비난 없는 문화(Blameless)',
          importance: 'must',
          explanation: '실수를 학습 기회로 삼는 문화가 빠른 성장의 전제 조건'
        },
        {
          keyword: '문서화/온보딩',
          importance: 'good_to_have',
          explanation: '팀이 커질 때 문화를 전파하는 핵심 수단'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 25,
          text: '3~5가지 핵심 원칙을 제시하고, 각각을 정착시킬 구체적 제도(포스트모템, 코드 리뷰 규칙, 온보딩 등)를 설명. 측정 방법도 포함.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 12,
          text: '좋은 문화가 중요하다고 하지만, 구체적 방법론 부족. 선언적 가치만 나열.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '문화는 자연스럽게 만들어진다거나, 중요하지 않다고 답변.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q13-f1',
          trigger: 'Expert',
          question_text: '새로 입사한 시니어 개발자가 기존 문화에 동의하지 않고 다른 방식을 주장한다면 어떻게 하시겠습니까?',
          why_matters: '문화 갈등 관리 능력을 확인.',
          listen_for: '경청과 유연성, 핵심 원칙의 비타협적 영역 구분.',
          good: {
            text: '의견을 듣되 핵심 원칙은 지키고, 개선 가능한 부분은 수용하는 균형.',
            score: 10
          },
          poor: {
            text: '내가 정한 문화니까 따라야 한다.',
            score: 0
          }
        },
        {
          id: 'q13-f2',
          trigger: 'Mid',
          question_text: '문화 원칙을 3가지만 골라야 한다면 무엇을 선택하시겠습니까?',
          why_matters: '우선순위 설정 능력을 확인.',
          listen_for: '구체적이고 실행 가능한 원칙.',
          good: {
            text: '투명성, 오너십, 지속적 학습 등 구체적 3가지와 실행 방법.',
            score: 5
          },
          poor: {
            text: '열정, 최고, 혁신 같은 추상적 키워드만 나열.',
            score: -2
          }
        },
        {
          id: 'q13-f3',
          trigger: 'Low',
          question_text: '좋은 개발팀의 특징은 무엇이라고 생각하시나요?',
          why_matters: '문화에 대한 기본적 인식을 확인.',
          listen_for: '협업, 소통, 학습 등 기본적 가치.',
          good: {
            text: '협업과 소통의 중요성을 인식.',
            score: 5
          },
          poor: {
            text: '실력 있는 사람만 모으면 된다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 "이 사람이 단순히 코드를 짜는 팀이 아니라, 함께 성장하는 조직을 만들 수 있는가"를 확인합니다. 빠르게 커지는 팀에서 문화가 없으면 각자 다른 방향으로 일하게 됩니다.',
        daily_analogy: '새 학교를 세우는 것과 비슷합니다. 교칙을 "착하게 지내라"라고만 하면 아무도 따르지 않습니다. "매주 금요일 발표 시간에 한 가지 배운 것을 공유한다", "실수하면 벌 대신 원인 분석을 함께 한다" 같은 구체적 제도가 있어야 문화가 됩니다.',
        level_expectation: 'CTO 수준에서는 문화를 "선언"이 아닌 "제도"로 만들 수 있어야 합니다. 포스트모템, 코드 리뷰 정책, 온보딩 프로그램 등 구체적 실행 방안이 있어야 합니다.'
      },
      expected_answer: {
        core: '• 핵심 원칙 3~5가지: 비난 없는 문화, 오너십, 투명한 소통, 지속적 학습, 문서화 우선\n• 정착 방법: 각 원칙에 대응하는 구체적 제도 운영\n• 측정: 팀 설문, 이직률, 온보딩 시간 등으로 문화 건강도 추적',
        example: '저는 5가지 핵심 원칙을 세우겠습니다. 첫째, "비난 없는 포스트모템" — 장애가 나면 24시간 내에 원인 분석 회의를 하되, "누가 실수했는가"가 아니라 "어떤 시스템이 이 실수를 막지 못했는가"를 논의합니다. 둘째, "코드 리뷰 24시간 규칙" — PR이 올라오면 24시간 내에 리뷰합니다. 셋째, "문서화 우선" — 코드를 작성하기 전에 설계 문서를 먼저 씁니다. 넷째, "월 1회 테크 톡" — 팀원이 돌아가며 배운 것을 발표합니다. 다섯째, "온보딩 버디 제도" — 신입에게 2주간 전담 멘토를 붙여줍니다. 이전 회사에서 이 방식으로 온보딩 시간을 4주에서 2주로 단축했습니다.',
        key_points: ['구체적 제도', '비난 없는 문화', '측정 가능']
      },
      jd_competency_link: 'JD 요구사항: "기술 전략 수립 및 팀 빌딩" → CTO로서의 리더십과 비전 검증',
      generation_rationale: '후보자의 이력서에 "Engineering Lead" 경험이 있어 CTO 역할 적합성을 검증',
      skills_assessed: ['leadership', 'strategy'],
      alternative_phrasings: ['빠르게 성장하는 스타트업에서 엔지니어링 문화를 처음부터 만들어야 한다면, 어떤 원칙을 세우고 어떻게 정착시키시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 14,
      category: 'technical_depth',
      difficulty: 'Easy',
      title: '보안 컴플라이언스 (SOC2) 이해',
      question_text: 'SOC2 인증이 무엇이며, 핀테크 스타트업에서 이 인증을 획득하기 위해 CTO로서 어떤 준비를 하시겠습니까?',
      context_bridge: '저희는 B2B 고객 확대를 위해 SOC2 인증이 필요한 상황입니다.',
      why_matters: '핀테크에서 보안 인증은 사업 확장의 전제 조건입니다.',
      listen_for: 'SOC2의 기본 이해, 실행 계획의 구체성, 외부 도움을 받을 줄 아는 겸손함.',
      code_reference: null,
      terminology: [
        {
          term: 'SOC2',
          pronunciation: '삭투',
          explanation: '고객 데이터를 안전하게 관리하고 있음을 증명하는 국제 인증입니다.',
          definition: '고객 데이터를 안전하게 관리하고 있음을 증명하는 국제 인증입니다.',
          plain_language: '고객 데이터를 안전하게 관리하고 있음을 증명하는 국제 인증입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Compliance',
          pronunciation: '컴플라이언스',
          explanation: '법규 준수. 법률이나 규정을 지키고 있음을 증명하는 것입니다.',
          definition: '법규 준수. 법률이나 규정을 지키고 있음을 증명하는 것입니다.',
          plain_language: '법규 준수. 법률이나 규정을 지키고 있음을 증명하는 것입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Trust Service Criteria',
          pronunciation: '트러스트 서비스 크라이테리아',
          explanation: 'SOC2의 5가지 평가 기준: 보안, 가용성, 처리 무결성, 기밀성, 프라이버시입니다.'
        },
        {
          term: 'Encryption',
          pronunciation: '인크립션',
          explanation: '암호화. 데이터를 읽을 수 없는 형태로 변환하여 보호하는 기술입니다.'
        },
        {
          term: 'Access Control',
          pronunciation: '액세스 컨트롤',
          explanation: '접근 제어. 허가된 사람만 특정 시스템에 접근할 수 있게 하는 것입니다.'
        },
        {
          term: 'Audit Log',
          pronunciation: '오딧 로그',
          explanation: '감사 기록. 누가 언제 무엇을 했는지 자동으로 기록하는 시스템입니다.'
        },
        {
          term: 'Penetration Test',
          pronunciation: '페네트레이션 테스트',
          explanation: '모의 해킹. 전문가가 시스템을 공격해서 취약점을 찾는 테스트입니다.'
        },
        {
          term: 'RBAC',
          pronunciation: '알백',
          explanation: '역할 기반 접근 제어. 직급이나 역할에 따라 접근 권한을 다르게 설정합니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: 'SOC2 기본 이해',
          importance: 'must',
          explanation: '5가지 원칙과 인증 프로세스에 대한 기본 지식'
        },
        {
          keyword: '단계별 실행 계획',
          importance: 'must',
          explanation: '우선순위를 잡는 접근'
        },
        {
          keyword: '외부 전문가 활용',
          importance: 'good_to_have',
          explanation: '처음이면 컨설턴트의 도움을 받는 것이 현실적'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 15,
          text: 'SOC2 Type I/II 차이를 알고, 6~12개월 로드맵과 함께 구체적 기술 과제를 제시.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 8,
          text: 'SOC2가 보안 인증이라는 것은 알지만, 구체적 준비 사항이 모호.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: 'SOC2가 무엇인지 모르거나, 보안팀이 알아서 할 일이라고 답변.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q14-f1',
          trigger: 'Expert',
          question_text: 'SOC2 준비 과정에서 개발 속도가 느려질 수 있는데, 이 트레이드오프를 팀에게 어떻게 설명하시겠습니까?',
          why_matters: '보안과 속도의 균형 감각.',
          listen_for: '비즈니스 필요성으로 설득, 자동화로 부담 최소화.',
          good: {
            text: 'B2B 매출 확대라는 비즈니스 가치를 설명하고, 보안 체크를 CI/CD에 자동화.',
            score: 8
          },
          poor: {
            text: '규정이니까 따라야 한다고만 답변.',
            score: 0
          }
        },
        {
          id: 'q14-f2',
          trigger: 'Mid',
          question_text: 'SOC2 인증을 받으려면 기술적으로 가장 먼저 해야 할 일은 무엇일까요?',
          why_matters: '실행 우선순위를 잡는 능력.',
          listen_for: 'gap analysis부터 시작해야 한다는 인식.',
          good: {
            text: '현재 보안 상태 점검(gap analysis)부터 시작한다고 답변.',
            score: 5
          },
          poor: {
            text: '잘 모르겠다, 조사해봐야 한다.',
            score: 0
          }
        },
        {
          id: 'q14-f3',
          trigger: 'Low',
          question_text: '고객의 개인정보를 보호하기 위해 가장 기본적으로 해야 할 일은 무엇일까요?',
          why_matters: '보안에 대한 기본적 인식 확인.',
          listen_for: '암호화, 접근 제어 등 기본 개념.',
          good: {
            text: '데이터 암호화와 접근 제어를 언급.',
            score: 5
          },
          poor: {
            text: '특별한 방법을 모르겠다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 보안 인증이 비즈니스에 왜 중요한지 이해하고 기술적으로 준비할 수 있는가를 확인합니다.',
        daily_analogy: '식당의 위생 인증과 비슷합니다. 음식이 맛있어도 위생 인증이 없으면 대형 납품이 불가능합니다.',
        level_expectation: 'CTO 수준에서는 SOC2의 기본 개념을 알고 획득 로드맵을 제시할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• SOC2: 고객 데이터 보호를 증명하는 국제 인증. Type I(설계)과 Type II(운영)\n• 핵심 준비: 접근 제어(RBAC), 데이터 암호화, 감사 로그, 모의 해킹\n• 로드맵: 1~3개월 gap analysis → 4~6개월 구축 → 7~9개월 Type I → 12개월 Type II',
        example: 'SOC2는 고객 데이터를 안전하게 관리하고 있음을 제3자가 인증해주는 것입니다. 저는 직접 SOC2를 획득해본 경험은 없지만, 로드맵을 세울 수 있습니다. 첫 3개월은 외부 컨설턴트와 gap analysis를 수행합니다. 그 다음 3개월간 RBAC, 암호화, 감사 로그 자동화를 진행합니다. 동시에 보안 체크를 배포 파이프라인에 자동화하여 개발 속도 저하를 최소화합니다.',
        key_points: ['기본 이해', '실행 로드맵', '외부 전문가 활용']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['SOC2 인증이 무엇이며, 핀테크 스타트업에서 이 인증을 획득하기 위해 CTO로서 어떤 준비를 하시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 15,
      category: 'technical_depth',
      difficulty: 'Medium',
      title: '핀테크 데이터 아키텍처',
      question_text: '핀테크 서비스의 데이터 아키텍처를 설계할 때 일반 서비스와 다르게 고려해야 할 핵심 요소는 무엇이며, 어떻게 설계하시겠습니까?',
      context_bridge: '저희는 결제와 송금 데이터를 다루는데, 데이터 정합성과 규제 준수가 매우 중요합니다.',
      why_matters: '핀테크는 데이터의 정확성과 추적 가능성이 특히 중요합니다.',
      listen_for: 'ACID 트랜잭션, 감사 추적, 데이터 보존 규정, 암호화 등.',
      code_reference: null,
      terminology: [
        {
          term: 'ACID',
          pronunciation: '에이시드',
          explanation: '데이터가 정확하고 안전하게 처리됨을 보장하는 4가지 원칙입니다.',
          definition: '데이터가 정확하고 안전하게 처리됨을 보장하는 4가지 원칙입니다.',
          plain_language: '데이터가 정확하고 안전하게 처리됨을 보장하는 4가지 원칙입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Audit Trail',
          pronunciation: '오딧 트레일',
          explanation: '감사 추적. 모든 데이터 변경 이력을 기록하는 것입니다.',
          definition: '감사 추적. 모든 데이터 변경 이력을 기록하는 것입니다.',
          plain_language: '감사 추적. 모든 데이터 변경 이력을 기록하는 것입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'PCI DSS',
          pronunciation: '피씨아이 디에스에스',
          explanation: '카드 결제 데이터를 안전하게 다루기 위한 보안 표준입니다.'
        },
        {
          term: 'Data Retention',
          pronunciation: '데이터 리텐션',
          explanation: '법적으로 일정 기간 데이터를 보관해야 하는 규정입니다.'
        },
        {
          term: 'Eventual Consistency',
          pronunciation: '이벤추얼 컨시스턴시',
          explanation: '데이터가 즉시 동기화되지 않지만 결국에는 같아지는 방식입니다.'
        },
        {
          term: 'Idempotency',
          pronunciation: '아이뎀포턴시',
          explanation: '멱등성. 같은 요청을 여러 번 보내도 결과가 한 번과 같은 성질입니다.'
        },
        {
          term: 'Sharding',
          pronunciation: '샤딩',
          explanation: '데이터를 여러 데이터베이스에 나눠서 저장하는 것입니다.'
        },
        {
          term: 'Backup',
          pronunciation: '백업',
          explanation: '데이터를 복사해서 별도로 보관하는 것입니다.'
        },
        {
          term: 'Masking',
          pronunciation: '마스킹',
          explanation: '카드번호를 ****-1234처럼 일부만 보여주는 것입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: 'ACID 트랜잭션',
          importance: 'must',
          explanation: '금융 데이터는 절대 부정확해서는 안 됨'
        },
        {
          keyword: '감사 추적 (Audit Trail)',
          importance: 'must',
          explanation: '모든 금융 거래는 추적 가능해야 함'
        },
        {
          keyword: '멱등성 (Idempotency)',
          importance: 'good_to_have',
          explanation: '중복 결제를 방지하는 핵심 패턴'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: 'ACID, 감사 추적, 멱등성, 데이터 보존 정책, 암호화를 포함한 체계적 설계 제시.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '데이터 정확성은 중요하다고 하지만 핀테크 특화 요구사항 언급 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '일반 서비스와 차이를 구분하지 못함.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q15-f1',
          trigger: 'Expert',
          question_text: '사용자가 실수로 같은 송금을 두 번 요청하면 어떻게 방지하시겠습니까?',
          why_matters: '멱등성 구현에 대한 구체적 이해.',
          listen_for: 'idempotency key, 중복 체크.',
          good: {
            text: '요청별 고유 키(idempotency key)를 발급하여 중복 처리를 서버에서 차단.',
            score: 8
          },
          poor: {
            text: '프론트엔드에서 버튼을 비활성화하면 된다.',
            score: 0
          }
        },
        {
          id: 'q15-f2',
          trigger: 'Mid',
          question_text: '결제 데이터와 일반 사용자 데이터를 같은 데이터베이스에 저장해도 될까요?',
          why_matters: '데이터 분리와 보안 수준 차등 인식.',
          listen_for: '민감 데이터 분리, 접근 제어.',
          good: {
            text: '결제 데이터는 별도 저장소에 격리하고 접근 권한을 제한.',
            score: 5
          },
          poor: {
            text: '같이 저장해도 괜찮다.',
            score: -2
          }
        },
        {
          id: 'q15-f3',
          trigger: 'Low',
          question_text: '데이터베이스에서 데이터가 정확하다는 것을 어떻게 보장할 수 있을까요?',
          why_matters: '기본적인 데이터 무결성 개념.',
          listen_for: '트랜잭션, 유효성 검사.',
          good: {
            text: '트랜잭션과 데이터 검증 규칙을 언급.',
            score: 5
          },
          poor: {
            text: '구체적 방법을 모르겠다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '금융 데이터를 다루는 특수성을 이해하고 있는가를 확인합니다. 1원이라도 틀리면 법적 문제입니다.',
        daily_analogy: '일반 가계부와 은행 장부의 차이입니다. 은행 장부는 1원 단위까지 정확해야 하고 감사관이 확인할 수 있어야 합니다.',
        level_expectation: 'CTO 수준에서는 핀테크 데이터의 특수성을 이해하고 구현 방법을 설명할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 정확성: ACID 트랜잭션으로 금융 데이터의 무결성 보장\n• 추적성: 모든 거래에 감사 추적 필수\n• 중복 방지: 멱등성 키로 중복 결제/송금 방지\n• 규제: 데이터 보존 기간 준수, PCI DSS 호환 설계',
        example: '핀테크 데이터 아키텍처는 세 가지가 일반 서비스와 다릅니다. 첫째, 모든 금융 트랜잭션은 ACID를 보장해야 합니다. 둘째, 감사 추적이 필수입니다. 모든 변경에 누가 언제 무엇을 왜 변경했는지 기록합니다. 셋째, 멱등성 설계가 필수입니다. 각 요청에 고유 키를 부여하여 중복 처리를 방지합니다.',
        key_points: ['ACID 트랜잭션', '감사 추적', '멱등성']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['핀테크 서비스의 데이터 아키텍처를 설계할 때 일반 서비스와 다르게 고려해야 할 핵심 요소는 무엇이며, 어떻게 설계하시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 16,
      category: 'technical_depth',
      difficulty: 'Hard',
      title: 'Build vs Buy 의사결정',
      question_text: '핵심 기술 컴포넌트를 직접 만들 것인지(Build) 외부 서비스를 구매할 것인지(Buy) 결정하는 프레임워크가 있으신가요?',
      context_bridge: '저희는 결제 게이트웨이, 인증 시스템, 모니터링 등 여러 기술 컴포넌트를 선택해야 합니다.',
      why_matters: '모든 것을 직접 만들면 시간이 부족하고, 모든 것을 사면 차별화가 없습니다.',
      listen_for: '핵심 경쟁력 vs 범용 기능 구분, TCO 분석, 팀 역량 고려.',
      code_reference: null,
      terminology: [
        {
          term: 'Build vs Buy',
          pronunciation: '빌드 버서스 바이',
          explanation: '자체 개발할지 외부 제품을 사용할지 결정하는 것입니다.',
          definition: '자체 개발할지 외부 제품을 사용할지 결정하는 것입니다.',
          plain_language: '자체 개발할지 외부 제품을 사용할지 결정하는 것입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'TCO',
          pronunciation: '티씨오',
          explanation: '총 소유 비용. 구매 비용뿐 아니라 유지보수, 인력 등 전체 비용입니다.',
          definition: '총 소유 비용. 구매 비용뿐 아니라 유지보수, 인력 등 전체 비용입니다.',
          plain_language: '총 소유 비용. 구매 비용뿐 아니라 유지보수, 인력 등 전체 비용입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Core Competency',
          pronunciation: '코어 컴피턴시',
          explanation: '핵심 역량. 우리 회사만의 차별화된 경쟁력입니다.'
        },
        {
          term: 'Vendor Lock-in',
          pronunciation: '벤더 록인',
          explanation: '특정 외부 서비스에 종속되어 바꾸기 어려운 상태입니다.'
        },
        {
          term: 'SaaS',
          pronunciation: '싸스',
          explanation: '소프트웨어를 인터넷으로 빌려 쓰는 서비스입니다.'
        },
        {
          term: 'API Integration',
          pronunciation: '에이피아이 인티그레이션',
          explanation: '외부 서비스를 우리 시스템에 연결하는 것입니다.'
        },
        {
          term: 'Maintenance Cost',
          pronunciation: '메인터넌스 코스트',
          explanation: '유지보수 비용. 시스템을 운영하는 데 지속적으로 드는 비용입니다.'
        },
        {
          term: 'Open Source',
          pronunciation: '오픈소스',
          explanation: '소스 코드가 공개된 소프트웨어. 무료이지만 직접 운영해야 합니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '핵심 역량 vs 범용 기능 구분',
          importance: 'must',
          explanation: '차별화에 필요한 것만 직접 만들고 나머지는 구매'
        },
        {
          keyword: 'TCO 분석',
          importance: 'must',
          explanation: '장기적 총 비용으로 판단'
        },
        {
          keyword: '벤더 록인 리스크',
          importance: 'good_to_have',
          explanation: '외부 서비스 의존의 위험성 인식'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 25,
          text: '핵심 경쟁력 구분 + TCO 분석 + 벤더 록인 리스크까지 포함한 체계적 프레임워크. 구체적 사례 포함.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 12,
          text: '한쪽으로 치우친 답변. 상황별 판단 기준 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '판단 기준 없이 그때그때 다르다는 답변.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q16-f1',
          trigger: 'Expert',
          question_text: '인증 시스템을 Auth0 같은 외부 서비스를 쓸지, 직접 만들지 어떻게 판단하시겠습니까?',
          why_matters: '구체적 사례에 프레임워크를 적용하는 능력.',
          listen_for: '핀테크 인증 특수성, 비용 비교.',
          good: {
            text: '초기에는 외부 서비스로 빠르게 시작하되 추상화 계층으로 록인 방지.',
            score: 10
          },
          poor: {
            text: '단정적으로 하나만 고집.',
            score: 0
          }
        },
        {
          id: 'q16-f2',
          trigger: 'Mid',
          question_text: '직접 만든 시스템의 유지보수 비용을 어떻게 산정하시나요?',
          why_matters: 'TCO에 대한 현실적 이해.',
          listen_for: '인력 비용, 버그 수정, 기회비용.',
          good: {
            text: '개발자 시간 + 운영 비용 + 기회비용을 포함하여 산정.',
            score: 5
          },
          poor: {
            text: '개발비만 계산.',
            score: -2
          }
        },
        {
          id: 'q16-f3',
          trigger: 'Low',
          question_text: '외부 서비스를 사용할 때 가장 큰 위험은 무엇이라고 생각하시나요?',
          why_matters: '외부 의존성의 기본적 위험 인식.',
          listen_for: '서비스 중단, 가격 인상.',
          good: {
            text: '서비스 종료나 가격 인상 위험을 언급.',
            score: 5
          },
          poor: {
            text: '위험이 없다고 답변.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '한정된 자원으로 무엇을 직접 만들고 무엇을 구매할지 전략적으로 판단할 수 있는가를 확인합니다.',
        daily_analogy: '식당을 열 때, 특제 소스는 직접 만들지만 식기와 테이블은 사는 것과 같습니다.',
        level_expectation: 'CTO 수준에서는 핵심 경쟁력 질문으로 Build와 Buy를 구분하고 TCO를 비교할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 핵심 경쟁력이면 Build, 범용 기능이면 Buy\n• TCO(3년 총 비용) 비교\n• 외부 서비스 사용 시 추상화 계층으로 벤더 록인 방지',
        example: '제 프레임워크는 3단계입니다. 첫째, 이것이 우리만의 차별점인가를 묻습니다. 리스크 분석 엔진은 직접 만들고, 이메일 발송은 SendGrid를 씁니다. 둘째, TCO를 비교합니다. 이전 회사에서 모니터링을 직접 만들었는데 3년간 개발자 1명이 50% 시간을 유지보수에 썼습니다. Datadog 구독료가 그 인건비의 1/3이었습니다. 셋째, 벤더 록인을 방지합니다. 외부 서비스 사용 시 추상화 계층을 두어 교체 가능하게 설계합니다.',
        key_points: ['핵심 경쟁력 구분', 'TCO 비교', '벤더 록인 방지']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['핵심 기술 컴포넌트를 직접 만들 것인지(Build) 외부 서비스를 구매할 것인지(Buy) 결정하는 프레임워크가 있으신가요에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 17,
      category: 'execution_ownership',
      difficulty: 'Easy',
      title: '제품 로드맵 우선순위',
      question_text: '기술 부채 해결, 새 기능 개발, 인프라 개선이 동시에 필요한 상황에서 제품 로드맵의 우선순위를 어떻게 결정하시겠습니까?',
      context_bridge: '저희는 밀린 기능 요청, 느려진 배포, 누적된 기술 부채가 동시에 존재합니다.',
      why_matters: '한정된 리소스로 최대 효과를 내는 우선순위 설정 능력은 CTO의 핵심 역량입니다.',
      listen_for: '비즈니스 임팩트 기반 판단, 정량적 기준, 이해관계자와의 합의 프로세스.',
      code_reference: null,
      terminology: [
        {
          term: 'Roadmap',
          pronunciation: '로드맵',
          explanation: '제품이 앞으로 어떻게 발전할지 그린 계획표입니다.',
          definition: '제품이 앞으로 어떻게 발전할지 그린 계획표입니다.',
          plain_language: '제품이 앞으로 어떻게 발전할지 그린 계획표입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Technical Debt',
          pronunciation: '테크니컬 뎃',
          explanation: '빨리 만들기 위해 대충 짠 코드가 나중에 문제를 일으키는 것입니다.',
          definition: '빨리 만들기 위해 대충 짠 코드가 나중에 문제를 일으키는 것입니다.',
          plain_language: '빨리 만들기 위해 대충 짠 코드가 나중에 문제를 일으키는 것입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Backlog',
          pronunciation: '백로그',
          explanation: '해야 할 일 목록. 아직 시작하지 않은 작업들의 대기열입니다.'
        },
        {
          term: 'Sprint',
          pronunciation: '스프린트',
          explanation: '1~2주 단위의 작업 주기. 짧은 주기로 계획하고 실행합니다.'
        },
        {
          term: 'Impact',
          pronunciation: '임팩트',
          explanation: '영향력. 이 작업이 비즈니스에 얼마나 큰 효과를 주는지입니다.'
        },
        {
          term: 'Effort',
          pronunciation: '에포트',
          explanation: '노력. 이 작업을 완료하는 데 필요한 시간과 인력입니다.'
        },
        {
          term: 'RICE Framework',
          pronunciation: '라이스 프레임워크',
          explanation: 'Reach, Impact, Confidence, Effort. 우선순위를 정하는 점수 체계입니다.'
        },
        {
          term: 'Opportunity Cost',
          pronunciation: '오퍼튜니티 코스트',
          explanation: '기회비용. A를 선택하면 포기해야 하는 B의 가치입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '비즈니스 임팩트 기준',
          importance: 'must',
          explanation: '매출, 고객 영향 등 비즈니스 가치로 우선순위를 결정해야 함'
        },
        {
          keyword: '정량적 프레임워크',
          importance: 'must',
          explanation: '감이 아닌 수치 기반 판단(RICE 등)'
        },
        {
          keyword: '기술 부채 비율',
          importance: 'good_to_have',
          explanation: '전체 작업 중 기술 부채에 일정 비율(20~30%)을 할당하는 전략'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 15,
          text: 'RICE 같은 정량적 프레임워크를 사용하고, 기술 부채에 20~30% 고정 할당하며, CEO/PM과 합의 프로세스를 설명.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 8,
          text: '우선순위가 중요하다고 하지만 구체적 판단 기준이나 프레임워크 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: 'CEO가 원하는 대로 하겠다거나, 기술 부채만 먼저 해결하겠다는 편향적 답변.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q17-f1',
          trigger: 'Expert',
          question_text: 'PM이 새 기능을, 개발팀이 기술 부채를 우선하자고 갈등할 때 어떻게 중재하시겠습니까?',
          why_matters: '이해관계자 간 갈등 중재 능력.',
          listen_for: '데이터 기반 설득, 양쪽 관점 존중.',
          good: {
            text: '기술 부채의 비즈니스 비용을 수치로 보여주고, 양쪽에 시간을 배분하는 합의안 제시.',
            score: 8
          },
          poor: {
            text: 'CTO이니까 기술 부채가 우선이라고 일방적 결정.',
            score: 0
          }
        },
        {
          id: 'q17-f2',
          trigger: 'Mid',
          question_text: '우선순위를 정할 때 가장 중요한 기준 하나를 고르라면 무엇인가요?',
          why_matters: '핵심 판단 기준의 명확성.',
          listen_for: '비즈니스 임팩트, 고객 가치 등.',
          good: {
            text: '고객에게 주는 가치나 매출 영향이라고 명확히 답변.',
            score: 5
          },
          poor: {
            text: '모든 기준이 다 중요하다.',
            score: -2
          }
        },
        {
          id: 'q17-f3',
          trigger: 'Low',
          question_text: '지금 당장 해야 할 일이 10개라면, 어떻게 3개로 줄이시겠습니까?',
          why_matters: '기본적인 우선순위 설정 능력.',
          listen_for: '제거 기준, 위임 가능성.',
          good: {
            text: '긴급성과 중요성으로 분류하여 3개를 선택.',
            score: 5
          },
          poor: {
            text: '10개 다 해야 한다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 제한된 시간과 인력으로 무엇을 먼저 할지 체계적으로 결정할 수 있는가를 확인합니다.',
        daily_analogy: '가정에서 월급으로 식비, 교육비, 저축을 동시에 해야 하는 것과 같습니다. 좋은 관리자는 비율을 정해놓고(식비 40%, 교육비 30%, 저축 30%) 매달 조정합니다.',
        level_expectation: 'CTO 수준에서는 감이 아닌 프레임워크로 판단하고, 기술 부채에 일정 비율을 고정 배분하는 전략이 있어야 합니다.'
      },
      expected_answer: {
        core: '• 프레임워크: RICE(Reach × Impact × Confidence ÷ Effort)로 정량 평가\n• 기술 부채: 전체 스프린트의 20~30%를 기술 부채에 고정 할당\n• 합의: CEO/PM과 분기별 로드맵 리뷰로 방향 정렬',
        example: '저는 세 가지 원칙으로 우선순위를 잡습니다. 첫째, 모든 작업에 RICE 점수를 매깁니다. "이 기능이 몇 명의 고객에게 영향을 주는지(Reach)", "영향의 크기(Impact)", "확신도(Confidence)", "필요한 시간(Effort)"을 점수화하여 비교합니다. 둘째, 매 스프린트에서 30%는 기술 부채 해결에 고정 배분합니다. 이는 협상 대상이 아닙니다. 셋째, 분기별로 CEO, PM과 함께 로드맵 리뷰를 합니다.',
        key_points: ['정량적 프레임워크', '기술 부채 고정 배분', '합의 프로세스']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['기술 부채 해결, 새 기능 개발, 인프라 개선이 동시에 필요한 상황에서 제품 로드맵의 우선순위를 어떻게 결정하시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 18,
      category: 'execution_ownership',
      difficulty: 'Hard',
      title: '벤더/도구 선택 프로세스',
      question_text: '새로운 기술 스택이나 외부 벤더를 도입할 때 어떤 평가 프로세스를 거치시나요? 잘못된 선택을 했을 때의 경험도 공유해주세요.',
      context_bridge: '저희는 모니터링 도구, CI/CD 파이프라인, 클라우드 서비스 등 여러 기술 선택을 앞두고 있습니다.',
      why_matters: '기술 선택은 장기적 영향을 미치므로 체계적 평가 프로세스가 필요합니다.',
      listen_for: '평가 기준의 체계성, 팀 참여, 실패 경험에서의 학습.',
      code_reference: null,
      terminology: [
        {
          term: 'POC',
          pronunciation: '피오씨',
          explanation: 'Proof of Concept. 개념 검증. 실제 도입 전에 소규모로 테스트하는 것입니다.',
          definition: 'Proof of Concept. 개념 검증. 실제 도입 전에 소규모로 테스트하는 것입니다.',
          plain_language: 'Proof of Concept. 개념 검증. 실제 도입 전에 소규모로 테스트하는 것입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Vendor',
          pronunciation: '벤더',
          explanation: '외부 제품이나 서비스를 제공하는 회사입니다.',
          definition: '외부 제품이나 서비스를 제공하는 회사입니다.',
          plain_language: '외부 제품이나 서비스를 제공하는 회사입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'SLA',
          pronunciation: '에스엘에이',
          explanation: 'Service Level Agreement. 서비스 수준 계약. 성능과 가용성 보장 조건입니다.'
        },
        {
          term: 'Migration Path',
          pronunciation: '마이그레이션 패스',
          explanation: '현재 시스템에서 새 시스템으로 이동하는 경로와 계획입니다.'
        },
        {
          term: 'Evaluation Matrix',
          pronunciation: '이밸류에이션 매트릭스',
          explanation: '평가 표. 여러 후보를 같은 기준으로 비교하는 표입니다.'
        },
        {
          term: 'Tech Stack',
          pronunciation: '테크 스택',
          explanation: '기술 스택. 서비스를 만들기 위해 사용하는 기술들의 조합입니다.'
        },
        {
          term: 'Lock-in',
          pronunciation: '록인',
          explanation: '특정 기술이나 벤더에 종속되어 변경이 어려운 상태입니다.'
        },
        {
          term: 'Rollback',
          pronunciation: '롤백',
          explanation: '되돌리기. 문제가 생겼을 때 이전 상태로 복원하는 것입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '체계적 평가 프로세스',
          importance: 'must',
          explanation: 'POC, 평가 매트릭스 등 구조화된 의사결정 방법'
        },
        {
          keyword: '팀 참여',
          importance: 'must',
          explanation: 'CTO 혼자가 아닌 팀이 함께 평가하는 프로세스'
        },
        {
          keyword: '실패 학습',
          importance: 'good_to_have',
          explanation: '잘못된 선택에서 배운 교훈을 공유하는 솔직함'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 25,
          text: '평가 매트릭스 + POC + 팀 투표 + 비용 분석의 체계적 프로세스를 제시하고, 실패 사례에서의 구체적 학습 공유.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 12,
          text: '조사하고 비교한다는 일반적 답변. 구체적 프로세스나 실패 경험 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '유명한 것을 쓰면 된다거나, 본인이 익숙한 것을 고집.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q18-f1',
          trigger: 'Expert',
          question_text: '팀원 과반이 A를 원하는데, 기술적으로 B가 더 적합하다면 어떻게 하시겠습니까?',
          why_matters: '기술 판단과 팀 합의의 균형.',
          listen_for: '데이터 기반 설득, 최종 결정 기준.',
          good: {
            text: 'B가 더 나은 이유를 데이터로 설명하되, 팀의 학습 비용과 동기도 고려하여 균형 잡힌 결정.',
            score: 10
          },
          poor: {
            text: '내가 CTO니까 B로 간다.',
            score: 0
          }
        },
        {
          id: 'q18-f2',
          trigger: 'Mid',
          question_text: 'POC 없이 바로 도입해도 되는 경우는 어떤 경우인가요?',
          why_matters: 'POC의 필요성 판단 기준.',
          listen_for: '영향 범위, 가역성, 비용.',
          good: {
            text: '영향 범위가 작고 되돌리기 쉬운 경우에는 빠르게 도입.',
            score: 5
          },
          poor: {
            text: 'POC는 항상 필요하다 또는 필요 없다는 극단적 답변.',
            score: -2
          }
        },
        {
          id: 'q18-f3',
          trigger: 'Low',
          question_text: '지금 사용하고 있는 기술 중 가장 만족하는 것과 후회하는 것은 무엇인가요?',
          why_matters: '기술 선택에 대한 기본적 성찰.',
          listen_for: '구체적 경험과 이유.',
          good: {
            text: '구체적 기술과 이유를 설명.',
            score: 5
          },
          poor: {
            text: '특별히 없다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '기술 도구 선택은 회사의 비용, 생산성, 미래 유연성에 큰 영향을 줍니다. 체계적으로 판단하는지 확인합니다.',
        daily_analogy: '자동차를 살 때 가격, 연비, 보험료, 수리비, 리셀 가치를 모두 비교하는 것과 같습니다. 디자인만 보고 사면 후회합니다.',
        level_expectation: 'CTO 수준에서는 개인 취향이 아닌 팀 참여 + 데이터 기반의 체계적 평가 프로세스가 있어야 합니다.'
      },
      expected_answer: {
        core: '• 프로세스: 요구사항 정의 → 후보 리스트 → 평가 매트릭스 → POC → 팀 리뷰 → 결정\n• 평가 기준: 기능, 비용(TCO), 팀 학습 곡선, 커뮤니티, 록인 리스크\n• 실패 학습: 과거 잘못된 선택의 원인과 개선점',
        example: '저는 5단계 프로세스를 씁니다. 1단계: 필수 요구사항과 우대 요구사항을 문서화합니다. 2단계: 후보 3~4개를 선정합니다. 3단계: 평가 매트릭스에 기능, 비용, 학습 곡선, 커뮤니티 활성도, 록인 리스크를 점수화합니다. 4단계: 상위 2개로 1~2주 POC를 진행합니다. 5단계: 팀과 함께 결과를 리뷰하고 최종 결정합니다. 실패 사례로는, 이전 회사에서 인기 있다는 이유로 GraphQL을 도입했는데 팀에 경험자가 없어 6개월간 생산성이 30% 떨어졌습니다. 이후 팀 역량을 평가 기준에 반드시 포함시킵니다.',
        key_points: ['체계적 프로세스', '팀 참여', '실패 학습']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['새로운 기술 스택이나 외부 벤더를 도입할 때 어떤 평가 프로세스를 거치시나요? 잘못된 선택을 했을 때의 경험도 공유해주세요.', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 19,
      category: 'execution_ownership',
      difficulty: 'Medium',
      title: '인시던트 관리와 SLA',
      question_text: '프로덕션 장애가 발생했을 때의 인시던트 관리 프로세스를 어떻게 설계하시겠습니까? SLA는 어떤 기준으로 설정하시나요?',
      context_bridge: '저희는 아직 공식적인 인시던트 관리 프로세스가 없고, 장애가 나면 그때그때 대응하고 있습니다.',
      why_matters: '핀테크 서비스의 장애는 고객의 돈과 직결됩니다. 체계적 장애 대응 능력을 확인합니다.',
      listen_for: '심각도 분류, 에스컬레이션 경로, 포스트모템, SLA 설정 기준.',
      code_reference: null,
      terminology: [
        {
          term: 'Incident',
          pronunciation: '인시던트',
          explanation: '장애. 서비스가 정상적으로 동작하지 않는 상황입니다.',
          definition: '장애. 서비스가 정상적으로 동작하지 않는 상황입니다.',
          plain_language: '장애. 서비스가 정상적으로 동작하지 않는 상황입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'SLA',
          pronunciation: '에스엘에이',
          explanation: 'Service Level Agreement. 고객에게 약속하는 서비스 가용성 수준입니다.',
          definition: 'Service Level Agreement. 고객에게 약속하는 서비스 가용성 수준입니다.',
          plain_language: 'Service Level Agreement. 고객에게 약속하는 서비스 가용성 수준입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'SLO',
          pronunciation: '에스엘오',
          explanation: 'Service Level Objective. 내부적으로 목표하는 서비스 수준입니다.'
        },
        {
          term: 'Severity',
          pronunciation: '세버리티',
          explanation: '심각도. 장애의 영향 범위와 긴급성을 분류하는 등급입니다.'
        },
        {
          term: 'Escalation',
          pronunciation: '에스컬레이션',
          explanation: '상위 보고. 장애가 심각하면 더 높은 직급에게 알리는 것입니다.'
        },
        {
          term: 'On-call',
          pronunciation: '온콜',
          explanation: '장애 발생 시 즉시 대응하는 당번 제도입니다.'
        },
        {
          term: 'Postmortem',
          pronunciation: '포스트모템',
          explanation: '장애 후 원인 분석과 재발 방지책을 논의하는 회의입니다.'
        },
        {
          term: 'MTTR',
          pronunciation: '엠티티알',
          explanation: '평균 복구 시간. 장애 발생부터 정상화까지 걸리는 시간입니다.'
        },
        {
          term: 'Runbook',
          pronunciation: '런북',
          explanation: '장애 대응 매뉴얼. 상황별로 어떻게 대응해야 하는지 적어놓은 문서입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '심각도 분류 체계',
          importance: 'must',
          explanation: '모든 장애를 같은 수준으로 대응하면 비효율적'
        },
        {
          keyword: '포스트모템 문화',
          importance: 'must',
          explanation: '장애에서 학습하는 체계가 있어야 반복 방지'
        },
        {
          keyword: 'SLA/SLO 구분',
          importance: 'good_to_have',
          explanation: '외부 약속(SLA)과 내부 목표(SLO)를 구분하는 인식'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: '심각도 4단계 분류 + 에스컬레이션 경로 + 온콜 로테이션 + 포스트모템 + SLA/SLO 구분까지 체계적 설계.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '장애 대응은 해봤지만 체계적 프로세스 설계 경험 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '장애가 나면 다 같이 모여서 해결한다는 비체계적 답변.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q19-f1',
          trigger: 'Expert',
          question_text: '심야에 P1 장애가 발생했는데, 온콜 담당자가 응답하지 않으면 어떻게 하시겠습니까?',
          why_matters: '에스컬레이션 프로세스의 구체성.',
          listen_for: '백업 온콜, 자동 에스컬레이션, 연락 체계.',
          good: {
            text: '백업 온콜 → 팀 리드 → CTO 순서의 자동 에스컬레이션 + 15분 룰.',
            score: 8
          },
          poor: {
            text: '전원에게 연락한다.',
            score: 0
          }
        },
        {
          id: 'q19-f2',
          trigger: 'Mid',
          question_text: 'SLA를 99.9%로 설정하면 연간 허용 다운타임이 얼마인지 아시나요?',
          why_matters: 'SLA 수치에 대한 현실적 이해.',
          listen_for: '약 8.7시간이라는 구체적 수치.',
          good: {
            text: '약 8~9시간이라고 답변하고, 현실적 달성 가능성을 논의.',
            score: 5
          },
          poor: {
            text: '모르겠다.',
            score: 0
          }
        },
        {
          id: 'q19-f3',
          trigger: 'Low',
          question_text: '장애가 발생했을 때 가장 먼저 해야 할 일은 무엇인가요?',
          why_matters: '기본적인 장애 대응 순서.',
          listen_for: '영향 범위 파악, 고객 공지, 원인 조사.',
          good: {
            text: '서비스 영향 범위를 파악하고 고객에게 공지하는 것이 먼저.',
            score: 5
          },
          poor: {
            text: '코드를 보고 버그를 찾는다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '핀테크에서 장애는 고객의 돈과 직결됩니다. 체계적 대응 프로세스가 없으면 작은 장애도 큰 사고로 번집니다.',
        daily_analogy: '병원 응급실의 트리아주(환자 분류) 시스템과 같습니다. 모든 환자를 같은 순서로 진료하면 생명이 위험한 환자가 기다려야 합니다. 심각도에 따라 대응 속도를 다르게 해야 합니다.',
        level_expectation: 'CTO 수준에서는 심각도 분류, 에스컬레이션 경로, 온콜 로테이션, 포스트모템까지 포함한 체계적 인시던트 관리 프로세스를 설계할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 심각도 분류: P1(전체 장애) ~ P4(경미) 4단계\n• 대응 체계: 온콜 로테이션 + 에스컬레이션 경로 + 런북\n• 학습: 모든 P1/P2에 대해 48시간 내 포스트모템\n• SLA: 외부 99.9%, 내부 SLO 99.95%로 여유분 확보',
        example: '저는 4단계 심각도 체계를 도입하겠습니다. P1은 전체 서비스 중단으로 15분 내 대응, P2는 핵심 기능 장애로 30분 내 대응, P3는 부분 기능 저하로 4시간 내, P4는 경미한 이슈로 다음 영업일 대응입니다. 온콜은 주 단위 로테이션으로 2명(주/부)을 배정합니다. 모든 P1/P2 장애 후 48시간 내에 비난 없는 포스트모템을 작성하여 전체 팀과 공유합니다. SLA는 고객에게 99.9%를 약속하되, 내부 목표(SLO)는 99.95%로 설정하여 여유분을 확보합니다.',
        key_points: ['심각도 분류', '온콜 체계', '포스트모템 문화']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['프로덕션 장애가 발생했을 때의 인시던트 관리 프로세스를 어떻게 설계하시실 건가요? SLA는 어떤 기준으로 설정하시나요에 대해 설명해 주시겠습니까?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 20,
      category: 'communication',
      difficulty: 'Hard',
      title: '이사회 기술 발표',
      question_text: '이사회에서 "현재 기술 팀에 대규모 투자가 필요하다"고 설득해야 합니다. 어떤 자료를 준비하고 어떻게 발표하시겠습니까?',
      context_bridge: 'Series A 투자 이후 이사회는 기술 투자의 ROI를 궁금해합니다.',
      why_matters: 'CTO는 기술 투자를 비즈니스 가치로 번역하여 비기술 이사회를 설득할 수 있어야 합니다.',
      listen_for: '비즈니스 언어로의 번역, 데이터 기반 설득, 리스크도 투명하게 공유.',
      code_reference: null,
      terminology: [
        {
          term: 'ROI',
          pronunciation: '알오아이',
          explanation: '투자 대비 수익률. 100만원을 투자해서 150만원을 벌면 ROI 50%입니다.',
          definition: '투자 대비 수익률. 100만원을 투자해서 150만원을 벌면 ROI 50%입니다.',
          plain_language: '투자 대비 수익률. 100만원을 투자해서 150만원을 벌면 ROI 50%입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Board Deck',
          pronunciation: '보드 덱',
          explanation: '이사회 발표 자료. 핵심 내용을 간결하게 담은 슬라이드입니다.',
          definition: '이사회 발표 자료. 핵심 내용을 간결하게 담은 슬라이드입니다.',
          plain_language: '이사회 발표 자료. 핵심 내용을 간결하게 담은 슬라이드입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Capex vs Opex',
          pronunciation: '캡엑스 옵엑스',
          explanation: '자본 지출과 운영 지출. 초기 투자 비용과 지속적 운영 비용의 구분입니다.'
        },
        {
          term: 'Headcount',
          pronunciation: '헤드카운트',
          explanation: '인원수. 팀에 필요한 사람의 수입니다.'
        },
        {
          term: 'Revenue Impact',
          pronunciation: '레베뉴 임팩트',
          explanation: '매출 영향. 기술 투자가 매출에 미치는 효과입니다.'
        },
        {
          term: 'Cost Reduction',
          pronunciation: '코스트 리덕션',
          explanation: '비용 절감. 기술 개선으로 운영 비용을 줄이는 것입니다.'
        },
        {
          term: 'Competitive Advantage',
          pronunciation: '컴페티티브 어드밴티지',
          explanation: '경쟁 우위. 다른 회사보다 더 나은 점입니다.'
        },
        {
          term: 'Risk Mitigation',
          pronunciation: '리스크 미티게이션',
          explanation: '위험 완화. 발생할 수 있는 문제를 미리 줄이는 것입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '비즈니스 언어 번역',
          importance: 'must',
          explanation: '기술 투자를 매출, 비용, 리스크로 번역'
        },
        {
          keyword: '데이터 기반 설득',
          importance: 'must',
          explanation: '감정이 아닌 수치와 비교 데이터로 설득'
        },
        {
          keyword: '리스크 투명 공유',
          importance: 'good_to_have',
          explanation: '투자하지 않았을 때의 리스크도 함께 제시'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 25,
          text: '비용/매출 영향 수치화 + 경쟁사 벤치마크 + 투자 안 할 경우의 리스크까지 포함한 균형 잡힌 발표 설계.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 12,
          text: '기술적으로 필요하다는 것은 설명하지만, 비즈니스 수치로의 번역이 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '기술 용어로만 설명하거나, 이사회 발표 경험에 대한 준비가 전혀 없음.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q20-f1',
          trigger: 'Expert',
          question_text: '이사회가 "왜 경쟁사보다 기술 인력이 더 많이 필요한가"라고 질문하면 어떻게 답하시겠습니까?',
          why_matters: '경쟁 분석과 자원 정당화 능력.',
          listen_for: '경쟁사 분석, 차별화 전략.',
          good: {
            text: '경쟁사 대비 기술 역량 분석과 우리만의 차별화 전략을 수치로 제시.',
            score: 10
          },
          poor: {
            text: '더 좋은 제품을 만들려면 사람이 더 필요하다는 일반론.',
            score: 0
          }
        },
        {
          id: 'q20-f2',
          trigger: 'Mid',
          question_text: '개발자 3명 채용의 ROI를 숫자로 설명해보실 수 있나요?',
          why_matters: '기술 투자의 정량적 가치 산정.',
          listen_for: '인건비 vs 생산성 향상 vs 매출 효과.',
          good: {
            text: '채용 비용 대비 배포 속도 개선 → 고객 확보 속도 → 매출 증가로 연결하여 설명.',
            score: 5
          },
          poor: {
            text: '개발자가 더 있으면 더 빨리 만든다는 정성적 답변.',
            score: -2
          }
        },
        {
          id: 'q20-f3',
          trigger: 'Low',
          question_text: '이사회에서 가장 피해야 할 발표 실수는 무엇일까요?',
          why_matters: '이사회 커뮤니케이션 기본 인식.',
          listen_for: '기술 용어 남발, 너무 긴 발표.',
          good: {
            text: '기술 용어를 쓰지 않고 비즈니스 영향으로 설명해야 한다.',
            score: 5
          },
          poor: {
            text: '모르겠다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: 'CTO가 기술 투자를 이사회에 설득하지 못하면 팀은 성장할 수 없습니다. 비즈니스 언어로 소통하는 능력이 핵심입니다.',
        daily_analogy: '집 수리가 필요할 때 배우자를 설득하는 것과 같습니다. "배관이 낡았다"가 아니라 "지금 100만원 쓰면 나중에 수해 복구비 1000만원을 아낄 수 있다"라고 해야 설득됩니다.',
        level_expectation: 'CTO 수준에서는 기술 투자를 매출 증가, 비용 절감, 리스크 감소의 3가지 관점에서 수치화하여 설명할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 프레이밍: 기술 투자가 아니라 비즈니스 성장 투자로 프레이밍\n• 3가지 축: 매출 증가, 비용 절감, 리스크 감소\n• 형식: 10장 이내 슬라이드, 숫자 중심, 경쟁사 비교 포함',
        example: '이사회 발표를 3파트로 구성합니다. 파트1 "현재 상황": 배포가 주 1회로 경쟁사(주 5회) 대비 느려서 고객 이탈이 월 5% 증가 중입니다. 파트2 "투자 계획": 시니어 개발자 3명 채용(연 2.4억) + 인프라 개선(5천만원). 파트3 "기대 효과": 배포 주 5회 달성 시 고객 이탈률 2%로 감소, 연 매출 3억 증가 예상. 투자 안 할 경우의 리스크도 함께 제시합니다: 현재 속도라면 6개월 후 경쟁사에 핵심 고객 3곳을 빼앗길 가능성이 높습니다.',
        key_points: ['비즈니스 언어', '수치화', '리스크 투명성']
      },
      jd_competency_link: 'JD 요구사항: "팀 리더십 8~15명 규모" → 비기술 이해관계자와의 소통 검증',
      generation_rationale: '후보자의 팀 규모 경험(4-6명)이 요구(8-15명)보다 작아 소통 역량 확인 필요',
      skills_assessed: ['communication', 'leadership'],
      alternative_phrasings: ['이사회에서 "현재 기술 팀에 대규모 투자가 필요하다"고 설득해야 합니다. 어떤 자료를 준비하고 어떻게 발표하시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 21,
      category: 'communication',
      difficulty: 'Easy',
      title: 'CEO와의 관계 관리',
      question_text: 'CEO와 의견이 다를 때 어떻게 소통하시나요? 특히 CEO가 기술적으로 불가능한 것을 요구할 때 어떻게 하시겠습니까?',
      context_bridge: 'CTO와 CEO의 관계는 회사의 성패를 좌우합니다. 건설적 갈등 관리가 중요합니다.',
      why_matters: 'CEO와의 건강한 긴장 관계를 유지하면서도 기술적 무결성을 지키는 능력을 확인합니다.',
      listen_for: '존중과 솔직함의 균형, 대안 제시, 최종 결정 수용과 기록.',
      code_reference: null,
      terminology: [
        {
          term: 'C-level',
          pronunciation: '씨레벨',
          explanation: 'CEO, CTO, CFO 등 최고 경영진을 총칭합니다.',
          definition: 'CEO, CTO, CFO 등 최고 경영진을 총칭합니다.',
          plain_language: 'CEO, CTO, CFO 등 최고 경영진을 총칭합니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Alignment',
          pronunciation: '얼라인먼트',
          explanation: '방향 정렬. 모두가 같은 목표를 향해 가고 있는 상태입니다.',
          definition: '방향 정렬. 모두가 같은 목표를 향해 가고 있는 상태입니다.',
          plain_language: '방향 정렬. 모두가 같은 목표를 향해 가고 있는 상태입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Managing Up',
          pronunciation: '매니징 업',
          explanation: '상위 관리. 상사와 효과적으로 소통하고 관계를 관리하는 것입니다.'
        },
        {
          term: 'Disagree and Commit',
          pronunciation: '디스어그리 앤 커밋',
          explanation: '반대하되 실행한다. 논의 후 결정되면 반대했어도 전적으로 실행하는 원칙입니다.'
        },
        {
          term: 'Data-driven',
          pronunciation: '데이터 드리븐',
          explanation: '데이터 기반. 직감이 아닌 수치와 증거로 판단하는 것입니다.'
        },
        {
          term: 'Trade-off',
          pronunciation: '트레이드오프',
          explanation: '하나를 얻기 위해 다른 것을 포기하는 선택입니다.'
        },
        {
          term: 'Stakeholder Management',
          pronunciation: '스테이크홀더 매니지먼트',
          explanation: '이해관계자 관리. 다양한 관련자들과 효과적으로 소통하는 것입니다.'
        },
        {
          term: 'Transparency',
          pronunciation: '트랜스페어런시',
          explanation: '투명성. 정보를 숨기지 않고 공개하는 것입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '대안 제시',
          importance: 'must',
          explanation: '안 된다만 말하지 않고 가능한 대안을 함께 제시'
        },
        {
          keyword: '데이터 기반 소통',
          importance: 'must',
          explanation: '감정이 아닌 데이터로 설득'
        },
        {
          keyword: 'Disagree and Commit',
          importance: 'good_to_have',
          explanation: '최종 결정 후에는 전적으로 실행하는 성숙함'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 15,
          text: 'CEO의 의도를 먼저 파악하고, 대안을 데이터와 함께 제시하며, 최종 결정은 존중하되 리스크는 기록하는 성숙한 접근.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 8,
          text: '안 된다고 말하거나, 무조건 따른다는 양극단.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: 'CEO와 갈등을 피하거나, 기술적 관점만 고집.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q21-f1',
          trigger: 'Expert',
          question_text: 'CEO가 당신의 반대에도 불구하고 결정을 밀어붙였는데, 결과적으로 실패했습니다. 어떻게 하시겠습니까?',
          why_matters: '갈등 후 관계 회복과 학습 능력.',
          listen_for: '비난 없이 학습, 프로세스 개선.',
          good: {
            text: '비난이 아닌 학습 관점으로 포스트모템을 진행하고, 향후 의사결정 프로세스를 개선 제안.',
            score: 8
          },
          poor: {
            text: '내가 반대했었다고 상기시킨다.',
            score: 0
          }
        },
        {
          id: 'q21-f2',
          trigger: 'Mid',
          question_text: 'CEO에게 나쁜 소식(프로젝트 지연 등)을 전할 때 어떻게 하시나요?',
          why_matters: '투명한 소통 의지.',
          listen_for: '빠른 공유, 원인과 대안 함께 제시.',
          good: {
            text: '가능한 빨리, 원인과 대안을 함께 가지고 가서 보고.',
            score: 5
          },
          poor: {
            text: '해결한 후에 보고한다.',
            score: -2
          }
        },
        {
          id: 'q21-f3',
          trigger: 'Low',
          question_text: 'CEO와 CTO가 잘 협업하는 회사의 특징은 무엇이라고 생각하시나요?',
          why_matters: 'C-level 협업에 대한 기본 인식.',
          listen_for: '상호 존중, 역할 분담, 투명한 소통.',
          good: {
            text: '역할 분담과 상호 존중을 언급.',
            score: 5
          },
          poor: {
            text: 'CEO가 기술을 이해하면 된다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: 'CTO와 CEO의 관계가 나쁘면 회사 전체가 흔들립니다. 건설적으로 의견을 다루는 능력이 핵심입니다.',
        daily_analogy: '부부가 집을 고를 때 의견이 다른 상황과 비슷합니다. 한쪽이 무조건 양보하거나 싸우면 안 되고, 각자의 우선순위를 공유하고 데이터(가격, 통근 시간)로 비교하여 합의해야 합니다.',
        level_expectation: 'CTO 수준에서는 CEO의 의도를 먼저 이해하고, 대안을 제시하며, 최종 결정 후에는 전적으로 실행하는 "Disagree and Commit" 원칙이 있어야 합니다.'
      },
      expected_answer: {
        core: '• 1단계: CEO의 의도(Why)를 먼저 파악\n• 2단계: 데이터와 대안을 함께 제시\n• 3단계: 최종 결정은 존중하되 리스크는 문서화\n• 원칙: Disagree and Commit',
        example: 'CEO가 불가능한 것을 요구할 때, 먼저 "왜 이것이 필요한가"를 물어봅니다. 대부분 기술 자체가 아니라 비즈니스 목표가 있습니다. 예를 들어 CEO가 "2주 안에 AI 추천 기능을 만들라"고 하면, "AI 추천의 목적이 전환율 향상이시죠? 2주 안에 규칙 기반 추천을 먼저 만들고, AI는 2개월에 걸쳐 고도화하는 건 어떨까요?"라고 대안을 제시합니다. 데이터로 설득하되, CEO가 최종적으로 다른 결정을 하면 존중하고 전적으로 실행합니다. 단, 리스크는 문서로 기록해둡니다.',
        key_points: ['의도 파악', '대안 제시', 'Disagree and Commit']
      },
      jd_competency_link: 'JD 요구사항: "팀 리더십 8~15명 규모" → 비기술 이해관계자와의 소통 검증',
      generation_rationale: '후보자의 팀 규모 경험(4-6명)이 요구(8-15명)보다 작아 소통 역량 확인 필요',
      skills_assessed: ['communication', 'leadership'],
      alternative_phrasings: ['CEO와 의견이 다를 때 어떻게 소통하시나요? 특히 CEO가 기술적으로 불가능한 것을 요구할 때 어떻게 하시겠습니까에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 22,
      category: 'communication',
      difficulty: 'Medium',
      title: '외부 파트너십 및 API 통합',
      question_text: '외부 결제 서비스나 데이터 제공업체와의 기술 파트너십을 관리한 경험이 있으신가요? 파트너사의 API가 불안정할 때 어떻게 대응하시겠습니까?',
      context_bridge: '저희는 결제 게이트웨이, 신용 평가, 본인 인증 등 여러 외부 서비스에 의존합니다.',
      why_matters: '핀테크는 외부 파트너 의존도가 높아 기술적 소통과 리스크 관리가 중요합니다.',
      listen_for: '파트너 관리 경험, 기술적 리스크 완화 전략, 커뮤니케이션 능력.',
      code_reference: null,
      terminology: [
        {
          term: 'API',
          pronunciation: '에이피아이',
          explanation: '프로그램끼리 대화하는 방법. 외부 서비스의 기능을 우리 시스템에서 사용할 수 있게 합니다.',
          definition: '프로그램끼리 대화하는 방법. 외부 서비스의 기능을 우리 시스템에서 사용할 수 있게 합니다.',
          plain_language: '프로그램끼리 대화하는 방법. 외부 서비스의 기능을 우리 시스템에서 사용할 수 있게 합니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'SLA',
          pronunciation: '에스엘에이',
          explanation: '서비스 수준 계약. 파트너가 보장하는 성능과 가용성 조건입니다.',
          definition: '서비스 수준 계약. 파트너가 보장하는 성능과 가용성 조건입니다.',
          plain_language: '서비스 수준 계약. 파트너가 보장하는 성능과 가용성 조건입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Fallback',
          pronunciation: '폴백',
          explanation: '대체 방안. 주 서비스가 안 될 때 사용하는 백업 서비스입니다.'
        },
        {
          term: 'Rate Limiting',
          pronunciation: '레이트 리미팅',
          explanation: '요청 제한. 일정 시간 내 보낼 수 있는 요청 수를 제한하는 것입니다.'
        },
        {
          term: 'Timeout',
          pronunciation: '타임아웃',
          explanation: '시간 초과. 응답이 너무 늦으면 자동으로 포기하는 설정입니다.'
        },
        {
          term: 'Circuit Breaker',
          pronunciation: '서킷 브레이커',
          explanation: '문제가 생긴 서비스로의 요청을 자동 차단하는 안전장치입니다.'
        },
        {
          term: 'Retry',
          pronunciation: '리트라이',
          explanation: '재시도. 실패한 요청을 다시 보내는 것입니다. 지수 백오프로 간격을 늘려가며 시도합니다.'
        },
        {
          term: 'Webhook',
          pronunciation: '웹훅',
          explanation: '외부 서비스가 우리 서비스에 자동으로 알림을 보내는 방식입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: 'Fallback 전략',
          importance: 'must',
          explanation: '파트너 장애 시 대체 서비스로 자동 전환하는 설계'
        },
        {
          keyword: 'Circuit Breaker 패턴',
          importance: 'must',
          explanation: '불안정한 파트너 API로 인한 연쇄 장애 방지'
        },
        {
          keyword: '파트너 SLA 관리',
          importance: 'good_to_have',
          explanation: '계약에 SLA를 명시하고 모니터링하는 관리 체계'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: 'Fallback + Circuit Breaker + 파트너 SLA 모니터링 + 정기 기술 미팅까지 포함한 체계적 파트너 관리 전략.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '파트너 API를 사용한 경험은 있지만, 장애 시 체계적 대응 전략 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: 0,
          text: '외부 파트너 관리 경험이 없거나, 파트너 문제는 파트너가 해결해야 한다는 태도.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q22-f1',
          trigger: 'Expert',
          question_text: '결제 게이트웨이 파트너가 갑자기 가격을 50% 인상한다고 통보했습니다. 어떻게 하시겠습니까?',
          why_matters: '벤더 의존성 관리와 협상 능력.',
          listen_for: '대안 준비, 협상 전략, 장기적 의존성 감소.',
          good: {
            text: '협상하면서 동시에 대안 벤더 POC를 진행하여 협상력 확보. 장기적으로 멀티 벤더 전략.',
            score: 8
          },
          poor: {
            text: '수용하거나 즉시 교체.',
            score: 0
          }
        },
        {
          id: 'q22-f2',
          trigger: 'Mid',
          question_text: '파트너 API의 응답 시간이 평소 200ms에서 2초로 느려졌다면 어떻게 대응하시겠습니까?',
          why_matters: '실시간 대응 능력.',
          listen_for: '타임아웃 설정, 캐싱, 파트너 연락.',
          good: {
            text: '타임아웃을 설정하고, 가능한 데이터는 캐싱하며, 파트너에게 즉시 연락.',
            score: 5
          },
          poor: {
            text: '기다린다.',
            score: -2
          }
        },
        {
          id: 'q22-f3',
          trigger: 'Low',
          question_text: '외부 API를 우리 시스템에 연결할 때 가장 주의해야 할 점은 무엇인가요?',
          why_matters: '기본적인 외부 의존성 인식.',
          listen_for: '장애 가능성, 보안, 버전 관리.',
          good: {
            text: '외부 서비스가 언제든 장애가 날 수 있다는 가정하에 설계해야 한다.',
            score: 5
          },
          poor: {
            text: '문서대로 연결하면 된다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '핀테크는 결제, 인증, 신용 평가 등 외부 서비스에 크게 의존합니다. 파트너 장애가 곧 우리 서비스 장애입니다.',
        daily_analogy: '식당이 식자재 납품업체에 의존하는 것과 같습니다. 주 납품업체가 못 올 때를 대비해 백업 업체를 확보하고, 핵심 재료는 항상 재고를 유지해야 합니다.',
        level_expectation: 'CTO 수준에서는 외부 파트너의 장애를 우리 시스템의 장애로 전파시키지 않는 기술적 방어 전략이 있어야 합니다.'
      },
      expected_answer: {
        core: '• 기술적 방어: Circuit Breaker + Timeout + Retry(지수 백오프) + Fallback 서비스\n• 관리 체계: 파트너 SLA 모니터링 + 분기별 기술 리뷰 미팅\n• 장기 전략: 핵심 파트너는 멀티 벤더 전략으로 의존도 분산',
        example: '외부 API 통합 시 3가지를 반드시 설계합니다. 첫째, Circuit Breaker를 두어 파트너 API가 5회 연속 실패하면 자동으로 요청을 차단하고, Fallback(대체 서비스 또는 캐시된 데이터)으로 전환합니다. 둘째, 모든 파트너 API의 응답 시간과 에러율을 실시간 모니터링합니다. 셋째, 핵심 파트너(결제 게이트웨이)는 반드시 백업 벤더를 확보하고, 분기별 기술 미팅으로 변경 사항을 사전에 파악합니다.',
        key_points: ['기술적 방어', 'SLA 모니터링', '멀티 벤더 전략']
      },
      jd_competency_link: 'JD 요구사항: "팀 리더십 8~15명 규모" → 비기술 이해관계자와의 소통 검증',
      generation_rationale: '후보자의 팀 규모 경험(4-6명)이 요구(8-15명)보다 작아 소통 역량 확인 필요',
      skills_assessed: ['communication', 'leadership'],
      alternative_phrasings: [
        '외부 결제 서비스나 데이터 제공업체와의 기술 파트너십을 관리한 경험이 있으신가요? 파트너사의 API가 불안정할 때 어떻게 대응하시겠습니까에 대해 설명해 주시실 건가요?',
        '이 주제에 대한 경험이나 생각을 공유해 주세요.'
      ]
    },
    {
      id: 23,
      category: 'risk_flags',
      difficulty: 'Easy',
      title: '팀 스케일링 경험 한계',
      is_risk: true,
      risk_source: 'LinkedIn 분석에서 최대 4-6명 리드 경험. JD 요구 8-15명 팀으로 스케일링 필요.',
      question_text: '4-6명 팀에서 15명 팀으로 성장시킨다면, 가장 먼저 무너지는 것이 무엇이라고 생각하시나요? 그리고 그것을 어떻게 방지하시겠습니까?',
      context_bridge: '팀 규모가 2~3배 커지면 이전과 완전히 다른 문제들이 생깁니다.',
      why_matters: '팀 스케일링 경험 부족이 가장 큰 위험 요소 중 하나입니다. 이 위험을 인지하고 대비하는지 확인합니다.',
      listen_for: '스케일링 시 발생하는 문제(소통 오버헤드, 사일로, 문화 희석)에 대한 구체적 인식.',
      code_reference: null,
      terminology: [
        {
          term: 'Scaling',
          pronunciation: '스케일링',
          explanation: '규모 확장. 팀이나 시스템을 더 크게 키우는 것입니다.',
          definition: '규모 확장. 팀이나 시스템을 더 크게 키우는 것입니다.',
          plain_language: '규모 확장. 팀이나 시스템을 더 크게 키우는 것입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Communication Overhead',
          pronunciation: '커뮤니케이션 오버헤드',
          explanation: '소통 비용. 사람이 늘수록 소통에 드는 시간과 에너지가 기하급수적으로 증가합니다.',
          definition: '소통 비용. 사람이 늘수록 소통에 드는 시간과 에너지가 기하급수적으로 증가합니다.',
          plain_language: '소통 비용. 사람이 늘수록 소통에 드는 시간과 에너지가 기하급수적으로 증가합니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Silo',
          pronunciation: '사일로',
          explanation: '부서 간 벽. 팀끼리 정보를 공유하지 않고 각자 일하는 현상입니다.'
        },
        {
          term: 'Culture Dilution',
          pronunciation: '컬처 딜루션',
          explanation: '문화 희석. 새로운 사람이 많이 들어오면서 기존 팀 문화가 약해지는 현상입니다.'
        },
        {
          term: 'Hiring Pipeline',
          pronunciation: '하이어링 파이프라인',
          explanation: '채용 파이프라인. 후보자 발굴부터 합격까지의 전체 채용 프로세스입니다.'
        },
        {
          term: 'Onboarding',
          pronunciation: '온보딩',
          explanation: '새 팀원이 빠르게 적응할 수 있도록 돕는 프로그램입니다.'
        },
        {
          term: 'Brooks Law',
          pronunciation: '브룩스 법칙',
          explanation: '늦은 프로젝트에 사람을 추가하면 오히려 더 늦어진다는 법칙입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '소통 비용 증가 인식',
          importance: 'must',
          explanation: '6명에서 15명은 소통 경로가 15개에서 105개로 증가'
        },
        {
          keyword: '구조적 대응',
          importance: 'must',
          explanation: '팀 분리, 중간 관리자, 프로세스 도입 등 구조적 해결책'
        },
        {
          keyword: '문화 보존 전략',
          importance: 'good_to_have',
          explanation: '빠른 성장 중에도 핵심 문화를 유지하는 방법'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 15,
          text: '소통 비용, 문화 희석, 온보딩 부담 등 구체적 위험을 인식하고 각각에 대한 구조적 대응책을 제시.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 8,
          text: '팀이 커지면 어려워진다는 것은 알지만, 구체적으로 무엇이 어떻게 달라지는지 명확하지 않음.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: -5,
          text: '팀 규모가 커져도 별 차이 없다거나, 문제를 인식하지 못함.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q23-f1',
          trigger: 'Expert',
          question_text: '팀이 빠르게 커지면서 기존 멤버들이 불만을 표시합니다. 어떻게 대응하시겠습니까?',
          why_matters: '성장통 관리 능력.',
          listen_for: '기존 멤버의 역할 확대, 소통, 인정.',
          good: {
            text: '기존 멤버를 리드/멘토 역할로 승격하고, 변화의 이유와 비전을 투명하게 공유.',
            score: 8
          },
          poor: {
            text: '변화에 적응하지 못하면 떠나도 어쩔 수 없다.',
            score: 0
          }
        },
        {
          id: 'q23-f2',
          trigger: 'Mid',
          question_text: '6명일 때와 15명일 때 회의 방식은 어떻게 달라져야 할까요?',
          why_matters: '스케일에 따른 프로세스 변화 인식.',
          listen_for: '전체 회의 축소, 팀별 회의, 비동기 소통.',
          good: {
            text: '전체 회의를 줄이고 팀별 스탠드업 + 비동기 문서 소통으로 전환.',
            score: 5
          },
          poor: {
            text: '전체 회의를 그대로 유지.',
            score: -2
          }
        },
        {
          id: 'q23-f3',
          trigger: 'Low',
          question_text: '팀원이 많아지면 왜 소통이 어려워질까요?',
          why_matters: '기본적인 조직 역학 이해.',
          listen_for: '소통 경로 증가, 정보 누락.',
          good: {
            text: '사람 수가 늘면 대화해야 할 조합이 기하급수적으로 늘어난다는 것을 이해.',
            score: 5
          },
          poor: {
            text: '왜 어려운지 모르겠다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '빠른 팀 성장은 스타트업의 핵심 과제입니다. 잘못하면 생산성이 오히려 떨어지고 핵심 인재가 이탈합니다.',
        daily_analogy: '4인 가족이 15인 대가족이 되는 것과 같습니다. 4명은 식탁에서 자연스럽게 대화하지만, 15명은 메뉴 선정, 좌석 배치, 식사 시간 조율이 필요합니다. 구조 없이 키우면 혼란만 커집니다.',
        level_expectation: 'CTO 수준에서는 스케일링 시 구체적으로 무엇이 깨지는지 알고, 구조적 대응책을 사전에 준비할 수 있어야 합니다.'
      },
      expected_answer: {
        core: '• 가장 먼저 무너지는 것: 소통 효율성 — 6명은 모두가 모든 것을 아는 구조, 15명은 불가능\n• 방지 전략: 5~6명 단위 팀 분리 + 팀 간 소통 프로토콜 + 문서화 문화\n• 문화 보존: 핵심 가치를 온보딩에 녹이고, 기존 멤버를 문화 전파자로 육성',
        example: '가장 먼저 무너지는 것은 "모두가 같은 맥락을 공유한다"는 가정입니다. 6명은 점심 때 자연스럽게 정보가 흐르지만, 15명은 불가능합니다. 제 방지 전략은 세 가지입니다. 첫째, 5~6명 단위 스쿼드로 나누고 각 스쿼드가 독립적으로 결정합니다. 둘째, 팀 간 소통을 위해 주 1회 대표자 미팅과 Confluence 문서화를 의무화합니다. 셋째, 신규 입사자 온보딩에 핵심 문화 원칙을 포함시키고, 기존 멤버를 온보딩 버디로 지정하여 문화를 전파합니다.',
        key_points: ['소통 비용 인식', '구조적 대응', '문화 보존']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: [
        '4-6명 팀에서 15명 팀으로 성장시킨다면, 가장 먼저 무너지는 것이 무엇이라고 생각하시나요? 그리고 그것을 어떻게 방지하시겠습니까에 대해 설명해 주시실 건가요?',
        '이 주제에 대한 경험이나 생각을 공유해 주세요.'
      ]
    },
    {
      id: 24,
      category: 'risk_flags',
      difficulty: 'Medium',
      title: '핀테크 도메인 경험 부재',
      is_risk: true,
      risk_source: '이력서와 LinkedIn에서 금융/핀테크 도메인 경험이 확인되지 않음. JD에서 우대사항으로 명시.',
      question_text: '금융 서비스 도메인 경험이 없으신 것으로 보이는데, 핀테크의 특수한 규제와 요구사항을 어떻게 빠르게 학습하실 계획인가요?',
      context_bridge: '핀테크는 일반 IT와 달리 금융 규제, 보안 요구사항, 고객 신뢰 등 특수한 영역이 있습니다.',
      why_matters: '도메인 지식 부족이 기술 결정에 영향을 미칠 수 있습니다. 빠른 학습 능력과 겸손함을 확인합니다.',
      listen_for: '갭에 대한 솔직한 인정, 구체적 학습 계획, 도메인 전문가 활용 전략.',
      code_reference: null,
      terminology: [
        {
          term: 'Domain Knowledge',
          pronunciation: '도메인 날리지',
          explanation: '특정 업무 영역에 대한 전문 지식. 금융, 의료, 교육 등 각 분야의 고유한 지식입니다.',
          definition: '특정 업무 영역에 대한 전문 지식. 금융, 의료, 교육 등 각 분야의 고유한 지식입니다.',
          plain_language: '특정 업무 영역에 대한 전문 지식. 금융, 의료, 교육 등 각 분야의 고유한 지식입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Regulatory',
          pronunciation: '레귤레이터리',
          explanation: '규제. 정부나 감독 기관이 정한 법적 규칙입니다.',
          definition: '규제. 정부나 감독 기관이 정한 법적 규칙입니다.',
          plain_language: '규제. 정부나 감독 기관이 정한 법적 규칙입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'KYC',
          pronunciation: '케이와이씨',
          explanation: 'Know Your Customer. 고객 신원 확인. 금융 서비스에서 법적으로 의무인 본인 인증 절차입니다.'
        },
        {
          term: 'AML',
          pronunciation: '에이엠엘',
          explanation: 'Anti-Money Laundering. 자금 세탁 방지. 불법 자금 유통을 막기 위한 규정입니다.'
        },
        {
          term: 'FinTech',
          pronunciation: '핀테크',
          explanation: 'Financial Technology. 금융과 기술의 결합. 모바일 결제, 송금 앱 등이 예입니다.'
        },
        {
          term: 'Compliance Officer',
          pronunciation: '컴플라이언스 오피서',
          explanation: '규제 준수 담당자. 회사가 법적 규정을 지키고 있는지 관리하는 전문가입니다.'
        },
        {
          term: 'Domain Expert',
          pronunciation: '도메인 엑스퍼트',
          explanation: '해당 분야의 전문가. 금융 도메인이라면 은행, 보험 등에서 오래 경험한 사람입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '갭 인정',
          importance: 'must',
          explanation: '경험 부족을 솔직히 인정하는 것이 출발점'
        },
        {
          keyword: '구체적 학습 계획',
          importance: 'must',
          explanation: '책, 컨설턴트, 멘토 등 구체적 학습 방법 제시'
        },
        {
          keyword: '도메인 전문가 채용/활용',
          importance: 'good_to_have',
          explanation: '혼자 학습이 아닌 전문가를 팀에 영입하는 전략'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 20,
          text: '갭을 솔직히 인정하고, 30/60/90일 학습 계획 + 도메인 전문가 채용/자문 + 규제 매핑까지 구체적 전략 제시.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 10,
          text: '열심히 공부하겠다는 의지는 있지만, 구체적 학습 계획이나 전문가 활용 방안 부족.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: -5,
          text: '도메인 경험은 중요하지 않다거나, 기술만 잘하면 된다는 태도.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q24-f1',
          trigger: 'Expert',
          question_text: '핀테크에서 기술 결정 시 규제 때문에 원하는 기술을 못 쓰는 경우가 있을 수 있습니다. 어떻게 대처하시겠습니까?',
          why_matters: '규제와 기술의 충돌 관리.',
          listen_for: '규제 우선, 대안 기술 탐색, 컴플라이언스 팀 협업.',
          good: {
            text: '규제를 먼저 이해하고, 규제 범위 내에서 최적의 기술 대안을 찾으며, 컴플라이언스 팀과 긴밀히 협업.',
            score: 8
          },
          poor: {
            text: '규제가 바뀌길 기다린다.',
            score: 0
          }
        },
        {
          id: 'q24-f2',
          trigger: 'Mid',
          question_text: '핀테크에서 일반 IT와 가장 다른 점이 무엇이라고 생각하시나요?',
          why_matters: '도메인 특수성에 대한 기본 인식.',
          listen_for: '규제, 보안, 돈을 다루는 책임감.',
          good: {
            text: '돈을 직접 다루므로 오류가 즉시 금전 손실로 이어진다는 특수성 인식.',
            score: 5
          },
          poor: {
            text: '크게 다르지 않다고 생각한다.',
            score: -3
          }
        },
        {
          id: 'q24-f3',
          trigger: 'Low',
          question_text: '새로운 분야를 배울 때 본인만의 학습 방법이 있으신가요?',
          why_matters: '학습 능력과 태도 확인.',
          listen_for: '구체적 학습 방법, 빠른 학습 사례.',
          good: {
            text: '구체적 학습 방법과 빠르게 배운 사례를 공유.',
            score: 5
          },
          poor: {
            text: '특별한 방법 없이 그냥 한다.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '핀테크 도메인 경험이 없는 것 자체가 탈락 사유는 아닙니다. 핵심은 이 갭을 인지하고 빠르게 메울 수 있는 계획과 겸손함이 있느냐입니다.',
        daily_analogy: '경력 있는 요리사가 일식 전문점에 지원한 것과 같습니다. 요리 실력은 검증됐지만, 일식의 특수한 재료, 기법, 문화를 빠르게 배워야 합니다. 실력을 믿되, 일식 전문가에게 배우겠다는 겸손함이 있어야 합니다.',
        level_expectation: 'CTO 수준에서는 도메인 경험 부족을 솔직히 인정하면서, 30/60/90일 단위의 구체적 학습 계획과 도메인 전문가 활용 전략이 있어야 합니다.'
      },
      expected_answer: {
        core: '• 솔직한 인정: 핀테크 도메인 경험이 부족함을 인정\n• 학습 계획: 30일 — 규제 프레임워크 학습, 60일 — 도메인 전문가 자문/채용, 90일 — 실무 적용\n• 전략: 기존 기술 역량 + 도메인 전문가 조합으로 보완',
        example: '솔직히 금융 도메인 경험은 없습니다. 하지만 빠르게 학습할 수 있는 계획이 있습니다. 첫 30일은 핀테크 규제 프레임워크(전자금융거래법, 개인정보보호법)를 집중 학습합니다. 금융 업계 출신 CTO 2~3명에게 멘토링을 요청할 계획입니다. 60일 차에는 도메인 경험이 있는 시니어 엔지니어를 최소 1명 채용합니다. 이 분이 기술 결정 시 규제 관점을 제공하는 역할을 합니다. 90일 차에는 학습한 내용을 기반으로 보안/규제 체크리스트를 개발 프로세스에 내재화합니다. 이전에도 헬스케어 스타트업에서 비슷하게 새 도메인을 3개월 만에 학습한 경험이 있습니다.',
        key_points: ['솔직한 인정', '구체적 학습 계획', '전문가 활용']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: ['금융 서비스 도메인 경험이 없으신 것으로 보이는데, 핀테크의 특수한 규제와 요구사항을 어떻게 빠르게 학습하실 계획인가요에 대해 설명해 주시실 건가요?', '이 주제에 대한 경험이나 생각을 공유해 주세요.']
    },
    {
      id: 25,
      category: 'risk_flags',
      difficulty: 'Hard',
      title: 'Kubernetes 경험 갭 확인',
      is_risk: true,
      risk_source: 'GitHub 분석에서 K8s manifest, Helm chart 등 Kubernetes 관련 코드가 발견되지 않음. Docker 경험만 확인.',
      question_text: '이력서에 클라우드 인프라 운영 경험을 언급하셨는데, GitHub에서 Kubernetes 관련 코드가 보이지 않습니다. Kubernetes 실무 경험 수준을 솔직하게 말씀해주시겠습니까?',
      context_bridge: '저희는 Kubernetes 기반으로 인프라를 운영할 계획이며, CTO가 이를 주도해야 합니다.',
      why_matters: '이력서와 실제 역량의 불일치를 직접 확인합니다. 솔직함과 학습 계획을 테스트합니다.',
      listen_for: '솔직한 수준 인정, Docker와 K8s의 차이 이해, 갭을 메울 구체적 계획.',
      code_reference: null,
      terminology: [
        {
          term: 'Kubernetes (K8s)',
          pronunciation: '쿠버네티스',
          explanation: '컨테이너를 자동으로 관리해주는 도구. 수십 개의 서버를 하나처럼 운영할 수 있게 합니다.',
          definition: '컨테이너를 자동으로 관리해주는 도구. 수십 개의 서버를 하나처럼 운영할 수 있게 합니다.',
          plain_language: '컨테이너를 자동으로 관리해주는 도구. 수십 개의 서버를 하나처럼 운영할 수 있게 합니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Docker',
          pronunciation: '도커',
          explanation: '프로그램을 격리된 환경에서 실행하는 기술. 컨테이너를 만드는 도구입니다.',
          definition: '프로그램을 격리된 환경에서 실행하는 기술. 컨테이너를 만드는 도구입니다.',
          plain_language: '프로그램을 격리된 환경에서 실행하는 기술. 컨테이너를 만드는 도구입니다.',
          context: '면접 전반에서 사용되는 용어'
        },
        {
          term: 'Container',
          pronunciation: '컨테이너',
          explanation: '프로그램과 실행 환경을 하나로 묶은 패키지. 어디서든 동일하게 실행됩니다.'
        },
        {
          term: 'Helm Chart',
          pronunciation: '헬름 차트',
          explanation: 'Kubernetes 애플리케이션을 쉽게 배포하기 위한 패키지 관리 도구입니다.'
        },
        {
          term: 'Manifest',
          pronunciation: '매니페스트',
          explanation: 'Kubernetes에 배포할 리소스를 정의한 설정 파일입니다.'
        },
        {
          term: 'Pod',
          pronunciation: '파드',
          explanation: 'Kubernetes에서 가장 작은 배포 단위. 하나 이상의 컨테이너를 포함합니다.'
        },
        {
          term: 'Cluster',
          pronunciation: '클러스터',
          explanation: '여러 서버를 하나로 묶은 그룹. Kubernetes가 관리하는 서버들의 집합입니다.'
        },
        {
          term: 'EKS',
          pronunciation: '이케이에스',
          explanation: 'Amazon Elastic Kubernetes Service. AWS에서 제공하는 관리형 Kubernetes 서비스입니다.'
        }
      ],
      answer_keywords: [
        {
          keyword: '솔직한 수준 인정',
          importance: 'must',
          explanation: 'Docker는 사용하지만 K8s 실무 경험은 부족하다는 솔직함'
        },
        {
          keyword: 'Docker와 K8s 차이 이해',
          importance: 'must',
          explanation: 'Docker는 컨테이너 생성, K8s는 컨테이너 오케스트레이션이라는 구분'
        },
        {
          keyword: '학습/보완 계획',
          importance: 'good_to_have',
          explanation: '교육, 외부 전문가, 관리형 서비스 활용 등 구체적 보완책'
        }
      ],
      scenarios: [
        {
          level: 'Expert',
          score: 25,
          text: 'Docker 경험은 있지만 K8s는 학습 단계라고 솔직히 인정. 관리형 서비스(EKS) 활용 + 외부 전문가 영입 + 본인 학습 계획의 3트랙 전략 제시.',
          depth_expectations: '구체적 수치와 사례를 들어 단계적 접근법을 설명. 트레이드오프를 인식하고 비즈니스 맥락을 연결.'
        },
        {
          level: 'Mid',
          score: 12,
          text: 'K8s를 조금 써봤다고 하지만 구체적 경험이 모호. 학습 의지는 있음.',
          depth_expectations: '기본 개념은 이해하나 구체적 경험이나 수치가 부족. 추가 질문으로 깊이 확인 필요.'
        },
        {
          level: 'Low',
          score: -5,
          text: 'K8s 경험이 있다고 과장하거나, Docker와 K8s의 차이를 설명하지 못함.',
          depth_expectations: '핵심 개념에 대한 이해 부족. 실무 경험이 없거나 준비가 부족한 상태.'
        }
      ],
      follow_ups: [
        {
          id: 'q25-f1',
          trigger: 'Expert',
          question_text: 'K8s 도입 초기에 관리형 서비스(EKS)와 자체 클러스터 구축 중 어떤 것을 선택하시겠습니까?',
          why_matters: '현실적 판단력.',
          listen_for: '팀 역량 고려, 관리 부담, 비용.',
          good: {
            text: '팀 K8s 경험이 부족하므로 EKS로 시작하여 관리 부담을 줄이고, 경험이 쌓이면 커스터마이징.',
            score: 10
          },
          poor: {
            text: '자체 구축이 더 좋다고 근거 없이 주장.',
            score: 0
          }
        },
        {
          id: 'q25-f2',
          trigger: 'Mid',
          question_text: 'Docker Compose로 운영하다가 Kubernetes로 전환해야 하는 시점은 언제라고 생각하시나요?',
          why_matters: '전환 시점 판단 능력.',
          listen_for: '서비스 수, 트래픽 규모, 배포 빈도 등 기준.',
          good: {
            text: '서비스 10개 이상, 배포 하루 수 회 이상일 때 등 구체적 기준 제시.',
            score: 5
          },
          poor: {
            text: '처음부터 K8s를 써야 한다.',
            score: -3
          }
        },
        {
          id: 'q25-f3',
          trigger: 'Low',
          question_text: 'Docker와 Kubernetes의 차이를 설명해주실 수 있나요?',
          why_matters: '기본 개념 이해 확인.',
          listen_for: 'Docker=컨테이너 생성, K8s=컨테이너 관리/오케스트레이션.',
          good: {
            text: 'Docker는 상자를 만들고, K8s는 상자들을 관리한다는 비유로 구분.',
            score: 5
          },
          poor: {
            text: '비슷한 것이라고 답변.',
            score: 0
          }
        }
      ],
      interviewer_note: {
        business_interpretation: '이 질문은 이력서에 적힌 것과 실제 역량이 일치하는지 확인합니다. Kubernetes 경험이 부족한 것 자체보다, 이를 솔직히 인정하고 보완할 계획이 있느냐가 핵심입니다.',
        daily_analogy: '운전면허가 있지만 수동 기어 경험이 없는 것과 같습니다. 자동 기어(Docker)는 능숙하지만, 수동 기어(K8s)는 별도로 배워야 합니다. 솔직히 인정하고 연습 계획을 세우는 것이 인정받는 길입니다.',
        level_expectation: 'CTO 수준에서는 모든 기술을 알 필요는 없지만, 모르는 것을 솔직히 인정하고 보완하는 전략이 있어야 합니다. K8s는 관리형 서비스와 전문가 영입으로 보완 가능합니다.'
      },
      expected_answer: {
        core: '• 솔직한 인정: Docker는 능숙하지만 K8s는 학습 수준\n• 차이 인식: Docker=컨테이너 생성, K8s=컨테이너 오케스트레이션(자동 관리, 스케일링, 복구)\n• 보완 전략: EKS(관리형) 활용 + DevOps 전문가 채용 + 본인 90일 학습 계획',
        example: '솔직히 말씀드리면, Docker는 3년 이상 실무에서 사용했지만 Kubernetes는 개인 프로젝트에서 minikube로 실습한 수준입니다. 프로덕션 K8s 운영 경험은 없습니다. 제 보완 전략은 3가지입니다. 첫째, AWS EKS를 사용하여 클러스터 관리 부담을 줄입니다. 직접 클러스터를 구축하는 것보다 관리형 서비스가 초기에 현실적입니다. 둘째, K8s 프로덕션 운영 경험이 있는 DevOps 엔지니어를 첫 달에 채용합니다. 셋째, 저도 CKA(Kubernetes 공인 자격증) 취득을 목표로 90일 학습 계획을 세우고 있습니다.',
        key_points: ['솔직한 인정', '관리형 서비스 활용', '전문가 채용']
      },
      jd_competency_link: 'JD 요구사항 연결',
      generation_rationale: '후보자 프로필 기반 질문 생성',
      skills_assessed: ['general'],
      alternative_phrasings: [
        '이력서에 클라우드 인프라 운영 경험을 언급하셨는데, GitHub에서 Kubernetes 관련 코드가 보이지 않습니다. Kubernetes 실무 경험 수준을 솔직하게 말씀해주시겠습니까에 대해 설명해 주시실 건가요?',
        '이 주제에 대한 경험이나 생각을 공유해 주세요.'
      ]
    }
  ]
};
