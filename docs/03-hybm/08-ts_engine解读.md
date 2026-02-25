# HYBM TS_Engine 模块逐行解读

## 模块概述

TS_Engine (Task Stream Engine) 模块是 HyBM 的任务流引擎，负责管理 SDMA 任务队列的提交、执行和同步。该模块基于昇腾 NPU 的硬件队列（SQ/CQ）实现，提供了：

1. **Stream 管理** - 管理任务流的生命周期
2. **任务提交** - 将 SDMA 任务提交到硬件队列
3. **任务同步** - 等待任务完成并处理完成队列（CQE）
4. **线程本地缓存** - 每个线程维护独立的 Stream 实例

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| hybm_task.h | 174 | 任务定义和硬件结构体 |
| hybm_stream.h/cpp | 391 | Stream 类实现 |
| hybm_stream_manager.h/cpp | 93 | Stream 管理器 |
| hybm_stream_notify.h/cpp | 通知机制 |

---

## 1. hybm_task.h - 任务定义

### 文件信息
- 文件路径: `src/hybm/csrc/ts_engine/hybm_task.h`
- 代码行数: 174 行
- 主要功能: 定义任务类型和硬件队列结构体

### 常量定义 (行 20-30)

```cpp
constexpr uint8_t RT_STARS_SQE_TYPE_NOTIFY_RECORD = 6U;
constexpr uint8_t RT_STARS_SQE_TYPE_NOTIFY_WAIT = 7U;
constexpr uint8_t RT_STARS_SQE_TYPE_WRITE_VALUE = 8U;
constexpr uint8_t RT_STARS_SQE_TYPE_SDMA = 11U;

constexpr uint8_t RT_STARS_DEFAULT_KERNEL_CREDIT = 254U;
constexpr uint8_t RT_STARS_NEVER_TIMEOUT_KERNEL_CREDIT = 255U;
constexpr uint32_t UINT32_BIT_NUM = 32U;
constexpr uint32_t MASK_17_BIT = 0x0001FFFFU;
constexpr uint32_t MASK_32_BIT = 0xFFFFFFFFU;
constexpr uint32_t HYBM_SQCQ_DEPTH = 2048U;
```

**逐行解读**:
- 第 20-23 行: SQE 类型定义
  - NOTIFY_RECORD: 通知记录
  - NOTIFY_WAIT: 通知等待
  - WRITE_VALUE: 写值
  - SDMA: DMA 传输
- 第 25-26 行: 内核信用值
  - DEFAULT: 254 - 默认
  - NEVER_TIMEOUT: 255 - 永不超时
- 第 30 行: SQ/CQ 队列深度（2048）

### 中断方向枚举 (行 32-39)

```cpp
/* stars send interrupt direction */
enum RtStarsSqeIntDirType {
    RT_STARS_SQE_INT_DIR_NO = 0,         // send no interrupt
    RT_STARS_SQE_INT_DIR_TO_TSCPU = 1,   // to tscpu
    RT_STARS_SQE_INT_DIR_TO_CTRLCPU = 2, // to ctrlcpu
    RT_STARS_SQE_INT_DIR_TO_HOST = 3,    // to host
    RT_STARS_SQE_INT_DIR_END = 4
};
```

**逐行解读**:
- 第 34 行: 不发送中断
- 第 35 行: 发送到 TS CPU
- 第 36 行: 发送到控制 CPU
- 第 37 行: 发送到主机

### 任务类型枚举 (行 41-45)

```cpp
enum StreamTaskType : uint32_t {
    STREAM_TASK_TYPE_SDMA = 1,
    STREAM_TASK_TYPE_RDMA = 2,
    STREAM_TASK_TYPE_NOTIFY = 3,
};
```

**逐行解读**:
- SDMA: 本地 DMA 任务
- RDMA: 远程 DMA 任务
- NOTIFY: 通知任务

### SQE 头部结构体 (行 47-64)

