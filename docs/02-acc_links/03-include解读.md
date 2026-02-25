# acc_links 模块 include 头文件解读

## 文件清单

| 文件 | 行数 | 功能描述 |
|------|------|----------|
| [acc_def.h](../../src/acc_links/include/acc_def.h) | 183 | 公共定义和数据结构 |
| [acc_log.h](../../src/acc_links/include/acc_log.h) | 51 | 日志接口 |
| [acc_ref.h](../../src/acc_links/include/acc_ref.h) | 181 | 引用计数和智能指针 |
| [acc_tcp_link.h](../../src/acc_links/include/acc_tcp_link.h) | 264 | TCP 链路接口 |
| [acc_tcp_server.h](../../src/acc_links/include/acc_tcp_server.h) | 185 | TCP 服务器接口 |
| [acc_tcp_request_context.h](../../src/acc_links/include/acc_tcp_request_context.h) | ~80 | 请求上下文接口 |
| [acc_tcp_shared_buf.h](../../src/acc_links/include/acc_tcp_shared_buf.h) | ~100 | 共享缓冲区接口 |

---

## 1. acc_def.h

### 文件信息
- **文件路径**: [src/acc_links/include/acc_def.h](../../src/acc_links/include/acc_def.h)
- **代码行数**: 183 行
- **主要功能**: 公共定义、常量、数据结构和类型别名

### 完整代码与逐行解读

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
```
**解读**:
- 第 1-11 行: 版权声明和许可证信息

```cpp
#ifndef ACC_LINKS_ACC_DEF_H
#define ACC_LINKS_ACC_DEF_H
```
**解读**:
- 第 12-13 行: 头文件保护宏

```cpp
#include <atomic>
#include <cstdint>
#include <functional>
#include <set>
#include <string>
#include <sstream>
#include <thread>

#include "acc_ref.h"
#include "acc_log.h"
```
**解读**:
- 第 15-22 行: 引入标准库头文件
  - `<atomic>`: 原子操作支持
  - `<cstdint>`: 整数类型定义
  - `<functional>`: 函数对象和 std::function
  - `<set>`: 集合容器
  - `<thread>`: 线程支持
- 第 23-24 行: 引入项目内部头文件

```cpp
namespace ock {
namespace acc {
```
**解读**:
- 第 26-27 行: 定义命名空间 `ock::acc`

```cpp
constexpr uint32_t MAX_RECV_BODY_LEN = 10 * 1024 * 1024; /* max receive body len limit */
constexpr uint32_t UNO_1024 = 1024;
constexpr uint32_t UNO_1000 = 1000;
constexpr uint32_t UNO_500 = 500;
constexpr uint32_t UNO_256 = 256;
constexpr uint32_t UNO_128 = 128;
constexpr uint32_t UNO_100 = 100;
constexpr uint32_t UNO_48 = 48;
constexpr uint32_t UNO_32 = 32;
constexpr uint32_t UNO_16 = 16;
constexpr uint32_t UNO_7 = 7;
constexpr uint32_t UNO_2 = 2;
constexpr uint32_t UNO_1 = 1;
```
**解读**:
- 第 28-40 行: 定义常量
  - `MAX_RECV_BODY_LEN`: 最大接收消息体长度 10MB
  - `UNO_*` 系列: 各种常用数值常量（UNO 可能代表 "Uno Number"）

```cpp
/**
 * @brief Header of connecting to server
 */
struct AccConnReq {
    int16_t magic = 0;
    int16_t version = 0;
    uint64_t rankId = 0;
};
```
**解读**:
- 第 42-49 行: `AccConnReq` 连接请求结构体
  - 用于客户端连接到服务器时携带的握手信息
  - `magic`: 魔数，用于验证连接类型
  - `version`: 协议版本
  - `rankId`: 节点 ID，标识发起连接的节点

```cpp
/**
 * @brief Response of connecting
 */
struct AccConnResp {
    int16_t result = 0;
};
```
**解读**:
- 第 51-56 行: `AccConnResp` 连接响应结构体
  - 服务器对连接请求的响应
  - `result`: 连接结果码

```cpp
/**
 * @brief Result of message sending
 */
enum AccMsgSentResult {
    MSG_SENT = 0,
    MSG_TIMEOUT = 1,
    MSG_LINK_BROKEN = 2,
    /* add error code ahead of this */
    MSG_BUTT,
};
```
**解读**:
- 第 58-67 行: `AccMsgSentResult` 枚举，消息发送结果
  - `MSG_SENT`: 消息已发送
  - `MSG_TIMEOUT`: 发送超时
  - `MSG_LINK_BROKEN`: 链路已断开
  - `MSG_BUTT`: 枚举边界值

```cpp
/**
 * @brief Header of message
 */
struct AccMsgHeader {
    int16_t type = 0;     /* data type or opCode */
    int16_t result = 0;   /* result for response */
    uint32_t bodyLen = 0; /* length of data */
    uint32_t seqNo = 0;   /* seqNo */
    uint32_t crc = 0;     /* reserved crc */

