import pytest
from registration import map_runner

def test_map_runner(faker):
    data = {
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "index": faker.numerify('####'),
        "birth_year": faker.year(),
        "country": faker.country_code()
    }
    
    mapped = map_runner(data)
    
    assert mapped["name"] == f"{data['last_name']}, {data['first_name']}"
    assert mapped["reg"] == data["index"]
    assert mapped["byear"] == data["birth_year"]
    assert mapped["country"] == data["country"]
