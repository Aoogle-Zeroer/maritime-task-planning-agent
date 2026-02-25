from litellm import completion
from config import Config
from utils.json_parser import extract_json_from_text
import math


class CollisionAvoidanceSkill:
    def __init__(self):
        self.system_prompt = """
        你是一名专业的海上船舶任务规划智能体。
        你的任务是根据起点、终点和障碍物信息，规划一条安全的航路点 (Waypoints) 序列。

        ⚠️ 核心安全规则（必须严格遵守）：
        1. 必须避开**所有**障碍物，不能只考虑部分障碍物
        2. 每个圆形障碍物格式：[中心 x, 中心 y, 半径]
        3. 路径上**任何点**（包括航点之间）距圆形障碍物**边缘**必须 ≥ 安全距离
        4. 即：路径到圆心的距离 ≥ 半径 + 安全距离

        📐 多障碍物规划策略：
        1. 先识别所有障碍物位置
        2. 找出障碍物之间的安全通道
        3. 如果障碍物密集，采用绕行策略（**宁可绕远，不可冒险**）
        4. 每个航点都要验证与所有障碍物的距离
        5. 建议生成 5-10 个中间航点，使路径更平滑安全

        ⚠️ 常见错误（避免）：
        - ❌ 只避开第一个障碍物，忽略后面的
        - ❌ 航点安全，但航点之间的连线穿过障碍物
        - ❌ 两个障碍物之间通道太窄仍强行通过
        - ❌ 路径太直，没有足够绕行空间

        ✅ 正确做法：
        - ✅ 采用"之"字形或弧形绕行
        - ✅ 在障碍物密集区增加中间航点
        - ✅ 保持足够的安全余量

        输出要求：
        1. 必须且只能输出标准的 JSON 格式
        2. JSON 结构：
        {
            "waypoints": [{"x": float, "y": float}, ...],
            "explanation": "详细说明如何避开每个障碍物"
        }
        3. 在 explanation 中逐个说明每个障碍物的避让策略
        4. 起点和终点必须包含在 waypoints 中
        """

    def plan(self, start_pos, end_pos, obstacles, user_instruction, safe_distance=10.0, max_retries=5):
        """
        调用 LLM 进行路径规划（迭代直到生成安全路线）

        :param safe_distance: 距障碍物边缘的最小安全距离 (m)
        """
        # 格式化障碍物信息
        obstacles_desc = []
        for i, obs in enumerate(obstacles):
            if len(obs) >= 3:
                min_safe_dist = obs[2] + safe_distance
                obstacles_desc.append(
                    f"【障碍物{i + 1}】中心 ({obs[0]}, {obs[1]}), 半径 {obs[2]}m, 距圆心最小安全距离 {min_safe_dist}m"
                )
            else:
                obstacles_desc.append(f"【障碍物{i + 1}】点 ({obs[0]}, {obs[1]})")

        # 计算障碍物之间的最小距离（帮助 LLM 理解密集程度）
        obstacle_analysis = self._analyze_obstacles(obstacles, safe_distance)

        attempt = 0
        last_validation_error = ""
        best_plan = None  # 保存最好的结果（即使不完全安全）

        while attempt < max_retries:
            attempt += 1
            print(f"🔄 规划尝试 {attempt}/{max_retries} (安全距离={safe_distance}m)")

            user_prompt = self._build_user_prompt(
                start_pos, end_pos, obstacles_desc,
                user_instruction, obstacle_analysis,
                last_validation_error, attempt, safe_distance
            )

            try:
                response = completion(
                    model=Config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    api_key=Config.LLM_API_KEY,
                    api_base=Config.LLM_BASE_URL if Config.LLM_BASE_URL else None,
                    temperature=0.1
                )

                content = response.choices[0].message.content
                plan_data = extract_json_from_text(content)

                if 'waypoints' not in plan_data or len(plan_data['waypoints']) == 0:
                    last_validation_error = "规划结果为空"
                    continue

                # 验证路径（包括线段验证）
                validation_result = self._validate_path_with_segments(
                    plan_data['waypoints'], obstacles, safe_distance
                )

                if validation_result['is_valid']:
                    # ✅ 验证通过，返回安全路线
                    plan_data['explanation'] += f" ✅ 路径验证通过（尝试{attempt}次，安全距离={safe_distance}m）"
                    plan_data['validation_status'] = 'SAFE'
                    plan_data['safe_distance'] = safe_distance
                    print(f"✅ 规划成功（尝试{attempt}次，安全距离={safe_distance}m）")
                    return plan_data
                else:
                    # ⚠️ 验证失败，记录错误并继续尝试
                    last_validation_error = validation_result['message']
                    plan_data['explanation'] += f" ⚠️ 验证问题：{last_validation_error}"
                    print(f"⚠️ 验证失败：{last_validation_error}")

                    # 保存当前最好的结果（风险最小的）
                    if best_plan is None:
                        best_plan = plan_data
                    else:
                        # 比较哪个计划风险更小（简单比较航点数量，越多通常越安全）
                        if len(plan_data.get('waypoints', [])) > len(best_plan.get('waypoints', [])):
                            best_plan = plan_data

            except Exception as e:
                last_validation_error = str(e)
                print(f"❌ 规划错误：{last_validation_error}")

        # 所有尝试都失败，返回最好的结果（带警告）
        if best_plan:
            best_plan[
                'explanation'] += f" ⚠️ 警告：经过{max_retries}次尝试仍无法生成完全安全的路径（安全距离={safe_distance}m），请人工核查或点击'重新规划'！"
            best_plan['validation_status'] = 'RISKY'
            best_plan['safe_distance'] = safe_distance
            return best_plan
        else:
            return {
                'error': f'经过{max_retries}次尝试仍无法生成路径',
                'waypoints': [],
                'explanation': f'规划失败：{last_validation_error}',
                'validation_status': 'FAILED',
                'safe_distance': safe_distance
            }

    def _build_user_prompt(self, start_pos, end_pos, obstacles_desc,
                           user_instruction, obstacle_analysis,
                           last_validation_error, attempt, safe_distance):
        """构建用户 Prompt（包含迭代反馈）"""

        prompt = f"""当前任务：{user_instruction}
起点坐标：{start_pos}
终点坐标：{end_pos}

⚠️ 安全距离要求：**距所有障碍物边缘至少 {safe_distance}m**

障碍物信息（共{len(obstacles_desc)}个，必须全部避开）：
{chr(10).join(obstacles_desc)}

障碍物分析：
{obstacle_analysis}

规划策略建议：
- 采用弧形或"之"字形绕行，不要走直线
- 在障碍物密集区域增加中间航点（建议 5-10 个航点）
- 宁可绕远路，也要保证安全距离 ≥ {safe_distance}m"""

        if attempt > 1 and last_validation_error:
            prompt += f"""

⚠️ 上次规划失败原因：{last_validation_error}
请重新规划，特别注意上述问题！建议：
- 增加绕行幅度
- 添加更多中间航点
- 远离障碍物中心
- 确保安全距离 ≥ {safe_distance}m"""

        prompt += f"""

请生成避碰路径，确保所有航点及航点连线距所有障碍物边缘至少 {safe_distance}m 安全距离。"""

        return prompt

    def _analyze_obstacles(self, obstacles, safe_distance):
        """分析障碍物分布情况"""
        if len(obstacles) < 2:
            return "单个障碍物，直接绕行即可"

        analysis = []
        for i in range(len(obstacles)):
            for j in range(i + 1, len(obstacles)):
                if len(obstacles[i]) >= 3 and len(obstacles[j]) >= 3:
                    dist = math.sqrt(
                        (obstacles[i][0] - obstacles[j][0]) ** 2 +
                        (obstacles[i][1] - obstacles[j][1]) ** 2
                    )
                    # 计算两个障碍物安全边界之间的间隙
                    min_gap = dist - obstacles[i][2] - obstacles[j][2] - 2 * safe_distance
                    if min_gap < 0:
                        analysis.append(
                            f"- 障碍物{i + 1}与{j + 1}之间**无法通过**：安全边界间隙 {min_gap:.1f}m（**必须绕行**）")
                    elif min_gap < 20:
                        analysis.append(
                            f"- 障碍物{i + 1}与{j + 1}之间通道狭窄：安全边界间隙 {min_gap:.1f}m（**建议绕行**）")
                    elif min_gap < 40:
                        analysis.append(f"- 障碍物{i + 1}与{j + 1}之间通道宽度：安全边界间隙 {min_gap:.1f}m（谨慎通过）")
                    else:
                        analysis.append(f"- 障碍物{i + 1}与{j + 1}之间通道宽度：安全边界间隙 {min_gap:.1f}m（安全可通过）")

        return chr(10).join(analysis) if analysis else "障碍物分布较散"

    def _validate_path_with_segments(self, waypoints, obstacles, safe_distance):
        """
        验证路径（包括航点和航点之间的线段）

        :param safe_distance: 距障碍物边缘的最小安全距离 (m)
        """
        # 1. 验证所有航点
        for i, wp in enumerate(waypoints):
            for obs in obstacles:
                if len(obs) >= 3:
                    obs_x, obs_y, radius = obs[0], obs[1], obs[2]
                    dist_to_center = math.sqrt((wp['x'] - obs_x) ** 2 + (wp['y'] - obs_y) ** 2)
                    dist_to_edge = dist_to_center - radius

                    if dist_to_edge < safe_distance:
                        return {
                            'is_valid': False,
                            'message': f"航点{i} ({wp['x']}, {wp['y']}) 距障碍物边缘仅 {dist_to_edge:.1f}m < {safe_distance}m！"
                        }

        # 2. 验证航点之间的线段（关键！）
        for i in range(len(waypoints) - 1):
            wp1 = waypoints[i]
            wp2 = waypoints[i + 1]

            for obs in obstacles:
                if len(obs) >= 3:
                    obs_x, obs_y, radius = obs[0], obs[1], obs[2]

                    # 计算线段到圆心的最短距离
                    min_dist = self._point_to_segment_distance(
                        obs_x, obs_y,
                        wp1['x'], wp1['y'],
                        wp2['x'], wp2['y']
                    )

                    dist_to_edge = min_dist - radius

                    if dist_to_edge < safe_distance:
                        return {
                            'is_valid': False,
                            'message': f"航点{i}到{i + 1}的连线距障碍物边缘仅 {dist_to_edge:.1f}m < {safe_distance}m！"
                        }

        return {'is_valid': True, 'message': ''}

    def _point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """
        计算点 (px, py) 到线段 (x1,y1)-(x2,y2) 的最短距离
        """
        # 线段向量
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            # 线段退化为点
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        # 计算投影参数 t
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))

        # 投影点坐标
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        # 返回点到投影点的距离
        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)
