from datetime import datetime
from typing import List, Optional, Tuple


class OResult:
    id: int
    name: str
    reg: str
    si: int
    tx: int
    time: int
    status: str
    order: List[Tuple[str, datetime, str]]
    place: int
    club: str
    start: Optional[datetime]
    finish: Optional[datetime]

    def __init__(
            self,
            id: int,
            name: str,
            reg: str,
            si: int,
            tx: int,
            time: int,
            status: str,
            order: List[Tuple[str, datetime, str]],
            club: str,
            start: Optional[int] = None,
            finish: Optional[int] = None
    ) -> None: ...


def calculate_category(
        db_path: str,
        name: str,
        include_unknown: bool,
        now: int
) -> List[OResult]: ...
