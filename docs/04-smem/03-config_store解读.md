# SMEM Config_Store 模块逐行解读

## 模块概述

Config_Store 模块是 Smem 的配置存储层，提供分布式键值存储功能，用于多个进程/节点间的配置信息同步。该模块支持：

1. **多后端支持** - 本地内存后端、TCP 后端
2. **客户端/服务端模式** - 支持 TCP 服务器/客户端架构
3. **TLS 安全通信** - 支持加密传输
4. **自动重连** - 连接断开时自动重连
5. **Watch 机制** - 监听键变化事件
6. **CAS 操作** - 原子比较交换

## 目录结构

```
config_store/
├── smem_config_store.h              # 配置存储接口定义
├── config_store_errno.h              # 错误码定义
├── config_store_log.h                # 配置存储日志
├── smem_store_factory.h/cpp          # 存储工厂
├── backend/
│   ├── smem_config_store_backend.h   # 后端接口
│   └── smem_local_memory_backend.h/cpp # 本地内存后端
├── tcp_store/
│   ├── smem_tcp_config_store.h/cpp       # TCP 配置存储
│   ├── smem_tcp_config_store_server.h/cpp # TCP 服务器端
│   ├── smem_prefix_config_store.h        # 前缀配置存储
│   ├── smem_tcp_config_store_ssl_helper.h # SSL 助手
│   └── smem_message_packer.h/cpp        # 消息打包器
└── ha/
    └── smem_ha_config_store.h/cpp    # 高可用配置存储
```

---

## 1. smem_config_store.h - 配置存储接口

### 文件信息
- 文件路径: `src/smem/csrc/config_store/smem_config_store.h`
- 代码行数: 372 行
- 主要功能: 定义配置存储的抽象接口

### 回调类型定义 (行 31-42)

```cpp
enum WatchRankType : uint32_t {
    WATCH_RANK_LINK_DOWN = 0,
};

const std::string AutoRankingStr = "AutoRanking#";

using ConfigStoreReconnectHandler = std::function<int32_t(void)>;

using ConfigStoreClientBrokenHandler = std::function<int()>;
using ConfigStoreServerOpHandler =
    std::function<int32_t(const uint32_t, const std::string &, std::vector<uint8_t> &, const StoreBackendPtr &)>;
using ConfigStoreServerBrokenHandler = std::function<void(const uint32_t, StoreBackendPtr &)>;
```

**逐行解读**:
- 第 31-33 行: `WatchRankType` - Rank 事件监听类型枚举
  - `WATCH_RANK_LINK_DOWN`: 监听 Rank 断连事件
- 第 35 行: `AutoRankingStr` - 自动排序前缀字符串常量
- 第 37 行: `ConfigStoreReconnectHandler` - 重连回调函数类型
- 第 39 行: `ConfigStoreClientBrokenHandler` - 客户端断连回调
- 第 40-42 行: `ConfigStoreServerOpHandler` - 服务端操作回调
- 第 43 行: `ConfigStoreServerBrokenHandler` - 服务端断连回调

### ConfigStore 类定义 (行 44-227)

```cpp
class ConfigStore : public SmReferable {
public:
    ~ConfigStore() override = default;

public:
    /**
     * @brief Set string value
     * @param key          [in] key to be set
     * @param value        [in] value to be set
     * @return 0 if successfully done
     */
    Result Set(const std::string &key, const std::string &value) noexcept;

    /**
     * @brief Get string value with key
     *
     * @param key          [in] key to be got
     * @param value        [out] value to be got
     * @param timeoutMs    [in] timeout
     * @return 0 if successfully done
     */
    Result Get(const std::string &key, std::string &value, int64_t timeoutMs = -1) noexcept;

    /**
     * @brief Get vector value with key
     *
     * @param key          [in] key to be got
     * @param value        [out] value to be got
     * @param timeoutMs    [in] timeout
     * @return 0 if successfully done
     */
    Result Get(const std::string &key, std::vector<uint8_t> &value, int64_t timeoutMs = -1) noexcept;

    /**
     * @brief Set vector value
     *
     * @param key          [in] key to be set
     * @param value        [in] value to be set
     * @return 0 if successfully done
     */
    virtual Result Set(const std::string &key, const std::vector<uint8_t> &value) noexcept = 0;
```

