/**
 * DeepAnalysisTab - Radar Chart + Engineering DNA + Skill Matching Table
 */
import { memo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { DeepAnalysis } from '../../types/interview'
import { RadarChart, ProgressBarGroup } from '../charts'

interface DeepAnalysisTabProps {
  analysis: DeepAnalysis
}

export const DeepAnalysisTab = memo(function DeepAnalysisTab({ analysis }: DeepAnalysisTabProps) {
  const { t } = useTranslation()
  const { radar_candidate, radar_required, engineering_dna, risk_flags, skill_table, overall_match, score_sources, data_confidence, data_confidence_score } = analysis
  const [showSources, setShowSources] = useState(false)

  const radarLabels = [
    t('deep_role_fit'),
    t('deep_technical'),
    t('deep_execution'),
    t('deep_communication'),
    t('deep_code_quality')
  ]

  return (
    <div className="space-y-6">
      {/* Overall Match Score */}
      {overall_match !== undefined && (
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-indigo-100">{t('deep_overall_match')}</h3>
              <p className="text-2xl sm:text-4xl font-bold mt-1">{overall_match}%</p>
              {data_confidence && (
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-2 ${
                  data_confidence === 'high' ? 'bg-emerald-400/20 text-emerald-100'
                  : data_confidence === 'medium' ? 'bg-amber-400/20 text-amber-100'
                  : 'bg-red-400/20 text-red-100'
                }`}>
                  {t('data_confidence_label')}: {t(`data_confidence_${data_confidence}`)}
                  {data_confidence_score != null && ` (${data_confidence_score}%)`}
                </span>
              )}
            </div>
            <div className="text-6xl opacity-20">📊</div>
          </div>
        </div>
      )}

      {/* Radar Chart Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
          </svg>
          {t('deep_radar')}
        </h3>

        <div className="flex flex-col lg:flex-row items-center justify-center gap-8">
          <RadarChart
            candidateData={radar_candidate}
            requiredData={radar_required}
            size={320}
          />

          {/* Score breakdown */}
          <div className="space-y-3 w-full lg:w-auto">
            {radarLabels.map((label, i) => {
              const candidate = radar_candidate?.[i] ?? 0
              const required = radar_required?.[i] ?? 0
              const diff = candidate - required
              return (
                <div key={label} className="flex items-center gap-3">
                  <span className="w-28 text-sm text-gray-600">{label}</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${candidate}%` }}
                    />
                  </div>
                  <span className={`text-sm font-medium w-16 text-right ${
                    diff >= 0 ? 'text-emerald-600' : 'text-red-600'
                  }`}>
                    {candidate}
                    <span className="text-xs text-gray-400 ml-1">/ {required}</span>
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Score Sources (collapsible) */}
      {score_sources && score_sources.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <button
            onClick={() => setShowSources(prev => !prev)}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="text-sm font-semibold text-gray-900">{t('score_sources_title')}</span>
              <span className="text-xs text-gray-400">({score_sources.length})</span>
            </div>
            <svg className={`w-5 h-5 text-gray-400 transition-transform ${showSources ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {showSources && (
            <div className="px-4 pb-4 border-t border-gray-100">
              <p className="text-xs text-gray-500 mt-3 mb-3">{t('score_sources_desc')}</p>
              <div className="space-y-2">
                {score_sources.map((source, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-medium mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-gray-700 font-mono text-xs leading-relaxed">{source}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Engineering DNA */}
      {engineering_dna && engineering_dna.length > 0 && (
        <ProgressBarGroup
          title={t('engineering_dna')}
          items={engineering_dna.map(item => ({
            label: item.label,
            value: item.value,
            display: item.display,
            color: item.color,
            note: item.note,
            tooltip: item.tooltip
          }))}
        />
      )}

      {/* Risk Flags */}
      {risk_flags && risk_flags.length > 0 && (
        <div className="bg-red-50 rounded-xl border border-red-200 p-6">
          <h3 className="text-lg font-semibold text-red-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            {t('deep_risk_flags')}
          </h3>
          <div className="space-y-3">
            {risk_flags.map((flag, i) => (
              <div key={i} className="card-hover bg-white rounded-lg p-4 border border-red-200">
                <div className="font-medium text-red-900">{flag.label}</div>
                <div className="text-sm text-red-700 mt-1">{flag.detail}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Matching Table */}
      {skill_table && skill_table.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm overflow-hidden">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            {t('deep_skill_matching')}
          </h3>

          <div className="overflow-x-auto -mx-6">
            <table className="w-full min-w-[500px]">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('deep_jd_skill')}</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('deep_candidate_skill')}</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('deep_match_type')}</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('deep_evidence')}</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">{t('deep_confidence')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {skill_table.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{row.skill}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{row.candidate}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        row.type === 'exact' ? 'bg-emerald-100 text-emerald-800' :
                        row.type === 'similar' ? 'bg-blue-100 text-blue-800' :
                        row.type === 'partial' ? 'bg-amber-100 text-amber-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {row.type === 'exact' ? t('deep_match_exact') :
                         row.type === 'similar' ? t('deep_match_similar') :
                         row.type === 'partial' ? t('deep_match_partial') : t('deep_match_none')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{row.evidence}</td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              row.confidence >= 80 ? 'bg-emerald-500' :
                              row.confidence >= 60 ? 'bg-blue-500' :
                              row.confidence >= 40 ? 'bg-amber-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${row.confidence}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-700">{row.confidence}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
})
