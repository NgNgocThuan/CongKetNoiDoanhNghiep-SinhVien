import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/lib/http';
import { rows, obj, text } from './api';
import { useRead } from './hooks';
import { LoadingError, Notice } from './ui';
import { errorText } from './messages';

export default function SkillPicker({ value, onChange, initialNames = {} }: { value: string[]; onChange: (ids: string[]) => void; initialNames?: Record<string, string> }) {
  const [query, setQuery] = useState('');
  const [known, setKnown] = useState<Record<string, string>>(initialNames);
  const client = useQueryClient();
  const q = useRead(`/catalog/skills?page=1&size=100&q=${encodeURIComponent(query)}`);
  const catalog = rows(obj(q.data).items);
  const add = (id: string, name: string) => {
    setKnown(previous => ({ ...previous, [id]: name }));
    if (!value.includes(id)) onChange([...value, id]);
    setQuery('');
  };
  const create = useMutation({
    mutationFn: async (name: string) => obj((await http.post('/catalog/skill-tags', { name })).data),
    onSuccess: skill => { add(text(skill.id), text(skill.name)); void client.invalidateQueries({ queryKey: ['freelancer'] }); },
  });
  function choose() {
    const name = query.trim();
    if (!name || create.isPending) return;
    const match = catalog.find(s => text(s.name).toLocaleLowerCase() === name.toLocaleLowerCase());
    if (match) add(text(match.id), text(match.name)); else create.mutate(name);
  }
  return <div className="ux-skills">
    <h3>Kỹ năng cần có</h3>
    <div className="ux-tags">{value.map(id => <span className="ux-tag" key={id}>
      {known[id] ?? text(catalog.find(s => text(s.id) === id)?.name, `Kỹ năng #${id}`)}
      <button type="button" aria-label={`Xóa ${known[id] ?? text(catalog.find(s => text(s.id) === id)?.name, id)}`} onClick={() => onChange(value.filter(v => v !== id))}>×</button>
    </span>)}</div>
    <input aria-label="Tìm hoặc thêm kỹ năng" placeholder="Nhập kỹ năng, nhấn Enter hoặc dấu phẩy để thêm" value={query} maxLength={100}
      disabled={create.isPending} onChange={e => setQuery(e.target.value)} onKeyDown={e => {
        if (!e.nativeEvent.isComposing && (e.key === 'Enter' || e.key === ',')) { e.preventDefault(); choose(); }
      }} />
    <LoadingError query={q} />
    {create.isError && <Notice danger>{errorText(create.error)}</Notice>}
    <div className="ux-suggestions">{catalog.filter(s => !value.includes(text(s.id))).slice(0, 12).map(s =>
      <button type="button" key={text(s.id)} onClick={() => add(text(s.id), text(s.name))}>{text(s.name)}</button>)}
      {query.trim() && !catalog.some(s => text(s.name).toLocaleLowerCase() === query.trim().toLocaleLowerCase()) &&
        <button type="button" disabled={create.isPending || q.isPending} onClick={choose}>+ Thêm mới “{query.trim()}”</button>}
    </div>
  </div>;
}
