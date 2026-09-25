# import pytest
# import requests
# from src.config import BASE_URL
# from src.one_click import one_click, get_password
# from src.ssh_conn import *
# from src.bd_conn import client_db
#
# @pytest.fixture(scope="module")
# def get_one_click_token():
#     return "Bearer " + one_click()
#
# @pytest.fixture()
# def get_user_id():
#     return get_password(GET_VALID_TOKEN).username
#
#
#
#
#
# user_id = get_password(GET_VALID_TOKEN).username / функция и фикстура / токен параметр
#
# cursors = client_db.cursor() / фнукция и фикстура/ что такое курсор?
# conn_refill(ssh_connect(), user_id) / рефилл айди фнкуия
# cursors.execute(
#     "SELECT * FROM refill WHERE (`user_id` = %s)", (user_id))
# refill_id = cursors.fetchone()[0] / функция и фистура / параметр курсор и юзер айди
# cursors.execute(
#     "UPDATE `refill` SET `status`=0 WHERE (`id`= %s)", (refill_id))
# client_db.commit()
# VALID_BODY = {
#     "refillId": f"{refill_id}",
#     "bonusPacketId": 212
# }
#
