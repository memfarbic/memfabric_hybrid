# ACC_Links C_SRC 模块逐行解读

## 模块概述

C_SRC 模块是 ACC_Links 的核心实现，包含 TCP 服务器、工作线程、链路管理、监听器等核心组件。该模块实现了基于 epoll 的高并发 TCP 通信框架。

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| acc_tcp_server_default.h/cpp | 681 | 默认 TCP 服务器实现 |
| acc_tcp_link_complex_default.h/cpp | 520 | 复杂链路实现 |
| acc_tcp_worker.h/cpp | - | 工作线程实现 |
| acc_tcp_listener.h/cpp | - | 监听器实现 |
| acc_tcp_request_context.cpp/h | - | 请求上下文 |
| acc_tcp_shared_buf.cpp | - | 共享缓冲区 |
| acc_tcp_common.cpp/h | - | TCP 公共定义 |

---

## 1. acc_tcp_server_default.h/cpp - 默认 TCP 服务器

### 文件信息
- 文件路径: `src/acc_links/csrc/acc_tcp_server_default.h/cpp`
- 代码行数: 681 行
- 主要功能: AccTcpServer 接口的默认实现

### AtmoicRollback 模板类 (行 22-43)

```cpp
template<class T>
class AtmoicRollback {
public:
    AtmoicRollback(std::atomic<T> &value, T failedValue) : value_(value), failedValue_(failedValue) {}

    ~AtmoicRollback()
    {
        if (!success_) {
            value_ = failedValue_;
        }
    }

    void SetSuccess(bool val)
    {
        success_ = val;
    }

private:
    bool success_ = true;
    std::atomic<T> &value_;
    T failedValue_;
};
```

**逐行解读**:
- 第 23 行: 构造函数，接收原子变量和失败值
- 第 27-32 行: 析构函数，失败时回滚值
- 第 34-37 行: 设置成功标志

### AccTcpServerDefault 类定义 (行 79-100)

```cpp
class AccTcpServerDefault : public AccTcpServer {
public:
    AccTcpServerDefault() = default;
    ~AccTcpServerDefault() override;

    Result Start(const AccTcpServerOptions &opt, const AccTlsOption &tlsOption) override;

    Result LoadDynamicLib(const std::string &dynLibPath) override;

    void Stop() override;

    void StopAfterFork() override;

    Result ConnectToPeerServer(const std::string &peerIp, uint16_t port, const AccConnReq &req, uint32_t maxRetryTimes,
                               AccTcpLinkComplexPtr &newLink) override;

    void RegisterNewRequestHandler(int16_t msgType, const AccNewReqHandler &h) override;

    void RegisterRequestSentHandler(int16_t msgType, const AccReqSentHandler &h) override;

    void RegisterLinkBrokenHandler(const AccLinkBrokenHandler &h) override;

    void RegisterNewLinkHandler(const AccNewLinkHandler &h) override;

    void RegisterDecryptHandler(const AccDecryptHandler &h) override;

private:
    AccNewReqHandler newRequestHandle_[UNO_48]{};
    AccReqSentHandler requestSentHandle_[UNO_48]{};
    AccLinkBrokenHandler linkBrokenHandle_ = nullptr;
    AccDecryptHandler decryptHandler_ = nullptr;
    std::vector<AccTcpWorkerPtr> workers_;
    AccTcpListenerPtr listener_;
    std::atomic<uint32_t> nextWorkerIndex_{0};
    std::unordered_map<uint32_t, AccTcpLinkComplexDefaultPtr> connectedLinks_;
    AccNewLinkHandler newLinkHandle_ = nullptr;
    AccTcpLinkDelayCleanupPtr delayCleanup_{nullptr};
    std::mutex linkCntMutex;
    std::unordered_map<uint32_t, uint32_t> workerLinkCnt_;
    uint32_t maxWorkerLinkeCnt_ = UNO_1024;

    std::mutex mutex_;
    std::atomic<bool> started_{false};
    AccTcpServerOptions options_;
    AccTcpSslHelperPtr sslHelper_ = nullptr;
    SSL_CTX *sslCtx_ = nullptr;
    AccTlsOption tlsOption_{};
};
```

