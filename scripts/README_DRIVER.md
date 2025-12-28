# Driver CSV处理脚本使用说明

## 功能说明

`process_driver_csv.py` 脚本用于读取和解析 `data/driver_new.csv` 文件，并生成Excel文件。

## 功能特性

1. **读取CSV文件**：自动识别制表符分隔的CSV文件
2. **数据清理**：
   - 自动转换数值类型列
   - 自动转换日期类型列
3. **生成Excel文件**：包含多个工作表
   - **原始数据**：完整的CSV数据
   - **汇总统计**：总体统计信息（记录数、司机数、城市数、供应商数、总收入、总奖励等）
   - **按城市统计**：按城市分组统计收入、奖励和司机数
   - **按供应商统计**：按供应商分组统计收入、奖励和司机数

## 使用方法

### 1. 安装依赖

```bash
pip install pandas openpyxl
```

或者使用项目依赖：

```bash
pip install -e .
```

### 2. 运行脚本

```bash
# 在项目根目录运行
python3 scripts/process_driver_csv.py

# 或者在scripts目录下运行
cd scripts
python3 process_driver_csv.py
```

### 3. 输出文件

脚本会在 `scripts/data/` 目录下生成Excel文件，文件名格式为：
`driver_new_processed_YYYYMMDD_HHMMSS.xlsx`

## 自定义输出路径

可以修改脚本中的 `process_driver_data` 函数调用，指定自定义的输出路径：

```python
output_path = Path("自定义路径/output.xlsx")
df = process_driver_data(csv_file, output_path=output_path)
```

## 数据字段说明

CSV文件包含以下主要字段：
- `estimate_id`: 估算ID
- `supplier_name`: 供应商名称
- `driver_id`: 司机ID
- `driver_last_name`: 司机姓名
- `city_name`: 城市名称
- `start_date`: 开始日期
- `end_date`: 结束日期
- `income_amount`: 收入金额
- `reward_amount`: 奖励金额
- `performance_order_count`: 订单数量
- 等等...

## 注意事项

- CSV文件使用制表符（Tab）作为分隔符
- 脚本会自动处理缺失值和数据类型转换
- 生成的Excel文件使用openpyxl引擎，支持.xlsx格式