    AccMsgHeader() = default;

    AccMsgHeader(int16_t t, uint32_t bLen, uint32_t sno) : type(t), bodyLen(bLen), seqNo(sno) {}

    AccMsgHeader(int16_t t, int16_t r, uint32_t bLen, uint32_t sno) : type(t), result(r), bodyLen(bLen), seqNo(sno) {}

    std::string ToString() const
    {
        std::ostringstream oss;
        oss << "type: " << type << ", result: " << result << ", bodyLen: " << bodyLen << ", seqNo: " << seqNo
            << ", crc: " << crc;
        return oss.str();
    }
};
```
**解读**:
- 第 69-92 行: `AccMsgHeader` 消息头结构体
  - 第 73-77 行: 成员变量
    - `type`: 消息类型或操作码
    - `result`: 响应结果码
    - `bodyLen`: 消息体长度
    - `seqNo`: 序列号，用于消息排序
    - `crc`: CRC 校验和（预留）
  - 第 79 行: 默认构造函数
  - 第 80-81 行: 请求消息构造函数
  - 第 82-83 行: 响应消息构造函数
  - 第 84-91 行: `ToString()` 方法，用于调试输出

```cpp
/**
 * @brief Options of Tcp Server, required when start a tcp server
 */
struct AccTcpServerOptions {
    std::string listenIp;                    /* listen ip */
    uint16_t listenPort = 9966L;             /* listen port */
    uint16_t workerCount = UNO_2;            /* number of worker threads */
    int16_t workerThreadPriority = 0;        /* priority of worker threads */
    int16_t workerPollTimeoutMs = UNO_500;   /* epoll timeout */
    int16_t workerStartCpuId = -1;           /* start cpu id of workers */
    uint16_t linkSendQueueSize = UNO_128;    /* send queue size */
    uint16_t keepaliveIdleTime = UNO_32;     /* tcp keepalive idle time */
    uint16_t keepaliveProbeTimes = UNO_7;    /* tcp keepalive probe times */
    uint16_t keepaliveProbeInterval = UNO_2; /* tcp keepalive probe interval */
    bool reusePort = true;                   /* reuse listen port */
    bool enableListener = false;             /* start listener or not */
    int16_t magic = 0;                       /* magic number of  */
    int16_t version = 0;                     /* version */
    uint32_t maxWorldSize = UNO_1024;        /* max client number */
};
```
**解读**:
- 第 94-113 行: `AccTcpServerOptions` TCP 服务器配置选项
  - 第 97 行: 监听 IP 地址
  - 第 98 行: 监听端口，默认 9966
  - 第 99 行: 工作线程数，默认 2
  - 第 100 行: 工作线程优先级
  - 第 101 行: epoll 超时时间（毫秒），默认 500ms
  - 第 102 行: 工作线程绑定的 CPU ID，-1 表示不绑定
  - 第 103 行: 链路发送队列大小
  - 第 104-106 行: TCP keepalive 配置
    - 空闲时间、探测次数、探测间隔
  - 第 107 行: 是否复用端口
  - 第 108 行: 是否启用监听器
  - 第 109-110 行: 魔数和版本号
  - 第 111 行: 最大客户端连接数

```cpp
/**
 * @brief Callback function of private key password decryptor, see @RegisterDecryptHandler
 *
 * @param cipherText       [in] the encrypted text(private key password)
 * @param cipherTextLen    [in] the length of cipherText
 * @param plainText        [out] the decrypted text(private key password)
 * @param plaintextLen     [out] the length of plainText
 */
using AccDecryptHandler =
    std::function<int(const char *cipherText, size_t cipherTextLen, char *plainText, size_t plainTextLen)>;
```
**解读**:
- 第 115-124 行: `AccDecryptHandler` 类型定义
  - 用于解密私钥密码的回调函数类型
  - 参数：密文、密文长度、明文缓冲区、明文长度
  - 返回值：int，0 表示成功

```cpp
/**
 * @brief Tls related option, required if TLS enabled
 */
struct AccTlsOption {
    bool enableTls = false;
    std::string tlsTopPath;           /* root path of certifications */
    std::string tlsCert;              /* certification of server */
    std::string tlsCrlPath;           /* optional, crl file path */
    std::string tlsCaPath;            /* ca file path */
    std::set<std::string> tlsCaFile;  /* paths of ca */
    std::set<std::string> tlsCrlFile; /* path of crl file */
    std::string tlsPk;                /* private key */
    std::string tlsPkPwd;             /* private key password, required, encrypt or plain both allowed */

