from datetime import datetime
from typing import List, Optional, Tuple, Any

class OResult:
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
