# HYBM Transport 模块逐行解读

## 模块概述

Transport 模块是 HyBM 的传输管理层，负责实现跨节点内存传输的底层通信功能。该模块提供了统一的传输接口抽象，支持多种传输协议：

- **HCOM (Host Communication)**: 主机端通信，支持 TCP、RoCE、UB (User Barrier) 等协议
- **HCCP (Device Communication)**: 设备端 RDMA 通信，NPU 直接发起远程内存访问
- **Compose**: 组合传输，同时管理主机和设备传输，根据策略选择最优传输方式

## 目录结构

```
transport/
├── hybm_transport_manager.h/cpp        # 传输管理器基类和工厂
├── hybm_transport_common.h              # 传输公共定义
├── compose/                              # 组合传输
│   ├── compose_transport_manager.h/cpp
├── host/                                # 主机端传输
│   ├── host_hcom_common.h              # HCOM 通用定义
│   ├── host_hcom_helper.h/cpp          # HCOM 辅助函数
│   ├── host_hcom_transport_manager.h/cpp
│   └── host_hcom_counter_stream.h      # 计数器流
└── device/                              # 设备端传输
    ├── device_rdma_transport_manager.h/cpp
    ├── device_rdma_common.h            # RDMA 公共定义
    ├── device_rdma_helper.h/cpp        # RDMA 辅助函数
    ├── device_qp_manager.h/cpp         # QP 管理器基类
    ├── bipartite_ranks_qp_manager.h/cpp # 二分图 QP 管理器
    ├── fixed_ranks_qp_manager.h/cpp     # 固定 QP 管理器
    ├── joinable_ranks_qp_manager.h/cpp  # 可加入 QP 管理器
    └── device_chip_info.h/cpp           # 设备芯片信息
```

---

## 1. hybm_transport_common.h - 传输公共定义

### 文件信息
- 文件路径: `src/hybm/csrc/transport/hybm_transport_common.h`
- 代码行数: 152 行
- 主要功能: 定义传输层使用的公共数据结构和常量

### 完整代码与逐行解读

#### 头文件引用 (行 1-26)

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * MemFabric_Hybrid is licensed under Mulan PSL v2.
 * ...
*/

#ifndef MF_HYBRID_HYBM_TRANSPORT_COMMON_H
#define MF_HYBRID_HYBM_TRANSPORT_COMMON_H

#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>
#include <ostream>
#include <iomanip>
#include <unordered_map>
#include "hybm_def.h"
#include "hybm_define.h"
#include "dl_hccp_def.h"
```

**逐行解读**:
- 第 1-11 行: 版权声明和许可证信息
- 第 13-14 行: 头文件保护宏，防止重复包含
- 第 16-22 行: 引入标准库头文件
  - `<cstdint>`: 整数类型定义
  - `<cstddef>`: size_t 等类型
  - `<string>`: 字符串类
  - `<vector>`: 动态数组
  - `<ostream>`: 输出流
  - `<iomanip>`: 输出格式化
  - `<unordered_map>`: 哈希表
- 第 23-25 行: 引入项目内部头文件
  - `hybm_def.h`: HyBM 基础定义
  - `hybm_define.h`: HyBM 宏定义
  - `dl_hccp_def.h`: HCCP (Host Communication Control Protocol) 定义

#### 命名空间和常量定义 (行 27-39)

```cpp
namespace ock {
namespace mf {
namespace transport {
constexpr uint32_t REG_MR_FLAG_DRAM = 0x1U;
constexpr uint32_t REG_MR_FLAG_HBM = 0x2U;
constexpr uint32_t REG_MR_FLAG_SELF = 0x4U;
constexpr uint32_t REG_MR_FLAG_ACL_DRAM = 0x8U;

constexpr int32_t REG_MR_ACCESS_FLAG_LOCAL_WRITE = 0x1;
constexpr int32_t REG_MR_ACCESS_FLAG_REMOTE_WRITE = 0x2;
constexpr int32_t REG_MR_ACCESS_FLAG_REMOTE_READ = 0x4;
constexpr int32_t REG_MR_ACCESS_FLAG_BOTH_READ_WRITE = 0x7;
constexpr uint32_t KEY_SIZE = 14;
```

**逐行解读**:
- 第 27-29 行: 定义三层嵌套命名空间 `ock::mf::transport`
- 第 30 行: `REG_MR_FLAG_DRAM = 0x1` - 标识注册的是 DRAM 内存
- 第 31 行: `REG_MR_FLAG_HBM = 0x2` - 标识注册的是 HBM 内存
- 第 32 行: `REG_MR_FLAG_SELF = 0x4` - 标识是自身内存（不需要导入到 VA 管理器）
- 第 33 行: `REG_MR_FLAG_ACL_DRAM = 0x8` - 标识 ACL DRAM 内存
- 第 35 行: `REG_MR_ACCESS_FLAG_LOCAL_WRITE = 0x1` - 本地写权限
- 第 36 行: `REG_MR_ACCESS_FLAG_REMOTE_WRITE = 0x2` - 远程写权限
- 第 37 行: `REG_MR_ACCESS_FLAG_REMOTE_READ = 0x4` - 远程读权限
- 第 38 行: `REG_MR_ACCESS_FLAG_BOTH_READ_WRITE = 0x7` - 完整读写权限 (1|2|4)
- 第 39 行: `KEY_SIZE = 14` - 内存密钥数组大小

#### 传输类型枚举 (行 41-46)

```cpp
enum TransportType {
    TT_HCCP = 0,
    TT_HCOM,
    TT_COMPOSE,
    TT_BUTT,
};
```

**逐行解读**:
- 第 41 行: 定义 `TransportType` 枚举，表示传输类型
- 第 42 行: `TT_HCCP = 0` - 设备端 RDMA 传输 (HCCP 协议)
- 第 43 行: `TT_HCOM` - 主机端通信传输 (HCOM 协议)
- 第 44 行: `TT_COMPOSE` - 组合传输模式
- 第 45 行: `TT_BUTT` - 枚举边界值（用于数组大小等）

#### TransportOptions 结构体 (行 48-56)

```cpp
struct TransportOptions {
    uint32_t rankId;
    uint32_t rankCount;
    uint32_t protocol;
    hybm_type initialType;
    hybm_role_type role;
    std::string nic;
    hybm_tls_config tlsOption;
};
```

**逐行解读**:
- 第 48 行: 定义传输选项结构体
- 第 49 行: `rankId` - 当前进程的 Rank ID
- 第 50 行: `rankCount` - 总 Rank 数量
- 第 51 行: `protocol` - 传输协议类型（位掩码）
- 第 52 行: `initialType` - 初始化类型
- 第 53 行: `role` - 角色（PEER/SENDER/RECEIVER）
- 第 54 行: `nic` - 网卡设备名
- 第 55 行: `tlsOption` - TLS 配置选项

#### TransportOptions 输出运算符 (行 58-63)

```cpp
static inline std::ostream &operator<<(std::ostream &output, const TransportOptions &options)
{
    output << "TransportOptions(rankId=" << options.rankId << ", count=" << options.rankCount << ", nic=" << options.nic
           << ")";
    return output;
}
```

**逐行解读**:
- 第 58 行: 重载输出运算符，用于日志打印
- 第 59-62 行: 输出格式化的 TransportOptions 信息

#### TransportMemoryRegion 结构体 (行 65-77)

```cpp
struct TransportMemoryRegion {
    uint64_t addr = 0;                                   /* virtual address of memory could be hbm or host dram */
    uint64_t size = 0;                                   /* size of memory to be registered */
    int32_t access = REG_MR_ACCESS_FLAG_BOTH_READ_WRITE; /* access right by local and remote */
    uint32_t flags = 0;                                  /* optional flags: 加一个flag标识是DRAM还是HBM */
};
```

**逐行解读**:
- 第 65 行: 定义传输内存区域结构体
- 第 66 行: `addr` - 内存虚拟地址（可能是 HBM 或 Host DRAM）
- 第 67 行: `size` - 要注册的内存大小
- 第 68 行: `access` - 访问权限，默认为完整读写权限
- 第 69 行: `flags` - 标志位，标识内存类型（DRAM/HBM/SELF）

#### TransportMemoryKey 结构体 (行 79-82)

```cpp
struct TransportMemoryKey {
    uint64_t keys[KEY_SIZE * 2];
};
```

**逐行解读**:
- 第 79 行: 定义传输内存密钥结构体
- 第 80 行: `keys` - 密钥数组，大小为 KEY_SIZE * 2 = 28
  - 设备 RDMA 使用前 14 个元素
  - 主机 HCOM 使用后 14 个元素

#### 密钥读写辅助函数 (行 83-101)

```cpp
inline void ReadDeviceRdmaMemoryKey(const TransportMemoryKey &input, TransportMemoryKey &output)
{
    std::copy_n(input.keys, KEY_SIZE, output.keys);
}

inline void ReadHcomMemoryKey(const TransportMemoryKey &input, TransportMemoryKey &output)
{
    std::copy_n(input.keys + KEY_SIZE, KEY_SIZE, output.keys);
}

inline void WriteDeviceRdmaMemoryKey(const TransportMemoryKey &input, TransportMemoryKey &output)
{
    std::copy_n(input.keys, KEY_SIZE, output.keys);
}

inline void WriteHcomMemoryKey(const TransportMemoryKey &input, TransportMemoryKey &output)
{
    std::copy_n(input.keys, KEY_SIZE, output.keys + KEY_SIZE);
}
```

**逐行解读**:
- 第 83-86 行: 从组合密钥读取设备 RDMA 密钥（前 14 个元素）
- 第 88-91 行: 从组合密钥读取 HCOM 密钥（后 14 个元素）
- 第 93-96 行: 写入设备 RDMA 密钥到组合密钥的前 14 个元素
- 第 98-101 行: 写入 HCOM 密钥到组合密钥的后 14 个元素

#### TransportRankPrepareInfo 结构体 (行 112-131)

```cpp
struct TransportRankPrepareInfo {
    std::string nic;
    hybm_role_type role{HYBM_ROLE_PEER};
    std::vector<TransportMemoryKey> memKeys;
    TransportRankPrepareInfo() {}
    TransportRankPrepareInfo(std::string n, TransportMemoryKey k) : nic{std::move(n)}, memKeys{k} {}
    TransportRankPrepareInfo(std::string n, std::vector<TransportMemoryKey> ks)
        : nic{std::move(n)}, memKeys{std::move(ks)}
        {}
};
```

**逐行解读**:
- 第 112 行: 定义 Rank 准备信息结构体
- 第 113 行: `nic` - 网卡地址
- 第 114 行: `role` - 角色，默认为 PEER
- 第 115 行: `memKeys` - 内存密钥列表
- 第 116-120 行: 构造函数重载

---

## 2. hybm_transport_manager.h/cpp - 传输管理器基类

### 文件信息
- 文件路径: `src/hybm/csrc/transport/hybm_transport_manager.h` (125 行)
- 文件路径: `src/hybm/csrc/transport/hybm_transport_manager.cpp` (75 行)
- 主要功能: 定义传输管理器抽象基类和工厂方法

### 头文件解读

#### TransportManager 类定义 (行 25-117)

```cpp
class TransportManager {
public:
    static std::shared_ptr<TransportManager> Create(TransportType type, HybmEntityTagInfoPtr tagManager = nullptr);

public:
    TransportManager() = default;

