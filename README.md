# 🎯 多智能体政策讨论可视化系统

基于MetaGPT框架的智能政策制定与讨论系统，通过多个专业角色的协作讨论，实现政策的科学制定和优化。

## ✨ 系统特色

### 🤖 多智能体协作
- **7个专业角色**：政策制定者、经济专家、环境专家、法规专家、制造专家、物流专家、基建专家
- **智能权重分配**：不同角色具有不同的决策权重，确保专业性
- **动态共识机制**：自动检测讨论共识，智能决定讨论轮次

### 🎨 实时可视化界面
- **现代化UI设计**：基于Tailwind CSS和Alpine.js的响应式界面
- **实时消息流**：Server-Sent Events技术实现毫秒级更新
- **智能内容解析**：自动提取评分、建议、问题等结构化信息
- **多维度筛选**：支持按角色、轮次筛选查看讨论内容

### 📊 智能分析功能
- **轮次追踪**：清晰显示讨论进展（1-10轮）
- **评分系统**：1-10分评价体系，颜色编码直观展示
- **统计分析**：角色活跃度、平均评分、同意度分析
- **政策演进**：追踪政策修订历史和变化

## 🚀 快速开始

### 环境要求
```bash
# Python 3.8+
# Anaconda/Miniconda

# 创建虚拟环境
conda create -n metagpt python=3.9
conda activate metagpt

# 安装依赖
pip install -r requirements.txt
```

### 配置设置
1. 复制配置文件：
```bash
cp config/config.yaml.example config/config.yaml
```

2. 配置API密钥（在 `config/config.yaml` 中）：
```yaml
llm:
  api_type: "zhipuai"  # 或其他支持的LLM
  api_key: "your-api-key-here"
  model: "glm-4"
```

### 启动系统

#### 方法1：Web界面启动（推荐）
```bash
# 启动Web服务器
python web_server_new.py

# 访问 http://localhost:5001
# 点击"启动讨论"按钮，输入政策议题即可开始
```

#### 方法2：命令行启动
```bash
# 直接运行讨论
python main.py "您的政策议题"

# 自定义参数
python main.py "政策议题" --investment 3.0 --n_round 10
```

## 🎯 使用示例

### 政策议题示例
- "建立分层低空空域区域与动态无人机交通管理系统"
- "制定新能源汽车产业发展扶持政策"
- "建立城市智能交通管理系统"
- "发展数字经济产业园区政策"

### 讨论流程
1. **议题输入** → 系统接收政策议题
2. **专家分析** → 各角色从专业角度分析
3. **政策修订** → 政策部门基于反馈修订政策
4. **共识检查** → 系统评估是否达成共识
5. **输出结果** → 生成最终政策文件

## 📁 项目结构

```
├── main.py                 # 核心讨论逻辑
├── web_server_new.py       # Web服务器和API
├── templates_new/          # 前端模板
│   └── dashboard.html      # 主界面
├── config/                 # 配置文件
├── logs/                   # 讨论日志
├── requirements.txt        # 依赖包列表
└── README.md              # 项目说明
```

## 🔧 核心功能

### 智能角色系统
- **政策部门（35%权重）**：主导政策制定和修订
- **经济顾问（15%权重）**：宏观与产业经济分析
- **合规律师（15%权重）**：法律合规性审查
- **环境学家（10%权重）**：环境影响评估
- **制造商（10%权重）**：生产制造可行性
- **物流公司（10%权重）**：运营效率分析
- **基建公司（5%权重）**：基础设施建设

### 共识达成机制
- **最小轮次**：3轮（确保充分讨论）
- **最大轮次**：10轮（防止无限循环）
- **共识分数**：≥85分（加权平均）
- **实质变更**：≥2次政策修订

## 🎨 界面功能

### 左侧面板
- **角色卡片**：显示头像、权重、发言统计
- **实时统计**：总发言数、活跃角色、平均评分
- **轮次筛选**：按讨论轮次筛选消息

### 右侧面板
- **消息流**：实时显示专家发言
- **结构化显示**：自动解析问题、建议、评分
- **智能标签**：评分颜色编码、同意度标识
- **轮次标识**：清晰显示每条消息所属轮次

### 控制功能
- **启动讨论**：输入议题开始新讨论
- **停止讨论**：中断当前讨论
- **清空数据**：清除历史讨论记录

## 🔄 技术架构

### 后端技术
- **MetaGPT框架**：多智能体协作引擎
- **Flask**：Web服务器和API
- **Server-Sent Events**：实时数据推送
- **异步处理**：多线程讨论执行

### 前端技术
- **Alpine.js**：轻量级响应式框架
- **Tailwind CSS**：现代化UI样式
- **EventSource API**：实时消息接收
- **响应式设计**：支持多设备访问

## 📊 数据流程

```
用户输入议题 → MetaGPT多智能体讨论 → 日志记录 → 
实时解析 → API接口 → 前端显示 → 用户交互
```

## 🛠️ 自定义配置

### 修改角色权重
在 `main.py` 中的 `ConsensusChecker.weights` 调整各角色权重。

### 调整讨论参数
- `min_round`：最小讨论轮次
- `min_score`：最小共识分数
- `min_change`：最小实质变更数

### 自定义角色
在 `web_server_new.py` 的 `ROLES_CONFIG` 中添加新角色配置。

## 🔍 故障排除

### 常见问题
1. **API密钥错误**：检查 `config/config.yaml` 中的配置
2. **端口占用**：修改 `web_server_new.py` 中的端口号
3. **依赖缺失**：运行 `pip install -r requirements.txt`
4. **日志文件占用**：使用"清空数据"功能清理

### 调试模式
```bash
# 启用调试模式
export DEBUG_PARSING=1
python web_server_new.py
```

## 📝 更新日志

### v1.0.0
- ✅ 完整的多智能体讨论系统
- ✅ 实时Web可视化界面
- ✅ 智能共识检测机制
- ✅ 轮次追踪和统计分析
- ✅ 数据清空和管理功能

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
git clone https://github.com/your-username/multi-agent-policy-discussion.git
cd multi-agent-policy-discussion
conda create -n dev python=3.9
conda activate dev
pip install -r requirements.txt
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [MetaGPT](https://github.com/geekan/MetaGPT) - 多智能体框架
- [Tailwind CSS](https://tailwindcss.com/) - UI框架
- [Alpine.js](https://alpinejs.dev/) - JavaScript框架

## 📞 联系方式

如有问题或建议，请提交Issue或联系：
- GitHub Issues: [项目Issues页面]
- Email: [您的邮箱]

---

⭐ 如果这个项目对您有帮助，请给个Star支持一下！
