import os
import re


def extract_cmd_values(
    input_path: str = "scripts/data/b.log",
    output_path: str = "scripts/data/fusion.log",
) -> None:
    """
    从每一行中提取 `cmd=` 后到空白字符前的内容，写入新的 fusion.log。
    例如：
        sum/cmd=dict_xxx\t123\t456
    会提取出：dict_xxx
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    pattern = re.compile(r"cmd=([^\s]+)")

    with open(input_path, "r", encoding="utf-8") as fin, open(
        output_path, "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            match = pattern.search(line)
            if not match:
                continue
            cmd_value = match.group(1)
            fout.write(cmd_value + "\n")


if __name__ == "__main__":
    extract_cmd_values()

