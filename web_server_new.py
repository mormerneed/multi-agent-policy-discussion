#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional, List, Dict

from flask import Flask, Response, render_template, jsonify, request
import html
import subprocess
import threading
import asyncio
import platform

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
TEMPLATES_DIR = BASE_DIR / "templates_new"
STATIC_DIR = BASE_DIR / "static_new"

# 全局状态管理
discussion_status = {
    "is_running": False,
    "current_topic": "",
    "start_time": None,
    "process": None,
    "progress": ""
}

# 角色配置
ROLES_CONFIG = {
    "政策部门": {
        "name": "政策制定者",
        "avatar": "🏛️",
        "color": "#2563EB",
        "bg_color": "#EFF6FF",
        "description": "主导政策制定和修订",
        "weight": 0.35
    },
    "经济顾问": {
        "name": "经济专家", 
        "avatar": "📈",
        "color": "#059669",
        "bg_color": "#ECFDF5",
        "description": "宏观与产业经济分析",
        "weight": 0.15
    },
    "环境学家": {
        "name": "环境专家",
        "avatar": "🌿", 
        "color": "#16A34A",
        "bg_color": "#F0FDF4",
        "description": "环境影响评估",
        "weight": 0.10
    },
    "合规律师": {
        "name": "法规专家",
        "avatar": "⚖️",
        "color": "#D97706", 
        "bg_color": "#FFFBEB",
        "description": "法律合规性审查",
        "weight": 0.15
    },
    "制造商": {
        "name": "制造专家",
        "avatar": "🏭",
        "color": "#7C3AED",
        "bg_color": "#F5F3FF", 
        "description": "生产制造可行性",
        "weight": 0.10
    },
    "物流公司": {
        "name": "物流专家",
        "avatar": "🚚",
        "color": "#0891B2",
        "bg_color": "#F0F9FF",
        "description": "运营效率分析", 
        "weight": 0.10
    },
    "基建公司": {
        "name": "基建专家",
        "avatar": "🏗️",
        "color": "#DC2626",
        "bg_color": "#FEF2F2",
        "description": "基础设施建设",
        "weight": 0.05
    }
}

