import redis
import sys

# 尝试多个连接方式
hosts_to_try = [
    ('localhost', 6379),  # 如果容器有端口映射
    ('172.17.0.2', 6379),  # 容器IP（需要端口映射或Docker网络）
]

connected = False
for host, port in hosts_to_try:
    try:
        print(f"尝试连接 {host}:{port}...")
        r = redis.Redis(
            host=host,
            port=port,
            db=0,
            socket_connect_timeout=5,
            socket_timeout=5,
            decode_responses=False
        )
        r.ping()
        print(f"Redis连接成功! (连接到 {host}:{port})")
        print(f"Redis版本: {r.info()['redis_version']}")
        connected = True
        break
    except Exception as e:
        print(f"连接 {host}:{port} 失败: {e}")
        continue

if not connected:
    print("\n所有连接尝试都失败了。")
    print("解决方案：")
    print("1. 如果使用 localhost，请重新创建容器并添加端口映射：")
    print("   docker stop redis_test")
    print("   docker rm redis_test")
    print("   docker run -d --name redis_test -p 6379:6379 redis:latest")
    print("2. 或者确保 Docker 网络配置允许从主机访问容器IP")
    sys.exit(1)