    AccTlsOption() : enableTls(false) {}
};
```
**解读**:
- 第 126-141 行: `AccTlsOption` TLS 配置选项
  - 第 128 行: 是否启用 TLS
  - 第 129 行: 证书根目录路径
  - 第 130 行: 服务器证书
  - 第 131 行: CRL（证书撤销列表）路径
  - 第 132 行: CA 文件路径
  - 第 133 行: CA 文件集合（支持多个）
  - 第 134 行: CRL 文件集合
  - 第 135 行: 私钥
  - 第 136 行: 私钥密码（加密或明文）
  - 第 137 行: 默认构造函数，禁用 TLS

```cpp
/**
 * @brief Result codes
 */
enum AccResult {
    ACC_OK = 0,
    ACC_ERROR = -1,
    ACC_NEW_OBJECT_FAIL = -2,
    ACC_MALLOC_FAIL = -3,
    ACC_INVALID_PARAM = -4,
    ACC_NOT_INITIALIZED = -5,
    ACC_TIMEOUT = -6,
    ACC_CONNECTION_NOT_READY = -7,
    ACC_EPOLL_ERROR = -8,
    ACC_LINK_OPTION_ERROR = -9,
    ACC_QUEUE_IS_FULL = -10,
    ACC_LINK_ERROR = -11,
    ACC_LINK_EAGAIN = -12,
    ACC_LINK_MSG_READY = -13,
    ACC_LINK_MSG_SENT = -14,
    ACC_LINK_MSG_INVALID = -15,
    ACC_LINK_NEED_RECONN = -16,
    ACC_LINK_ADDRESS_IN_USE = -17,
    ACC_RESULT_BUTT = -18,
};
```
**解读**:
- 第 143-166 行: `AccResult` 错误码枚举
  - `ACC_OK`: 成功
  - `ACC_ERROR`: 一般错误
  - `ACC_NEW_OBJECT_FAIL`: 对象创建失败
  - `ACC_MALLOC_FAIL`: 内存分配失败
  - `ACC_INVALID_PARAM`: 无效参数
  - `ACC_NOT_INITIALIZED`: 未初始化
  - `ACC_TIMEOUT`: 超时
  - `ACC_CONNECTION_NOT_READY`: 连接未就绪
  - `ACC_EPOLL_ERROR`: epoll 错误
  - `ACC_LINK_OPTION_ERROR`: 链路选项错误
  - `ACC_QUEUE_IS_FULL`: 队列已满
  - `ACC_LINK_ERROR`: 链路错误
  - `ACC_LINK_EAGAIN`: 需要重试（EAGAIN）
  - `ACC_LINK_MSG_READY`: 消息就绪
  - `ACC_LINK_MSG_SENT`: 消息已发送
  - `ACC_LINK_MSG_INVALID`: 无效消息
  - `ACC_LINK_NEED_RECONN`: 需要重连
  - `ACC_LINK_ADDRESS_IN_USE`: 地址已被占用
  - `ACC_RESULT_BUTT`: 边界值

```cpp
class AccDataBuffer;
class AccTcpServer;
class AccTcpLink;
class AccTcpRequestContext;
class AccTcpLinkComplex;
using AccDataBufferPtr = AccRef<AccDataBuffer>;
using AccTcpServerPtr = AccRef<AccTcpServer>;
using AccTcpLinkPtr = AccRef<AccTcpLink>;
using AccTcpLinkComplexPtr = AccRef<AccTcpLinkComplex>;

#define ACC_API __attribute__((visibility("default")))
```
**解读**:
- 第 168-176 行: 前向声明和类型别名
  - 声明各个类
  - 定义智能指针类型别名，基于 `AccRef`
- 第 178 行: `ACC_API` 宏
  - 将函数标记为默认可见，用于动态库导出

```cpp
} // namespace acc
} // namespace ock