def find_latest_log_file() -> Optional[Path]:
    """查找最新的日志文件"""
    if not LOG_DIR.exists():
        return None
    log_files = sorted(LOG_DIR.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    return log_files[0] if log_files else None

def parse_log_message(line: str) -> Optional[Dict]:
    """解析日志消息"""
    try:
        # 查找 publish_message: 部分
        if "publish_message:" not in line:
            return None
        
        # 提取JSON部分 - 找到 "publish_message: " 后的JSON
        marker = "publish_message: "
        json_start = line.find(marker)
        if json_start == -1:
            return None
        
        json_start += len(marker)
        json_str = line[json_start:].strip()
        
        # 解析JSON - 处理可能的多余数据
        try:
            message_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # 如果有多余数据，尝试只解析第一个完整的JSON对象
            if "Extra data" in str(e):
                # 找到第一个完整的JSON对象
                brace_count = 0
                json_end = 0
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end > 0:
                    clean_json = json_str[:json_end]
                    message_data = json.loads(clean_json)
                else:
                    return None
            else:
                return None
        
        # 提取时间戳
        timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else ""
        
        return {
            "id": message_data.get("id", ""),
            "content": message_data.get("content", ""),
            "role": message_data.get("role", ""),
            "sent_from": message_data.get("sent_from", ""),
            "send_to": message_data.get("send_to", []),
            "cause_by": message_data.get("cause_by", ""),
            "timestamp": timestamp
        }
    except Exception as e:
        # 只在调试时输出错误，避免控制台刷屏
        if "DEBUG_PARSING" in os.environ:
            print(f"解析消息失败: {e}")
        return None

def extract_structured_content(content: str, role: str) -> Dict:
    """提取结构化内容"""
    result = {
        "raw_content": content,
        "sections": {},
        "score": None,
        "agreement": None
    }
    
    # 提取评分
    score_patterns = [
        r"可接受性评分[:：]\s*(\d+)/10",
        r"环境影响评分[:：]\s*(\d+)/10", 
        r"合规风险评分[:：]\s*(\d+)/10",
        r"可制造性评分[:：]\s*(\d+)/10",
        r"运营可行性评分[:：]\s*(\d+)/10",
        r"基础设施可行性评分[:：]\s*(\d+)/10"
    ]
    
    for pattern in score_patterns:
        match = re.search(pattern, content)
        if match:
            result["score"] = int(match.group(1))
            break
    
    # 提取同意程度
    agreement_match = re.search(r"同意程度[:：]\s*(强烈反对|反对|中立|同意|强烈同意)", content)
    if agreement_match:
        result["agreement"] = agreement_match.group(1)
    
    # 根据角色提取不同的结构化信息
    if "关键经济问题" in content:
        result["sections"]["problems"] = extract_numbered_list(content, "关键经济问题")
        result["sections"]["suggestions"] = extract_bullet_list(content, "建议改进")
    elif "关键环境问题" in content:
        result["sections"]["problems"] = extract_numbered_list(content, "关键环境问题") 
        result["sections"]["suggestions"] = extract_bullet_list(content, "建议改进")
    elif "法规合规问题" in content:
        result["sections"]["problems"] = extract_numbered_list(content, "法规合规问题")
        result["sections"]["suggestions"] = extract_bullet_list(content, "建议修改")
    elif "制造问题" in content:
        result["sections"]["problems"] = extract_numbered_list(content, "制造问题")
        result["sections"]["suggestions"] = extract_bullet_list(content, "建议修改") 
    elif "物流运营问题" in content:
        result["sections"]["problems"] = extract_numbered_list(content, "物流运营问题")
        result["sections"]["suggestions"] = extract_bullet_list(content, "建议修改")
    elif "基础设施开发问题" in content:
        result["sections"]["problems"] = extract_numbered_list(content, "基础设施开发问题")
        result["sections"]["suggestions"] = extract_bullet_list(content, "建议修改")
    elif "修订后的政策" in content:
        # 提取政策内容
        policy_match = re.search(r"修订后的政策[:：]\s*(.*?)\s*所做修改", content, re.DOTALL)
        if policy_match:
            result["sections"]["policy"] = policy_match.group(1).strip()
        result["sections"]["changes"] = extract_numbered_list(content, "所做修改")
    
    return result

def extract_numbered_list(text: str, section_name: str) -> List[str]:
    """提取编号列表"""
    try:
        # 找到section开始位置
        start_pattern = f"{section_name}[:：]"
        start_match = re.search(start_pattern, text)
        if not start_match:
            return []
        
        # 从section开始位置提取内容
        start_pos = start_match.end()
        remaining_text = text[start_pos:]
        
        # 查找下一个section或结束
        next_section_patterns = [
            r"\n\n[^0-9\-\s].*[:：]",  # 下一个section
            r"\n建议改进[:：]",
            r"\n建议修改[:：]", 
            r"\n可接受性评分[:：]",
            r"\n环境影响评分[:：]",
            r"\n合规风险评分[:：]",
            r"\n可制造性评分[:：]",
            r"\n运营可行性评分[:：]",
            r"\n基础设施可行性评分[:：]",
            r"\n同意程度[:：]"
        ]
        
        end_pos = len(remaining_text)
        for pattern in next_section_patterns:
            match = re.search(pattern, remaining_text)
            if match:
                end_pos = min(end_pos, match.start())
        
        section_text = remaining_text[:end_pos].strip()
        
        # 提取编号项目
        items = []
        lines = section_text.split('\n')
        current_item = ""
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line):  # 以数字开头
                if current_item:
                    items.append(current_item.strip())
                current_item = line
            elif current_item and line:  # 续行
                current_item += " " + line
        
        if current_item:
            items.append(current_item.strip())
        
        return items
    except Exception:
        return []

def extract_bullet_list(text: str, section_name: str) -> List[str]:
    """提取项目符号列表"""
    try:
        start_pattern = f"{section_name}[:：]"
        start_match = re.search(start_pattern, text)
        if not start_match:
            return []
        
        start_pos = start_match.end()
        remaining_text = text[start_pos:]
        
        # 查找下一个section
        next_section_patterns = [
            r"\n\n[^-\s].*[:：]",
            r"\n可接受性评分[:：]",
            r"\n环境影响评分[:：]", 
            r"\n合规风险评分[:：]",
            r"\n可制造性评分[:：]",
            r"\n运营可行性评分[:：]",
            r"\n基础设施可行性评分[:：]",
            r"\n同意程度[:：]"
        ]
        
        end_pos = len(remaining_text)
        for pattern in next_section_patterns:
            match = re.search(pattern, remaining_text)
            if match:
                end_pos = min(end_pos, match.start())
        
        section_text = remaining_text[:end_pos].strip()
        
        # 提取项目符号项目
        items = []
        lines = section_text.split('\n')
        current_item = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                if current_item:
                    items.append(current_item.strip())
                current_item = line[1:].strip()  # 去掉符号
            elif current_item and line:
                current_item += " " + line
        
        if current_item:
            items.append(current_item.strip())
        
        return items
    except Exception:
        return []

