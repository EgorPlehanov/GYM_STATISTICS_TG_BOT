/*
КОЭФФИЦИЕНТ КЭШИРОВАНИЯ ИНДЕКСОВ (INDEX CACHE HIT RATE)

Данный коэффициент похож на обычный коэффициент кэширования, но рассчитывается на данных использования индексов.
*/
SELECT sum(idx_blks_read) as idx_read,
       sum(idx_blks_hit)  as idx_hit,
       (sum(idx_blks_hit) - sum(idx_blks_read)) / sum(idx_blks_hit) as ratio
FROM pg_statio_user_indexes;