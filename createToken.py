import httpx
import json
import os
from dotenv import load_dotenv
from email_validator import validate_email, caching_resolver

resolver = caching_resolver(timeout=10)
load_dotenv()

def create_token(email):
    valid_email = validate_email(email, dns_resolver=resolver).email
    r = httpx.post('https://api-b2b.mubert.com/v2/GetServiceAccess',
                json={
                    "method": "GetServiceAccess",
                    "params": {
                        "email": email,
                        "license": os.getenv('API_LICENSE'),
                        "token": os.getenv('API_TOKEN'),
                        "mode": "loop"
                    }
                })
    
    rdata = json.loads(r.text)
    assert rdata['status'] == 1, "probably incorrect e-mail"
    pat = rdata['data']['pat']

    print(f'Got token: {pat}')

    os.environ['API_ACCESS_TOKEN'] = pat

    return pat