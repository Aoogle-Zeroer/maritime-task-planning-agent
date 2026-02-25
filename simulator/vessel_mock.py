import math


class VesselMock:
    """
    模拟底层船舶运动模型接口。
    后续可替换为课题组提供的真实 3-DOF/6-DOF 模型类。
    """

    def __init__(self, x=0, y=0, heading=0):
        self.x = x
        self.y = y
        self.heading = heading  # 航向角 (度)
        self.path_history = [(x, y)]

    def update_position(self, target_x, target_y, speed=1.0):
        """
        简单模拟向目标点移动一步
        """
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist < 0.5:  # 到达阈值
            self.x, self.y = target_x, target_y
            return True  # 到达

        # 更新位置 (简化模拟，直接插值)
        self.x += (dx / dist) * speed
        self.y += (dy / dist) * speed

        # 更新航向
        self.heading = math.degrees(math.atan2(dy, dx))
        self.path_history.append((self.x, self.y))
        return False

    def get_state(self):
        return {"x": self.x, "y": self.y, "heading": self.heading}
