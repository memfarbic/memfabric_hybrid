# smem/net 模块逐行解读

## 模块概述

smem/net 模块实现了组通信功能，提供 Barrier（屏障同步）和 AllGather（全收集）等集合通信原语。该模块基于配置存储（ConfigStore）实现分布式节点间的协调。

### 文件清单

| 文件路径 | 代码行数 | 功能描述 |
|---------|---------|---------|
| [smem_net_common.h](../../src/smem/csrc/net/smem_net_common.h) | 31 行 | 网络公共定义和工具 |
| [smem_net_common.cpp](../../src/smem/csrc/net/smem_net_common.cpp) | 186 行 | IP地址提取和本地IP获取 |
| [smem_net_group_engine.h](../../src/smem/csrc/net/smem_net_group_engine.h) | 167 行 | 组引擎类定义 |
| [smem_net_group_engine.cpp](../../src/smem/csrc/net/smem_net_group_engine.cpp) | 1,109 行 | 组引擎实现 |

### 核心概念

1. **Group（组）**: 一组协同工作的进程，每个进程有一个 rank ID
2. **Barrier（屏障）**: 所有 rank 必须到达屏障点后才能继续执行
3. **AllGather（全收集）**: 每个 rank 发送数据给所有 rank，收集所有 rank 的数据
4. **Dynamic Group（动态组）**: 支持运行时 rank 加入和退出

---

## 一、smem_net_common.h 逐行解读

### 文件信息
- 文件路径: `src/smem/csrc/net/smem_net_common.h`
- 代码行数: 31 行
- 主要功能: 定义 URL 提取结构和本地 IP 获取函数

### 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * MemFabric_Hybrid is licensed under Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *          http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
 * EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
 * MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
 * See the Mulan PSL v2 for more details.
*/

#ifndef MEM_FABRIC_HYBRID_SMEM_NET_COMMON_H
#define MEM_FABRIC_HYBRID_SMEM_NET_COMMON_H

#include "smem_common_includes.h"

namespace ock {
namespace smem {

struct UrlExtraction {
    std::string ip;        /* ip */
    uint16_t port = 9980L; /* listen port */

    Result ExtractIpPortFromUrl(const std::string &url);
};

Result GetLocalIpWithTarget(const std::string &target, std::string &local);
} // namespace smem
} // namespace ock
#endif // MEM_FABRIC_HYBRID_SMEM_NET_COMMON_H
```

### 逐行解读

**第 1-11 行**: 版权和许可证声明
- 第 1-2 行: 版权所有，华为技术有限公司 2025 年
- 第 3-4 行: 采用 Mulan PSL v2 许可证
- 第 5-6 行: 可在指定网址获取许可证副本
- 第 7-10 行: 软件按"原样"提供，不提供任何形式的担保

**第 13-14 行**: 头文件保护宏开始
- 第 13 行: 定义 `MEM_FABRIC_HYBRID_SMEM_NET_COMMON_H` 宏，防止头文件重复包含

**第 15 行**: 引入公共头文件
- `#include "smem_common_includes.h"` - 引入 smem 模块的公共头文件集合，包含基础类型和工具定义

**第 18-19 行**: 命名空间开始
- `namespace ock` - 外层命名空间 ock（可能代表某个公司或项目名）
- `namespace smem` - 内层命名空间 smem（semantic memory）

**第 21-27 行**: `UrlExtraction` 结构体定义
- 第 21 行: 定义结构体 `UrlExtraction`，用于从 URL 中提取 IP 和端口
- 第 22 行: 成员变量 `ip`，`std::string` 类型，存储提取出的 IP 地址
- 第 23 行: 成员变量 `port`，`uint16_t` 类型，默认值为 9980，存储端口号
- 第 24 行: 空行，分隔变量和函数声明
- 第 25 行: 声明成员函数 `ExtractIpPortFromUrl`，接收 URL 字符串，返回 `Result` 类型（结果码）

**第 29 行**: 声明全局函数 `GetLocalIpWithTarget`
- 参数 `target`: 目标 IP 地址字符串
- 参数 `local`: 输出参数，返回找到的本地 IP 地址
- 返回值: `Result` 类型，表示操作成功或失败

**第 30-31 行**: 命名空间结束
- 第 30 行: `} // namespace smem` - 结束 smem 命名空间
- 第 31 行: `} // namespace ock` - 结束 ock 命名空间

---

## 二、smem_net_common.cpp 逐行解读

### 文件信息
- 文件路径: `src/smem/csrc/net/smem_net_common.cpp`
- 代码行数: 186 行
- 主要功能: 实现 URL 解析和本地 IP 获取

### 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ... (许可证同上)
*/

#include "smem_net_common.h"

#include <arpa/inet.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <vector>
#include <map>
#include <regex>
#include "mf_ipv4_validator.h"
#include "mf_str_util.h"

