import math
from dataclasses import dataclass

from turn_calculator import calculate_speed_and_time

speed_ = 110
turns_map: dict[str, int] = {
    "right": 4,
    "left": 3,
    "straight": 1,
    "back": 2,
}
"""
Мапинг движения.

Использовать будем только вперед. ну мб нужно будет предусмотреть немного назад для корректировки
"""


@dataclass
class RobotCommand:
    command: int
    speed: int
    time: float


# ============================================================
# Класс для представления робота
# ============================================================
class Robot:
    """
    Класс, описывающий робота.

    :param color: уникальный идентификатор
    :param x: координата x
    :param y: координата y
    :param angle: угол поворота (в градусах или радианах)
    :param radius: радиус сферы коллизии (для проверки столкновений)
    :param target_x: целевая координата x
    :param target_y: целевая координата y
    :param finish_radius: радиус сферы, при попадании в которую финиш засчитывается

    finished - флаг, указывающий, достиг ли робот финиша
    has_collision - флаг, указывающий, что робот столкнулся с другим
    """

    def __init__(
        self, color, x, y, angle, radius=5, finish_radius=5, target_x=None, target_y=None, target_angle=None
    ):
        self.color = color
        self.x = x
        self.y = y
        self.angle = angle
        self.radius = radius
        self.has_collision = False
        self.target_x = target_x
        self.target_y = target_y
        self.finish_radius = finish_radius
        self.finished = False
        self.target_angle = target_angle

    def __repr__(self):
        return (
            f"Robot(color={self.color}, x={self.x}, y={self.y}, angle={self.angle}, "
            f"radius={self.radius}, finished={self.finished})"
        )

    def distance_squared_to(self, other):
        """Возвращает квадрат расстояния до другого робота (для оптимизации)"""
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def check_collision_with(self, other):
        """Проверяет коллизию с другим роботом (использует квадраты расстояний)"""
        if self.color == other.color:
            return False
        r_sum = self.radius + other.radius
        return self.distance_squared_to(other) < r_sum * r_sum

    def set_target(self, x, y):
        """Устанавливает целевую точку и сбрасывает флаг finished"""
        self.target_x = x
        self.target_y = y
        self.finished = False
        self.target_angle = self.calculate_rotation()

    def check_finish(self):
        """
        Проверяет, находится ли робот в сфере финиша (т.е. достиг ли цели).
        Если да, устанавливает флаг finished = True и возвращает True.
        """
        if self.target_x is None or self.target_y is None:
            return False  # цель не задана

        dx = self.x - self.target_x
        dy = self.y - self.target_y
        distance_sq = dx * dx + dy * dy
        if distance_sq <= self.finish_radius * self.finish_radius:
            self.finished = True
            return True
        return False

    def calculate_rotation(self) -> float:
        """
        Вычисляет минимальный угол поворота робота (со знаком) для направления на целевую точку.
        """

        # Угол от робота до точки в радианах, затем в градусах
        target_angle_rad = math.atan2(self.target_y - self.y, self.target_x - self.x)
        target_angle_deg = math.degrees(target_angle_rad)

        # Разница углов (без нормализации)
        delta = (target_angle_deg - self.angle) % 360

        # Выбираем больший поворот: если дельта <= 180, то идём в другую сторону (360 - дельта)
        return delta - 360 if delta <= 180 else delta


# ============================================================
# Функции для получения данных и расчёта целевых точек
# ============================================================
pohody_debug = True


def get_robots():
    """
    Возвращает список роботов.
    В режиме отладки возвращает тестовый набор.
    """
    if pohody_debug:
        return [
            Robot(color=1, x=62, y=12, angle=1, radius=5, finish_radius=5),
            Robot(color=2, x=1, y=1, angle=1, radius=5, finish_radius=5),
            Robot(color=3, x=5, y=5, angle=1, radius=5, finish_radius=5),
            Robot(color=4, x=10, y=10, angle=1, radius=5, finish_radius=5),
            Robot(color=5, x=10, y=20, angle=1, radius=5, finish_radius=5),
        ]
    return None  # данные с камеры


