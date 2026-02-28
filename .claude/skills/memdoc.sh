#!/bin/bash
# MemFabric Hybrid 文档导航技能实现

DOCS_DIR="$(git rev-parse --show-toplevel)/docs"
README="$DOCS_DIR/README.md"

show_overview() {
    echo "=== MemFabric Hybrid 文档概览 ==="
    echo ""
    cat "$README" | head -60
}

show_api_info() {
    echo "=== MemFabric Hybrid API 对比 ==="
    echo ""
    cat "$README" | grep -A 10 "### API 类型"
}

show_module_info() {
    local module=$1
    echo "=== $module 模块信息 ==="
    echo ""

    case "$module" in
        "util"|"01-util")
            cat "$DOCS_DIR/01-util/01-总览及导航.md" 2>/dev/null || head -100 "$DOCS_DIR/01-util"/*.md
            ;;
        "acc_links"|"02-acc_links")
            cat "$DOCS_DIR/02-acc_links/01-总览及导航.md" 2>/dev/null || head -100 "$DOCS_DIR/02-acc_links"/*.md
            ;;
        "hybm"|"03-hybm")
            cat "$DOCS_DIR/03-hybm/01-总览及导航.md" 2>/dev/null || head -100 "$DOCS_DIR/03-hybm"/*.md
            ;;
        "smem"|"04-smem")
            cat "$DOCS_DIR/04-smem/01-总览及导航.md" 2>/dev/null || head -100 "$DOCS_DIR/04-smem"/*.md
            ;;
        *)
            echo "未知模块: $module"
            echo "可用模块: util, acc_links, hybm, smem, 3rdparty, example"
            ;;
    esac
}

explain_concept() {
    local concept=$1
    echo "=== 概念解释: $concept ==="
    echo ""

    case "$concept" in
        "G2G"|"H2G"|"G2H"|"L2G"|"G2L")
            cat "$README" | grep -A 5 "### 内存拷贝类型"
            ;;
        "GVA"|"Global Virtual Address")
            echo "GVA (Global Virtual Address) - 全局虚拟地址"
            echo "详见: docs/03-hybm/04-driver解读.md"
            grep -i "GVA\|全局虚拟" "$DOCS_DIR/03-hybm/04-driver解读.md" 2>/dev/null | head -20
            ;;
        "RDMA"|"Remote Direct Memory Access")
            echo "RDMA - 远程直接内存访问"
            echo "相关文件:"
            echo "  - src/hybm/csrc/data_operation/host/hybm_data_op_host_rdma.cpp"
            echo "  - src/hybm/csrc/transport/device/device_rdma_transport_manager.cpp"
            ;;
        "AllReduce")
            echo "AllReduce - 集合通信原语，所有节点求和并广播"
            echo "示例: docs/06-example/00-示例解读.md"
            grep -A 20 "AllReduce" "$DOCS_DIR/06-example/00-示例解读.md" 2>/dev/null | head -30
            ;;
        *)
            echo "搜索概念: $concept"
            grep -r -i "$concept" "$DOCS_DIR" --include="*.md" | head -10
            ;;
    esac
}

find_example() {
    local example=$1
    echo "=== 查找示例: $example ==="
    echo ""

    grep -r -i "$example" "$DOCS_DIR/06-example/" --include="*.md" -A 5 2>/dev/null || \
    grep -r -i "$example" "example/" --include="*.cpp" --include="*.py" -l
}

search_pattern() {
    local pattern=$1
    echo "=== 搜索: $pattern ==="
    echo ""

    echo "文档中:"
    grep -r "$pattern" "$DOCS_DIR" --include="*.md" -l | head -10

    echo ""
    echo "源码中:"
    find src/ -name "*$pattern*" -type f 2>/dev/null | head -10
}

# 主处理逻辑
case "$1" in
    "")
        show_overview
        ;;
    "api")
        show_api_info
        ;;
    "module")
        if [ -z "$2" ]; then
            echo "请指定模块名称"
            echo "可用模块: util, acc_links, hybm, smem, 3rdparty, example"
        else
            show_module_info "$2"
        fi
        ;;
    "concept")
        if [ -z "$2" ]; then
            echo "请指定概念名称"
            echo "常用概念: G2G, H2G, GVA, RDMA, AllReduce"
        else
            explain_concept "$2"
        fi
        ;;
    "example")
        if [ -z "$2" ]; then
            ls -la "$DOCS_DIR/06-example/"
        else
            find_example "$2"
        fi
        ;;
    "find")
        if [ -z "$2" ]; then
            echo "请指定搜索模式"
        else
            search_pattern "$2"
        fi
        ;;
    *)
        echo "未知命令: $1"
        echo "使用方式: /memdoc [api|module|concept|example|find] [参数]"
        ;;
esac