namespace ock {
namespace smem {

const std::string PROTOCOL_TCP = "tcp://";

inline void Split(const std::string &src, const std::string &sep, std::vector<std::string> &out)
{
    std::string::size_type pos1 = 0;
    std::string::size_type pos2 = src.find(sep);

    std::string tmpStr;
    while (pos2 != std::string::npos) {
        tmpStr = src.substr(pos1, pos2 - pos1);
        out.emplace_back(tmpStr);
        pos1 = pos2 + sep.size();
        pos2 = src.find(sep, pos1);
    }

    if (pos1 != src.length()) {
        tmpStr = src.substr(pos1);
        out.emplace_back(tmpStr);
    }
}

inline bool IsValidIpV4(const std::string &address)
{
    static const std::regex ipV4Pattern("^(?:(?:25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)($|(?!\\.$)\\.)){4}$");
    static const std::regex zeroPattern("^0+\\.0+\\.0+\\.0+$");
    // 校验输入长度，防止正则表达式栈溢出
    constexpr size_t maxIpLen = 15;
    if (address.size() > maxIpLen) {
        return false;
    }
    if (std::regex_match(address, zeroPattern)) {
        return false;
    }

    if (!std::regex_match(address, ipV4Pattern)) {
        return false;
    }
    return true;
}

Result UrlExtraction::ExtractIpPortFromUrl(const std::string &url)
{
    std::map<std::string, std::string> details;
    auto parser = mf::SocketAddressParserMgr::getInstance().CreateParser(url);
    SM_ASSERT_RETURN(parser != nullptr, SM_ERROR);

    std::string ipStr = parser->GetIp();
    std::string portStr = std::to_string(parser->GetPort());

    /* covert port */
    long tmpPort = 0;
    if (!mf::StrUtil::String2Int<long>(portStr, tmpPort)) {
        SM_LOG_ERROR("Invalid url. ");
        return SM_INVALID_PARAM;
    }

    if (!parser->IsIpv6()) {
        if (!IsValidIpV4(ipStr) || tmpPort <= N1024 || tmpPort > UINT16_MAX) {
            SM_LOG_ERROR("Invalid url. ");
            return SM_INVALID_PARAM;
        }
    }

    /* set ip and port */
    ip = ipStr;
    port = tmpPort;
    return SM_OK;
}

static Result GetLocalIpV6WithTarget(const std::string &target, std::string &local)
{
    struct ifaddrs *ifaddr;
    char localResultIp[INET6_ADDRSTRLEN];
    Result result = SM_ERROR;
    struct in6_addr targetIp;
    if (inet_pton(AF_INET6, target.c_str(), &targetIp) != 1) {
        SM_LOG_ERROR("target IPv6 address invalid. " << target);
        return SM_INVALID_PARAM;
    }
    if (getifaddrs(&ifaddr) == -1) {
        SM_LOG_ERROR("get local net interfaces failed: " << errno << ": " << strerror(errno));
        return SM_ERROR;
    }
    for (auto ifa = ifaddr; ifa != nullptr; ifa = ifa->ifa_next) {
        if ((ifa->ifa_addr == nullptr) || (ifa->ifa_addr->sa_family != AF_INET6) || (ifa->ifa_netmask == nullptr)) {
            continue;
        }
        auto localIp = reinterpret_cast<struct sockaddr_in6 *>(ifa->ifa_addr)->sin6_addr;
        auto localMask = reinterpret_cast<struct sockaddr_in6 *>(ifa->ifa_netmask)->sin6_addr;
        bool sameSubnet = true;
        for (int i = 0; i < N16; ++i) {
            uint8_t localByte = localIp.s6_addr[i] & localMask.s6_addr[i];
            uint8_t targetByte = targetIp.s6_addr[i] & localMask.s6_addr[i];
            if (localByte != targetByte) {
                sameSubnet = false;
                break;
            }
        }
        if (!sameSubnet) {
            continue;
        }
        if (inet_ntop(AF_INET6, &localIp, localResultIp, sizeof(localResultIp)) == nullptr) {
            SM_LOG_ERROR("convert local IPv6 to string failed: " << errno << ": " << strerror(errno));
            result = SM_ERROR;
        } else {
            local = std::string(localResultIp);
            result = SM_OK;
        }
        break;
    }
    freeifaddrs(ifaddr);
    return result;
}

Result GetLocalIpWithTarget(const std::string &target, std::string &local)
{
    if (!IsValidIpV4(target)) {
        return GetLocalIpV6WithTarget(target, local);
    }
    struct ifaddrs *ifaddr;
    char localResultIp[64];
    Result result = SM_ERROR;

    struct in_addr targetIp;
    if (inet_aton(target.c_str(), &targetIp) == 0) {
        SM_LOG_ERROR("target ip address invalid. " << target);
        return SM_INVALID_PARAM;
    }

    if (getifaddrs(&ifaddr) == -1) {
        SM_LOG_ERROR("get local net interfaces failed: " << errno << ": " << strerror(errno));
        return SM_ERROR;
    }

    for (auto ifa = ifaddr; ifa != nullptr; ifa = ifa->ifa_next) {
        if ((ifa->ifa_addr == nullptr) || (ifa->ifa_addr->sa_family != AF_INET) || (ifa->ifa_netmask == nullptr)) {
            continue;
        }

        auto localIp = reinterpret_cast<struct sockaddr_in *>(ifa->ifa_addr)->sin_addr;
        auto localMask = reinterpret_cast<struct sockaddr_in *>(ifa->ifa_netmask)->sin_addr;
        if ((localIp.s_addr & localMask.s_addr) != (targetIp.s_addr & localMask.s_addr)) {
            continue;
        }

        if (inet_ntop(AF_INET, &localIp, localResultIp, sizeof(localResultIp)) == nullptr) {
            SM_LOG_ERROR("convert local ip to string failed. ");
            result = SM_ERROR;
        } else {
            local = std::string(localResultIp);
            result = SM_OK;
        }
        break;
    }

    freeifaddrs(ifaddr);
    return result;
}
} // namespace smem
} // namespace ock
```

### 逐行解读

**第 1-26 行**: 版权声明和头文件引用
- 第 13-21 行: 引入系统头文件
  - `arpa/inet.h` - IP 地址转换函数
  - `ifaddrs.h` - 网络接口地址获取
  - `net/if.h` - 网络接口操作
  - `vector` - 动态数组
  - `map` - 键值对容器
  - `regex` - 正则表达式
- 第 22-23 行: 引入项目工具头文件
  - `mf_ipv4_validator.h` - IPv4 验证器
  - `mf_str_util.h` - 字符串工具

**第 28 行**: TCP 协议常量
- 定义 `PROTOCOL_TCP` 为 `"tcp://"`，用于 URL 协议前缀

**第 30-46 行**: `Split` 辅助函数
- **功能**: 字符串分割函数
- 第 31-32 行: 定义位置变量，`pos1` 起始位置为 0，`pos2` 查找分隔符位置
- 第 33 行: 定义临时字符串变量
- 第 35-40 行: 循环处理每个分隔符
  - 第 36 行: 提取子串
  - 第 37 行: 添加到输出向量
  - 第 38 行: 更新起始位置
  - 第 39 行: 查找下一个分隔符
- 第 42-45 行: 处理剩余部分
  - 第 42 行: 如果还有剩余字符
  - 第 43 行: 提取剩余子串
  - 第 44 行: 添加到输出向量

**第 48-65 行**: `IsValidIpV4` IPv4 验证函数
- **功能**: 验证字符串是否为有效的 IPv4 地址
- 第 49 行: 定义 IPv4 正则表达式模式
  - `25[0-5]` 匹配 250-255
  - `2[0-4]\\d` 匹配 200-249
  - `1\\d\\d` 匹配 100-199
  - `[1-9]?\\d` 匹配 0-99
- 第 50 行: 定义全零 IP 模式（0.0.0.0 无效）
- 第 53-56 行: 长度检查防止正则表达式栈溢出
- 第 57-59 行: 拒绝全零 IP 地址
- 第 61-64 行: 使用正则表达式验证格式

**第 67-94 行**: `ExtractIpPortFromUrl` URL 解析函数
- **功能**: 从 URL 中提取 IP 地址和端口
- 第 68 行: 定义 details 映射（未使用）
- 第 69-70 行: 获取 SocketAddressParser 单例并创建解析器
- 第 71 行: 断言返回，解析器创建失败返回错误
- 第 73-74 行: 从解析器获取 IP 和端口字符串
- 第 77-81 行: 端口字符串转整数，转换失败返回错误
- 第 83-88 行: 非 IPv6 时验证 IPv4 地址和端口范围
  - 端口必须 > 1024（系统端口保留）
  - 端口必须 <= UINT16_MAX（65535）
- 第 91-92 行: 设置成员变量 ip 和 port
- 第 93 行: 返回成功

**第 96-139 行**: `GetLocalIpV6WithTarget` IPv6 本地 IP 获取
- **功能**: 根据目标 IPv6 地址找到同一子网的本地 IPv6 地址
- 第 98-100 行: 定义变量
- 第 101-105 行: 将目标字符串转换为 IPv6 地址结构
- 第 106-109 行: 获取本地网络接口列表
- 第 110-136 行: 遍历所有网络接口
  - 第 111-113 行: 跳过无效接口和非 IPv6 接口
  - 第 114-115 行: 提取本地 IP 和子网掩码
  - 第 116-124 行: 检查是否在同一子网（通过比较 IP & 掩码）
    - IPv6 地址 16 字节，逐字节比较
  - 第 125-127 行: 不在同一子网则继续
  - 第 128-135 行: 找到同子网接口，转换 IP 为字符串
- 第 137 行: 释放接口列表
- 第 138 行: 返回结果

**第 141-184 行**: `GetLocalIpWithTarget` IPv4 本地 IP 获取
- **功能**: 根据目标 IPv4 地址找到同一子网的本地 IPv4 地址
- 第 143-145 行: 如果不是 IPv4，调用 IPv6 版本
- 第 146-148 行: 定义变量
- 第 150-154 行: 将目标字符串转换为 IPv4 地址结构
  - `inet_aton` 将点分十进制转为网络字节序
- 第 156-159 行: 获取本地网络接口列表
- 第 161-180 行: 遍历所有网络接口
  - 第 162-164 行: 跳过无效接口和非 IPv4 接口
  - 第 166-167 行: 提取本地 IP 和子网掩码
  - 第 168-170 行: 检查是否在同一子网
  - 第 172-179 行: 找到同子网接口，转换 IP 为字符串
- 第 182 行: 释放接口列表
- 第 183 行: 返回结果

---

## 三、smem_net_group_engine.h 逐行解读

### 文件信息
- 文件路径: `src/smem/csrc/net/smem_net_group_engine.h`
- 代码行数: 167 行
- 主要功能: 定义组通信引擎类

### 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ... (许可证同上)
*/
#ifndef SMEM_SMEM_NET_GROUP_ENGINE_H
#define SMEM_SMEM_NET_GROUP_ENGINE_H

#include <functional>
#include <thread>
#include <atomic>
#include <list>
#include "smem_common_includes.h"
#include "smem_config_store.h"

namespace ock {
namespace smem {

class SmemNetGroupEngine;
using SmemGroupEnginePtr = SmRef<SmemNetGroupEngine>;
using SmemGroupChangeCallback = std::function<Result(uint32_t rank)>;
const uint32_t REMOVE_INTERVAL = 2;

/**
 * @brief create group option
 * @param rankSize          [in] the number of rank
 * @param rank              [in] local rank (rank is not necessarily between 0 and rankSize)
 * @param timeoutMs         [in] operation timeout (barrier, all_gather)
 * @param dynamic           [in] rankSize is dynamic (can join or leave some rank)
 * @param joinCb            [in] the callback which is called when some rank join
 * @param leaveCb           [in] the callback which is called when some rank leave
*/
struct SmemGroupOption {
    uint32_t rankSize;
    uint32_t rank;
    uint64_t timeoutMs;

    bool dynamic;
    SmemGroupChangeCallback joinCb;
    SmemGroupChangeCallback leaveCb;
};

enum class GroupEventType : int8_t { LUNCH_JOIN_LEAVE_EVENT = 0, REMOTE_DOWN_EVENT = 1 };

struct GroupEvent {
    GroupEventType eventType;
    uint32_t remoteRankId;
    std::string value;
    explicit GroupEvent(uint32_t id) : eventType{GroupEventType::REMOTE_DOWN_EVENT}, remoteRankId{id} {}
    explicit GroupEvent(std::string val)
        : eventType{GroupEventType::LUNCH_JOIN_LEAVE_EVENT}, remoteRankId{std::numeric_limits<uint32_t>::max()},
          value{std::move(val)}
    {}
};

struct GroupListenContext {
    uint32_t watchId = UINT32_MAX;
    int32_t ret = SM_OK;
    std::list<GroupEvent> events;
};

constexpr uint32_t MAX_RANK_COUNT = 1024U;
constexpr uint32_t BITS_COUNT_IN_U64 = 64U;
constexpr uint32_t RANK_BITS_U64_COUNT = MAX_RANK_COUNT / BITS_COUNT_IN_U64;

class SmemNetGroupEngine : public SmReferable {
public:
    static SmemGroupEnginePtr Create(const StorePtr &store, const SmemGroupOption &option);

public:
    SmemNetGroupEngine(const StoreManagerPtr &store, const SmemGroupOption &option) : store_(store), option_(option)
    {
        joined_ = !option_.dynamic;
        if (option_.dynamic) {
            option_.rankSize = 1;
        }
        store_->RegisterReconnectHandler(std::bind(&SmemNetGroupEngine::LinkReconnectHandler, this));
        bzero(joinedRanksBitmap_, sizeof(joinedRanksBitmap_));
    }
    ~SmemNetGroupEngine() override;

    Result GroupBarrier();

    Result GroupBarrier(const char *key, uint32_t rankSize, uint32_t rankId);

    Result GroupAllGather(const char *sendBuf, uint32_t sendSize, char *recvBuf, uint32_t recvSize);

    Result GroupAllGather(const char *key, uint32_t rankSize, uint32_t rankId, const char *sendBuf, uint32_t sendSize,
                          char *recvBuf, uint32_t recvSize);

    Result GroupBroadcastExit(int status);

    Result RegisterExit(const std::function<void(int)> &exit);

    int32_t AllocNumber();

    Result ReleaseNumber(int32_t val);

    Result StartListenEvent();

    Result GroupJoin();

    Result GroupLeave();

    uint32_t GetLocalRank() const;

    uint32_t GetRankSize() const;

    void SetBitmapFromRanks(const std::vector<uint32_t> &rankIds);

    void GroupSnClean();

private:
    bool ReWatch();
    void GroupListenEvent();
    void JoinLeaveEventProcess(const std::string &value, std::string &prevEventValue);
    void RankLinkDownEventProcess(uint32_t rankId, std::string &prevEventValue);
    void LinkDownUpdateMeta(uint32_t rankId);
    void UpdateGroupVersion(int32_t ver);
    void GroupWatchCb(int result, const std::string &key, const std::string &value);
    void RemoteRankLinkDownCb(uint32_t remoteRankId);
    void ClearBitmapForRank(uint32_t rankId);
    bool TestBitmapForRank(uint32_t rankId) const;
    int32_t LinkReconnectHandler();
    void RankExit(int result, const std::string &key, const std::string &value);

    StoreManagerPtr store_ = nullptr;
    SmemGroupOption option_;
    int32_t groupVersion_ = 0;
    uint32_t allGatherGroupSn_ = 0;
    uint32_t barrierGroupSn_ = 0;

    std::thread listenThread_;
    SmemTimedwait listenSignal_;
    GroupListenContext listenCtx_;
    std::atomic_uint32_t listenLinkStatusWatchId_ = UINT32_MAX;
    mutable std::mutex groupEventHandleMutex_;
    std::atomic_bool joined_ = false;
    std::atomic<bool> listenThreadStarted_{false};
    std::atomic_bool groupStoped_ = false;
    std::function<void(int)> globalExitHandler_;
    uint64_t joinedRanksBitmap_[RANK_BITS_U64_COUNT]{};
    mutable std::mutex rankBitmapMutex_;
    std::unordered_map<std::string, uint32_t> userGroupGatherSn_;
    std::unordered_map<std::string, uint32_t> userGroupBarrierSn_;
    std::set<int32_t> allocedSet_;
};

inline uint32_t SmemNetGroupEngine::GetLocalRank() const
{
    return option_.rank;
}

inline uint32_t SmemNetGroupEngine::GetRankSize() const
{
    return option_.rankSize;
}

} // namespace smem
} // namespace ock
#endif // SMEM_SMEM_NET_GROUP_ENGINE_H
```