    virtual ~TransportManager() = default;

    /*
     * 1、本地IP（NIC、Device）
     * @return 0 if successful
     */
    virtual Result OpenDevice(const TransportOptions &options) = 0;

    virtual Result CloseDevice() = 0;

    virtual Result ConnectWithOptions(const HybmTransPrepareOptions &options);
```

**逐行解读**:
- 第 27 行: `Create` - 工厂方法，根据类型创建传输管理器
- 第 30 行: 默认构造函数
- 第 32 行: 虚析构函数，确保正确派生类析构
- 第 38 行: `OpenDevice` - 纯虚函数，打开传输设备
- 第 40 行: `CloseDevice` - 纯虚函数，关闭传输设备
- 第 42 行: `ConnectWithOptions` - 带选项的连接（有默认实现）

```cpp
    /*
     * 2、注册内存
     * @return 0 if successful
     */
    virtual Result RegisterMemoryRegion(const TransportMemoryRegion &mr) = 0;

    virtual Result UnregisterMemoryRegion(uint64_t addr) = 0;

    virtual bool QueryHasRegistered(uint64_t addr, uint64_t size) = 0;

    virtual Result QueryMemoryKey(uint64_t addr, TransportMemoryKey &key) = 0;
```

**逐行解读**:
- 第 48 行: `RegisterMemoryRegion` - 注册内存区域，获取远程访问密钥
- 第 50 行: `UnregisterMemoryRegion` - 注销内存区域
- 第 52 行: `QueryHasRegistered` - 查询地址是否已注册
- 第 54 行: `QueryMemoryKey` - 查询内存密钥

```cpp
    /*
     * 3、建链前的准备工作
     * @return 0 if successful
     */
    virtual Result Prepare(const HybmTransPrepareOptions &options) = 0;

    /*
     * 建链完成状态，删除一部分节点
     */
    virtual Result RemoveRanks(const std::vector<uint32_t> &removedRanks) = 0;

    /*
     * 4、建链
     * @return 0 if successful
     */
    virtual Result Connect() = 0;

    /*
     * 异步建链
     * @return 0 if successful
     */
    virtual Result AsyncConnect() = 0;

    /*
     * 等待异步建链完成
     * @return 0 if successful
     */
    virtual Result WaitForConnected(int64_t timeoutNs) = 0;

    /*
     * 建链完成后，更新rank配置信息，可以新增rank或减少rank
     */
    virtual Result UpdateRankOptions(const HybmTransPrepareOptions &options) = 0;
```

**逐行解读**:
- 第 60 行: `Prepare` - 准备连接信息
- 第 65 行: `RemoveRanks` - 移除指定 Rank
- 第 71 行: `Connect` - 建立连接
- 第 77 行: `AsyncConnect` - 异步建立连接
- 第 83 行: `WaitForConnected` - 等待连接完成
- 第 88 行: `UpdateRankOptions` - 更新 Rank 配置

```cpp
    /**
     * 查询
     */
    virtual const std::string &GetNic() const = 0; // X

    virtual const void *GetQpInfo() const;

    /**
      * rdma单边传输
      */
    virtual Result ReadRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) = 0;

    virtual Result WriteRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) = 0;

    virtual Result ReadRemoteAsync(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) = 0;

    virtual Result WriteRemoteAsync(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) = 0;

    virtual Result Synchronize(uint32_t rankId) = 0;

    virtual Result Remove(const std::vector<uint32_t> &removeList);

