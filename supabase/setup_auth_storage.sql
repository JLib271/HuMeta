-- Apply once in the Supabase SQL Editor. The Streamlit app must use the
-- publishable/anon key in SUPABASE_KEY; never use a service-role key here.

alter table public.studies
    add column if not exists user_id uuid references auth.users(id) on delete cascade;

alter table public.studies enable row level security;

drop policy if exists "Researchers read their studies" on public.studies;
create policy "Researchers read their studies"
    on public.studies for select to authenticated
    using (user_id = (select auth.uid()));

drop policy if exists "Researchers create their studies" on public.studies;
create policy "Researchers create their studies"
    on public.studies for insert to authenticated
    with check (user_id = (select auth.uid()));

drop policy if exists "Researchers update their studies" on public.studies;
create policy "Researchers update their studies"
    on public.studies for update to authenticated
    using (user_id = (select auth.uid()))
    with check (user_id = (select auth.uid()));

drop policy if exists "Researchers delete their studies" on public.studies;
create policy "Researchers delete their studies"
    on public.studies for delete to authenticated
    using (user_id = (select auth.uid()));

alter table public.variables enable row level security;

create table if not exists public.study_module2_plans (
    study_id uuid primary key references public.studies(id) on delete cascade,
    owner_id uuid not null references auth.users(id) on delete cascade,
    plan_json jsonb not null,
    updated_at timestamptz not null default now()
);

create index if not exists study_module2_plans_owner_idx
    on public.study_module2_plans (owner_id, updated_at desc);

create table if not exists public.study_discovery (
    study_id uuid primary key references public.studies(id) on delete cascade,
    owner_id uuid not null references auth.users(id) on delete cascade,
    study_title text not null,
    context_tags text[] not null default '{}',
    study_metadata jsonb not null default '{}'::jsonb,
    published_at timestamptz not null default now()
);

create index if not exists study_discovery_context_tags_idx
    on public.study_discovery using gin (context_tags);

alter table public.study_discovery enable row level security;
revoke all on public.study_discovery from anon, public;
grant select, insert, update, delete on public.study_discovery to authenticated;

drop policy if exists "Researchers read shared study summaries" on public.study_discovery;
create policy "Researchers read shared study summaries"
    on public.study_discovery for select to authenticated
    using (true);

drop policy if exists "Researchers publish their study summaries" on public.study_discovery;
create policy "Researchers publish their study summaries"
    on public.study_discovery for insert to authenticated
    with check (
        owner_id = (select auth.uid())
        and exists (
            select 1 from public.studies s
            where s.id = study_discovery.study_id
              and s.user_id = (select auth.uid())
        )
    );

drop policy if exists "Researchers update their shared study summaries" on public.study_discovery;
create policy "Researchers update their shared study summaries"
    on public.study_discovery for update to authenticated
    using (owner_id = (select auth.uid()))
    with check (
        owner_id = (select auth.uid())
        and exists (
            select 1 from public.studies s
            where s.id = study_discovery.study_id
              and s.user_id = (select auth.uid())
        )
    );

drop policy if exists "Researchers unpublish their study summaries" on public.study_discovery;
create policy "Researchers unpublish their study summaries"
    on public.study_discovery for delete to authenticated
    using (owner_id = (select auth.uid()));

alter table public.study_module2_plans enable row level security;
revoke all on public.study_module2_plans from anon, public;
grant select, insert, update, delete on public.study_module2_plans to authenticated;

drop policy if exists "Researchers read their Module 2 plans" on public.study_module2_plans;
create policy "Researchers read their Module 2 plans"
    on public.study_module2_plans for select to authenticated
    using (
        owner_id = (select auth.uid())
        and exists (
            select 1 from public.studies s
            where s.id = study_module2_plans.study_id
              and s.user_id = (select auth.uid())
        )
    );

drop policy if exists "Researchers create their Module 2 plans" on public.study_module2_plans;
create policy "Researchers create their Module 2 plans"
    on public.study_module2_plans for insert to authenticated
    with check (
        owner_id = (select auth.uid())
        and exists (
            select 1 from public.studies s
            where s.id = study_module2_plans.study_id
              and s.user_id = (select auth.uid())
        )
    );

drop policy if exists "Researchers update their Module 2 plans" on public.study_module2_plans;
create policy "Researchers update their Module 2 plans"
    on public.study_module2_plans for update to authenticated
    using (
        owner_id = (select auth.uid())
        and exists (
            select 1 from public.studies s
            where s.id = study_module2_plans.study_id
              and s.user_id = (select auth.uid())
        )
    )
    with check (
        owner_id = (select auth.uid())
        and exists (
            select 1 from public.studies s
            where s.id = study_module2_plans.study_id
              and s.user_id = (select auth.uid())
        )
    );

