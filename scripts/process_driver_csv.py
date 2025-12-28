"""
处理driver_new.csv文件，随机抽取50条数据，生成Excel文件
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import pandas as pd
except ImportError:
    print("错误: 需要安装pandas和openpyxl库")
    print("请运行: pip install pandas openpyxl")
    sys.exit(1)

from data_tools.input import read_csv


def process_driver_data(csv_path: Path, output_path: Path = None, sample_size: int = 50) -> pd.DataFrame:
    """
    读取并处理driver CSV文件，随机抽取指定数量的记录

    Args:
        csv_path: CSV文件路径
        output_path: 输出Excel文件路径，如果为None则自动生成
        sample_size: 随机抽取的记录数量，默认50条

    Returns:
        处理后的DataFrame（随机抽取后的数据）
    """
    print(f"正在读取CSV文件: {csv_path}")
    
    # 读取CSV文件（使用制表符分隔）
    data = read_csv(csv_path, delimiter="\t")
    
    # 转换为DataFrame
    df = pd.DataFrame(data)
    
    print(f"成功读取 {len(df)} 行数据")
    print(f"列数: {len(df.columns)}")
    
    # 随机抽取指定数量的记录
    if len(df) > sample_size:
        print(f"随机抽取 {sample_size} 条记录...")
        df = df.sample(n=sample_size, random_state=None).reset_index(drop=True)
        print(f"已抽取 {len(df)} 条记录")
    else:
        print(f"数据总数 {len(df)} 条，少于抽取数量 {sample_size}，使用全部数据")
    
    # 定义列顺序（按照用户指定的顺序）
    column_order = [
        'images', 'estimate_id', 'supplier_name', 'driver_id', 'driver_last_name',
        'car_type', 'car_number', 'product_type', 'start_date', 'end_date',
        'summary_order_count', 'driver_cancel_count', 'online_duration',
        'peak_online_duration', 'ok_server_day_count', 'serve_duration',
        'income_amount', 'reward_amount', 'performance_order_count',
        'source_type', 'city_name', 'activity_name', 'city_illegal', 'platform'
    ]
    
    # 重新排列列顺序：指定的列在前，其他列在后
    ordered_columns = []
    # 先添加指定顺序中存在的列
    for col in column_order:
        if col in df.columns:
            ordered_columns.append(col)
    
    # 然后添加其他不在指定顺序中的列
    other_columns = [col for col in df.columns if col not in ordered_columns]
    ordered_columns.extend(other_columns)
    
    # 重新排列DataFrame的列
    df = df[ordered_columns]
    
    print(f"列已重新排序，共 {len(ordered_columns)} 列")
    
    # 生成输出文件路径
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = csv_path.parent / f"driver_new_processed_{timestamp}.xlsx"
    
    print(f"\n正在生成Excel文件: {output_path}")
    
    # 写入Excel文件
    df.to_excel(output_path, sheet_name='数据', index=False, engine='openpyxl')
    
    print(f"Excel文件已成功生成: {output_path}")
    print(f"共写入 {len(df)} 条记录")
    return df


def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    csv_file = script_dir / "data" / "driver_new.csv"
    
    # 检查文件是否存在
    if not csv_file.exists():
        print(f"错误: 文件不存在 {csv_file}")
        sys.exit(1)
    
    # 处理数据并生成Excel
    try:
        df = process_driver_data(csv_file)
        print("\n处理完成！")
        print(f"数据预览（前5行）:")
        print(df.head())
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