### 逐行解读

**第 12-26 行**: 头文件保护和引用
- 第 12 行: 头文件保护宏 `SMEM_SMEM_NET_GROUP_ENGINE_H`
- 第 16-20 行: 引入标准库
  - `functional` - 函数对象和 std::function
  - `thread` - 线程支持
  - `atomic` - 原子操作
  - `list` - 双向链表
- 第 21-22 行: 引入项目头文件
  - `smem_common_includes.h` - 公共定义
  - `smem_config_store.h` - 配置存储接口

**第 25-27 行**: 类型别名和常量
- 第 25 行: 前置声明 `SmemNetGroupEngine` 类
- 第 26 行: 定义 `SmemGroupEnginePtr` 为 `SmemNetGroupEngine` 的智能指针类型
- 第 27 行: 定义 `SmemGroupChangeCallback` 为回调函数类型，接收 rank ID，返回 Result
- 第 28 行: 定义 `REMOVE_INTERVAL` 常量为 2，用于控制旧 key 清理间隔

**第 30-47 行**: `SmemGroupOption` 组选项结构体
- 第 37 行: `rankSize` - 组中 rank 的数量
- 第 38 行: `rank` - 本地 rank ID（不一定在 0 到 rankSize-1 范围内）
- 第 39 行: `timeoutMs` - 操作超时时间（毫秒）
- 第 41 行: `dynamic` - 是否为动态组（支持 rank 加入/退出）
- 第 42 行: `joinCb` - rank 加入时的回调
- 第 43 行: `leaveCb` - rank 退出时的回调

**第 49 行**: `GroupEventType` 事件类型枚举
- `LUNCH_JOIN_LEAVE_EVENT = 0` - 加入/退出事件
- `REMOTE_DOWN_EVENT = 1` - 远程节点下线事件

**第 51-60 行**: `GroupEvent` 事件结构体
- 第 52 行: `eventType` - 事件类型
- 第 53 行: `remoteRankId` - 远程 rank ID（用于下线事件）
- 第 54 行: `value` - 事件值字符串（用于加入/退出事件）
- 第 55 行: 构造函数，创建下线事件，接收 rank ID
- 第 56-59 行: 构造函数，创建加入/退出事件，接收事件值字符串

**第 62-66 行**: `GroupListenContext` 监听上下文
- 第 63 行: `watchId` - 监听 ID，初始值为 UINT32_MAX（无效值）
- 第 64 行: `ret` - 返回码，初始为 SM_OK
- 第 65 行: `events` - 事件列表

**第 68-70 行**: bitmap 常量
- 第 68 行: `MAX_RANK_COUNT = 1024` - 最大 rank 数量
- 第 69 行: `BITS_COUNT_IN_U64 = 64` - uint64_t 的位数
- 第 70 行: `RANK_BITS_U64_COUNT = 16` - 需要 16 个 uint64_t 存储 1024 位的 bitmap

**第 72-120 行**: `SmemNetGroupEngine` 类定义
- 第 72 行: 继承自 `SmReferable`，支持引用计数
- 第 74 行: 静态工厂方法 `Create`

**第 77-86 行**: 构造函数
- 第 77 行: 接收存储管理器和组选项
- 第 78 行: 初始化列表，绑定 store_ 和 option_
- 第 80 行: 非动态组默认已加入
- 第 81-83 行: 动态组初始 rankSize 为 1
- 第 84 行: 注册重连回调
- 第 85 行: 清空 bitmap

**第 88-119 行**: 公共方法
- 第 88 行: 默认 Barrier（使用组默认配置）
- 第 89 行: 自定义 Barrier（指定 key、rankSize、rankId）
- 第 91-92 行: AllGather 的两个重载版本
- 第 96 行: `GroupBroadcastExit` - 广播退出状态
- 第 97 行: `RegisterExit` - 注册退出回调
- 第 100 行: `AllocNumber` - 分配一个编号（CAS 操作）
- 第 102 行: `ReleaseNumber` - 释放编号
- 第 104 行: `StartListenEvent` - 开始监听事件（动态组）
- 第 106 行: `GroupJoin` - 加入组
- 第 108 行: `GroupLeave` - 离开组
- 第 110-113 行: Getter 和 Setter

**第 121-132 行**: 私有方法
- 第 121 行: `ReWatch` - 重新监听
- 第 122 行: `GroupListenEvent` - 事件监听线程函数
- 第 123 行: `JoinLeaveEventProcess` - 处理加入/退出事件
- 第 124 行: `RankLinkDownEventProcess` - 处理 rank 下线事件
- 第 125 行: `LinkDownUpdateMeta` - 更新元数据
- 第 126 行: `UpdateGroupVersion` - 更新组版本
- 第 127 行: `GroupWatchCb` - 监听回调
- 第 128 行: `RemoteRankLinkDownCb` - 远程 rank 下线回调
- 第 129 行: `ClearBitmapForRank` - 清除 rank 的 bitmap 位
- 第 130 行: `TestBitmapForRank` - 测试 rank 是否在 bitmap 中
- 第 131 行: `LinkReconnectHandler` - 重连处理
- 第 132 行: `RankExit` - 退出处理

**第 134-152 行**: 成员变量
- 第 134 行: `store_` - 配置存储管理器
- 第 135 行: `option_` - 组选项
- 第 136 行: `groupVersion_` - 组版本号
- 第 137 行: `allGatherGroupSn_` - AllGather 序列号
- 第 138 行: `barrierGroupSn_` - Barrier 序列号
- 第 140 行: `listenThread_` - 监听线程
- 第 141 行: `listenSignal_` - 监听信号量
- 第 142 行: `listenCtx_` - 监听上下文
- 第 143 行: `listenLinkStatusWatchId_` - 链路状态监听 ID
- 第 144 行: `groupEventHandleMutex_` - 事件处理互斥锁
- 第 145 行: `joined_` - 是否已加入
- 第 146 行: `listenThreadStarted_` - 监听线程是否已启动
- 第 147 行: `groupStoped_` - 组是否停止
- 第 147 行: `globalExitHandler_` - 全局退出处理函数
- 第 148 行: `joinedRanksBitmap_` - 已加入 rank 的 bitmap
- 第 149 行: `rankBitmapMutex_` - bitmap 互斥锁
- 第 150 行: `userGroupGatherSn_` - 用户 AllGather 序列号映射
- 第 151 行: `userGroupBarrierSn_` - 用户 Barrier 序列号映射
- 第 152 行: `allocedSet_` - 已分配编号集合

**第 155-163 行**: 内联函数
- 第 155-158 行: `GetLocalRank` 返回本地 rank ID
- 第 160-163 行: `GetRankSize` 返回 rank 数量

---

## 四、smem_net_group_engine.cpp 逐行解读（第一部分：常量和辅助函数）

### 文件信息
- 文件路径: `src/smem/csrc/net/smem_net_group_engine.cpp`
- 代码行数: 1,109 行
- 主要功能: 组引擎实现

### 第一部分：常量定义和辅助结构（第 12-87 行）