def extract_round_info(messages: List[Dict]) -> List[Dict]:
    """从消息中提取轮次信息"""
    if not messages:
        return messages
    
    current_round = 1
    policy_revisions = 0  # 政策修订计数
    max_rounds = 10  # 最大轮次限制
    
    for i, message in enumerate(messages):
        content = message.get("content", "")
        role = message.get("role", "")
        
        # 查找明确的轮次标识（如果日志中有的话）
        round_match = re.search(r'第\s*(\d+)\s*轮', content)
        if round_match:
            explicit_round = int(round_match.group(1))
            # 确保不超过最大轮次
            current_round = min(explicit_round, max_rounds)
        
        # 为消息添加轮次信息
        message["round"] = current_round
        
        # 根据政策修订来推断轮次变化
        # 政策部门的政策修订通常标志着一轮讨论的结束
        if role == "政策部门" and "修订后的政策" in content:
            policy_revisions += 1
            # 每次政策修订后，如果还有后续消息，则开始新轮次
            if i < len(messages) - 1 and current_round < max_rounds:
                current_round += 1
        
        # 另一种轮次推断方式：基于消息序列模式
        # 如果是经济顾问的第一条消息，且前面已有政策修订，可能是新轮次
        elif role == "经济顾问" and policy_revisions > 0:
            # 检查前面是否刚有政策修订
            if i > 0 and messages[i-1].get("role") == "政策部门":
                # 保持当前轮次不变，因为已经在上面的逻辑中处理了
                pass
    
    # 最后检查：确保所有消息的轮次都不超过最大值
    for message in messages:
        if message.get("round", 1) > max_rounds:
            message["round"] = max_rounds
    
    return messages

