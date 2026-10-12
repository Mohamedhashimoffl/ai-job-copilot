-- database schema
-- Run everything below in the Supabase SQL Editor on a fresh project so that u could get all specifications covered.

-- Extensions

create extension if not exists "uuid-ossp";
create extension if not exists vector;

 
-- Tables
 
create table users (
  id uuid primary key default uuid_generate_v4(),
  email text unique not null,
  created_at timestamptz default now()
);

create table resumes (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) on delete cascade,
  raw_text text not null,
  file_name text,
  embedding vector(768),
  uploaded_at timestamptz default now()
);

create table resume_chunks (
  id uuid primary key default uuid_generate_v4(),
  resume_id uuid references resumes(id) on delete cascade,
  chunk_text text not null,
  embedding vector(768)
);

create table job_postings (
  id uuid primary key default uuid_generate_v4(),
  title text not null,
  company text,
  description text not null,
  source_url text,
  embedding vector(768),
  created_at timestamptz default now()
);

create table applications (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) on delete cascade,
  job_id uuid references job_postings(id) on delete cascade,
  status text default 'draft',  
  applied_at timestamptz,
  created_at timestamptz default now()
);

create table matches (
  id uuid primary key default uuid_generate_v4(),
  resume_id uuid references resumes(id) on delete cascade,
  job_id uuid references job_postings(id) on delete cascade,
  score float,
  explanation text,
  strengths jsonb,
  gaps jsonb,
  created_at timestamptz default now(),
  constraint matches_resume_job_unique unique (resume_id, job_id)
);
 
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email)
  values (new.id, new.email);
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

 
-- Row Level Security
 
alter table users enable row level security;          
alter table resumes enable row level security;
alter table resume_chunks enable row level security;
alter table job_postings enable row level security;
alter table applications enable row level security;
alter table matches enable row level security;

-- resumes: owner only
create policy "Users can insert own resumes"
on resumes for insert
with check (auth.uid() = user_id);

create policy "Users can view own resumes"
on resumes for select
using (auth.uid() = user_id);

create policy "Users can update own resumes"
on resumes for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

-- resume_chunks: ownership inherited from the parent resume
create policy "Users can insert own resume chunks"
on resume_chunks for insert
with check (
  exists (select 1 from resumes
          where resumes.id = resume_chunks.resume_id
          and resumes.user_id = auth.uid())
);

create policy "Users can view own resume chunks"
on resume_chunks for select
using (
  exists (select 1 from resumes
          where resumes.id = resume_chunks.resume_id
          and resumes.user_id = auth.uid())
);

-- job_postings: shared data, anyone can read, signed-in users can add
create policy "Anyone can view job postings"
on job_postings for select
using (true);

create policy "Authenticated users can insert job postings"
on job_postings for insert
to authenticated
with check (true);

-- matches: ownership inherited from the parent resume
create policy "Users can manage own matches"
on matches for all
using (
  exists (select 1 from resumes
          where resumes.id = matches.resume_id
          and resumes.user_id = auth.uid())
)
with check (
  exists (select 1 from resumes
          where resumes.id = matches.resume_id
          and resumes.user_id = auth.uid())
);

-- applications: owner only
create policy "Users can manage own applications"
on applications for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
 

-- Rank jobs against one resume by cosine similarity
create or replace function match_jobs(resume_id uuid, match_count int default 5)
returns table(job_id uuid, title text, company text, similarity float)
language sql stable
as $$
  select
    job_postings.id,
    job_postings.title,
    job_postings.company,
    1 - (job_postings.embedding <=> resumes.embedding) as similarity
  from job_postings, resumes
  where resumes.id = resume_id
    and job_postings.embedding is not null
  order by job_postings.embedding <=> resumes.embedding
  limit match_count;
$$;

-- Find the resume chunks closest to a query embedding (used for RAG)
create or replace function match_resume_chunks(
  p_resume_id uuid, query_embedding vector(768), match_count int default 5
)
returns table(chunk_text text, similarity float)
language sql stable
as $$
  select
    resume_chunks.chunk_text,
    1 - (resume_chunks.embedding <=> query_embedding) as similarity
  from resume_chunks
  where resume_chunks.resume_id = p_resume_id
  order by resume_chunks.embedding <=> query_embedding
  limit match_count;
$$;