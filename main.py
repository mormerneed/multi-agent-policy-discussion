# 目前对话流程还有问题
# 现状：经济学家提出问题政策提出者解决，环境学家提出问题，政策提出者解决，以此类推
# 希望：政策提出后，每位专家可以自由发言

import asyncio
import platform
from typing import Any, Dict, List
from difflib import SequenceMatcher
import logging

import fire

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入MetaGPT，如果失败则使用简化版本
try:
    from metagpt.logs import logger as metagpt_logger
    from metagpt.roles import Role
    from metagpt.schema import Message
    from metagpt.team import Team
    from metagpt.actions import Action, UserRequirement
    METAGPT_AVAILABLE = True
    logger.info("MetaGPT导入成功")
except ImportError as e:
    logger.warning(f"MetaGPT导入失败: {e}")
    logger.info("使用简化版本...")
    METAGPT_AVAILABLE = False
    
    # 创建简化的类
    class Message:
        def __init__(self, content="", role="", cause_by=None, sent_from="", send_to=None):
            self.content = content
            self.role = role
            self.cause_by = cause_by
            self.sent_from = sent_from
            self.send_to = send_to
    
    class Action:
        def __init__(self):
            self.name = "Action"
        
        async def _aask(self, prompt):
            # 使用真正的AI API
            try:
                import openai
                client = openai.OpenAI(
                    api_key="9c4b5e32f28a435fad45e813335d9c0e.cGnGRKpzYc6esxB4",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                
                response = client.chat.completions.create(
                    model="qwen-plus",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"AI API调用失败: {e}")
                # 如果API失败，使用模拟响应
                return self._get_mock_response(prompt)
        
        def _get_mock_response(self, prompt):
            """生成模拟响应"""
            if "政策部门" in prompt or "政策制定者" in prompt:
                return """
修订后的政策:
建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营

具体措施：
1. 设立低空空域分层管理制度，分为禁飞区、限制区和开放区
2. 建立无人机交通管理系统，实现实时监控和调度
3. 制定商业无人机运营标准和准入条件
4. 建立安全监管机制和应急响应体系

所做修改:
1. 增加了分层管理制度的详细说明
2. 明确了商业运营的具体条件
"""
            elif "经济顾问" in prompt or "经济学家" in prompt:
                return """
关键经济问题:
1. 空域资源利用效率问题 - 需要量化空域使用率和经济效益
2. 监管成本与市场活力的平衡 - 过严监管可能抑制创新
3. 基础设施建设投资回报 - 需要明确投资规模和预期收益

建议改进:
- 建议建立空域使用费制度，提高资源利用效率
- 建议设立产业发展基金，支持技术创新

可接受性评分: 7/10
同意程度: 同意
"""
            elif "环境学家" in prompt or "环境科学家" in prompt:
                return """
关键环境问题:
1. 噪音污染控制 - 需要制定分贝限制标准
2. 碳排放影响 - 无人机运营会增加碳排放
3. 野生动物干扰 - 低空飞行可能影响鸟类栖息

建议改进:
- 建议在生态敏感区域设立禁飞区
- 建议推广电动无人机，减少碳排放

环境影响评分: 6/10
同意程度: 中立
"""
            elif "合规律师" in prompt or "法规专家" in prompt:
                return """
法规合规问题:
1. 空域管理权限问题 - 需要明确各级管理权限
2. 责任划分不明确 - 事故责任归属需要明确
3. 国际标准对接 - 需要符合国际民航组织标准

建议修改:
- 建议明确空域管理部门的职责分工
- 建议建立责任保险制度

合规风险评分: 5/10
同意程度: 反对
"""
            elif "制造商" in prompt or "生产主管" in prompt:
                return """
制造问题:
1. 技术标准不统一 - 影响批量生产成本
2. 认证流程复杂 - 增加产品上市时间
3. 供应链管理 - 需要建立标准化供应链

建议修改:
- 建议制定统一的技术标准
- 建议简化认证流程

可制造性评分: 6/10
同意程度: 中立
"""
            elif "物流公司" in prompt or "物流总监" in prompt:
                return """
物流运营问题:
1. 空域使用限制 - 影响配送效率
2. 成本控制 - 需要平衡效率与成本
3. 可扩展性 - 需要支持大规模运营

建议修改:
- 建议优化空域分配机制
- 建议建立动态定价系统

运营可行性评分: 8/10
同意程度: 同意
"""
            elif "基建公司" in prompt or "基础设施" in prompt:
                return """
基础设施开发问题:
1. 建设成本高 - 需要大量投资
2. 技术标准 - 需要统一的技术规范
3. 维护管理 - 需要建立长期维护机制

建议修改:
- 建议分阶段建设，降低初期投资
- 建议建立标准化建设规范

基础设施可行性评分: 7/10
同意程度: 同意
"""
            else:
                return f"模拟响应: {prompt[:100]}..."
    
    class Role:
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'Role')
            self.profile = kwargs.get('profile', 'Role')
            self.rc = type('RC', (), {'news': [], 'todo': None, 'memory': type('Memory', (), {'add': lambda x: None})()})()
            self._watch = lambda x: None
            self.set_actions = lambda x: None
            self.get_memories = lambda: []
            self.actions = []
        
        async def _observe(self):
            return len(self.rc.news)
        
        async def _act(self):
            if self.actions:
                action = self.actions[0]()
                prompt = f"作为{self.profile}，请分析政策并提供专业意见。"
                response = await action._aask(prompt)
                return Message(content=response, role=self.profile, sent_from=self.name)
            return Message()
    
    class Team:
        def __init__(self):
            self.members = []
            self.idea = ""
        
        def hire(self, roles):
            self.members.extend(roles)
        
        def invest(self, amount):
            pass
        
        def run_project(self, idea, send_to=None):
            self.idea = idea
        
        async def run(self, n_round=1):
            for round_num in range(n_round):
                logger.info(f"\n=== 第 {round_num + 1} 轮讨论 ===")
                for member in self.members:
                    logger.info(f"\n--- {member.name} 发言 ---")
                    message = await member._act()
                    logger.info(message.content)
                    logger.info("-" * 40)
    
    class UserRequirement:
        pass

