from typing import Dict
import os
from collections import namedtuple



FileData = namedtuple("FileData", ["name", "comment", "query"])

def get_db_monitoring_sql_queries(
    current_filename: str = None,
    directory: str = "db/sql_queries/queries_database_monitoring",
) -> Dict[str, FileData]:
    """
    Функция для получения SQL-запросов из папки с SQL-файлами
    """
    files = {}

    for filename in os.listdir(directory):
        if (
            filename.endswith(".sql")
            and (filename == current_filename if current_filename is not None else True)
        ):
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
                lines = file.readlines()
                comment_name = ""
                comment_content = ""
                sql_query = ""
                in_comment = False

                for line in lines:
                    if line.strip().startswith("/*") and not in_comment:
                        in_comment = True
                    elif line.strip().endswith("*/") and in_comment:
                        in_comment = False
                        files[filename] = (comment_name, comment_content, sql_query)
                    elif in_comment and comment_name == "":
                        comment_name = line.strip()
                    elif in_comment:
                        comment_content += line
                    else:
                        sql_query += line
        
            files[filename] = FileData(comment_name, comment_content.strip(), sql_query.strip())
    return files