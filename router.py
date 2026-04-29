from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect
from fastapi.responses import Response
import json
import time
import asyncio

from robot import Robot, get_target_coordinates, assign_targets_to_robots, set_angle, drive, check_all_finished
from websocket_manager import ws_connection_manager

router = APIRouter()

ROBOTS_MAPPING = {
    "pink": "10.0.6.101",
    "green": "10.0.6.102",
    "red": "10.0.6.103",
    "yellow": "10.0.6.104",
    "blue": "10.0.6.105",
}

ROBOTS_ASSIGNED = False
ROBOTS_ASSIGNED_TARGETS = False


@router.websocket("/ws/robots/")
async def robot_connection(websocket: WebSocket, color: str = Query(...)):
    await ws_connection_manager.connect(websocket, color)
    print(f"Робот {color} подключен")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("Connectin closed")
        await websocket.close()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_connection_manager.disconnect(websocket)


@router.websocket("/ws/camera/")
async def camera_connection(websocket: WebSocket):
    global ROBOTS_ASSIGNED
    global ROBOTS_ASSIGNED_TARGETS
    await websocket.accept()
    print("Камера подключена")
    try:
        while True:
            robots = []
            data = await websocket.receive_text()
            if data == None:
                print("FUCK VASYA")
                continue
            message = json.loads(data)
            print(f"CAMERA SAYS {message}")
            for r in message["robots"]:
                robots.append(Robot(**r, finish_radius=100))
            targets = get_target_coordinates(robots)
            print(f"TARGETS {targets}")
            assign_targets_to_robots(robots, targets)
            if not ROBOTS_ASSIGNED_TARGETS:
                messages_for_robots = set_angle(robots)
                if not any(command.speed for _, command in messages_for_robots.items()):
                    ROBOTS_ASSIGNED_TARGETS = True
            else:
                is_all_finished = check_all_finished(robots)
                print(f"Is all finished? {is_all_finished}")
                if is_all_finished:
                    print("All finished!!")
                    #raise WebSocketDisconnect
                messages_for_robots = drive(robots)
            for robot in robots:
                message_ = messages_for_robots.get(robot.color)
                if not message_:
                    continue
                if robot.finished:
                    str_message = f"{message_.command} 0 0"
                else:
                    str_message = f"{message_.command} {message_.speed} {message_.time}"
                await ws_connection_manager.send_to_robot(robot, str_message)
                print(f"Отправлено роботу {robot.color}")
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        print("Connectin closed")
        await websocket.close()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.post("/test/")
async def test(message: str):
    await ws_connection_manager.broadcast(message)
    return Response("!")
