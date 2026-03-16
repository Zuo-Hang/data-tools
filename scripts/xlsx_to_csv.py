"""
将 Excel (.xlsx) 文件转换为 CSV 格式
"""

import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("错误: 需要安装 pandas 和 openpyxl 库")
    print("请运行: pip install pandas openpyxl")
    sys.exit(1)


def xlsx_to_csv(xlsx_path: Path, output_path: Path = None, sheet_name: str | int = 0) -> Path:
    """
    将 xlsx 文件转换为 csv

    Args:
        xlsx_path: Excel 文件路径
        output_path: 输出 CSV 路径，默认与 xlsx 同目录同名
        sheet_name: 工作表名称或索引，默认第一个工作表

    Returns:
        输出 CSV 文件路径
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"文件不存在: {xlsx_path}")

    if output_path is None:
        output_path = xlsx_path.with_suffix(".csv")

    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"已转换: {xlsx_path} -> {output_path}")
    print(f"行数: {len(df)}, 列数: {len(df.columns)}")
    return output_path


def main():
    script_dir = Path(__file__).parent
    xlsx_path = script_dir / "data1" / "冒泡.xlsx"

    if len(sys.argv) > 1:
        xlsx_path = Path(sys.argv[1])

    xlsx_to_csv(xlsx_path)


if __name__ == "__main__":
    main()