# 政策修订动作
class PolicyRevision(Action):
    # 基于经济学家反馈修订政策
    
    PROMPT_TEMPLATE: str = """
    ## 角色
    您是{name1}部门的高级政策制定者，您是低空经济政策制定的主导者，代表政策制定方。您在制定或修订低空经济政策时，
    需要明确权衡下列方面：
    - 政策稳定性和市场灵活行之间的矛盾
    - 专家的建议反馈与实施可行性之间的矛盾
    - 短期实施可行性与长期发展目标的平衡
    - 监管严格性与行业创新空间的权衡


    ## 规则
    1. 在评估和修订时应保持政策核心连续性（至少保留60%的原政策措辞）。
    2. 修改应当是有理由、可追溯且可实施的；不要为获得同意而无原则让步。
    3. 限定修改规模（最多3-5处关键修改）以避免频繁大幅变更引发不确定性。
    4. 在未解决重大合规或安全问题前，不做最终同意决定。
    5. 评分与同意程度对应关系：1-2分为强烈反对，3-4分为反对，5-6分为中立，7-8分为同意，9-10分为强烈同意

    ## 任务
    1. 阅读以下讨论历史并基于其内容修订政策：
    {context}
    2. 找出并解决反馈中至少2个关键问题或矛盾点。
    3. 最多可修改5个关键方面；为每项修改说明政策理由与预期影响（安全、合规、效率、成本）。
    4. 输出修订后的政策文本并列出所做修改。

    ## 输出格式
    修订后的政策:
    [政策文本]

    所做修改:
    1. [修改1及理由，来源反馈]
    2. [修改2及理由，来源反馈]
    """
    name: str = "PolicyRevision"

    async def run(self, context: str, name1: str, opponent_name1: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context, name1=name1, opponent_name1=opponent_name1)
        logger.debug(f"PolicyRevision prompt: {prompt[:200]}...")
        rsp = await self._aask(prompt)
        logger.debug(f"PolicyRevision response: {rsp}")
        if not rsp or rsp.strip() == "":
            logger.error("PolicyRevision returned empty response!")
            rsp = "错误：AI模型未返回有效响应，请检查API配置"
        return rsp

# 经济反馈动作
class EconomicFeedback(Action):
    # 提供严谨的经济分析
    
    PROMPT_TEMPLATE: str = """
    ## 角色
    您是{name2}研究院的首席经济学家，是低空经济政策制定的参与者，代表宏观与产业经济视角。
    您在评估低空经济政策时应考虑：
    - 短期经济效益与长期产业健康的平衡
    - 局部利益与整体经济效益的协调
    - 诗词昂自由竞争和必要监管干预的边界
    - 产业可持续性与创新激励之间的矛盾
    - 投资成本与预期收益的风险权衡

    ## 规则 
    1. 保持分析严谨、基于证据与可衡量指标。
    2. 所有结论需基于可验证的经济数据或模型。
    3. 兼顾定量（数据执政）与定性（趋势判断）视角
    4. 避免冗长：核心结论应简洁明确（最多100字的要点摘要）。
    5. 评分与同意程度对应关系：1-2分为强烈反对，3-4分为反对，5-6分为中立，7-8分为同意，9-10分为强烈同意


    ## 任务
    1. 阅读以下讨论历史：{context}，并进行政策经济性分析。
    2. 列出至少3个需要改进或关注的领域，并说明为何重要（用可量化指标或推理）。
    3. 提出2项可衡量的改进建议，包括预期经济收益数据。
    4. 对政策整体经济可行性进行1-10分评分，并明确同意程度


    ## 输出格式
    关键经济问题:
    1. [问题1及影响分析]
    2. [问题2及影响分析]
    3. [问题3及影响分析]


    建议改进:
    - [建议1及预期结果]
    - [建议2及预期结果]


    可接受性评分: [X/10]
    同意程度: [强烈反对/反对/中立/同意/强烈同意]
    """
    name: str = "EconomicFeedback"

    async def run(self, context: str, name2: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context, name2=name2)
        rsp = await self._aask(prompt)
        return rsp

