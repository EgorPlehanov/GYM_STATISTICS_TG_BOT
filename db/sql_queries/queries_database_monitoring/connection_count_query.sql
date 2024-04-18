/*
КОЛИЧЕСТВО ОТКРЫТЫХ ПОДКЛЮЧЕНИЙ

Показывает открытые подключения ко всем базам данных в вашем экземпляре PostgreSQL. Если у вас несколько баз данных в одном PostgreSQL, то в условие WHERE стоит добавить datname = 'Ваша_база_данных'.
*/
SELECT COUNT(*) as connections,
       backend_type
FROM pg_stat_activity
where state = 'active' OR state = 'idle'
GROUP BY backend_type
ORDER BY connections DESC;