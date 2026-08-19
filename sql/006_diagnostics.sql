select
  count(*) as total_rows,
  count(distinct chunk_id) as unique_chunk_ids
from guideline_chunks;

select chunk_id, count(*) as duplicates
from guideline_chunks
group by chunk_id
having count(*) > 1
order by duplicates desc
limit 50;