**逐行解读**:
- 第 44 行: ConfigStore 继承自 SmReferable（引用计数基类）
- 第 46 行: 虚析构函数
- 第 55 行: `Set(key, value)` - 设置字符串值的包装函数
- 第 65 行: `Get(key, value, timeoutMs)` - 获取字符串值
- 第 75 行: `Get(key, value, timeoutMs)` - 获取字节向量值
- 第 84 行: `Set(key, value)` - 设置字节向量值（纯虚函数）

```cpp
    /**
     * @brief Add integer value
     *
     * @param key          [in] key to be increased
     * @param increment    [in] value to be increased
     * @param value        [out] value after increased
     * @return 0 if successfully done
     */
    virtual Result Add(const std::string &key, int64_t increment, int64_t &value) noexcept = 0;

    /**
     * @brief Remove a key
     *
     * @param key          [in] key to be removed
     * @return 0 if successfully done
     */
    Result Remove(const std::string &key) noexcept;

    /**
     * @brief Remove a key
     *
     * @param key               [in] key to be removed
     * @param printKeyNotExist  [in] whether to print non exist key
     * @return 0 if successfully done
     */
    virtual Result Remove(const std::string &key, bool printKeyNotExist) noexcept = 0;
```

**逐行解读**:
- 第 94 行: `Add` - 原子增加操作（用于计数器）
- 第 102 行: `Remove` - 删除键的包装函数
- 第 111 行: `Remove(key, printKeyNotExist)` - 删除键（带日志控制）

```cpp
    /**
     * @brief Append string to a key with string value
     *
     * @param key          [in] key to be appended
     * @param value        [in] value to be appended
     * @param newSize      [out] new size of value after appended
     * @return 0 if successfully done
     */
    Result Append(const std::string &key, const std::string &value, uint64_t &newSize) noexcept;

    /**
     * @brief Append char/int8 vector to a key with char/int8 value
     *
     * @param key          [in] key to be appended
     * @param value        [in] value to be appended
     * @param newSize      [out] new size of value after appended
     * @return 0 if successfully done
     */
    virtual Result Append(const std::string &key, const std::vector<uint8_t> &value, uint64_t &newSize) noexcept = 0;
```

**逐行解读**:
- 第 121 行: `Append` - 追加字符串的包装函数
- 第 131 行: `Append` - 追加字节向量的纯虚函数

### CAS 操作 (行 144-159)

```cpp
    /**
     * @brief Perform an atomic compare and swap for string type. That is, if the current value for <i>key</i> equals
     *        <i>expect</i>, then set the value of <i>key</i> to be <i>value</i>.
     * @param key          [in] key for performed
     * @param expect       [in] expected value for old, empty string equals non-exist
     * @param value        [in] value for set if expected matches
     * @param exists       [out] old value of the key before this operation
     * @return If the communication with the store server is successful, 0 is returned. Otherwise, non-zero is returned.
     *         Returning 0 does not indicate successful CAS. To determine whether the CAS is successful, compare
     *         <i>exists</i> and <i>expect</i>.
     */
    Result Cas(const std::string &key, const std::string &expect, const std::string &value,
               std::string &exists) noexcept;

    /**
     * @brief Perform an atomic compare and swap for uint8 vector. That is, if the current value for <i>key</i> equals
     *        <i>expect</i>, then set the value of <i>key</i> to be <i>value</i>.
     * @param key          [in] key for performed
     * @param expect       [in] expected value for old, empty vector equals non-exist
     * @param value        [in] value for set if expected matches
     * @param exists       [out] old value of the key before this operation
     * @return If the communication with the store server is successful, 0 is returned. Otherwise, non-zero is returned.
     *         Returning 0 does not indicate successful CAS. To determine whether the CAS is successful, compare
     *         <i>exists</i> and <i>expect</i>.
     */
    virtual Result Cas(const std::string &key, const std::vector<uint8_t> &expect, const std::vector<uint8_t> &value,
                       std::vector<uint8_t> &exists) noexcept = 0;
```

**逐行解读**:
- 第 144-145 行: 字符串 CAS 操作，用于分布式锁实现
  - `expect`: 期望的当前值
  - `value`: 要设置的新值
  - `exists`: 输出实际的当前值
  - 返回 0 只表示通信成功，需要比较 `exists` 和 `expect` 判断 CAS 是否成功
