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

### GET `/api/energy/timeseries`

返回时序能源数据，供前端画折线图。支持按时间范围和粒度过滤。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `days` | 正整数 或 `all` | `7` | 返回最近 N 天数据；`all` 返回全部 |
| `interval` | `15m` / `1h` / `1d` | `15m` | 数据粒度（15分钟 / 按小时聚合 / 按天聚合） |

**组合限制：**

| `days` | 允许的 `interval` |
|--------|-----------------|
| ≤ 7 | `15m`, `1h`, `1d` |
| 8 ~ 90 | `1h`, `1d` |
| > 90 或 `all` | `1d` |

违规组合返回 `400 Bad Request`。

```bash
curl "http://127.0.0.1:8000/api/energy/timeseries?days=7&interval=1h"
```

**返回字段：**

| 字段 | 说明 |
|------|------|
| `datetime` | 时间戳（UTC） |
| `wind_mw` | 风力发电量（MW） |
| `solar_mw` | 太阳能发电量（MW） |
| `total_demand_mw` | 全国总用电需求（MW） |
| `renewable_score` | 可再生能源占比（0~1） |

```json
[
  {
    "datetime": "2026-04-24T00:00:00+00:00",
    "wind_mw": 1200.0,
    "solar_mw": 3.0,
    "total_demand_mw": 3000.0,
    "renewable_score": 0.401
  }
]
```

---

### GET `/api/recommendations`

返回 K-Means 算法推荐的新 EV 充电站位置（当前 11 个），按优先级排序，GeoJSON FeatureCollection 格式。

```bash
curl http://127.0.0.1:8000/api/recommendations
```

**返回字段：**

| 字段 | 说明 |
|---|---|
| `rank` | 优先级排名（1 = 最需要建站） |
| `cluster` | K-Means 聚类编号 |
| `gap_score` | 供需缺口评分（0~1，越高越缺） |
| `traffic_volume` | 该区域平均交通流量 |
| `charger_count_nearby` | 附近现有充电桩数量 |
| `road_density` | 道路密度 |
| `distance_to_nearest_substation_m` | 距最近变电站距离（米） |
| `traffic_source` | 交通数据来源（DCC / DLR / SDCC） |
| `reason` | 推荐原因说明 |
| `k_value` | K-Means 聚类 K 值 |
| `candidate_percentile` | 候选点百分位数 |
| `minimum_spacing_m` | 最小站点间距（米） |

```json
{
  "type": "FeatureCollection",
  "count": 11,
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-6.2191, 53.4254] },
      "properties": {
        "rank": 1,
        "cluster": 5,
        "gap_score": 0.702,
        "traffic_volume": 7731.5,
        "charger_count_nearby": 0,
        "road_density": 3,
        "distance_to_nearest_substation_m": 138.2,
        "traffic_source": "DCC_2024_2025",
        "reason": "Recommended due to: high traffic volume, no existing chargers nearby",
        "k_value": 6,
        "candidate_percentile": 80,
        "minimum_spacing_m": 500
      }
    }
  ]
}
```

---

### GET `/api/scenario`

根据 EV 渗透率场景返回对应推荐站点，供 Scenario Analysis 功能使用。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ev_penetration` | `0.05` / `0.08` / `0.12` | ✅ | EV 渗透率场景 |

其他值返回 `400 Bad Request`。

```bash
curl "http://127.0.0.1:8000/api/scenario?ev_penetration=0.08"
```

**返回字段：**

| 字段 | 说明 |
|------|------|
| `rank` | 优先级排名 |
| `cluster` | K-Means 聚类编号 |
| `gap_score` | 该场景下的供需缺口评分 |
| `ev_penetration` | EV 渗透率 |
| `k_value` | K 值 |
| `candidate_percentile` | 候选点百分位数 |

```json
{
  "type": "FeatureCollection",
  "count": 11,
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-6.2191, 53.4254] },
      "properties": {
        "rank": 1,
        "cluster": 4,
        "gap_score": 0.737,
        "ev_penetration": 0.08,
        "k_value": 6,
        "candidate_percentile": 80
      }
    }
  ]
}
```

---

### GET `/api/traffic`

返回 Dublin 交通监测站点的流量数据（DLR + DCC + SDCC 三区共 1039 个站点），按流量从高到低排序。支持按数据来源过滤。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source` | `DCC` / `DLR` / `SDCC` | 无（返回全部） | 按数据来源过滤 |

