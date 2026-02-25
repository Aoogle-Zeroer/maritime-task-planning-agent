<img width="995" height="323" alt="image" src="https://github.com/user-attachments/assets/06b74ca7-2a6c-456e-83db-2c0d3405296e" /># 🚢 海上作业任务规划智能体

基于大语言模型（LLM）的海上作业任务规划智能体，实现自然语言指令→路径规划→仿真演示的完整流程。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 核心功能

- 🗣️ **自然语言交互**：通过自然语言指令进行任务规划
- 🛡️ **可配置安全距离**：自定义船舶距障碍物的最小安全距离（5-50m）
- 🗺️ **实时可视化**：动态海图监控 + 仿真动画
- 🔄 **自动迭代优化**：LLM 自动迭代直到生成安全路径
- ✅ **路径验证**：验证航点及连线与障碍物的安全距离

## 🚀 快速开始

1. 克隆项目
bash
git clone https://github.com/YOUR_USERNAME/maritime-task-planning-agent.git
cd maritime-task-planning-agent

2. 安装依赖
bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

3. 配置 API 密钥
bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥

4. 运行应用
bash
streamlit run app.py

🏗️ 技术架构
┌─────────────────────────────────────┐
│         Streamlit GUI               │
│      (用户交互 + 可视化展示)          │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│    CollisionAvoidanceSkill          │
│    (LLM 路径规划 + 验证 + 迭代)       │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│         LiteLLM + LLM API           │
│    (DeepSeek / OpenAI / Ollama)     │
└─────────────────────────────────────┘

📁 项目结构
maritime-task-planning-agent/
├── .gitignore
├── .env.example
├── README.md
├── LICENSE
├── requirements.txt
├── config.py
├── app.py                        # 主程序
├── skills/
│   ├── __init__.py
│   └── collision_avoidance.py    # 避碰规划技能
├── simulator/
│   ├── __init__.py
│   └── vessel_mock.py            # 船舶运动模拟
├── utils/
│   ├── __init__.py
│   └── json_parser.py            # JSON 解析工具
└── docs/
    └── architecture.md           # 架构说明

🔧 配置选项
LLM 服务商配置  
服务商         	LLM_PROVIDER	  LLM_MODEL_NAME	          LLM_BASE_URL
DeepSeek	      deepseek      	deepseek-chat	            https://api.deepseek.com
OpenAI	        openai	        gpt-3.5-turbo	            https://api.openai.com/v1
OpenRouter	    openrouter	    deepseek/deepseek-chat	  https://openrouter.ai/api/v1
Ollama(本地)	  ollama	        qwen2.5	                  http://localhost:11434

📝 开发计划
 支持更多障碍物形状（多边形、矩形）
 集成真实 3-DOF/6-DOF 船舶运动模型
 添加历史路径记录功能
 支持多船协同规划
 集成 LangGraph 状态管理

🤝 贡献指南
欢迎提交 Issue 和 Pull Request！

1.Fork 本项目
2.创建功能分支 (git checkout -b feature/AmazingFeature)
3.提交更改 (git commit -m 'Add some AmazingFeature')
4.推送到分支 (git push origin feature/AmazingFeature)
5.开启 Pull Request
📄 许可证
本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情

📧 联系方式
作者：Aoogle-Zeroer
邮箱：2261542172@qq.com








