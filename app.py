import streamlit as st
import plotly.graph_objects as go
import time
import math
from config import Config
from skills.collision_avoidance import CollisionAvoidanceSkill
from simulator.vessel_mock import VesselMock

# 页面配置
st.set_page_config(page_title="海上作业任务规划智能体", layout="wide")
st.title("🚢 基于基础模型的海上作业任务规划智能体 (Phase 2)")

# 初始化 Session State
if 'vessel' not in st.session_state:
    st.session_state.vessel = VesselMock(x=-50, y=-50)
if 'plan_result' not in st.session_state:
    st.session_state.plan_result = None
if 'is_simulating' not in st.session_state:
    st.session_state.is_simulating = False
if 'frame_count' not in st.session_state:
    st.session_state.frame_count = 0
if 'safe_distance' not in st.session_state:
    st.session_state.safe_distance = 10.0

# 侧边栏：设置与输入
with st.sidebar:
    st.header("⚙️ 场景设置")
    start_x = st.number_input("起点 X", value=-50.0, key="start_x")
    start_y = st.number_input("起点 Y", value=-50.0, key="start_y")
    end_x = st.number_input("终点 X", value=50.0, key="end_x")
    end_y = st.number_input("终点 Y", value=50.0, key="end_y")

    # 安全距离设置
    st.subheader("🛡️ 安全距离设置")
    safe_distance = st.slider(
        "距障碍物边缘最小安全距离 (m)",
        min_value=5.0,
        max_value=50.0,
        value=10.0,
        step=1.0,
        key="safe_distance_slider",
        help="船舶路径距障碍物边缘的最小安全距离"
    )
    st.session_state.safe_distance = safe_distance
    st.info(f"💡 当前安全距离：**{safe_distance}m**")

    st.subheader("🔴 圆形障碍物设置")
    st.markdown("格式：`x, y, 半径` (每行一个)")
    obs_input = st.text_area(
        "障碍物坐标 (x, y, radius)",
        "0, 0, 15\n20, 20, 10",
        key="obs_input",
        height=100
    )

    # 解析障碍物
    obstacles = []
    for line in obs_input.strip().split('\n'):
        try:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                obstacles.append({
                    'x': float(parts[0]),
                    'y': float(parts[1]),
                    'radius': float(parts[2])
                })
            elif len(parts) == 2:
                obstacles.append({
                    'x': float(parts[0]),
                    'y': float(parts[1]),
                    'radius': 5.0
                })
        except Exception as e:
            st.warning(f"解析失败：{line}")

    if obstacles:
        st.success(f"✅ 已设置 {len(obstacles)} 个圆形障碍物")
        for i, obs in enumerate(obstacles):
            safe_radius = obs['radius'] + safe_distance
            st.caption(f"障碍物 {i + 1}: 中心 ({obs['x']}, {obs['y']}), 半径 {obs['radius']}m")

    st.session_state.vessel.x = start_x
    st.session_state.vessel.y = start_y
    st.session_state.vessel.path_history = [(start_x, start_y)]

    st.header("💬 指令输入")
    user_cmd = st.text_input("自然语言指令", f"请规划一条安全路径到达终点，距障碍物边缘至少 {safe_distance}m。",
                             key="user_cmd")

    if st.button("🔄 重新规划 (更换路径)", key="btn_replan"):
        st.session_state.plan_result = None
        st.session_state.is_simulating = False
        st.rerun()

    if st.button("🧠 生成规划", key="btn_plan"):
        with st.spinner(f"LLM 正在思考 (安全距离={safe_distance}m)..."):
            skill = CollisionAvoidanceSkill()
            obstacles_info = [[obs['x'], obs['y'], obs['radius']] for obs in obstacles]
            result = skill.plan(
                start_pos=[start_x, start_y],
                end_pos=[end_x, end_y],
                obstacles=obstacles_info,
                user_instruction=user_cmd,
                safe_distance=safe_distance,
                max_retries=5
            )
            st.session_state.plan_result = result
            st.session_state.is_simulating = False
            st.session_state.frame_count = 0

            if result.get('validation_status') == 'SAFE':
                st.success(f"✅ 规划完成！路径已验证安全")
            elif result.get('validation_status') == 'RISKY':
                st.warning(f"⚠️ 路径存在风险，请重新规划")
            else:
                st.error("❌ 规划失败")

    if st.button("▶️ 开始仿真演示", key="btn_simulate"):
        if st.session_state.plan_result and 'waypoints' in st.session_state.plan_result:
            st.session_state.is_simulating = True
            st.session_state.frame_count = 0
        else:
            st.warning("请先生成规划！")

    if st.button("⏹️ 停止仿真", key="btn_stop"):
        st.session_state.is_simulating = False

