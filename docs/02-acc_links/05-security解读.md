# ACC_Links Security 模块逐行解读

## 模块概述

Security 模块是 ACC_Links 的 SSL/TLS 安全通信模块，基于 OpenSSL 实现了安全的 TCP 通信。该模块提供了完整的 SSL 上下文管理、证书加载、证书验证、私钥解密等功能。

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| acc_tcp_ssl_helper.h/cpp | 611 | SSL 助手实现 |

---

## acc_tcp_ssl_helper.h/cpp - SSL 助手

### 文件信息
- 文件路径: `src/acc_links/csrc/security/acc_tcp_ssl_helper.h/cpp`
- 代码行数: 611 行
- 主要功能: 封装 OpenSSL API，提供 SSL 上下文管理

### 常量定义 (行 31-33)

```cpp
constexpr int MIN_PRIVATE_KEY_CONTENT_BIT_LEN = 3072; // RSA密钥长度要求大于3072
constexpr int MIN_PRIVATE_KEY_CONTENT_BYTE_LEN = MIN_PRIVATE_KEY_CONTENT_BIT_LEN / 8;
```

**逐行解读**:
- 第 31 行: RSA 私钥最小长度（比特），3072 位
- 第 32 行: 转换为字节长度

### AccTcpSslHelper 类定义 (行 34-86)

```cpp
class AccTcpSslHelper : public AccReferable {
public:
    AccResult Start(SSL_CTX *sslCtx, AccTlsOption &param);
    void Stop(bool afterFork = false);

    ~AccTcpSslHelper()
    {
        Stop();
    }

    void EraseDecryptData();

    static AccResult NewSslLink(bool isServer, int fd, SSL_CTX *ctx, SSL *&ssl);
    void RegisterDecryptHandler(const AccDecryptHandler &h);

private:
    AccResult InitTlsPath(AccTlsOption &param);
    AccResult InitSSL(SSL_CTX *sslCtx);

    static int CaVerifyCallback(X509_STORE_CTX *x509ctx, void *arg);
    static int ProcessCrlAndVerifyCert(std::vector<std::string> paths, X509_STORE_CTX *x509ctx);
    AccResult ReadFile(const std::string &path, std::string &content);
    AccResult LoadCaCert(SSL_CTX *sslCtx);
    AccResult LoadServerCert(SSL_CTX *sslCtx);
    AccResult LoadPrivateKey(SSL_CTX *sslCtx);
    AccResult CertVerify(X509 *cert) const;
    AccResult CheckCertExpiredTask();
    AccResult StartCheckCertExpired();
    void StopCheckCertExpired(bool afterFork);
    AccResult HandleCertExpiredCheck() const;
    static AccResult CertExpiredCheck(std::string path, std::string type);
    void ReadCheckCertParams();
    AccResult GetPkPass();

private:
    AccDecryptHandler mDecryptHandler_ = nullptr; // 解密回调
    std::pair<char *, int> mKeyPass = {nullptr, 0};
    std::thread checkExpiredThread;
    std::mutex mMutex;
    std::condition_variable mCond;
    bool checkExpiredRunning = false;
    int32_t certCheckAheadDays = 0;
    int32_t checkPeriodHours = 0;

    std::string crlFullPath;
    // 证书相关路径
    std::string tlsTopPath;
    std::string tlsCert;
    std::string tlsPk;
    std::string tlsPkPwd;
    std::vector<std::string> tlsCaPaths;
    std::vector<std::string> tlsCrlPaths;
};
```

**逐行解读**:
- 第 36-37 行: 启动和停止方法
- 第 39-42 行: 析构函数自动调用 Stop
- 第 44 行: 擦除解密数据
- 第 46 行: 创建 SSL 链接（静态）
- 第 47 行: 注册解密处理器
- 第 50-65 行: 私有方法
- 第 68-85 行: 私有成员
  - 解密回调
  - 密钥密码
  - 检查过期线程
  - 证书相关路径