**逐行解读**:
- 第 80-81 行: 默认构造函数
- 第 82 行: 虚析构函数
- 第 84-87 行: 公有接口
  - Start - 启动服务器
  - LoadDynamicLib - 加载动态库
  - Stop - 停止服务器
  - StopAfterFork - Fork 后停止
  - ConnectToPeerServer - 连接到对等服务器
  - 注册各种处理器
- 第 80-92 行: 私有成员
  - 处理器数组（48 个消息类型）
  - Worker 列表
  - 监听器
  - 连接映射表
  - 链接计数
  - 同步互斥锁

### Start() - 启动服务器 (行 45-91)

```cpp
Result AccTcpServerDefault::Start(const AccTcpServerOptions &opt, const AccTlsOption &tlsOption)
{
    bool expected = false;
    if (!started_.compare_exchange_strong(expected, true)) {
        return ACC_OK;
    }

    AtmoicRollback<bool> rollback{started_, false};
    rollback.SetSuccess(false);
    options_ = opt;
    tlsOption_ = tlsOption;

    auto result = ValidateOptions();
    LOG_ERROR_RETURN_IT_IF_NOT_OK(result, "Failed to start AccTcpServerDefault as options are invalid");

    maxWorkerLinkeCnt_ = options_.maxWorldSize;

    result = ValidateHandler();
    LOG_ERROR_RETURN_IT_IF_NOT_OK(result, "Failed to start AccTcpServerDefault as handler are invalid");

    result = GenerateSslCtx();
    LOG_ERROR_RETURN_IT_IF_NOT_OK(result, "Failed to generate ssl ctx as " << result);

    result = StartDelayCleanup();
    LOG_ERROR_RETURN_IT_IF_NOT_OK(result, "Failed to start AccTcpServerDefault delay cleanup");

    /* start workers firstly, in case of connecting comes just after listener started */
    result = StartWorkers();
    if (result != ACC_OK) {
        StopAndCleanDelayCleanup();
        StopAndCleanWorkers();
        LOG_ERROR("Failed to start AccTcpServerDefault workers");
        return result;
    }

    /* start listener secondly */
    result = StartListener();
    if (result != ACC_OK) {
        StopAndCleanDelayCleanup();
        StopAndCleanWorkers();
        LOG_ERROR("Failed to start AccTcpServerDefault listener, result: " << result);
        return result;
    }

    rollback.SetSuccess(true);
    return ACC_OK;
}
```

**逐行解读**:
- 第 47-50 行: 原子操作检查是否已启动
- 第 52 行: 创建回滚对象
- 第 53-55 行: 保存配置
- 第 57-58 行: 验证选项
- 第 60 行: 设置最大链接数
- 第 62-63 行: 验证处理器
- 第 65-66 行: 生成 SSL 上下文
- 第 68-69 行: 启动延迟清理
- 第 72-78 行: 启动 Worker 线程
- 第 81-87 行: 启动监听器
- 第 89 行: 设置成功标志

### StartWorkers() - 启动 Worker 线程 (行 232-265)

```cpp
Result AccTcpServerDefault::StartWorkers()
{
    AccTcpWorkerOptions workerOptions;
    workerOptions.threadPriority = options_.workerThreadPriority;
    workerOptions.cpuId = -1;
    workerOptions.pollingTimeoutMs = options_.workerPollTimeoutMs;
    for (uint16_t i = 0; i < options_.workerCount; i++) {
        if (options_.workerStartCpuId != -1) {
            workerOptions.cpuId = options_.workerStartCpuId + i;
        }
        workerOptions.index = i;

        AccTcpWorkerPtr tmpWorker = new (std::nothrow) AccTcpWorker(workerOptions);
        ASSERT_RETURN(tmpWorker.Get() != nullptr, ACC_NEW_OBJECT_FAIL);
        tmpWorker->RegisterNewRequestHandler(
            std::bind(&AccTcpServerDefault::HandleNewRequest, this, std::placeholders::_1));
        tmpWorker->RegisterRequestSentHandler(std::bind(&AccTcpServerDefault::HandleRequestSent, this,
                                                        std::placeholders::_1, std::placeholders::_2,
                                                        std::placeholders::_3));
        tmpWorker->RegisterLinkBrokenHandler(
            std::bind(&AccTcpServerDefault::HandleLinkBroken, this, std::placeholders::_1));
        workers_.push_back(tmpWorker);
    }

    for (auto &item : workers_) {
        auto result = item->Start();
        if (result != ACC_OK) {
            StopAndCleanWorkers();
            return result;
        }
    }

    return ACC_OK;
}
```