# 环境反馈动作
class EnvironmentalFeedback(Action):
    # 评估政策对环境的影响
    
    PROMPT_TEMPLATE: str = """
    ## 角色
    您是{name}研究所的环境科学家，是低空经济政策制定的参与者，代表生态与可持续性视角。
    您在评估低空经济政策时应权衡：
    - 产业扩张需求与生态保护目标的冲突
    - 短期环境影响（如噪音/排放）与长期生态风险（如生物多样性）之间的平衡
    - 局部环境影响与区域生态系统的关联性
    - 噪音/排放/野生动物干扰等具体影响指标

    ## 规则
    1. 评估要基于证据和可量化指标（如噪音分贝、碳排放、生态扰动频率）。
    2. 建议需包含具体减排/保护指标，避免模糊表述
    3. 简洁但完整地呈现关键结论（最多100字的摘要）。
    4. 在重大环境问题未解前，不支持给予最终同意。
    5. 评分与同意程度对应关系：1-2分为强烈反对，3-4分为反对，5-6分为中立，7-8分为同意，9-10分为强烈同意


    ## 任务
    1. 阅读以下讨论历史：{context}，并评估政策的环境影响。
    2. 列出至少3个环境风险或潜在益处，并说明影响路径与可量化指标。
    3. 提出2项可量化的改进建议，包括预期环境改善效果
    4. 评估整体环境影响评分（1-10）。


    ## 输出格式
    关键环境问题:
    1. [问题1及影响分析]
    2. [问题2及影响分析]
    3. [问题3及影响分析]


    建议改进:
    - [建议1及预期结果]
    - [建议2及预期结果]


    环境影响评分: [X/10]
    同意程度: [强烈反对/反对/中立/同意/强烈同意]
    """
    name: str = "EnvironmentalFeedback"

    async def run(self, context: str, name: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context, name=name)
        rsp = await self._aask(prompt)
        return rsp

# 法律合规审查动作
class LegalComplianceReview(Action):
    # 确保政策符合航空法规
    
    PROMPT_TEMPLATE: str = """
    ## 角色
    您是{name}，专门从事航空法规的合规律师，是低空经济政策制定的参与者，您代表法律与监管合规视角，
    应权衡：
    - 国家/地方法规与国际标准的协统一
    - 权利保障与责任划分的明确性要求
    - 合规成本对产业发展的影响
    - 监管灵活性需求与法律确定性原则的平衡


    ## 规则
    1. 引用具体法律、法规或标准以支持分析。
    2. 分析应突出潜在法律冲突与企业/政府的责任承担方式。
    3. 需明确区分"违反现行法"与"存在法律模糊性"
    4. 在重大合规风险未被可行替代方案解决前，不支持最终同意。
    5. 简洁但完整地呈现关键结论。
    6. 评分与同意程度对应关系：1-2分为强烈反对，3-4分为反对，5-6分为中立，7-8分为同意，9-10分为强烈同意


    ## 任务
    1. 阅读以下讨论历史：{context}，并从法律角度分析政策合规性。
    2. 列出至少1个法规合规问题，并引用相关法律条文或准则作为依据。
    3. 为每项合规问题提出法律上合理的修改建议或替代方案，并评估其可行性。
    4. 给出整体合规风险评分（1-10）。


    ## 输出格式
    法规合规问题:
    1. [问题1及法律依据]
    2. [问题2及法律依据]
    3. [问题3及法律依据]


    建议修改:
    - [修改1及法律理由]
    - [修改2及法律理由]


    合规风险评分: [X/10]
    同意程度: [强烈反对/反对/中立/同意/强烈同意]
    """
    name: str = "LegalComplianceReview"

    async def run(self, context: str, name: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context, name=name)
        rsp = await self._aask(prompt)
        return rsp

# 制造反馈动作
class ManufacturingFeedback(Action):
    # 评估政策对生产的影响
    
    PROMPT_TEMPLATE: str = """
        ## 角色
    您是{name}，是低空经济政策制定的参与者，代表无人机制造公司的产品/生产负责人。
    您在评估政策时应考虑：
    - 生产成本与交付时间（成本/速度） 
    - 制造成本控制与安全质量标准的协调
    - 技术创新需求与生产标准化要求的平衡
    - 供应链脆弱性与本地化生产的权衡


    ## 规则
    1. 分析应覆盖生产成本、时间表与对创新的影响。
    2. 需量化评估对生产成本和效率的影响。
    3. 分析需基于实际生产流程和技术可行性
    4. 在政策不支持可持续制造能力前，不支持最终同意。
    5. 简洁但完整地呈现关键结论（最多100字的摘要）。
    6. 评分与同意程度对应关系：1-2分为强烈反对，3-4分为反对，5-6分为中立，7-8分为同意，9-10分为强烈同意


    ## 任务
    1. 阅读以下讨论历史：{context}，并评估政策对制造与供应链的影响。
    2. 列出至少3个对制造业务的具体影响，并分析对成本和时间的影响。
    3. 提出行业友好的替代方案并给出实施时间表或阶段性里程碑。
    4. 给出整体可制造性评分（1-10）。


    ## 输出格式
    制造问题:
    1. [问题1及生产影响]
    2. [问题2及成本分析]
    3. [问题3及创新影响]


    建议修改:
    - [修改1及行业理由]
    - [修改2及实施时间表]


    可制造性评分: [X/10]
    同意程度: [强烈反对/反对/中立/同意/强烈同意]

    """
    name: str = "ManufacturingFeedback"

    async def run(self, context: str, name: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context, name=name)
        rsp = await self._aask(prompt)
        return rsp