```cpp
#include <algorithm>
#include <cerrno>
#include <cctype>
#include <climits>
#include "mf_num_util.h"
#include "mf_monotonic_time.h"
#include "acc_def.h"
#include "smem_store_factory.h"
#include "mf_str_util.h"
#include "smem_net_group_engine.h"
#include "smem_shm_def.h"

namespace ock {
namespace smem {
using namespace mf;

const std::string SMEM_GROUP_SET_STR = "ok";
const std::string SMEM_GROUP_EXIT_KEY = "EXIT";
const std::string SMEM_GROUP_LISTEN_EVENT_KEY = "EVENT";
const std::string SMEM_GROUP_DYNAMIC_SIZE_KEY = "DSIZE";
const std::string SMEM_GROUP_CAS_ALLOC_NUM_KEY = "AT_NUM";
constexpr uint32_t SMEM_ALLOC_NUM_SIZE = SMEM_SHM_ATOMIC_NUM_LIMIT;
constexpr uint32_t SMEM_ALLOC_NUM_BUF_LEN = (SMEM_ALLOC_NUM_SIZE + 7) / 8; // uint8_t
constexpr uint32_t SMEM_GATHER_PREFIX_SIZE = 4U;
constexpr int32_t SMEM_GROUP_MS_TO_US = 1000;
constexpr int64_t SMEM_GROUP_LISTER_TIMEOUT = 10LL * 1000;              // 10s, unit: ms
constexpr int32_t SMEM_GROUP_SLEEP_TIMEOUT = 100 * SMEM_GROUP_MS_TO_US; // 100ms, unit: us
constexpr int32_t SMEM_GROUP_SLEEP_5S = 5000 * SMEM_GROUP_MS_TO_US;     // 5s

constexpr uint32_t UINT_BIT = 8U;
constexpr int32_t GROUP_DYNAMIC_SIZE_BIT_LEN = 30;
constexpr uint32_t GROUP_DYNAMIC_SIZE_BIT_MASK = (1 << 30) - 1;

constexpr uint32_t USER_GROUP_KEY_LEN_MAX = 64;

struct JoinLeaveEventValue {
    bool join; // true => join, false => leave
    char evt;
    uint32_t rankId;

    JoinLeaveEventValue() : JoinLeaveEventValue{true, 0} {}
    JoinLeaveEventValue(bool j, uint32_t r) : join{j}, evt{j ? 'J' : 'L'}, rankId{r} {}

    std::string ToString() const
    {
        std::stringstream ss;
        ss << (join ? 'J' : 'L') << rankId;
        return ss.str();
    }

    int32_t Parse(const std::string &str)
    {
        std::stringstream ss(str);
        ss >> evt >> rankId;
        join = (evt == 'J');
        auto check = ToString();
        if (check != str) {
            SM_LOG_ERROR("parse from str: (" << str << ") invalid.");
            return SM_ERROR;
        }
        return SM_OK;
    }
};

static inline std::pair<int32_t, int32_t> SplitSizeAndVersion(int64_t val)
{
    auto unsignedVal = static_cast<uint64_t>(val);
    return std::make_pair(unsignedVal >> GROUP_DYNAMIC_SIZE_BIT_LEN, unsignedVal & GROUP_DYNAMIC_SIZE_BIT_MASK);
}

static int64_t MergeSizeAndVersion(int32_t ver, int32_t size)
{
    auto unsignedVer = static_cast<uint32_t>(ver);
    auto unsignedSize = static_cast<uint32_t>(size);
    return ((1LL * unsignedVer) << GROUP_DYNAMIC_SIZE_BIT_LEN) | unsignedSize;
}
```

### 逐行解读

**第 12-23 行**: 头文件引用
- 第 12-15 行: 标准库 - 算法、错误码、字符处理、数值限制
- 第 16-21 行: 项目头文件
  - `mf_num_util.h` - 数值工具
  - `mf_monotonic_time.h` - 单调时间（性能测量）
  - `acc_def.h` - acc_links 定义
  - `smem_store_factory.h` - 存储工厂
  - `mf_str_util.h` - 字符串工具
  - `smem_net_group_engine.h` - 组引擎头文件
  - `smem_shm_def.h` - SHM 定义

**第 28 行**: `SMEM_GROUP_SET_STR = "ok"` - Barrier/AllGather 完成标记

**第 29 行**: `SMEM_GROUP_EXIT_KEY = "EXIT"` - 退出通知 key

**第 30 行**: `SMEM_GROUP_LISTEN_EVENT_KEY = "EVENT"` - 事件监听 key

**第 31 行**: `SMEM_GROUP_DYNAMIC_SIZE_KEY = "DSIZE"` - 动态组大小 key

**第 32 行**: `SMEM_GROUP_CAS_ALLOC_NUM_KEY = "AT_NUM"` - CAS 分配编号 key

**第 33-34 行**: 分配编号相关常量
- 第 33 行: `SMEM_ALLOC_NUM_SIZE` = SHM 原子数量限制
- 第 34 行: `SMEM_ALLOC_NUM_BUF_LEN` = 字节缓冲区长度（向上取整）

**第 35 行**: `SMEM_GATHER_PREFIX_SIZE = 4` - AllGather 前缀大小（存储 rank ID）

**第 36-38 行**: 超时时间常量
- 第 36 行: 毫秒转微秒乘数 1000
- 第 37 行: 监听器超时 10 秒
- 第 38 行: 睡眠超时 100 毫秒
- 第 39 行: 5 秒睡眠超时

**第 41-43 行**: 动态大小编码常量
- 第 41 行: `UINT_BIT = 8` - uint8_t 位数
- 第 42 行: `GROUP_DYNAMIC_SIZE_BIT_LEN = 30` - 版本号位数
- 第 43 行: `GROUP_DYNAMIC_SIZE_BIT_MASK` - 大小掩码（低 30 位）
- 高 32 位用于版本号，低 30 位用于大小

**第 45 行**: `USER_GROUP_KEY_LEN_MAX = 64` - 用户 key 最大长度

**第 47-74 行**: `JoinLeaveEventValue` 结构体
- **功能**: 表示加入/退出事件的值
- 第 48 行: `join` - true 为加入，false 为退出
- 第 49 行: `evt` - 事件字符（'J' 或 'L'）
- 第 50 行: `rankId` - rank ID
- 第 52 行: 委托构造函数，默认加入，rank 0
- 第 53 行: 构造函数，设置 join 和 rankId，evt 自动设置
- 第 55-60 行: `ToString` 转为字符串 "J{rankId}" 或 "L{rankId}"
- 第 62-73 行: `Parse` 从字符串解析
  - 第 64 行: 从字符串读取事件字符和 rankId
  - 第 65 行: 根据 evt 设置 join
  - 第 66-70 行: 验证解析结果正确性

**第 76-80 行**: `SplitSizeAndVersion` 函数
- **功能**: 从合并的 64 位值中分离出版本号和大小
- 第 78 行: 转为无符号
- 第 79 行: 高位是版本号，低位是大小，返回 pair

**第 82-87 行**: `MergeSizeAndVersion` 函数
- **功能**: 将版本号和大小合并为 64 位值
- 第 84-85 行: 转为无符号
- 第 86 行: 版本号左移 30 位，与大小按或合并

---

## 五、smem_net_group_engine.cpp 逐行解读（第二部分：析构和创建）

### 第二部分：析构函数和 Create 方法（第 89-120 行）

```cpp
SmemNetGroupEngine::~SmemNetGroupEngine()
{
    groupStoped_ = true;
    if (listenCtx_.watchId != UINT32_MAX) {
        (void)store_->Unwatch(listenCtx_.watchId);
    }
    uint32_t linkStatusWatchId = listenLinkStatusWatchId_.load(std::memory_order_acquire);
    if (linkStatusWatchId != UINT32_MAX) {
        (void)store_->Unwatch(linkStatusWatchId);
        listenLinkStatusWatchId_.store(UINT32_MAX, std::memory_order_release);
    }
    if (listenThread_.joinable()) {
        listenSignal_.PthreadSignal();
        listenThread_.join();
    }
}

SmemGroupEnginePtr SmemNetGroupEngine::Create(const StorePtr &store, const SmemGroupOption &option)
{
    std::string prefix = (option.dynamic ? "D_" : "S_");
    StorePtr ss = StoreFactory::PrefixStore(store, prefix);
    SM_ASSERT_RETURN(ss != nullptr, nullptr);
    StoreManagerPtr managerPtr = Convert<ConfigStore, ConfigStoreManager>(ss);
    SM_ASSERT_RETURN(managerPtr != nullptr, nullptr);
    SmemGroupEnginePtr group = SmMakeRef<SmemNetGroupEngine>(managerPtr, option);
    SM_ASSERT_RETURN(group != nullptr, nullptr);

    if (option.dynamic) {
        SM_ASSERT_RETURN(group->StartListenEvent() == SM_OK, nullptr);
    }
    return group.Get();
}
```

### 逐行解读

**析构函数（第 89-104 行）**:
- 第 91 行: 设置停止标志
- 第 92-94 行: 取消事件监听
- 第 95-99 行: 取消链路状态监听
  - 第 95 行: 使用 acquire 内存语义加载
  - 第 97 行: 取消监听
  - 第 98 行: 使用 release 内存语义存储
- 第 100-103 行: 等待监听线程结束
  - 第 100 行: 检查线程是否可 join
  - 第 101 行: 发送信号唤醒线程
  - 第 102 行: 等待线程结束

**Create 静态方法（第 106-120 行）**:
- **功能**: 创建组引擎实例
- 第 108 行: 动态组使用 "D_" 前缀，静态组使用 "S_" 前缀
- 第 109 行: 创建带前缀的存储
- 第 110 行: 断言返回，存储创建失败
- 第 111 行: 转换为存储管理器指针
- 第 112 行: 断言返回，转换失败
- 第 113 行: 创建组引擎实例
- 第 114 行: 断言返回，创建失败
- 第 116-118 行: 动态组启动事件监听
- 第 119 行: 返回裸指针（智能指针管理生命周期）