    virtual Result WriteRemoteBatchAsync(uint32_t rankId, const CopyDescriptor &descriptor) = 0;

    virtual Result ReadRemoteBatchAsync(uint32_t rankId, const CopyDescriptor &descriptor) = 0;
protected:
    bool connected_{false};
};
```

**逐行解读**:
- 第 93 行: `GetNic` - 获取网卡信息
- 第 95 行: `GetQpInfo` - 获取 QP (Queue Pair) 信息
- 第 100 行: `ReadRemote` - 同步读取远程内存
- 第 102 行: `WriteRemote` - 同步写入远程内存
- 第 104 行: `ReadRemoteAsync` - 异步读取远程内存
- 第 106 行: `WriteRemoteAsync` - 异步写入远程内存
- 第 108 行: `Synchronize` - 同步等待完成
- 第 110 行: `Remove` - 移除 Rank（有默认实现）
- 第 112 行: `WriteRemoteBatchAsync` - 批量异步写入
- 第 114 行: `ReadRemoteBatchAsync` - 批量异步读取
- 第 116 行: `connected_` - 连接状态标志

### 实现文件解读

#### Create() 工厂方法 (行 22-39)

```cpp
std::shared_ptr<TransportManager> TransportManager::Create(TransportType type, HybmEntityTagInfoPtr tagManager)
{
    if (tagManager == nullptr) {
        BM_LOG_ERROR("Failed to create transport manager, tag manager is nullptr");
        return nullptr;
    }
    switch (type) {
        case TT_HCOM:
            return host::HcomTransportManager::GetInstance();
        case TT_HCCP:
            return std::make_shared<device::RdmaTransportManager>();
        case TT_COMPOSE:
            return std::make_shared<ComposeTransportManager>(tagManager);
        default:
            BM_LOG_ERROR("Invalid trans type: " << type);
            return nullptr;
    }
}
```

**逐行解读**:
- 第 22 行: 工厂方法实现
- 第 23-27 行: 检查 tagManager 是否为空
- 第 28 行: 根据 type 创建对应的管理器
- 第 30 行: `TT_HCOM` - 返回 HCOM 传输管理器单例
- 第 32 行: `TT_HCCP` - 创建设备 RDMA 传输管理器
- 第 34 行: `TT_COMPOSE` - 创建组合传输管理器
- 第 36-38 行: 未知类型返回错误

#### ConnectWithOptions() 实现 (行 47-68)

```cpp
Result TransportManager::ConnectWithOptions(const HybmTransPrepareOptions &options)
{
    BM_LOG_DEBUG("ConnectWithOptions now connected=" << connected_);
    if (!connected_) {
        auto ret = Prepare(options);
        if (ret != BM_OK) {
            BM_LOG_ERROR("prepare connection failed: " << ret);
            return ret;
        }

        ret = Connect();
        if (ret != BM_OK) {
            BM_LOG_ERROR("connect failed: " << ret);
            return ret;
        }

        connected_ = true;
        return BM_OK;
    }

    return UpdateRankOptions(options);
}
```

**逐行解读**:
- 第 48 行: 带选项的连接实现
- 第 50 行: 检查是否已连接
- 第 51-55 行: 未连接则先准备
- 第 57-61 行: 然后建立连接
- 第 63 行: 设置连接状态
- 第 67 行: 已连接则更新配置

---

## 3. device_rdma_transport_manager - 设备 RDMA 传输

### 文件信息
- 文件路径: `src/hybm/csrc/transport/device/device_rdma_transport_manager.h` (121 行)
- 文件路径: `src/hybm/csrc/transport/device/device_rdma_transport_manager.cpp` (969 行)
- 主要功能: 实现设备端 RDMA 传输，NPU 直接发起远程内存访问

### 头文件解读

#### RdmaTransportManager 类定义 (行 37-114)

```cpp
class RdmaTransportManager : public TransportManager {
public:
    ~RdmaTransportManager() override;

    Result OpenDevice(const TransportOptions &options) override;
    Result CloseDevice() override;
    Result RegisterMemoryRegion(const TransportMemoryRegion &mr) override;
    Result UnregisterMemoryRegion(uint64_t addr) override;
    bool QueryHasRegistered(uint64_t addr, uint64_t size) override;
    Result QueryMemoryKey(uint64_t addr, TransportMemoryKey &key) override;
    Result Prepare(const HybmTransPrepareOptions &options) override;
    Result RemoveRanks(const std::vector<uint32_t> &removedRanks) override;
    Result Connect() override;
    Result AsyncConnect() override;
    Result WaitForConnected(int64_t timeoutNs) override;
    Result UpdateRankOptions(const HybmTransPrepareOptions &options) override;
    const std::string &GetNic() const override;
    const void *GetQpInfo() const override;
    Result ReadRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) override;
    Result WriteRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) override;
    Result ReadRemoteAsync(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) override;
    Result WriteRemoteAsync(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) override;
    Result Synchronize(uint32_t rankId) override;
```

**逐行解读**:
- 第 37 行: RdmaTransportManager 继承 TransportManager
- 第 39-63 行: 重写所有传输管理器接口

```cpp
    Result ReadRemoteBatchAsync(uint32_t rankId, const CopyDescriptor &descriptor) override
    {
        BM_LOG_ERROR("ReadRemoteBatchAsync not implment.");
        return BM_INVALID_PARAM;
    }

    Result WriteRemoteBatchAsync(uint32_t rankId, const CopyDescriptor &descriptor) override
    {
        BM_LOG_ERROR("WriteRemoteBatchAsync not implment.");
        return BM_INVALID_PARAM;
    }
```

**逐行解读**:
- 第 65-69 行: 批量异步读取（未实现）
- 第 71-75 行: 批量异步写入（未实现）

```cpp
private:
    static bool PrepareOpenDevice(uint32_t userId, uint32_t device, uint32_t rankCount, in_addr &deviceIp,
                                  void *&rdmaHandle);
    static bool OpenTsd(uint32_t deviceId, uint32_t rankCount);
    static bool RaInit(uint32_t deviceId);
    static bool RetireDeviceIp(uint32_t deviceId, in_addr &deviceIp);
    static bool RaRdevInit(uint32_t deviceId, in_addr deviceIp, void *&rdmaHandle);
    void ClearAllRegisterMRs();
    int CheckPrepareOptions(const HybmTransPrepareOptions &options);
    int RemoteIO(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size, bool write, bool sync);
    int CorrectHostRegWr(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size, send_wr_v2 &wr);
    int ConvertHccpMrInfo(const TransportMemoryRegion &mr, HccpMrInfo &info);
    void OptionsToRankMRs(const HybmTransPrepareOptions &options);
    Result WaitQpReady();
    int GetRegAddress(const MemoryRegionMap &map, uint64_t inputAddr, uint64_t size, bool isLocal, uint64_t &outputAddr,
                      uint32_t &mrKey) const;
