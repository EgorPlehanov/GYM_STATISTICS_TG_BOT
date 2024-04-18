/*
МОНИТОРИНГ БЛОКИРОВОК

Данный запрос показывает всю информацию о заблокированных запросах, 
а также информацию о том, кем они заблокированы.
*/
SELECT COALESCE(blockingl.relation::regclass::text, blockingl.locktype) AS locked_item,
       now() - blockeda.query_start                                     AS waiting_duration,
       blockeda.pid                                                     AS blocked_pid,
       blockeda.query                                                   AS blocked_query,
       blockedl.mode                                                    AS blocked_mode,
       blockinga.pid                                                    AS blocking_pid,
       blockinga.query                                                  AS blocking_query,
       blockingl.mode                                                   AS blocking_mode
FROM pg_locks blockedl
JOIN pg_stat_activity blockeda ON blockedl.pid = blockeda.pid
JOIN pg_locks blockingl ON (blockingl.transactionid = blockedl.transactionid OR
                            blockingl.relation = blockedl.relation AND
                            blockingl.locktype = blockedl.locktype) AND blockedl.pid <> blockingl.pid
JOIN pg_stat_activity blockinga ON blockingl.pid = blockinga.pid AND blockinga.datid = blockeda.datid
WHERE NOT blockedl.granted AND blockinga.datname = current_database();



/*
СНЯТИЕ БЛОКИРОВОК

PID_ID - это ID запроса, который блокирует другие запросы. Чаще всего хватает отмены одного блокирующего запроса, чтобы снять блокировки и запустить всю накопившуюся очередь. Разница между pg_cancel_backend и pg_terminate_backend в том, что pg_cancel_backend отменяет запрос, а pg_terminate_backend завершает сеанс и, соответственно, закрывает подключение к базе данных. Команда pg_cancel_backend более щадящая и в большинстве случаев вам её хватит. Если нет, используем pg_terminate_backend.
*/
/*
SELECT pg_cancel_backend(PID_ID);
OR
SELECT pg_terminate_backend(PID_ID);
*/