#!/usr/bin/env python3
"""
MemFabric Hybrid 文档导航助手
用于快速查找和定位项目文档信息
"""

import os
import sys
import subprocess
from pathlib import Path

# 文档根目录
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"
README = DOCS_DIR / "README.md"


class MemDoc:
    """MemFabric Hybrid 文档导航器"""

    MODULES = {
        "util": ("01-util", "公共工具模块", 2707),
        "acc_links": ("02-acc_links", "内部通信层", 6364),
        "hybm": ("03-hybm", "内存管理与访问层 (核心)", 27970),
        "smem": ("04-smem", "语义与接口层", 14504),
        "3rdparty": ("05-3rdparty", "第三方库", None),
        "example": ("06-example", "示例代码", None),
    }

    API_TYPES = {
        "BM": ("Big Memory", "跨节点内存拷贝，支持 H2G/G2G/G2H 等操作"),
        "SHM": ("Shared Memory", "对称共享内存，支持 AllReduce 等集合操作"),
        "Trans": ("Transfer", "点对点数据传输，支持发送/接收语义"),
    }

    COPY_TYPES = {
        "H2G": "Host → Global (Device)",
        "G2G": "Global → Global (跨设备)",
        "G2H": "Global → Host",
        "L2G": "Local → Global",
        "G2L": "Global → Local",
    }

    def __init__(self):
        if not DOCS_DIR.exists():
            print(f"错误: 文档目录不存在: {DOCS_DIR}")
            sys.exit(1)

    def show_overview(self):
        """显示文档概览"""
        if README.exists():
            print(README.read_text()[:2000])
        else:
            print("README.md 不存在")

    def show_api_info(self, api=None):
        """显示 API 信息"""
        if api:
            api = api.upper()
            if api in self.API_TYPES:
                full_name, desc = self.API_TYPES[api]
                print(f"=== {api} API ({full_name}) ===")
                print(f"说明: {desc}")
            else:
                print(f"未知 API: {api}")
                print(f"可用 API: {', '.join(self.API_TYPES.keys())}")
        else:
            print("=== API 类型对比 ===")
            for api, (full_name, desc) in self.API_TYPES.items():
                print(f"\n{api} ({full_name}):")
                print(f"  {desc}")

    def show_module_info(self, module):
        """显示模块信息"""
        module_key = module.lower().replace("0", "").replace("-", "_")
        for key, (dir_name, desc, lines) in self.MODULES.items():
            if key in module or dir_name in module:
                print(f"=== {key} 模块 ===")
                print(f"目录: docs/{dir_name}/")
                print(f"描述: {desc}")
                if lines:
                    print(f"代码行数: {lines:,}")

                overview = DOCS_DIR / dir_name / "01-总览及导航.md"
                if overview.exists():
                    print(f"\n{overview.read_text()[:1500]}...")
                return

        print(f"未知模块: {module}")
        print(f"可用模块: {', '.join(self.MODULES.keys())}")

    def explain_concept(self, concept):
        """解释概念"""
        concept_upper = concept.upper()

        if concept_upper in self.COPY_TYPES:
            print(f"=== {concept_upper} 拷贝类型 ===")
            print(f"说明: {self.COPY_TYPES[concept_upper]}")
            print("\n代码示例:")
            if concept_upper == "H2G":
                print('  smem_bm_copy(handle, &params, SMEMB_COPY_H2G, 0)')
            elif concept_upper == "G2G":
                print('  smem_bm_copy(handle, &params, SMEMB_COPY_G2G, 0)')
            return

        # 其他概念搜索
        print(f"=== 概念: {concept} ===")

        # 在文档中搜索
        for md_file in DOCS_DIR.rglob("*.md"):
            content = md_file.read_text()
            if concept.lower() in content.lower():
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if concept.lower() in line.lower():
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        print(f"\n来自 {md_file.relative_to(DOCS_DIR)}:")
                        print("\n".join(lines[start:end]))
                        break
                return

        print(f"未找到概念 '{concept}' 的说明")

    def find_example(self, name):
        """查找示例"""
        example_dir = Path(__file__).parent.parent.parent / "example"

        print(f"=== 查找示例: {name} ===")

        # 在文档中查找
        example_doc = DOCS_DIR / "06-example" / "00-示例解读.md"
        if example_doc.exists():
            content = example_doc.read_text()
            if name.lower() in content.lower():
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if name.lower() in line.lower():
                        start = max(0, i - 3)
                        end = min(len(lines), i + 10)
                        print("\n".join(lines[start:end]))
                        return

        # 在示例代码中查找
        for cpp_file in example_dir.rglob("*.cpp"):
            if name.lower() in cpp_file.name.lower():
                print(f"\n找到文件: {cpp_file.relative_to(example_dir.parent)}")
                print(cpp_file.read_text()[:500] + "...")
                return

        print(f"未找到示例 '{name}'")

    def search(self, pattern):
        """搜索文档"""
        print(f"=== 搜索: {pattern} ===\n")

        print("文档中:")
        for md_file in DOCS_DIR.rglob("*.md"):
            content = md_file.read_text()
            if pattern.lower() in content.lower():
                print(f"  {md_file.relative_to(DOCS_DIR)}")

        print("\n源码中:")
        src_dir = Path(__file__).parent.parent.parent / "src"
        for src_file in src_dir.rglob("*"):
            if pattern.lower() in src_file.name.lower():
                print(f"  {src_file.relative_to(src_dir.parent)}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        doc = MemDoc()
        doc.show_overview()
        return

    cmd = sys.argv[1].lower()
    doc = MemDoc()

    if cmd == "api":
        api = sys.argv[2] if len(sys.argv) > 2 else None
        doc.show_api_info(api)
    elif cmd == "module":
        if len(sys.argv) < 3:
            print("请指定模块名称")
            print("可用模块:", ", ".join(doc.MODULES.keys()))
        else:
            doc.show_module_info(sys.argv[2])
    elif cmd == "concept":
        if len(sys.argv) < 3:
            print("请指定概念名称")
            print("常用概念:", ", ".join(list(doc.COPY_TYPES.keys()) + ["GVA", "RDMA", "AllReduce"]))
        else:
            doc.explain_concept(sys.argv[2])
    elif cmd == "example":
        if len(sys.argv) < 3:
            print("请指定示例名称")
            print("常用示例: allreduce, rdma, bm, shift")
        else:
            doc.find_example(sys.argv[2])
    elif cmd == "find":
        if len(sys.argv) < 3:
            print("请指定搜索模式")
        else:
            doc.search(sys.argv[2])
    else:
        # 默认作为概念搜索
        doc.explain_concept(cmd)


if __name__ == "__main__":
    main()
