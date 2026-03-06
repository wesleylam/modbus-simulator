# Modbus TCP Simulator

Hosts Modbus TCP registers from a CSV file over the network, with a live dashboard to view changes and update values.

## Quickstart

```bash
# 1. Edit your register map
nano registers.csv

# 2. Start everything
docker-compose up --build

# 3. Open dashboard
open http://localhost:3000

# 4. Point your Modbus client at
#    Host: <your machine IP>   Port: 502
```

## CSV Format

| Column    | Required | Values                              |
|-----------|----------|-------------------------------------|
| `address` | ✓        | Integer (e.g. `1`, `100`)           |
| `type`    | ✓        | `coil`, `discrete`, `holding`, `input` |
| `name`    | ✓        | Human-readable label                |
| `value`   | ✓        | Integer or `0`/`1`                  |
| `access`  | ✓        | `R` (read-only) or `RW` (read-write) |

### Example

```csv
address,type,name,value,access
1,holding,pump_speed,0,RW
2,input,inlet_pressure,0,R
3,coil,pump_enable,0,RW
4,discrete,fault_active,0,R
```

## API Reference

### Registers

| Method  | Path                  | Description                        |
|---------|-----------------------|------------------------------------|
| `GET`   | `/registers`          | List all registers + live values   |
| `GET`   | `/registers/{addr}`   | Get single register                |
| `PATCH` | `/registers/{addr}`   | Update value `{"value": 42}`       |

### Config

| Method  | Path              | Description                        |
|---------|-------------------|------------------------------------|
| `POST`  | `/config/reload`  | Hot-reload CSV from disk           |
| `POST`  | `/config/upload`  | Upload a new CSV file              |

### Health

| Method | Path      | Description                              |
|--------|-----------|------------------------------------------|
| `GET`  | `/status` | Server status, register count, WS clients |

## WebSocket

Connect to `ws://<host>:8000/ws`

**On connect** — receives a snapshot:
```json
{ "type": "snapshot", "registers": [...] }
```

**On every register change**:
```json
{
  "type": "update",
  "address": 1,
  "old_value": 0,
  "new_value": 100,
  "source": "modbus",
  "client_ip": "192.168.1.50",
  "timestamp": 1712345678.123
}
```

## Supported Modbus Function Codes

| FC  | Name                          |
|-----|-------------------------------|
| 01  | Read Coils                    |
| 02  | Read Discrete Inputs          |
| 03  | Read Holding Registers        |
| 04  | Read Input Registers          |
| 05  | Write Single Coil             |
| 06  | Write Single Holding Register |
| 15  | Write Multiple Coils          |
| 16  | Write Multiple Holding Registers |

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
CSV_PATH=../registers.csv python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:3000 — proxies to backend automatically
```

## Hot-swapping the register map

Edit `registers.csv`, then either:
- Call `POST /config/reload` (keeps server running)
- Use the "↺ Reload CSV" button in the dashboard
- Upload a new file with "⬆ Upload CSV"
