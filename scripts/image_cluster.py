"""
图片相似度聚类脚本
输入一批图片，通过向量化后根据相似度进行分类
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.embedding import ImageEmbedding
import numpy as np


class ImageCluster:
    """图片聚类类"""
    
    def __init__(self, embedding_model: ImageEmbedding, similarity_threshold: float = 0.85):
        """
        初始化图片聚类器
        
        Args:
            embedding_model: 图片向量化模型
            similarity_threshold: 相似度阈值，超过此阈值的图片被认为属于同一类
        """
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
    
    def cluster_images(self, image_paths: List[Path], similarity_threshold: float = None) -> Dict[int, List[str]]:
        """
        根据相似度对图片进行聚类
        
        Args:
            image_paths: 图片路径列表
            similarity_threshold: 相似度阈值，如果为None则使用初始化时的阈值
            
        Returns:
            聚类结果字典，键为类别ID，值为该类别的图片路径列表
        """
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
        
        # 1. 向量化所有图片
        print(f"正在向量化 {len(image_paths)} 张图片...")
        embeddings = []
        valid_paths = []
        
        for image_path in image_paths:
            embedding = self.embedding_model.encode_image(image_path)
            if embedding is not None:
                embeddings.append(embedding)
                valid_paths.append(str(image_path))
            else:
                print(f"警告: 无法向量化图片 {image_path}")
        
        if len(embeddings) == 0:
            print("错误: 没有成功向量化的图片")
            return {}
        
        print(f"成功向量化 {len(embeddings)} 张图片")
        
        # 2. 使用相似度阈值进行聚类
        print(f"正在根据相似度阈值 {similarity_threshold} 进行聚类...")
        clusters = self._cluster_by_similarity(embeddings, valid_paths, similarity_threshold)
        
        return clusters
    
    def _cluster_by_similarity(
        self,
        embeddings: List[np.ndarray],
        image_paths: List[str],
        similarity_threshold: float
    ) -> Dict[int, List[str]]:
        """
        基于相似度阈值进行聚类
        
        Args:
            embeddings: 向量列表
            image_paths: 对应的图片路径列表
            similarity_threshold: 相似度阈值
            
        Returns:
            聚类结果字典
        """
        clusters = {}
        cluster_id = 0
        assigned = [False] * len(embeddings)
        
        for i in range(len(embeddings)):
            if assigned[i]:
                continue
            
            # 创建新类别
            clusters[cluster_id] = [image_paths[i]]
            assigned[i] = True
            
            # 查找与当前图片相似的图片
            for j in range(i + 1, len(embeddings)):
                if assigned[j]:
                    continue
                
                # 计算相似度
                similarity = self.embedding_model.compute_similarity(
                    embeddings[i], embeddings[j], method="cosine"
                )
                
                # 如果相似度超过阈值，加入同一类别
                if similarity >= similarity_threshold:
                    clusters[cluster_id].append(image_paths[j])
                    assigned[j] = True
            
            cluster_id += 1
        
        return clusters
    
    def cluster_by_kmeans(self, image_paths: List[Path], n_clusters: int = None) -> Dict[int, List[str]]:
        """
        使用 KMeans 进行聚类（需要 sklearn）
        
        Args:
            image_paths: 图片路径列表
            n_clusters: 聚类数量，如果为None则自动确定
            
        Returns:
            聚类结果字典
        """
        try:
            from sklearn.cluster import KMeans
        except ImportError:
            print("错误: 需要安装 sklearn 库 (pip install scikit-learn)")
            return {}
        
        # 向量化所有图片
        print(f"正在向量化 {len(image_paths)} 张图片...")
        embeddings = []
        valid_paths = []
        
        for image_path in image_paths:
            embedding = self.embedding_model.encode_image(image_path)
            if embedding is not None:
                embeddings.append(embedding)
                valid_paths.append(str(image_path))
        
        if len(embeddings) == 0:
            print("错误: 没有成功向量化的图片")
            return {}
        
        embeddings_array = np.array(embeddings)
        
        # 自动确定聚类数量（使用肘部法则的简化版本）
        if n_clusters is None:
            # 简单策略：根据数据点数量确定
            n_clusters = min(len(embeddings) // 3, 10)  # 至少3张图一个类别，最多10个类别
            n_clusters = max(1, n_clusters)
        
        print(f"使用 KMeans 进行聚类，聚类数量: {n_clusters}")
        
        # 执行 KMeans 聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings_array)
        
        # 组织聚类结果
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            clusters[label].append(valid_paths[idx])
        
        return dict(clusters)
    
    def print_clusters(self, clusters: Dict[int, List[str]]):
        """
        打印聚类结果
        
        Args:
            clusters: 聚类结果字典
        """
        print("\n" + "=" * 60)
        print(f"聚类结果: 共 {len(clusters)} 个类别")
        print("=" * 60)
        
        for cluster_id, image_paths in sorted(clusters.items()):
            print(f"\n类别 {cluster_id + 1}: {len(image_paths)} 张图片")
            print("-" * 60)
            for image_path in image_paths:
                print(f"  - {image_path}")
    
    def save_clusters(self, clusters: Dict[int, List[str]], output_path: Path, format: str = "json"):
        """
        保存聚类结果到文件
        
        Args:
            clusters: 聚类结果字典
            output_path: 输出文件路径
            format: 输出格式 ("json", "txt")
        """
        output_path = Path(output_path)
        
        if format == "json":
            # 转换为可序列化的格式
            result = {
                "num_clusters": len(clusters),
                "clusters": {str(k): v for k, v in clusters.items()}
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        elif format == "txt":
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"聚类结果: 共 {len(clusters)} 个类别\n")
                f.write("=" * 60 + "\n\n")
                
                for cluster_id, image_paths in sorted(clusters.items()):
                    f.write(f"类别 {cluster_id + 1}: {len(image_paths)} 张图片\n")
                    f.write("-" * 60 + "\n")
                    for image_path in image_paths:
                        f.write(f"  - {image_path}\n")
                    f.write("\n")
        
        print(f"\n聚类结果已保存到: {output_path}")


def collect_image_files(input_paths: List[str]) -> List[Path]:
    """
    收集图片文件路径
    
    Args:
        input_paths: 输入路径列表（可以是文件或目录）
        
    Returns:
        图片文件路径列表
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    image_files = []
    
    for input_path in input_paths:
        path = Path(input_path)
        
        if path.is_file():
            # 单个文件
            if path.suffix.lower() in image_extensions:
                image_files.append(path)
        elif path.is_dir():
            # 目录，递归查找所有图片
            for ext in image_extensions:
                image_files.extend(path.rglob(f'*{ext}'))
                image_files.extend(path.rglob(f'*{ext.upper()}'))
    
    return sorted(set(image_files))  # 去重并排序


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="图片相似度聚类工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 聚类单个目录下的图片
  %(prog)s scripts/image/ --threshold 0.85
  
  # 使用 KMeans 聚类，指定聚类数量
  %(prog)s scripts/image/ --method kmeans --n-clusters 5
  
  # 聚类多个目录
  %(prog)s dir1/ dir2/ --output result.json
        """
    )
    parser.add_argument(
        "input_paths",
        nargs="+",
        help="图片文件路径或目录路径（支持多个）"
    )
    parser.add_argument(
        "--method",
        choices=["similarity", "kmeans"],
        default="similarity",
        help="聚类方法: similarity (基于相似度阈值) 或 kmeans"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="相似度阈值（仅用于 similarity 方法，默认: 0.85）"
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=None,
        help="聚类数量（仅用于 kmeans 方法，默认自动确定）"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="dinov2_vits14",
        help="使用的模型名称（默认: dinov2_vits14）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出结果文件路径（可选，支持 .json 或 .txt 格式）"
    )
    parser.add_argument(
        "--format",
        choices=["json", "txt"],
        default="json",
        help="输出格式（默认: json）"
    )
    
    args = parser.parse_args()
    
    try:
        # 1. 收集图片文件
        print("正在收集图片文件...")
        image_files = collect_image_files(args.input_paths)
        
        if len(image_files) == 0:
            print("错误: 没有找到图片文件")
            sys.exit(1)
        
        print(f"找到 {len(image_files)} 张图片")
        
        # 2. 初始化向量化模型
        print(f"正在加载模型: {args.model}")
        embedding_model = ImageEmbedding(model_name=args.model)
        
        # 3. 初始化聚类器
        clusterer = ImageCluster(embedding_model, similarity_threshold=args.threshold)
        
        # 4. 执行聚类
        if args.method == "similarity":
            clusters = clusterer.cluster_images(image_files, similarity_threshold=args.threshold)
        else:  # kmeans
            clusters = clusterer.cluster_by_kmeans(image_files, n_clusters=args.n_clusters)
        
        # 5. 输出结果
        clusterer.print_clusters(clusters)
        
        # 6. 保存结果（如果指定）
        if args.output:
            output_path = Path(args.output)
            # 如果输出路径没有扩展名，使用默认格式
            if not output_path.suffix:
                output_path = output_path.with_suffix(f".{args.format}")
            clusterer.save_clusters(clusters, output_path, format=args.format)
        
        print(f"\n完成！共 {len(clusters)} 个类别")
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

