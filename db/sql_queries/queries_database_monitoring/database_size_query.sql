/*
РАЗМЕР БАЗ ДАННЫХ

После запуска запроса вы получите информацию о размере всех баз данных, созданных в рамках вашего экземпляра PostgreSQL.
*/
SELECT pg_database.datname,
       pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
where pg_database.datname = 'training_stat_bot'
ORDER BY pg_database_size(pg_database.datname) DESC;