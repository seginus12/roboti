import math
import itertools
from dataclasses import dataclass

from turn_calculator import calculate_speed_and_time

speed_ = 110
turns_map: dict[str, int] = {
    "right": 4,
    "left": 3,
    "straight": 2,
    "back": 1,
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
        Вычисляет абсолютный угол направления на целевую точку (0-360°).
        """

        target_angle_rad = math.atan2(self.target_y - self.y, self.target_x - self.x)
        target_angle_deg = math.degrees(target_angle_rad)

        return (target_angle_deg % 360 + 360) % 360


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
            Robot(color="red", x=365, y=224, angle=1, radius=5, finish_radius=5),
            Robot(color="blue", x=547, y=393, angle=1, radius=5, finish_radius=5),
            Robot(color="green", x=393, y=800, angle=1, radius=5, finish_radius=5),
        ]
    return None  # данные с камеры




def get_target_coordinates(robots):
    """
    Рассчитывает координаты целевых точек для каждого робота.
    Назначает каждой машине ближайшую доступную точку,
    минимизируя суммарное расстояние перемещения.
    Возвращает словарь {color_робота: (x, y)}.
    """
    map_size = 1080
    collision_distance = 250
    N = len(robots)
    if N == 0:
        return {}

    cx = map_size / 2
    cy = map_size / 2
    margin = collision_distance

    # 1. Расчёт радиуса окружности целевых точек (оставляем вашу логику)
    if N == 1:
        R = 0
    else:
        max_R_x = cx - margin
        max_R_y = cy - margin
        max_R = min(max_R_x, max_R_y)

        min_vertex_distance = 2 * max_R * math.sin(math.pi / N)
        if min_vertex_distance < collision_distance:
            max_R = collision_distance / (2 * math.sin(math.pi / N))
        R = max_R

    # 2. Генерация целевых точек (равномерно по окружности)
    target_points = []
    for i in range(N):
        vertex_angle = i * 2 * math.pi / N
        tx = round(cx + R * math.cos(vertex_angle))
        ty = round(cy + R * math.sin(vertex_angle))
        target_points.append((tx, ty))

    targets = {}

    # 3. Для одного робота точка всегда в центре
    if N == 1:
        targets[robots[0].color] = target_points[0]
        return targets

    # 4. Оптимальное назначение "робот -> точка" по минимальному расстоянию
    # Для N <= 5 перебор перестановок работает мгновенно и гарантирует лучший результат
    best_perm = None
    min_total_sq_dist = float('inf')

    for perm in itertools.permutations(range(N)):
        total_sq_dist = 0
        for r_idx in range(N):
            t_idx = perm[r_idx]
            dx = robots[r_idx].x - target_points[t_idx][0]
            dy = robots[r_idx].y - target_points[t_idx][1]
            total_sq_dist += dx * dx + dy * dy  # квадрат расстояния быстрее sqrt

        if total_sq_dist < min_total_sq_dist:
            min_total_sq_dist = total_sq_dist
            best_perm = perm

    # 5. Запись результата
    for r_idx in range(N):
        t_idx = best_perm[r_idx]
        targets[robots[r_idx].color] = target_points[t_idx]

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

    # # Проверка коллизий между роботами (на начальных позициях)
    # print("\nПроверка коллизий на начальных позициях:")
    # if check_all_collisions(robots):
    #     print("Обнаружены коллизии:")
    #     for r in robots:
    #         if r.has_collision:
    #             print(f"Робот {r.color} в коллизии (координаты: ({r.x}, {r.y}))")
    # else:
    #     print("Коллизий не обнаружено")
    #
    # # Проверка, достигли ли роботы финиша
    # print("\nПроверка достижения финиша:")
    # check_all_finished(robots)
    # for robot in robots:
    #     status = "финишировал" if robot.finished else "в пути"
    #     print(f"Робот {robot.color}: {status}")
    # set_angle(robots)


def set_angle(robots: list[Robot]) -> dict[str, RobotCommand]:
    """
    Поворот роботов.

    Не учитываем их новый угол поворота, т.к. он может быть немного сбит.

    """
    commands: dict[str, RobotCommand] = {}
    for r in robots:
        if r.finished:
            continue
        delta = ((r.target_angle - r.angle + 180) % 360) - 180
        direction, speed, time_val = calculate_speed_and_time(abs(delta))
        print(f"{direction}, {speed}, {time_val}")
        print(f"{r.color} ----------- {abs(delta)}")
        if abs(delta) < 10:
            commands[r.color] = RobotCommand(direction, 0, 0)
            continue
        commands[r.color] = RobotCommand(direction, speed, time_val)
        #r.target_angle = r.calculate_rotation()
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
