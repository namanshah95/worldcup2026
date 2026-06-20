import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL || '';
const key = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const supabase = url && key ? createClient(url, key) : null;

export function subscribeToScoreUpdates(onUpdate: () => void) {
  if (!supabase) return () => {};
  const channel = supabase
    .channel('score-updates')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'score_events' }, () => onUpdate())
    .subscribe();
  return () => {
    supabase.removeChannel(channel);
  };
}