---

## 六、smem_net_group_engine.cpp 逐行解读（第三部分：Barrier 实现）

### 第三部分：GroupBarrier 实现（第 122-265 行）

```cpp
Result SmemNetGroupEngine::GroupBarrier()
{
    SM_ASSERT_RETURN(store_ != nullptr, SM_INVALID_PARAM);
    uint32_t size = option_.rankSize;
    std::string idx = std::to_string(groupVersion_) + "_" + std::to_string(++barrierGroupSn_);
    std::string addKey = idx + "_BA";
    std::string waitKey = idx + "_BW";
    int64_t val = 0;

    MonoPerfTrace traceBarrier;
    /* all guys add 1 to barrier key and get it */
    MonoPerfTrace traceAdd;
    auto ret = store_->Add(addKey, 1, val);
    if (ret != SM_OK) {
        SM_LOG_AND_SET_LAST_ERROR("store add key: " << store_->GetCompleteKey(addKey)
                                                    << " failed, result:" << ConfigStore::ErrStr(ret));
        return SM_ERROR;
    }
    traceAdd.RecordEnd();
    SM_LOG_DEBUG("store add key: " << store_->GetCompleteKey(addKey) << " value: " << val << " size:" << size);

    /* only the first rank needs to clear the last key, and it's unnecessary to clear map for first time */
    if (val == 1 && barrierGroupSn_ > REMOVE_INTERVAL) {
        uint32_t removeBarrierGroupSn = barrierGroupSn_ - REMOVE_INTERVAL;
        std::string removeAddIdx = std::to_string(groupVersion_) + "_" + std::to_string(removeBarrierGroupSn) + "_BA";
        std::string removeWaitIdx = std::to_string(groupVersion_) + "_" + std::to_string(removeBarrierGroupSn) + "_BW";
        /* There is no need to return ERROR, when the removed key is already not exist.
        The WARNING LOG is contained in the remove func itself, no need to print more log. */
        (void)store_->Remove(removeAddIdx);
        (void)store_->Remove(removeWaitIdx);
    }

    /* the last guy set the status to ok, and other guys just wait for the last guy set the value */
    if (val == size) {
        ret = store_->Set(waitKey, SMEM_GROUP_SET_STR);
        if (ret != SM_OK) {
            SM_LOG_AND_SET_LAST_ERROR("store set key: " << store_->GetCompleteKey(waitKey)
                                                        << " failed, result:" << ConfigStore::ErrStr(ret));
            return SM_ERROR;
        }
        SM_LOG_DEBUG("store set key: " << store_->GetCompleteKey(waitKey));
    }

    /* all guys wait for waitKey status with timeout, timeout happens if the ok status not set by the last guy */
    MonoPerfTrace traceGetStatus;
    std::string getVal;
    ret = store_->Get(waitKey, getVal, option_.timeoutMs);
    if (ret != SM_OK) {
        SM_LOG_AND_SET_LAST_ERROR("store get key: " << store_->GetCompleteKey(waitKey)
                                                    << " failed, result:" << ConfigStore::ErrStr(ret));
        return SM_ERROR;
    }
    traceGetStatus.RecordEnd();

    if (getVal != SMEM_GROUP_SET_STR) {
        SM_LOG_AND_SET_LAST_ERROR("store get key: " << store_->GetCompleteKey(waitKey) << " val is not equal, val: "
                                                    << getVal << " expect: " << SMEM_GROUP_SET_STR);
        return SM_ERROR;
    }
    traceBarrier.RecordEnd();

    SM_LOG_INFO("groupBarrier successfully, key: " << store_->GetCompleteKey(waitKey) << ", size: " << size
                                                   << ", timeCostUs: total(" << traceBarrier.PeriodUs() << ") add("
                                                   << traceAdd.PeriodUs() << ") getStatus(" << traceGetStatus.PeriodUs()
                                                   << ")");
    return SM_OK;
}
```

### 逐行解读

**GroupBarrier 默认实现（第 122-188 行）**:
- **功能**: 实现分布式屏障同步
- 第 124 行: 断言存储有效
- 第 125 行: 获取 rank 数量
- 第 126 行: 生成索引 "版本号_序列号"
- 第 127 行: 生成 add key "版本号_序列号_BA"（Barrier Add）
- 第 128 行: 生成 wait key "版本号_序列号_BW"（Barrier Wait）
- 第 129 行: 值变量初始化为 0

- **第一阶段：所有 rank 自增计数**（第 131-141 行）
  - 第 131 行: 创建性能追踪器
  - 第 132 行: 注释，所有 rank 向 add key 加 1
  - 第 134 行: 调用 Add 操作，原子递增并返回新值
  - 第 135-139 行: 错误处理，记录日志并返回

- **第二阶段：第一个 rank 清理旧 key**（第 143-152 行）
  - 第 144 行: 只有第一个 rank（val == 1）且不是首次执行时清理
  - 第 145-151 行: 删除 REMOVE_INTERVAL 之前的旧 key

- **第三阶段：最后一个 rank 设置完成标记**（第 154-163 行）
  - 第 155 行: 判断是否为最后一个 rank
  - 第 156 行: 设置 wait key 为 "ok"
  - 第 157-161 行: 错误处理

- **第四阶段：所有 rank 等待完成标记**（第 165-180 行）
  - 第 168 行: 获取 wait key 的值
  - 第 169-173 行: 错误处理
  - 第 176-180 行: 验证值为 "ok"

- **完成**（第 181-187 行）
  - 第 181 行: 记录结束时间
  - 第 183-186 行: 输出成功日志，包含耗时统计

**GroupBarrier 重载版本（第 190-265 行）**:
- **功能**: 支持用户自定义 key、rankSize、rankId 的 Barrier
- 第 192-198 行: 参数验证
  - key 不为空
  - key 长度不超过限制
  - rankSize 有效
  - rankId 有效
- 第 202 行: 获取用户 key 的本地序列号引用
- 第 203 行: 生成用户 key 的索引
- 其余逻辑与默认版本相同，但使用用户 key 的序列号

---

## 七、smem_net_group_engine.cpp 逐行解读（第四部分：AllGather 和辅助函数）

### 第四部分：GroupAllGather 实现（第 267-534 行）

```cpp
static inline void GatherFillRank(std::vector<uint8_t> &vec, uint32_t rank)
{
    uint32_t *st = reinterpret_cast<uint32_t *>(vec.data());
    *st = rank;
}

static void SortGatherRecv(std::vector<uint8_t> &vec, uint32_t preSize, uint32_t rankSize, char *recvBuf)
{
    std::vector<std::pair<uint32_t, uint32_t>> offset(rankSize);
    uint32_t unitSize = preSize + SMEM_GATHER_PREFIX_SIZE;
    uint8_t *ptr = vec.data();
    for (uint32_t i = 0; i < rankSize; i++) {
        uint32_t idx = i * unitSize;
        offset[i].first = *reinterpret_cast<uint32_t *>(ptr + idx);
        offset[i].second = idx + SMEM_GATHER_PREFIX_SIZE;
    }

    std::sort(offset.begin(), offset.end());
    for (uint32_t i = 0; i < rankSize; i++) {
        (void)std::copy_n(ptr + offset[i].second, preSize, recvBuf + preSize * i);
    }
}

Result SmemNetGroupEngine::GroupAllGather(const char *sendBuf, uint32_t sendSize, char *recvBuf, uint32_t recvSize)
{
    // ... 实现
}
```

### 逐行解读

**GatherFillRank 辅助函数（第 267-271 行）**:
- **功能**: 在向量头部填充 rank ID
- 第 269 行: 将向量数据转为 uint32_t 指针
- 第 270 行: 写入 rank ID

**SortGatherRecv 辅助函数（第 273-288 行）**:
- **功能**: 对接收到的 AllGather 数据按 rank ID 排序
- 第 275 行: 创建偏移量对数组（rank ID, 数据偏移）
- 第 276 行: 计算单元大小（数据大小 + 4字节 rank ID）
- 第 277 行: 获取数据指针
- 第 278-282 行: 遍历所有 rank，提取 rank ID 和数据偏移
- 第 284 行: 按 rank ID 排序
- 第 285-287 行: 按排序后的顺序拷贝数据到接收缓冲区

**GroupAllGather 默认实现（第 350-436 行）**:
- **功能**: 收集所有 rank 的数据
- 第 352 行: 断言存储有效
- 第 353 行: 验证接收缓冲区大小正确
- 第 356-358 行: 生成 key
- 第 360-362 行: 准备输入数据（前缀填 rank ID，后跟发送数据）

- **第一阶段：所有 rank 追加数据**（第 364-374 行）
  - 第 368 行: 调用 Append 追加数据，返回当前长度
  - 第 369-373 行: 错误处理

- **第二阶段：清理旧数据**（第 376-385 行）
  - 第 377 行: 第一个 rank 清理旧 key

- **第三阶段：最后一个 rank 设置完成标记**（第 387-395 行）
  - 第 388 行: 判断是否为最后一个 rank
  - 第 389 行: 设置 wait key

- **第四阶段：等待完成**（第 397-412 行）
  - 第 400 行: 等待 wait key 为 "ok"

- **第五阶段：获取数据并排序**（第 414-428 行）
  - 第 417 行: 获取完整数据
  - 第 418-423 行: 验证数据大小
  - 第 428 行: 调用 SortGatherRecv 排序

