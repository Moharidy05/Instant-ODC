-- Optional cleanup. Run sql/006_diagnostics.sql first and use this only if
-- duplicate chunk_id rows exist. Keeps the newest row per chunk_id.

with ranked as (
  select
    id,
    row_number() over (
      partition by chunk_id
      order by created_at desc nulls last, id desc
    ) as row_rank
  from guideline_chunks
)
delete from guideline_chunks
where id in (
  select id
  from ranked
  where row_rank > 1
);
