import pytest
import math
from skills.collision_avoidance import CollisionAvoidanceSkill


class TestCollisionAvoidanceSkill:
    """避碰规划技能测试"""

    def test_point_to_segment_distance(self):
        """测试点到线段距离计算"""
        skill = CollisionAvoidanceSkill()

        # 点在线段上
        dist = skill._point_to_segment_distance(5, 0, 0, 0, 10, 0)
        assert dist == 0

        # 点在线段外
        dist = skill._point_to_segment_distance(5, 5, 0, 0, 10, 0)
        assert dist == 5

    def test_validate_path_safe(self):
        """测试安全路径验证"""
        skill = CollisionAvoidanceSkill()

        waypoints = [{'x': 0, 'y': 0}, {'x': 50, 'y': 50}]
        obstacles = [[100, 100, 10]]  # 障碍物远离路径

        result = skill._validate_path_with_segments(waypoints, obstacles, safe_distance=10)
        assert result['is_valid'] == True

    def test_validate_path_unsafe(self):
        """测试危险路径验证"""
        skill = CollisionAvoidanceSkill()

        waypoints = [{'x': 0, 'y': 0}, {'x': 10, 'y': 10}]
        obstacles = [[5, 5, 10]]  # 障碍物在路径上

        result = skill._validate_path_with_segments(waypoints, obstacles, safe_distance=10)
        assert result['is_valid'] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