```cpp
#pragma pack(push)
#pragma pack(1)
struct rtStarsSqeHeader_t {
    uint8_t type : 6;
    uint8_t l1_lock : 1;
    uint8_t l1_unlock : 1;

    uint8_t ie : 2;
    uint8_t pre_p : 2;
    uint8_t post_p : 2;
    uint8_t wr_cqe : 1;
    uint8_t reserved : 1;

    uint16_t block_dim; // block_dim or res

    uint16_t rt_stream_id;
    uint16_t task_id;
};
```

**逐行解读**:
- 第 50 行: type（6 位）- 任务类型
- 第 51 行: l1_lock（1 位）- L1 缓存锁定
- 第 52 行: l1_unlock（1 位）- L1 缓存解锁
- 第 54 行: ie（2 位）- 中断使能
- 第 55 行: pre_p（2 位）- 前处理优先级
- 第 56 行: post_p（2 位）- 后处理优先级
- 第 57 行: wr_cqe（1 位）- 写 CQE
- 第 60 行: block_dim - 块维度
- 第 62-63 行: 流 ID 和任务 ID

### Memcpy Async SQE 结构体 (行 66-110)

```cpp
struct rtStarsMemcpyAsyncSqe_t {
    rtStarsSqeHeader_t header;

    uint32_t res3;
    /********12 bytes**********/

    uint16_t res4; // max_retry(u8) retry_cnt(u8)
    uint8_t kernelCredit;
    uint8_t ptrMode : 1;
    uint8_t res5 : 7;
    /********16 bytes**********/

    uint32_t opcode : 8;
    uint32_t ie2 : 1;
    uint32_t sssv : 1;
    uint32_t dssv : 1;
    uint32_t sns : 1;
    uint32_t dns : 1;
    uint32_t qos : 4;
    uint32_t sro : 1;
    uint32_t dro : 1;
    uint32_t partid : 8;
    uint32_t mpam : 1;
    uint32_t d2dOffsetFlag : 1;
    uint32_t res6 : 3;
    /********20 bytes**********/

    uint16_t src_streamid;
    uint16_t src_sub_streamid;
    uint16_t dst_streamid;
    uint16_t dstSubStreamId;
    /********28 bytes**********/

    uint32_t length;
    uint32_t src_addr_low;
    uint32_t src_addr_high;
    uint32_t dst_addr_low;
    uint32_t dst_addr_high;

    uint32_t srcOffsetLow;
    uint32_t dstOffsetLow;
    uint16_t srcOffsetHigh;
    uint16_t dstOffsetHigh;
    uint32_t resLast[1];
};
```

**逐行解读**:
- 第 67 行: SQE 头部
- 第 69 行: 保留字段
- 第 72 行: 重试相关
- 第 73 行: 内核信用值
- 第 74-75 行: 指针模式
- 第 78-90 行: 操作配置
  - opcode: 操作码
  - ie2: 中断使能 2
  - sssv/dssv: 源/目的同步虚拟地址
  - sns/dns: 源/目的非安全
  - qos: 服务质量
  - sro/dro: 源/目的重排序
  - partid: 分区 ID
- 第 93-96 行: 流 ID 配置
- 第 99-103 行: 传输地址和长度
- 第 105-108 行: 偏移量配置

### StreamTask 结构体 (行 165-168)

```cpp
struct StreamTask {
    StreamTaskType type;
    rtStarsSqe_t sqe{};
};
```

**逐行解读**:
- 第 166 行: 任务类型
- 第 167 行: SQE 联合体

---

## 2. hybm_stream.h/cpp - Stream 类实现

### 文件信息
- 文件路径: `src/hybm/csrc/ts_engine/hybm_stream.h/cpp`
- 代码行数: 391 行
- 主要功能: 实现 Stream 类

### 类定义 (行 25-69)

