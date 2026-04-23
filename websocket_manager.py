from typing import List, Dict, Any, Optional
from fastapi import WebSocket
import logging

from robot import Robot

logger = logging.getLogger(__name__)


class WSConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_data: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, color: str) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_data[websocket] = {"color": color}

        logger.info(
            f"Робор подключен. Всего активных соединений: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if websocket in self.client_data:
            del self.client_data[websocket]

        logger.info(
            f"Клиент отключен. Осталось активных соединений: {len(self.active_connections)}"
        )

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        try:
            await websocket.send_text(message)
            print(f"Сообщение отправлено роботу: {message}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения роботу: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str) -> None:
        disconnected_clients = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения клиенту: {e}")
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client)

    async def broadcast_json(self, message: Dict[str, Any]) -> None:
        disconnected_clients = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Ошибка при отправке JSON сообщения клиенту: {e}")
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client)

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    def get_client_info(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        return self.client_data.get(websocket)

    def update_client_info(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        if websocket in self.client_data:
            self.client_data[websocket].update(data)

    async def cleanup(self) -> None:
        self.active_connections.clear()
        self.client_data.clear()

        logger.info("Менеджер соединений очищен")

    async def send_to_robot(self, robot: Robot, message: str) -> None:
        for connection, data in self.client_data.items():
            if data.get("color") == robot.color:
                await self.send_personal_message(message, connection)


ws_connection_manager = WSConnectionManager()
