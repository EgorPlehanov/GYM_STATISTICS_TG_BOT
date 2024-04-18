/*
РАЗМЕР ТАБЛИЧНЫХ ПРОСТРАНСТВ

После запуска запроса вы получите информацию о размере всех tablespace созданных в вашей БД.Функция pg_tablespace_size предоставляет информацию о размере tablespace в байтах, поэтому для приведения к читаемому виду мы также используем функцию pg_size_pretty. Пространство pg_global исключаем, так как оно используется для общих системных каталогов.
*/
SELECT spcname, pg_size_pretty(pg_tablespace_size(spcname)) 
FROM pg_tablespace
WHERE spcname<>'pg_global';