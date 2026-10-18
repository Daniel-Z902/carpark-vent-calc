"""carpark_vent - car park mechanical ventilation calculations.

Reproduces the logic of Daniel Zhang's ``carpark_calcs.xlsx`` workbook
(AS 1668.2-2012, the default, and AS 1668.2-2024).

No text, tables or figures from Australian Standards are reproduced here;
only the calculation logic and constants used in the source workbook.
"""

from carpark_vent.calcs import calculate_level, calculate_project
from carpark_vent.editions import DEFAULT_EDITION, EDITIONS, get_edition
from carpark_vent.models import Level, LevelResult, Project, ProjectInfo, ProjectResult

__all__ = [
    "DEFAULT_EDITION",
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