drop policy if exists "Researchers delete their Module 2 plans" on public.study_module2_plans;
create policy "Researchers delete their Module 2 plans"
    on public.study_module2_plans for delete to authenticated
    using (
        owner_id = (select auth.uid())
        and exists (
            select 1 from public.studies s
            where s.id = study_module2_plans.study_id
              and s.user_id = (select auth.uid())
        )
    );

revoke all on public.studies, public.variables from anon, public;
grant select, insert, update, delete
    on public.studies, public.variables
    to authenticated;

drop policy if exists "Researchers read variables in their studies" on public.variables;
create policy "Researchers read variables in their studies"
    on public.variables for select to authenticated
    using (
        exists (
            select 1 from public.studies s
            where s.id = variables.study_id
              and s.user_id = (select auth.uid())
        )
    );

drop policy if exists "Researchers manage variables in their studies" on public.variables;
create policy "Researchers manage variables in their studies"
    on public.variables for all to authenticated
    using (
        exists (
            select 1 from public.studies s
            where s.id = variables.study_id
              and s.user_id = (select auth.uid())
        )
    )
    with check (
        exists (
            select 1 from public.studies s
            where s.id = variables.study_id
              and s.user_id = (select auth.uid())
        )
    );

create table if not exists public.study_datasets (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    dataset_title text not null,
    file_name text not null,
    object_path text not null unique,
    bucket_id text not null check (bucket_id in ('study-datasets', 'public-study-datasets')),
    access_level text not null check (access_level in ('private', 'public')),
    row_count bigint not null check (row_count >= 0),
    column_count integer not null check (column_count >= 0),
    byte_size bigint not null check (byte_size >= 0),
    created_at timestamptz not null default now(),
    constraint dataset_bucket_access_match check (
        (access_level = 'private' and bucket_id = 'study-datasets')
        or (access_level = 'public' and bucket_id = 'public-study-datasets')
    )
);

create index if not exists study_datasets_owner_created_idx
    on public.study_datasets (owner_id, created_at desc);
create index if not exists study_datasets_public_created_idx
    on public.study_datasets (created_at desc)
    where access_level = 'public';

alter table public.study_datasets enable row level security;
revoke all on public.study_datasets from anon, public;
grant select, insert, update, delete on public.study_datasets to authenticated;

drop policy if exists "Owners and public can read dataset records" on public.study_datasets;
create policy "Owners and public can read dataset records"
    on public.study_datasets for select to authenticated
    using (owner_id = (select auth.uid()) or access_level = 'public');

drop policy if exists "Researchers create their dataset records" on public.study_datasets;
create policy "Researchers create their dataset records"
    on public.study_datasets for insert to authenticated
    with check (
        owner_id = (select auth.uid())
        and (
            (access_level = 'private' and bucket_id = 'study-datasets')
            or (access_level = 'public' and bucket_id = 'public-study-datasets')
        )
    );

drop policy if exists "Researchers update their dataset records" on public.study_datasets;
create policy "Researchers update their dataset records"
    on public.study_datasets for update to authenticated
    using (owner_id = (select auth.uid()))
    with check (owner_id = (select auth.uid()));

drop policy if exists "Researchers delete their dataset records" on public.study_datasets;
create policy "Researchers delete their dataset records"
    on public.study_datasets for delete to authenticated
    using (owner_id = (select auth.uid()));

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
    ('study-datasets', 'study-datasets', false, 52428800, array['text/csv']),
    ('public-study-datasets', 'public-study-datasets', true, 52428800, array['text/csv'])
on conflict (id) do update
set public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Owners upload study dataset objects" on storage.objects;
create policy "Owners upload study dataset objects"
    on storage.objects for insert to authenticated
    with check (
        bucket_id in ('study-datasets', 'public-study-datasets')
        and (storage.foldername(name))[1] = (select auth.uid())::text
    );

drop policy if exists "Owners and authorized public records read dataset objects" on storage.objects;
create policy "Owners and authorized public records read dataset objects"
    on storage.objects for select to authenticated
    using (
        (
            bucket_id = 'study-datasets'
            and (storage.foldername(name))[1] = (select auth.uid())::text
        )
        or (
            bucket_id = 'public-study-datasets'
            and exists (
                select 1 from public.study_datasets d
                where d.object_path = storage.objects.name
                  and d.bucket_id = storage.objects.bucket_id
                  and (d.owner_id = (select auth.uid()) or d.access_level = 'public')
            )
        )
    );

drop policy if exists "Owners delete their dataset objects" on storage.objects;
create policy "Owners delete their dataset objects"
    on storage.objects for delete to authenticated
    using (
        bucket_id in ('study-datasets', 'public-study-datasets')
        and (storage.foldername(name))[1] = (select auth.uid())::text
    );