# 主界面布局
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 规划解释")
    if st.session_state.plan_result:
        if 'error' in st.session_state.plan_result:
            st.error(f"错误：{st.session_state.plan_result['error']}")
        else:
            status = st.session_state.plan_result.get('validation_status', 'UNKNOWN')
            safe_dist = st.session_state.safe_distance

            if status == 'SAFE':
                st.success(f"✅ 路径验证状态：安全")
            elif status == 'RISKY':
                st.warning(f"⚠️ 路径验证状态：存在风险")
            else:
                st.error("❌ 路径验证状态：失败")

            st.info(st.session_state.plan_result.get('explanation', '无解释'))

            if 'waypoints' in st.session_state.plan_result and len(st.session_state.plan_result['waypoints']) > 0:
                st.subheader(f"🔍 路径验证详情")
                waypoints = st.session_state.plan_result['waypoints']

                all_safe = True
                min_distances = []
                for i, wp in enumerate(waypoints):
                    wp_min_dist = float('inf')
                    for obs in obstacles:
                        if len(obs) >= 3:
                            dist = math.sqrt((wp['x'] - obs['x']) ** 2 + (wp['y'] - obs['y']) ** 2) - obs['radius']
                            if dist < wp_min_dist:
                                wp_min_dist = dist
                    min_distances.append(wp_min_dist)

                    if wp_min_dist < safe_dist:
                        st.error(f"⚠️ 航点{i}: 距边缘 {wp_min_dist:.1f}m < {safe_dist}m")
                        all_safe = False
                    elif wp_min_dist < safe_dist * 1.5:
                        st.warning(f"⚡ 航点{i}: 距边缘 {wp_min_dist:.1f}m")
                    else:
                        st.success(f"✅ 航点{i}: 距边缘 {wp_min_dist:.1f}m")

                if all_safe:
                    st.success(f"🎉 所有航点均满足安全距离要求！")

                if min_distances:
                    overall_min = min(min_distances)
                    st.metric("📏 路径最小安全距离", f"{overall_min:.1f}m")

            with st.expander("📄 查看完整 JSON"):
                st.json(st.session_state.plan_result)
    else:
        st.write("等待规划生成...")