### Start() - 启动 SSL 助手 (行 39-64)

```cpp
AccResult AccTcpSslHelper::Start(SSL_CTX *sslCtx, AccTlsOption &param)
{
    SSL_LAYER_CHECK_RET(InitTlsPath(param) != ACC_OK, "Failed to initialize tls parameters");

    if (mDecryptHandler_ == nullptr && !tlsPkPwd.empty()) {
        LOG_ERROR("with private key password, decrypt handler must be set");
        return ACC_ERROR;
    }

    ReadCheckCertParams();
    auto ret = StartCheckCertExpired();
    if (ret != ACC_OK) {
        LOG_ERROR("check cert expired failed");
        Stop();
        return ACC_ERROR;
    }

    ret = InitSSL(sslCtx);
    if (ret != ACC_OK) {
        LOG_ERROR("load init ssl failed");
        Stop();
        return ACC_ERROR;
    }

    return ACC_OK;
}
```

**逐行解读**:
- 第 41 行: 初始化 TLS 路径参数
- 第 43-46 行: 检查私钥密码需要解密处理器
- 第 48 行: 读取证书检查参数
- 第 49-54 行: 启动证书过期检查
- 第 56-61 行: 初始化 SSL
- 第 63 行: 返回成功

### InitTlsPath() - 初始化 TLS 路径 (行 66-96)

```cpp
AccResult AccTcpSslHelper::InitTlsPath(AccTlsOption &param)
{
    tlsTopPath = param.tlsTopPath;
    tlsCert = param.tlsCert;
    tlsPk = param.tlsPk;
    tlsPkPwd = param.tlsPkPwd;

    tlsCaPaths.clear();
    const std::string caDir = tlsTopPath + "/" + param.tlsCaPath;
    for (auto &file : param.tlsCaFile) {
        auto tmpPath = caDir + "/" + file;
        if (!mf::FileUtil::Realpath(tmpPath)) {
            LOG_ERROR("Failed to check ca path with ca file");
            return ACC_ERROR;
        }
        tlsCaPaths.emplace_back(tmpPath);
    }

    tlsCrlPaths.clear();
    const std::string crlDir = tlsTopPath + "/" + param.tlsCrlPath;
    for (auto &file : param.tlsCrlFile) {
        auto tmpPath = crlDir + "/" + file;
        if (!mf::FileUtil::Realpath(tmpPath)) {
            LOG_ERROR("Failed to check crl path with crl file");
            return ACC_ERROR;
        }
        tlsCrlPaths.emplace_back(tmpPath);
    }

    return ACC_OK;
}
```

**逐行解读**:
- 第 68-71 行: 保存证书和私钥路径
- 第 73-82 行: 构建并验证 CA 文件路径
- 第 84-93 行: 构建并验证 CRL 文件路径

### InitSSL() - 初始化 SSL (行 104-133)

```cpp
AccResult AccTcpSslHelper::InitSSL(SSL_CTX *sslCtx)
{
    auto ret = OpenSslApiWrapper::OpensslInitSsl(0, nullptr);
    SSL_LAYER_CHECK_RET((ret <= 0), "Failed to init openssl");

    ret = OpenSslApiWrapper::OpensslInitSsl(OpenSslApiWrapper::OPENSSL_INIT_LOAD_SSL_STRINGS |
                                                OpenSslApiWrapper::OPENSSL_INIT_LOAD_CRYPTO_STRINGS,
                                            nullptr);
    SSL_LAYER_CHECK_RET((ret <= 0), "Failed to load error strings");

    auto sslRet = OpenSslApiWrapper::SslCtxCtrl(sslCtx, OpenSslApiWrapper::SSL_CTRL_SET_MIN_PROTO_VERSION,
                                                OpenSslApiWrapper::TLS1_3_VERSION, nullptr);
    SSL_LAYER_CHECK_RET(sslRet <= 0, "Failed to set ssl proto version");

    ret = OpenSslApiWrapper::SslCtxSetCipherSuites(sslCtx, "TLS_AES_128_GCM_SHA256:"
                                                       "TLS_AES_256_GCM_SHA384:"
                                                       "TLS_CHACHA20_POLY1305_SHA256:"
                                                       "TLS_AES_128_CCM_SHA256");
    SSL_LAYER_CHECK_RET(ret <= 0, "Failed to set cipher suites to TLS context");

    ret = LoadCaCert(sslCtx);
    SSL_LAYER_CHECK_RET(ret != ACC_OK, "Failed to load ca cert");

    ret = LoadServerCert(sslCtx);
    SSL_LAYER_CHECK_RET(ret != ACC_OK, "Failed to load server cert");

    ret = LoadPrivateKey(sslCtx);
    SSL_LAYER_CHECK_RET(ret != ACC_OK, "Failed to load private key");
    return ACC_OK;
}
```