**逐行解读**:
- 第 234-237 行: 配置 Worker 选项
- 第 238 行: 循环创建 Worker
- 第 239-241 行: 设置 CPU 亲和性
- 第 244 行: 创建 Worker 对象
- 第 246-252 行: 注册回调处理器
  - 新请求处理器
  - 请求发送处理器
  - 链路断开处理器
- 第 253 行: 添加到列表
- 第 256-262 行: 启动所有 Worker

### HandleNewConnection() - 处理新连接 (行 358-416)

```cpp
Result AccTcpServerDefault::HandleNewConnection(const AccConnReq &req, const AccTcpLinkComplexDefaultPtr &newLink)
{
    ASSERT_RETURN(newLink.Get() != nullptr, ACC_INVALID_PARAM);
    if (req.magic != options_.magic) {
        LOG_ERROR("New link connected but magic mismatched, refuse the link from "
                  << newLink->ShortName() << ", req: " << req.magic << ", options: " << options_.magic
                  << ", listenPort: " << options_.listenPort);
        return ACC_ERROR;
    }

    if (req.version != options_.version) {
        LOG_ERROR("New link connected but version mismatched, refuse the link from " << newLink->ShortName());
        return ACC_ERROR;
    }

    auto workIndex = WorkerSelect();
    if (workIndex == ACC_ERROR) {
        LOG_ERROR("Failed to select available worker.");
        return ACC_ERROR;
    }

    auto &worker = workers_[workIndex];
    auto result = newLink->Initialize(options_.linkSendQueueSize, workIndex, worker.Get());
    if (UNLIKELY(result != ACC_OK)) {
        LOG_ERROR("Failed to initialize the link from " << newLink->ShortName() << ", result " << result);
        return ACC_ERROR;
    }

    result = newLinkHandle_(req, newLink.Get());
    if (UNLIKELY(result != ACC_OK)) {
        return result;
    }

    newLink->EnableNoBlocking();
    {
        /* check and add new link into map */
        std::lock_guard<std::mutex> guard(mutex_);
        if (!started_) {
            LOG_WARN("The server is being destroyed or has been destroyed. can't receive new connection.");
            return ACC_ERROR;
        }
        auto iter = connectedLinks_.find(newLink->Id());
        if (iter != connectedLinks_.end()) {
            LOG_ERROR("Failed to handle new connection as found duplicated link id " << newLink->Id());
            return ACC_ERROR;
        }

        /* added to worker */
        result = worker->AddLink(newLink, EPOLLIN | EPOLLOUT | EPOLLET);
        if (UNLIKELY(result != ACC_OK)) {
            return result;
        }

        /* emplace map */
        connectedLinks_.emplace(newLink->Id(), newLink);
    }

    return ACC_OK;
}
```

**逐行解读**:
- 第 360-361 行: 参数校验
- 第 362-366 行: 验证 magic 字段
- 第 368-371 行: 验证版本号
- 第 373-377 行: 选择可用 Worker
- 第 379-384 行: 初始化链接
- 第 386-389 行: 调用用户回调
- 第 391 行: 启用非阻塞模式
- 第 393-413 行: 加锁并添加到映射表
  - 检查启动状态
  - 检查重复 ID
  - 添加到 Worker epoll
  - 添加到连接映射表

### ConnectToPeerServer() - 连接到对等服务器 (行 467-524)