---

## 八、smem_net_group_engine.cpp 逐行解读（第五部分：退出和编号分配）

### 第五部分：退出和编号管理（第 290-594 行）

```cpp
Result SmemNetGroupEngine::GroupBroadcastExit(int status)
{
    SM_ASSERT_RETURN(store_ != nullptr, SM_INVALID_PARAM);
    auto ret = store_->Set(SMEM_GROUP_EXIT_KEY, std::to_string(status));
    SM_VALIDATE_RETURN(ret == SM_OK,
                       "store set key: " << store_->GetCompleteKey(SMEM_GROUP_EXIT_KEY)
                                         << " failed, result:" << ConfigStore::ErrStr(ret),
                       SM_ERROR);
    SM_LOG_DEBUG("store set key: " << store_->GetCompleteKey(SMEM_GROUP_EXIT_KEY));
    return ret;
}

Result SmemNetGroupEngine::RegisterExit(const std::function<void(int)> &exit)
{
    if (globalExitHandler_ != nullptr) {
        SM_LOG_WARN("the exit function is not null");
        return SM_INVALID_PARAM;
    }
    SM_ASSERT_RETURN(exit != nullptr, SM_INVALID_PARAM);
    SM_ASSERT_RETURN(store_ != nullptr, SM_INVALID_PARAM);
    globalExitHandler_ = exit;
    uint32_t wid;
    auto ret = store_->Watch(SMEM_GROUP_EXIT_KEY,
                             std::bind(&SmemNetGroupEngine::RankExit, this, std::placeholders::_1,
                                       std::placeholders::_2, std::placeholders::_3),
                             wid);
    if (ret != SM_OK) {
        SM_LOG_WARN("group watch failed, maybe link down, ret: " << ret);
        globalExitHandler_ = nullptr;
        return ret;
    }
    return SM_OK;
}

void SmemNetGroupEngine::RankExit(int result, const std::string &key, const std::string &value)
{
    if (result == SUCCESS && globalExitHandler_ != nullptr) {
        if (value.empty()) {
            SM_LOG_WARN("the value is empty");
            return;
        }
        int val = 0;
        try {
            long tempVal = std::stol(value);
            if (tempVal < std::numeric_limits<int>::min() || tempVal > std::numeric_limits<int>::max()) {
                SM_LOG_WARN("value out of int range: " << tempVal << " (value='" << value << "')");
                return;
            }
            val = static_cast<int>(tempVal);
        } catch (...) {
            SM_LOG_WARN("convert string to int failed");
            return;
        }
        globalExitHandler_(val);
    } else {
        SM_LOG_WARN("global exit failed");
    }
}

int32_t SmemNetGroupEngine::AllocNumber()
{
    std::vector<uint8_t> expect;
    std::vector<uint8_t> value(SMEM_ALLOC_NUM_BUF_LEN, 0);
    std::vector<uint8_t> old;
    int32_t num;
    int32_t ret;
    do {
        swap(expect, old);
        if (expect.size() != 0) {
            value = expect;
        }
        num = -1;
        for (uint32_t i = 0; i < SMEM_ALLOC_NUM_SIZE; i++) {
            if ((value[i / UINT_BIT] & (1U << (i % UINT_BIT))) == 0) {
                num = static_cast<int32_t>(i);
                value[i / UINT_BIT] ^= 1U << (i % UINT_BIT);
                break;
            }
        }
        if (num == -1) {
            SM_LOG_ERROR("there is no free number available for allocation!");
            return SM_ERROR;
        }
        ret = store_->Cas(SMEM_GROUP_CAS_ALLOC_NUM_KEY, expect, value, old);
    } while (ret != 0 || old != expect);
    allocedSet_.insert(num);
    return num;
}

Result SmemNetGroupEngine::ReleaseNumber(int32_t val)
{
    if (allocedSet_.count(val) == 0) {
        SM_LOG_ERROR("key(" << val << ") is not exist!");
        return SM_OBJECT_NOT_EXISTS;
    }
    allocedSet_.erase(val);

    std::vector<uint8_t> expect;
    std::vector<uint8_t> value(SMEM_ALLOC_NUM_BUF_LEN, 0);
    std::vector<uint8_t> old;
    int32_t ret;

    value[val / UINT_BIT] ^= 1U << (val % UINT_BIT);
    do {
        swap(expect, old);
        if (expect.size() != 0) {
            value = expect;
        }
        if ((value[val / UINT_BIT] >> (val % UINT_BIT)) & 1U) {
            value[val / UINT_BIT] ^= 1U << (val % UINT_BIT);
        } else {
            SM_LOG_WARN("key(" << val << ") has released!");
            return SM_OK;
        }
        ret = store_->Cas(SMEM_GROUP_CAS_ALLOC_NUM_KEY, expect, value, old);
    } while (ret == 0 && old == expect);
    return SM_OK;
}
```

### 逐行解读

**GroupBroadcastExit（第 290-301 行）**:
- **功能**: 广播退出状态给所有 rank
- 第 292 行: 设置 EXIT key 为状态码字符串

**RegisterExit（第 303-323 行）**:
- **功能**: 注册退出回调函数
- 第 305-308 行: 检查是否已注册
- 第 309-310 行: 参数验证
- 第 311 行: 保存回调函数
- 第 312-316 行: 监听 EXIT key，设置回调
- 第 317-321 行: 失败处理

**RankExit（第 325-348 行）**:
- **功能**: 退出事件回调
- 第 327 行: 检查结果和回调
- 第 328-331 行: 检查值非空
- 第 333-343 行: 字符串转 int
  - 第 334 行: string 转 long
  - 第 335-338 行: 范围检查
  - 第 339 行: 转为 int
  - 第 340-343 行: 异常处理
- 第 344 行: 调用用户回调

**AllocNumber（第 536-564 行）**:
- **功能**: 使用 CAS 分配一个唯一编号
- 第 538-541 行: 定义 CAS 循环变量
- 第 543-561 行: CAS 循环
  - 第 544 行: 交换 expect 和 old
  - 第 545-547 行: 如果有期望值，使用它
  - 第 549-555 行: 查找第一个空闲位
  - 第 556-559 行: 无空闲编号错误
  - 第 560 行: 执行 CAS 操作
  - 第 561 行: 继续直到成功
- 第 562 行: 记录已分配
- 第 563 行: 返回编号

**ReleaseNumber（第 566-594 行）**:
- **功能**: 释放编号
- 第 568-571 行: 检查编号是否已分配
- 第 572 行: 从集合移除
- 第 574-593 行: CAS 循环清除位
  - 第 579 行: 预设清除对应位
  - 第 585-590 行: 如果位未设置，说明已释放
  - 第 591 行: CAS 操作

---

## 九、smem_net_group_engine.cpp 逐行解读（第六部分：事件监听和动态组）

### 第六部分：事件监听（第 596-858 行）

```cpp
bool SmemNetGroupEngine::ReWatch()
{
    uint32_t wid;
    auto ret = store_->Watch(SMEM_GROUP_LISTEN_EVENT_KEY,
                             std::bind(&SmemNetGroupEngine::GroupWatchCb, this, std::placeholders::_1,
                                       std::placeholders::_2, std::placeholders::_3),
                             wid);
    if (ret != SM_OK) {
        SM_LOG_WARN_LIMIT("group watch failed, ret: " << ret);
        if (listenLinkStatusWatchId_.load() > 0) {
            store_->Unwatch(listenLinkStatusWatchId_.load());
            listenLinkStatusWatchId_.store(UINT32_MAX);
        }
        usleep(SMEM_GROUP_SLEEP_TIMEOUT);
        return true;
    }
    SM_LOG_INFO("Watch group listen successfully, wid: " << wid);
    listenCtx_.watchId = wid;
    listenCtx_.ret = SM_OK;
    if (listenLinkStatusWatchId_.load() == UINT32_MAX) {
        ret = store_->Watch(
            WatchRankType::WATCH_RANK_LINK_DOWN,
            [this](WatchRankType type, uint32_t downRankId) { RemoteRankLinkDownCb(downRankId); }, wid);
        if (ret != SM_OK) {
            SM_LOG_WARN_LIMIT("group watch failed, ret: " << ret);
            store_->Unwatch(listenCtx_.watchId);
            listenCtx_.watchId = UINT32_MAX;
            usleep(SMEM_GROUP_SLEEP_TIMEOUT);
            return true;
        }
        listenLinkStatusWatchId_.store(wid);
        SM_LOG_INFO("Watch link down event successfully, wid: " << wid);
    }
    return false;
}

void SmemNetGroupEngine::GroupListenEvent()
{
    std::string getVal;
    std::string prevEvent;

    listenThreadStarted_ = true;
    while (!groupStoped_.load()) {
        if (!joined_) {
            usleep(SMEM_GROUP_SLEEP_TIMEOUT);
            continue;
        }

        if (listenCtx_.watchId == UINT32_MAX) {
            if (ReWatch()) {
                continue;
            }
        }

        int contextRet = SM_OK;
        std::list<GroupEvent> currentEvents;
        auto ret = listenSignal_.TimedwaitMillsecs(SMEM_GROUP_LISTER_TIMEOUT, [this, &contextRet, &currentEvents]() {
            currentEvents = std::move(listenCtx_.events);
            contextRet = listenCtx_.ret;
        });

        if (groupStoped_.load()) {
            break;
        }

        if (ret != SM_OK) {
            continue;
        }

        if (contextRet != SM_OK) {
            store_->Unwatch(listenCtx_.watchId);
            listenCtx_.watchId = UINT32_MAX;
            store_->Unwatch(listenLinkStatusWatchId_.load());
            listenLinkStatusWatchId_.store(UINT32_MAX);
            continue;
        }

        if (!joined_) { // maybe has leaved
            continue;
        }

        for (auto &event : currentEvents) {
            std::unique_lock<std::mutex> uniqueLock{groupEventHandleMutex_};
            if (event.remoteRankId != option_.rank) {
                uniqueLock.unlock();
            }
            if (event.eventType == GroupEventType::LUNCH_JOIN_LEAVE_EVENT) {
                JoinLeaveEventProcess(event.value, prevEvent);
            } else if (event.eventType == GroupEventType::REMOTE_DOWN_EVENT) {
                RankLinkDownEventProcess(event.remoteRankId, prevEvent);
            } else {
                SM_LOG_ERROR("unknown group event type: " << static_cast<uint32_t>(event.eventType));
            }
        }
    }
    listenThreadStarted_ = false;
}
```