**逐行解读**:
- 第 106-107 行: 初始化 OpenSSL
- 第 109-112 行: 加载错误字符串
- 第 114-116 行: 设置最小协议版本为 TLS 1.3
- 第 118-122 行: 设置加密套件
  - AES_128_GCM_SHA256
  - AES_256_GCM_SHA384
  - CHACHA20_POLY1305_SHA256
  - AES_128_CCM_SHA256
- 第 124-125 行: 加载 CA 证书
- 第 127-128 行: 加载服务器证书
- 第 130-131 行: 加载私钥

### LoadCaCert() - 加载 CA 证书 (行 135-175)

```cpp
AccResult AccTcpSslHelper::LoadCaCert(SSL_CTX *sslCtx)
{
    // 设置校验函数
    OpenSslApiWrapper::SslCtxSetVerify(
        sslCtx, OpenSslApiWrapper::SSL_VERIFY_PEER | OpenSslApiWrapper::SSL_VERIFY_FAIL_IF_NO_PEER_CERT, nullptr);

    if (!tlsCrlPaths.empty()) {
        crlFullPath = "";
        bool isFirstFile = true;
        for (const auto &crlFile : tlsCrlPaths) {
            if (isFirstFile) {
                isFirstFile = false;
            } else {
                crlFullPath += ",";
            }
            crlFullPath += crlFile;
        }
        OpenSslApiWrapper::SslCtxSetCertVerifyCallback(
            sslCtx, CaVerifyCallback, reinterpret_cast<void *>(const_cast<char *>(crlFullPath.c_str())));
    }

    for (auto &caFile : tlsCaPaths) {
        FILE *fp = fopen(caFile.c_str(), "r");
        if (!fp) {
            LOG_ERROR("Failed to open ca file");
            return ACC_ERROR;
        }
        X509 *ca = OpenSslApiWrapper::PemReadX509(fp, NULL, NULL, NULL);
        fclose(fp);
        auto res = CertVerify(ca);
        OpenSslApiWrapper::X509Free(ca);
        if (res != ACC_OK) {
            LOG_ERROR("Failed to verify ca");
            return ACC_ERROR;
        }
        auto ret = OpenSslApiWrapper::SslCtxLoadVerifyLocations(sslCtx, caFile.c_str(), nullptr);
        SSL_LAYER_CHECK_RET(ret <= 0, "TLS load verify file failed");
    }

    return ACC_OK;
}
```

**逐行解读**:
- 第 138-139 行: 设置验证模式
  - SSL_VERIFY_PEER: 验证对端证书
  - SSL_VERIFY_FAIL_IF_NO_PEER_CERT: 无证书时允许继续
- 第 141-154 行: 处理 CRL 文件列表
  - 构建逗号分隔的路径字符串
  - 设置 CRL 验证回调
- 第 156-172 行: 加载每个 CA 证书
  - 打开文件
  - 读取证书
  - 验证证书
  - 加载验证位置

### LoadPrivateKey() - 加载私钥 (行 191-241)