```cpp
class HybmStream {
public:
    HybmStream(uint32_t deviceId, uint32_t prio, uint32_t flags) noexcept;
    ~HybmStream()
    {
        Destroy();
    }

    int Initialize() noexcept;
    void Destroy();

    int SubmitTasks(const StreamTask &tasks) noexcept;
    int Synchronize(uint32_t task = UINT32_MAX) noexcept;

    uint32_t GetId() const;
    uint32_t GetDevId() const;
    uint32_t GetTsId() const;
    bool GetWqeFlag() const;

private:
    int32_t AllocStreamId();
    int32_t AllocSqcq(uint32_t ssid);
    int32_t AllocLogicCq();
    bool GetCqeStatus();
    int32_t GetSqHead(uint32_t &head);
    int32_t ReceiveCqe(uint32_t &lastTask);
    bool TaskInRange(uint32_t task) const;

private:
    const uint32_t deviceId_;
    const uint32_t prio_;
    const uint32_t flags_;

    uint32_t tsId_{std::numeric_limits<uint32_t>::max()};
    uint32_t sqId_{0};
    uint32_t cqId_{0};
    uint32_t logicCq_{0};
    uint32_t streamId_{UINT32_MAX};
    uint32_t sqHead_{0};
    uint32_t sqTail_{0};
    std::atomic<int64_t> runningTaskCount_{0};
    std::vector<StreamTask> taskList_;
    bool wqeFlag_ = false;
    std::atomic_bool inited_ = false;
};
```

**逐行解读**:
- 第 27-31 行: 构造和析构函数
- 第 33-39 行: 公有接口
  - 初始化/销毁
  - 提交任务
  - 同步等待
  - 获取 ID
- 第 41-50 行: 私有方法
  - 分配资源
  - 查询状态
  - 接收 CQE
- 第 52-69 行: 私有成员
  - 设备 ID、优先级、标志
  - TS/SQ/CQ/逻辑 CQ ID
  - 流 ID
  - 队列头尾指针
  - 运行任务计数
  - 任务列表
  - 初始化标志

### Initialize() - 初始化 Stream (行 29-50)

```cpp
int HybmStream::Initialize() noexcept
{
    uint32_t ssid = 0;
    int32_t ret = 0;

    tsId_ = 0; // 当前仅支持0
    ret = AllocStreamId();
    BM_ASSERT_RETURN(ret == 0, ret);

    ret = AllocSqcq(ssid);
    BM_ASSERT_RETURN(ret == 0, ret);

    ret = AllocLogicCq();
    BM_ASSERT_RETURN(ret == 0, ret);

    BM_LOG_INFO("init stream ok, stream:" << streamId_ << " sq:" << sqId_ << " cq:" << cqId_ << " logic:" << logicCq_
                                          << " ssid:" << ssid);
    runningTaskCount_.store(0L);
    taskList_.resize(HYBM_SQCQ_DEPTH);
    inited_ = true;
    return BM_OK;
}
```

**逐行解读**:
- 第 31-32 行: 本地变量
- 第 34 行: 设置 TS ID 为 0（仅支持 TS0）
- 第 35-36 行: 分配 Stream ID
- 第 38-39 行: 分配 SQ/CQ
- 第 41-42 行: 分配逻辑 CQ
- 第 44-45 行: 打印日志
- 第 46 行: 重置任务计数
- 第 47 行: 调整任务列表大小
- 第 48 行: 设置初始化标志

### AllocStreamId() - 分配 Stream ID (行 52-72)

```cpp
int32_t HybmStream::AllocStreamId()
{
    if (streamId_ != UINT32_MAX) {
        return BM_OK;
    }

    struct halResourceIdInputInfo resAllocInput{};
    struct halResourceIdOutputInfo resAllocOutput;

    resAllocInput.type = DRV_STREAM_ID;
    resAllocInput.tsId = tsId_;

    auto ret = DlHalApi::HalResourceIdAlloc(deviceId_, &resAllocInput, &resAllocOutput);
    if (ret != 0) {
        BM_LOG_ERROR("alloc stream id failed, ts_id:" << tsId_ << " ret: " << ret);
        return BM_ERROR;
    }

    streamId_ = static_cast<uint32_t>(resAllocOutput.resourceId);
    return BM_OK;
}
```

