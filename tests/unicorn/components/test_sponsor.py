from unittest.mock import patch

from unicorn.components.sponsor import (  # _get_sponsorships_as_maintainer,
    check_sponsorship,
)

sponsorships_gql_data = {
    "data": {
        "viewer": {
            "sponsorshipsAsMaintainer": {
                "nodes": [
                    {"sponsorEntity": {"login": "login1"}},
                    {"sponsorEntity": {"login": "login2"}},
                    {"sponsorEntity": {}},
                ]
            }
        }
    }
}


@patch(
    "unicorn.components.sponsor._get_sponsorships_as_maintainer",
    return_value=sponsorships_gql_data,
)
def test_find_github_username_in_sponsors_missing(_get_sponsorships_as_maintainer):
    assert not check_sponsorship("blob")


@patch(
    "unicorn.components.sponsor._get_sponsorships_as_maintainer",
    return_value=sponsorships_gql_data,
)
def test_find_github_username_in_sponsors(_get_sponsorships_as_maintainer):
    assert check_sponsorship("login1")
