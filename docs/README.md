# MemFabric Hybrid 项目文档索引与上下文

> 最后更新: 2025-03-01
> 文档状态: 全部完成 ✅

## 项目概述

**MemFabric Hybrid** 是一款面向昇腾超节点和服务器的开源内存池化软件，主要提供：
- 异构设备的统一池化（DRAM|HBM等）
- 内存语义访问接口
- 高性能的跨机器内存直接访问能力

### 项目规模
- **总文件数**: 259 个源代码文件
- **总代码行数**: 约 51,545 行
- **文档覆盖**: 100%

---

## 文档目录结构

```
docs/
├── 00-项目总览.md           # 项目架构与快速入门
├── 01-util/                 # 公共工具模块 (2,707 行)
├── 02-acc_links/            # 内部通信层 (6,364 行)
├── 03-hybm/                 # 内存管理与访问层 (27,970 行) ⭐核心
├── 04-smem/                 # 语义与接口层 (14,504 行)
├── 05-3rdparty/             # 第三方库说明
└── 06-example/              # 示例代码解读
```

---

## 模块导航

### 1. Util 模块 (`01-util/`)
提供跨模块的公共工具函数。

| 文件 | 说明 |
|------|------|
| [01-总览及导航.md](01-util/01-总览及导航.md) | 模块概述与文件导航 |
| [02-csrc解读.md](01-util/02-csrc解读.md) | 11个工具头文件逐行解读 |
| [03-ptracer解读.md](01-util/03-ptracer解读.md) | 性能打点工具 |

### 2. Acc_links 模块 (`02-acc_links/`)
基于 TCP 的进程间控制命令通信层。

| 文件 | 说明 |
|------|------|
| [01-总览及导航.md](02-acc_links/01-总览及导航.md) | Server-Worker-Link 架构说明 |
| [02-csrc解读.md](02-acc_links/02-csrc解读.md) | TCP 服务器、工作线程、链路实现 |
| [03-include解读.md](02-acc_links/03-include解读.md) | 公共接口定义 |
| [04-common解读.md](02-acc_links/04-common解读.md) | 通用组件 |
| [05-security解读.md](02-acc_links/05-security解读.md) | SSL 助手 |
| [06-openssl解读.md](02-acc_links/06-openssl解读.md) | OpenSSL 动态加载封装 |

### 3. HyBM 模块 (`03-hybm/`) ⭐核心
全局内存管理 + 数据操作 + 传输管理。

| 文件 | 说明 | 重要性 |
|------|------|--------|
| [01-总览及导航.md](03-hybm/01-总览及导航.md) | 三层架构详解 | ⭐⭐⭐ |
| [02-common解读.md](03-hybm/02-common解读.md) | 公共定义与工具 | ⭐⭐ |
| [03-data_operation解读.md](03-hybm/03-data_operation解读.md) | xcopy 数据操作算子 | ⭐⭐⭐ |
| [04-driver解读.md](03-hybm/04-driver解读.md) | 驱动接口与 GVA 管理 | ⭐⭐⭐ |
| [05-entity解读.md](03-hybm/05-entity解读.md) | 实体管理核心 (1,238行) | ⭐⭐⭐ |
| [06-mm解读.md](03-hybm/06-mm解读.md) | 内存管理与 VMM | ⭐⭐⭐ |
| [07-transport解读.md](03-hybm/07-transport解读.md) | Device/Host 传输管理 | ⭐⭐⭐ |
| [08-ts_engine解读.md](03-hybm/08-ts_engine解读.md) | 任务流引擎 | ⭐⭐ |
| [09-under_api解读.md](03-hybm/09-under_api解读.md) | 下层 API 封装 | ⭐⭐ |
| [10-copy_extend解读.md](03-hybm/10-copy_extend解读.md) | 拷贝扩展 | ⭐ |
| [11-entry解读.md](03-hybm/11-entry解读.md) | 模块入口点 | ⭐⭐⭐ |

### 4. Smem 模块 (`04-smem/`)
语义接口层 (BM API + SHM API + Trans API)。

| 文件 | 说明 | 重要性 |
|------|------|--------|
| [01-总览及导航.md](04-smem/01-总览及导航.md) | 三种 API 使用场景 | ⭐⭐⭐ |
| [02-common解读.md](04-smem/02-common解读.md) | 公共组件 | ⭐⭐ |
| [03-config_store解读.md](04-smem/03-config_store解读.md) | 配置存储 (TCP/HA) | ⭐⭐⭐ |
| [04-net解读.md](04-smem/04-net解读.md) | 网络组引擎 | ⭐⭐⭐ |
| [05-python_wrapper解读.md](04-smem/05-python_wrapper解读.md) | Python 绑定 | ⭐⭐ |
| [06-smem_bm解读.md](04-smem/06-smem_bm解读.md) | Big Memory API | ⭐⭐⭐ |
| [07-smem_shm解读.md](04-smem/07-smem_shm解读.md) | Shared Memory API | ⭐⭐⭐ |
| [08-smem_trans解读.md](04-smem/08-smem_trans解读.md) | Transfer API | ⭐⭐⭐ |

### 5. 第三方库 (`05-3rdparty/`)
| 文件 | 说明 |
|------|------|
| [说明文档.md](05-3rdparty/说明文档.md) | Googletest, Mockcpp, OpenSSL, RDMA |