```cpp
Result AccTcpServerDefault::ConnectToPeerServer(const std::string &peerIp, uint16_t port, const AccConnReq &req,
                                                uint32_t maxRetryTimes, AccTcpLinkComplexPtr &newLink)
{
    auto parser = mf::SocketAddressParserMgr::getInstance().GetParser(port);
    ASSERT_RETURN(parser != nullptr, ACC_ERROR);
    if (!parser->IsIpv6()) {
        ASSERT_RETURN(AccCommonUtil::IsValidIPv4(peerIp), ACC_ERROR);
    }
    std::string ipAndPort = peerIp + ":" + std::to_string(port);

    auto tmpFD = ::socket(parser->GetAddressFamily(), SOCK_STREAM, 0);
    if (tmpFD < 0) {
        LOG_ERROR("Failed to create socket, errno:" << errno << ", please check if fd is out of limit");
        return ACC_ERROR;
    }

    int flags = 1;
    setsockopt(tmpFD, SOL_TCP, TCP_NODELAY, reinterpret_cast<void *>(&flags), sizeof(flags));
    int synCnt = 1; /* Set connect() retry time for quick connect */
    setsockopt(tmpFD, IPPROTO_TCP, TCP_SYNCNT, &synCnt, sizeof(synCnt));

    uint32_t timesRetried = 0;
    int lastErrno = 0;
    auto [addrPtr, addrLen] = parser->GetPeerAddress(peerIp, port);
    while (timesRetried < maxRetryTimes) {
        LOG_INFO_LIMIT("Trying to connect to " << ipAndPort);
        errno = 0;
        if (::connect(tmpFD, addrPtr, addrLen) == 0) {
            struct timeval timeout = {ACC_LINK_RECV_TIMEOUT, 0};
            setsockopt(tmpFD, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
            auto ret = Handshake(tmpFD, req, ipAndPort, newLink);
            if (ret != ACC_OK) {
                LOG_ERROR("Failed to Handshake to " << ipAndPort << " after tried " << timesRetried << " times"
                                                    << ", listenPort: " << options_.listenPort);
                SafeCloseFd(tmpFD);
            }
            return ret;
        }

        if (errno == EINTR) {
            continue;
        }

        if (lastErrno != errno) {
            LOG_INFO_LIMIT("Trying to connect to " << ipAndPort << " errno:" << errno
                                                   << ", retry times:" << timesRetried);
            lastErrno = errno;
        }

        // interval between each retry, 1 sec for each time,
        sleep(1);
        timesRetried++;
    }

    SafeCloseFd(tmpFD);
    LOG_ERROR_LIMIT("Failed to connect to " << ipAndPort << " after tried " << timesRetried << " times");
    return ACC_ERROR;
}
```

**逐行解读**:
- 第 470 行: 获取地址解析器
- 第 472-474 行: 验证 IPv4 地址
- 第 475 行: 构建 IP:Port 字符串
- 第 477 行: 创建 socket
- 第 479-481 行: 失败处理
- 第 483-486 行: 设置 TCP 选项
  - TCP_NODELAY: 禁用 Nagle 算法
  - TCP_SYNCNT: 连接重试次数
- 第 488-490 行: 重试循环变量
- 第 491 行: 获取对端地址
- 第 492-503 行: 重试连接循环
  - 尝试连接
  - 成功则进行握手
  - 处理 EINTR 中断
  - 打印日志
  - 休眠 1 秒
- 第 521-523 行: 清理并返回错误

### GenerateSslCtx() - 生成 SSL 上下文 (行 534-576)

```cpp
Result AccTcpServerDefault::GenerateSslCtx()
{
    if (!tlsOption_.enableTls) {
        return ACC_OK;
    }

    if (sslCtx_ != nullptr) {
        return ACC_OK;
    }

    AccTcpSslHelperPtr tmpHelperPtr = nullptr;
    if (sslHelper_ == nullptr) {
        tmpHelperPtr = AccMakeRef<AccTcpSslHelper>();
        if (tmpHelperPtr == nullptr) {
            LOG_ERROR("Failed to create server ssl helper");
            return ACC_MALLOC_FAIL;
        }
    } else {
        tmpHelperPtr = sslHelper_;
    }

    if (decryptHandler_) { // decryptHandler_ not null means private key password is encrypted
        tmpHelperPtr->RegisterDecryptHandler(decryptHandler_);
    }

    auto tmpSslCtx = OpenSslApiWrapper::SslCtxNew(OpenSslApiWrapper::TlsMethod());
    if (tmpSslCtx == nullptr) {
        LOG_ERROR("Failed to create server ssl ctx");
        return ACC_MALLOC_FAIL;
    }

    auto result = tmpHelperPtr->Start(tmpSslCtx, tlsOption_);
    if (result != ACC_OK) {
        LOG_ERROR("Failed to init server ssl ctx, ret " << result);
        OpenSslApiWrapper::SslCtxFree(tmpSslCtx);
        tmpSslCtx = nullptr;
        return result;
    }

    sslHelper_ = tmpHelperPtr;
    sslCtx_ = tmpSslCtx;
    return ACC_OK;
}
```

