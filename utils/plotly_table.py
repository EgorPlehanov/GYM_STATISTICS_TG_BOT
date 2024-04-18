from typing import List
from sqlalchemy.engine.cursor import CursorResult
import plotly.graph_objects as go
from io import BytesIO




def get_plotly_table_bytes(
    result_query: CursorResult,
) -> None:
    """
    Функция для построения таблицы Plotly на основе результата запроса.

    Аргументы:
    - result_query: Результат выполнения запроса типа CursorResult.

    Возвращает:
    - None
    """
    column_names: List[str] = [column for column in result_query.keys()]
    data = result_query.fetchall()
    cells = [list(column) for column in zip(*data)]

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=column_names,
            line_color='darkslategray',
            fill_color='royalblue',
            font=dict(color='white', size=12),
        ),
        cells=dict(
            values=cells,
            line_color='darkslategray',
            font_size=12,
        )
    )])
    
    fig.update_layout(
        autosize=True,  # Автоматически подбирать размер столбцов
    )

    buffer = BytesIO()
    fig.write_image(
        buffer,
        format="png",
        width=200 * len(cells) + 300,
        height=20 * (len(cells[0]) if len(cells) > 0 else 0) + 300,
    )
    buffer.seek(0)
    return buffer.getvalue()