```cpp
AccResult AccTcpSslHelper::LoadPrivateKey(SSL_CTX *sslCtx)
{
    auto tmpPath = tlsTopPath + tlsPk;
    if (!mf::FileUtil::Realpath(tmpPath)) {
        LOG_ERROR("Failed to get private key path");
        return ACC_ERROR;
    }

    int ret = 0;
    auto tmpTlsPriKeyPwdPath = tlsTopPath + tlsPkPwd;
    if (!tlsPkPwd.empty()) {
        std::string cipher;
        auto ret = ReadFile(tmpTlsPriKeyPwdPath, cipher);
        if (ret != ACC_OK) {
            LOG_ERROR("Read private key file failed");
            return ACC_ERROR;
        }
        auto buffer = new (std::nothrow) char[cipher.length()];
        if (buffer == nullptr) {
            LOG_ERROR("allocate memory for buffer failed");
            return ACC_ERROR;
        }
        auto dataLength = static_cast<int>(cipher.length());
        ret = static_cast<AccResult>(mDecryptHandler_(cipher.c_str(), cipher.length(), buffer, dataLength));
        if (ret != ACC_OK) {
            LOG_ERROR("Failed to decrypt private key password");
            delete[] buffer;
            buffer = nullptr;
            return ret;
        }
        mKeyPass = std::make_pair(buffer, dataLength);
        OpenSslApiWrapper::SslCtxSetDefaultPasswdCbUserdata(sslCtx, mKeyPass.first);
    }

    /* load private key */
    ret = OpenSslApiWrapper::SslCtxUsePrivateKeyFile(sslCtx, tmpPath.c_str(), OpenSslApiWrapper::SSL_FILETYPE_PEM);
    if (ret <= 0) {
        LOG_ERROR("Failed to set use private key file");
        EraseDecryptData();
        return ACC_ERROR;
    }

    /* check private key */
    ret = OpenSslApiWrapper::SslCtxCheckPrivateKey(sslCtx);
    if (ret <= 0) {
        LOG_ERROR("Failed to set use private key file");
        EraseDecryptData();
        return ACC_ERROR;
    }
    return ACC_OK;
}
```

**逐行解读**:
- 第 193-197 行: 验证私钥文件路径
- 第 199-223 行: 处理加密的私钥密码
  - 读取密码文件
  - 分配缓冲区
  - 调用解密回调
  - 保存解密后的密码
- 第 226 行: 加载私钥文件
- 第 234-239 行: 检查私钥有效性

### NewSslLink() - 创建 SSL 链接 (行 270-309)

```cpp
AccResult AccTcpSslHelper::NewSslLink(bool isServer, int fd, SSL_CTX *ctx, SSL *&ssl)
{
    auto tmpSsl = OpenSslApiWrapper::SslNew(ctx);
    if (tmpSsl == nullptr) {
        LOG_ERROR("Failed to new ssl object");
        return ACC_MALLOC_FAIL;
    }

    auto ret = OpenSslApiWrapper::SslSetFd(tmpSsl, fd);
    if (ret <= 0) {
        LOG_ERROR("Failed to set fd to TLS, result " << ret);
        OpenSslApiWrapper::SslFree(tmpSsl);
        tmpSsl = nullptr;
        return ACC_ERROR;
    }

    if (isServer) {
        ret = OpenSslApiWrapper::SslAccept(tmpSsl);
        if (ret <= 0) {
            int sslErr = OpenSslApiWrapper::SslGetError(tmpSsl, ret);
            LOG_ERROR("Failed to ssl accept, result " << ret << ", ssl error " << sslErr);
            OpenSslApiWrapper::SslFree(tmpSsl);
            tmpSsl = nullptr;
            return ACC_ERROR;
        }
    } else {
        ret = OpenSslApiWrapper::SslConnect(tmpSsl);
        if (ret <= 0) {
            int sslErr = OpenSslApiWrapper::SslGetError(tmpSsl, ret);
            LOG_ERROR("Failed to ssl connect, result " << ret << ", ssl error " << sslErr);
            OpenSslApiWrapper::SslFree(tmpSsl);
            tmpSsl = nullptr;
            return ACC_ERROR;
        }
    }

    // tmpSsl is free in the external function.
    ssl = tmpSsl;
    return ACC_OK;
}
```

