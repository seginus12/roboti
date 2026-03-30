from fastapi import APIRouter, WebSocket, Query
from fastapi.responses import Response
import json
from websocket_manager import ws_connection_manager

router = APIRouter()

ROBOTS_MAPPING = {
    "pink": "10.0.6.101",
    "green": "10.0.6.102",
    "red": "10.0.6.103",
    "yellow": "10.0.6.104",
    "blue": "10.0.6.105",
}


@router.websocket("/ws/robots/")
async def robot_connection(websocket: WebSocket, color: str = Query(...)):
    await ws_connection_manager.connect(websocket, color)
    print(f"Робот {color} подключен")

    try:
        while True:
            try:
                await websocket.receive_text()
            except Exception as e:
                print(f"Ошибка при приеме сообщения: {e}")
                break

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_connection_manager.disconnect(websocket)


@router.websocket("/ws/camera/")
async def camera_connection(websocket: WebSocket):
    await websocket.accept()
    print("Камера подключена")

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                color = message.get("color")

                if color and color in ROBOTS_MAPPING:
                    await ws_connection_manager.send_to_color(color, data)
                    print(f"Отправлено роботу {color}: {data}")
                else:
                    print(f"Некорректный цвет или цвет не найден: {color}")

            except json.JSONDecodeError:
                print("Ошибка декодирования JSON")
            except Exception as e:
                print(f"Ошибка при приеме сообщения: {e}")
                break

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.post("/test/")
async def test(message: str):
    await ws_connection_manager.broadcast(message)
    return Response("!")