### 逐行解读

**ReWatch（第 596-630 行）**:
- **功能**: 重新建立监听
- 第 598-602 行: 监听 EVENT key
- 第 603-611 行: 失败处理
  - 取消链路监听
  - 睡眠后返回 true（需要重试）
- 第 613-615 行: 成功，保存 watch ID
- 第 616-628 行: 监听链路下线事件
- 第 629 行: 返回 false（无需重试）

**GroupListenEvent（第 632-692 行）**:
- **功能**: 事件监听线程主循环
- 第 634-635 行: 局部变量
- 第 637 行: 标记线程已启动
- 第 638-642 行: 主循环，未加入时睡眠
- 第 644-648 行: 需要重新监听
- 第 650-655 行: 等待事件（带超时）
- 第 657-659 行: 检查停止标志
- 第 661-663 行: 超时继续
- 第 665-671 行: 错误处理，取消监听
- 第 673-675 行: 再次检查是否已加入
- 第 677-689 行: 处理事件列表
  - 第 678 行: 加锁
  - 第 679-681 行: 非本地 rank 事件提前解锁
  - 第 682-688 行: 分发事件

**JoinLeaveEventProcess（第 694-732 行）**:
- **功能**: 处理加入/退出事件
- 第 696 行: 取消当前监听
- 第 698-702 行: 解析事件值
- 第 704-707 行: 去重检查
- 第 709-718 行: 获取当前组大小并更新版本
- 第 720-731 行: 调用用户回调

**RankLinkDownEventProcess（第 734-786 行）**:
- **功能**: 处理 rank 下线事件
- 第 736 行: 断言存储有效
- 第 738 行: 构造事件值字符串
- 第 739 行: 获取当前事件值
- 第 740-743 行: 错误处理
- 第 745-748 行: 检查 rank 是否已加入
- 第 751-765 行: 处理当前有事件的情况
- 第 767-773 行: CAS 清除事件
- 第 781-785 行: 无当前事件，直接更新
- 第 785 行: 清除 bitmap

**LinkDownUpdateMeta（第 788-823 行）**:
- **功能**: 更新元数据
- 第 791-796 行: 获取当前动态大小
- 第 798-800 行: 分离版本和大小
- 第 801-806 行: 版本不一致时的处理
- 第 807-821 行: 版本一致时 CAS 更新
- 第 822 行: 调用用户退出回调

**GroupWatchCb（第 825-847 行）**:
- **功能**: 监听回调
- 第 828-832 行: 检查结果
- 第 834-837 行: 检查 key
- 第 839-846 行: 加锁添加事件

**RemoteRankLinkDownCb（第 849-858 行）**:
- **功能**: 远程 rank 下线回调
- 第 852-857 行: 加锁添加下线事件

---

## 十、smem_net_group_engine.cpp 逐行解读（第七部分：bitmap 和组操作）

### 第七部分：Bitmap 和组操作（第 860-1109 行）

```cpp
void SmemNetGroupEngine::ClearBitmapForRank(uint32_t rankId)
{
    if (rankId >= MAX_RANK_COUNT) {
        SM_LOG_ERROR("ClearBitmapForRank invalid rank id: " << rankId);
        return;
    }

    std::unique_lock<std::mutex> uniqueLock{rankBitmapMutex_};
    auto index = rankId / BITS_COUNT_IN_U64;
    auto shift = rankId % BITS_COUNT_IN_U64;
    joinedRanksBitmap_[index] &= ~(1UL << shift);
}

bool SmemNetGroupEngine::TestBitmapForRank(uint32_t rankId) const
{
    if (rankId >= MAX_RANK_COUNT) {
        SM_LOG_ERROR("TestBitmapForRank invalid rank id: " << rankId);
        return false;
    }

    std::unique_lock<std::mutex> uniqueLock{rankBitmapMutex_};
    auto index = rankId / BITS_COUNT_IN_U64;
    auto shift = rankId % BITS_COUNT_IN_U64;

    return ((joinedRanksBitmap_[index] & (1UL << shift)) != 0UL);
}

Result SmemNetGroupEngine::StartListenEvent()
{
    SM_ASSERT_RETURN(store_ != nullptr, SM_INVALID_PARAM);
    SM_ASSERT_RETURN(listenSignal_.Initialize() == SM_OK, SM_ERROR);

    uint32_t wid = 0;
    auto ret = store_->Watch(
        WatchRankType::WATCH_RANK_LINK_DOWN,
        [this](WatchRankType type, uint32_t downRankId) { RemoteRankLinkDownCb(downRankId); }, wid);
    SM_ASSERT_RETURN(ret == SM_OK, ret);
    listenLinkStatusWatchId_.store(wid);

    std::thread th(&SmemNetGroupEngine::GroupListenEvent, this);
    while (!listenThreadStarted_) {
        usleep(SMEM_GROUP_SLEEP_TIMEOUT);
    }
    listenThread_ = std::move(th);
    return SM_OK;
}

Result SmemNetGroupEngine::GroupJoin()
{
    SM_ASSERT_RETURN(store_ != nullptr, SM_INVALID_PARAM);
    SM_ASSERT_RETURN(option_.dynamic, SM_INVALID_PARAM);
    std::unique_lock<std::mutex> uniqueLock{groupEventHandleMutex_};
    if (joined_) {
        return SM_OK;
    }
    std::string old;
    std::string val = "J" + std::to_string(option_.rank);
    int retry_count = 0;
    static constexpr int MAX_RETRY = 100000;
    while (retry_count++ < MAX_RETRY) {
        auto ret = store_->Cas(SMEM_GROUP_LISTEN_EVENT_KEY, "", val, old);
        if (ret == SM_OK && (old.empty() || old == val)) {
            break;
        }
        usleep(SMEM_GROUP_SLEEP_TIMEOUT);
    }
    int64_t tmp;
    auto ret = store_->Add(SMEM_GROUP_DYNAMIC_SIZE_KEY, 0, tmp);
    if (ret != SM_OK) {
        SM_LOG_ERROR("get group dynamic size failed, ret: " << ret);
        goto join_exit;
    }
    GroupSnClean();
    UpdateGroupVersion(SplitSizeAndVersion(tmp).first + 1);
    option_.rankSize = static_cast<uint32_t>(SplitSizeAndVersion(tmp).second + 1);
    if (option_.joinCb != nullptr) {
        ret = option_.joinCb(option_.rank);
        if (ret != SM_OK) {
            SM_LOG_ERROR("call join func failed, ret: " << ret);
            goto join_exit;
        }
    }
    ret = store_->Add(SMEM_GROUP_DYNAMIC_SIZE_KEY, 1LL << GROUP_DYNAMIC_SIZE_BIT_LEN | 1, tmp);
    if (ret != SM_OK) {
        SM_LOG_ERROR("update group dynamic size failed, ret: " << ret);
    }

join_exit:
    auto ret2 = store_->Remove(SMEM_GROUP_LISTEN_EVENT_KEY);
    if (ret2 != SM_OK) {
        SM_LOG_ERROR("reset group event failed, ret: " << ret2);
    }

    if ((ret | ret2) == SM_OK) {
        joined_ = true;
        return SM_OK;
    }
    return SM_ERROR;
}

Result SmemNetGroupEngine::GroupLeave()
{
    SM_ASSERT_RETURN(store_ != nullptr, SM_INVALID_PARAM);
    SM_ASSERT_RETURN(option_.dynamic, SM_INVALID_PARAM);
    std::unique_lock<std::mutex> uniqueLock{groupEventHandleMutex_};
    SM_ASSERT_RETURN(joined_, SM_NOT_STARTED);

    Result ret;
    uint32_t watchId = 0;
    listenSignal_.OperateInLock(
        [&watchId, this]() {
            watchId = listenCtx_.watchId;
            groupStoped_ = true;
        },
        true);
    ret = store_->Unwatch(watchId);
    if (ret != SM_OK) {
        SM_LOG_ERROR("unwatch id: " << watchId << " failed: " << ret);
    }
    std::string old;
    std::string val = "L" + std::to_string(option_.rank);
    int retry_count = 0;
    static constexpr int MAX_RETRY = 100000;
    while (retry_count++ < MAX_RETRY) {
        ret = store_->Cas(SMEM_GROUP_LISTEN_EVENT_KEY, "", val, old);
        if (ret == SM_OK && (old.empty() || old == val)) {
            break;
        }
        usleep(SMEM_GROUP_SLEEP_TIMEOUT);
    }

    if (option_.leaveCb != nullptr) {
        ret = option_.leaveCb(option_.rank);
        if (ret != SM_OK) {
            SM_LOG_ERROR("call join func failed, ret: " << ret);
            goto leave_exit;
        }
    }
    int64_t tmpVal;
    ret = store_->Add(SMEM_GROUP_DYNAMIC_SIZE_KEY, GROUP_DYNAMIC_SIZE_BIT_MASK, tmpVal);
    if (ret != SM_OK) {
        SM_LOG_ERROR("update group dynamic size failed, ret: " << ret);
    }
    GroupSnClean();
    UpdateGroupVersion(SplitSizeAndVersion(tmpVal).first + 1);

leave_exit:
    auto ret2 = store_->Remove(SMEM_GROUP_LISTEN_EVENT_KEY);
    if (ret2 != SM_OK) {
        SM_LOG_ERROR("reset group event failed, ret: " << ret2);
    }

    joined_ = false;
    return (ret | ret2) == SM_OK ? SM_OK : SM_ERROR;
}

void SmemNetGroupEngine::UpdateGroupVersion(int32_t ver)
{
    groupVersion_ = ver;
    allGatherGroupSn_ = 0;
    barrierGroupSn_ = 0;
    SM_LOG_DEBUG("[DEBUG]Update version(" << SMEM_GROUP_DYNAMIC_SIZE_KEY << ") ver:" << " local:" << option_.rank);
}

void SmemNetGroupEngine::SetBitmapFromRanks(const std::vector<uint32_t> &rankIds)
{
    uint64_t tempBitmap[RANK_BITS_U64_COUNT];
    bzero(tempBitmap, sizeof(tempBitmap));
    for (auto rankId : rankIds) {
        if (rankId >= MAX_RANK_COUNT) {
            SM_LOG_ERROR("AddRanksToBitmap invalid rank id: " << rankId);
            continue;
        }

        auto index = rankId / BITS_COUNT_IN_U64;
        auto shift = rankId % BITS_COUNT_IN_U64;
        tempBitmap[index] |= (1UL << shift);
    }

    std::unique_lock<std::mutex> uniqueLock{rankBitmapMutex_};
    for (auto i = 0U; i < RANK_BITS_U64_COUNT; i++) {
        joinedRanksBitmap_[i] = tempBitmap[i];
    }
}

int32_t SmemNetGroupEngine::LinkReconnectHandler()
{
    uint32_t wid = 0;
    auto ret = store_->Watch(
        WatchRankType::WATCH_RANK_LINK_DOWN,
        [this](WatchRankType type, uint32_t downRankId) { RemoteRankLinkDownCb(downRankId); }, wid);
    if (ret != SM_OK) {
        SM_LOG_WARN("Failed to watch rank link status, ret: " << ret);
    } else {
        SM_LOG_INFO("Watch link down event successful wid: " << wid);
        listenLinkStatusWatchId_.store(wid);
    }

    int64_t tmpVal = 0L;
    ret = store_->Add(SMEM_GROUP_DYNAMIC_SIZE_KEY, 0L, tmpVal);
    if (ret != SM_OK) {
        SM_LOG_ERROR("get group dynamic size failed, ret: " << ret);
        return ret;
    }

    auto version = groupVersion_;
    auto rankSize = option_.rankSize;
    auto newVal = MergeSizeAndVersion(version, rankSize);
    auto oldValStr = std::to_string(tmpVal);
    auto newValStr = std::to_string(newVal);
    std::string existStr;
    SM_LOG_DEBUG("[DEBUG]Try cas for key(" << SMEM_GROUP_DYNAMIC_SIZE_KEY << ") version: " << std::hex << version
                                           << ", rankSize:" << rankSize << ", oldVar:" << tmpVal);
    ret = store_->Cas(SMEM_GROUP_DYNAMIC_SIZE_KEY, oldValStr, newValStr, existStr);
    if (ret != SM_OK) {
        SM_LOG_WARN("CAS for key(" << SMEM_GROUP_DYNAMIC_SIZE_KEY << ") failed: " << ret);
    } else {
        StrUtil::String2Int(existStr, newVal);
        auto pair = SplitSizeAndVersion(newVal);
        SM_LOG_INFO("Cas for key(" << SMEM_GROUP_DYNAMIC_SIZE_KEY << ") version: " << version
                                   << ", rankSize:" << rankSize << ", oldVar: " << pair.first << "_" << pair.second);
    }
    return SM_OK;
}

void SmemNetGroupEngine::GroupSnClean()
{
    for (uint32_t i = 0; i < REMOVE_INTERVAL; i++) {
        if (allGatherGroupSn_ < i) {
            break;
        }
        uint32_t rmAllGatherGroupSn = allGatherGroupSn_ - i;
        std::string removeAddIdx = std::to_string(groupVersion_) + "_" + std::to_string(rmAllGatherGroupSn) + "_GA";
        std::string removeWaitIdx = std::to_string(groupVersion_) + "_" + std::to_string(rmAllGatherGroupSn) + "_GW";
        (void)store_->Remove(removeAddIdx);
        (void)store_->Remove(removeWaitIdx);
    }

    for (uint32_t i = 0; i < REMOVE_INTERVAL; i++) {
        if (barrierGroupSn_ < i) {
            break;
        }
        uint32_t removeBarrierGroupSn = barrierGroupSn_ - i;
        std::string removeAddIdx = std::to_string(groupVersion_) + "_" + std::to_string(removeBarrierGroupSn) + "_BA";
        std::string removeWaitIdx = std::to_string(groupVersion_) + "_" + std::to_string(removeBarrierGroupSn) + "_BW";
        (void)store_->Remove(removeAddIdx);
        (void)store_->Remove(removeWaitIdx);
    }
}
```

