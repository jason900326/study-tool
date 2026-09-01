-- MedSlime minimal Supabase Auth + RLS migration
-- Run AFTER the existing game/task/achievement/focus SQL files.
-- Safe to run again. Existing prototype rows are kept, but rows without user_id become inaccessible under RLS.

-- 1) Bind every private row to auth.users.id.
alter table if exists public.player_game_state
    add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table if exists public.player_slimes
    add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table if exists public.achievement_claims
    add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table if exists public.player_task_events
    add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table if exists public.player_task_claims
    add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table if exists public.player_task_quiz_events
    add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table if exists public.focus_sessions
    add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table if exists public.mistakes
    add column if not exists user_id uuid references auth.users(id) on delete cascade;

-- Helpful user-scoped indexes for the future web frontend.
create unique index if not exists player_game_state_user_id_uidx on public.player_game_state(user_id) where user_id is not null;
create unique index if not exists player_slimes_user_slime_uidx on public.player_slimes(user_id, slime_name) where user_id is not null;
create unique index if not exists achievement_claims_user_achievement_uidx on public.achievement_claims(user_id, achievement_id) where user_id is not null;
create unique index if not exists task_events_user_date_uidx on public.player_task_events(user_id, event_date) where user_id is not null;
create unique index if not exists task_claims_user_period_task_uidx on public.player_task_claims(user_id, period_type, period_key, task_id) where user_id is not null;
create unique index if not exists task_quiz_user_token_uidx on public.player_task_quiz_events(user_id, quiz_token) where user_id is not null;
create unique index if not exists focus_sessions_user_token_uidx on public.focus_sessions(user_id, session_token) where user_id is not null;
create index if not exists mistakes_user_created_idx on public.mistakes(user_id, created_at desc);

-- 2) Turn RLS on. Public national_exam_questions is intentionally NOT changed.
alter table if exists public.player_game_state enable row level security;
alter table if exists public.player_slimes enable row level security;
alter table if exists public.achievement_claims enable row level security;
alter table if exists public.player_task_events enable row level security;
alter table if exists public.player_task_claims enable row level security;
alter table if exists public.player_task_quiz_events enable row level security;
alter table if exists public.focus_sessions enable row level security;
alter table if exists public.mistakes enable row level security;

-- 3) Remove prototype anon access. Authenticated users keep table privileges;
-- RLS below decides which rows they can see/change.
revoke all on table public.player_game_state from anon;
revoke all on table public.player_slimes from anon;
revoke all on table public.achievement_claims from anon;
revoke all on table public.player_task_events from anon;
revoke all on table public.player_task_claims from anon;
revoke all on table public.player_task_quiz_events from anon;
revoke all on table public.focus_sessions from anon;
revoke all on table public.mistakes from anon;

grant select, insert, update, delete on table public.player_game_state to authenticated;
grant select, insert, update, delete on table public.player_slimes to authenticated;
grant select, insert, update, delete on table public.achievement_claims to authenticated;
grant select, insert, update, delete on table public.player_task_events to authenticated;
grant select, insert, update, delete on table public.player_task_claims to authenticated;
grant select, insert, update, delete on table public.player_task_quiz_events to authenticated;
grant select, insert, update, delete on table public.focus_sessions to authenticated;
grant select, insert, update, delete on table public.mistakes to authenticated;
grant usage, select on all sequences in schema public to authenticated;

-- 4) One reusable rule per table: auth.uid() must equal row.user_id.
drop policy if exists "player_game_state_own_rows" on public.player_game_state;
create policy "player_game_state_own_rows" on public.player_game_state
    for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "player_slimes_own_rows" on public.player_slimes;
create policy "player_slimes_own_rows" on public.player_slimes
    for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "achievement_claims_own_rows" on public.achievement_claims;
create policy "achievement_claims_own_rows" on public.achievement_claims
    for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "player_task_events_own_rows" on public.player_task_events;
create policy "player_task_events_own_rows" on public.player_task_events
    for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "player_task_claims_own_rows" on public.player_task_claims;
create policy "player_task_claims_own_rows" on public.player_task_claims
    for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "player_task_quiz_events_own_rows" on public.player_task_quiz_events;
create policy "player_task_quiz_events_own_rows" on public.player_task_quiz_events
    for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "focus_sessions_own_rows" on public.focus_sessions;
create policy "focus_sessions_own_rows" on public.focus_sessions
    for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "mistakes_own_rows" on public.mistakes;
create policy "mistakes_own_rows" on public.mistakes
    for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

comment on column public.player_game_state.user_id is 'Authenticated owner. Canonical identity for the future web frontend.';