- 第 158-159 行: 字节向量 CAS 操作

### Watch 机制 (行 168-199)

```cpp
    /**
     * @brief Watch the specified non-existent key. When the key is created, the specified notify function is invoked.
     * @param key          [in] key to be watched
     * @param notify       [in] notify function when key is created.
     * @param wid          [out] Unique ID of the watch event.
     * @return 0 if successfully done
     */
    Result Watch(const std::string &key,
                 const std::function<void(int result, const std::string &, const std::string &)> &notify,
                 uint32_t &wid) noexcept;

    /**
     * @brief Watch the specified non-existent key. When the key is created, the specified notify function is invoked.
     * @param key          [in] key to be watched
     * @param notify       [in] notify function when key is created.
     * @param wid          [out] Unique ID of the watch event.
     * @return 0 if successfully done
     */
    virtual Result
    Watch(const std::string &key,
          const std::function<void(int result, const std::string &, const std::vector<uint8_t> &)> &notify,
          uint32_t &wid) noexcept = 0;

    /**
     * @brief Watch the event for rank state change.
     * @param type         [in] watch rank event type
     * @param notify       [in] callback function
     * @param wid          [out] Unique ID of the watch event.
     * @return 0 if successfully done
     */
    virtual Result Watch(WatchRankType type, const std::function<void(WatchRankType, uint32_t)> &notify,
                         uint32_t &wid) noexcept = 0;

    /**
     * @brief Cancel an existed watcher.
     * @param wid          [in] Unique ID of the watch event.
     * @return 0 if successfully done
     */
    virtual Result Unwatch(uint32_t wid) noexcept = 0;
```

**逐行解读**:
- 第 168-170 行: 监听键创建事件（字符串版本）
- 第 179-182 行: 监听键创建事件（字节向量版本）
- 第 191-192 行: 监听 Rank 状态变化事件
- 第 199 行: 取消监听

### 内联函数实现 (行 283-342)

```cpp
inline Result ConfigStore::Set(const std::string &key, const std::string &value) noexcept
{
    return Set(key, std::vector<uint8_t>(value.begin(), value.end()));
}

inline Result ConfigStore::Get(const std::string &key, std::string &value, int64_t timeoutMs) noexcept
{
    std::vector<uint8_t> u8val;
    auto ret = GetReal(key, u8val, timeoutMs);
    if (ret != 0) {
        return ret;
    }

    value = std::string(u8val.begin(), u8val.end());
    return 0;
}

inline Result ConfigStore::Get(const std::string &key, std::vector<uint8_t> &value, int64_t timeoutMs) noexcept
{
    return GetReal(key, value, timeoutMs);
}

inline Result ConfigStore::Remove(const std::string &key) noexcept
{
    return Remove(key, false);
}

inline Result ConfigStore::Append(const std::string &key, const std::string &value, uint64_t &newSize) noexcept
{
    std::vector<uint8_t> u8val(value.begin(), value.end());
    return Append(key, u8val, newSize);
}

inline Result ConfigStore::Cas(const std::string &key, const std::string &expect, const std::string &value,
                               std::string &exists) noexcept
{
    std::vector<uint8_t> u8expect{expect.begin(), expect.end()};
    std::vector<uint8_t> u8value{value.begin(), value.end()};
    std::vector<uint8_t> u8exists;
    auto ret = Cas(key, u8expect, u8value, u8exists);
    if (ret != SM_OK) {
        return ret;
    }

    exists = std::string{u8exists.begin(), u8exists.end()};
    return SM_OK;
}

inline Result
ConfigStore::Watch(const std::string &key,
                   const std::function<void(int result, const std::string &, const std::string &)> &notify,
                   uint32_t &wid) noexcept
{
    return Watch(
        key,
        [notify](int res, const std::string &k, const std::vector<uint8_t> &v) {
            notify(res, k, std::string{v.begin(), v.end()});
        },
        wid);
}
```

**逐行解读**:
- 第 283-286 行: Set 字符串重载，转换为字节向量
- 第 288-298 行: Get 字符串重载，调用 GetReal 后转换回字符串
- 第 300-303 行: Get 字节向量重载，直接调用 GetReal
- 第 305-308 行: Remove 包装函数，默认不打印错误
- 第 310-314 行: Append 字符串重载
- 第 316-329 行: Cas 字符串重载，处理类型转换
- 第 331-342 行: Watch 字符串重载，lambda 转换字节向量到字符串