def get_target_coordinates(robots):
    """
    Рассчитывает координаты целевых точек для каждого робота.
    Алгоритм остаётся неизменным.
    Возвращает словарь {color_робота: (x, y)}.
    976 x 651
    """
    map_size = 1080  # размер карты
    collision_distance = 100  # дистанция между роботами и краями карты
    N = len(robots)
    if N == 0:
        return {}

    # Центр карты
    cx = map_size / 2
    cy = map_size / 2

    margin = collision_distance

    if N == 1:
        R = 0
    else:
        # радиусы для того чтобы не выехать за карту
        max_R_x = cx - margin
        max_R_y = cy - margin
        max_R = min(max_R_x, max_R_y)

        if N > 1:
            # Если роботов много (но вероятно больше 5 не будет)
            min_vertex_distance = 2 * max_R * math.sin(math.pi / N)
            if min_vertex_distance < collision_distance and N > 1:
                max_R = collision_distance / (2 * math.sin(math.pi / N))

        R = max_R

    # чтобы роботы ехали к ближайшей точке
    robots_with_angle = []
    for r in robots:
        angle = math.atan2(r.y - cy, r.x - cx)
        robots_with_angle.append((angle, r))
    robots_with_angle.sort(key=lambda x: x[0])

    targets = {}
    for i, (_, robot) in enumerate(robots_with_angle):
        if N == 1:
            tx, ty = cx, cy  # тупо в центр
        else:
            # Угол вершины (начинаем с 0 и идём против часовой стрелки)
            vertex_angle = i * 2 * math.pi / N
            tx = round(cx + R * math.cos(vertex_angle))
            ty = round(cy + R * math.sin(vertex_angle))

        targets[robot.color] = (tx, ty)

    return targets


def assign_targets_to_robots(robots, targets):
    """Присваивает каждому роботу его целевую точку"""
    for robot in robots:
        if robot.color in targets:
            robot.set_target(targets[robot.color][0], targets[robot.color][1])
        else:
            robot.set_target(None, None)  # если цели нет (но по логике должна быть)


def check_all_collisions(robots):
    """
    Проверяет коллизии между всеми парами роботов.
    Использует квадраты расстояний для ускорения.
    Возвращает True, если хотя бы одна коллизия обнаружена.
    """
    # Сбросить флаги
    for robot in robots:
        robot.has_collision = False

    n = len(robots)
    collision_detected = False

    for i in range(n):
        for j in range(i + 1, n):
            if robots[i].check_collision_with(robots[j]):
                robots[i].has_collision = True
                robots[j].has_collision = True
                collision_detected = True

    return collision_detected


def check_all_finished(robots):
    """Проверяет для всех роботов, достигли ли они финиша.
    Возвращает True, если все роботы финишировали.
    """
    all_finished = True
    for robot in robots:
        robot.check_finish()
        if not robot.finished:
            all_finished = False
    return all_finished


def main():
    robots = get_robots()
    targets = get_target_coordinates(robots)
    assign_targets_to_robots(robots, targets)

    print("Целевые точки:")
    for robot in robots:
        print(f"Робот {robot.color}: ({robot.target_x}, {robot.target_y})")

    # Проверка коллизий между роботами (на начальных позициях)
    print("\nПроверка коллизий на начальных позициях:")
    if check_all_collisions(robots):
        print("Обнаружены коллизии:")
        for r in robots:
            if r.has_collision:
                print(f"Робот {r.color} в коллизии (координаты: ({r.x}, {r.y}))")
    else:
        print("Коллизий не обнаружено")

    # Проверка, достигли ли роботы финиша
    print("\nПроверка достижения финиша:")
    check_all_finished(robots)
    for robot in robots:
        status = "финишировал" if robot.finished else "в пути"
        print(f"Робот {robot.color}: {status}")
    set_angle(robots)


def set_angle(robots: list[Robot]) -> dict[str, RobotCommand]:
    """
    Поворот роботов.

    Не учитываем их новый угол поворота, т.к. он может быть немного сбит.

    """
    commands: dict[str, RobotCommand] = {}
    for r in robots:
        if r.finished:
            continue
        direction, speed, time_val = calculate_speed_and_time(r.target_angle)
        if r.angle + 5 < r.target_angle:
            commands[r.color] = RobotCommand(direction, 0, 0)
            continue
        commands[r.color] = RobotCommand(direction, speed, time_val)
        r.target_angle = r.calculate_rotation()
    return commands


def drive(robots: list[Robot]) -> dict[str, RobotCommand]:
    """Движение роботов"""
    commands: dict[str, RobotCommand] = {}
    for r in robots:
        if r.finished:
            continue
        commands[r.color] = RobotCommand(turns_map["straight"], speed_, 0.5)
    return commands


if __name__ == "__main__":
    main()