**逐行解读**:
- 第 536-538 行: 未启用 TLS 则返回
- 第 540-542 行: 已创建则返回
- 第 544-553 行: 创建 SSL 助手
- 第 555-557 行: 注册解密处理器
- 第 559-563 行: 创建 SSL 上下文
- 第 565-571 行: 初始化 SSL 上下文
- 第 573-574 行: 保存并返回

---

## 2. acc_tcp_link_complex_default.h/cpp - 复杂链路

### 文件信息
- 文件路径: `src/acc_links/csrc/acc_tcp_link_complex_default.h/cpp`
- 代码行数: 520 行
- 主要功能: 非阻塞模式的复杂链路实现

### AccLinkedMessageNode 结构体 (行 27-86)

```cpp
struct AccLinkedMessageNode {
    AccLinkedMessageNode *next = nullptr;
    AccMsgHeader header{};
    AccDataBufferPtr data{nullptr};
    AccDataBufferPtr cbCtx{nullptr};
    uint32_t headerRemain = sizeof(AccMsgHeader);
    uint32_t dataRemain = 0;

    AccLinkedMessageNode() = default;

    AccLinkedMessageNode(const AccMsgHeader &h, const AccDataBufferPtr &d, const AccDataBufferPtr &ctx)
        : header(h), data(d), cbCtx(ctx), dataRemain{d->DataLen()}
    {}

    inline bool HeaderSent() const
    {
        return headerRemain == 0;
    }

    inline bool DataSent() const
    {
        return dataRemain == 0;
    }

    inline bool Sent() const
    {
        return headerRemain == 0 && dataRemain == 0;
    }

    inline void *HeaderPtrToBeSend() const
    {
        auto baseHeaderPtr = reinterpret_cast<uintptr_t>(&header);
        return reinterpret_cast<void *>(baseHeaderPtr + (sizeof(AccMsgHeader) - headerRemain));
    }

    inline void *DataPtrToBeSend() const
    {
        return reinterpret_cast<void *>(data->DataIntPtr() + (data->DataLen() - dataRemain));
    }

    inline bool HeaderAllSent(uint32_t size)
    {
        if (headerRemain <= size) {
            headerRemain = 0;
            return true;
        }
        headerRemain -= size;
        return false;
    }

    inline bool DataAllSent(uint32_t size)
    {
        if (dataRemain <= size) {
            dataRemain = 0;
            return true;
        }
        dataRemain -= size;
        return false;
    }
};
```

**逐行解读**:
- 第 28-33 行: 成员变量
  - next: 下一个节点
  - header: 消息头
  - data: 数据缓冲区
  - cbCtx: 回调上下文
  - headerRemain: 剩余头部字节
  - dataRemain: 剩余数据字节
- 第 41-44 行: 检查头部是否发送完
- 第 46-49 行: 检查数据是否发送完
- 第 51-54 行: 检查是否全部发送完
- 第 56-60 行: 获取待发送的头部指针
- 第 62-65 行: 获取待发送的数据指针
- 第 67-75 行: 处理头部发送
- 第 77-85 行: 处理数据发送

### AccLinkedMessageQueue 类 (行 91-245)