### 错误码转换 (行 344-366)

```cpp
inline const char *ConfigStore::ErrStr(int16_t errCode)
{
    switch (errCode) {
        case SUCCESS:
            return "success";
        case ERROR:
            return "error";
        case INVALID_MESSAGE:
            return "invalid message";
        case INVALID_KEY:
            return "invalid key";
        case NOT_EXIST:
            return "key not exists";
        case TIMEOUT:
            return "timeout";
        case IO_ERROR:
            return "socket error";
        case RESTORE:
            return "restore";
        default:
            return "unknown error";
    }
}
```

**逐行解读**:
- 第 344 行: 静态方法，根据错误码返回错误字符串
- 第 346-366 行: 错误码映射
  - `SUCCESS` - 成功
  - `ERROR` - 一般错误
  - `INVALID_MESSAGE` - 无效消息
  - `INVALID_KEY` - 无效键
  - `NOT_EXIST` - 键不存在
  - `TIMEOUT` - 超时
  - `IO_ERROR` - Socket 错误
  - `RESTORE` - 恢复（重连成功）

### ConfigStoreManager 类 (行 230-281)

```cpp
class ConfigStoreManager : public ConfigStore {
public:
    ~ConfigStoreManager() override = default;

public:
    /**
     * @brief Register reconnect handler for broken connection recovery
     * @param callback     [in] callback function to be invoked on reconnection
     */
    virtual void RegisterReconnectHandler(ConfigStoreReconnectHandler callback) noexcept = 0;

    /**
     * @brief Reconnect after connection broken
     * @param reconnectRetryTimes [in] number of retry times for reconnection
     * @return 0 if successfully done
     */
    virtual Result ReConnectAfterBroken(int reconnectRetryTimes) noexcept = 0;

    /**
     * @brief Get current connection status
     * @return true if connected, false otherwise
     */
    virtual bool GetConnectStatus() noexcept = 0;

    /**
     * @brief Set connection status
     * @param status       [in] connection status to be set
     */
    virtual void SetConnectStatus(bool status) noexcept = 0;

    /**
     * @brief Register client broken handler
     * @param handler      [in] handler to be invoked when client connection is broken
     */
    virtual void RegisterClientBrokenHandler(const ConfigStoreClientBrokenHandler &handler) noexcept = 0;

    /**
     * @brief Register server broken handler
     * @param handler      [in] handler to be invoked when server connection is broken
     */
    virtual void RegisterServerBrokenHandler(const ConfigStoreServerBrokenHandler &handler) noexcept = 0;

    /**
     * @brief Register server operation handler
     * @param opCode       [in] operation code
     * @param handler      [in] handler to be invoked for the specified operation
     */
    virtual void RegisterServerOpHandler(int16_t opCode, const ConfigStoreServerOpHandler &handler) noexcept = 0;

    virtual void SetRankId(const int32_t &rankId) noexcept {}
};
```

**逐行解读**:
- 第 230 行: ConfigStoreManager 继承 ConfigStore
- 第 232 行: 虚析构函数
- 第 239 行: `RegisterReconnectHandler` - 注册重连处理器
- 第 246 行: `ReConnectAfterBroken` - 断连后重连
- 第 252 行: `GetConnectStatus` - 获取连接状态
- 第 258 行: `SetConnectStatus` - 设置连接状态
- 第 264 行: `RegisterClientBrokenHandler` - 注册客户端断连处理器
- 第 270 行: `RegisterServerBrokenHandler` - 注册服务端断连处理器
- 第 277 行: `RegisterServerOpHandler` - 注册服务端操作处理器
- 第 279 行: `SetRankId` - 设置 Rank ID

---

## 2. smem_store_factory.h/cpp - 存储工厂

### 文件信息
- 文件路径: `src/smem/csrc/config_store/smem_store_factory.h` (79 行)
- 主要功能: 创建和管理配置存储实例

### StoreFactory 类定义 (行 25-74)

