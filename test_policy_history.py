#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试政策修订历史功能
"""

import webbrowser
import time
import subprocess
import sys
from pathlib import Path

def main():
    print("📜 启动政策修订历史测试")
    print("=" * 50)
    
    # 启动web服务器
    print("📡 启动Web服务器...")
    try:
        server_process = subprocess.Popen([
            sys.executable, "web_server_new.py"
        ], cwd=Path(__file__).parent)
        
        # 等待服务器启动
        print("⏳ 等待服务器启动...")
        time.sleep(3)
        
        # 打开浏览器到不同页面
        print("🌐 打开浏览器...")
        
        # 主讨论面板
        webbrowser.open("http://127.0.0.1:5001/")
        time.sleep(1)
        
        # 政策修订历史
        webbrowser.open("http://127.0.0.1:5001/history")
        time.sleep(1)
        
        print("✅ 测试环境已启动！")
        print("\n📋 功能测试清单:")
        print("1. 🏠 主面板 (http://127.0.0.1:5001/)")
        print("   - 启动一个政策讨论")
        print("   - 观察专家们的讨论过程")
        print("")
        print("2. 📜 修订历史 (http://127.0.0.1:5001/history)")
        print("   - 查看政策版本的时间线")
        print("   - 对比不同版本的政策内容")
        print("   - 查看每次修改的具体变更")
        print("   - ✨ 新功能：查看促成修改的专家建议")
        print("   - 测试三种视图模式:")
        print("     • 时间线视图 - 看到政策演进过程和专家建议")
        print("     • 对比视图 - 详细对比两个版本")
        print("     • 变更列表 - 查看所有修改记录")
        print("")
        print("🎯 重点测试 - 专家建议追踪:")
        print("• 启动讨论后，观察专家建议如何影响政策修订")
        print("• 查看每个政策版本下方的'促成修改的专家建议'部分")
        print("• 观察建议与修改之间的关联性和相关度评分")
        print("• 查看匹配的关键词和建议分类")
        print("• 测试专家建议的实时更新和统计")
        print("")
        print("按 Ctrl+C 停止服务器")
        
        # 保持运行
        server_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 停止服务器...")
        server_process.terminate()
        server_process.wait()
        print("✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
