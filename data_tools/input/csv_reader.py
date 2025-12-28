"""
CSV读取器类
提供CSV文件的读取和处理功能
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Union, Callable
import csv


class CSVReader:
    """CSV文件读取器"""

    def __init__(self, file_path: Union[str, Path], encoding: str = "utf-8", delimiter: str = ","):
        """
        初始化CSV读取器

        Args:
            file_path: CSV文件路径
            encoding: 文件编码，默认utf-8
            delimiter: 分隔符，默认逗号
        """
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.delimiter = delimiter

        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        if not self.file_path.is_file():
            raise ValueError(f"路径不是文件: {self.file_path}")

    def read_all(self) -> List[Dict[str, Any]]:
        """
        读取整个CSV文件

        Returns:
            包含所有行的字典列表，每行作为字典返回
        """
        data = []
        with open(self.file_path, "r", encoding=self.encoding, newline="") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            data = list(reader)
        return data

    def read_iterator(self) -> Iterator[Dict[str, Any]]:
        """
        返回迭代器，逐行读取CSV文件（适用于大文件）

        Yields:
            每行的字典
        """
        with open(self.file_path, "r", encoding=self.encoding, newline="") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            for row in reader:
                yield row

    def read_chunks(self, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        """
        分块读取CSV文件

        Args:
            chunk_size: 每块的大小

        Yields:
            包含多行数据的列表
        """
        chunk = []
        for row in self.read_iterator():
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:  # 返回剩余数据
            yield chunk

    def get_headers(self) -> List[str]:
        """
        获取CSV文件的列头

        Returns:
            列头列表
        """
        with open(self.file_path, "r", encoding=self.encoding, newline="") as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            headers = next(reader)
        return headers

    def get_row_count(self) -> int:
        """
        获取CSV文件的行数（不包括标题行）

        Returns:
            行数
        """
        with open(self.file_path, "r", encoding=self.encoding, newline="") as f:
            return sum(1 for _ in f) - 1  # 减去标题行

    def filter_rows(self, condition: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        """
        根据条件过滤行

        Args:
            condition: 过滤函数，接收字典参数，返回布尔值

        Returns:
            过滤后的行列表
        """
        return [row for row in self.read_iterator() if condition(row)]

