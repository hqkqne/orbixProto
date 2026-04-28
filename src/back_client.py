from PyQt6.QtCore import QThread, pyqtSignal
import httpx

class ApiWorker(QThread):
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method: str, url: str, json_data :dict = None, headers: dict = None):
        super().__init__()
        self.method = method.upper()
        self.url = url
        self.json_data = json_data or {}
        self.headers = headers or {}

    def run(self):
        try:
            with httpx.Client(timeout=10.0) as client:
                if self.method == "GET":
                    resp = client.get(self.url, headers= self.headers)
                elif self.method == "POST":
                    resp = client.post(self.url, json= self.json_data, headers = self.headers)
                elif self.method == "DELETE":
                    resp = client.delete(self.url, headers= self.headers)
                elif self.method == "PUT":
                    resp = client.put(self.url, json = self.json_data, headers= self.headers)
                else:
                    raise ValueError(f"Method {self.method} not supported")

                resp.raise_for_status()
                data = resp.json() if resp.content else {}
                self.success.emit(data)
        except httpx.HTTPStatusError as e:
            error_detail = ''
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except:
                error_detail = e.response.text
            self.error.emit(f"Error {e.response.status_code}: {error_detail}")
        except httpx.ConnectError:
            self.error.emit("Не удалось подключиться к серверу")
        except Exception as e:
            self.error.emit(str(e))