### 逐行解读

**ClearBitmapForRank（第 860-871 行）**:
- **功能**: 清除 rank 的 bitmap 位
- 第 862-865 行: 参数检查
- 第 867 行: 加锁
- 第 868 行: 计算 uint64 数组索引
- 第 869 行: 计算位偏移
- 第 870 行: 清除对应位

**TestBitmapForRank（第 873-885 行）**:
- **功能**: 测试 rank 是否在 bitmap 中
- 第 875-878 行: 参数检查
- 第 880 行: 加锁
- 第 881-882 行: 计算索引和偏移
- 第 884 行: 返回位状态

**StartListenEvent（第 887-905 行）**:
- **功能**: 启动事件监听
- 第 889 行: 初始化信号量
- 第 892-895 行: 监听链路下线
- 第 899 行: 创建监听线程
- 第 900-902 行: 等待线程启动
- 第 903 行: 转移线程所有权

**GroupJoin（第 907-958 行）**:
- **功能**: 加入动态组
- 第 909-914 行: 参数检查和状态检查
- 第 916 行: 构造加入值 "J{rankId}"
- 第 917-925 行: CAS 循环获取事件锁
- 第 926-930 行: 获取当前组大小
- 第 932-934 行: 清理序列号并更新版本
- 第 935 行: 更新 rankSize
- 第 936-941 行: 调用用户加入回调
- 第 942 行: 增加组大小（版本+1，大小+1）
- 第 947-957 行: 清理事件 key，设置 joined 标志

**GroupLeave（第 960-1014 行）**:
- **功能**: 离开动态组
- 第 962-965 行: 参数检查
- 第 967 行: 停止监听
- 第 975 行: 取消监听
- 第 980 行: 构造离开值 "L{rankId}"
- 第 981-989 行: CAS 循环获取事件锁
- 第 991-997 行: 调用用户离开回调
- 第 998-1000 行: 更新元数据
- 第 1012 行: 清除 joined 标志

**UpdateGroupVersion（第 1016-1022 行）**:
- **功能**: 更新组版本，重置序列号
- 第 1018 行: 更新版本号
- 第 1019 行: 重置 AllGather 序列号
- 第 1020 行: 重置 Barrier 序列号

**SetBitmapFromRanks（第 1024-1043 行）**:
- **功能**: 从 rank ID 列表设置 bitmap
- 第 1026 行: 清空临时 bitmap
- 第 1028-1037 行: 遍历设置每个 rank 的位
- 第 1039 行: 加锁
- 第 1040-1042 行: 复制到成员变量

**LinkReconnectHandler（第 1045-1083 行）**:
- **功能**: 重连处理回调
- 第 1047-1056 行: 重新监听链路下线
- 第 1058-1063 行: 获取当前组大小
- 第 1065-1073 行: CAS 更新组大小
- 第 1074-1081 行: 记录结果

**GroupSnClean（第 1085-1108 行）**:
- **功能**: 清理最近的序列号 key
- 第 1087-1096 行: 清理 AllGather key
- 第 1098-1107 行: 清理 Barrier key

---

## 总结

smem/net 模块实现了完整的分布式组通信功能：

### 核心特性

1. **Barrier（屏障同步）**:
   - 基于 Add + Get 实现
   - 第一个 rank 负责清理旧 key
   - 最后一个 rank 设置完成标记
   - 所有 rank 等待完成标记

2. **AllGather（全收集）**:
   - 基于 Append 实现
   - 数据前缀包含 rank ID 用于排序
   - 最后一个 rank 设置完成标记
   - 接收后按 rank ID 排序

3. **动态组管理**:
   - 支持运行时加入/退出
   - 使用 CAS 保证事件串行化
   - 版本号机制处理并发变更
   - bitmap 跟踪已加入 rank

4. **故障处理**:
   - 链路下线监听
   - 重连后自动恢复
   - CAS 保证元数据一致性

### 设计亮点

- 使用 ConfigStore 作为同步原语，支持多种后端
- 版本号机制处理动态组成员变更
- bitmap 高效跟踪大量 rank 状态
- 分离序列号支持用户自定义组操作
- 性能追踪内置，便于调试优化