**逐行解读**:
- 第 272-276 行: 创建 SSL 对象
- 第 278-284 行: 绑定文件描述符
- 第 286-294 行: 服务端 SSL 握手
  - SslAccept 执行 SSL 握手
  - 错误处理
- 第 295-303 行: 客户端 SSL 握手
  - SslConnect 执行 SSL 握手
  - 错误处理

### CertVerify() - 验证证书 (行 423-482)

```cpp
AccResult AccTcpSslHelper::CertVerify(X509 *cert) const
{
    if (cert == nullptr) {
        LOG_ERROR("get cert failed");
        return ACC_ERROR;
    }

    // Validity period of the proofreading certificate
    if (OpenSslApiWrapper::X509CmpCurrentTime(OpenSslApiWrapper::X509GetNotAfter(cert)) < 0) {
        LOG_ERROR("Certificate has expired! current time after cert time.");
        return ACC_ERROR;
    }
    if (OpenSslApiWrapper::X509CmpCurrentTime(OpenSslApiWrapper::X509GetNotBefore(cert)) > 0) {
        LOG_ERROR("Certificate has expired! current time before cert time.");
        return ACC_ERROR;
    }

    // The length of the private key of the verification certificate
    EVP_PKEY *pkey = OpenSslApiWrapper::X509GetPubkey(cert);
    if (pkey == nullptr) {
        LOG_ERROR("get public key failed.");
        return ACC_ERROR;
    }
    int keyLength = OpenSslApiWrapper::EvpPkeyBits(pkey);
    if (keyLength < MIN_PRIVATE_KEY_CONTENT_BIT_LEN) {
        LOG_ERROR("Certificate key length is too short, key length < " << MIN_PRIVATE_KEY_CONTENT_BIT_LEN);
        OpenSslApiWrapper::EvpPkeyFree(pkey);
        return ACC_ERROR;
    }
    OpenSslApiWrapper::EvpPkeyFree(pkey);

    // Check if the certificate is in the revocation list
    if (!tlsCrlPaths.empty()) {
        for (const auto &crlPath : tlsCrlPaths) {
            X509_CRL *crl = LoadCertRevokeListFile(crlPath.c_str());
            if (crl == nullptr) {
                LOG_WARN("Failed to load cert revocation list: " << crlPath);
                continue;
            }

            // Check if the CRL is expired
            if (OpenSslApiWrapper::X509CmpCurrentTime(OpenSslApiWrapper::X509CrlGet0NextUpdate(crl)) <= 0) {
                LOG_WARN("Crl has expired! current time after next update time. CRL path: " << crlPath);
            }

            // Check if certificate is revoked
            X509_REVOKED *revoked = nullptr;
            int result = OpenSslApiWrapper::X509CrlGet0ByCert(crl, &revoked, cert);
            if (result != 0 && revoked != nullptr) {
                LOG_ERROR("Certificate has been revoked!");
                OpenSslApiWrapper::X509CrlFree(crl);
                return ACC_ERROR;
            }

            OpenSslApiWrapper::X509CrlFree(crl);
        }
    }

    return ACC_OK;
}
```

**逐行解读**:
- 第 425-428 行: 证书指针检查
- 第 431-434 行: 检查证书是否过期
  - NotAfter: 当前时间晚于过期时间
- 第 435-438 行: 检查证书是否未生效
  - NotBefore: 当前时间早于生效时间
- 第 441-445 行: 获取并验证公钥
- 第 446-451 行: 检查私钥长度（≥3072 位）
- 第 455-479 行: 检查 CRL 吊销列表
  - 加载 CRL 文件
  - 检查 CRL 是否过期
  - 检查证书是否被吊销

### StartCheckCertExpired() - 启动证书过期检查 (行 484-498)