#endif // ACC_LINKS_ACC_DEF_H
```
**解读**:
- 第 179-182 行: 命名空间结束和头文件保护结束

---

## 2. acc_log.h

### 文件信息
- **文件路径**: [src/acc_links/include/acc_log.h](../../src/acc_links/include/acc_log.h)
- **代码行数**: 51 行
- **主要功能**: 日志接口定义

### 完整代码与逐行解读

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
 */
#ifndef ACC_LINKS_ACC_LOG_H
#define ACC_LINKS_ACC_LOG_H

#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Set external log function, user can set customized logger function...
 */
int32_t AccSetExternalLog(void (*func)(int level, const char *msg));

/**
 * @brief Set log level
 * ...
 */
int32_t AccSetLogLevel(int level);

#ifdef __cplusplus
}
#endif

#endif // ACC_LINKS_ACC_LOG_H
```

**解读**:
- 提供 C 接口的日志函数
- `AccSetExternalLog`: 设置外部日志函数，允许用户自定义日志输出
- `AccSetLogLevel`: 设置日志级别（0-3）

---

## 3. acc_ref.h

### 文件信息
- **文件路径**: [src/acc_links/include/acc_ref.h](../../src/acc_links/include/acc_ref.h)
- **代码行数**: 181 行
- **主要功能**: 引用计数和智能指针实现

### 完整代码与逐行解读

```cpp
class AccReferable {
public:
    AccReferable() = default;
    virtual ~AccReferable() = default;

    inline void IncreaseRef()
    {
        __sync_fetch_and_add(&mRefCount, 1);
    }

    inline void DecreaseRef()
    {
        // delete itself if reference count equal to 0
        if (__sync_sub_and_fetch(&mRefCount, 1) == 0) {
            delete this;
        }
    }

protected:
    int32_t mRefCount = 0;
};
```
**解读**:
- 第 25-45 行: `AccReferable` 可引用对象基类
  - 第 27-28 行: 默认构造函数
  - 第 29 行: 虚析构函数
  - 第 30-33 行: `IncreaseRef()` 增加引用计数
    - 使用 `__sync_fetch_and_add` 原子操作
  - 第 34-41 行: `DecreaseRef()` 减少引用计数
    - 如果引用计数变为 0，自动删除对象
  - 第 43-44 行: 引用计数成员

```cpp
template<typename T>
class AccRef {
public:
    AccRef() noexcept = default;

    AccRef(T *newObj) noexcept
    {
        if (newObj != nullptr) {
            newObj->IncreaseRef();
            mObj = newObj;
        }
    }

    AccRef(const AccRef<T> &other) noexcept
    {
        if (other.mObj != nullptr) {
            other.mObj->IncreaseRef();
            mObj = other.mObj;
        }
    }

    AccRef(AccRef<T> &&other) noexcept : mObj(std::__exchange(other.mObj, nullptr))
    {
        // move constructor
    }

    ~AccRef()
    {
        if (mObj != nullptr) {
            mObj->DecreaseRef();
        }
    }
```
**解读**:
- 第 50-89 行: `AccRef` 智能指针类
  - 第 54 行: 默认构造函数
  - 第 56-65 行: 指针构造函数，增加新对象的引用计数
  - 第 67-75 行: 拷贝构造函数，增加源对象的引用计数
  - 第 77-80 行: 移动构造函数，使用 `std::__exchange` 转移所有权
  - 第 82-89 行: 析构函数，减少引用计数

