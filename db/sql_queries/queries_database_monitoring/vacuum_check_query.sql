/*
ПРОВЕРКА ЗАПУСКОВ VACUUM

Раздувание можно уменьшить с помощью команды VACUUM, но также PostgreSQL поддерживает AUTOVACUUM. О его настройке можно прочитать тут.
*/
SELECT relname, 
       last_vacuum, 
       last_autovacuum 
FROM pg_stat_user_tables;