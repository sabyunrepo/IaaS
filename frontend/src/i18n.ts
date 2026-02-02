import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  ko: {
    translation: {
      app_title: 'Vantict Sniper',
      login: '로그인',
      logout: '로그아웃',
      jobs: 'Job 목록',
      create_job: 'Job 생성',
      status: '상태',
      loading: '로딩 중...',
      login_with_google: 'Google로 로그인',
      login_with_github: 'GitHub으로 로그인',
      jd_placeholder: '채용공고(JD)를 입력하세요...',
      submit: '제출',
      no_jobs: 'Job이 없습니다.',
    },
  },
  en: {
    translation: {
      app_title: 'Vantict Sniper',
      login: 'Login',
      logout: 'Logout',
      jobs: 'Jobs',
      create_job: 'Create Job',
      status: 'Status',
      loading: 'Loading...',
      login_with_google: 'Login with Google',
      login_with_github: 'Login with GitHub',
      jd_placeholder: 'Enter job description...',
      submit: 'Submit',
      no_jobs: 'No jobs found.',
    },
  },
}

i18n.use(initReactI18next).init({
  resources,
  lng: 'ko',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

export default i18n