```cpp
AccResult AccTcpSslHelper::StartCheckCertExpired()
{
    {
        std::unique_lock<std::mutex> lockGuard{mMutex};
        checkExpiredRunning = true;
    }

    auto ret = HandleCertExpiredCheck();
    if (ret != ACC_OK) {
        return ACC_ERROR;
    }

    checkExpiredThread = std::thread([this]() { return CheckCertExpiredTask(); });
    return ret;
}
```

**逐行解读**:
- 第 487-489 行: 设置运行标志
- 第 491-494 行: 执行一次检查
- 第 496 行: 创建检查线程

### CheckCertExpiredTask() - 证书过期检查任务 (行 500-520)

```cpp
AccResult AccTcpSslHelper::CheckCertExpiredTask()
{
    while (true) {
        {
            std::unique_lock<std::mutex> lockGuard{mMutex};
            if (!checkExpiredRunning) {
                return ACC_ERROR;
            }

            mCond.wait_for(lockGuard, std::chrono::hours(this->checkPeriodHours));
            if (!checkExpiredRunning) {
                return ACC_ERROR;
            }
        }

        auto ret = HandleCertExpiredCheck();
        if (ret != ACC_OK) {
            LOG_WARN("Failed to handle cert expired check");
        }
    }
}
```

**逐行解读**:
- 第 502-513 行: 等待条件变量
  - 检查运行状态
  - 等待指定小时数
- 第 515-518 行: 执行过期检查

---

## 总结

Security 模块提供了完整的 SSL/TLS 功能：

### 1. SSL 初始化流程

```
InitSSL()
    ├── OpensslInitSsl() - 初始化 OpenSSL
    ├── OpensslInitSsl() - 加载错误字符串
    ├── SslCtxCtrl() - 设置最小协议版本 (TLS 1.3)
    ├── SslCtxSetCipherSuites() - 设置加密套件
    ├── LoadCaCert() - 加载 CA 证书
    ├── LoadServerCert() - 加载服务器证书
    └── LoadPrivateKey() - 加载私钥
```

### 2. 私钥密码处理

```
LoadPrivateKey()
    ├── 读取加密的密码文件
    ├── 分配解密缓冲区
    ├── 调用解密回调解密密码
    ├── 保存解密后的密码
    ├── SslCtxSetDefaultPasswdCbUserdata() - 设置密码回调
    ├── SslCtxUsePrivateKeyFile() - 加载私钥文件
    ├── SslCtxCheckPrivateKey() - 验证私钥
    └── EraseDecryptData() - 擦除解密数据
```

### 3. 证书验证

```
CertVerify()
    ├── X509CmpCurrentTime(X509GetNotAfter) - 检查过期时间
    ├── X509CmpCurrentTime(X509GetNotBefore) - 检查生效时间
    ├── X509GetPubkey() - 获取公钥
    ├── EvpPkeyBits() - 检查密钥长度（≥3072 位）
    └── 检查 CRL 吊销列表
```

### 4. 证书过期检查

```
StartCheckCertExpired()
    ├── ReadCheckCertParams() - 读取环境变量配置
    ├── HandleCertExpiredCheck() - 执行检查
    └── CheckCertExpiredTask() - 后台线程定期检查
```

### 5. SSL 链接创建

```
NewSslLink()
    ├── SslNew() - 创建 SSL 对象
    ├── SslSetFd() - 绑定文件描述符
    ├── 服务端: SslAccept() - SSL 握手
    ├── 客户端: SslConnect() - SSL 握手
    └── 返回 SSL 对象
```

### 6. 关键特性

1. **TLS 1.3 支持**: 强制使用 TLS 1.3 版本
2. **现代加密套件**: 支持 AES-GCM 和 ChaCha20-Poly1305
3. **证书验证**: 完整的证书链验证
4. **CRL 支持**: 证书吊销列表检查
5. **私钥加密**: 支持加密的私钥密码存储
6. **定期检查**: 后台线程定期检查证书过期
