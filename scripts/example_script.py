"""
示例脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径，以便导入 data_tools
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """主函数"""
    print("这是一个示例脚本")
    print(f"项目根目录: {project_root}")


if __name__ == "__main__":
    main()

