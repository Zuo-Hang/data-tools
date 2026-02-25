from pathlib import Path


def load_lines(path: Path) -> set[str]:
    """读取文件非空行，去掉首尾空白，返回去重集合。"""
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    lines: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            lines.add(s)
    return lines


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    task_path = base_dir / "data" / "task.log"
    fusion_path = base_dir / "data" / "fusion.log"

    task_set = load_lines(task_path)
    fusion_set = load_lines(fusion_path)

    common = sorted(task_set & fusion_set)

    print(f"task.log 行数: {len(task_set)}")
    print(f"fusion.log 行数: {len(fusion_set)}")
    print(f"相同行数量: {len(common)}\n")

    if common:
        print("相同的任务名：")
        for name in common:
            print(name)
    else:
        print("没有找到相同的任务名。")


if __name__ == "__main__":
    main()

