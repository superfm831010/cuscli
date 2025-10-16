# 终端兼容性改进实施记录

**实施日期**: 2025-01-16
**问题描述**: 在Windows Server等不同操作系统和终端版本中,主界面ASCII艺术字显示错位,codecheck进度条不断刷新新行
**解决方案**: 实施终端能力自适应检测,自动降级为legacy模式

---

## 问题分析

### 1. 主界面显示问题

**现象**:
- ASCII艺术字使用的Unicode框线字符(╔═╗等)在非UTF-8终端显示为乱码
- 彩色ANSI转义码在传统Windows cmd中不生效

**根本原因**:
- Windows Server 2016/2019 默认终端编码为GBK/CP936,不完全支持Unicode
- 传统cmd.exe不支持或部分支持ANSI转义码

### 2. 进度条刷新问题

**现象**:
- codecheck进度显示不断刷新新行,而非原地更新
- 终端被大量进度输出刷屏

**根本原因**:
- Rich库的Live组件使用ANSI转义码(`\r`回车、`\033[K`清除行)实现原地更新
- Windows传统终端对这些控制码支持不完整,导致无法原地刷新

---

## 解决方案实施

### 阶段1: 终端能力检测工具

**新建文件**: `autocoder/common/terminal_compat.py` (336行)

**核心功能**:

1. **TerminalCapability 类**:
   ```python
   class TerminalCapability:
       def __init__(self):
           self.platform = platform.system()
           self.is_windows = self.platform == "Windows"
           self.encoding = self._detect_encoding()
           self.term_width = self._detect_width()
           self.ansi_support = self._detect_ansi_support()
           self.unicode_support = self._detect_unicode_support()
           self.terminal_type = self._detect_terminal_type()
   ```

2. **检测策略**:
   - **编码检测**: 从`sys.stdout.encoding`获取,标准化为小写
   - **ANSI支持检测**:
     - Windows: 检测版本(10+ Build 10586+)并尝试启用VT100模式
     - Unix/Linux: 检查TERM环境变量(dumb终端除外)
   - **Unicode支持**: 编码包含'utf'即支持,Windows GBK不支持
   - **终端类型**: 检测Windows Terminal、VSCode、cmd等

3. **Windows VT100启用** (关键实现):
   ```python
   def _detect_windows_ansi_support(self) -> bool:
       import ctypes
       kernel32 = ctypes.windll.kernel32

       STD_OUTPUT_HANDLE = -11
       handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

       mode = ctypes.c_ulong()
       kernel32.GetConsoleMode(handle, ctypes.byref(mode))

       ENABLE_VT100 = 0x0004
       new_mode = mode.value | ENABLE_VT100

       return kernel32.SetConsoleMode(handle, new_mode)
   ```

4. **判断Legacy模式**:
   ```python
   def should_use_legacy_mode(self) -> bool:
       # 用户强制指定
       if os.environ.get('AUTOCODER_LEGACY_UI'):
           return True

       # 非交互式终端
       if not sys.stdout.isatty():
           return True

       # 不支持ANSI
       if not self.ansi_support:
           return True

       # Windows cmd(即使启用VT100也体验不佳)
       if self.is_windows and self.terminal_type == 'cmd':
           return True

       return False
   ```

5. **全局单例模式**:
   ```python
   _terminal_capability: Optional[TerminalCapability] = None

   def get_terminal_capability() -> TerminalCapability:
       global _terminal_capability
       if _terminal_capability is None:
           _terminal_capability = TerminalCapability()
       return _terminal_capability
   ```

**测试覆盖**:
- ✅ Windows 10+ (Windows Terminal/PowerShell 7) - 标准模式
- ✅ Windows Server 2016/2019 (cmd/PowerShell 5.x) - Legacy模式
- ✅ Linux/macOS - 标准模式
- ✅ SSH远程终端 - 根据TERM自动适配

---

### 阶段2: 主界面自适应Logo

**修改文件**: `autocoder/chat_auto_coder.py`

**修改位置**: 行1304-1329

**实现方式**:

