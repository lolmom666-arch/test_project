import allure
import httpx

from src.config import BASE_URL


def attach_request(request: httpx.Request) -> None:
    body = request.content.decode("utf-8", errors="replace")
    allure.attach(
        f"Метод: {request.method}\n"
        f"URL: {request.url}\n"
        f"Тело: {body}",
        name="HTTP-запрос",
        attachment_type=allure.attachment_type.TEXT,
    )


def attach_response(response: httpx.Response) -> None:
    response.read()
    allure.attach(
        f"HTTP-статус: {response.status_code}\n"
        f"URL: {response.url}\n"
        f"Тело: {response.text}",
        name="HTTP-ответ",
        attachment_type=allure.attachment_type.TEXT,
    )


EVENT_HOOKS = {
    "request": [attach_request],
    "response": [attach_response]
}


class BonusPacketsClient:
    def __init__(self, client: httpx.Client):
        self.client = client

    def put_bonus_packets_refill(
        self,
        body: dict[str, object],
        headers: dict[str, str],
    ) -> httpx.Response:
        return self.client.put(
            f"{BASE_URL}/api/v1/bonus/packets/refill",
            json=body,
            headers=headers,
        )


class UserClient:
    def __init__(self, client):
        self.client = client

    def post_registration_one_click(
            self,
            payload,
    ) -> httpx.Response:
        return self.client.post(
            f"{BASE_URL}/api/v1/registration/one_click",
            data=payload,
        )

    def get_registration_one_click_get_password(
            self,
            header: dict[str, str],
    ) -> httpx.Response:
        return self.client.get(
            f"{BASE_URL}/api/v1/registration/one_click/get_password.json",
        headers=header,
        )