```cpp
class AccLinkedMessageQueue : public AccReferable {
public:
    explicit AccLinkedMessageQueue(uint32_t queueCap) : sizeCap_(queueCap) {}

    ~AccLinkedMessageQueue() override
    {
        /* set the tmp node */
        AccLinkedMessageNode *tmpNode = nullptr;
        {
            std::lock_guard<std::mutex> guard(mutex_);
            tmpNode = headNode_;
            headNode_ = nullptr;
            tailNode_ = nullptr;
            size_ = 0;
        }

        if (tmpNode == nullptr) {
            return;
        }

        /* loop and delete */
        while (tmpNode != nullptr) {
            auto nodeToBeDelete = tmpNode;
            tmpNode = tmpNode->next;
            delete nodeToBeDelete;
            nodeToBeDelete = nullptr;
        }
    }

    uint32_t GetSize()
    {
        std::lock_guard<std::mutex> guard(mutex_);
        return size_;
    }

    Result EnqueueBack(const AccMsgHeader &h, const AccDataBufferPtr &d, const AccDataBufferPtr &cbCtx)
    {
        ASSERT_RETURN(d.Get() != nullptr, ACC_INVALID_PARAM);

        /* create new node */
        auto tmpNode = new (std::nothrow) AccLinkedMessageNode(h, d, cbCtx);
        ASSERT_RETURN(tmpNode != nullptr, ACC_NEW_OBJECT_FAIL);
        tmpNode->dataRemain = d->DataLen();

        {
            /* check and add */
            std::lock_guard<std::mutex> guard(mutex_);
            if (size_ >= sizeCap_) {
                delete tmpNode;
                tmpNode = nullptr;
                return ACC_QUEUE_IS_FULL;
            }

            /* if the empty */
            if (headNode_ == nullptr) {
                headNode_ = tmpNode;
                tailNode_ = tmpNode;
                ++size_;
                return ACC_OK;
            }

            /* if not empty */
            auto currentTail = tailNode_;
            tailNode_ = tmpNode;
            currentTail->next = tmpNode;
            ++size_;
            return ACC_OK;
        }
    }

    AccLinkedMessageNode *DequeueFront()
    {
        /* check and */
        std::lock_guard<std::mutex> guard(mutex_);
        if (size_ == 0) {
            return nullptr;
        }

        auto tmpNode = headNode_;
        /* only one node */
        if (size_ == 1) {
            headNode_ = nullptr;
            tailNode_ = nullptr;
            --size_;
            return tmpNode;
        }

        /* a lot of nodes */
        headNode_ = tmpNode->next;
        --size_;
        return tmpNode;
    }
    // ... 其他方法
};
```

**逐行解读**:
- 第 93 行: 构造函数，设置队列容量
- 第 95-118 行: 析构函数，清理所有节点
- 第 120-124 行: 获取队列大小
- 第 133-166 行: 入队操作
  - 创建新节点
  - 检查队列是否已满
  - 处理空队列情况
  - 处理非空队列情况
- 第 173-194 行: 出队操作
  - 检查空队列
  - 处理单节点情况
  - 处理多节点情况

### HandlePollIn() - 处理 POLLIN 事件 (行 337-402)

