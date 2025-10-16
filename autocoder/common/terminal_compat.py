"""
终端兼容性检测工具

自动检测终端能力,为不同平台/终端提供最佳显示方案。

功能:
- 检测ANSI转义码支持
- 检测终端编码(UTF-8/GBK/等)
- 检测终端宽度
- 自动判断是否需要legacy模式

作者: Claude AI
创建时间: 2025-01-16
"""

import os
import sys
import platform
from typing import Optional
from loguru import logger


class TerminalCapability:
    """
    终端能力检测类

    检测当前终端的能力,包括:
    - ANSI转义码支持
    - Unicode/UTF-8编码支持
    - 终端宽度
    - 操作系统和终端类型
    """

    def __init__(self):
        """初始化终端能力检测"""
        self.platform = platform.system()
        self.is_windows = self.platform == "Windows"
        self.encoding = self._detect_encoding()
        self.term_width = self._detect_width()
        self.ansi_support = self._detect_ansi_support()
        self.unicode_support = self._detect_unicode_support()
        self.terminal_type = self._detect_terminal_type()

        logger.debug(
            f"终端能力检测: platform={self.platform}, "
            f"encoding={self.encoding}, width={self.term_width}, "
            f"ansi={self.ansi_support}, unicode={self.unicode_support}, "
            f"type={self.terminal_type}"
        )

    def _detect_encoding(self) -> str:
        """
        检测终端编码

        Returns:
            编码名称(如 'utf-8', 'gbk', 'cp936')
        """
        # 优先从stdout获取编码
        encoding = getattr(sys.stdout, 'encoding', None)

        if not encoding:
            # 回退到系统默认编码
            encoding = sys.getdefaultencoding()

        # 标准化编码名称
        if encoding:
            encoding = encoding.lower()
        else:
            encoding = 'utf-8'  # 默认假设UTF-8

        return encoding

    def _detect_width(self) -> int:
        """
        检测终端宽度

        Returns:
            终端宽度(字符数),默认80
        """
        # 优先使用环境变量(用户可手动设置)
        if 'AUTOCODER_TERM_WIDTH' in os.environ:
            try:
                return int(os.environ['AUTOCODER_TERM_WIDTH'])
            except ValueError:
                pass

        # 尝试从终端获取
        try:
            import shutil
            width, _ = shutil.get_terminal_size(fallback=(80, 24))
            return width
        except Exception:
            return 80  # 默认宽度

    def _detect_ansi_support(self) -> bool:
        """
        检测ANSI转义码支持

        策略:
        1. 检查NO_COLOR环境变量(用户明确禁用)
        2. Windows: 检测是否为Windows 10+且启用了VT100
        3. Linux/macOS: 检查TERM环境变量

        Returns:
            True表示支持ANSI转义码
        """
        # 用户明确禁用彩色输出
        if os.environ.get('NO_COLOR'):
            return False

        # 用户强制启用
        if os.environ.get('FORCE_COLOR') or os.environ.get('CLICOLOR_FORCE'):
            return True

        # 非交互式终端(重定向到文件等)通常禁用ANSI
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False

        if self.is_windows:
            return self._detect_windows_ansi_support()
        else:
            return self._detect_unix_ansi_support()

    def _detect_windows_ansi_support(self) -> bool:
        """
        检测Windows终端的ANSI支持

        Windows 10+ (1511+)支持VT100转义码(需启用)
        传统cmd/PowerShell 5.x不支持或支持有限

        Returns:
            True表示支持ANSI
        """
        # 检测Windows版本
        try:
            import sys
            version = sys.getwindowsversion()
            major = version.major
            build = version.build

            # Windows 10+ (Build 10586+)支持VT100
            if major >= 10 and build >= 10586:
                # 尝试启用VT100模式
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32

                    # 获取stdout句柄
                    STD_OUTPUT_HANDLE = -11
                    handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

                    # 获取当前控制台模式
                    mode = ctypes.c_ulong()
                    kernel32.GetConsoleMode(handle, ctypes.byref(mode))

                    # 启用VT100处理(ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004)
                    ENABLE_VT100 = 0x0004
                    new_mode = mode.value | ENABLE_VT100

                    # 尝试设置新模式
                    if kernel32.SetConsoleMode(handle, new_mode):
                        logger.debug("Windows VT100模式已启用")
                        return True
                    else:
                        logger.debug("Windows VT100模式启用失败")
                        return False
                except Exception as e:
                    logger.debug(f"启用Windows VT100失败: {e}")
                    return False
            else:
                # 传统Windows(7/8/Server 2012等)不支持
                logger.debug(f"Windows版本 {major}.{build} 不支持VT100")
                return False
        except Exception as e:
            logger.warning(f"检测Windows ANSI支持时出错: {e}")
            return False

    def _detect_unix_ansi_support(self) -> bool:
        """
        检测Unix/Linux/macOS终端的ANSI支持

        大多数现代Unix终端都支持ANSI

        Returns:
            True表示支持ANSI
        """
        # 检查TERM环境变量
        term = os.environ.get('TERM', '')

        # dumb终端不支持ANSI
        if term == 'dumb':
            return False

        # 大多数现代终端都支持
        # xterm, xterm-256color, screen, tmux等
        if term:
            return True

        # 如果没有TERM变量,但是tty,假设支持
        return True

    def _detect_unicode_support(self) -> bool:
        """
        检测Unicode/UTF-8支持

        Returns:
            True表示支持Unicode特殊字符
        """
        # 检查编码
        if 'utf' in self.encoding or 'utf8' in self.encoding:
            return True

        # Windows下GBK/CP936也可能支持部分Unicode
        # 但不推荐使用特殊字符
        if self.is_windows and ('gbk' in self.encoding or 'cp936' in self.encoding):
            return False

        # 其他编码保守假设不支持
        return False

    def _detect_terminal_type(self) -> str:
        """
        检测终端类型

        Returns:
            终端类型字符串
        """
        if self.is_windows:
            # Windows终端类型检测
            term_program = os.environ.get('TERM_PROGRAM', '').lower()
            wt_session = os.environ.get('WT_SESSION')  # Windows Terminal

            if wt_session:
                return 'windows_terminal'
            elif term_program == 'vscode':
                return 'vscode'
            elif 'conemu' in os.environ.get('ConEmuANSI', '').lower():
                return 'conemu'
            else:
                # 传统cmd或PowerShell
                return 'cmd'
        else:
            # Unix/Linux/macOS
            term = os.environ.get('TERM', '').lower()
            term_program = os.environ.get('TERM_PROGRAM', '').lower()

            if term_program == 'vscode':
                return 'vscode'
            elif 'tmux' in term:
                return 'tmux'
            elif 'screen' in term:
                return 'screen'
            elif term_program == 'apple_terminal':
                return 'macos_terminal'
            else:
                return term or 'unknown'

    def should_use_legacy_mode(self) -> bool:
        """
        判断是否应该使用legacy模式(逐行打印而非原地更新)

        策略:
        - Windows传统终端(cmd/PowerShell 5.x): 使用legacy
        - 不支持ANSI的终端: 使用legacy
        - 用户强制指定: 遵守环境变量

        Returns:
            True表示应该使用legacy模式
        """
        # 用户强制指定
        if os.environ.get('AUTOCODER_LEGACY_UI'):
            return True

        # 非交互式终端(如重定向到文件)
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return True

        # 不支持ANSI转义码
        if not self.ansi_support:
            return True

        # Windows传统cmd终端
        if self.is_windows and self.terminal_type == 'cmd':
            # 即使启用了VT100,传统cmd的体验仍不如legacy模式
            return True

        # 其他情况使用标准模式
        return False

    def supports_unicode(self) -> bool:
        """
        是否支持Unicode特殊字符(如框线字符╔═╗)

        Returns:
            True表示可以安全使用Unicode特殊字符
        """
        return self.unicode_support

    def get_safe_width(self, default: int = 80) -> int:
        """
        获取安全的显示宽度

        Args:
            default: 默认宽度

        Returns:
            建议的显示宽度
        """
        if self.term_width > 0:
            # 预留2字符边距
            return max(40, self.term_width - 2)
        else:
            return default


# 全局单例
_terminal_capability: Optional[TerminalCapability] = None


def get_terminal_capability() -> TerminalCapability:
    """
    获取终端能力检测实例(单例模式)

    Returns:
        TerminalCapability实例
    """
    global _terminal_capability

    if _terminal_capability is None:
        _terminal_capability = TerminalCapability()

    return _terminal_capability


def reset_terminal_capability():
    """重置终端能力检测(用于测试)"""
    global _terminal_capability
    _terminal_capability = None
