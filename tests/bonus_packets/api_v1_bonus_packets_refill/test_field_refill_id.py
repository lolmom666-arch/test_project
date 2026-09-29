import pytest
import requests

from src.bd_client import BDConnection
from src.config import BASE_URL
from src.one_click import one_click, get_password
from src.ssh_client import SSHClient

user_token = one_click()
print(user_token)
user = get_password(f"Bearer {user_token}")
ssh = SSHClient()
ssh.refill(user_id=user.username)
bd = BDConnection()
cursors = bd.cursor()
cursors.execute(
        "SELECT * FROM refill WHERE (`user_id` = %s)", (user.username))
refill_id = str(cursors.fetchone()[0])

@pytest.mark.parametrize("refill_status, code, refill_ids", [
    (0,200, refill_id),
    (1,200, refill_id),
    (2,400, refill_id),
    (3,400, refill_id),
    (4,400, 777777),
    (5,400, "-1000"),
])
def test_field_refill_id(refill_status, code, refill_ids):
    if refill_status <= 3:
        cursors.execute(
            "UPDATE `refill` SET `status`=%s WHERE `id`= %s",
            (refill_status, refill_ids,)
        )
        bd.commit()

    valid_body = {"refillId": refill_ids, "bonusPacketId": 50001}
    headers = {"Authorization": f"Bearer {user_token}"}
    auth = requests.put(f"{BASE_URL}/api/v1/bonus/packets/refill", json=valid_body, headers=headers, timeout=10)
    auth_text = auth.json()
    print(auth_text)
    assert auth.status_code == code
    if code == 200:
            assert auth_text == []
    elif refill_ids == 777777:
            assert auth_text['message'] == "Invalid request"
    elif refill_ids == "-1000":
            assert auth_text['message'] == "refill_not_found"
    else:
        assert auth_text['message'] == "refill_status_not_allowed"