```cpp
class StoreFactory {
public:
    /**
     * @brief create a new store
     * @param ip server ip address
     * @param port server tcp port
     * @param isServer is local store server side
     * @param rankId rank id, default 0
     * @param connMaxRetry Maximum number of retry times for the client to connect to the server.
     * @return Newly created store
     */
    static StorePtr CreateStore(const std::string &ip, uint16_t port, bool isServer, uint32_t worldSize = 0,
                                int32_t rankId = -1, int32_t connMaxRetry = -1) noexcept;

    static StorePtr CreateStoreServer(const std::string &ip, uint16_t port, uint32_t worldSize = UINT32_MAX,
                                      int32_t rankId = -1, int32_t connMaxRetry = -1) noexcept;

    static StorePtr CreateStoreClient(const std::string &ip, uint16_t port, uint32_t worldSize = 1024,
                                      int32_t rankId = -1, int32_t connMaxRetry = -1) noexcept;

    /**
     * @brief destroy on exist store
     * @param ip server ip address
     * @param port server tcp port
     */
    static void DestroyStore(const std::string &ip, uint16_t port) noexcept;

    static void DestroyStoreAll(bool afterFork = false) noexcept;

    /**
     * @brief Encapsulate an existing store into a prefix store.
     * @param base existing store
     * @param prefix Prefix of keys
     * @return prefix store.
     */
    static StorePtr PrefixStore(const StorePtr &base, const std::string &prefix) noexcept;

    static int GetFailedReason() noexcept;

    static void SetTlsInfo(const smem_tls_config &tlsOption) noexcept;

private:
    static std::mutex storesMutex_;
    static std::unordered_map<std::string, StorePtr> storesMap_;
    static smem_tls_config tlsOption_;
    static bool enableTls;
    static std::string tlsInfo;
    static std::string tlsPkInfo;
    static std::string tlsPkPwdInfo;
};
```

**逐行解读**:
- 第 36-37 行: `CreateStore` - 创建存储（根据 isServer 选择客户端或服务端）
- 第 39-40 行: `CreateStoreServer` - 创建服务端存储
- 第 42-43 行: `CreateStoreClient` - 创建客户端存储
- 第 50 行: `DestroyStore` - 销毁指定 IP:Port 的存储
- 第 52 行: `DestroyStoreAll` - 销毁所有存储（afterFork 用于 fork 后清理）
- 第 60 行: `PrefixStore` - 创建前缀存储（键自动添加前缀）
- 第 62 行: `GetFailedReason` - 获取失败原因
- 第 64 行: `SetTlsInfo` - 设置 TLS 配置
- 第 67-74 行: 静态成员变量
  - `storesMutex_` - 存储 map 互斥锁
  - `storesMap_` - IP:Port 到 Store 的映射
  - `tlsOption_` - TLS 配置
  - `enableTls` - TLS 启用标志
  - `tlsInfo` - TLS 信息
  - `tlsPkInfo` - TLS 私钥信息
  - `tlsPkPwdInfo` - TLS 私钥密码信息

---

## 3. tcp_store/smem_tcp_config_store.h - TCP 配置存储

### 文件信息
- 文件路径: `src/smem/csrc/config_store/tcp_store/smem_tcp_config_store.h`
- 代码行数: 148 行
- 主要功能: 基于 TCP 的配置存储实现

### ClientCommonContext (行 28-39)

```cpp
class ClientCommonContext {
public:
    virtual ~ClientCommonContext() = default;
    virtual std::shared_ptr<ock::acc::AccTcpRequestContext> WaitFinished() noexcept = 0;
    virtual void SetFinished(const ock::acc::AccTcpRequestContext &response) noexcept = 0;
    virtual void SetFailedFinish() noexcept = 0;
    virtual bool Blocking() const noexcept = 0;
    virtual bool OnlyOneTime() const noexcept
    {
        return true;
    }
};
```

**逐行解读**:
- 第 28 行: 客户端通用上下文抽象基类
- 第 30 行: 虚析构函数
- 第 31 行: `WaitFinished` - 等待操作完成
- 第 32 行: `SetFinished` - 设置完成状态
- 第 33 行: `SetFailedFinish` - 设置失败状态
- 第 34 行: `Blocking` - 是否阻塞模式
- 第 35-38 行: `OnlyOneTime` - 是否一次性（默认 true）

### TcpConfigStore 类定义 (行 41-143)