**逐行解读**:
- 第 54-56 行: 已分配则返回成功
- 第 58-59 行: 输入输出结构体
- 第 61 行: 设置类型为 STREAM_ID
- 第 62 行: 设置 TS ID
- 第 64 行: 调用 HAL API 分配资源 ID
- 第 65-68 行: 失败处理
- 第 70 行: 保存 Stream ID

### AllocSqcq() - 分配 SQ/CQ (行 74-109)

```cpp
int32_t HybmStream::AllocSqcq(uint32_t ssid)
{
    halSqCqInputInfo input{};
    halSqCqOutputInfo output{};
    StreamAllocInfo *sinfo = (StreamAllocInfo *)input.info;

    input.type = DRV_NORMAL_TYPE;
    input.tsId = tsId_;
    input.sqeSize = 64U;
    input.cqeSize = 12U;
    input.sqeDepth = HYBM_SQCQ_DEPTH;
    input.cqeDepth = HYBM_SQCQ_DEPTH;
    input.grpId = 0;
    input.flag = flags_;
    input.cqId = 0;
    input.sqId = 0;
    input.res[SQCQ_RESV_LENGTH - 1] = ssid; // set ssid

    sinfo->streamId = streamId_;
    sinfo->priority = 0U;
    sinfo->satMode = 1U;
    sinfo->overflowEn = 0U;
    sinfo->threadDisableFlag = 1U;
    sinfo->shareSqId = UINT32_MAX;
    sinfo->tsSqType = 0U;

    auto ret = DlHalApi::HalSqCqAllocate(deviceId_, &input, &output);
    if (ret != 0) {
        BM_LOG_INFO("allocate sq_cq with ts_id:" << tsId_ << " failed: " << ret);
        return ret;
    }

    sqId_ = output.sqId;
    cqId_ = output.cqId;
    return BM_OK;
}
```

**逐行解读**:
- 第 76-77 行: 输入输出结构体
- 第 78 行: 获取流分配信息指针
- 第 80-88 行: 配置输入参数
  - 类型: 普通类型
  - SQE 大小: 64 字节
  - CQE 大小: 12 字节
  - 深度: 2048
- 第 90-97 行: 配置流信息
  - 流 ID
  - 优先级: 0
  - SAT 模式: 1
  - 禁用溢出
  - 禁用线程
- 第 99 行: 调用 HAL API 分配 SQ/CQ
- 第 100-104 行: 失败处理
- 第 106-107 行: 保存 SQ/CQ ID

### AllocLogicCq() - 分配逻辑 CQ (行 111-164)

```cpp
int32_t HybmStream::AllocLogicCq()
{
    halSqCqInputInfo input{};
    halSqCqOutputInfo output{};

    input.type = DRV_LOGIC_TYPE;
    input.tsId = tsId_;
    input.sqeSize = 0U;
    input.cqeSize = static_cast<uint32_t>(sizeof(rtLogicCqReport_t));
    input.sqeDepth = 0U;
    input.cqeDepth = 4096U;
    input.grpId = 0;
    input.flag = 0;
    input.cqId = 65535U;
    input.sqId = 0;
    input.info[0] = streamId_;

    pid_t realTid = syscall(SYS_gettid);
    if (realTid < 0) {
        BM_LOG_ERROR("get real tid failed " << realTid);
        return BM_ERROR;
    }
    input.info[1] = static_cast<uint32_t>(realTid);

    auto ret = DlHalApi::HalSqCqAllocate(deviceId_, &input, &output);
    if (ret != 0) {
        BM_LOG_INFO("allocate logic cq with ts_id:" << tsId_ << " failed: " << ret);
        return ret;
    }
    logicCq_ = output.cqId;

    struct halResourceIdInputInfo in = {};
    in.type = DRV_STREAM_ID;
    in.tsId = tsId_;
    in.resourceId = streamId_;
    in.res[1U] = 0;

    struct halResourceConfigInfo configInfo = {};
    configInfo.prop = DRV_STREAM_BIND_LOGIC_CQ;
    configInfo.value[0U] = logicCq_; // res[0]: logicCqId

    ret = DlHalApi::HalResourceConfig(deviceId_, &in, &configInfo);
    if (ret != 0) {
        BM_LOG_INFO("bind logic cq with ts_id:" << tsId_ << " failed: " << ret);
        halSqCqFreeInfo freeInfo{};
        freeInfo.type = DRV_LOGIC_TYPE;
        freeInfo.tsId = tsId_;
        freeInfo.sqId = output.sqId;
        freeInfo.cqId = output.cqId;
        DlHalApi::HalSqCqFree(deviceId_, &freeInfo);
        return ret;
    }
    return BM_OK;
}
```

