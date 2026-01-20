"""
图片向量化 Embedding 脚本
基于 DINOv2-Small 模型进行图片向量化
"""

import sys
import json
import os
from pathlib import Path
from typing import Optional, Union, List
from io import BytesIO

import numpy as np
import torch
from PIL import Image
import torchvision.transforms as transforms

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ImageEmbedding:
    """图片向量化类 - 基于 DINOv2-Small"""
    
    # DINOv2-Small 的向量维度
    EMBEDDING_DIM = 384
    
    def __init__(self, model_name: str = "dinov2_vits14", device: str = None, **kwargs):
        """
        初始化图片向量化模型
        
        Args:
            model_name: 模型名称，默认为 "dinov2_vits14" (DINOv2-Small)
                        可选: "dinov2_vitb14", "dinov2_vitl14", "dinov2_vitg14"
            device: 使用的设备 ("cuda", "cpu")，None 表示自动选择
            **kwargs: 其他初始化参数
        """
        self.model_name = model_name
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = None
        self._load_model()
    
    def _load_model(self):
        """加载 DINOv2 模型"""
        try:
            # 首先尝试使用 torch.hub 加载（会检查本地缓存）
            # 如果本地缓存不存在且网络连接失败，会抛出错误
            print(f"正在加载模型 {self.model_name}...")
            
            # 尝试从缓存加载，如果缓存不存在则不验证网络连接
            try:
                self.model = torch.hub.load(
                    'facebookresearch/dinov2',
                    self.model_name,
                    source='github',
                    trust_repo=True,
                    skip_validation=True
                )
            except Exception as e:
                # 如果网络下载失败，尝试使用本地缓存
                cache_dir = Path.home() / '.cache' / 'torch' / 'hub'
                model_cache = cache_dir / 'facebookresearch_dinov2_main'
                
                if not model_cache.exists():
                    print("\n错误: 无法从网络下载模型，且本地缓存不存在")
                    print(f"本地缓存路径: {cache_dir}")
                    print("\n解决方案:")
                    print("1. 检查网络连接和 SSL 证书配置")
                    print("2. 手动下载模型到本地:")
                    print(f"   运行: pip install dinov2")
                    print("   或使用: python -c \"import torch; torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14')\"")
                    print("3. 或者安装 transformers 库并使用:")
                    print("   pip install transformers")
                    raise RuntimeError(f"加载 DINOv2 模型失败: {e}\n\n提示: 请检查网络连接或手动下载模型") from e
                else:
                    # 尝试从本地缓存加载
                    print("尝试从本地缓存加载...")
                    self.model = torch.hub.load(
                        str(model_cache.parent),
                        self.model_name,
                        source='local',
                        trust_repo=True
                    )
            
            self.model.eval()
            self.model.to(self.device)
            
            # 设置图像预处理
            # DINOv2 需要将图像转换为 224x224 并归一化
            self.transform = transforms.Compose([
                transforms.Resize(256, interpolation=transforms.InterpolationMode.BICUBIC),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            
            print(f"模型加载成功，使用设备: {self.device}")
        except RuntimeError:
            # 重新抛出 RuntimeError
            raise
        except Exception as e:
            raise RuntimeError(f"加载 DINOv2 模型失败: {e}") from e
    
    def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        预处理图片
        
        Args:
            image: PIL Image 对象
            
        Returns:
            预处理后的 tensor
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return self.transform(image).unsqueeze(0).to(self.device)
    
    def _extract_features(self, image_tensor: torch.Tensor) -> np.ndarray:
        """
        提取特征向量
        
        Args:
            image_tensor: 预处理后的图片 tensor
            
        Returns:
            特征向量 (numpy array)
        """
        with torch.no_grad():
            # 使用 DINOv2 提取特征
            # cls_token 是 [CLS] token 的表示，通常用于全局图像表示
            features = self.model(image_tensor)
            # 转换为 numpy 并归一化（L2 归一化）
            features = features.cpu().numpy().flatten()
            # L2 归一化
            features = features / np.linalg.norm(features)
            return features.astype(np.float32)
    
    def encode_image(self, image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        对单张图片进行向量化
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            向量数组（numpy array），如果失败返回 None
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                print(f"错误: 图片文件不存在: {image_path}")
                return None
            
            # 加载图片
            image = Image.open(image_path)
            
            # 预处理
            image_tensor = self._preprocess_image(image)
            
            # 提取特征
            embedding = self._extract_features(image_tensor)
            
            return embedding
        except Exception as e:
            print(f"图片向量化失败: {e}")
            return None
    
    def encode_images(self, image_paths: List[Union[str, Path]], batch_size: int = 8) -> List[Optional[np.ndarray]]:
        """
        对多张图片进行批量向量化
        
        Args:
            image_paths: 图片文件路径列表
            batch_size: 批量处理大小
            
        Returns:
            向量数组列表
        """
        results = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_images = []
            batch_indices = []
            
            # 加载批次图片
            for idx, image_path in enumerate(batch_paths):
                try:
                    image_path = Path(image_path)
                    if image_path.exists():
                        image = Image.open(image_path)
                        image_tensor = self._preprocess_image(image)
                        batch_images.append(image_tensor)
                        batch_indices.append(i + idx)
                except Exception as e:
                    print(f"加载图片失败 {image_path}: {e}")
                    results.append(None)
            
            if batch_images:
                try:
                    # 批量处理
                    batch_tensor = torch.cat(batch_images, dim=0)
                    
                    with torch.no_grad():
                        batch_features = self.model(batch_tensor)
                        # 归一化
                        batch_features = batch_features / torch.norm(batch_features, dim=1, keepdim=True)
                        batch_features = batch_features.cpu().numpy().astype(np.float32)
                    
                    # 将结果放回对应位置
                    for idx, feature in zip(batch_indices, batch_features):
                        while len(results) <= idx:
                            results.append(None)
                        results[idx] = feature
                except Exception as e:
                    print(f"批量处理失败: {e}")
                    for idx in batch_indices:
                        while len(results) <= idx:
                            results.append(None)
                        results[idx] = None
        
        # 确保结果列表长度与输入一致
        while len(results) < len(image_paths):
            results.append(None)
        
        return results
    
    def encode_image_from_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        从图片二进制数据直接向量化
        
        Args:
            image_bytes: 图片的二进制数据
            
        Returns:
            向量数组（numpy array），如果失败返回 None
        """
        try:
            # 从字节流加载图片
            image = Image.open(BytesIO(image_bytes))
            
            # 预处理
            image_tensor = self._preprocess_image(image)
            
            # 提取特征
            embedding = self._extract_features(image_tensor)
            
            return embedding
        except Exception as e:
            print(f"从字节流向量化失败: {e}")
            return None
    
    def get_embedding_dimension(self) -> Optional[int]:
        """
        获取向量维度
        
        Returns:
            向量维度，如果模型未初始化返回 None
        """
        if self.model is None:
            return None
        return self.EMBEDDING_DIM
    
    def save_embedding(self, embedding: np.ndarray, output_path: Union[str, Path], format: str = "npy") -> bool:
        """
        保存向量到文件
        
        Args:
            embedding: 向量数组
            output_path: 输出文件路径
            format: 保存格式 ("npy", "json")
            
        Returns:
            是否保存成功
        """
        try:
            output_path = Path(output_path)
            
            if format == "npy":
                # 保存为 numpy 二进制格式
                np.save(output_path, embedding)
            elif format == "json":
                # 保存为 JSON 格式
                data = {
                    "dimension": len(embedding),
                    "embedding": embedding.tolist()
                }
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                print(f"不支持的格式: {format}")
                return False
            
            return True
        except Exception as e:
            print(f"保存向量失败: {e}")
            return False
    
    def load_embedding(self, embedding_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        从文件加载向量
        
        Args:
            embedding_path: 向量文件路径
            
        Returns:
            向量数组，如果加载失败返回 None
        """
        try:
            embedding_path = Path(embedding_path)
            if not embedding_path.exists():
                print(f"错误: 向量文件不存在: {embedding_path}")
                return None
            
            # 根据文件扩展名判断格式
            if embedding_path.suffix == '.npy':
                embedding = np.load(embedding_path)
            elif embedding_path.suffix == '.json':
                with open(embedding_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                embedding = np.array(data['embedding'], dtype=np.float32)
            else:
                # 默认尝试作为 npy 文件加载
                embedding = np.load(embedding_path)
            
            return embedding.astype(np.float32)
        except Exception as e:
            print(f"加载向量失败: {e}")
            return None
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray, method: str = "cosine") -> float:
        """
        计算两个向量之间的相似度
        
        Args:
            embedding1: 第一个向量
            embedding2: 第二个向量
            method: 相似度计算方法（"cosine", "euclidean", "dot"）
            
        Returns:
            相似度分数
        """
        if method == "cosine":
            # 余弦相似度（向量已归一化，直接点积即可）
            return float(np.dot(embedding1, embedding2))
        elif method == "euclidean":
            # 欧氏距离（距离越小越相似，这里返回距离）
            return float(np.linalg.norm(embedding1 - embedding2))
        elif method == "dot":
            # 点积
            return float(np.dot(embedding1, embedding2))
        else:
            raise ValueError(f"不支持的相似度计算方法: {method}")
    
    def find_similar_images(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5,
        method: str = "cosine"
    ) -> List[tuple]:
        """
        在候选向量中查找与查询向量最相似的向量
        
        Args:
            query_embedding: 查询向量
            candidate_embeddings: 候选向量列表
            top_k: 返回前k个最相似的结果
            method: 相似度计算方法
            
        Returns:
            相似度排序列表，每个元素为 (索引, 相似度分数)
        """
        similarities = []
        
        for idx, candidate in enumerate(candidate_embeddings):
            if candidate is None:
                continue
            
            if method == "cosine":
                similarity = self.compute_similarity(query_embedding, candidate, method="cosine")
            elif method == "euclidean":
                # 欧氏距离，距离越小越相似，所以用负数
                distance = self.compute_similarity(query_embedding, candidate, method="euclidean")
                similarity = -distance  # 转换为相似度（越大越相似）
            else:
                similarity = self.compute_similarity(query_embedding, candidate, method=method)
            
            similarities.append((idx, similarity))
        
        # 按相似度排序（降序）
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前 top_k 个结果
        return similarities[:top_k]


def main():
    """主函数 - 示例用法"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="图片向量化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s scripts/image/000714.jpg
  %(prog)s --output embedding.npy scripts/image/10340.jpg
  %(prog)s --batch scripts/image/*.jpg
        """
    )
    parser.add_argument(
        "image_path",
        type=str,
        nargs="?",
        help="图片文件路径"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="使用的模型名称"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出向量文件路径"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量处理模式"
    )
    parser.add_argument(
        "--dimension",
        action="store_true",
        help="显示向量维度"
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化模型
        model_name = args.model if args.model else "dinov2_vits14"
        embedding_model = ImageEmbedding(model_name=model_name)
        
        if args.dimension:
            # 显示向量维度
            dim = embedding_model.get_embedding_dimension()
            print(f"向量维度: {dim}")
        
        elif args.image_path:
            # 处理单张图片
            print(f"处理图片: {args.image_path}")
            embedding = embedding_model.encode_image(args.image_path)
            
            if embedding is not None:
                print(f"向量维度: {len(embedding)}")
                print(f"向量前10维: {embedding[:10]}")
                
                # 如果指定了输出路径，保存向量
                if args.output:
                    output_path = Path(args.output)
                    format_type = "npy" if output_path.suffix == ".npy" else "json"
                    if embedding_model.save_embedding(embedding, output_path, format=format_type):
                        print(f"向量已保存到: {output_path}")
                    else:
                        print("保存向量失败")
            else:
                print("图片向量化失败")
                sys.exit(1)
        
        elif args.batch:
            # 批量处理（需要实现）
            print("批量处理模式: 请指定图片路径或使用通配符")
            parser.print_help()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

