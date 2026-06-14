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

所有接口均返回 JSON，无需鉴权。

---

### GET `/api/chargers`

返回 Dublin 全部 134 个公共 EV 充电站，GeoJSON FeatureCollection 格式。

```bash
curl http://127.0.0.1:8000/api/chargers
```

**返回字段：**

| 字段 | 说明 |
|---|---|
| `id` | 充电站唯一 ID（如 `esb_0`、`dlr_3`） |
| `address` | 地址 |
| `operator` | 运营商（ESB eCars / EasyGo 等） |
| `num_chargers` | 充电桩数量 |
| `source_area` | 数据来源（ESB_national / DLR / SDCC） |
| `open_hours` | 开放时间 |

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

返回最新一条 EirGrid 可再生能源数据（15 分钟间隔）。

```bash
curl http://127.0.0.1:8000/api/energy/latest
```

**返回字段：**

| 字段 | 说明 |
|---|---|
| `datetime` | 时间戳（UTC） |
| `wind_mw` | 风力发电量（MW） |
| `solar_mw` | 太阳能发电量（MW） |
| `total_demand_mw` | 全国总用电需求（MW） |
| `renewable_score` | 可再生能源占比（0~1，越高越绿色） |

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

### GET `/api/recommendations`

返回 K-Means 算法推荐的 10 个新 EV 充电站位置，按优先级排序（rank 1 最优先），GeoJSON FeatureCollection 格式。

```bash
curl http://127.0.0.1:8000/api/recommendations
```

**返回字段：**

| 字段 | 说明 |
|---|---|
| `rank` | 优先级排名（1 = 最需要建站） |
| `cluster_id` | K-Means 聚类编号 |
| `gap_score` | 供需缺口评分（越高越缺充电桩） |
| `traffic_volume` | 该区域平均交通流量 |
| `charger_count_nearby` | 附近现有充电桩数量 |
| `renewable_score` | 可再生能源评分 |

```json
{
  "type": "FeatureCollection",
  "count": 10,
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-6.1501, 53.2766] },
      "properties": {
        "rank": 1,
        "cluster_id": 5,
        "gap_score": 2120.1,
        "traffic_volume": 2120.1,
        "charger_count_nearby": 0.0,
        "renewable_score": 0.4102
      }
    }
  ]
}
```

---

### GET `/api/traffic`

返回 223 个 Dublin SCATS 交通监测站点的交通流量数据，按流量从高到低排序。

```bash
curl http://127.0.0.1:8000/api/traffic
```

**返回字段：**

| 字段 | 说明 |
|---|---|
| `lat` | 纬度 |
| `lon` | 经度 |
| `volume` | 年均小时交通流量（辆/小时） |

```json
[
  { "lat": 53.344, "lon": -6.267, "volume": 1234.5 },
  { "lat": 53.351, "lon": -6.258, "volume": 1100.2 }
]
```

**测试方式：**
- 浏览器访问：`http://127.0.0.1:8000/api/traffic`
- Swagger UI：`http://127.0.0.1:8000/docs` → 找到 `/api/traffic` → 点击 Try it out → Execute

---

## 目录结构

```
backend/
├── main.py                    # FastAPI 入口
├── database.py                # 数据库连接（Supabase）
├── routers/
│   ├── chargers.py            # GET /api/chargers
│   ├── energy.py              # GET /api/energy/latest
│   ├── recommendations.py     # GET /api/recommendations
│   └── traffic.py             # GET /api/traffic
├── ingest/
│   ├── load_chargers.py       # 导入充电站数据
│   ├── load_energy.py         # 导入能源数据
│   ├── load_recommendations.py# 导入 K-Means 推荐结果
│   └── load_traffic.py        # 导入 SCATS 交通流量数据
└── tests/
```
