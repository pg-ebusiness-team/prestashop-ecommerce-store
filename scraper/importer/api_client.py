import os

import requests


class PrestaShopAPI:

    def __init__(self, shop_url: str, api_key: str, pool_size: int = 10):
        self.base_url = shop_url.rstrip("/") + "/api/"
        self.api_key = api_key

        self.session = requests.Session()
        # Pula połączeń co najmniej tak duża jak liczba wątków importu
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=pool_size)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.verify = os.getenv("PS_VERIFY_SSL", "1") != "0"
        self.session.auth = (self.api_key, "")
        self.session.headers.update({
            "Accept": "application/xml"
        })
        # Kontener narzędziowy łączy się z https://proxy (sieć Dockera), a PrestaShop przekierowuje (302)
        # zapytania pod inną domeną niż swoja (PS_DOMAIN, np. localhost:8443) - wtedy podajemy ją w nagłówku Host
        if shop_host := os.getenv("PS_SHOP_HOST"):
            self.session.headers["Host"] = shop_host

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
        
    def post_image(
        self,
        product_id: int,
        image_data: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ):
        url = self.base_url + f"images/products/{product_id}"

        return self._send_request(
            "POST",
            url,
            files={
                "image": (
                    filename,
                    image_data,
                    content_type
                )
            }
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