```cpp
class TcpConfigStore : public ConfigStoreManager {
public:
    TcpConfigStore(StoreBackendPtr storeBackend, std::string ip, uint16_t port, bool isServer, uint32_t worldSize = 0,
                   int32_t rankId = -1) noexcept;
    ~TcpConfigStore() noexcept override;

    Result Startup(const smem_tls_config &tlsConfig, int reconnectRetryTimes = -1) noexcept;
    Result ClientStart(const smem_tls_config &tlsConfig, int reconnectRetryTimes = -1) noexcept;
    Result ServerStart(const smem_tls_config &tlsConfig, int reconnectRetryTimes = -1) noexcept;
    void Shutdown(bool afterFork = false) noexcept;

    Result Set(const std::string &key, const std::vector<uint8_t> &value) noexcept override;
    Result Add(const std::string &key, int64_t increment, int64_t &value) noexcept override;
    Result Remove(const std::string &key, bool printKeyNotExist) noexcept override;
    Result Append(const std::string &key, const std::vector<uint8_t> &value, uint64_t &newSize) noexcept override;
    Result Cas(const std::string &key, const std::vector<uint8_t> &expect, const std::vector<uint8_t> &value,
               std::vector<uint8_t> &exists) noexcept override;
    Result Watch(const std::string &key,
                 const std::function<void(int result, const std::string &, const std::vector<uint8_t> &)> &notify,
                 uint32_t &wid) noexcept override;
    Result Watch(WatchRankType type, const std::function<void(WatchRankType, uint32_t)> &notify,
                 uint32_t &wid) noexcept override;
    Result Unwatch(uint32_t wid) noexcept override;
    Result Write(const std::string &key, const std::vector<uint8_t> &value, const uint32_t offset) noexcept override;
```

**逐行解读**:
- 第 43-45 行: 构造函数，接收后端、IP、端口、服务端标志等
- 第 46 行: 虚析构函数
- 第 47 行: `Startup` - 启动（根据 isServer 选择客户端或服务端启动）
- 第 48 行: `ClientStart` - 客户端启动
- 第 49 行: `ServerStart` - 服务端启动
- 第 50 行: `Shutdown` - 关闭
- 第 52-64 行: 实现所有 ConfigStore 接口

```cpp
    void RegisterReconnectHandler(ConfigStoreReconnectHandler callback) noexcept override
    {
        reconnectHandler = callback;
    }

    void SetRankId(const int32_t &rankId) noexcept override
    {
        rankId_ = rankId;
    }

    Result ReConnectAfterBroken(int reconnectRetryTimes) noexcept override;
    bool GetConnectStatus() noexcept override;
    void SetConnectStatus(bool status) noexcept override;
    void RegisterClientBrokenHandler(const ConfigStoreClientBrokenHandler &handler) noexcept override;

    void RegisterServerBrokenHandler(const ConfigStoreServerBrokenHandler &handler) noexcept override;

    void RegisterServerOpHandler(int16_t opCode, const ConfigStoreServerOpHandler &handler) noexcept override;

protected:
    Result GetReal(const std::string &key, std::vector<uint8_t> &value, int64_t timeoutMs) noexcept override;

private:
    std::shared_ptr<ock::acc::AccTcpRequestContext> SendMessageBlocked(const std::vector<uint8_t> &reqBody) noexcept;
    Result LinkBrokenHandler(const ock::acc::AccTcpLinkComplexPtr &link) noexcept;
    Result ReceiveResponseHandler(const ock::acc::AccTcpRequestContext &context) noexcept;
    Result SendWatchRequest(const std::vector<uint8_t> &reqBody,
                            const std::function<void(int result, const std::vector<uint8_t> &)> &notify,
                            uint32_t &id) noexcept;
    void HeartBeat() noexcept;

    inline int32_t LocalNonBlockSend(int16_t msgType, uint32_t seqNo, const acc::AccDataBufferPtr &d,
                                     const acc::AccDataBufferPtr &cbCtx)
    {
        auto ret = accClientLink_->NonBlockSend(msgType, seqNo, d, cbCtx);
        if (ret == acc::ACC_LINK_ERROR) {
            ReConnectAfterBroken(1UL);
            ret = accClientLink_->NonBlockSend(msgType, seqNo, d, cbCtx);
        }
        return ret;
    }
```

