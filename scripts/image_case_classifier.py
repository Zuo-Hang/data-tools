"""
基于案例（Case）的图片分类脚本
预先准备案例图片并向量化，然后将新图片分类到最相似的案例类别
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.embedding import ImageEmbedding
import numpy as np


class CaseLibrary:
    """案例库管理类"""
    
    def __init__(self, library_path: Path = None):
        """
        初始化案例库
        
        Args:
            library_path: 案例库文件路径（JSON格式）
        """
        self.library_path = library_path or Path("case_library.json")
        # 支持每个类别有多个案例样例
        # {case_name: [{"path": str, "embedding": list, "description": str}, ...]}
        self.cases: Dict[str, List[Dict]] = {}
        # 用于快速查找的嵌入向量列表 {case_name: [embedding_array, ...]}
        self.embeddings: Dict[str, List[np.ndarray]] = {}
        self._load_library()
    
    def add_case(
        self,
        case_name: str,
        image_path: Path,
        embedding_model: ImageEmbedding,
        description: str = ""
    ) -> bool:
        """
        添加案例到案例库（追加模式，同一类别可以有多个样例）
        
        Args:
            case_name: 案例名称（类别名称）
            image_path: 案例图片路径
            embedding_model: 向量化模型
            description: 案例描述
            
        Returns:
            是否添加成功
        """
        try:
            # 向量化案例图片
            embedding = embedding_model.encode_image(image_path)
            if embedding is None:
                print(f"错误: 无法向量化案例图片 {image_path}")
                return False
            
            # 如果类别不存在，创建新列表
            if case_name not in self.cases:
                self.cases[case_name] = []
                self.embeddings[case_name] = []
            
            # 追加案例信息（支持同一类别多个样例）
            case_info = {
                "path": str(image_path),
                "embedding": embedding.tolist(),
                "description": description
            }
            self.cases[case_name].append(case_info)
            self.embeddings[case_name].append(embedding)
            
            print(f"✓ 添加案例: {case_name} ({len(self.cases[case_name])} 个样例) - {image_path}")
            return True
        except Exception as e:
            print(f"错误: 添加案例失败 {case_name}: {e}")
            return False
    
    def remove_case(self, case_name: str, case_index: int = None) -> bool:
        """
        删除案例
        
        Args:
            case_name: 案例名称
            case_index: 案例索引（如果为None，删除整个类别）
        """
        if case_name not in self.cases:
            return False
        
        if case_index is None:
            # 删除整个类别
            del self.cases[case_name]
            if case_name in self.embeddings:
                del self.embeddings[case_name]
            print(f"✓ 删除案例类别: {case_name}")
        else:
            # 删除指定索引的样例
            if 0 <= case_index < len(self.cases[case_name]):
                removed = self.cases[case_name].pop(case_index)
                self.embeddings[case_name].pop(case_index)
                print(f"✓ 删除案例样例: {case_name}[{case_index}] - {removed.get('path', '')}")
                # 如果类别为空，删除整个类别
                if len(self.cases[case_name]) == 0:
                    del self.cases[case_name]
                    del self.embeddings[case_name]
            else:
                print(f"错误: 索引 {case_index} 超出范围")
                return False
        return True
    
    def list_cases(self) -> List[str]:
        """列出所有案例名称"""
        return list(self.cases.keys())
    
    def get_case_info(self, case_name: str, case_index: int = None) -> Optional[Dict]:
        """
        获取案例信息
        
        Args:
            case_name: 案例名称
            case_index: 案例索引（如果为None，返回第一个）
        """
        if case_name not in self.cases:
            return None
        
        if case_index is None:
            # 返回第一个样例的信息
            return self.cases[case_name][0] if self.cases[case_name] else None
        else:
            if 0 <= case_index < len(self.cases[case_name]):
                return self.cases[case_name][case_index]
            return None
    
    def get_case_count(self, case_name: str) -> int:
        """获取某个类别的案例数量"""
        return len(self.cases.get(case_name, []))
    
    def save_library(self):
        """保存案例库到文件"""
        try:
            with open(self.library_path, 'w', encoding='utf-8') as f:
                json.dump(self.cases, f, ensure_ascii=False, indent=2)
            print(f"✓ 案例库已保存到: {self.library_path}")
            return True
        except Exception as e:
            print(f"错误: 保存案例库失败: {e}")
            return False
    
    def _load_library(self):
        """从文件加载案例库（支持追加模式）"""
        if self.library_path.exists():
            try:
                with open(self.library_path, 'r', encoding='utf-8') as f:
                    loaded_cases = json.load(f)
                
                # 兼容旧格式（单个案例）和新格式（案例列表）
                for case_name, case_data in loaded_cases.items():
                    # 如果是旧格式（单个字典），转换为列表格式
                    if isinstance(case_data, dict) and 'embedding' in case_data:
                        # 旧格式：单个案例
                        self.cases[case_name] = [case_data]
                        self.embeddings[case_name] = [
                            np.array(case_data['embedding'], dtype=np.float32)
                        ]
                    elif isinstance(case_data, list):
                        # 新格式：案例列表
                        self.cases[case_name] = case_data
                        self.embeddings[case_name] = [
                            np.array(item['embedding'], dtype=np.float32)
                            for item in case_data if 'embedding' in item
                        ]
                
                total_cases = sum(len(cases) for cases in self.cases.values())
                print(f"✓ 加载案例库: {len(self.cases)} 个类别，共 {total_cases} 个案例样例")
            except Exception as e:
                print(f"警告: 加载案例库失败: {e}")
                self.cases = {}
                self.embeddings = {}
        else:
            print(f"案例库文件不存在，将创建新库: {self.library_path}")


class CaseBasedClassifier:
    """基于案例的分类器"""
    
    def __init__(self, case_library: CaseLibrary, embedding_model: ImageEmbedding):
        """
        初始化分类器
        
        Args:
            case_library: 案例库
            embedding_model: 向量化模型
        """
        self.case_library = case_library
        self.embedding_model = embedding_model
    
    def classify_image(self, image_path: Path, top_k: int = 1) -> List[Tuple[str, float]]:
        """
        对单张图片进行分类（与所有案例样例比较，取最高相似度）
        
        Args:
            image_path: 图片路径
            top_k: 返回前k个最相似的案例类别
            
        Returns:
            分类结果列表，每个元素为 (案例名称, 相似度分数)
        """
        # 向量化图片
        embedding = self.embedding_model.encode_image(image_path)
        if embedding is None:
            return []
        
        # 与所有案例样例计算相似度，每个类别取最高相似度
        category_similarities = {}
        for case_name, case_embeddings_list in self.case_library.embeddings.items():
            # 计算与所有样例的相似度，取最大值
            max_similarity = -1.0
            for case_embedding in case_embeddings_list:
                similarity = self.embedding_model.compute_similarity(
                    embedding, case_embedding, method="cosine"
                )
                max_similarity = max(max_similarity, similarity)
            category_similarities[case_name] = max_similarity
        
        # 按相似度排序
        similarities = sorted(
            category_similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return similarities[:top_k]
    
    def classify_images(
        self,
        image_paths: List[Path],
        similarity_threshold: float = 0.0
    ) -> Dict[str, List[str]]:
        """
        批量分类图片
        
        Args:
            image_paths: 图片路径列表
            similarity_threshold: 相似度阈值，低于此阈值的图片归为"未分类"
            
        Returns:
            分类结果字典，键为案例名称，值为图片路径列表
        """
        results = defaultdict(list)
        unclassified = []
        
        print(f"正在分类 {len(image_paths)} 张图片...")
        
        for idx, image_path in enumerate(image_paths, 1):
            print(f"处理进度: {idx}/{len(image_paths)} - {image_path.name}", end='\r')
            
            # 分类图片
            classifications = self.classify_image(image_path, top_k=1)
            
            if classifications:
                case_name, similarity = classifications[0]
                
                if similarity >= similarity_threshold:
                    results[case_name].append(str(image_path))
                else:
                    unclassified.append(str(image_path))
            else:
                unclassified.append(str(image_path))
        
        print()  # 换行
        
        # 如果有未分类的图片，添加到结果中
        if unclassified:
            results["未分类"] = unclassified
        
        return dict(results)
    
    def print_classification_results(self, results: Dict[str, List[str]]):
        """打印分类结果"""
        print("\n" + "=" * 60)
        print(f"分类结果: 共 {len(results)} 个类别")
        print("=" * 60)
        
        total_images = sum(len(images) for images in results.values())
        print(f"总图片数: {total_images}\n")
        
        for case_name, image_paths in sorted(results.items()):
            case_info = self.case_library.get_case_info(case_name)
            case_count = self.case_library.get_case_count(case_name)
            description = case_info.get('description', '') if case_info else ''
            
            print(f"类别: {case_name}")
            if case_count > 1:
                print(f"  案例样例数: {case_count}")
            if description:
                print(f"  描述: {description}")
            print(f"  图片数量: {len(image_paths)}")
            print("-" * 60)
            for image_path in image_paths:
                print(f"  - {image_path}")
            print()
    
    def save_results(self, results: Dict[str, List[str]], output_path: Path, format: str = "json"):
        """保存分类结果"""
        output_path = Path(output_path)
        
        if format == "json":
            result_data = {
                "total_categories": len(results),
                "total_images": sum(len(images) for images in results.values()),
                "classifications": results
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        elif format == "txt":
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"分类结果: 共 {len(results)} 个类别\n")
                f.write(f"总图片数: {sum(len(images) for images in results.values())}\n")
                f.write("=" * 60 + "\n\n")
                
                for case_name, image_paths in sorted(results.items()):
                    case_info = self.case_library.get_case_info(case_name)
                    case_count = self.case_library.get_case_count(case_name)
                    description = case_info.get('description', '') if case_info else ''
                    
                    f.write(f"类别: {case_name}\n")
                    if case_count > 1:
                        f.write(f"  案例样例数: {case_count}\n")
                    if description:
                        f.write(f"  描述: {description}\n")
                    f.write(f"  图片数量: {len(image_paths)}\n")
                    f.write("-" * 60 + "\n")
                    for image_path in image_paths:
                        f.write(f"  - {image_path}\n")
                    f.write("\n")
        
        print(f"\n分类结果已保存到: {output_path}")


def collect_image_files(input_paths: List[str]) -> List[Path]:
    """收集图片文件路径"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    image_files = []
    
    for input_path in input_paths:
        path = Path(input_path)
        
        if path.is_file():
            if path.suffix.lower() in image_extensions:
                image_files.append(path)
        elif path.is_dir():
            for ext in image_extensions:
                image_files.extend(path.rglob(f'*{ext}'))
                image_files.extend(path.rglob(f'*{ext.upper()}'))
    
    return sorted(set(image_files))


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="基于案例的图片分类工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 添加案例
  %(prog)s add-case "首页" scripts/image/case1.jpg --description "首页模板"
  
  # 分类图片
  %(prog)s classify scripts/image/ --threshold 0.8
  
  # 列出所有案例
  %(prog)s list-cases
  
  # 删除案例
  %(prog)s remove-case "首页"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 添加案例命令
    add_parser = subparsers.add_parser('add-case', help='添加案例到案例库')
    add_parser.add_argument('case_name', help='案例名称（类别名称）')
    add_parser.add_argument('image_path', help='案例图片路径')
    add_parser.add_argument('--description', default='', help='案例描述')
    add_parser.add_argument('--library', default='case_library.json', help='案例库文件路径')
    add_parser.add_argument('--model', default='dinov2_vits14', help='模型名称')
    
    # 删除案例命令
    remove_parser = subparsers.add_parser('remove-case', help='从案例库删除案例')
    remove_parser.add_argument('case_name', help='案例名称')
    remove_parser.add_argument('--library', default='case_library.json', help='案例库文件路径')
    
    # 列出案例命令
    list_parser = subparsers.add_parser('list-cases', help='列出所有案例')
    list_parser.add_argument('--library', default='case_library.json', help='案例库文件路径')
    
    # 分类命令
    classify_parser = subparsers.add_parser('classify', help='对图片进行分类')
    classify_parser.add_argument('input_paths', nargs='+', help='图片文件或目录路径')
    classify_parser.add_argument('--threshold', type=float, default=0.0, help='相似度阈值')
    classify_parser.add_argument('--library', default='case_library.json', help='案例库文件路径')
    classify_parser.add_argument('--model', default='dinov2_vits14', help='模型名称')
    classify_parser.add_argument('--output', help='输出结果文件路径')
    classify_parser.add_argument('--format', choices=['json', 'txt'], default='json', help='输出格式')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        library_path = Path(args.library)
        case_library = CaseLibrary(library_path)
        
        if args.command == 'add-case':
            # 添加案例
            embedding_model = ImageEmbedding(model_name=args.model)
            case_library.add_case(
                args.case_name,
                Path(args.image_path),
                embedding_model,
                args.description
            )
            case_library.save_library()
        
        elif args.command == 'remove-case':
            # 删除案例
            if case_library.remove_case(args.case_name):
                case_library.save_library()
            else:
                print(f"错误: 案例 '{args.case_name}' 不存在")
        
        elif args.command == 'list-cases':
            # 列出案例
            cases = case_library.list_cases()
            if cases:
                print(f"\n案例库中共有 {len(cases)} 个案例:\n")
                for case_name in cases:
                    case_info = case_library.get_case_info(case_name)
                    description = case_info.get('description', '') if case_info else ''
                    print(f"  - {case_name}")
                    if description:
                        print(f"    描述: {description}")
                    print(f"    路径: {case_info.get('path', '')}")
                    print()
            else:
                print("案例库为空")
        
        elif args.command == 'classify':
            # 分类图片
            if len(case_library.cases) == 0:
                print("错误: 案例库为空，请先添加案例")
                sys.exit(1)
            
            # 收集图片
            image_files = collect_image_files(args.input_paths)
            if len(image_files) == 0:
                print("错误: 没有找到图片文件")
                sys.exit(1)
            
            print(f"找到 {len(image_files)} 张图片")
            
            # 初始化模型和分类器
            embedding_model = ImageEmbedding(model_name=args.model)
            classifier = CaseBasedClassifier(case_library, embedding_model)
            
            # 执行分类
            results = classifier.classify_images(image_files, similarity_threshold=args.threshold)
            
            # 输出结果
            classifier.print_classification_results(results)
            
            # 保存结果
            if args.output:
                output_path = Path(args.output)
                if not output_path.suffix:
                    output_path = output_path.with_suffix(f".{args.format}")
                classifier.save_results(results, output_path, format=args.format)
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