# 物流反馈动作
class LogisticsFeedback(Action):
    # 评估政策对运营的影响
    
    PROMPT_TEMPLATE: str = """
    
    ## 角色
    您是低空经济政策制定的参与者，主要考虑航空物流和快递公司的权益，你需要从“遵守空域使用限制规定
    与充分运用空域以提高物流配送效率两者的平衡”角度评估政策对公司物流流转效率和新业务开展的影响


    ## 规则
    1. 分析要兼顾交付效率、成本和合规性，不以牺牲安全为代价提高效率。
    2. 提出替代方案时应具体、可操作并便于量化效果。
    3. 需考虑空域利用和交通管理的实际限制
    4. 只有在政策确实支持可扩展运营时才给出同意或强烈同意。
    5. 简洁但完整地呈现关键结论
    6. 评分与同意程度对应关系：1-2分为强烈反对，3-4分为反对，5-6分为中立，7-8分为同意，9-10分为强烈同意


    ## 任务
    1. 阅读以下讨论历史：{context}，并基于其评估政策对运营的影响。
    2. 找出至少3个运营挑战或机遇，并分别说明其对交付效率、成本结构或新业务开展的影响。
    3. 为提高效率提出至少2条具体的政策修改建议或运营优化方案，并说明理由与预期效益。
    4. 评估整体运营可行性并给出评分（1-10）。


    ## 输出格式
    物流运营问题:
    1. [问题1及效率影响]
    2. [问题2及可扩展性分析]
    3. [问题3及成本影响]


    建议修改:
    - [修改1及运营理由]
    - [修改2及效率预测]


    运营可行性评分: [X/10]
    同意程度: [强烈反对/反对/中立/同意/强烈同意]
    """
    name: str = "LogisticsFeedback"

    async def run(self, context: str, name: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context, name=name)
        rsp = await self._aask(prompt)
        return rsp

# 基础设施反馈动作
class InfrastructureFeedback(Action):
    # 评估政策对建设的影响
    
    PROMPT_TEMPLATE: str = """
    ## 角色
    您是{name}，代表基础设施开发公司，是低空经济政策制定的参与者，
    应从建设与系统集成角度评估政策影响，关注点包括：
    - 标准化建设与区域差异化需求的矛盾
    - 基础设施建设速度与质量安全的平衡
    - 新建设施与现有交通系统的整合与运营维护要求


    ## 规则
    1. 分析应包括建设成本、实施时间表与维护安排。
    2. 提出的替代方案应可量化、可分阶段实施。
    3. 需考虑与现有基础设施的兼容性
    4. 在政策未明确支持可行基础设施方案前，不支持最终同意。
    5. 简洁但完整地呈现关键结论
    6. 评分与同意程度对应关系：1-2分为强烈反对，3-4分为反对，5-6分为中立，7-8分为同意，9-10分为强烈同意


    ## 任务
    1. 阅读以下讨论历史：{context}，并评估政策对物理基础设施的影响。
    2. 列出至少2个基础设施挑战或需求，并分析对建设成本与实施时间表的影响。
    3. 提出一条可行的开发或整合替代方案，并给出实施路线图。
    4. 给出整体基础设施可行性评分（1-10）。


    ## 输出格式
    基础设施开发问题:
    1. [问题1及建设影响]
    2. [问题2及整合挑战]
    3. [问题3及维护要求]


    建议修改:
    - [修改1及开发理由]
    - [修改2及实施路线图]


    基础设施可行性评分: [X/10]
    同意程度: [强烈反对/反对/中立/同意/强烈同意]
    """
    name: str = "InfrastructureFeedback"

    async def run(self, context: str, name: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context, name=name)
        rsp = await self._aask(prompt)
        return rsp

# 政策制定者角色
class PolicyMaker(Role):
    name1: str = "政策部门"
    profile: str = "高级政策制定者"
    # 每轮最小修改数量
    min_changes_per_round: int = 1

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.policy_versions = []
        if METAGPT_AVAILABLE:
            self.set_actions([PolicyRevision])
            self._watch([UserRequirement, EconomicFeedback, EnvironmentalFeedback, 
                        LegalComplianceReview, ManufacturingFeedback, LogisticsFeedback, 
                        InfrastructureFeedback])
        else:
            self.actions = [PolicyRevision]

    async def _observe(self) -> int:
        await super()._observe()
        logger.debug(f"{self.name} 收到原始消息: {len(self.rc.news)} 条")
        valid_messages = []
        for msg in self.rc.news:
            # 1. 接收所有广播消息
            if msg.send_to is None:
                valid_messages.append(msg)
                continue
            # 2. 指向自己的消息
            targets = msg.send_to if isinstance(msg.send_to, (set, list)) else {msg.send_to}
            if self.name in targets:
                valid_messages.append(msg)
                continue
            # 3. 专家角色发出的消息
            if msg.sent_from in {
                "经济顾问", "环境学家", "合规律师",
                "制造商", "物流公司", "基建公司",
            }:
                valid_messages.append(msg)
                continue
            # 4. 用户需求生成的消息
            if msg.cause_by == UserRequirement:
                valid_messages.append(msg)
                continue
        self.rc.news = valid_messages
        logger.debug(f"{self.name} 处理后的消息: {len(self.rc.news)} 条")
        return len(self.rc.news)

    async def _act(self) -> Message:
        if METAGPT_AVAILABLE:
            logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
            todo = self.rc.todo

            memories = self.get_memories()
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memories)

            rsp = await todo.run(context=context, name1=self.name1, opponent_name1="专家团队")
            
            # 显示政策制定者的具体回复内容
            logger.info(f"\n=== {self.name} 的回复 ===")
            logger.info(rsp)
            logger.info("=" * 50)
            
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=type(todo),
                sent_from=self.name,
                send_to=None,
            )
            self.rc.memory.add(msg)
            self.policy_versions.append(rsp)
            return msg
        else:
            # 简化版本
            if self.actions:
                action = self.actions[0]()
                prompt = f"作为{self.profile}，请分析政策：建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营。请提供政策修订建议。"
                response = await action._aask(prompt)
                
                logger.info(f"\n=== {self.name} 的回复 ===")
                logger.info(response)
                logger.info("=" * 50)
                
                return Message(content=response, role=self.profile, sent_from=self.name)
            return Message()