**逐行解读**:
- 第 113-114 行: 输入输出结构体
- 第 116-124 行: 配置输入参数
  - 类型: 逻辑类型
  - CQE 大小: rtLogicCqReport_t
  - CQ 深度: 4096
  - CQ ID: 65535（特殊值）
  - info[0]: 流 ID
- 第 126-132 行: 获取真实线程 ID
- 第 134-139 行: 分配逻辑 CQ
- 第 140 行: 保存逻辑 CQ ID
- 第 142-151 行: 配置绑定信息
- 第 152-162 行: 绑定逻辑 CQ 到流
  - 失败则释放逻辑 CQ

### SubmitTasks() - 提交任务 (行 213-242)

```cpp
int32_t HybmStream::SubmitTasks(const StreamTask &tasks) noexcept
{
    BM_ASSERT_LOG_AND_RETURN(inited_, "stream not init!", BM_NOT_INITIALIZED);
    int ret = 0;
    if ((sqTail_ + UN40) % HYBM_SQCQ_DEPTH == sqHead_) {
        ret = Synchronize(sqHead_);
        BM_ASSERT_LOG_AND_RETURN(ret == BM_OK, "stream synchronize failed!", BM_ERROR);
    }

    BM_ASSERT_LOG_AND_RETURN(((sqTail_ + 1U) % HYBM_SQCQ_DEPTH != sqHead_), "stream if full!", BM_NOT_INITIALIZED);
    uint32_t taskId = sqTail_;
    sqTail_ = (sqTail_ + 1U) % HYBM_SQCQ_DEPTH;

    taskList_[taskId] = tasks;
    taskList_[taskId].sqe.memcpyAsyncSqe.header.task_id = taskId;

    halTaskSendInfo info{};
    info.type = DRV_NORMAL_TYPE;
    info.sqe_addr = (uint8_t *)(ptrdiff_t)(const void *)&(taskList_[taskId].sqe);
    info.sqe_num = 1U;
    info.tsId = tsId_;
    info.sqId = sqId_;

    ret = DlHalApi::HalSqTaskSend(deviceId_, &info);
    if (ret != 0) {
        BM_LOG_ERROR("SQ send task failed: " << ret);
        return BM_DL_FUNCTION_FAILED;
    }
    return BM_OK;
}
```

**逐行解读**:
- 第 215 行: 检查初始化状态
- 第 217-220 行: 剩余空间不足时同步等待
- 第 222 行: 检查队列是否已满
- 第 223-224 行: 分配任务 ID
- 第 226 行: 保存任务
- 第 227 行: 设置任务 ID
- 第 229-234 行: 配置发送信息
- 第 236 行: 发送任务到 SQ
- 第 237-240 行: 失败处理

### GetCqeStatus() - 获取 CQE 状态 (行 244-258)

