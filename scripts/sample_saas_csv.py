"""
从 scripts/data/saas.csv 随机抽取指定数量的数据，生成新的 CSV 文件
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
    print("错误: 需要安装 pandas 库")
    print("请运行: pip install pandas")
    sys.exit(1)


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "scripts" / "data"
DEFAULT_INPUT = DATA_DIR / "saas.csv"


def sample_saas_data(
    csv_path: Path, 
    output_path: Path = None, 
    sample_size: int = 50,
    filter_city: str = None
) -> pd.DataFrame:
    """
    读取 saas.csv 文件，先过滤指定城市，然后随机抽取指定数量的记录，并保存为新的 CSV 文件

    Args:
        csv_path: 输入 CSV 文件路径
        output_path: 输出 CSV 文件路径，如果为 None 则自动生成
        sample_size: 随机抽取的记录数量，默认 50 条
        filter_city: 过滤的城市名称，如果为 None 则不进行过滤

    Returns:
        处理后的 DataFrame（随机抽取后的数据）
    """
    print(f"正在读取 CSV 文件: {csv_path}")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"文件不存在: {csv_path}")
    
    # 读取 CSV 文件
    df = pd.read_csv(csv_path, encoding="utf-8")
    
    print(f"成功读取 {len(df)} 行数据")
    print(f"列数: {len(df.columns)}")
    
    # 先进行城市过滤
    if filter_city:
        if 'city_name' not in df.columns:
            raise ValueError("CSV 文件中没有 'city_name' 列")
        
        original_count = len(df)
        df = df[df['city_name'] == filter_city].copy()
        filtered_count = len(df)
        
        print(f"\n过滤条件: city_name = '{filter_city}'")
        print(f"过滤前: {original_count} 条记录")
        print(f"过滤后: {filtered_count} 条记录")
        
        if filtered_count == 0:
            raise ValueError(f"没有找到 city_name='{filter_city}' 的记录")
    
    # 从过滤后的数据中随机抽取指定数量的记录
    if len(df) > sample_size:
        print(f"\n随机抽取 {sample_size} 条记录...")
        df_sampled = df.sample(n=sample_size, random_state=None).reset_index(drop=True)
        print(f"已抽取 {len(df_sampled)} 条记录")
    else:
        print(f"\n数据总数 {len(df)} 条，少于抽取数量 {sample_size}，使用全部数据")
        df_sampled = df
    
    # 生成输出文件路径
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        city_suffix = f"_{filter_city}" if filter_city else ""
        output_path = csv_path.parent / f"saas_sample_{sample_size}{city_suffix}_{timestamp}.csv"
    
    print(f"\n正在生成 CSV 文件: {output_path}")
    
    # 写入 CSV 文件
    df_sampled.to_csv(output_path, index=False, encoding="utf-8")
    
    print(f"CSV 文件已成功生成: {output_path}")
    print(f"共写入 {len(df_sampled)} 条记录")
    
    return df_sampled


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="从 scripts/data/saas.csv 随机抽取指定数量的数据，生成新的 CSV 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认输入路径，过滤石家庄市，抽取 50 条数据
  python scripts/sample_saas_csv.py

  # 指定输入和输出文件，抽取 50 条数据
  python scripts/sample_saas_csv.py \\
      --input scripts/data/saas.csv \\
      --output scripts/data/saas_sample_50.csv

  # 抽取 100 条数据
  python scripts/sample_saas_csv.py --sample-size 100

  # 过滤其他城市
  python scripts/sample_saas_csv.py --filter-city 北京市
        """,
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT),
        help="输入 CSV 文件路径（默认: scripts/data/saas.csv）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出 CSV 文件路径（默认: 自动生成，格式为 saas_sample_<数量>_<时间戳>.csv）",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=50,
        help="随机抽取的记录数量（默认: 50）",
    )
    parser.add_argument(
        "--filter-city",
        type=str,
        default="石家庄市",
        help="过滤的城市名称（默认: 石家庄市），设置为空字符串则不进行过滤",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None
    filter_city = args.filter_city if args.filter_city else None

    try:
        sample_saas_data(input_path, output_path, args.sample_size, filter_city)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