```cpp
inline Result AccTcpLinkComplexDefault::HandlePollIn() noexcept
{
    const auto headDataPtr = reinterpret_cast<uintptr_t>(&header_);

    /* receive header */
    ssize_t result = 0;
    if (receiveState_.ShouldReceiveHeader()) {
        result = PollInRecv(reinterpret_cast<void *>(headDataPtr + receiveState_.ReceivedHeaderLen()),
                            receiveState_.headerToBeReceived);
        if (LIKELY((result) > 0)) {
            if (receiveState_.HeaderSatisfied(result)) { /* header is full, continue to receive body */
                // validate header
                if (UNLIKELY(!data_->AllocIfNeed(header_.bodyLen))) {
                    LOG_ERROR("Failed to expand receive buffer to " << header_.bodyLen << ", probably out of memory");
                    receiveState_.ResetHeader();
                    return ACC_MALLOC_FAIL;
                }
                receiveState_.bodyToBeReceived = header_.bodyLen; /* expand memory size */
                data_->SetDataSize(0);
            } else { /* header is not fully, need to continue to receive */
                return ACC_LINK_EAGAIN;
            }
        } else {                            /* ECONNRESET is broken during io, SUCCESS is broken during idle time. */
            const auto errorNumber = errno; // avoid errno writen by log
            if (errorNumber == ECONNRESET || errorNumber == 0) {
                LOG_DEBUG("Link " << id_ << " receive header failed, reset by peer, errno " << errorNumber);
                return ACC_LINK_ERROR; /* socket is closed by peer, socket is error */
            }
            /* if errno is eagain is normal, need to continue to receive */
            /* else meaning failed to read from socket, socket is error */
            if (errorNumber != EAGAIN) {
                LOG_WARN("Link " << id_ << " receive header failed, errno " << errorNumber);
            }

            return (errorNumber == EAGAIN ? ACC_LINK_EAGAIN : ACC_LINK_ERROR);
        }
    }

    /* receive body */
    auto dataPtr = data_->DataIntPtr() + (header_.bodyLen - static_cast<size_t>(receiveState_.bodyToBeReceived));
    result = PollInRecv(reinterpret_cast<void *>(dataPtr), receiveState_.bodyToBeReceived);
    if (LIKELY((result) > 0)) {
        if (receiveState_.BodySatisfied(result)) { /* body is full */
            receiveState_.ResetHeader();
            data_->SetDataSize(header_.bodyLen);
            return ACC_LINK_MSG_READY; /* message fully received, we can do the upper call */
        }

        LOG_DEBUG("Receive sock " << id_ << " not full body size: " << receiveState_.bodyToBeReceived);
        /* body is not fully received, continue to receive */
        return ACC_LINK_EAGAIN;
    } else {                            /* ECONNRESET is broken during io, SUCCESS is broken during idle time. */
        const auto errorNumber = errno; // avoid errno writen by log
        if (errorNumber == ECONNRESET || errorNumber == 0) {
            LOG_INFO("Link " << id_ << " receive body failed, reset by peer, errno " << errorNumber);
            return ACC_LINK_ERROR; /* socket is closed by peer, socket is error */
        }
        /* if errno is eagain is normal, need to continue to receive */
        /* else meaning failed to read from socket,socket is error */
        if (errorNumber != EAGAIN) {
            LOG_ERROR("Link " << id_ << " receive body failed, errno " << errorNumber);
        }

        return (errorNumber == EAGAIN ? ACC_LINK_EAGAIN : ACC_LINK_ERROR);
    }
}
```

**逐行解读**:
- 第 339 行: 获取头部数据指针
- 第 342-373 行: 接收头部
  - 调用 PollInRecv 接收数据
  - 成功时检查是否接收完整
  - 完整则准备接收 body
  - 不完整则返回 EAGAIN
  - 处理连接重置和 EAGAIN
- 第 375-401 行: 接收 body
  - 计算 body 接收位置
  - 调用 PollInRecv 接收数据
  - 成功时检查是否完整
  - 完整则重置状态并返回 MSG_READY
  - 不完整则返回 EAGAIN
  - 处理连接重置和 EAGAIN

### HandlePollOut() - 处理 POLLOUT 事件 (行 404-461)

```cpp
inline Result AccTcpLinkComplexDefault::HandlePollOut(AccMsgHeader &header, AccDataBufferPtr &cbCtx) noexcept
{
    ASSERT_RETURN(queue_.Get() != nullptr, ACC_NOT_INITIALIZED);
    AccLinkedMessageNode *oneMsg = queue_->DequeueFront();
    if (UNLIKELY(oneMsg == nullptr)) {
        return ACC_OK;
    }

    ASSERT_RETURN(!oneMsg->Sent(), ACC_OK);
    header = oneMsg->header;
    cbCtx = oneMsg->cbCtx;

    /* send header if not sent */
    if (!oneMsg->HeaderSent()) {
        auto result = PollOutWrite(oneMsg->HeaderPtrToBeSend(), oneMsg->headerRemain);
        if (LIKELY(result > 0)) {
            if (!oneMsg->HeaderAllSent(result)) { /* not all sent */
                queue_->EnqueueFront(oneMsg);
                return ACC_LINK_EAGAIN;
            }
            /* if no data body send finished */
            if (oneMsg->DataSent()) {
                delete oneMsg;
                oneMsg = nullptr;
                return ACC_LINK_MSG_SENT;
            }

            /* continue to send data part */
        } else {
            delete oneMsg;
            oneMsg = nullptr;
            return SendPostProcess(errno);
        }
    }

    /* send data if not sent */
    if (!oneMsg->DataSent()) {
        auto result = PollOutWrite(oneMsg->DataPtrToBeSend(), oneMsg->dataRemain);
        if (LIKELY(result > 0)) {
            if (!oneMsg->DataAllSent(result)) { /* not all sent */
                queue_->EnqueueFront(oneMsg);
                return ACC_LINK_EAGAIN;
            }

            delete oneMsg;
            oneMsg = nullptr;
            return ACC_LINK_MSG_SENT;
        } else {
            delete oneMsg;
            oneMsg = nullptr;
            return SendPostProcess(errno);
        }
    }

    delete oneMsg;
    oneMsg = nullptr;
    return ACC_OK;
}
```

