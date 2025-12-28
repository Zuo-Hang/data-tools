"""
主模块测试
"""

from data_tools.main import main


def test_main(capsys):
    """测试主函数"""
    main()
    captured = capsys.readouterr()
    assert "Hello from data-tools!" in captured.out

