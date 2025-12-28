#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 规则文件转换为 Markdown 格式的脚本

用法:
    python scripts/convert_rules.py

功能:
    1. 解析 Excel 规则文件（xlsx）
    2. 生成 Markdown 规则文件
    3. 自动修正包名：cn.customs.* → cn.gov.customs.*
"""

import zipfile
import xml.etree.ElementTree as ET
import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Rule:
    """规则数据类"""
    id: str
    title: str
    severity: str
    description: str
    explanation: str
    bad_example: str
    good_example: str


def parse_xlsx(xlsx_path: str) -> List[Rule]:
    """
    解析 xlsx 文件，提取规则数据

    Args:
        xlsx_path: xlsx 文件路径

    Returns:
        规则列表
    """
    rules = []

    with zipfile.ZipFile(xlsx_path, 'r') as zf:
        # 读取共享字符串
        shared_strings = []
        if 'xl/sharedStrings.xml' in zf.namelist():
            content = zf.read('xl/sharedStrings.xml').decode('utf-8')
            root = ET.fromstring(content)
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for si in root.findall('.//main:si', ns):
                # 处理包含多个 <t> 元素的情况
                texts = []
                for t in si.findall('.//main:t', ns):
                    if t.text:
                        texts.append(t.text)
                shared_strings.append(''.join(texts))

        # 读取工作表
        sheet_content = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
        root = ET.fromstring(sheet_content)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

        # 解析行数据
        rows_data = []
        for row in root.findall('.//main:row', ns):
            row_num = int(row.get('r', 0))
            cells = {}
            for cell in row.findall('main:c', ns):
                cell_ref = cell.get('r', '')  # 如 A1, B1
                col_letter = ''.join(filter(str.isalpha, cell_ref))
                cell_type = cell.get('t')
                value_elem = cell.find('main:v', ns)

                if value_elem is not None:
                    if cell_type == 's':  # 共享字符串
                        idx = int(value_elem.text)
                        cells[col_letter] = shared_strings[idx] if idx < len(shared_strings) else ''
                    else:
                        cells[col_letter] = value_elem.text or ''
                else:
                    cells[col_letter] = ''

            if cells:
                rows_data.append((row_num, cells))

        # 跳过表头行，处理数据行
        # 表头: A=规则ID, B=标题, C=规则来源(忽略), D=严重程度, E=描述, F=说明, G=错误示例, H=正确示例
        for row_num, cells in rows_data:
            if row_num == 1:  # 跳过表头
                continue

            rule_id = cells.get('A', '').strip()
            if not rule_id or not rule_id.startswith(('backend_', 'frontend_')):
                continue

            rule = Rule(
                id=rule_id,
                title=cells.get('B', '').strip(),
                severity=cells.get('D', 'warning').strip().lower() or 'warning',
                description=cells.get('E', '').strip(),
                explanation=cells.get('F', '').strip(),
                bad_example=cells.get('G', '').strip(),
                good_example=cells.get('H', '').strip(),
            )
            rules.append(rule)

    return rules


def fix_package_name(text: str) -> str:
    """
    修正包名：cn.customs.* → cn.gov.customs.*

    Args:
        text: 原始文本

    Returns:
        修正后的文本
    """
    if not text:
        return text
    # 匹配 cn.customs 后面跟着点或星号或空格或行尾的情况
    return re.sub(r'cn\.customs(?=[\.\*\s]|$)', 'cn.gov.customs', text)


def get_category(rule_id: str, rule_type: str) -> str:
    """
    根据规则ID获取分类名称

    Args:
        rule_id: 规则ID (如 backend_001)
        rule_type: 规则类型 (backend 或 frontend)

    Returns:
        分类名称
    """
    # 提取数字部分
    num = int(rule_id.split('_')[1])

    if rule_type == 'backend':
        if num <= 4:
            return "应用开发架构使用"
        elif num <= 13:
            return "代码结构"
        elif num <= 22:
            return "其他"
        elif num == 23:
            return "安全性"
        elif num <= 28:
            return "异常处理"
        elif num <= 30:
            return "安全性"
        elif num <= 33:
            return "缓存"
        elif num <= 36:
            return "配置_工具"
        elif num <= 39:
            return "日志输出"
        elif num <= 43:
            return "接口定义"
        elif num <= 47:
            return "数据库"
        elif num <= 50:
            return "配置_工具"
        else:
            return "海关定制"
    else:  # frontend
        if num <= 5:
            return "应用开发架构使用"
        elif num <= 19:
            return "代码结构"
        elif num <= 26:
            return "布局规范"
        elif num == 27:
            return "字体设置"
        elif num <= 32:
            return "字体大小-标准版"
        elif num <= 37:
            return "字体大小-关怀版"
        elif num <= 61:
            return "颜色-海关蓝"
        elif num <= 70:
            return "颜色-政务红"
        elif num <= 78:
            return "边距"
        elif num <= 86:
            return "按钮"
        else:
            return "业界通用"


def generate_markdown(rules: List[Rule], rule_type: str, output_path: str):
    """
    生成 Markdown 格式的规则文件

    Args:
        rules: 规则列表
        rule_type: 规则类型 (backend 或 frontend)
        output_path: 输出文件路径
    """
    # 标题
    if rule_type == 'backend':
        title = "后端代码检查规则"
        intro = f"本文档包含 {len(rules)} 条后端代码检查规则，适用于 Python 和 Java 后端开发。"
    else:
        title = "前端代码检查规则"
        intro = f"本文档包含 {len(rules)} 条前端代码检查规则，适用于 Vue/TypeScript 前端开发。"

    # 按分类分组
    categories: Dict[str, List[Rule]] = {}
    for rule in rules:
        category = get_category(rule.id, rule_type)
        if category not in categories:
            categories[category] = []
        categories[category].append(rule)

    # 生成 Markdown
    lines = [
        f"# {title}",
        "",
        intro,
        "",
        "---",
        "",
    ]

    for category, category_rules in categories.items():
        lines.append(f"## {category}")
        lines.append("")

        for rule in category_rules:
            lines.append(f"### 规则ID: {rule.id}")
            lines.append(f"**标题**: {fix_package_name(rule.title)}")
            lines.append(f"**严重程度**: {rule.severity}")
            lines.append(f"**描述**: {fix_package_name(rule.description)}")
            lines.append("")

            if rule.explanation:
                lines.append(f"**说明**: {fix_package_name(rule.explanation)}")
                lines.append("")

            if rule.bad_example:
                lines.append("**错误示例**:")
                # 检测代码语言
                lang = "java" if rule_type == "backend" else "javascript"
                if "```" in rule.bad_example:
                    # 已经包含代码块标记，直接使用
                    lines.append(fix_package_name(rule.bad_example))
                else:
                    lines.append(f"```{lang}")
                    lines.append(fix_package_name(rule.bad_example))
                    lines.append("```")
                lines.append("")

            if rule.good_example:
                lines.append("**正确示例**:")
                lang = "java" if rule_type == "backend" else "javascript"
                if "```" in rule.good_example:
                    lines.append(fix_package_name(rule.good_example))
                else:
                    lines.append(f"```{lang}")
                    lines.append(fix_package_name(rule.good_example))
                    lines.append("```")
                lines.append("")

            lines.append("---")
            lines.append("")

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"已生成: {output_path} ({len(rules)} 条规则)")


def main():
    """主函数"""
    # 项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Excel 文件路径
    backend_xlsx = os.path.join(project_root, "backend_rules修订版 (2).xlsx")
    frontend_xlsx = os.path.join(project_root, "frontend_rules修订版 (1).xlsx")

    # 输出文件路径
    backend_md = os.path.join(project_root, "rules", "backend_rules.md")
    frontend_md = os.path.join(project_root, "rules", "frontend_rules.md")

    # 检查文件是否存在
    if not os.path.exists(backend_xlsx):
        print(f"错误: 找不到后端规则 Excel 文件: {backend_xlsx}")
        return 1

    if not os.path.exists(frontend_xlsx):
        print(f"错误: 找不到前端规则 Excel 文件: {frontend_xlsx}")
        return 1

    # 转换后端规则
    print("正在解析后端规则...")
    backend_rules = parse_xlsx(backend_xlsx)
    print(f"  解析到 {len(backend_rules)} 条规则")
    generate_markdown(backend_rules, "backend", backend_md)

    # 转换前端规则
    print("正在解析前端规则...")
    frontend_rules = parse_xlsx(frontend_xlsx)
    print(f"  解析到 {len(frontend_rules)} 条规则")
    generate_markdown(frontend_rules, "frontend", frontend_md)

    print("\n转换完成！")
    print(f"  后端规则: {backend_md}")
    print(f"  前端规则: {frontend_md}")

    return 0


if __name__ == "__main__":
    exit(main())
