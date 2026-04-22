import pytest
from sqlalchemy import select
from models import BasicInfo
import api

def test_basic_info_crud(engine, faker):
    data = {
        "name": faker.word(),
        "date_tzero": faker.date_time_this_decade().isoformat(),
        "organizer": faker.company(),
        "limit": str(faker.random_int(10, 180)),
        "band": "2m"
    }
    
    # Test setting
    api.set_basic_info(engine, data)
    
    # Test getting
    retrieved = api.get_basic_info(engine)
    assert retrieved["name"] == data["name"]
    assert retrieved["organizer"] == data["organizer"]
    assert retrieved["limit"] == data["limit"]
    
    # Test update
    new_data = {"name": "New Name"}
    api.set_basic_info(engine, new_data)
    
    retrieved = api.get_basic_info(engine)
    assert retrieved["name"] == "New Name"
    assert retrieved["organizer"] == data["organizer"] # unchanged