```python
from autocoder.common.terminal_compat import get_terminal_capability

term = get_terminal_capability()

if term.supports_unicode() and term.ansi_support:
    # 终端支持Unicode和ANSI,显示彩色ASCII logo
    print(f"""\033[1;32m  ██████╗██╗   ██╗███████╗          ██████╗██╗     ██╗
 ██╔════╝██║   ██║██╔════╝         ██╔════╝██║     ██║
 ██║     ██║   ██║███████╗ ██████  ██║     ██║     ██║
 ██║     ██║   ██║╚════██║         ██║     ██║     ██║
 ╚██████╗╚██████╔╝███████║         ╚██████╗███████╗██║
  ╚═════╝ ╚═════╝ ╚══════╝          ╚═════╝╚══════╝╚═╝
                                             {__version__}
                            Produced by 黄埔海关科技处\033[0m""")
else:
    # 降级为纯ASCII logo(兼容传统Windows终端)
    print(f"""
  ====================================
   CUS-CLI - Custom CLI Tool
   Version: {__version__}
   Produced by 黄埔海关科技处
  ====================================
""")
```

**print_warning_box函数修改** (行89-192):

1. 检测终端能力,选择边框字符:
   ```python
   if term.supports_unicode():
       top_left, top_right = "╔", "╗"
       horizontal, vertical = "═", "║"
   else:
       top_left, top_right = "+", "+"
       horizontal, vertical = "=", "|"
   ```

2. ANSI颜色自适应:
   ```python
   reset = "\033[0m" if term.ansi_support else ""
   text_color = "\033[1;31m" if term.ansi_support else ""
   box_color = color if term.ansi_support else ""
   ```

---

### 阶段3: 进度显示Legacy模式

**修改文件**: `autocoder/checker/progress_display.py`

**核心修改**:

1. **构造函数增加legacy_mode参数** (行46-65):
   ```python
   def __init__(self, console: Optional[Console] = None, legacy_mode: Optional[bool] = None):
       self.console = console or Console()

       # 自动检测终端能力
       if legacy_mode is None:
           from autocoder.common.terminal_compat import get_terminal_capability
           term = get_terminal_capability()
           self.legacy_mode = term.should_use_legacy_mode()
       else:
           self.legacy_mode = legacy_mode

       # Legacy模式参数
       self.last_print_time = 0
       self.print_interval = 2.0  # 每2秒打印一次
   ```

2. **display_progress上下文管理器** (行186-211):
   ```python
   @contextmanager
   def display_progress(self):
       if self.legacy_mode:
           # Legacy模式：不使用Live更新
           yield self
           self._print_legacy_status(final=True)
       else:
           # 标准模式：使用Rich Live原地更新
           self.live = Live(
               self._create_display_group(),
               console=self.console,
               refresh_per_second=4,
               transient=False
           )
           with self.live:
               yield self
   ```

3. **_update_display方法** (行213-220):
   ```python
   def _update_display(self):
       if self.legacy_mode:
           self._print_legacy_status_if_needed()
       elif self.live:
           self.live.update(self._create_display_group())
   ```

4. **Legacy模式打印方法** (行222-269):
   ```python
   def _print_legacy_status_if_needed(self):
       """定期打印状态（防止刷屏）"""
       current_time = time.time()
       if current_time - self.last_print_time >= self.print_interval:
           self._print_legacy_status()
           self.last_print_time = current_time

   def _print_legacy_status(self, final: bool = False):
       """打印当前状态(纯文本,逐行追加)"""
       timestamp = datetime.now().strftime("%H:%M:%S")

       status_parts = [f"[{timestamp}] 检查进度: {completed}/{total} ({percentage:.1f}%)"]

       # 添加速度、Chunk、LLM信息
       if self.current_state["files_per_minute"] > 0:
           status_parts.append(f"速度: {self.current_state['files_per_minute']:.1f} files/min")

       # ...其他状态信息

       status_line = " | ".join(status_parts)
       print(status_line, flush=True)
   ```

**Legacy模式输出示例**:
```
[14:23:01] 检查进度: 15/100 (15.0%) | 速度: 12.5 files/min | Chunk 3/5 | LLM 1/1
[14:23:03] 检查进度: 18/100 (18.0%) | 速度: 13.2 files/min | Chunk 1/4 | LLM 1/1
[14:23:05] 检查进度: 22/100 (22.0%) | 速度: 13.8 files/min | Chunk 5/6 | LLM 1/1
```

5. **update_file_progress修改** (行323-339):
   ```python
   # 只在非legacy模式下更新Rich进度条
   if not self.legacy_mode:
       if self.main_task_id is None:
           self.main_task_id = self.progress.add_task(description, total=...)
       else:
           self.progress.update(self.main_task_id, completed=...)

   self._update_display()
   ```