# 所有专家的基类
class ExpertRole(Role):
    def __init__(self,**data:Any):
        super().__init__(**data)
        # 观察政策修订和其他专家的反馈
        self._watch([PolicyRevision, UserRequirement])
    
    async def _observe(self) -> int:
        await super()._observe()
        logger.debug(f"{self.name} 收到原始消息: {len(self.rc.news)} 条")
        valid_messages = []
        for msg in self.rc.news:
            # 1. 接收所有广播消息
            if msg.send_to is None:
                valid_messages.append(msg)
                continue
            # 2. 指向自己的消息
            targets = msg.send_to if isinstance(msg.send_to, (set, list)) else {msg.send_to}
            if self.name in targets:
                valid_messages.append(msg)
                continue
            # 3. 政策修订触发的消息
            if msg.cause_by == PolicyRevision:
                valid_messages.append(msg)
                continue
            # 4. 用户需求生成的消息
            if msg.cause_by == UserRequirement:
                valid_messages.append(msg)
                continue
        self.rc.news = valid_messages
        logger.debug(f"{self.name} 处理后的消息: {len(self.rc.news)} 条")
        return len(self.rc.news)
    

# 经济顾问角色
class EconomicAdvisor(ExpertRole):
    name2: str = "经济顾问"
    profile: str = "首席经济学家"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if METAGPT_AVAILABLE:
            self.set_actions([EconomicFeedback])
        else:
            self.actions = [EconomicFeedback]

    async def _act(self) -> Message:
        if METAGPT_AVAILABLE:
            logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
            todo = self.rc.todo

            memories = self.get_memories()
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memories)

            rsp = await todo.run(context=context, name2=self.name2)

            # 显示经济顾问的具体回复内容
            logger.info(f"\n=== {self.name} 的回复 ===")
            logger.info(rsp)
            logger.info("=" * 50)

            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=type(todo),
                sent_from=self.name,
                send_to={"政策部门"},
            )
            self.rc.memory.add(msg)
            return msg
        else:
            # 简化版本
            if self.actions:
                action = self.actions[0]()
                prompt = f"作为{self.profile}，请从经济角度分析政策：建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营。请提供经济分析和建议。"
                response = await action._aask(prompt)
                
                logger.info(f"\n=== {self.name} 的回复 ===")
                logger.info(response)
                logger.info("=" * 50)
                
                return Message(content=response, role=self.profile, sent_from=self.name)
            return Message()

# 环境学家角色
class Environmentalist(ExpertRole):
    name: str = "环境学家"
    profile: str = "环境科学家"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if METAGPT_AVAILABLE:
            self.set_actions([EnvironmentalFeedback])
        else:
            self.actions = [EnvironmentalFeedback]
    
    async def _act(self) -> Message:
        if METAGPT_AVAILABLE:
            logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
            todo = self.rc.todo
            
            memories = self.get_memories()
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memories)
            
            rsp = await todo.run(context=context, name=self.name)
            
            # 显示环境学家的具体回复内容
            logger.info(f"\n=== {self.name} 的回复 ===")
            logger.info(rsp)
            logger.info("=" * 50)
            
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=type(todo),
                sent_from=self.name,
                send_to={"政策部门"},
            )
            self.rc.memory.add(msg)
            return msg
        else:
            # 简化版本
            if self.actions:
                action = self.actions[0]()
                prompt = f"作为{self.profile}，请从环境角度分析政策：建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营。请提供环境影响分析和建议。"
                response = await action._aask(prompt)
                
                logger.info(f"\n=== {self.name} 的回复 ===")
                logger.info(response)
                logger.info("=" * 50)
                
                return Message(content=response, role=self.profile, sent_from=self.name)
            return Message()

# 合规律师角色
class ComplianceLawyer(ExpertRole):
    name: str = "合规律师"
    profile: str = "航空法规专家"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if METAGPT_AVAILABLE:
            self.set_actions([LegalComplianceReview])
        else:
            self.actions = [LegalComplianceReview]

    async def _act(self) -> Message:
        if METAGPT_AVAILABLE:
            logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
            todo = self.rc.todo
            
            memories = self.get_memories()
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memories)
            
            rsp = await todo.run(context=context, name=self.name)
            
            # 显示合规律师的具体回复内容
            logger.info(f"\n=== {self.name} 的回复 ===")
            logger.info(rsp)
            logger.info("=" * 50)
            
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=type(todo),
                sent_from=self.name,
                send_to={"政策部门"},
            )
            self.rc.memory.add(msg)
            return msg
        else:
            # 简化版本
            if self.actions:
                action = self.actions[0]()
                prompt = f"作为{self.profile}，请从法律合规角度分析政策：建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营。请提供法律合规分析和建议。"
                response = await action._aask(prompt)
                
                logger.info(f"\n=== {self.name} 的回复 ===")
                logger.info(response)
                logger.info("=" * 50)
                
                return Message(content=response, role=self.profile, sent_from=self.name)
            return Message()