```

**逐行解读**:
- 第 71-72 行: `PrepareOpenDevice` - 准备并打开设备
- 第 73 行: `OpenTsd` - 打开 TSD (Transport Service Domain)
- 第 74 行: `RaInit` - 初始化 RDMA Agent
- 第 75 行: `RetireDeviceIp` - 获取设备 IP
- 第 76 行: `RaRdevInit` - 初始化 RDMA 设备
- 第 77 行: `ClearAllRegisterMRs` - 清除所有已注册的 MR
- 第 78 行: `CheckPrepareOptions` - 检查准备选项
- 第 79 行: `RemoteIO` - 远程 IO 操作
- 第 80 行: `CorrectHostRegWr` - 修正主机注册写请求
- 第 81 行: `ConvertHccpMrInfo` - 转换 HCCP MR 信息
- 第 82 行: `OptionsToRankMRs` - 选项转 Rank MR 列表
- 第 83 行: `WaitQpReady` - 等待 QP 就绪
- 第 84-85 行: `GetRegAddress` - 获取注册地址

```cpp
private: // RDMA HOST STARS
    void ConstructSqeNoSinkModeForRdmaDbSendTask(const send_wr_rsp &rspInfo, rtStarsSqe_t &command, HybmStreamPtr st);
    uint64_t GetRoceDbAddrForRdmaDbSendTask();
    int32_t InitStreamNotifyBuf();
    int32_t Synchronize(void *qpHandle, uint32_t rankId);

