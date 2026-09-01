-- MedSlime persistent game-state MVP
-- Run once in Supabase SQL Editor. Safe to run again.

create table if not exists public.player_game_state (
    user_key text primary key,
    coins integer not null default 520 check (coins >= 0),
    tickets integer not null default 0 check (tickets >= 0),
    streak integer not null default 0 check (streak >= 0),
    selected_slime text not null default '綠色史萊姆',
    gacha_pity integer not null default 0 check (gacha_pity >= 0),
    gacha_free_date date,
    gacha_pull_count integer not null default 0 check (gacha_pull_count >= 0),
    focus_seconds_total bigint not null default 0 check (focus_seconds_total >= 0),
    focus_seconds_today bigint not null default 0 check (focus_seconds_today >= 0),
    focus_coins_today integer not null default 0 check (focus_coins_today >= 0),
    updated_at timestamptz not null default now()
);

create table if not exists public.player_slimes (
    user_key text not null,
    slime_name text not null,
    owned boolean not null default false,
    fragments integer not null default 0 check (fragments >= 0),
    accessory_unlocked boolean not null default false,
    accessory_equipped boolean not null default false,
    nickname text,
    acquired_order integer,
    acquired_at timestamptz,
    updated_at timestamptz not null default now(),
    primary key (user_key, slime_name)
);

alter table public.player_slimes
    add column if not exists accessory_equipped boolean not null default false;

create index if not exists player_slimes_user_key_idx
    on public.player_slimes (user_key);

-- Prototype only: there is not yet an authenticated account id.
-- The app uses a random player key kept in the URL so refreshes can restore the same data.
-- Replace user_key + these prototype grants with auth.uid()-based RLS when login is implemented.
alter table public.player_game_state disable row level security;
alter table public.player_slimes disable row level security;

grant select, insert, update on table public.player_game_state to anon, authenticated;
grant select, insert, update on table public.player_slimes to anon, authenticated;

comment on table public.player_game_state is
'MedSlime MVP player resources, gacha state and focus counters. user_key is temporary until authentication exists.';
comment on table public.player_slimes is
'MedSlime MVP per-slime ownership, fragments, accessory unlock and nickname state.';
