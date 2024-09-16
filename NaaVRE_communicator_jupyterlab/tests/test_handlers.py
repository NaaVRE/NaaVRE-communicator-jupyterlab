import json
import os

bodies = [
    {
        'query': {
            'method': 'GET',
            'url': 'https://qcdis.github.io/NaaVRE-website/',
            'headers': {},
            'data': {},
            }
        },
    ]


async def test_get_example(jp_fetch, valid_access_token):
    os.environ["OAUTH_ACCESS_TOKEN"] = valid_access_token

    body = bodies[0]
    # When
    response = await jp_fetch(
        "naavre-communicator",
        "external-service",
        method='POST',
        body=json.dumps(body),
        )

    # Then
    assert response.code == 200
    payload = json.loads(response.body)
    assert payload['status_code'] == 200