# 制造商角色
class Manufacturer(ExpertRole):
    name: str = "制造商"
    profile: str = "无人机生产主管"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if METAGPT_AVAILABLE:
            self.set_actions([ManufacturingFeedback])
        else:
            self.actions = [ManufacturingFeedback]


    async def _act(self) -> Message:
        if METAGPT_AVAILABLE:
            logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
            todo = self.rc.todo
            
            memories = self.get_memories()
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memories)
            
            rsp = await todo.run(context=context, name=self.name)
            
            # 显示制造商的具体回复内容
            logger.info(f"\n=== {self.name} 的回复 ===")
            logger.info(rsp)
            logger.info("=" * 50)
            
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=type(todo),
                sent_from=self.name,
                send_to={"政策部门"},
            )
            self.rc.memory.add(msg)
            return msg
        else:
            # 简化版本
            if self.actions:
                action = self.actions[0]()
                prompt = f"作为{self.profile}，请从制造角度分析政策：建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营。请提供制造可行性分析和建议。"
                response = await action._aask(prompt)
                
                logger.info(f"\n=== {self.name} 的回复 ===")
                logger.info(response)
                logger.info("=" * 50)
                
                return Message(content=response, role=self.profile, sent_from=self.name)
            return Message()

# 物流公司角色
class LogisticsCompany(ExpertRole):
    name: str = "物流公司"
    profile: str = "航空物流总监"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if METAGPT_AVAILABLE:
            self.set_actions([LogisticsFeedback])
        else:
            self.actions = [LogisticsFeedback]
    
    async def _act(self) -> Message:
        if METAGPT_AVAILABLE:
            logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
            todo = self.rc.todo
            
            memories = self.get_memories()
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memories)
            
            rsp = await todo.run(context=context, name=self.name)
            
            # 显示物流公司的具体回复内容
            logger.info(f"\n=== {self.name} 的回复 ===")
            logger.info(rsp)
            logger.info("=" * 50)
            
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=type(todo),
                sent_from=self.name,
                send_to={"政策部门"},
            )
            self.rc.memory.add(msg)
            return msg
        else:
            # 简化版本
            if self.actions:
                action = self.actions[0]()
                prompt = f"作为{self.profile}，请从物流运营角度分析政策：建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营。请提供物流运营分析和建议。"
                response = await action._aask(prompt)
                
                logger.info(f"\n=== {self.name} 的回复 ===")
                logger.info(response)
                logger.info("=" * 50)
                
                return Message(content=response, role=self.profile, sent_from=self.name)
            return Message()

# 基建公司角色
class InfrastructureCompany(ExpertRole):
    name: str = "基建公司"
    profile: str = "基础设施开发经理"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if METAGPT_AVAILABLE:
            self.set_actions([InfrastructureFeedback])
        else:
            self.actions = [InfrastructureFeedback]
    
    async def _act(self) -> Message:
        if METAGPT_AVAILABLE:
            logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
            todo = self.rc.todo
            
            memories = self.get_memories()
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memories)
            
            rsp = await todo.run(context=context, name=self.name)
            
            # 显示基建公司的具体回复内容
            logger.info(f"\n=== {self.name} 的回复 ===")
            logger.info(rsp)
            logger.info("=" * 50)
            
            msg = Message(
                content=rsp,
                role=self.profile,
                cause_by=type(todo),
                sent_from=self.name,
                send_to={"政策部门"},
            )
            self.rc.memory.add(msg)
            return msg
        else:
            # 简化版本
            if self.actions:
                action = self.actions[0]()
                prompt = f"作为{self.profile}，请从基础设施角度分析政策：建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营。请提供基础设施分析和建议。"
                response = await action._aask(prompt)
                
                logger.info(f"\n=== {self.name} 的回复 ===")
                logger.info(response)
                logger.info("=" * 50)
                
                return Message(content=response, role=self.profile, sent_from=self.name)
            return Message()

