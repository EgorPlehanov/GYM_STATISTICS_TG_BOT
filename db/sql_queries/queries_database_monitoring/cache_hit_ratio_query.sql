/*
КОЭФФИЦИЕНТ КЭШИРОВАНИЯ (CACHE HIT RATIO)

Коэффициент кэширования - это показатель эффективности чтения, измеряемый долей операций чтения из кэша по сравнению с общим количеством операций чтения как с диска, так и из кэша. За исключением случаев использования хранилища данных, идеальный коэффициент кэширования составляет 99% или выше, что означает, что по крайней мере 99% операций чтения выполняются из кэша и не более 1% - с диска.

hits / (hits + reads) * 100%
*/
SELECT sum(heap_blks_read) as heap_read,
       sum(heap_blks_hit)  as heap_hit,
       sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM 
  pg_statio_user_tables;  