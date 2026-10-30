import { Check, CircleHelp, Info, Sparkles } from 'lucide-react'
import type { ReactNode } from 'react'
import type { MatchResult } from '../types'
import { computedAtLabel, scoreLabel, scoreValue } from '../format'
export function SkillTags({ skills, missing = false }: { skills: string[]; missing?: boolean }) {
  return <div className={'match-tags' + (missing ? ' match-tags--missing' : '')}>{skills.length ? skills.map((skill, index) => <span key={skill + index}>{skill}</span>) : <span className="match-tags__empty">{missing ? 'Không ghi nhận kỹ năng còn thiếu' : 'Chưa ghi nhận kỹ năng phù hợp'}</span>}</div>
}
export function MatchSummary({ match }: { match: MatchResult }) {
  return <><div className="match-skill-group"><h3><Check size={15} />Kỹ năng phù hợp <span>({match.matched_skills.length})</span></h3><SkillTags skills={match.matched_skills} /></div>
    <div className="match-skill-group match-skill-group--missing"><h3><CircleHelp size={15} />Kỹ năng cần bổ sung <span>({match.missing_skills.length})</span></h3><SkillTags skills={match.missing_skills} missing /></div>
    <p className="match-explanation"><Sparkles size={17} aria-hidden="true" /><span>{match.explanation || 'Chưa có giải thích cho kết quả này.'}</span></p></>
}
export function MatchPanel({ match, title, subtitle, children, actions }: { match: MatchResult; title: string; subtitle?: string; children?: ReactNode; actions?: ReactNode }) {
  const value = scoreValue(match.score)
  const components = [['Kỹ năng', match.skill_score], ['Kinh nghiệm', match.experience_score], ['Độ liên quan nội dung', match.semantic_score]] as const
  return <section className="match-panel" aria-label="Chi tiết mức độ phù hợp"><div className="match-panel__head"><span className="eyebrow">PHÂN TÍCH MỨC ĐỘ PHÙ HỢP</span><h2>{title}</h2>{subtitle && <p className="muted">{subtitle}</p>}</div>
    <div className="match-score-overview"><div className="match-ring" style={{ background: 'conic-gradient(var(--match-teal) ' + (value ?? 0) * 3.6 + 'deg, var(--match-soft) 0deg)' }}><strong>{scoreLabel(match.score)}</strong></div><div><h3>Điểm phù hợp</h3><p>Dựa trên kết quả matching của hệ thống</p></div></div>
    {children}
    <div className="match-bars"><h3>Điểm thành phần</h3>{components.map(([label, score]) => <div key={label}><div><span>{label}</span><strong>{scoreLabel(score)}</strong></div>{scoreValue(score) !== null && <progress max={100} value={scoreValue(score)!} aria-label={label} />}</div>)}</div>
    <MatchSummary match={match} />
    <p className="match-disclaimer"><Info size={17} /><span>Điểm phù hợp mang tính tham khảo, không đảm bảo kết quả tuyển dụng. Kỹ năng chưa ghi nhận không đồng nghĩa với việc ứng viên không có kỹ năng đó.</span></p>
    <p className="match-computed">Tính lúc: {computedAtLabel(match.computed_at)}</p>{actions && <div className="match-panel__actions">{actions}</div>}
  </section>
}