# 检查共识
class ConsensusChecker:
    # 赞同关键词
    positive_words = ["强烈同意", "同意", "支持", "认可", "批准", "接受", "肯定"]
    # 反对关键词
    negative_words = ["强烈反对", "反对", "拒绝", "否决", "不同意", "否认", "不批准"]
    # 最小共识分数
    min_score = 85
    # 最小讨论轮数
    min_round = 3
    # 最小实质变更数
    min_change = 2
    # 政策最小差异要求
    min_diff = 0.25
    
    # 角色权重配置(你们可以自行再调整一下)
    weights = {
        "政策部门": 0.35,      # 政策制定者权重最高
        "经济顾问": 0.15,      # 经济专家权重次高
        "合规律师": 0.15,      # 法律合规性重要
        "环境学家": 0.10,      # 环境因素重要
        "制造商": 0.10,        # 制造可行性
        "物流公司": 0.10,      # 运营可行性
        "基建公司": 0.05       # 基础设施因素
    }

    @staticmethod
    def analyze(messages: List[Message], current_round: int) -> Dict[str, Any]:
        results = {
            # 共识分数
            "agree_score": 0,
            # 赞同分数
            "positive_score": 0,
            # 不赞同分数
            "negative_score": 0,
            # 中立分数
            "neutral_score": 0,
            # 关键议题
            "key_issues": [],
            # 政策变化幅度
            "substantial_changes": 0,
            # 政策版本
            "policy_versions": [],
            # 轮数要求是否达标（True or False)
            "meets_round_requirement": current_round >= ConsensusChecker.min_round,
            # 政策是否发生变化（True or False)
            "meets_change_requirement": False
        }

        if not messages:
            return results

        # 提取所有政策版本
        policy_versions = [msg.content for msg in messages if "修订后的政策:" in msg.content]
        results["policy_versions"] = policy_versions
        
        # 计算版本间差异
        substantial_changes = 0
        for i in range(1, len(policy_versions)):
            diff = ConsensusChecker.calculate_policy_diff(policy_versions[i-1], policy_versions[i])
            if diff >= ConsensusChecker.min_diff:
                substantial_changes += 1
        results["substantial_changes"] = substantial_changes
        results["meets_change_requirement"] = substantial_changes >= ConsensusChecker.min_change

        # 分析共识程度（带权重）
        for message in messages:
            role = message.role
            weight = ConsensusChecker.weights.get(role, 1)  # 默认权重 1

            
            content = message.content.lower()
            
            # 检查共识说明
            if "共识说明:" in content:
                results["positive_score"] += 2 * weight
                continue
            
            # 检查反对意见
            has_negative = any(neg in content for neg in ConsensusChecker.negative_words)
            # 检查赞同意见（确保没有被否定词修饰）
            has_positive = any(pos in content and not ConsensusChecker.is_negated(pos, content) 
                            for pos in ConsensusChecker.positive_words)

            if has_negative:
                score = 2 if "强烈" in content else 1
                results["negative_score"] += score * weight
            elif has_positive:
                score = 2 if "强烈" in content else 1
                results["positive_score"] += score * weight
            else:
                results["neutral_score"] += 1 * weight
        
        # 计算加权共识分数
        total_weight = sum(ConsensusChecker.weights.values())
        max_possible = total_weight * 2  # 每个角色最高可得2分
        
        # 分占比减去负分影响的20%
        if max_possible > 0:
            results["agree_score"] = max(0, min(100, 
                (results["positive_score"] / max_possible * 100) - 
                (results["negative_score"] / max_possible * 20)))
        else:
            results["agree_score"] = 0
            
        # 共识分数计算过程
        # 政策部门：强烈同意 (2×0.35=0.70)
        # 经济顾问：同意 (1×0.15=0.15)
        # 合规律师：反对 (1×0.15=0.15)
        # 环境学家：强烈同意 (2×0.10=0.20)
        # 制造商：同意 (1×0.10=0.10)
        # 物流公司：中立 (1×0.10=0.10)
        # 基建公司：中立 (1×0.05=0.05)

        # 积极分数 = 0.70 + 0.15 + 0.20 + 0.10 = 1.15
        # 消极分数 = 0.15
        # 最大可能分数 = 2.0
        # 积极占比 = 1.15 / 2.0 = 0.575
        # 消极影响 = 0.15 / 2.0 × 0.2 = 0.015
        # 共识分数 = (0.575 - 0.015) × 100 = 56.0
            
        if results["negative_score"] > 0:
            results["key_issues"] = ConsensusChecker.extract_issues(messages)
            
        return results

    @staticmethod
    def calculate_policy_diff(policy1: str, policy2: str) -> float:
        """计算两个政策版本之间的差异率（0-1）"""
        policy1_clean = policy1.split("修订后的政策:")[-1].strip()
        policy2_clean = policy2.split("修订后的政策:")[-1].strip()
        return 1 - SequenceMatcher(None, policy1_clean, policy2_clean).ratio()

    @staticmethod
    def is_negated(keyword: str, text: str) -> bool:
        """检查关键词是否被否定词修饰"""
        negation_words = ["不", "没有", "从未", "无", "缺少", "反对", "拒绝"]
        keyword_index = text.find(keyword)
        if keyword_index == -1:
            return False
        preceding_text = text[:keyword_index].strip()
        if not preceding_text:
            return False
        last_word = preceding_text.split()[-1]
        return last_word in negation_words

    @staticmethod
    def extract_issues(messages: List[Message]) -> List[str]:
        """提取关键分歧点"""
        issues = set()
        for message in messages:
            content = message.content.lower()
            if any(neg in content for neg in ConsensusChecker.negative_words):
                markers = ["因为", "由于", "鉴于", "原因:", "问题:"]
                for marker in markers:
                    if marker in content:
                        issue = content.split(marker)[-1].strip()
                        if issue and len(issue.split()) > 2:
                            issues.add(issue.capitalize())
                            break
        return list(issues)

    @staticmethod
    def reached(analysis_result: Dict[str, Any]) -> bool:
        """检查是否达成共识"""
        return (analysis_result["agree_score"] >= ConsensusChecker.min_score and
                analysis_result["meets_round_requirement"] and
                analysis_result["meets_change_requirement"])

