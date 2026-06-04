# app/api.py
from __future__ import annotations

import logging
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from config.logging_config import setup_logging
from database.ch import ClickHouseRepo
from service.analyzer import SlowQueryAnalyzerService
from service.mongo_collector import MongoProfileCollectorService
from service.mongo_analyzer import MongoSlowQueryAnalyzerService


setup_logging(logging.INFO)

app = FastAPI(title="Slow Query AI Analyzer", version="0.1.0")

ch_repo = ClickHouseRepo()
mysql_service = SlowQueryAnalyzerService()
mongo_collector = MongoProfileCollectorService()
mongo_analyzer = MongoSlowQueryAnalyzerService()



@app.get("/health")
def health():
    """
    健康检查接口。
    """
    return {"status": "ok"}


@app.get("/analyses")
def latest_analyses(limit: int = 20):
    """
    返回最新的 AI 分析摘要，供前端或 Metabase 查询。
    """
    return {"items": ch_repo.list_latest_mysql_analyses(limit=limit)}


@app.get("/analysis/{db_type}/{db_name}/{sql_fingerprint}")
def analysis_detail(db_type: str, db_name: str, sql_fingerprint: str):
    """
    返回某个 SQL 指纹的详细分析记录。
    """
    rows = ch_repo.get_analysis_detail(
        db_type=db_type,
        db_name=db_name,
        sql_fingerprint=sql_fingerprint,
    )
    return {"items": rows}


@app.post("/mongo/collect-once")
def mongo_collect_once():
    return mongo_collector.run_once()


@app.post("/mongo/analyze-once")
def mongo_analyze_once(days: int = 7, limit: int = 20):
    return mongo_analyzer.run_once(days=days, limit=limit)


@app.get("/analyses")
def analyses(limit: int = 20):
    return {
        "mysql": ch_repo.list_latest_mysql_analyses(limit=limit),
        "mongodb": ch_repo.list_latest_mongo_analyses(limit=limit),
    }


