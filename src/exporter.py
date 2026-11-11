
import html
import json
from pathlib import Path


class ReportExporter:

    @staticmethod
    def export_json(
        data: dict,
        file_path: str | Path,
    ) -> None:
        """Экспортирует данные в JSON."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4,
            )

    @staticmethod
    def export_html(
        stats: dict,
        file_path: str | Path,
    ) -> None:
        """Создаёт HTML-отчёт со статистикой crawler."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        status_distribution = stats.get("status_distribution", {})
        top_domains = stats.get("top_domains", [])

        max_status = max(status_distribution.values(), default=1)
        max_domain = max(
            (item["pages"] for item in top_domains),
            default=1,
        )

        status_rows = ""
        for status, count in status_distribution.items():
            width = count / max_status * 100

            status_rows += f"""
                <tr>
                    <td>{html.escape(str(status))}</td>
                    <td>{count}</td>
                    <td>
                        <div class="bar">
                            <div class="bar-fill" style="width: {width}%"></div>
                        </div>
                    </td>
                </tr>
            """

        domain_rows = ""
        for item in top_domains:
            domain = html.escape(str(item["domain"]))
            count = item["pages"]
            width = count / max_domain * 100

            domain_rows += f"""
                <tr>
                    <td>{domain}</td>
                    <td>{count}</td>
                    <td>
                        <div class="bar">
                            <div class="bar-fill" style="width: {width}%"></div>
                        </div>
                    </td>
                </tr>
            """

        pages = stats.get("pages_processed", 0)
        successful = stats.get("successful_pages", 0)
        failed = stats.get("failed_pages", 0)
        runtime = stats.get("runtime_seconds", 0)
        speed = stats.get("pages_per_second", 0)

        report = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Crawler Report</title>

            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f4f6f9;
                    margin: 0;
                    padding: 30px;
                    color: #222;
                }}

                .container {{
                    max-width: 1000px;
                    margin: auto;
                }}

                h1, h2 {{
                    color: #263238;
                }}

                .metrics {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                    gap: 15px;
                    margin: 25px 0;
                }}

                .card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }}

                .value {{
                    font-size: 26px;
                    font-weight: bold;
                    margin-top: 10px;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    margin-bottom: 30px;
                }}

                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #eee;
                }}

                th {{
                    background: #263238;
                    color: white;
                }}

                .bar {{
                    background: #e8edf2;
                    height: 12px;
                    border-radius: 6px;
                    overflow: hidden;
                }}

                .bar-fill {{
                    background: #3498db;
                    height: 100%;
                }}
            </style>
        </head>

        <body>
            <div class="container">
                <h1>Crawler Report</h1>

                <div class="metrics">
                    <div class="card">
                        Pages processed
                        <div class="value">{pages}</div>
                    </div>

                    <div class="card">
                        Successful pages
                        <div class="value">{successful}</div>
                    </div>

                    <div class="card">
                        Failed pages
                        <div class="value">{failed}</div>
                    </div>

                    <div class="card">
                        Runtime
                        <div class="value">{runtime} sec</div>
                    </div>

                    <div class="card">
                        Pages per second
                        <div class="value">{speed}</div>
                    </div>
                </div>

                <h2>HTTP Status Distribution</h2>

                <table>
                    <tr>
                        <th>Status</th>
                        <th>Count</th>
                        <th>Distribution</th>
                    </tr>
                    {status_rows}
                </table>

                <h2>Top Domains</h2>

                <table>
                    <tr>
                        <th>Domain</th>
                        <th>Pages</th>
                        <th>Distribution</th>
                    </tr>
                    {domain_rows}
                </table>
            </div>
        </body>
        </html>
        """

        path.write_text(report, encoding="utf-8")