---

## 环境变量控制

用户可通过环境变量手动控制显示模式:

```bash
# 强制使用legacy模式(Windows Server等不兼容终端)
export AUTOCODER_LEGACY_UI=1

# 强制禁用彩色输出
export NO_COLOR=1

# 手动指定终端宽度
export AUTOCODER_TERM_WIDTH=80
```

---

## 代码统计

| 文件 | 操作 | 行数 |
|------|------|------|
| `autocoder/common/terminal_compat.py` | 新建 | 336行 |
| `autocoder/chat_auto_coder.py` | 修改 | 约60行 |
| `autocoder/checker/progress_display.py` | 修改 | 约80行 |
| **总计** | | **约476行** |

---

## 兼容性测试

### 测试环境

| 环境 | 编码 | ANSI支持 | Unicode支持 | 模式 |
|------|------|----------|-------------|------|
| Windows 11 + Windows Terminal | UTF-8 | ✅ | ✅ | 标准模式 |
| Windows Server 2019 + cmd | GBK | ❌ | ❌ | Legacy模式 |
| Windows Server 2019 + PowerShell 5.x | GBK | ⚠️ 部分 | ❌ | Legacy模式 |
| Ubuntu 22.04 + bash | UTF-8 | ✅ | ✅ | 标准模式 |
| macOS Terminal | UTF-8 | ✅ | ✅ | 标准模式 |
| SSH (PuTTY/XShell) | 取决于配置 | 取决于TERM | 取决于编码 | 自动检测 |

### 测试结果

**主界面**:
- ✅ Windows Terminal: 彩色Unicode logo正常显示
- ✅ Windows Server cmd: 降级为纯ASCII logo,无乱码
- ✅ Linux/macOS: 彩色Unicode logo正常显示

**进度条**:
- ✅ Windows Terminal: Rich Live原地更新正常
- ✅ Windows Server cmd: 每2秒打印一行状态,无刷屏
- ✅ Linux/macOS: Rich Live原地更新正常

---

## 技术要点

### 1. Windows VT100模式启用

Windows 10+ 支持VT100转义码,但需要通过Windows API启用:

```python
import ctypes

kernel32 = ctypes.windll.kernel32
STD_OUTPUT_HANDLE = -11
handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

mode = ctypes.c_ulong()
kernel32.GetConsoleMode(handle, ctypes.byref(mode))

ENABLE_VT100 = 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
new_mode = mode.value | ENABLE_VT100

success = kernel32.SetConsoleMode(handle, new_mode)
```

### 2. 编码检测fallback

```python
encoding = getattr(sys.stdout, 'encoding', None) or sys.getdefaultencoding()
encoding = encoding.lower() if encoding else 'utf-8'
```

### 3. Legacy模式防刷屏策略

使用时间间隔控制打印频率,避免刷屏:

```python
if current_time - self.last_print_time >= self.print_interval:
    print(status_line, flush=True)
    self.last_print_time = current_time
```

### 4. 终端类型检测

```python
# Windows Terminal
if os.environ.get('WT_SESSION'):
    return 'windows_terminal'

# VSCode
if os.environ.get('TERM_PROGRAM') == 'vscode':
    return 'vscode'

# ConEmu
if 'conemu' in os.environ.get('ConEmuANSI', '').lower():
    return 'conemu'
```

---

## 后续优化建议

1. **更精细的终端检测**:
   - 检测终端颜色支持级别(8色/256色/真彩色)
   - 根据终端宽度自适应调整显示内容

2. **配置文件支持**:
   - 允许用户在`.auto-coder/config.yml`中配置显示模式
   - 保存用户的终端偏好设置

3. **Windows ConPTY支持**:
   - Windows 10 1809+ 提供ConPTY(伪终端)
   - 可考虑使用ConPTY改善终端兼容性

4. **Rich降级策略**:
   - 当Rich Live不可用时,使用Rich的其他组件(Table、Panel等)
   - 保持输出格式的一致性

---

## 参考文档

- [Windows Console Virtual Terminal Sequences](https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences)
- [Rich Library Documentation](https://rich.readthedocs.io/)
- [Python wcwidth Module](https://github.com/jquast/wcwidth)
- [ANSI Escape Code - Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code)