private:
    static thread_local HybmStreamNotifyPtr notify_;
    RdmaNotifyInfo notifyInfo_;
    std::mutex mutex_;
    bool started_{false};
    uint32_t rankId_{0};
    uint32_t rankCount_{1};
    uint32_t deviceId_{0};
    hybm_role_type role_{HYBM_ROLE_PEER};
    in_addr deviceIp_{0};
    uint16_t devicePort_{0};
    void *rdmaHandle_{nullptr};
    std::string nicInfo_;
    MemoryRegionMap registerMRS_;
    std::vector<MemoryRegionMap> ranksMRs_;
    std::shared_ptr<DeviceQpManager> qpManager_;
    std::vector<std::pair<uint64_t, uint32_t>> notifyRemoteInfo_;
    std::shared_ptr<DeviceChipInfo> deviceChipInfo_;
    std::atomic<uint64_t> wrIdx_{0};

    ReadWriteLock lock_;
};
```

**逐行解读**:
- 第 87-91 行: RDMA HOST STARS 相关私有方法
- 第 93 行: `notify_` - 线程本地通知对象
- 第 94 行: `notifyInfo_` - 通知信息
- 第 95 行: `mutex_` - 互斥锁
- 第 96 行: `started_` - 启动标志
- 第 97 行: `rankId_` - 当前 Rank ID
- 第 98 行: `rankCount_` - Rank 总数
- 第 99 行: `deviceId_` - 设备 ID
- 第 100 行: `role_` - 角色
- 第 101 行: `deviceIp_` - 设备 IP
- 第 102 行: `devicePort_` - 设备端口
- 第 103 行: `rdmaHandle_` - RDMA 句柄
- 第 104 行: `nicInfo_` - 网卡信息字符串
- 第 105 行: `registerMRS_` - 本地已注册的 MR
- 第 106 行: `ranksMRs_` - 各 Rank 的 MR
- 第 107 行: `qpManager_` - QP 管理器
- 第 108 行: `notifyRemoteInfo_` - 远程通知信息
- 第 109 行: `deviceChipInfo_` - 设备芯片信息
- 第 110 行: `wrIdx_` - 工作请求索引原子计数器
- 第 113 行: `lock_` - 读写锁

### 实现文件关键方法解读

#### OpenDevice() - 打开设备 (行 58-115)

```cpp
Result RdmaTransportManager::OpenDevice(const TransportOptions &options)
{
    int32_t userId = -1;
    int32_t logicId = -1;
    std::unique_lock<std::mutex> unique_lock(mutex_);
    BM_LOG_DEBUG("begin to open device with " << options);
    auto ret = DlAclApi::AclrtGetDevice(&userId);
    BM_ASSERT_LOG_AND_RETURN(ret == 0 && userId >= 0,
                             "AclrtGetDevice() return=" << ret << ", output deviceId=" << userId,
                             BM_DL_FUNCTION_FAILED);

    ret = DlAclApi::RtGetLogicDevIdByUserDevId(userId, &logicId);
    BM_ASSERT_LOG_AND_RETURN(ret == 0 && logicId >= 0,
                             "RtGetLogicDevIdByUserDevId() return=" << ret << ", output deviceId=" << logicId,
                             BM_DL_FUNCTION_FAILED);

    deviceId_ = static_cast<uint32_t>(logicId);
    rankId_ = options.rankId;
    rankCount_ = options.rankCount;
    role_ = options.role;
```

**逐行解读**:
- 第 58-60 行: 定义局部变量
- 第 61 行: 加锁
- 第 62 行: 打印调试日志
- 第 64-67 行: 获取用户设备 ID
- 第 69-72 行: 获取逻辑设备 ID
- 第 74-77 行: 设置成员变量

```cpp
    ret = ParseDeviceNic(options.nic, devicePort_);
    BM_ASSERT_LOG_AND_RETURN(ret == BM_OK, "parse input nic(" << options.nic << ") failed!", BM_INVALID_PARAM);

    if (!PrepareOpenDevice(userId, deviceId_, rankCount_, deviceIp_, rdmaHandle_)) {
        BM_LOG_ERROR("PrepareOpenDevice failed.");
        return BM_ERROR;
    }

    nicInfo_ = GenerateDeviceNic(deviceIp_, devicePort_);
    BM_ASSERT_LOG_AND_RETURN(
        !nicInfo_.empty(),
        "GenerateDeviceNic failed, deviceIp=" << DescribeIPv4(deviceIp_) << ", devicePort=" << devicePort_, BM_ERROR);
```

**逐行解读**:
- 第 78-79 行: 解析网卡配置
- 第 81-84 行: 准备并打开设备
- 第 86-89 行: 生成网卡信息字符串

```cpp
    sockaddr_in deviceAddr{};
    deviceAddr.sin_family = AF_INET;
    deviceAddr.sin_addr = deviceIp_;
    deviceAddr.sin_port = devicePort_;
    if (role_ == HYBM_ROLE_PEER) {
        if (options.initialType == HYBM_TYPE_AI_CORE_INITIATE) {
            qpManager_ = std::make_shared<FixedRanksQpManager>(userId, rankId_, rankCount_, deviceAddr);
        } else {
            qpManager_ = std::make_shared<JoinableRanksQpManager>(userId, deviceId_, rankId_, rankCount_, deviceAddr);
        }
    } else {
        qpManager_ = std::make_shared<BipartiteRanksQpManager>(userId, deviceId_, rankId_, rankCount_, deviceAddr,
                                                               role_ == HYBM_ROLE_RECEIVER);
    }
```

**逐行解读**:
- 第 91-94 行: 构建设备地址结构体
- 第 95-104 行: 根据角色创建对应的 QP 管理器
  - `HYBM_ROLE_PEER` + `HYBM_TYPE_AI_CORE_INITIATE` -> FixedRanksQpManager
  - `HYBM_ROLE_PEER` + 其他 -> JoinableRanksQpManager
  - SENDER/RECEIVER -> BipartiteRanksQpManager

```cpp
    deviceChipInfo_ = std::make_shared<DeviceChipInfo>(userId);
    ret = deviceChipInfo_->Init();
    BM_ASSERT_LOG_AND_RETURN(ret == BM_OK, "device info init failed: " << ret, ret);

    ret = InitStreamNotifyBuf();
    BM_ASSERT_LOG_AND_RETURN(ret == BM_OK, "notify init failed: " << ret, ret);
    ranksMRs_.resize(rankCount_);
    BM_LOG_INFO("open device with " << options << " success.");
    return BM_OK;
}
```

**逐行解读**:
- 第 106-108 行: 创建并初始化芯片信息
- 第 110-111 行: 初始化流通知缓冲区
- 第 112 行: 调整 ranksMRs_ 大小
- 第 113-114 行: 打印成功日志并返回

#### RegisterMemoryRegion() - 注册内存区域 (行 133-164)

```cpp
Result RdmaTransportManager::RegisterMemoryRegion(const TransportMemoryRegion &mr)
{
    void *mrHandle = nullptr;
    HccpMrInfo info{};

    auto ret = ConvertHccpMrInfo(mr, info);
    if (ret != BM_OK) {
        return ret;
    }

    ret = DlHccpApi::RaRegisterMR(rdmaHandle_, &info, mrHandle);
    if (ret != 0) {
        BM_LOG_ERROR("register MR=" << mr << " failed: " << ret);
        return BM_DL_FUNCTION_FAILED;
    }

    RegMemResult result{mr.addr, (uint64_t)(ptrdiff_t)info.addr, mr.size, mrHandle, info.lkey, info.rkey};
    BM_LOG_DEBUG("register MR result=" << result);
```

**逐行解读**:
- 第 133-134 行: 定义局部变量
- 第 136-139 行: 转换 MR 信息
- 第 143-147 行: 调用 HCCP API 注册 MR
- 第 149-150 行: 构造注册结果

```cpp
    if ((mr.flags & REG_MR_FLAG_SELF) == 0) {
        auto type = (mr.flags & REG_MR_FLAG_DRAM) ? HYBM_MEM_TYPE_HOST : HYBM_MEM_TYPE_DEVICE;
        ret = HybmVaManager::GetInstance().AddVaInfoFromExternal({result.regAddress, mr.size, type, mr.addr}, rankId_);
        if (ret != BM_OK) {
            BM_LOG_ERROR("Add va info failed, ret: " << ret << ", gva: " << result.regAddress);
            DlHccpApi::RaDeregisterMR(rdmaHandle_, mrHandle);
            return ret;
        }
    }

    WriteGuard lockGuard(lock_);
    registerMRS_.emplace(mr.addr, result);
    return BM_OK;
}
```

**逐行解读**:
- 第 151 行: 检查是否需要添加到 VA 管理器
- 第 152 行: 确定内存类型
- 第 153-159 行: 添加 VA 信息，失败时注销 MR
- 第 161 行: 写锁保护
- 第 162 行: 保存注册结果
- 第 163 行: 返回成功

#### RemoteIO() - 远程 IO 操作 (行 665-726)

```cpp
int RdmaTransportManager::RemoteIO(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size, bool write,
                                   bool sync)
{
    if (qpManager_ == nullptr) {
        BM_LOG_ERROR("ReadRemote(): connection manager not created.");
        return BM_ERROR;
    }
    auto qp = qpManager_->GetQpHandleWithRankId(rankId);
    if (qp == nullptr) {
        BM_LOG_ERROR("no qp to rankId: " << rankId);
        return BM_ERROR;
    }

    auto hStream = HybmStreamManager::GetThreadHybmStream(HybmGetInitedLogicDeviceId());
    BM_ASSERT_RETURN(hStream != nullptr, BM_ERROR);

    struct send_wr_v2 wr = {};
    struct sg_list sgList = {.addr = lAddr, .len = (uint32_t)size, .lkey = 0};
    wr.buf_list = &sgList;
    wr.buf_num = 1;
    wr.dst_addr = rAddr;
    wr.op = write ? 0 : 4; /* RDMA_WRITE: 0  RDMA_READ: 4 */
    wr.send_flag = RA_SEND_SIGNALED;
    wr.wr_id = wrIdx_.fetch_add(1U);
```

**逐行解读**:
- 第 665-666 行: 函数参数（rankId、本地地址、远程地址、大小、是否写、是否同步）
- 第 668-671 行: 检查 QP 管理器
- 第 672-676 行: 获取 QP 句柄
- 第 678-679 行: 获取线程本地流
- 第 681-688 行: 构造 RDMA 工作请求
  - `wr.op = 0` 为 RDMA_WRITE
  - `wr.op = 4` 为 RDMA_READ

```cpp
    auto ret = CorrectHostRegWr(rankId, lAddr, rAddr, size, wr);
    if (ret != BM_OK) {
        BM_LOG_ERROR("CorrectHostRegWr failed : " << ret);
        qpManager_->PutQpHandle(qp);
        return ret;
    }

    send_wr_rsp rspInfo{};
    TP_TRACE_BEGIN(TP_HYBM_DEV_SEND_WR);
    ret = DlHccpApi::RaSendWrV2(qp->qpHandle, &wr, &rspInfo);
    TP_TRACE_END(TP_HYBM_DEV_SEND_WR, ret);
    if (ret != 0) {
        BM_LOG_ERROR("DlHccpApi::RaSendWr(handle, &wr, &opRsp) failed: " << ret);
        qpManager_->PutQpHandle(qp);
        return ret;
    }

    StreamTask task;
    task.type = STREAM_TASK_TYPE_RDMA;
    ConstructSqeNoSinkModeForRdmaDbSendTask(rspInfo, task.sqe, hStream);
    TP_TRACE_BEGIN(TP_HYBM_DEV_SUBMIT_TASK);
    ret = hStream->SubmitTasks(task);
    TP_TRACE_END(TP_HYBM_DEV_SUBMIT_TASK, ret);
```

**逐行解读**:
- 第 689-694 行: 修正主机注册写请求
- 第 696 行: 准备响应信息结构体
- 第 698-704 行: 发送工作请求
- 第 706-708 行: 准备流任务
- 第 709-711 行: 构造 SQE（提交队列入口）
- 第 712-716 行: 提交任务到流

```cpp
    if (ret != BM_OK) {
        BM_LOG_ERROR("SubmitTasks(task) failed: " << ret);
        qpManager_->PutQpHandle(qp);
        return ret;
    }

    if (sync) {
        ret = Synchronize(qp->qpHandle, rankId);
        if (ret != BM_OK) {
            BM_LOG_ERROR("Synchronize failed: " << ret);
        }
    }
    qpManager_->PutQpHandle(qp);
    return ret;
}
```

**逐行解读**:
- 第 717-721 行: 检查提交结果
- 第 723-727 行: 同步等待完成
- 第 724 行: 归还 QP 句柄
- 第 725 行: 返回结果

---

## 4. host_hcom_transport_manager - 主机 HCOM 传输

### 文件信息
- 文件路径: `src/hybm/csrc/transport/host/host_hcom_transport_manager.h` (151 行)
- 文件路径: `src/hybm/csrc/transport/host/host_hcom_transport_manager.cpp` (1068 行)
- 主要功能: 实现主机端 HCOM 通信，支持 TCP/RoCE/UB 协议

### 头文件解读

#### HcomTransportManager 类定义 (行 36-145)

```cpp
class HcomTransportManager : public TransportManager {
public:
    static std::shared_ptr<HcomTransportManager> GetInstance()
    {
        static auto instance = std::make_shared<HcomTransportManager>();
        return instance;
    }

