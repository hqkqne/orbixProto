import json
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal
import httpx

class ApiWorker(QThread):
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, method: str, url: str, json_data :dict = None, headers: dict = None):
        super().__init__()
        self.method = method.upper()
        self.url = url
        self.json_data = json_data
        self.headers = headers or {}

        self.finished.connect(self.deleteLater)

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
        except httpx.TimeoutException:
            self.error.emit("Превышено время ожидания ответа сервера")
        except (json.JSONDecodeError, httpx.DecodingError):
            self.error.emit("Сервер вернул некорректный JSON")
        except Exception as e:
            self.error.emit(str(e))

class EmailCheckWorker(QThread):
    verification_success = pyqtSignal()
    verification_failed = pyqtSignal(str)

    def __init__(self, url: str, email:str, timeout: int = 60, interval: int = 3):
        super().__init__()
        self.url = url
        self.email = email
        self.timeout = timeout
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self):
        print('непосредственно начал работать')
        start_time = time.time()
        with httpx.Client(timeout=5.0) as client:
            while time.time() - start_time < self.timeout and not self._stop_event.is_set():
                try:
                    response = client.get(self.url, params={"email": self.email})
                    response.raise_for_status()
                    data = response.json()
                    if bool(data):
                        print("EmailCheckWorker: verified!")
                        self.verification_success.emit()
                        return
                except httpx.TimeoutException:
                    print("Polling: timeout, retrying...")
                except httpx.ConnectError:
                    print("Polling: connect error, retrying...")
                except (json.JSONDecodeError, httpx.DecodingError) as e:
                    print(f"Polling: bad JSON: {e}")
                except httpx.HTTPStatusError as e:
                    print(f"Polling: HTTP {e.response.status_code} - {e.response.text[:100]}")
                except Exception as e:
                    print(f"Polling: unexpected error: {e}")
                self._stop_event.wait(self.interval)
            self.verification_failed.emit("Время подтверждения истекло")

    def stop(self):
        self._stop_event.set()
        self.wait()