"""carpark_vent - car park mechanical ventilation calculations.

Reproduces the logic of Daniel Zhang's ``carpark_calcs.xlsx`` workbook
(one sheet per AS 1668.2 edition: 2024, 2012, 2002, 1991).

No text, tables or figures from Australian Standards are reproduced here;
only the calculation logic and constants used in the source workbook.
"""

from carpark_vent.calcs import calculate_level, calculate_project
from carpark_vent.editions import EDITIONS, get_edition
from carpark_vent.models import Level, LevelResult, Project, ProjectInfo, ProjectResult

__all__ = [
    "EDITIONS",
    "Level",
    "LevelResult",
    "Project",
    "ProjectInfo",
    "ProjectResult",
    "calculate_level",
    "calculate_project",
    "get_edition",
]

__version__ = "0.1.0"
