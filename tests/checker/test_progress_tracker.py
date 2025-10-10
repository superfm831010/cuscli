"""
测试进度跟踪器模块
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime

from autocoder.checker.progress_tracker import ProgressTracker
from autocoder.checker.types import CheckState


class TestProgressTracker:
    """测试 ProgressTracker 类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录用于测试"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def tracker(self, temp_dir):
        """创建 ProgressTracker 实例"""
        return ProgressTracker(state_dir=temp_dir)

    def test_tracker_initialization(self, tracker, temp_dir):
        """测试跟踪器初始化"""
        assert tracker.state_dir == temp_dir
        assert os.path.exists(temp_dir)

    def test_start_check(self, tracker):
        """测试开始检查"""
        files = ["file1.py", "file2.py", "file3.py"]
        config = {"max_workers": 5}

        check_id = tracker.start_check(files, config, "test_project")

        # 验证 check_id 格式
        assert check_id.startswith("test_project_")
        assert len(check_id) > len("test_project_")

        # 验证状态已保存
        state = tracker.load_state(check_id)
        assert state is not None
        assert state.check_id == check_id
        assert len(state.total_files) == 3
        assert len(state.remaining_files) == 3
        assert len(state.completed_files) == 0

    def test_mark_completed(self, tracker):
        """测试标记文件完成"""
        files = ["file1.py", "file2.py", "file3.py"]
        check_id = tracker.start_check(files, {}, "test")

        # 标记第一个文件完成
        tracker.mark_completed(check_id, "file1.py")

        state = tracker.load_state(check_id)
        assert len(state.completed_files) == 1
        assert "file1.py" in state.completed_files
        assert len(state.remaining_files) == 2
        assert "file1.py" not in state.remaining_files

    def test_mark_all_completed(self, tracker):
        """测试标记所有文件完成"""
        files = ["file1.py", "file2.py"]
        check_id = tracker.start_check(files, {}, "test")

        # 标记所有文件完成
        tracker.mark_completed(check_id, "file1.py")
        tracker.mark_completed(check_id, "file2.py")

        state = tracker.load_state(check_id)
        assert len(state.completed_files) == 2
        assert len(state.remaining_files) == 0
        assert state.status == "completed"

    def test_get_remaining_files(self, tracker):
        """测试获取剩余文件"""
        files = ["file1.py", "file2.py", "file3.py"]
        check_id = tracker.start_check(files, {}, "test")

        # 完成一个文件
        tracker.mark_completed(check_id, "file1.py")

        remaining = tracker.get_remaining_files(check_id)
        assert len(remaining) == 2
        assert "file1.py" not in remaining
        assert "file2.py" in remaining
        assert "file3.py" in remaining

    def test_save_and_load_state(self, tracker):
        """测试状态保存和加载"""
        check_id = "test_20251010_120000"
        state = CheckState(
            check_id=check_id,
            start_time=datetime.now().isoformat(),
            config={"test": True},
            total_files=["file1.py", "file2.py"],
            completed_files=["file1.py"],
            remaining_files=["file2.py"],
            status="running"
        )

        # 保存状态
        tracker.save_state(check_id, state)

        # 加载状态
        loaded_state = tracker.load_state(check_id)
        assert loaded_state is not None
        assert loaded_state.check_id == check_id
        assert len(loaded_state.total_files) == 2
        assert len(loaded_state.completed_files) == 1

    def test_load_nonexistent_state(self, tracker):
        """测试加载不存在的状态"""
        state = tracker.load_state("nonexistent_check_id")
        assert state is None

    def test_list_checks(self, tracker):
        """测试列出检查记录"""
        # 创建多个检查
        check_id1 = tracker.start_check(["file1.py"], {}, "project1")
        check_id2 = tracker.start_check(["file2.py"], {}, "project2")

        checks = tracker.list_checks()
        assert len(checks) >= 2

        # 验证检查记录包含必要信息
        check_ids = [c["check_id"] for c in checks]
        assert check_id1 in check_ids
        assert check_id2 in check_ids

        # 验证记录结构
        for check in checks:
            assert "check_id" in check
            assert "start_time" in check
            assert "status" in check
            assert "total" in check
            assert "completed" in check
            assert "remaining" in check

    def test_delete_check(self, tracker):
        """测试删除检查记录"""
        files = ["file1.py"]
        check_id = tracker.start_check(files, {}, "test")

        # 确认存在
        assert tracker.load_state(check_id) is not None

        # 删除
        result = tracker.delete_check(check_id)
        assert result is True

        # 确认已删除
        assert tracker.load_state(check_id) is None

    def test_delete_nonexistent_check(self, tracker):
        """测试删除不存在的检查记录"""
        result = tracker.delete_check("nonexistent_check_id")
        assert result is False

    def test_get_check_summary(self, tracker):
        """测试获取检查摘要"""
        files = ["file1.py", "file2.py", "file3.py"]
        config = {"max_workers": 5}
        check_id = tracker.start_check(files, config, "test")

        # 完成一个文件
        tracker.mark_completed(check_id, "file1.py")

        summary = tracker.get_check_summary(check_id)
        assert summary is not None
        assert summary["check_id"] == check_id
        assert summary["total_files"] == 3
        assert summary["completed_files"] == 1
        assert summary["remaining_files"] == 2
        assert summary["progress_percentage"] == pytest.approx(33.33, rel=0.01)

    def test_get_summary_nonexistent(self, tracker):
        """测试获取不存在检查的摘要"""
        summary = tracker.get_check_summary("nonexistent_check_id")
        assert summary is None

    def test_cleanup_old_checks(self, tracker):
        """测试清理旧检查记录"""
        # 创建一个检查
        check_id = tracker.start_check(["file1.py"], {}, "test")

        # 清理（保留7天，刚创建的不会被清理）
        deleted = tracker.cleanup_old_checks(keep_days=7)
        assert deleted == 0

        # 验证记录仍存在
        assert tracker.load_state(check_id) is not None

    def test_progress_percentage(self, tracker):
        """测试进度百分比计算"""
        files = ["file1.py", "file2.py", "file3.py", "file4.py"]
        check_id = tracker.start_check(files, {}, "test")

        # 完成2个文件
        tracker.mark_completed(check_id, "file1.py")
        tracker.mark_completed(check_id, "file2.py")

        state = tracker.load_state(check_id)
        progress = state.get_progress_percentage()
        assert progress == 50.0

    def test_check_id_format(self, tracker):
        """测试 check_id 格式"""
        check_id = tracker.start_check(["file1.py"], {}, "testproject")

        # 验证格式：{project_name}_{YYYYMMDD_HHMMSS}
        assert check_id.startswith("testproject_")

        parts = check_id.split("_")
        assert len(parts) == 3  # project, date, time

        # 验证日期和时间部分格式
        date_part = parts[1]
        time_part = parts[2]
        assert len(date_part) == 8  # YYYYMMDD
        assert len(time_part) == 6  # HHMMSS

    def test_concurrent_access(self, tracker):
        """测试并发访问（基本测试）"""
        files = ["file1.py", "file2.py"]
        check_id = tracker.start_check(files, {}, "test")

        # 模拟并发标记完成
        tracker.mark_completed(check_id, "file1.py")
        tracker.mark_completed(check_id, "file2.py")

        state = tracker.load_state(check_id)
        assert len(state.completed_files) == 2