```cpp
bool HybmStream::GetCqeStatus()
{
    struct halSqCqQueryInfo queryInfoIn = {};
    queryInfoIn.type = DRV_NORMAL_TYPE;
    queryInfoIn.tsId = tsId_;
    queryInfoIn.sqId = sqId_;
    queryInfoIn.cqId = 0U;
    queryInfoIn.prop = DRV_SQCQ_PROP_SQ_CQE_STATUS;

    TP_TRACE_BEGIN(TP_HYBM_SDMA_G2G_HAL_QUERY_SQ_STATUS);
    auto ret = DlHalApi::HalSqCqQuery(deviceId_, &queryInfoIn);
    TP_TRACE_END(TP_HYBM_SDMA_G2G_HAL_QUERY_SQ_STATUS, ret);
    BM_ASSERT_LOG_AND_RETURN(ret == 0, "HalSqCqQuery failed! ret:" << ret, false);
    return (queryInfoIn.value[0] != 0U);
}
```

**逐行解读**:
- 第 246-251 行: 配置查询信息
  - 类型: 普通类型
  - 属性: SQ CQE 状态
- 第 253-255 行: 性能打点和查询
- 第 256 行: 返回 CQE 状态

### ReceiveCqe() - 接收 CQE (行 310-356)

```cpp
int32_t HybmStream::ReceiveCqe(uint32_t &lastTask)
{
    int32_t retFlag = BM_OK;
    uint32_t revNum = 0;
    while (true) {
        halReportRecvInfo info{};
        rtLogicCqReport_t reportInfo[RT_MILAN_MAX_QUERY_CQE_NUM] = {};
        info.type = DRV_LOGIC_TYPE;
        info.tsId = tsId_;
        info.cqId = logicCq_;
        info.timeout = 0;
        info.cqe_addr = reinterpret_cast<uint8_t *>(reportInfo);
        info.cqe_num = RT_MILAN_MAX_QUERY_CQE_NUM;
        info.stream_id = streamId_;
        info.task_id = UINT16_MAX;
        info.report_cqe_num = RT_MILAN_MAX_QUERY_CQE_NUM;
        auto ret = DlHalApi::HalCqReportRecv(deviceId_, &info);
        if (ret != 0) {
            BM_LOG_ERROR("HalCqReportRecv failed: " << ret);
            return BM_DL_FUNCTION_FAILED;
        }
        if (info.report_cqe_num > RT_MILAN_MAX_QUERY_CQE_NUM) {
            BM_LOG_ERROR("Invalid report_cqe_num");
            return BM_INVALID_PARAM;
        }

        for (uint32_t idx = 0; idx < info.report_cqe_num; idx++) {
            lastTask = reportInfo[idx].taskId;
            if (reportInfo[idx].errorCode != 0) {
                BM_LOG_ERROR("task exec failed, stream:"
                             << reportInfo[idx].streamId
                             << " sqeType:" << static_cast<uint32_t>(reportInfo[idx].sqeType)
                             << " cqeErrorCode:" << reportInfo[idx].errorCode << "(" << GetCqeErrorStr(reportInfo[idx])
                             << ") cqeErrorType:" << static_cast<uint32_t>(reportInfo[idx].errorType));
                retFlag = BM_ERROR;
                PrintSqe(&taskList_[reportInfo[idx].taskId].sqe);
            }
        }

        revNum += info.report_cqe_num;
        if (info.report_cqe_num == 0) {
            break;
        }
    }
    BM_LOG_DEBUG("receive task count: " << revNum << " ret:" << retFlag << " last:" << lastTask);
    return retFlag;
}
```

**逐行解读**:
- 第 312-313 行: 返回标志和接收计数
- 第 314 行: 循环接收
- 第 315-326 行: 配置接收信息并调用 HAL API
- 第 327-334 行: 校验接收到的 CQE 数量
- 第 336-346 行: 处理每个 CQE
  - 更新最后任务 ID
  - 检查错误码
  - 打印错误信息和 SQE
- 第 348-353 行: 更新接收计数并检查是否完成
- 第 354-355 行: 打印日志并返回

### Synchronize() - 同步等待任务完成 (行 358-389)