@app.post("/run-once")
def run_once(
    db_type: str = Query(..., description="mysql or mongodb"),
    days: int = 7,
    limit: int = 20,
):
    db_type = db_type.lower().strip()

    if db_type == "mysql":
        result = mysql_service.run_once(days=days, limit=limit)
        return {"db_type": "mysql", "result": result}

    if db_type == "mongodb":
        collect_result = mongo_collector.run_once()
        analyze_result = mongo_analyzer.run_once(days=days, limit=limit)
        return {
            "db_type": "mongodb",
            "collect_result": collect_result,
            "analyze_result": analyze_result,
        }

    return {"error": f"unsupported db_type: {db_type}"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(limit: int = 20):
    mysql_items = ch_repo.list_latest_mysql_analyses(limit=limit)
    mongo_items = ch_repo.list_latest_mongo_analyses(limit=limit)

    mysql_cards = []
    for item in mysql_items:
        mysql_cards.append(f"""
        <div class="card">
          <div class="card-head">
            <div>
              <div class="title">{item["db_name"]}</div>
              <div class="sub">MySQL · {item["sql_fingerprint"]}</div>
            </div>
            <span class="badge {item["risk_level"].lower()}">{item["risk_level"]}</span>
          </div>
          <pre class="sql">{item["sample_sql"]}</pre>
          <div class="metric">总结：{item["summary"]}</div>
          <div class="metric">根因：{item["root_cause"]}</div>
          <div class="metric">建议：{item["optimization_suggestion"]}</div>
          <div class="metric">索引：{item["index_suggestion"]}</div>
          <div class="metric">预估收益：{item["estimated_improvement"]}</div>
          <details>
            <summary>优化后的 SQL</summary>
            <pre class="sql">{item["optimized_sql"]}</pre>
          </details>
        </div>
        """)

    mongo_cards = []
    for item in mongo_items:
        mongo_cards.append(f"""
        <div class="card">
          <div class="card-head">
            <div>
              <div class="title">{item["db_name"]}.{item["collection_name"]}</div>
              <div class="sub">MongoDB · {item["operation_type"]} · {item["fingerprint"]}</div>
            </div>
            <span class="badge {item["risk_level"].lower()}">{item["risk_level"]}</span>
          </div>
          <pre class="sql">{item["sample_query"]}</pre>
          <div class="metric">总结：{item["summary"]}</div>
          <div class="metric">根因：{item["root_cause"]}</div>
          <div class="metric">建议：{item["optimization_suggestion"]}</div>
          <div class="metric">索引：{item["index_suggestion"]}</div>
          <div class="metric">预估收益：{item["estimated_improvement"]}</div>
          <details>
            <summary>优化后的查询</summary>
            <pre class="sql">{item["optimized_query"]}</pre>
          </details>
        </div>
        """)

    html = f"""
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <title>Slow Query AI Dashboard</title>
      <style>
        body {{
          margin: 0;
          font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial;
          background: #f6f8fc;
          color: #0f172a;
        }}
        .wrap {{
          max-width: 1280px;
          margin: 0 auto;
          padding: 28px;
        }}
        .hero {{
          background: linear-gradient(135deg, #eef4ff, #f7f1ff);
          border: 1px solid #e5e7eb;
          border-radius: 20px;
          padding: 24px;
          margin-bottom: 20px;
        }}
        h1 {{ margin: 0 0 8px 0; }}
        .actions {{
          margin-top: 12px;
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          align-items: center;
        }}
        .btn {{
          border: 0;
          border-radius: 999px;
          padding: 10px 16px;
          cursor: pointer;
          font-weight: 600;
          background: #2563eb;
          color: white;
        }}
        .btn.secondary {{
          background: #7c3aed;
        }}
        .btn:disabled {{
          opacity: 0.6;
          cursor: not-allowed;
        }}
        .status {{
          font-size: 14px;
          color: #475569;
        }}
        .section {{
          margin-top: 22px;
        }}
        .section-title {{
          font-size: 20px;
          font-weight: 700;
          margin: 0 0 12px 0;
        }}
        .grid {{
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
          gap: 16px;
        }}
        .card {{
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 18px;
          padding: 18px;
          box-shadow: 0 4px 18px rgba(15,23,42,0.05);
        }}
        .card-head {{
          display:flex;
          justify-content:space-between;
          gap:12px;
          align-items:flex-start;
          margin-bottom: 12px;
        }}
        .title {{ font-size: 18px; font-weight: 700; }}
        .sub {{ font-size: 12px; color: #64748b; margin-top: 4px; word-break: break-all; }}
        .badge {{
          padding: 6px 10px;
          border-radius: 999px;
          color: white;
          font-size: 12px;
          font-weight: 700;
        }}
        .low {{ background: #22c55e; }}
        .medium {{ background: #f59e0b; }}
        .high {{ background: #ef4444; }}
        .critical {{ background: #7c3aed; }}
        .sql {{
          white-space: pre-wrap;
          background: #0f172a;
          color: #e2e8f0;
          padding: 12px;
          border-radius: 12px;
          overflow-x: auto;
          font-size: 13px;
        }}
        .metric {{
          margin-top: 10px;
          line-height: 1.65;
          font-size: 14px;
        }}
        details {{
          margin-top: 12px;
        }}
        summary {{
          cursor: pointer;
          font-weight: 600;
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>Slow Query AI Dashboard</h1>
          <div>统一查看 MySQL 和 MongoDB 的慢查询分析结果。</div>
          <div class="actions">
            <a href="/docs">API Docs</a>
            <a href="/analyses" style="margin-left:8px;">JSON data</a>
            <button class="btn" id="runMysqlBtn">Run MySQL</button>
            <button class="btn secondary" id="runMongoBtn">Run MongoDB</button>
            <span class="status" id="runStatus"></span>
          </div>
        </div>

        <div class="section">
          <div class="section-title">MySQL 分析结果</div>
          <div class="grid">
            {''.join(mysql_cards) if mysql_cards else '<div>暂无 MySQL 分析结果。点击 Run MySQL 生成一批。</div>'}
          </div>
        </div>

        <div class="section">
          <div class="section-title">MongoDB 分析结果</div>
          <div class="grid">
            {''.join(mongo_cards) if mongo_cards else '<div>暂无 MongoDB 分析结果。点击 Run MongoDB 生成一批。</div>'}
          </div>
        </div>
      </div>

      <script>
        const runStatus = document.getElementById("runStatus");
        const runMysqlBtn = document.getElementById("runMysqlBtn");
        const runMongoBtn = document.getElementById("runMongoBtn");

        async function runJob(dbType) {{
          runMysqlBtn.disabled = true;
          runMongoBtn.disabled = true;
          runStatus.textContent = dbType === "mysql"
            ? "正在执行 MySQL 分析..."
            : "正在执行 MongoDB 采集与分析...";

          try {{
            const resp = await fetch(`/run-once?db_type=${{dbType}}&days=7&limit=20`, {{
              method: "POST",
              headers: {{
                "Content-Type": "application/json"
              }}
            }});

            if (!resp.ok) {{
              throw new Error(`HTTP ${{resp.status}}`);
            }}

            const data = await resp.json();

            if (dbType === "mysql") {{
              const r = data.result;
              runStatus.textContent = `MySQL 完成：scanned=${{r.scanned}}, analyzed=${{r.analyzed}}, skipped=${{r.skipped}}, failed=${{r.failed}}`;
            }} else {{
              const c = data.collect_result;
              const a = data.analyze_result;
              runStatus.textContent = `MongoDB 完成：collect=${{c.scanned}}/${{c.inserted}}，analyze scanned=${{a.scanned}}, analyzed=${{a.analyzed}}, skipped=${{a.skipped}}, failed=${{a.failed}}`;
            }}

            setTimeout(() => window.location.reload(), 1200);
          }} catch (err) {{
            runStatus.textContent = "执行失败：" + err.message;
          }} finally {{
            runMysqlBtn.disabled = false;
            runMongoBtn.disabled = false;
          }}
        }}

        runMysqlBtn.addEventListener("click", () => runJob("mysql"));
        runMongoBtn.addEventListener("click", () => runJob("mongodb"));
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)