**逐行解读**:
- 第 80-83 行: 注册重连处理器
- 第 85-88 行: 设置 Rank ID
- 第 90-93 行: `ReConnectAfterBroken` - 断连重连
- 第 94-96 行: 连接状态管理
- 第 103-105 行: 注册断连处理器
- 第 111-120 行: 私有方法
  - `SendMessageBlocked` - 阻塞发送消息
  - `LinkBrokenHandler` - 断链处理
  - `ReceiveResponseHandler` - 接收响应处理
  - `SendWatchRequest` - 发送 Watch 请求
  - `HeartBeat` - 心跳线程
- 第 111-120 行: `LocalNonBlockSend` - 本地非阻塞发送（带自动重连）

```cpp
private:
    AccStoreServerPtr accServer_;
    ock::acc::AccTcpServerPtr accClient_;
    ock::acc::AccTcpLinkComplexPtr accClientLink_;

    std::mutex msgCtxMutex_;
    std::unordered_map<uint32_t, std::shared_ptr<ClientCommonContext>> msgClientContext_;
    static std::atomic<uint32_t reqSeqGen_;

    std::mutex mutex_;
    const std::string serverIp_;
    const uint16_t serverPort_;
    const bool isServer_;
    int32_t rankId_;
    const uint32_t worldSize_;
    std::atomic<bool> isConnect_{false};
    ConfigStoreReconnectHandler reconnectHandler{nullptr};
    ConfigStoreClientBrokenHandler brokenHandler_ = nullptr;
    std::atomic<bool> isRunning_{false};
    std::thread heartBeatThread_;
    StoreBackendPtr backend_;
};
```

**逐行解读**:
- 第 123 行: `accServer_` - ACC 服务端（服务端模式）
- 第 124 行: `accClient_` - ACC 客户端
- 第 125 行: `accClientLink_` - ACC 客户端链路
- 第 127 行: `msgCtxMutex_` - 消息上下文互斥锁
- 第 128 行: `msgClientContext_` - 消息上下文映射
- 第 129 行: `reqSeqGen_` - 请求序列号生成器（原子计数器）
- 第 131 行: `mutex_` - 类级别互斥锁
- 第 132-136 行: 连接参数
- 第 137 行: `isConnect_` - 连接状态
- 第 138 行: `reconnectHandler` - 重连处理器
- 第 139 行: `brokenHandler_` - 断连处理器
- 第 140 行: `isRunning_` - 运行状态
- 第 141 行: `heartBeatThread_` - 心跳线程
- 第 142 行: `backend_` - 存储后端

---

## 总结

Config_Store 模块提供了完整的分布式配置存储功能：

### 1. 接口层次

```
ConfigStore (抽象基类)
    ├── ConfigStoreManager (管理接口)
    │     └── TcpConfigStore (TCP 实现)
    ├── PrefixConfigStore (前缀装饰器)
    └── LocalMemoryBackend (本地内存实现)
```

### 2. 核心功能

| 功能 | 方法 | 用途 |
|------|------|------|
| 设置键值 | `Set` | 存储配置 |
| 获取键值 | `Get` | 读取配置 |
| 原子增加 | `Add` | 计数器 |
| 删除键 | `Remove` | 清理配置 |
| 追加 | `Append` | 扩展配置 |
| 原子交换 | `Cas` | 分布式锁 |
| 监听 | `Watch` | 事件通知 |

### 3. TCP 架构

```
Client                          Server
  │                               │
  ├─ AccTcpLink ─────────────> ├─ AccTcpServer
  │                               │
  ├─ TcpConfigStore             ├─ TcpConfigStore
  │   │                           │   │
  │   ├─ SendMessage            │   ├─ ReceiveMessage
  │   ├─ ReceiveResponse        │   ├─ SendResponse
  │   └─ HeartBeat ─────────────> │   └─ Backend
  │                               │
  └─ StoreBackend               └─ StoreBackend
```

### 4. 断连恢复

- 连接状态检测（心跳机制）
- 自动重连（带重试次数限制）
- 重连回调通知
- 断连回调处理

### 5. 设计模式

**工厂模式**: StoreFactory 创建不同类型存储
**装饰器模式**: PrefixStore 为存储添加前缀
**策略模式**: 不同后端实现（本地、TCP）
**观察者模式**: Watch 机制

### 6. 线程安全

- 互斥锁保护共享状态
- 原子操作（序列号生成、连接状态）
- 线程安全的消息上下文管理