```cpp
int HybmStream::Synchronize(uint32_t task) noexcept
{
    BM_ASSERT_LOG_AND_RETURN(inited_, "stream not init!", BM_NOT_INITIALIZED);
    constexpr int MAX_RETRY = 1000000;
    int retry = 0;
    int ret = BM_OK;
    while (sqHead_ != sqTail_ && TaskInRange(task) && retry < MAX_RETRY) {
        uint32_t head = UINT16_MAX;
        ret = GetSqHead(head);
        BM_ASSERT_LOG_AND_RETURN(ret == 0, "GetSqHead failed! ret:" << ret, ret);
        BM_ASSERT_LOG_AND_RETURN(head < HYBM_SQCQ_DEPTH, "GetSqHead invalid! head:" << head, BM_ERROR);

        if (!GetCqeStatus()) { // no cqe
            while (sqHead_ != head) {
                BM_LOG_DEBUG("finished task, task_Id:" << sqHead_ << " sqTail:" << sqTail_ << " task_type:"
                                                       << static_cast<int32_t>(taskList_[sqHead_].type));
                sqHead_ = (sqHead_ + 1U) % HYBM_SQCQ_DEPTH;
            }
        } else {
            uint32_t lastTask = UINT16_MAX;
            ret = ReceiveCqe(lastTask);
            if (lastTask != UINT16_MAX) {
                sqHead_ = (lastTask + 1U) % HYBM_SQCQ_DEPTH;
            }
            BM_ASSERT_LOG_AND_RETURN(ret == 0, "ReceiveCqe failed! ret:" << ret, ret);
        }
        retry++;
        usleep(1U);
    }

    return (retry >= MAX_RETRY ? BM_TIMEOUT : ret);
}
```

**逐行解读**:
- 第 360 行: 检查初始化状态
- 第 361 行: 最大重试次数
- 第 362-363 行: 重试计数和返回值
- 第 364 行: 循环等待条件
  - SQ 非空
  - 任务在范围内
  - 未超时
- 第 365-368 行: 获取 SQ 头指针
- 第 370-375 行: 无 CQE 时的处理
  - 更新 sqHead 到硬件头指针
- 第 376-382 行: 有 CQE 时的处理
  - 接收 CQE
  - 更新 sqHead
- 第 384-385 行: 重试计数并休眠
- 第 388 行: 返回结果（超时或成功）

---

## 3. hybm_stream_manager.h/cpp - Stream 管理器

### 文件信息
- 文件路径: `src/hybm/csrc/ts_engine/hybm_stream_manager.h/cpp`
- 代码行数: 93 行
- 主要功能: 管理线程本地的 Stream 实例

### 全局变量 (行 22-23)

```cpp
static std::shared_mutex g_allThreadStreamMutex;
static std::unordered_map<int64_t, HybmStreamPtr> g_allThreadStreams;
```

**逐行解读**:
- 第 22 行: 共享读写锁，保护线程流映射
- 第 23 行: 线程 ID 到 Stream 的映射表

### GetThreadHybmStream() - 获取线程本地 Stream (行 24-51)

```cpp
HybmStreamPtr HybmStreamManager::GetThreadHybmStream(uint32_t devId)
{
    const auto thisId = Func::GetCurTid();
    {
        std::shared_lock lock(g_allThreadStreamMutex);
        auto it = g_allThreadStreams.find(thisId);
        if (it != g_allThreadStreams.end()) {
            return it->second;
        }
    }
    HybmStreamPtr hybmStream_ = nullptr;
    {
        std::unique_lock lock(g_allThreadStreamMutex);
        auto it = g_allThreadStreams.find(thisId);
        if (it != g_allThreadStreams.end()) {
            return it->second;
        }
        hybmStream_ = std::make_shared<HybmStream>(devId, 0, 0);
        auto ret = hybmStream_->Initialize();
        if (ret != BM_OK) {
            BM_LOG_ERROR("HybmStream init failed: " << ret);
            hybmStream_->Destroy();
            return nullptr;
        }
        g_allThreadStreams[thisId] = hybmStream_;
    }
    return hybmStream_;
}
```

