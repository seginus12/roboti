import asyncio
import websockets
import json


async def robot_client(color: str):
    uri = f"ws://localhost:8000/api/ws/robots/?color={color}"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"Робот {color}: Подключен к серверу")

            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"Робот {color}: Получено: {data}")
                except websockets.exceptions.ConnectionClosed:
                    print(f"Робот {color}: Соединение закрыто")
                    break
                except json.JSONDecodeError:
                    print(f"Робот {color}: Получено текстовое сообщение: {message}")

    except Exception as e:
        print(f"Робот {color}: Ошибка: {e}")


async def camera_client():
    uri = "ws://localhost:8000/api/ws/camera/"

    try:
        async with websockets.connect(uri) as websocket:
            print("Камера: Подключена к серверу")

            while True:
                message = input("Введите сообщение (или 'quit' для выхода): ")
                if message.lower() == "quit":
                    break

                color = input("Введите цвет робота (red, green, blue, yellow, pink): ")
                data = {"color": color, "data": message}

                await websocket.send(json.dumps(data))
                print(f"Камера: Отправлено роботу {color}: {message}")

    except Exception as e:
        print(f"Камера: Ошибка: {e}")


async def main():
    print("Запуск тестовых WebSocket клиентов...")
    print("Выберите режим:")
    print("1 - Запустить роботов")
    print("2 - Запустить камеру")

    choice = input("Ваш выбор (1/2): ")

    if choice == "1":
        colors = ["red", "green", "blue"]
        tasks = [robot_client(color) for color in colors]
        await asyncio.gather(*tasks)
    elif choice == "2":
        await camera_client()
    else:
        print("Некорректный выбор")


if __name__ == "__main__":
    asyncio.run(main())