# 政策推演流程
async def policy_development(idea: str, investment: float = 3.0, max_round: int = 10):
    # 运行政策推演流程
    # 初始化所有角色
    policy_maker = PolicyMaker(
        name="政策部门",
        name1="政策部门",
        profile="高级政策制定者",
    )
    
    economic_advisor = EconomicAdvisor(
        name="经济顾问",
        profile="首席经济学家",
    )
    
    environmentalist = Environmentalist(
        name="环境学家",
        profile="环境科学家",
    )
    
    compliance_lawyer = ComplianceLawyer(
        name="合规律师",
        profile="航空法规专家",
    )
    
    manufacturer = Manufacturer(
        name="制造商",
        profile="无人机生产主管",
    )
    
    logistics_company = LogisticsCompany(
        name="物流公司",
        profile="航空物流总监",
    )
    
    infrastructure_company = InfrastructureCompany(
        name="基建公司",
        profile="基础设施开发经理",
    )
    
    # 组建团队
    team = Team()
    team.hire([
        policy_maker, 
        economic_advisor,
        environmentalist,
        compliance_lawyer,
        manufacturer,
        logistics_company,
        infrastructure_company
    ])
    team.invest(investment)

    rounds = 0
    consensus = False
    round_results = []
    final_policy = ""

    # 多轮讨论
    while rounds < max_round and not consensus:
        rounds += 1
        team.run_project(idea, send_to="经济顾问")
        await team.run(n_round=2)  
        team.run_project(idea, send_to="环境学家")
        await team.run(n_round=2)
        team.run_project(idea, send_to="合规律师")
        await team.run(n_round=2) 
        team.run_project(idea, send_to="制造商")
        await team.run(n_round=2) 
        team.run_project(idea, send_to="物流公司")
        await team.run(n_round=2) 
        team.run_project(idea, send_to="基建公司")
        await team.run(n_round=2) 

        # 收集所有消息
        all_messages = []
        for role in [policy_maker, economic_advisor, environmentalist, compliance_lawyer, 
                    manufacturer, logistics_company, infrastructure_company]:
            all_messages.extend(role.get_memories())
            
        analysis = ConsensusChecker.analyze(all_messages, rounds)
        round_results.append(analysis)

        # 输出轮次摘要
        logger.info(f"\n=== 第 {rounds} 轮摘要 ===")
        logger.info(f"共识分数: {analysis['agree_score']:.1f}/100")
        logger.info(f"实质变更: {analysis['substantial_changes']}/{ConsensusChecker.min_change} 需满足")
        logger.info(f"完成轮数: {rounds}/{ConsensusChecker.min_round} 最低要求")
        
        # 输出关键问题
        if analysis["key_issues"]:
            logger.warning("未解决问题:")
            for issue in analysis["key_issues"]:
                logger.warning(f" - {issue}")
        
        consensus = ConsensusChecker.reached(analysis)
        
        # 强制最小讨论轮数
        if rounds < ConsensusChecker.min_round:
            logger.info("未达到最低讨论轮数，继续讨论...")
            consensus = False
        
        if analysis["substantial_changes"] < ConsensusChecker.min_change:
            logger.info("实质变更不足，继续讨论...")
            consensus = False

        # 保存最新政策版本
        if policy_maker.policy_versions:
            final_policy = policy_maker.policy_versions[-1]

    # 最终结果
    final_result = round_results[-1] if round_results else {}
    
    # 输出最终结果
    if consensus:
        logger.info("\n=== 达成最终共识 ===")
        logger.info(f"经过 {rounds} 轮讨论")
        logger.info(f"最终共识分数: {final_result['agree_score']:.1f}/100")
        logger.info(f"实质变更数量: {final_result['substantial_changes']}")
        
        logger.info("\n=== 最终政策 ===")
        logger.info(extract_policy_text(final_policy))
        
        logger.info("\n=== 政策演进过程 ===")
        for i, version in enumerate(policy_maker.policy_versions, 1):
            logger.info(f"\n版本 {i}:")
            logger.info(extract_policy_text(version))
    else:
        logger.warning("\n=== 讨论结束，未达成共识 ===")
        logger.warning(f"经过 {rounds} 轮讨论")
        logger.warning(f"最终共识分数: {final_result.get('agree_score', 0):.1f}/100")
        
        if policy_maker.policy_versions:
            logger.warning("\n最新政策草案:")
            logger.warning(extract_policy_text(final_policy))
        
        if final_result.get("key_issues"):
            logger.warning("\n未解决问题:")
            for issue in final_result["key_issues"]:
                logger.warning(f" - {issue}")
        
        logger.warning("\n未达成共识原因:")
        if rounds < ConsensusChecker.min_round:
            logger.warning(f"- 未达到最低 {ConsensusChecker.min_round} 轮讨论")
        if final_result.get('substantial_changes', 0) < ConsensusChecker.min_change:
            logger.warning(f"- 仅 {final_result.get('substantial_changes', 0)} 项实质变更（需要 {ConsensusChecker.min_change} 项）")
        if final_result.get('agree_score', 0) < ConsensusChecker.min_score:
            logger.warning(f"- 共识分数 {final_result.get('agree_score', 0):.1f} 低于最低要求 {ConsensusChecker.min_score}")

# 提取政策文本
def extract_policy_text(full_text: str) -> str:
    """从完整消息中提取政策部分"""
    if "修订后的政策:" in full_text:
        policy_part = full_text.split("修订后的政策:")[-1]
        return policy_part.split("所做修改:")[0].strip()
    return full_text

# 主函数
def main(idea: str, investment: float = 3.0, n_round: int = 10):
    """
    :param idea: 政策提案，例如 "对进口零部件征收40%的关税"

    :param investment: 讨论预算
    :param n_round: 最大讨论轮数（强制执行最低3轮）
    """
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    n_round = max(n_round, 3)
    asyncio.run(policy_development(idea, investment, n_round))

if __name__ == "__main__":
    fire.Fire(main)

# python main.py "建立分层低空空域区域与动态无人机交通管理系统，支持商业无人机运营"