    Result OpenDevice(const TransportOptions &options) override;
    Result CloseDevice() override;
    Result RegisterMemoryRegion(const TransportMemoryRegion &mr) override;
    Result UnregisterMemoryRegion(uint64_t addr) override;
    bool QueryHasRegistered(uint64_t addr, uint64_t size) override;
    Result QueryMemoryKey(uint64_t addr, TransportMemoryKey &key) override;
    Result Prepare(const HybmTransPrepareOptions &parma) override;
    Result RemoveRanks(const std::vector<uint32_t> &removedRanks) override;
    Result Connect() override;
    Result AsyncConnect() override;
    Result WaitForConnected(int64_t timeoutNs) override;
    Result UpdateRankOptions(const HybmTransPrepareOptions &param) override;
    const std::string &GetNic() const override;
```

**逐行解读**:
- 第 37-42 行: 单例模式获取实例
- 第 44-67 行: 重写传输管理器接口

```cpp
    Result ReadRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) override;

    Result ReadRemoteBatchAsync(uint32_t rankId, const CopyDescriptor &descriptor) override;

    Result WriteRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) override;

    Result WriteRemoteBatchAsync(uint32_t rankId, const CopyDescriptor &descriptor) override;

    Result ReadRemoteAsync(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) override;

    Result WriteRemoteAsync(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size) override;

    Result Synchronize(uint32_t rankId) override;
```

**逐行解读**:
- 第 70-82 行: 远程内存访问接口

```cpp
private:
    Result InnerReadRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size);

    Result InnerWriteRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size);

    Result CheckTransportOptions(const TransportOptions &options);

    static Result TransportRpcHcomNewEndPoint(Hcom_Channel newCh, uint64_t usrCtx, const char *payLoad);

    static Result TransportRpcHcomEndPointBroken(Hcom_Channel ch, uint64_t usrCtx, const char *payLoad);

    static Result TransportRpcHcomRequestReceived(Service_Context ctx, uint64_t usrCtx);

    static Result TransportRpcHcomRequestPosted(Service_Context ctx, uint64_t usrCtx);

    static Result TransportRpcHcomOneSideDone(Service_Context ctx, uint64_t usrCtx);

    Result ConnectHcomChannel(uint32_t rankId, const std::string &url);

    void DisConnectHcomChannel(uint32_t rankId, Hcom_Channel ch);

    void HcomChannelDisconnected(uint32_t rankId, Hcom_Channel ch);

    void ForceReConnectHcomChannel(uint32_t rankId);

    Result GetMemoryRegionByAddr(const uint32_t &rankId, const uint64_t &addr, HcomMemoryRegion &mr);

    Result UpdateRankMrInfos(const std::unordered_map<uint32_t, TransportRankPrepareInfo> &opt);

    Result UpdateRankConnectInfos(const std::unordered_map<uint32_t, TransportRankPrepareInfo> &options);

    static int GetCACallBack(const char *name, char **caPath, char **crlPath, Hcom_PeerCertVerifyType *verifyType,
                             Hcom_TlsCertVerify *verify);

    static int GetCertCallBack(const char *name, char **certPath);

    static int GetPrivateKeyCallBack(const char *name, char **priKeyPath, char **keyPass, Hcom_TlsKeyPassErase *erase);

    static int CertVerifyCallBack(void *x509, const char *crlPath);

    static void KeyPassEraseCallBack(char *keyPass, int len);

    int PrepareThreadLocalStream();
