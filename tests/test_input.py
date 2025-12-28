"""
数据输入模块测试
"""

import tempfile
from pathlib import Path
import pytest
from data_tools.input import CSVReader, read_csv, load_csv_file


def test_csv_reader_basic():
    """测试CSVReader基本功能"""
    # 创建临时CSV文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age,city\n")
        f.write("Alice,25,Beijing\n")
        f.write("Bob,30,Shanghai\n")
        temp_path = f.name

    try:
        reader = CSVReader(temp_path)
        data = reader.read_all()

        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[0]["age"] == "25"
        assert data[1]["name"] == "Bob"

        headers = reader.get_headers()
        assert headers == ["name", "age", "city"]

        row_count = reader.get_row_count()
        assert row_count == 2

    finally:
        Path(temp_path).unlink()


def test_csv_reader_iterator():
    """测试CSVReader迭代器功能"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\n")
        f.write("Alice,25\n")
        f.write("Bob,30\n")
        temp_path = f.name

    try:
        reader = CSVReader(temp_path)
        rows = list(reader.read_iterator())

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[1]["name"] == "Bob"

    finally:
        Path(temp_path).unlink()


def test_csv_reader_chunks():
    """测试CSVReader分块读取功能"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("id,value\n")
        for i in range(5):
            f.write(f"{i},{i*10}\n")
        temp_path = f.name

    try:
        reader = CSVReader(temp_path)
        chunks = list(reader.read_chunks(chunk_size=2))

        assert len(chunks) == 3  # 5行数据，每块2行，需要3块
        assert len(chunks[0]) == 2
        assert len(chunks[2]) == 1  # 最后一块只有1行

    finally:
        Path(temp_path).unlink()


def test_csv_reader_filter():
    """测试CSVReader过滤功能"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\n")
        f.write("Alice,25\n")
        f.write("Bob,30\n")
        f.write("Charlie,25\n")
        temp_path = f.name

    try:
        reader = CSVReader(temp_path)
        filtered = reader.filter_rows(lambda row: row["age"] == "25")

        assert len(filtered) == 2
        assert all(row["age"] == "25" for row in filtered)

    finally:
        Path(temp_path).unlink()


def test_read_csv_function():
    """测试read_csv便捷函数"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\n")
        f.write("Alice,25\n")
        temp_path = f.name

    try:
        data = read_csv(temp_path)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Alice"

        data_list = read_csv(temp_path, as_dict=False)
        assert isinstance(data_list, list)
        assert len(data_list) == 2  # 包括标题行

    finally:
        Path(temp_path).unlink()


def test_load_csv_file():
    """测试load_csv_file函数"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age\n")
        f.write("Alice,25\n")
        temp_path = f.name

    try:
        reader = load_csv_file(temp_path)
        assert isinstance(reader, CSVReader)
        assert reader.get_row_count() == 1

    finally:
        Path(temp_path).unlink()


def test_csv_reader_file_not_found():
    """测试文件不存在的情况"""
    with pytest.raises(FileNotFoundError):
        CSVReader("nonexistent_file.csv")