**逐行解读**:
- 第 406-410 行: 从队列取出消息
- 第 412-414 行: 设置输出参数
- 第 416-437 行: 发送头部
  - 调用 PollOutWrite 发送
  - 成功时检查是否全部发送
  - 未全部发送则重新入队
  - 无数据则删除节点并返回
  - 失败则调用后处理
- 第 439-456 行: 发送数据
  - 调用 PollOutWrite 发送
  - 成功时检查是否全部发送
  - 未全部发送则重新入队
  - 成功则删除节点并返回

### NonBlockSend() - 非阻塞发送 (行 478-490)

```cpp
inline Result AccTcpLinkComplexDefault::NonBlockSend(int16_t msgType, const AccDataBufferPtr &d,
                                                     const AccDataBufferPtr &cbCtx)
{
    ASSERT_RETURN(msgType >= MIN_MSG_TYPE && msgType < MAX_MSG_TYPE, ACC_INVALID_PARAM);
    ASSERT_RETURN(d.Get() != nullptr, ACC_INVALID_PARAM);

    if (UNLIKELY(!Established())) {
        LOG_ERROR_LIMIT("Failed to send message with message type " << msgType << " as the link is broken");
        return ACC_LINK_ERROR;
    }

    return EnqueueAndModifyEpoll({msgType, d->DataLen(), seqNo_++}, d, cbCtx);
}
```

**逐行解读**:
- 第 481-482 行: 参数校验
- 第 484-487 行: 检查链接状态
- 第 489 行: 构造消息头并入队，修改 epoll

---

## 总结

C_SRC 模块实现了 TCP 服务器的核心功能：

### 1. 服务器启动流程

```
Start()
    ├── 验证选项
    ├── 验证处理器
    ├── 生成 SSL 上下文
    ├── 启动延迟清理
    ├── 启动 Worker 线程
    │   ├── 创建 Worker 对象
    │   ├── 注册回调处理器
    │   └── 启动线程
    └── 启动监听器
        └── 开始监听端口
```

### 2. 连接处理流程

```
HandleNewConnection()
    ├── 验证 magic 和 version
    ├── 选择可用 Worker
    ├── 初始化链接
    ├── 调用用户回调
    ├── 添加到 Worker epoll
    └── 添加到连接映射表
```

### 3. 数据收发流程

```
接收 (HandlePollIn)
    ├── 接收头部
    │   ├── PollInRecv
    │   ├── 检查完整性
    │   └── 准备接收 body
    └── 接收 body
        ├── PollInRecv
        ├── 检查完整性
        └── 返回 MSG_READY

发送 (HandlePollOut)
    ├── 从队列取出消息
    ├── 发送头部
    │   ├── PollOutWrite
    │   ├── 检查完整性
    │   └── 继续发送数据
    └── 发送数据
        ├── PollOutWrite
        ├── 检查完整性
        └── 返回 MSG_SENT
```

### 4. 链接队列管理

```
AccLinkedMessageQueue
    ├── EnqueueBack() - 尾部入队
    ├── DequeueFront() - 头部出队
    ├── EnqueueFront() - 头部入队（失败重试）
    └── TakeAwayMessages() - 取走所有消息
```

### 5. 关键特性

1. **多 Worker 线程**: 支持多个工作线程并行处理
2. **epoll 事件驱动**: 基于 epoll 的高并发 I/O
3. **非阻塞 I/O**: 完整的非阻塞发送和接收
4. **消息队列**: 链表实现的消息队列
5. **SSL/TLS 支持**: 支持 OpenSSL 加密通信
6. **延迟清理**: 独立线程延迟清理断开链接