```

**逐行解读**:
- 第 84-85 行: `InnerReadRemote` - 内部读取实现
- 第 87-88 行: `InnerWriteRemote` - 内部写入实现
- 第 90 行: `CheckTransportOptions` - 检查传输选项
- 第 92-102 行: HCOM 回调函数
  - `TransportRpcHcomNewEndPoint` - 新端点回调
  - `TransportRpcHcomEndPointBroken` - 端点断开回调
  - `TransportRpcHcomRequestReceived` - 请求接收回调
  - `TransportRpcHcomRequestPosted` - 请求发送回调
  - `TransportRpcHcomOneSideDone` - 单边操作完成回调
- 第 104-109 行: 通道管理方法
- 第 111 行: `ForceReConnectHcomChannel` - 强制重连
- 第 113 行: `GetMemoryRegionByAddr` - 根据地址获取 MR
- 第 115-116 行: 更新 Rank 信息方法
- 第 118-125 行: TLS 相关回调函数
- 第 126 行: `PrepareThreadLocalStream` - 准备线程本地流

```cpp
private:
    hybm_data_op_type bmOptype_{};
    ReadWriteLock lock_;
    static thread_local HcomCounterStreamPtr stream_;
    std::string localNic_{};
    std::string localIp_{};
    Hcom_Service rpcService_{0};
    uint32_t rankId_{UINT32_MAX};
    uint32_t rankCount_{0};
    std::vector<std::mutex> mrMutex_;
    std::vector<std::vector<HcomMemoryRegion>> mrs_;
    std::vector<std::mutex> channelMutex_;
    std::vector<std::string> nics_;
    std::vector<Hcom_Channel> channels_;
    static hybm_tls_config tlsConfig_;
    static char keyPass_[KEYPASS_MAX_LEN];
    static std::mutex keyPassMutex;
};
```

**逐行解读**:
- 第 129 行: `bmOptype_` - 数据操作类型
- 第 130 行: `lock_` - 读写锁
- 第 131 行: `stream_` - 线程本地计数器流
- 第 132-133 行: 本地网卡和 IP
- 第 134 行: `rpcService_` - HCOM 服务句柄
- 第 135-136 行: Rank ID 和数量
- 第 137-141 行: MR 和通道相关成员
- 第 142-144 行: TLS 配置静态成员

### 实现文件关键方法解读

#### OpenDevice() - 打开设备 (行 81-129)

```cpp
Result HcomTransportManager::OpenDevice(const TransportOptions &options)
{
    BM_ASSERT_RETURN(rpcService_ == 0, BM_OK);
    BM_ASSERT_RETURN(CheckTransportOptions(options) == BM_OK, BM_INVALID_PARAM);
    Service_Options opt{};
    opt.workerGroupMode = C_SERVICE_BUSY_POLLING;
    opt.maxSendRecvDataSize = HCOM_RECV_DATA_SIZE;
    opt.workerThreadPriority = HCOM_THREAD_PRIORITY;
    Service_Type enumProtocolType = HostHcomHelper::HybmDopTransHcomProtocol(options.protocol, options.nic);
    int ret = DlHcomApi::ServiceCreate(enumProtocolType, HCOM_RPC_SERVICE_NAME, opt, &rpcService_);
    if (ret != 0) {
        BM_LOG_ERROR("Failed to create hcom service, nic: " << options.nic << " type: " << enumProtocolType
                                                            << " ret: " << ret);
        return BM_DL_FUNCTION_FAILED;
    }
```

**逐行解读**:
- 第 81-82 行: 检查服务是否已创建
- 第 83 行: 检查传输选项
- 第 84-87 行: 设置服务选项
  - `workerGroupMode` - 工作线程模式为忙轮询
  - `maxSendRecvDataSize` - 最大收发数据大小
  - `workerThreadPriority` - 工作线程优先级
- 第 88 行: 获取协议类型
- 第 89-95 行: 创建 HCOM 服务

```cpp
    BM_LOG_INFO("Create hcom service successful, nic: " << options.nic << " type: " << enumProtocolType);
    tlsConfig_ = options.tlsOption;
    DlHcomApi::ServiceSetTlsOptions(rpcService_, options.tlsOption.tlsEnable, C_SERVICE_TLS_1_3, C_SERVICE_AES_GCM_256,
                                    GetCertCallBack, GetPrivateKeyCallBack, GetCACallBack);
    DlHcomApi::SetUbsModeFunc(rpcService_, UbsHcomServiceUbcMode::C_SERVICE_HIGHBANDWIDTH);
    DlHcomApi::ServiceRegisterChannelBrokerHandler(rpcService_, TransportRpcHcomEndPointBroken, C_CHANNEL_RECONNECT, 1);
    DlHcomApi::ServiceRegisterHandler(rpcService_, C_SERVICE_REQUEST_RECEIVED, TransportRpcHcomRequestReceived, 1);
    DlHcomApi::ServiceRegisterHandler(rpcService_, C_SERVICE_REQUEST_POSTED, TransportRpcHcomRequestPosted, 1);
    DlHcomApi::ServiceRegisterHandler(rpcService_, C_SERVICE_READWRITE_DONE, TransportRpcHcomOneSideDone, 1);
```

**逐行解读**:
- 第 97 行: 打印成功日志
- 第 98 行: 保存 TLS 配置
- 第 99-100 行: 设置 TLS 选项（TLS 1.3, AES-GCM-256）
- 第 101 行: 设置 UBS 模式为高带宽
- 第 102 行: 注册通道断线重连处理器
- 第 103 行: 注册请求接收处理器
- 第 104 行: 注册请求发送处理器
- 第 105 行: 注册读写完成处理器

```cpp
    if (enumProtocolType != Service_Type::C_SERVICE_UBC) {
        std::string ipMask = localIp_ + "/32";
        DlHcomApi::ServiceSetDeviceIpMask(rpcService_, ipMask.c_str());
    }

    DlHcomApi::ServiceBind(rpcService_, localNic_.c_str(), TransportRpcHcomNewEndPoint);
    ret = DlHcomApi::ServiceStart(rpcService_);
    if (ret != 0) {
        BM_LOG_ERROR("Failed to start hcom service, nic: " << localNic_ << " type: " << enumProtocolType
                                                           << " ret: " << ret);
        DlHcomApi::ServiceDestroy(rpcService_, HCOM_RPC_SERVICE_NAME);
        rpcService_ = 0;
        return BM_DL_FUNCTION_FAILED;
    }
```

**逐行解读**:
- 第 107-109 行: 非 UBC 协议时设置 IP 掩码
- 第 111 行: 绑定网卡并注册新端点回调
- 第 112 行: 启动服务
- 第 113-119 行: 启动失败时清理资源

```cpp
    bmOptype_ = static_cast<hybm_data_op_type>(options.protocol);
    rankId_ = options.rankId;
    rankCount_ = options.rankCount;
    mrMutex_ = std::vector<std::mutex>(rankCount_);
    mrs_ = std::vector<std::vector<HcomMemoryRegion>>(rankCount_);
    channelMutex_ = std::vector<std::mutex>(rankCount_);
    nics_ = std::vector<std::string>(rankCount_, "");
    channels_ = std::vector<Hcom_Channel>(rankCount_, 0);
    return BM_OK;
}
```

**逐行解读**:
- 第 120-123 行: 保存基本配置
- 第 124-127 行: 初始化向量成员
- 第 128 行: 返回成功

#### ReadRemote() - 远程读取 (带重试) (行 261-280)

```cpp
Result HcomTransportManager::ReadRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size)
{
    constexpr uint32_t kMaxRetries = 3u;
    for (uint32_t attempt = 0; attempt < kMaxRetries; ++attempt) {
        Result ret = InnerReadRemote(rankId, lAddr, rAddr, size);
        if (ret == BM_OK) {
            return BM_OK;
        }
        BM_LOG_ERROR("Failed to ReadRemote, ret: " << ret << ", attempt: " << attempt << ", rank: " << rankId);
        if (ret > 0 || channels_[rankId] == 0) {
            ForceReConnectHcomChannel(rankId);
        }
        if (attempt < kMaxRetries - 1) {
            std::this_thread::sleep_for(std::chrono::seconds(attempt + 1));
        }
    }
    return BM_ERROR;
}
```

**逐行解读**:
- 第 261 行: 函数签名
- 第 262 行: 最大重试次数为 3
- 第 263 行: 重试循环
- 第 264-267 行: 调用内部读取，成功则返回
- 第 268-270 行: 打印错误日志
- 第 271-273 行: 失败时强制重连
- 第 274-276 行: 退避延迟（第1次不等，第2次等1s，第3次等2s）
- 第 278 行: 返回错误

---

## 5. compose_transport_manager - 组合传输管理器

### 文件信息
- 文件路径: `src/hybm/csrc/transport/compose/compose_transport_manager.h` (98 行)
- 文件路径: `src/hybm/csrc/transport/compose/compose_transport_manager.cpp` (543 行)
- 主要功能: 组合管理设备 RDMA 和主机 HCOM 传输

### 头文件解读

#### ComposeMemoryRegion 结构体 (行 25-33)

```cpp
struct ComposeMemoryRegion {
    uint64_t addr = 0;
    uint64_t size = 0;
    TransportType type = TT_BUTT;

    ComposeMemoryRegion(const uint64_t addr, const uint64_t size, TransportType type)
        : addr{addr}, size{size}, type{type}
    {}
};
```

**逐行解读**:
- 第 25 行: 定义组合内存区域结构体
- 第 26 行: `addr` - 内存地址
- 第 27 行: `size` - 内存大小
- 第 28 行: `type` - 传输类型
- 第 30-32 行: 构造函数

#### ComposeTransportManager 类定义 (行 35-94)

```cpp
class ComposeTransportManager : public TransportManager {
public:
    explicit ComposeTransportManager(HybmEntityTagInfoPtr tag) noexcept : tagManager_{std::move(tag)}{};

    // ... 所有接口重写

private:
    Result OpenHostTransport(const TransportOptions &options);
    Result OpenDeviceTransport(const TransportOptions &options);
    void GetHostPrepareOptions(const HybmTransPrepareOptions &param, HybmTransPrepareOptions &hostOptions);
    void GetDevicePrepareOptions(const HybmTransPrepareOptions &param, HybmTransPrepareOptions &DeviceOptions);

private:
    std::shared_ptr<TransportManager> deviceTransportManager_{nullptr};
    std::shared_ptr<TransportManager> hostTransportManager_{nullptr};