```cpp
    inline AccRef<T> &operator=(T *newObj)
    {
        this->Set(newObj);
        return *this;
    }

    inline AccRef<T> &operator=(const AccRef<T> &other)
    {
        if (this != &other) {
            this->Set(other.mObj);
        }
        return *this;
    }

    AccRef<T> &operator=(AccRef<T> &&other) noexcept
    {
        if (this != &other) {
            auto tmp = mObj;
            mObj = std::__exchange(other.mObj, nullptr);
            if (tmp != nullptr) {
                tmp->DecreaseRef();
            }
        }
        return *this;
    }
```
**解读**:
- 第 91-116 行: 赋值运算符重载
  - 第 92-96 行: 指针赋值
  - 第 98-104 行: 拷贝赋值
  - 第 106-116 行: 移动赋值

```cpp
    inline bool operator==(const AccRef<T> &other) const
    {
        return mObj == other.mObj;
    }

    inline T *operator->() const
    {
        return mObj;
    }

    inline T *Get() const
    {
        return mObj;
    }

    inline void Set(T *newObj)
    {
        if (newObj == mObj) {
            return;
        }

        if (newObj != nullptr) {
            newObj->IncreaseRef();
        }

        if (mObj != nullptr) {
            mObj->DecreaseRef();
        }

        mObj = newObj;
    }

private:
    T *mObj = nullptr;
};
```
**解读**:
- 第 118-169 行: 比较运算符、箭头运算符、Get 和 Set 方法

```cpp
template<class Src, class Des>
static AccRef<Des> AccConvert(const AccRef<Src> &child)
{
    if (child.Get() != nullptr) {
        return AccRef<Des>(static_cast<Des *>(child.Get()));
    }
    return nullptr;
}
```
**解读**:
- 第 171-178 行: `AccConvert` 智能指针转换函数模板
  - 使用 `static_cast` 进行类型转换
  - 自动管理引用计数

---

## 4. acc_tcp_link.h

### 文件信息
- **文件路径**: [src/acc_links/include/acc_tcp_link.h](../../src/acc_links/include/acc_tcp_link.h)
- **代码行数**: 264 行
- **主要功能**: TCP 链路接口定义

### 主要类

#### AccTcpLink - 基础链路类

```cpp
class ACC_API AccTcpLink : public AccReferable {
public:
    void UpCtx(uint64_t context);              // 设置上层上下文
    uint64_t UpCtx() const;                    // 获取上层上下文
    std::string ShortName() const;             // 获取短名称
    const std::string &GetLinkRemoteIpPort() const;  // 获取对端 IP:Port
    uint32_t Id() const;                        // 获取链路 ID
    bool Established() const;                    // 是否已建立
    bool Break();                               // 断开链路

    // 纯虚函数，需子类实现
    virtual int32_t BlockSend(void *data, uint32_t len) = 0;
    virtual int32_t BlockRecv(void *data, uint32_t demandLen) = 0;
    virtual int32_t PollingInput(int32_t timeoutInMs) const = 0;
    virtual int32_t SetSendTimeout(uint32_t timeoutInUs) const = 0;
    virtual int32_t SetReceiveTimeout(uint32_t timeoutInUs) const = 0;
    virtual int32_t EnableNoBlocking() const = 0;
    virtual void Close() = 0;
    virtual bool IsConnected() const = 0;

protected:
    AccTcpLink(int fd, const std::string &ipPort, uint32_t id);

    int established_;      // 连接状态
    int fd_;               // 文件描述符
    uint64_t upCtx_;       // 上层上下文
    const uint32_t id_;    // 链路 ID
    const std::string ipPort_;  // 对端 IP:Port
};
```

