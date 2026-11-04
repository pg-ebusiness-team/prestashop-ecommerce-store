import requests


class PrestaShopAPI:

    def __init__(self, shop_url: str, api_key: str):
        self.base_url = shop_url.rstrip("/") + "/api/"
        self.api_key = api_key

        self.session = requests.Session()
        self.session.auth = (self.api_key, "")
        self.session.headers.update({
            "Accept": "application/xml"
        })
        
    def _send_request(self, method: str, url: str, **kwargs):
        try:
            response = self.session.request(
                method,
                url,
                timeout=15,
                **kwargs
            )

            response.raise_for_status()

            return response.text

        except requests.exceptions.Timeout:
            raise RuntimeError("Przekroczono czas oczekiwania na PrestaShop API.")

        except requests.exceptions.ConnectionError:
            raise RuntimeError("Nie udało się połączyć z PrestaShop API.")

        except requests.exceptions.HTTPError as e:
            error_details = e.response.text[:2000]

            raise RuntimeError(
                f"PrestaShop API zwróciło błąd HTTP: "
                f"{e.response.status_code}. "
                f"Szczegóły: {error_details}"
            )

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Błąd komunikacji z PrestaShop API: {e}")
        
    def get(self, resource: str, params: dict | None = None):
        url = self.base_url + resource.lstrip("/")

        return self._send_request("GET", url, params=params)
    
    def post(self, resource: str, xml_data: str):
        url = self.base_url + resource.lstrip("/")

        return self._send_request(
            "POST",
            url,
            data=xml_data.encode("utf-8"),
            headers={"Content-Type": "application/xml; charset=utf-8"}
        )


    def put(self, resource: str, resource_id: int, xml_data: str):
        url = self.base_url + resource.lstrip("/") + f"/{resource_id}"

        return self._send_request(
            "PUT",
            url,
            data=xml_data.encode("utf-8"),
            headers={"Content-Type": "application/xml; charset=utf-8"}
        )


    def delete(self, resource: str, resource_id: int):
        url = self.base_url + resource.lstrip("/") + f"/{resource_id}"

        return self._send_request("DELETE", url)