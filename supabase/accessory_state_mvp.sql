-- MedSlime exclusive-accessory equip state MVP
-- Run once in Supabase SQL Editor. Safe to run again.

alter table public.player_slimes
    add column if not exists accessory_equipped boolean not null default false;

comment on column public.player_slimes.accessory_equipped is
'Whether this slime currently has its exclusive cosmetic accessory equipped.';
