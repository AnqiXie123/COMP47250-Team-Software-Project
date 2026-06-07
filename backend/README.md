# EcoCharge Dublin — 后端启动与配置指南

## 环境要求

- macOS（Apple Silicon 或 Intel）
- Python 3.14（已通过 Homebrew 安装）
- PostgreSQL 17 + PostGIS（通过 Homebrew 安装）

---

## 第一次配置（只需做一次）

### 1. 安装数据库

```bash
brew install postgresql@17
brew install postgis
```

将 PostgreSQL 加入 PATH（如果还没加）：

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2. 启动 PostgreSQL 服务

```bash
brew services start postgresql@17
```

验证是否正常运行：

```bash
psql -l
```

能看到数据库列表说明成功。

### 3. 建库并初始化表结构

```bash
createdb ecocharge
psql -d ecocharge -f backend/schema_local.sql
```

> 说明：`schema_local.sql` 是本地开发用的精简版 schema，去掉了 TimescaleDB（Docker 部署时才需要）。
> 这是项目风险清单中的 Sprint 2 fallback 方案，Sprint 4 再统一用 Docker 加上 TimescaleDB。

### 4. 创建 Python 虚拟环境并安装依赖

在项目根目录（`COMP47250-Team-Software-Projec/`）下执行：

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

### 5. 导入初始数据

先导入充电站数据：

```bash
.venv/bin/python -m backend.ingest.load_chargers
```

输出：`Loaded 134 EV charger records into ev_chargers.`

再导入 EirGrid 能源数据：

```bash
.venv/bin/python -m backend.ingest.load_energy
```

输出：`Loaded 11516 energy records into renewable_energy.`

> 两个脚本都可以重复执行，不会产生重复数据。

---

## 日常启动

### 启动 PostgreSQL（如果没有设置开机自启）

```bash
brew services start postgresql@17
```

### 启动 API 服务器

在项目根目录（`COMP47250-Team-Software-Projec/`）下执行：

```bash
.venv/bin/uvicorn backend.main:app --reload
```

服务器默认运行在 `http://127.0.0.1:8000`，`--reload` 参数让代码修改后自动重启。

### 停止服务器

在运行服务器的终端按 `Ctrl + C`。

---

## 接口说明

| 接口 | 说明 |
|---|---|
| `GET /api/chargers` | 返回全部 134 个 Dublin 公共充电站（id、坐标、运营商等） |
| `GET /api/energy/latest` | 返回最新一条 EirGrid 可再生能源数据（风电、光伏、可再生评分） |

### 示例请求

```bash
curl http://127.0.0.1:8000/api/chargers
curl http://127.0.0.1:8000/api/energy/latest
```

### Swagger 交互文档

浏览器打开：`http://127.0.0.1:8000/docs`

---

## 运行测试

```bash
.venv/bin/pytest backend/tests/ -v
```

当前共 6 个测试，全部应通过。测试使用 mock 数据库，不需要连接真实 PostgreSQL。

---

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://localhost/ecocharge` | 数据库连接地址，本地不需要改 |

如需修改数据库地址：

```bash
export DATABASE_URL="postgresql+asyncpg://用户名:密码@地址/ecocharge"
.venv/bin/uvicorn backend.main:app --reload
```

---

## 目录结构

```
backend/
├── README.md              # 本文档
├── schema_local.sql       # 本地建表 SQL（无 TimescaleDB）
├── requirements.txt       # Python 依赖
├── database.py            # 数据库连接配置
├── main.py                # FastAPI 入口
├── routers/
│   ├── chargers.py        # GET /api/chargers
│   └── energy.py          # GET /api/energy/latest
├── ingest/
│   ├── load_chargers.py   # 导入充电站数据（一次性）
│   └── load_energy.py     # 导入能源数据（一次性）
└── tests/
    ├── test_chargers.py   # 充电站接口测试
    └── test_energy.py     # 能源接口测试
```