### 6. 示例代码 (`06-example/`)
| 文件 | 说明 |
|------|------|
| [00-示例解读.md](06-example/00-示例解读.md) | BM/SHM/Trans 完整示例 |

---

## 核心概念速查

### API 类型

| API | 全称 | 用途 |
|-----|------|------|
| **BM API** | Big Memory | 跨节点内存拷贝，支持 H2G/G2G/G2H 等操作 |
| **SHM API** | Shared Memory | 对称共享内存，支持 AllReduce 等集合操作 |
| **Trans API** | Transfer | 点对点数据传输，支持发送/接收语义 |

### 内存拷贝类型

| 类型 | 说明 | 示例 |
|------|------|------|
| H2G | Host → Global (Device) | `smem_bm_copy(handle, &params, SMEMB_COPY_H2G, 0)` |
| G2G | Global → Global (Device→Device) | 跨 NPU 内存拷贝 |
| G2H | Global → Host | 设备内存回传到主机 |
| L2G | Local → Global | 本地内存到全局虚拟地址 |
| G2L | Global → Local | 全局虚拟地址到本地 |

### 传输管理器

| 类型 | 说明 | 文件 |
|------|------|------|
| Device RDMA | 设备端 RDMA 传输 | `device_rdma_transport_manager.cpp` |
| Host HCOM | 主机端 HCOM 传输 | `host_hcom_transport_manager.cpp` |
| Compose | 组合传输管理器 | `compose_transport_manager.cpp` |

---

## 关键文件快速索引

### 核心入口
- [hybm_entry.cpp](../src/hybm/csrc/hybm_entry.cpp) - HyBM 模块入口
- [smem.cpp](../src/smem/csrc/smem.cpp) - Smem 模块入口

### 高优先级文件 (行数 > 1000)
| 文件 | 行数 | 模块 | 功能 |
|------|------|------|------|
| `hybm_entity_default.cpp` | 1,238 | hybm/entity | 实体管理核心 |
| `smem_net_group_engine.cpp` | 1,109 | smem/net | 网络组引擎 |
| `host_hcom_transport_manager.cpp` | 1,068 | hybm/transport | HCOM 传输 |
| `hybm_data_op_host_rdma.cpp` | 1,024 | hybm/data_operation | Host RDMA 操作 |

### 中优先级文件 (行数 600-1000)
| 文件 | 行数 | 模块 | 功能 |
|------|------|------|------|
| `device_rdma_transport_manager.cpp` | 968 | hybm/transport | Device RDMA 传输 |
| `bipartite_ranks_qp_manager.cpp` | 861 | hybm/transport | QP 管理器 |
| `smem_tcp_config_store_server.cpp` | 899 | smem/config_store | TCP 存储服务器 |
| `smem_trans_entry.cpp` | 702 | smem/trans | Trans 入口 |
| `devmm_svm_gva.cpp` | 695 | hybm/driver | SVM GVA 实现 |
| `acc_tcp_server_default.cpp` | 681 | acc_links | TCP 服务器 |
| `acc_tcp_ssl_helper.cpp` | 610 | acc_links/security | SSL 助手 |

---

## 技术栈

### 编程语言
- C++17 (核心代码)
- Python 3.x (Python 绑定)
- C (部分驱动层)

### 依赖库
- **Googletest** v1.14.0 - 单元测试
- **Mockcpp** v2.7 - Mock 框架
- **rdma-core** - RDMA 支持
- **OpenSSL** - TLS 1.3 安全通信

### 硬件平台
- 华为昇腾 NPU (Ascend)
- 支持 RDMA 的网卡

---

## 阅读建议

### 新手入门路径
1. 阅读 [00-项目总览.md](00-项目总览.md)
2. 阅读 [01-util/01-总览及导航.md](01-util/01-总览及导航.md)
3. 阅读 [06-example/00-示例解读.md](06-example/00-示例解读.md) 运行示例

### 架构理解路径
1. [03-hybm/01-总览及导航.md](03-hybm/01-总览及导航.md)
2. [04-smem/01-总览及导航.md](04-smem/01-总览及导航.md)
3. [02-acc_links/01-总览及导航.md](02-acc_links/01-总览及导航.md)

### 核心功能深入
1. BM API: [04-smem/06-smem_bm解读.md](04-smem/06-smem_bm解读.md)
2. SHM API: [04-smem/07-smem_shm解读.md](04-smem/07-smem_shm解读.md)
3. 传输管理: [03-hybm/07-transport解读.md](03-hybm/07-transport解读.md)

---

## Git 提交信息

最近提交:
- `8625437b` - 完成 acc_links/openssl 模块文档
- 分支: `develop`
- 待推送: `git push origin develop`

---

## 维护状态

| 模块 | 状态 | 完成度 |
|------|------|--------|
| util | ✅ 完成 | 100% |
| acc_links | ✅ 完成 | 100% |
| hybm | ✅ 完成 | 100% |
| smem | ✅ 完成 | 100% |
| 3rdparty | ✅ 完成 | 100% |
| example | ✅ 完成 | 100% |

---

*本文档由 Claude Code 自动生成和维护*
