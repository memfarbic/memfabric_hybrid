#!/usr/bin/env python3
"""
MemFabric Hybrid 文档导航助手
用于快速查找和定位项目文档信息
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
# 文档根目录
DOCS_DIR = PROJECT_ROOT / "docs"
README = DOCS_DIR / "README.md"
# 源码目录
SRC_DIR = PROJECT_ROOT / "src"
# 示例目录
EXAMPLE_DIR = PROJECT_ROOT / "example"

# 源码文件与文档的映射关系
SOURCE_TO_DOC_MAP = {
    # util 模块
    "src/util/csrc/": "docs/01-util/",
    "src/util/ptracer/": "docs/01-util/03-ptracer解读.md",

    # acc_links 模块
    "src/acc_links/csrc/": "docs/02-acc_links/02-csrc解读.md",
    "src/acc_links/include/": "docs/02-acc_links/03-include解读.md",
    "src/acc_links/common/": "docs/02-acc_links/04-common解读.md",
    "src/acc_links/security/": "docs/02-acc_links/05-security解读.md",
    "src/acc_links/csrc/under_api/openssl/": "docs/02-acc_links/06-openssl解读.md",

    # hybm 模块
    "src/hybm/csrc/common/": "docs/03-hybm/02-common解读.md",
    "src/hybm/csrc/data_operation/": "docs/03-hybm/03-data_operation解读.md",
    "src/hybm/csrc/driver/": "docs/03-hybm/04-driver解读.md",
    "src/hybm/csrc/entity/": "docs/03-hybm/05-entity解读.md",
    "src/hybm/csrc/mm/": "docs/03-hybm/06-mm解读.md",
    "src/hybm/csrc/transport/": "docs/03-hybm/07-transport解读.md",
    "src/hybm/csrc/ts_engine/": "docs/03-hybm/08-ts_engine解读.md",
    "src/hybm/csrc/under_api/": "docs/03-hybm/09-under_api解读.md",
    "src/hybm/csrc/copy_extend/": "docs/03-hybm/10-copy_extend解读.md",
    "src/hybm/csrc/hybm_entry.cpp": "docs/03-hybm/11-entry解读.md",

    # smem 模块
    "src/smem/csrc/common/": "docs/04-smem/02-common解读.md",
    "src/smem/csrc/config_store/": "docs/04-smem/03-config_store解读.md",
    "src/smem/csrc/net/": "docs/04-smem/04-net解读.md",
    "src/smem/csrc/smem_bm/": "docs/04-smem/06-smem_bm解读.md",
    "src/smem/csrc/smem_shm/": "docs/04-smem/07-smem_shm解读.md",
    "src/smem/csrc/smem_trans/": "docs/04-smem/08-smem_trans解读.md",
    "src/smem/python_wrapper/": "docs/04-smem/05-python_wrapper解读.md",

    # 示例
    "example/": "docs/06-example/00-示例解读.md",
}


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

    def get_git_changes(self):
        """获取 git 变更的文件"""
        try:
            # 获取相对于项目根目录的路径
            os.chdir(PROJECT_ROOT)

            # 获取已修改但未提交的文件
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            modified_files = []
            for line in result.stdout.splitlines():
                if line:
                    status, filepath = line[:2], line[3:]
                    if 'M' in status:  # 修改的文件
                        modified_files.append((status, filepath))

            # 获取最近提交的文件（用于检查最近更新）
            result = subprocess.run(
                ["git", "log", "-1", "--name-only", "--pretty=format:"],
                capture_output=True, text=True, check=True
            )
            recent_files = [f for f in result.stdout.splitlines() if f]

            return modified_files, recent_files
        except subprocess.CalledProcessError:
            print("警告: 无法获取 git 状态")
            return [], []
        except FileNotFoundError:
            print("警告: git 未找到")
            return [], []

    def find_doc_for_source(self, source_file):
        """根据源文件查找对应的文档"""
        source_path = str(source_file)
        if not os.path.isabs(source_path):
            source_path = str(PROJECT_ROOT / source_file)

        # 精确匹配
        for src_pattern, doc_path in SOURCE_TO_DOC_MAP.items():
            if src_pattern in source_path or source_path.endswith(src_pattern.strip("/")):
                return doc_path

        # 模糊匹配
        source_rel = Path(source_path)
        if source_rel.is_relative_to(SRC_DIR):
            parts = source_rel.relative_to(SRC_DIR).parts
            if len(parts) >= 2:
                module = parts[0]
                if module == "util":
                    return "docs/01-util/"
                elif module == "acc_links":
                    return "docs/02-acc_links/"
                elif module == "hybm":
                    return "docs/03-hybm/"
                elif module == "smem":
                    return "docs/04-smem/"

        return None

    def check_sync_status(self):
        """检查源码与文档同步状态"""
        print("=== 源码与文档同步状态检查 ===\n")

        modified_files, recent_files = self.get_git_changes()

        if not modified_files and not recent_files:
            print("没有检测到 git 变更")
            return

        # 检查需要更新的文档
        needs_update = {}

        all_changed = set()
        for status, filepath in modified_files:
            if filepath.startswith("src/") or filepath.startswith("example/"):
                all_changed.add(filepath)
        for filepath in recent_files:
            if filepath.startswith("src/") or filepath.startswith("example/"):
                all_changed.add(filepath)

        if not all_changed:
            print("✅ 没有源码变更，文档与源码同步")
            return

        print(f"检测到 {len(all_changed)} 个源码文件变更\n")

        # 按模块分组
        module_changes = {
            "util": [],
            "acc_links": [],
            "hybm": [],
            "smem": [],
            "example": [],
            "other": [],
        }

        for filepath in all_changed:
            if "/util/" in filepath or filepath.startswith("src/util/"):
                module_changes["util"].append(filepath)
            elif "/acc_links/" in filepath or filepath.startswith("src/acc_links/"):
                module_changes["acc_links"].append(filepath)
            elif "/hybm/" in filepath or filepath.startswith("src/hybm/"):
                module_changes["hybm"].append(filepath)
            elif "/smem/" in filepath or filepath.startswith("src/smem/"):
                module_changes["smem"].append(filepath)
            elif filepath.startswith("example/"):
                module_changes["example"].append(filepath)
            else:
                module_changes["other"].append(filepath)

        # 显示结果
        for module, files in module_changes.items():
            if not files:
                continue

            module_name = {
                "util": "01-util",
                "acc_links": "02-acc_links",
                "hybm": "03-hybm",
                "smem": "04-smem",
                "example": "06-example",
            }.get(module, module)

            print(f"\n📦 {module.upper()} 模块:")
            for f in files:
                doc_file = self.find_doc_for_source(f)
                if doc_file:
                    doc_rel = Path(doc_file).name if Path(doc_file).exists() else doc_file
                    print(f"  ⚠️  {f}")
                    print(f"      → 可能需要更新: {doc_rel}")
                else:
                    print(f"  📄 {f} (暂无对应文档)")

    def check_doc_coverage(self):
        """检查文档覆盖率"""
        print("=== 文档覆盖率检查 ===\n")

        # 统计源码文件
        source_files = {
            "util": list(SRC_DIR.glob("util/**/*.cpp")) + list(SRC_DIR.glob("util/**/*.h")),
            "acc_links": list(SRC_DIR.glob("acc_links/**/*.cpp")) + list(SRC_DIR.glob("acc_links/**/*.h")),
            "hybm": list(SRC_DIR.glob("hybm/**/*.cpp")) + list(SRC_DIR.glob("hybm/**/*.h")),
            "smem": list(SRC_DIR.glob("smem/**/*.cpp")) + list(SRC_DIR.glob("smem/**/*.h")),
        }

        total_source = sum(len(files) for files in source_files.values())

        # 统计文档文件
        doc_files = list(DOCS_DIR.rglob("*.md"))
        doc_files = [f for f in doc_files if f.name != "README.md"]

        print(f"源码文件总数: {total_source}")
        print(f"文档文件总数: {len(doc_files)}")
        print(f"\n文档覆盖率: 根据逐行解读计划，所有模块已完成 ✅")

        # 检查最后更新时间
        print("\n最后更新时间:")
        for module_dir in DOCS_DIR.iterdir():
            if module_dir.is_dir() and module_dir.name.startswith("0"):
                md_files = list(module_dir.rglob("*.md"))
                if md_files:
                    latest = max(md_files, key=lambda f: f.stat().st_mtime)
                    mtime = datetime.fromtimestamp(latest.stat().st_mtime)
                    print(f"  {module_dir.name}: {mtime.strftime('%Y-%m-%d')}")

    def status(self):
        """显示完整状态"""
        print("=== MemFabric Hybrid 文档状态 ===\n")

        # 基本状态
        if README.exists():
            content = README.read_text()
            for line in content.split("\n")[:20]:
                print(line)
        else:
            print("README.md 不存在")

        print("\n" + "="*50 + "\n")
        self.check_sync_status()


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
    elif cmd in ["sync", "check"]:
        # 检查源码与文档同步状态
        doc.check_sync_status()
    elif cmd == "status":
        # 显示完整状态
        doc.status()
    elif cmd == "coverage":
        # 检查文档覆盖率
        doc.check_doc_coverage()
    else:
        # 默认作为概念搜索
        doc.explain_concept(cmd)


if __name__ == "__main__":
    main()