def get_discussion_data() -> Dict:
    """获取讨论数据"""
    latest_log = find_latest_log_file()
    if not latest_log:
        return {"messages": [], "stats": {}}
    
    messages = []
    role_stats = {role: {"message_count": 0, "total_score": 0, "agreements": []} 
                  for role in ROLES_CONFIG.keys()}
    
    with latest_log.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            msg = parse_log_message(line)
            if not msg or not msg["content"].strip():
                continue
            
            # 映射角色名称
            display_role = None
            
            # 角色映射表
            role_mapping = {
                "首席经济学家": "经济顾问",
                "环境科学家": "环境学家", 
                "航空法规专家": "合规律师",
                "无人机生产主管": "制造商",
                "航空物流总监": "物流公司",
                "基础设施开发经理": "基建公司",
                "高级政策制定者": "政策部门"
            }
            
            # 先尝试直接映射
            for role_key in ROLES_CONFIG.keys():
                if (role_key in msg["sent_from"] or 
                    role_key in msg["role"]):
                    display_role = role_key
                    break
            
            # 如果直接映射失败，尝试通过映射表
            if not display_role:
                for profile, role_key in role_mapping.items():
                    if profile in msg["role"] or profile in msg["sent_from"]:
                        display_role = role_key
                        break
            
            # 如果还是没找到，跳过这条消息
            if not display_role:
                continue
            
            # 解析结构化内容
            structured = extract_structured_content(msg["content"], display_role)
            
            message = {
                "id": msg["id"],
                "role": display_role,
                "role_config": ROLES_CONFIG[display_role],
                "content": msg["content"],
                "structured": structured,
                "timestamp": msg["timestamp"],
                "send_to": msg["send_to"]
            }
            
            messages.append(message)
            
            # 更新统计信息
            role_stats[display_role]["message_count"] += 1
            if structured["score"] is not None:
                role_stats[display_role]["total_score"] += structured["score"]
            if structured["agreement"]:
                role_stats[display_role]["agreements"].append(structured["agreement"])
    
    # 计算平均分数
    for role, stats in role_stats.items():
        if stats["message_count"] > 0 and stats["total_score"] > 0:
            stats["avg_score"] = stats["total_score"] / len([m for m in messages 
                                                           if m["role"] == role and m["structured"]["score"]])
        else:
            stats["avg_score"] = 0
    
    # 提取轮次信息
    messages = extract_round_info(messages)
    
    return {
        "messages": messages,
        "stats": role_stats,
        "total_messages": len(messages),
        "latest_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def clear_old_logs():
    """清空旧的日志文件"""
    try:
        if LOG_DIR.exists():
            for log_file in LOG_DIR.glob("*.txt"):
                try:
                    # 首先尝试直接删除
                    log_file.unlink()
                    print(f"✅ 已删除: {log_file.name}")
                except PermissionError:
                    # 如果文件被占用，尝试清空内容而不是删除
                    try:
                        log_file.write_text("", encoding="utf-8")
                        print(f"✅ 已清空内容: {log_file.name}")
                    except Exception as e2:
                        print(f"⚠️ 无法清空 {log_file.name}: {e2}")
                except Exception as e1:
                    print(f"⚠️ 无法删除 {log_file.name}: {e1}")
        
        LOG_DIR.mkdir(exist_ok=True)
        print("✅ 日志清理完成")
    except Exception as e:
        print(f"⚠️ 清空日志文件时出错: {e}")

def force_clear_logs():
    """强制清空日志文件（更激进的方法）"""
    global discussion_status
    
    try:
        # 1. 停止当前讨论进程
        if discussion_status.get("process"):
            try:
                discussion_status["process"].terminate()
                discussion_status["process"].wait(timeout=5)
                print("✅ 已停止讨论进程")
            except:
                try:
                    discussion_status["process"].kill()
                    print("✅ 已强制终止讨论进程")
                except:
                    pass
            discussion_status["process"] = None
            discussion_status["is_running"] = False
        
        # 2. 等待一下让文件句柄释放
        import time
        time.sleep(1)
        
        # 3. 清空日志
        clear_old_logs()
        
    except Exception as e:
        print(f"⚠️ 强制清空失败: {e}")

def create_timestamped_log_dir():
    """为每次讨论创建带时间戳的日志目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_log_dir = LOG_DIR / f"discussion_{timestamp}"
    timestamped_log_dir.mkdir(parents=True, exist_ok=True)
    return timestamped_log_dir

def run_discussion_async(topic: str):
    """在后台异步运行政策讨论"""
    global discussion_status
    
    try:
        discussion_status["is_running"] = True
        discussion_status["current_topic"] = topic
        discussion_status["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        discussion_status["progress"] = "正在清理旧数据..."
        
        # 清空旧的日志文件，确保新讨论有干净的开始
        clear_old_logs()
        
        discussion_status["progress"] = "正在启动讨论..."
        
        # 构建命令
        if platform.system() == "Windows":
            cmd = ["python", "main.py", topic]
        else:
            cmd = ["python3", "main.py", topic]
        
        print(f"🚀 启动新讨论: {topic}")
        print(f"📝 命令: {' '.join(cmd)}")
        
        # 启动进程，确保输出到控制台以便调试
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 合并stderr到stdout
            text=True,
            cwd=BASE_DIR,
            bufsize=1,
            universal_newlines=True
        )
        
        discussion_status["process"] = process
        discussion_status["progress"] = "讨论进行中..."
        
        # 实时输出进程信息（用于调试）
        print("📊 进程输出:")
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"   {output.strip()}")
        
        # 获取最终返回码
        return_code = process.poll()
        
        if return_code == 0:
            discussion_status["progress"] = "讨论已完成"
            print("✅ 讨论成功完成")
        else:
            discussion_status["progress"] = f"讨论出错，返回码: {return_code}"
            print(f"❌ 讨论失败，返回码: {return_code}")
        
    except Exception as e:
        discussion_status["progress"] = f"启动失败: {str(e)}"
        print(f"❌ 启动失败: {e}")
    finally:
        discussion_status["is_running"] = False
        discussion_status["process"] = None

def start_discussion_thread(topic: str):
    """在新线程中启动讨论"""
    thread = threading.Thread(target=run_discussion_async, args=(topic,))
    thread.daemon = True
    thread.start()

# Flask应用
app = Flask(__name__, 
           template_folder=str(TEMPLATES_DIR),
           static_folder=str(STATIC_DIR))

@app.route("/")
def index():
    """主页 - 显示多智能体讨论面板"""
    data = get_discussion_data()
    return render_template("dashboard.html", 
                         roles=ROLES_CONFIG,
                         data=data,
                         now=datetime.now())

@app.route("/api/discussion")
def api_discussion():
    """获取讨论数据API"""
    return jsonify(get_discussion_data())

@app.route("/api/messages/stream")
def stream_messages():
    """实时消息流"""
    def generate():
        latest_log = find_latest_log_file()
        if not latest_log:
            yield f"data: {json.dumps({'type': 'error', 'message': '未找到日志文件'})}\n\n"
            return
        
        # 先发送现有消息
        data = get_discussion_data()
        yield f"data: {json.dumps({'type': 'init', 'data': data})}\n\n"
        
        # 监听新消息
        with latest_log.open("r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    msg = parse_log_message(line)
                    if msg and msg["content"].strip():
                        # 映射角色
                        display_role = None
                        
                        # 角色映射表
                        role_mapping = {
                            "首席经济学家": "经济顾问",
                            "环境科学家": "环境学家", 
                            "航空法规专家": "合规律师",
                            "无人机生产主管": "制造商",
                            "航空物流总监": "物流公司",
                            "基础设施开发经理": "基建公司",
                            "高级政策制定者": "政策部门"
                        }
                        
                        # 先尝试直接映射
                        for role_key in ROLES_CONFIG.keys():
                            if role_key in msg["sent_from"] or role_key in msg["role"]:
                                display_role = role_key
                                break
                        
                        # 如果直接映射失败，尝试通过映射表
                        if not display_role:
                            for profile, role_key in role_mapping.items():
                                if profile in msg["role"] or profile in msg["sent_from"]:
                                    display_role = role_key
                                    break
                        
                        if display_role:
                            structured = extract_structured_content(msg["content"], display_role)
                            message = {
                                "id": msg["id"],
                                "role": display_role,
                                "role_config": ROLES_CONFIG[display_role],
                                "content": msg["content"],
                                "structured": structured,
                                "timestamp": msg["timestamp"],
                                "round": 1  # 新消息默认为当前轮次，后续会更新
                            }
                            yield f"data: {json.dumps({'type': 'message', 'message': message})}\n\n"
                else:
                    time.sleep(1)
    
    return Response(generate(), mimetype="text/event-stream")

@app.route("/api/stats")
def api_stats():
    """获取统计信息"""
    data = get_discussion_data()
    return jsonify(data["stats"])

@app.route("/api/start_discussion", methods=["POST"])
def api_start_discussion():
    """启动新的政策讨论"""
    global discussion_status
    
    if discussion_status["is_running"]:
        return jsonify({
            "success": False,
            "message": "讨论已在进行中，请等待完成"
        }), 400
    
    data = request.get_json()
    if not data or not data.get("topic"):
        return jsonify({
            "success": False,
            "message": "请提供讨论主题"
        }), 400
    
    topic = data["topic"].strip()
    if not topic:
        return jsonify({
            "success": False,
            "message": "讨论主题不能为空"
        }), 400
    
    try:
        start_discussion_thread(topic)
        return jsonify({
            "success": True,
            "message": "讨论已启动",
            "topic": topic
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"启动失败: {str(e)}"
        }), 500

@app.route("/api/discussion_status")
def api_discussion_status():
    """获取讨论状态"""
    # 创建一个可序列化的状态副本，排除Popen对象
    safe_status = {
        "is_running": discussion_status.get("is_running", False),
        "current_topic": discussion_status.get("current_topic", ""),
        "start_time": discussion_status.get("start_time", ""),
        "progress": discussion_status.get("progress", ""),
        # 不包含 "process" 字段，因为Popen对象无法JSON序列化
    }
    return jsonify(safe_status)

@app.route("/api/stop_discussion", methods=["POST"])
def api_stop_discussion():
    """停止当前讨论"""
    global discussion_status
    
    if not discussion_status["is_running"]:
        return jsonify({
            "success": False,
            "message": "没有正在运行的讨论"
        })
    
    try:
        if discussion_status["process"]:
            discussion_status["process"].terminate()
            discussion_status["progress"] = "讨论已停止"
            discussion_status["is_running"] = False
            discussion_status["process"] = None
        
        return jsonify({
            "success": True,
            "message": "讨论已停止"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"停止失败: {str(e)}"
        }), 500

@app.route("/api/clear_data", methods=["POST"])
def api_clear_data():
    """清空旧数据"""
    try:
        force_clear_logs()
        return jsonify({
            "success": True,
            "message": "数据已清空"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"清空失败: {str(e)}"
        }), 500

if __name__ == "__main__":
    # 确保目录存在
    TEMPLATES_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(exist_ok=True)
    
    app.run(host="127.0.0.1", port=5001, debug=True, threaded=True)
