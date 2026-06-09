# EcoCharge Dublin — Backend API

Base URL: `http://127.0.0.1:8000`
Swagger docs: `http://127.0.0.1:8000/docs`

---

## 快速启动

### 第 0 步：创建 `.env` 文件

在项目根目录 `COMP47250-Team-Software-Projec/` 下新建 `.env` 文件，复制以下内容：

```
DATABASE_URL=postgresql://postgres.surezityslscwrkgvnws:Cq3ygcvMP9%25fSWF@aws-0-eu-west-1.pooler.supabase.com:5432/postgres
```

### 第 1 步：安装依赖

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

### 第 2 步：启动 API

```bash
.venv/bin/uvicorn backend.main:app --reload
```

看到以下输出说明成功：

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

浏览器打开 `http://127.0.0.1:8000/docs` 可以直接测试所有接口。

**停止服务器：** 终端按 `Ctrl + C`

---

## 接口

### GET `/api/chargers`

返回全部 Dublin 公共 EV 充电站，GeoJSON FeatureCollection 格式。

```bash
curl http://127.0.0.1:8000/api/chargers
```

```json
{
  "type": "FeatureCollection",
  "count": 134,
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-6.182852, 53.611523] },
      "properties": {
        "id": "esb_0",
        "address": "Irish Rail, Railway Street, Balbriggan",
        "operator": "ESB eCars",
        "num_chargers": 1,
        "source_area": "ESB_national",
        "open_hours": "24 x 7"
      }
    }
  ]
}
```

---

### GET `/api/energy/latest`

返回最新一条可再生能源数据。

```bash
curl http://127.0.0.1:8000/api/energy/latest
```

```json
{
  "datetime": "2026-04-30T23:45:00+00:00",
  "wind_mw": 607.09,
  "solar_mw": 2.16,
  "total_demand_mw": 3645.06,
  "renewable_score": 0.1671
}
```

---

## 目录结构

```
backend/
├── main.py            # FastAPI 入口
├── database.py        # 数据库连接（Supabase）
├── routers/
│   ├── chargers.py    # GET /api/chargers
│   └── energy.py      # GET /api/energy/latest
├── ingest/
│   ├── load_chargers.py
│   └── load_energy.py
└── tests/
```