with col2:
    st.subheader("🗺️ 实时海图监控")

    safe_dist = st.session_state.safe_distance

    # 创建基础图表
    fig = go.Figure()

    fig.update_layout(
        xaxis=dict(range=[-100, 100], title="X (m)", showgrid=True, gridcolor='lightgray'),
        yaxis=dict(range=[-100, 100], title="Y (m)", scaleanchor="x", scaleratio=1, showgrid=True,
                   gridcolor='lightgray'),
        width=600,
        height=500,
        plot_bgcolor='lightblue',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.8)')
    )

    # 1. 绘制圆形障碍物区域
    if obstacles:
        for i, obs in enumerate(obstacles):
            theta = [j * 2 * math.pi / 50 for j in range(51)]
            circle_x = [obs['x'] + obs['radius'] * math.cos(t) for t in theta]
            circle_y = [obs['y'] + obs['radius'] * math.sin(t) for t in theta]

            fig.add_trace(go.Scatter(
                x=circle_x, y=circle_y,
                fill='toself',
                fillcolor='rgba(255, 0, 0, 0.3)',
                line=dict(color='red', width=2),
                name=f'障碍物{i + 1}',
                mode='lines',
                hoverinfo='name',
                opacity=0.7
            ))

            safe_radius = obs['radius'] + safe_dist
            safe_x = [obs['x'] + safe_radius * math.cos(t) for t in theta]
            safe_y = [obs['y'] + safe_radius * math.sin(t) for t in theta]

            fig.add_trace(go.Scatter(
                x=safe_x, y=safe_y,
                fill='toself',
                fillcolor='rgba(255, 165, 0, 0.1)',
                line=dict(color='orange', width=1, dash='dash'),
                name=f'安全区{i + 1}',
                mode='lines',
                showlegend=False,
                opacity=0.5
            ))

    # 2. 绘制规划路径
    if st.session_state.plan_result and 'waypoints' in st.session_state.plan_result:
        waypoints = st.session_state.plan_result['waypoints']

        if len(waypoints) > 0:
            path_x = [p['x'] for p in waypoints]
            path_y = [p['y'] for p in waypoints]

            status = st.session_state.plan_result.get('validation_status', 'UNKNOWN')
            line_color = 'green' if status == 'SAFE' else ('orange' if status == 'RISKY' else 'red')

            fig.add_trace(go.Scatter(
                x=path_x, y=path_y,
                mode='lines+markers',
                line=dict(color=line_color, width=4),
                name='规划路径',
                marker=dict(size=6)
            ))

            # 添加船舶轨迹标记（初始位置）
            fig.add_trace(go.Scatter(
                x=[st.session_state.vessel.x],
                y=[st.session_state.vessel.y],
                mode='markers',
                marker=dict(color='green', size=20, symbol='triangle-up'),
                name='本船',
                uid='vessel_marker'
            ))

            # 仿真动画
            if st.session_state.is_simulating:
                vessel = st.session_state.vessel
                plot_placeholder = st.empty()
                progress_bar = st.progress(0)

                frame_count = 0

                for i, target in enumerate(waypoints):
                    if not st.session_state.is_simulating:
                        break

                    while True:
                        reached = vessel.update_position(target['x'], target['y'], speed=1.0)

                        # 复制基础图
                        fig_ship = go.Figure(fig)

                        # 更新船舶位置
                        fig_ship.data[-1].x = [vessel.x]
                        fig_ship.data[-1].y = [vessel.y]

                        # 计算距离信息
                        distances = []
                        for obs in obstacles:
                            dist_to_center = math.sqrt((vessel.x - obs['x']) ** 2 + (vessel.y - obs['y']) ** 2)
                            dist_to_edge = dist_to_center - obs['radius']

                            if dist_to_edge < safe_dist:
                                status_icon = "⚠️"
                            elif dist_to_edge < safe_dist * 1.5:
                                status_icon = "⚡"
                            else:
                                status_icon = "✅"

                            distances.append(f"{dist_to_edge:.1f}m{status_icon}")

                        # 添加距离标注
                        fig_ship.update_layout(
                            annotations=[
                                dict(
                                    x=0.5, y=1.02,
                                    xref='paper', yref='paper',
                                    text=f"📍 ({vessel.x:.1f}, {vessel.y:.1f}) | 距障碍物：{' | '.join(distances)}",
                                    showarrow=False,
                                    font=dict(size=10, color='darkblue'),
                                    bgcolor='rgba(255,255,255,0.9)',
                                    bordercolor='blue',
                                    borderwidth=1,
                                    borderpad=4
                                )
                            ],
                            transition=dict(duration=100),
                            uirevision='constant'
                        )

                        # 渲染图表
                        plot_placeholder.plotly_chart(
                            fig_ship,
                            use_container_width=True,
                            key=f"ship_frame_{frame_count}",
                            config={
                                'displayModeBar': False,
                                'displaylogo': False,
                                'responsive': True,
                                'scrollZoom': False
                            }
                        )
                        frame_count += 1

                        # 控制帧率
                        time.sleep(0.15)

                        if reached:
                            break

                    progress_bar.progress((i + 1) / len(waypoints))

                st.session_state.is_simulating = False
                st.success("仿真结束")
            else:
                # 静态显示
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="main_chart",
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'responsive': True
                    }
                )
        else:
            st.plotly_chart(fig, use_container_width=True, key="empty_chart")
    else:
        fig.add_trace(go.Scatter(
            x=[start_x], y=[start_y],
            mode='markers',
            name='起点',
            marker=dict(color='blue', size=15)
        ))
        st.plotly_chart(fig, use_container_width=True, key="empty_chart")