```bash
curl http://127.0.0.1:8000/api/traffic
curl "http://127.0.0.1:8000/api/traffic?source=SDCC"
```

**返回字段：**

| 字段 | 说明 |
|---|---|
| `lat` | 纬度 |
| `lon` | 经度 |
| `volume` | 年均小时交通流量（辆/小时） |
| `source` | 数据来源（DCC / DLR / SDCC） |

```json
[
  { "lat": 53.344, "lon": -6.267, "volume": 1234.5, "source": "DCC" }
]
```

---

### GET `/api/windfarms`

返回 313 个爱尔兰风电场，按装机容量从高到低排序。

```bash
curl http://127.0.0.1:8000/api/windfarms
```

**返回字段：**

| 字段 | 说明 |
|---|---|
| `name` | 风电场名称 |
| `county` | 所在郡 |
| `capacity_mw` | 装机容量（MW） |
| `lat` | 纬度 |
| `lon` | 经度 |

```json
[
  { "name": "Derrybrien", "county": "Galway", "capacity_mw": 130.0, "lat": 53.05, "lon": -8.45 }
]
```

---

### GET `/api/substations`

返回变电站数据（共 7,780 个）。支持按坐标和半径过滤，用于地图图层和推荐可解释性展示。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `lat` | float | 无 | 中心点纬度（需与 `lon` 同时提供） |
| `lon` | float | 无 | 中心点经度 |
| `radius` | float | `500` | 搜索半径（米），上限 10000 |

不传 `lat`/`lon` 时返回全部 7,780 条（慎用）。

```bash
curl "http://127.0.0.1:8000/api/substations?lat=53.425&lon=-6.219&radius=500"
```

**返回字段：**

| 字段 | 说明 |
|---|---|
| `name` | 变电站名称 |
| `voltage_class` | 电压等级 |
| `lat` | 纬度 |
| `lon` | 经度 |

```json
[
  { "name": "Finglas", "voltage_class": "110kV", "lat": 53.426, "lon": -6.218 }
]
```

---

## 目录结构

```
backend/
├── main.py                              # FastAPI 入口
├── database.py                          # 数据库连接（Supabase）
├── routers/
│   ├── chargers.py                      # GET /api/chargers
│   ├── energy.py                        # GET /api/energy/latest, GET /api/energy/timeseries
│   ├── recommendations.py               # GET /api/recommendations, GET /api/scenario
│   ├── traffic.py                       # GET /api/traffic
│   └── infrastructure.py               # GET /api/windfarms, GET /api/substations
├── ingest/
│   ├── load_chargers.py                 # 导入充电站数据
│   ├── load_energy.py                   # 导入能源数据
│   ├── load_recommendations.py          # 导入 K-Means 推荐结果
│   ├── load_scenario_recommendations.py # 导入场景分析数据（ev05/08/12）
│   └── load_traffic.py                  # 导入 SCATS 交通流量数据
└── tests/
```

---

## 当前 API 汇总

| 接口 | 数据量 | 说明 |
|---|---|---|
| `GET /api/chargers` | 134 条 | Dublin EV 充电站（GeoJSON） |
| `GET /api/energy/latest` | 1 条（最新） | EirGrid 可再生能源最新一条数据 |
| `GET /api/energy/timeseries` | 可变（按 days/interval） | EirGrid 时序数据，供前端画折线图 |
| `GET /api/recommendations` | 11 条 | K-Means 推荐新建充电站位置（GeoJSON） |
| `GET /api/scenario` | 11 条（按场景） | EV 渗透率场景分析推荐（GeoJSON） |
| `GET /api/traffic` | 最多 1039 条 | SCATS 交通流量（DLR+DCC+SDCC），支持 ?source= 过滤 |
| `GET /api/windfarms` | 313 条 | 爱尔兰风电场 |
| `GET /api/substations` | 最多 7,780 条 | 变电站，支持 ?lat=&lon=&radius= 过滤 |
