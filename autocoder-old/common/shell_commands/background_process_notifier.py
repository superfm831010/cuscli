"""
BackgroundProcessNotifier

A lightweight in-memory notifier that monitors background processes and
produces async completion messages correlated by conversation_id.

It periodically polls the global ProcessManager's background processes,
detects transitions from running to completed, collects final outputs,
and enqueues AsyncTaskMessage items keyed by conversation_id for consumers
to poll.

This module intentionally does not depend on the events/ module.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple

from loguru import logger

# Reuse the global background process manager accessor to avoid divergence
from .command_executor import get_background_processes, get_background_process_info


@dataclass
class BackgroundTaskRegistration:
    conversation_id: str
    pid: int
    tool_name: str
    command: str
    cwd: Optional[str]
    agent_name: Optional[str]
    task: Optional[str]
    task_id: str
    start_time: float


@dataclass
class AsyncTaskMessage:
    conversation_id: str
    task_id: str
    pid: int
    tool_name: str
    status: str  # "completed" | "failed"
    exit_code: Optional[int]
    duration_sec: Optional[float]
    command: str
    cwd: Optional[str]
    agent_name: Optional[str]
    task: Optional[str]
    output_tail: Optional[str]
    error_tail: Optional[str]
    completed_at: float


class BackgroundProcessNotifier:
    """
    Singleton notifier for background process completion correlated by conversation_id.

    Public API:
    - get_instance()
    - register_process(...)
    - poll_messages(conversation_id, max_items=32)
    - has_messages(conversation_id)
    - set_options(...)
    - stop()
    """

    _instance: Optional["BackgroundProcessNotifier"] = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "BackgroundProcessNotifier":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = BackgroundProcessNotifier()
        return cls._instance

    def __init__(self) -> None:
        # Thread-safety primitives
        self._lock = threading.RLock()
        self._stop_event = threading.Event()

        # Configurable options
        self._poll_interval_sec: float = 0.5
        self._max_output_bytes: int = 16 * 1024
        self._max_output_lines: int = 200

        # State
        # Use (pid, start_time) as stable key to avoid PID reuse collisions
        self._registrations: Dict[Tuple[int, float], BackgroundTaskRegistration] = {}
        self._pid_to_key: Dict[int, Tuple[int, float]] = {}
        self._reported: set[Tuple[int, float]] = set()
        self._pending_messages: Dict[str, Deque[AsyncTaskMessage]] = defaultdict(deque)

        # Start monitor thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, name="BackgroundProcessNotifierThread", daemon=True
        )
        self._monitor_thread.start()

    # ---------------------------- Public API ----------------------------
    def set_options(
        self,
        poll_interval_sec: Optional[float] = None,
        max_output_bytes: Optional[int] = None,
        max_output_lines: Optional[int] = None,
    ) -> None:
        with self._lock:
            if poll_interval_sec is not None and poll_interval_sec > 0:
                self._poll_interval_sec = float(poll_interval_sec)
            if max_output_bytes is not None and max_output_bytes > 0:
                self._max_output_bytes = int(max_output_bytes)
            if max_output_lines is not None and max_output_lines > 0:
                self._max_output_lines = int(max_output_lines)

    def register_process(
        self,
        *,
        conversation_id: str,
        pid: int,
        tool_name: str,
        command: str,
        cwd: Optional[str] = None,
        agent_name: Optional[str] = None,
        task: Optional[str] = None,
    ) -> str:
        """
        Register a background process to be monitored.
        Returns a generated task_id string.
        """
        start_time = self._get_process_start_time(pid)
        task_id = str(uuid.uuid4())
        registration = BackgroundTaskRegistration(
            conversation_id=conversation_id,
            pid=pid,
            tool_name=tool_name,
            command=command,
            cwd=cwd,
            agent_name=agent_name,
            task=task,
            task_id=task_id,
            start_time=start_time,
        )

        key = (pid, start_time)
        with self._lock:
            self._registrations[key] = registration
            self._pid_to_key[pid] = key

        logger.info(
            f"BackgroundProcessNotifier: registered pid={pid} tool={tool_name} conv={conversation_id} task_id={task_id}"
        )
        return task_id

    def poll_messages(self, conversation_id: str, max_items: int = 32) -> List[AsyncTaskMessage]:
        with self._lock:
            q = self._pending_messages.get(conversation_id)
            if not q:
                return []
            items: List[AsyncTaskMessage] = []
            for _ in range(min(max_items, len(q))):
                items.append(q.popleft())
            # Clean up empty deque entries
            if not q:
                self._pending_messages.pop(conversation_id, None)
            return items

    def has_messages(self, conversation_id: str) -> bool:
        with self._lock:
            q = self._pending_messages.get(conversation_id)
            return bool(q and len(q) > 0)

    def stop(self) -> None:
        self._stop_event.set()
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)

    # ---------------------------- Internal ----------------------------
    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._scan_background_processes()
            except Exception as e:
                logger.warning(f"BackgroundProcessNotifier monitor error: {e}")
            finally:
                self._stop_event.wait(self._poll_interval_sec)

    def _scan_background_processes(self) -> None:
        bg = get_background_processes()
        if not bg:
            return

        # Snapshot keys for iteration under lock safety
        with self._lock:
            registrations_items = list(self._registrations.items())

        for key, reg in registrations_items:
            pid, reg_start_time = key
            info = bg.get(pid)
            if not info:
                # Might have been cleaned up already
                continue

            status = info.get("status")
            if status != "completed":
                continue

            # Ensure this completion hasn't been reported yet
            with self._lock:
                if key in self._reported:
                    continue

            # Build message
            exit_code = info.get("exit_code")
            end_time = info.get("end_time", time.time())
            start_time = info.get("start_time", reg_start_time)
            duration = (end_time - start_time) if (end_time and start_time) else None

            output_tail, error_tail = self._read_process_output_tails(info)

            message = AsyncTaskMessage(
                conversation_id=reg.conversation_id,
                task_id=reg.task_id,
                pid=pid,
                tool_name=reg.tool_name,
                status="failed" if (exit_code is not None and exit_code != 0) else "completed",
                exit_code=exit_code,
                duration_sec=duration,
                command=reg.command,
                cwd=reg.cwd,
                agent_name=reg.agent_name,
                task=reg.task,
                output_tail=output_tail,
                error_tail=error_tail,
                completed_at=end_time,
            )

            with self._lock:
                self._pending_messages[reg.conversation_id].append(message)
                self._reported.add(key)
                # Remove registration after reporting
                self._registrations.pop(key, None)
                # Keep pid_to_key consistent
                old_key = self._pid_to_key.get(pid)
                if old_key == key:
                    self._pid_to_key.pop(pid, None)

            logger.info(
                f"BackgroundProcessNotifier: reported completion for pid={pid} task_id={reg.task_id} conv={reg.conversation_id} exit_code={exit_code}"
            )

    def _read_process_output_tails(self, info: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Read stdout/stderr tails from files in .auto-coder/backgrounds directory.
        Files are named as {process_uniq_id}.out and {process_uniq_id}.err.
        """
        # Get process_uniq_id
        process_uniq_id = info.get("process_uniq_id")
        
        if not process_uniq_id:
            return None, None

        # Resolve backgrounds directory relative to the process working directory if provided,
        # otherwise fall back to current working directory. This keeps notifier robust when
        # called from different CWDs.
        cwd = info.get("cwd") or info.get("working_directory")
        base_dir = cwd if isinstance(cwd, str) and len(cwd) > 0 else os.getcwd()
        backgrounds_dir = os.path.join(base_dir, '.auto-coder', 'backgrounds')
        stdout_file = os.path.join(backgrounds_dir, f"{process_uniq_id}.out")
        stderr_file = os.path.join(backgrounds_dir, f"{process_uniq_id}.err")

        out_tail = self._read_file_tail(stdout_file)
        err_tail = self._read_file_tail(stderr_file)
        
        return out_tail, err_tail

    def _read_file_tail(self, filepath: str) -> Optional[str]:
        """
        Read the tail of a file according to configured limits.
        Returns None if file doesn't exist or can't be read.
        """
        if not os.path.exists(filepath):
            return None
        
        try:
            # Get file size
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                return ""
            
            with open(filepath, 'rb') as f:
                # Read from the end of file
                if file_size > self._max_output_bytes:
                    # Seek to position that gives us approximately max_output_bytes
                    f.seek(-self._max_output_bytes, os.SEEK_END)
                    # Read to end of current line to avoid partial lines
                    f.readline()  # Skip partial line
                    data = f.read()
                else:
                    # Read entire file if it's small enough
                    data = f.read()
                
                # Decode and process
                text = data.decode('utf-8', errors='replace')
                return self._tail_text(text)
                
        except Exception as e:
            logger.warning(f"Failed to read tail from {filepath}: {e}")
            return None

    def _tail_text(self, text: str) -> str:
        # First bound by bytes length, then by line count
        if not text:
            return ""

        # Trim by bytes (approx via UTF-8 encoding)
        data = text.encode("utf-8", errors="replace")
        if len(data) > self._max_output_bytes:
            data = data[-self._max_output_bytes :]
        trimmed = data.decode("utf-8", errors="replace")

        # Then trim by lines
        lines = trimmed.splitlines()
        if len(lines) > self._max_output_lines:
            lines = lines[-self._max_output_lines :]
        return "\n".join(lines)

    def _get_process_start_time(self, pid: int) -> float:
        info = get_background_process_info(pid)
        if info and "start_time" in info and isinstance(info["start_time"], (int, float)):
            return float(info["start_time"])
        return time.time()


def get_background_process_notifier() -> BackgroundProcessNotifier:
    return BackgroundProcessNotifier.get_instance()


