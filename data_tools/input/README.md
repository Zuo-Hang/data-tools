# 数据输入模块

用于处理CSV格式文件的输入。

## 功能特性

- 支持CSV文件的完整读取
- 支持迭代器方式读取（适用于大文件）
- 支持分块读取
- 支持数据过滤
- 支持自定义编码和分隔符

## 使用示例

### 基本用法

```python
from data_tools.input import read_csv

# 读取CSV文件为字典列表
data = read_csv("data.csv")
for row in data:
    print(row["column_name"])
```

### 使用CSVReader类

```python
from data_tools.input import CSVReader

# 创建读取器
reader = CSVReader("data.csv")

# 读取所有数据
all_data = reader.read_all()

# 迭代读取（适用于大文件）
for row in reader.read_iterator():
    process(row)

# 分块读取
for chunk in reader.read_chunks(chunk_size=1000):
    process_chunk(chunk)

# 过滤数据
filtered = reader.filter_rows(lambda row: int(row["age"]) > 18)

# 获取列头
headers = reader.get_headers()

# 获取行数
count = reader.get_row_count()
```

### 使用load_csv_file函数

```python
from data_tools.input import load_csv_file

reader = load_csv_file("data.csv", encoding="utf-8", delimiter=",")
data = reader.read_all()
```