    std::string nicInfo_;
    std::mutex mrsMutex_;
    std::map<uint64_t, ComposeMemoryRegion, std::greater<uint64_t>> mrs_;
    TransportOptions options_{};
    HybmEntityTagInfoPtr tagManager_{};
};
```

**逐行解读**:
- 第 37 行: 构造函数接收 tagManager
- 第 86-87 行: `deviceTransportManager_` - 设备传输管理器
- 第 88 行: `hostTransportManager_` - 主机传输管理器
- 第 89 行: `nicInfo_` - 网卡信息
- 第 90 行: `mrsMutex_` - MR 互斥锁
- 第 91 行: `mrs_` - 组合 MR 映射
- 第 92 行: `options_` - 传输选项
- 第 93 行: `tagManager_` - 标签管理器

### 实现文件关键方法解读

#### ReadRemote() - 组合远程读取 (行 365-387)

```cpp
Result ComposeTransportManager::ReadRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size)
{
    uint32_t opType = tagManager_->GetRank2RankOpType(rankId, options_.rankId);
    // 传输顺序 device_rdma -> host_rdma
    if ((opType & HYBM_DOP_TYPE_DEVICE_RDMA) && deviceTransportManager_ != nullptr) {
        auto ret = deviceTransportManager_->ReadRemote(rankId, lAddr, rAddr, size);
        if (ret == BM_OK) {
            return BM_OK;
        }
        BM_LOG_ERROR("Failed to ReadRemote by device transport ret:" << ret);
    }

    if (opType & HOST_PROTOCOL) {
        auto ret = hostTransportManager_->ReadRemote(rankId, lAddr, rAddr, size);
        if (ret == BM_OK) {
            return BM_OK;
        }
        BM_LOG_ERROR("Failed to ReadRemote by host transport ret:" << ret);
    }

    BM_LOG_ERROR("Failed to ReadRemote.");
    return BM_ERROR;
}
```

**逐行解读**:
- 第 365-366 行: 获取 Rank 间传输类型
- 第 369 行: 优先使用设备 RDMA
- 第 370-374 行: 设备传输成功则返回
- 第 377-382 行: 设备传输失败则使用主机传输
- 第 385-386 行: 全部失败返回错误

#### WriteRemote() - 组合远程写入 (行 389-409)

```cpp
Result ComposeTransportManager::WriteRemote(uint32_t rankId, uint64_t lAddr, uint64_t rAddr, uint64_t size)
{
    uint32_t opType = tagManager_->GetRank2RankOpType(rankId, options_.rankId);
    if ((opType & HYBM_DOP_TYPE_DEVICE_RDMA) && deviceTransportManager_ != nullptr) {
        auto ret = deviceTransportManager_->WriteRemote(rankId, lAddr, rAddr, size);
        if (ret == BM_OK) {
            return BM_OK;
        }
        BM_LOG_ERROR("Failed to WriteRemote by device transport ret:" << ret);
    }

    if (opType & HOST_PROTOCOL) {
        auto ret = hostTransportManager_->WriteRemote(rankId, lAddr, rAddr, size);
        if (ret == BM_OK) {
            return BM_OK;
        }
        BM_LOG_ERROR("Failed to WriteRemote by host transport ret:" << ret);
    }
    BM_LOG_ERROR("Failed to WriteRemote.");
    return BM_ERROR;
}
```

**逐行解读**:
- 与 ReadRemote 类似，优先使用设备 RDMA，失败则降级到主机传输

---

## 6. device_rdma_common.h - 设备 RDMA 公共定义

### 文件信息
- 文件路径: `src/hybm/csrc/transport/device/device_rdma_common.h` (247 行)
- 主要功能: 设备 RDMA 传输使用的公共数据结构

### 关键结构体

#### RegMemResult (行 36-57)

```cpp
struct RegMemResult {
    uint64_t address;
    uint64_t size;
    uint64_t regAddress;
    void *mrHandle;
    uint32_t lkey;
    uint32_t rkey;

    uint32_t type;
    uint32_t notifyRkey = 0;
    uint64_t notifyAddr = 0;

    RegMemResult() : RegMemResult{0, 0, nullptr, 0, 0} {}

    RegMemResult(uint64_t addr, uint64_t sz, void *hd, uint32_t lk, uint32_t rk)
        : type{TT_HCCP}, address(addr), size(sz), regAddress{addr}, mrHandle(hd), lkey(lk), rkey(rk)
    {}

    RegMemResult(uint64_t addr, uint64_t regAddr, uint64_t sz, void *hd, uint32_t lk, uint32_t rk)
        : type{TT_HCCP}, address(addr), size(sz), regAddress{regAddr}, mrHandle(hd), lkey(lk), rkey(rk)
    {}
};
```

**逐行解读**:
- 第 36 行: 注册内存结果结构体
- 第 37 行: `address` - 原始地址
- 第 38 行: `size` - 大小
- 第 39 行: `regAddress` - 注册后地址（可能不同）
- 第 40 行: `mrHandle` - MR 句柄
- 第 41 行: `lkey` - 本地密钥
- 第 42 行: `rkey` - 远程密钥
- 第 44-46 行: 通知相关字段
- 第 48-56 行: 构造函数重载

#### ConnectRankInfo (行 66-85)

```cpp
struct ConnectRankInfo {
    hybm_role_type role;
    sockaddr_in network;
    MemoryRegionMap memoryMap;

    ConnectRankInfo(hybm_role_type r, sockaddr_in nw, const TransportMemoryKey &mk) : role{r}, network{std::move(nw)}
    {
        auto &deviceKey = container_of(&mk, RegMemKeyUnion, commonKey)->deviceKey;
        memoryMap.emplace(deviceKey.address, deviceKey);
    }

    ConnectRankInfo(hybm_role_type r, sockaddr_in nw, const std::vector<TransportMemoryKey> &mks)
        : role{r}, network{std::move(nw)}
    {
        for (auto &mk : mks) {
            auto &deviceKey = container_of(&mk, RegMemKeyUnion, commonKey)->deviceKey;
            memoryMap.emplace(deviceKey.address, deviceKey);
        }
    }
};
```

**逐行解读**:
- 第 66 行: Rank 连接信息结构体
- 第 67 行: `role` - 角色
- 第 68 行: `network` - 网络地址
- 第 69 行: `memoryMap` - 内存映射

#### RdmaNotifyInfo (行 234-240)

```cpp
struct RdmaNotifyInfo {
    uint64_t srcAddr;
    uint64_t notifyAddr;
    uint32_t len;
    uint32_t srcRkey;
    uint32_t notifyLkey;
};
```

**逐行解读**:
- 第 234 行: RDMA 通知信息结构体
- 第 235 行: `srcAddr` - 源地址
- 第 236 行: `notifyAddr` - 通知地址
- 第 237 行: `len` - 通知长度
- 第 238 行: `srcRkey` - 源远程密钥
- 第 239 行: `notifyLkey` - 通知本地密钥

---

## 总结

Transport 模块实现了完整的跨节点内存传输功能：

### 1. 传输类型

| 传输类型 | 说明 | 支持协议 |
|---------|------|---------|
| TT_HCOM | 主机端通信 | TCP, RoCE, UB |
| TT_HCCP | 设备端 RDMA | NPU 直接 RDMA |
| TT_COMPOSE | 组合传输 | 同时管理 HCOM + HCCP |

### 2. 关键设计

**工厂模式**: `TransportManager::Create()` 根据类型创建对应管理器

**策略模式**: 不同 QP 管理器实现不同拓扑
- `BipartiteRanksQpManager` - 二分图拓扑
- `FixedRanksQpManager` - 固定连接
- `JoinableRanksQpManager` - 可动态加入

**组合模式**: ComposeTransportManager 同时管理设备和主机传输

**单例模式**: HcomTransportManager 使用单例

### 3. 传输流程

1. **初始化**: `OpenDevice()` - 打开传输设备
2. **内存注册**: `RegisterMemoryRegion()` - 注册内存获取密钥
3. **准备连接**: `Prepare()` - 交换 Rank 信息
4. **建立连接**: `Connect()` - 建立 QP 连接
5. **数据传输**: `ReadRemote()/WriteRemote()` - RDMA 操作
6. **同步等待**: `Synchronize()` - 等待完成

### 4. 特性支持

- **重试机制**: HCOM 传输支持自动重试和重连
- **分块传输**: 大数据自动分块，避免单次传输过大
- **批量操作**: 支持散列读/写优化
- **TLS 安全**: 支持 TLS 1.3 加密
- **降级策略**: Compose 传输支持设备失败时降级到主机传输