#### AccTcpLinkComplex - 复杂链路类（非阻塞）

```cpp
class ACC_API AccTcpLinkComplex : public AccTcpLink {
public:
    // 非阻塞发送方法
    virtual int32_t NonBlockSend(int16_t msgType, const AccDataBufferPtr &d,
                                  const AccDataBufferPtr &cbCtx) = 0;
    virtual int32_t NonBlockSend(int16_t msgType, uint32_t seqNo, const AccDataBufferPtr &d,
                                  const AccDataBufferPtr &cbCtx) = 0;
    virtual int32_t NonBlockSend(int16_t msgType, int16_t opCode, uint32_t seqNo,
                                  const AccDataBufferPtr &d, const AccDataBufferPtr &cbCtx) = 0;
    virtual int32_t EnqueueAndModifyEpoll(const AccMsgHeader &h, const AccDataBufferPtr &d,
                                          const AccDataBufferPtr &cbCtx) = 0;

protected:
    AccTcpLinkComplex(int fd, const std::string &ipPort, uint32_t id);
};
```

---

## 5. acc_tcp_server.h

### 文件信息
- **文件路径**: [src/acc_links/include/acc_tcp_server.h](../../src/acc_links/include/acc_tcp_server.h)
- **代码行数**: 185 行
- **主要功能**: TCP 服务器接口定义

### 主要回调函数类型

```cpp
// 新连接回调
using AccNewLinkHandler = std::function<int(const AccConnReq &req,
                                            const AccTcpLinkComplexPtr &link)>;

// 新请求回调
using AccNewReqHandler = std::function<int32_t(const AccTcpRequestContext &context)>;

// 请求发送完成回调
using AccReqSentHandler = std::function<int32_t(AccMsgSentResult result,
                                               const AccMsgHeader &header,
                                               const AccDataBufferPtr &cbCtx)>;

// 链路断开回调
using AccLinkBrokenHandler = std::function<int32_t(const AccTcpLinkComplexPtr &link)>;
```

### AccTcpServer 类

```cpp
class ACC_API AccTcpServer : public AccReferable {
public:
    static AccTcpServerPtr Create();  // 工厂方法

    // 启动服务器
    int32_t Start(const AccTcpServerOptions &opt);
    virtual int32_t Start(const AccTcpServerOptions &opt, const AccTlsOption &tlsOption) = 0;

    // 停止服务器
    virtual void Stop() = 0;
    virtual void StopAfterFork() = 0;

    // 连接到对端服务器
    virtual int32_t ConnectToPeerServer(const std::string &peerIp, uint16_t port,
                                         const AccConnReq &req, uint32_t maxRetryTimes,
                                         AccTcpLinkComplexPtr &newLink) = 0;

    // 注册回调
    virtual void RegisterNewRequestHandler(int16_t msgType, const AccNewReqHandler &h) = 0;
    virtual void RegisterRequestSentHandler(int16_t msgType, const AccReqSentHandler &h) = 0;
    virtual void RegisterLinkBrokenHandler(const AccLinkBrokenHandler &h) = 0;
    virtual void RegisterNewLinkHandler(const AccNewLinkHandler &h) = 0;
    virtual void RegisterDecryptHandler(const AccDecryptHandler &h) = 0;

    // 加载动态库
    virtual int32_t LoadDynamicLib(const std::string &dynLibPath) = 0;
};
```

**服务器架构**:
- **Listener**: 接受新连接
- **Workers**: 多个工作线程处理 I/O 事件
- **Connection Manager**: 管理所有连接

---

## 总结

acc_links 模块的公共头文件定义了：

1. **基础类型**: 引用计数、智能指针、结果码
2. **数据结构**: 连接请求/响应、消息头
3. **配置结构**: 服务器选项、TLS 选项
4. **接口定义**: TCP 链路、TCP 服务器
5. **回调函数**: 新连接、新请求、发送完成、链路断开

这些接口为整个 acc_links 模块提供了统一的抽象。
