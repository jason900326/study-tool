-- MedSlime daily / weekly task MVP
-- Run once in Supabase SQL Editor. Safe to run again.

create table if not exists public.player_task_events (
    user_key text not null,
    event_date date not null,
    answered_count integer not null default 0 check (answered_count >= 0),
    reviewed_count integer not null default 0 check (reviewed_count >= 0),
    focus_seconds integer not null default 0 check (focus_seconds >= 0),
    updated_at timestamptz not null default now(),
    primary key (user_key, event_date)
);

create table if not exists public.player_task_claims (
    user_key text not null,
    period_type text not null check (period_type in ('daily', 'weekly')),
    period_key text not null,
    task_id text not null,
    reward_type text not null check (reward_type in ('coins', 'tickets')),
    reward_amount integer not null check (reward_amount >= 0),
    claimed_at timestamptz not null default now(),
    primary key (user_key, period_type, period_key, task_id)
);

create table if not exists public.player_task_quiz_events (
    user_key text not null,
    quiz_token text not null,
    answered_count integer not null check (answered_count >= 0),
    recorded_at timestamptz not null default now(),
    primary key (user_key, quiz_token)
);

create index if not exists player_task_events_user_date_idx
    on public.player_task_events (user_key, event_date);
create index if not exists player_task_claims_user_period_idx
    on public.player_task_claims (user_key, period_type, period_key);

-- Prototype only. Replace with auth.uid()-based RLS after login is implemented.
alter table public.player_task_events disable row level security;
alter table public.player_task_claims disable row level security;
alter table public.player_task_quiz_events disable row level security;

grant select, insert, update on table public.player_task_events to anon, authenticated;
grant select, insert on table public.player_task_claims to anon, authenticated;
grant select, insert on table public.player_task_quiz_events to anon, authenticated;

comment on table public.player_task_events is
'MedSlime MVP daily activity counters used to derive daily and weekly task progress.';
comment on table public.player_task_claims is
'MedSlime MVP task reward claims. Composite primary key prevents duplicate claims.';
comment on table public.player_task_quiz_events is
'MedSlime MVP idempotency records so refreshing a result page does not count the same quiz twice.';