**逐行解读**:
- 第 26 行: 获取当前线程 ID
- 第 27-33 行: 第一次检查（读锁）
  - 找到则返回
- 第 35 行: 新建 Stream 指针
- 第 36-49 行: 双重检查锁定（写锁）
  - 再次检查是否已创建
  - 创建并初始化 Stream
  - 失败则销毁
  - 保存到映射表
- 第 50 行: 返回 Stream

### GetThreadAclStream() - 获取线程本地 ACL Stream (行 73-90)

```cpp
void *HybmStreamManager::GetThreadAclStream()
{
    static thread_local void *stream_ = nullptr;
    if (stream_ != nullptr) {
        return stream_;
    }
#if defined(ASCEND_NPU)
    static uint32_t ACL_STREAM_FAST_LAUNCH = 1U;
    static uint32_t ACL_STREAM_FAST_SYNC = 2U;
    auto ret = DlAclApi::AclrtCreateStreamWithConfig(&stream_, 0, ACL_STREAM_FAST_LAUNCH | ACL_STREAM_FAST_SYNC);
    if (ret != 0) {
        BM_LOG_ERROR("create stream failed: " << ret);
        return nullptr;
    }
#endif
    static thread_local AclrtStream aclrtStream_(stream_);
    return stream_;
}
```

**逐行解读**:
- 第 75 行: 线程本地静态变量
- 第 76-78 行: 已创建则返回
- 第 80-81 行: ACL Stream 配置标志
  - FAST_LAUNCH: 快速启动
  - FAST_SYNC: 快速同步
- 第 82-86 行: 创建 ACL Stream（仅 NPU）
- 第 88 行: RAII 包装，自动销毁
- 第 89 行: 返回 Stream

---

## 总结

TS_Engine 模块提供了任务流管理的完整实现：

### 1. 初始化流程

```
HybmStream::Initialize()
    ├── AllocStreamId() - 分配 Stream ID
    │   └── HalResourceIdAlloc(DRV_STREAM_ID)
    ├── AllocSqcq() - 分配 SQ/CQ
    │   ├── 配置 SQE/CQE 大小和深度
    │   ├── 配置流信息（优先级、SAT 模式等）
    │   └── HalSqCqAllocate()
    └── AllocLogicCq() - 分配逻辑 CQ
        ├── 配置逻辑 CQ 参数
        ├── 获取线程 ID
        ├── HalSqCqAllocate()
        └── HalResourceConfig(DRV_STREAM_BIND_LOGIC_CQ)
```

### 2. 任务提交流程

```
SubmitTasks()
    ├── 检查队列空间
    ├── 空间不足时 Synchronize()
    ├── 分配任务 ID
    ├── 保存任务到列表
    └── HalSqTaskSend() - 发送到硬件 SQ
```

### 3. 同步等待流程

```
Synchronize()
    ├── 循环直到任务完成
    ├── GetSqHead() - 获取硬件头指针
    ├── GetCqeStatus() - 检查 CQE 状态
    ├── 无 CQE 时: 更新 sqHead
    └── 有 CQE 时:
        ├── ReceiveCqe() - 接收完成队列
        │   ├── HalCqReportRecv()
        │   ├── 处理错误码
        │   └── 更新 lastTask
        └── 更新 sqHead
```

### 4. 线程本地管理

```
GetThreadHybmStream()
    ├── 第一次检查（读锁）
    ├── 双重检查锁定（写锁）
    ├── 创建 HybmStream
    ├── 初始化 Stream
    └── 保存到映射表
```

### 5. 关键特性

1. **线程本地**: 每个线程维护独立的 Stream 实例
2. **硬件队列**: 直接使用 NPU 的 SQ/CQ 硬件队列
3. **异步执行**: 任务提交后异步执行
4. **批量处理**: 支持深度为 2048 的任务队列
5. **错误处理**: 通过 CQE 错误码检测任务失败
