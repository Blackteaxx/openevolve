#!/usr/bin/env python3
import os
import json
import shutil
import argparse
import logging
from typing import Dict, Any, List


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


def find_code_field(d: Dict[str, Any]) -> str | None:
    candidates = [
        "program",
        "code",
        "content",
        "text",
        "program_code",
        "source_code",
        "body",
    ]
    for key in candidates:
        v = d.get(key)
        if isinstance(v, str) and v.strip():
            return v
    for key, v in d.items():
        if isinstance(v, dict):
            nested = find_code_field(v)
            if nested:
                return nested
    return None


def read_code(path: str) -> str:
    try:
        ext = os.path.splitext(path)[1].lower()
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            if ext == ".json":
                data = json.load(f)
                code = find_code_field(data) or ""
            else:
                code = f.read()
        return code
    except Exception as e:
        logging.warning(f"读取代码失败: {path}: {type(e).__name__}: {e}")
        return ""


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generate_single_page(output_dir: str, clusters: Dict[int, List[int]], index: List[Dict[str, Any]]):
    total = sum(len(v) for v in clusters.values())
    # 构造嵌入的数据：每个簇的程序条目及代码内容
    clusters_full: Dict[int, List[Dict[str, Any]]] = {}
    for cid, members in clusters.items():
        items: List[Dict[str, Any]] = []
        for mid in members:
            item = index[mid]
            code = read_code(item.get("path", ""))
            items.append({
                "id": item.get("id", mid),
                "path": item.get("path", ""),
                "code": code,
            })
        clusters_full[int(cid)] = items

    # 生成单页 HTML，包含交互脚本与内联数据
    html = []
    html.append("<!DOCTYPE html>")
    html.append("<html lang=\"zh-CN\">")
    html.append("<head>")
    html.append("<meta charset=\"UTF-8\">")
    html.append("<title>按簇展示与对比</title>")
    html.append("<link rel=\"stylesheet\" href=\"static/css/main.css\">")
    html.append("<style>")
    html.append("body{padding:20px}")
    html.append(".cluster-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin:10px 0}")
    html.append(".cluster-card{padding:12px;border:1px solid #ddd;border-radius:8px;cursor:pointer;background:#fafafa}")
    html.append(".badge{background:#eee;border-radius:6px;padding:2px 8px;margin-left:8px}")
    html.append(".cluster-section{margin:16px 0;padding:12px;border:1px solid #ddd;border-radius:8px}")
    html.append(".program{margin:14px 0;padding:10px;border:1px solid #eee;border-radius:6px}")
    html.append("pre{background:#f5f5f5;padding:10px;border-radius:6px;white-space:pre-wrap;word-break:break-word;max-height:none !important;overflow:visible !important}")
    html.append(".compare-bar{position:sticky;top:0;background:#fff;border-bottom:1px solid #ddd;padding:8px 0;margin-bottom:10px}")
    html.append(".compare-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:8px}")
    html.append(".compare-item{border:1px solid #ddd;border-radius:6px;padding:8px}")
    html.append(".controls{display:flex;gap:8px;align-items:center}")
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")
    html.append(f"<h1>按簇展示与对比</h1><p>共 {total} 个程序，{len(clusters)} 个簇。</p>")
    html.append("<div class=\"compare-bar\">")
    html.append("<div class=\"controls\">")
    html.append("<span>选择程序进行对比（最多 3 个）：</span>")
    html.append("<button id=\"clearSelection\">清空选择</button>")
    html.append("</div>")
    html.append("<div id=\"compareGrid\" class=\"compare-grid\"></div>")
    html.append("</div>")
    html.append("<h2>所有簇</h2>")
    html.append("<div class=\"cluster-list\">")
    for cid in sorted(clusters.keys()):
        count = len(clusters[cid])
        html.append(f"<div class=\"cluster-card\" data-cid=\"{cid}\">簇 {cid}<span class=\"badge\">{count} 项</span></div>")
    html.append("</div>")
    # 容器：每个簇的程序内容（初始隐藏）
    for cid in sorted(clusters_full.keys()):
        html.append(f"<section class=\"cluster-section\" id=\"cluster-{cid}\" style=\"display:none\">")
        html.append(f"<h3>簇 {cid}</h3>")
        for item in clusters_full[cid]:
            pid = html_escape(str(item["id"]))
            path = html_escape(item.get("path", ""))
            code_html = html_escape(item.get("code", ""))
            # 每个程序带选择框以加入对比
            html.append("<div class=\"program\">")
            html.append(f"<label style=\"display:flex;align-items:center;gap:8px\"><input type=\"checkbox\" class=\"compare-toggle\" data-pid=\"{pid}\" data-path=\"{path}\" data-code=\"{code_html}\"> 加入对比</label>")
            html.append(f"<h4>程序 {pid}</h4>")
            html.append(f"<p style=\"color:#666\">路径: {path}</p>")
            html.append(f"<pre><code>{code_html}</code></pre>")
            html.append("</div>")
        html.append("</section>")

    # 内联数据脚本（如需）与交互脚本
    html.append("<script src=\"static/js/clusters_site.js\"></script>")
    html.append("</body>")
    html.append("</html>")
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))


def generate_cluster_page(output_dir: str, cid: int, members: List[int], index: List[Dict[str, Any]]):
    html = [
        "<!DOCTYPE html>",
        "<html lang=\"zh-CN\">",
        "<head>",
        "<meta charset=\"UTF-8\">",
        f"<title>簇 {cid} - 代码程序</title>",
        "<link rel=\"stylesheet\" href=\"static/css/main.css\">",
        "<style>body{padding:20px} .program{margin:16px 0;padding:12px;border:1px solid #ddd;border-radius:8px} pre{background:#f5f5f5;padding:10px;border-radius:6px;white-space:pre-wrap;word-break:break-word}</style>",
        "</head>",
        "<body>",
        f"<h1>簇 {cid}（{len(members)} 项）</h1>",
        "<p><a href=\"index.html\">返回簇索引</a></p>",
    ]

    for mid in members:
        item = index[mid]
        pid = item.get("id", mid)
        path = item.get("path", "")
        code = read_code(path)
        code_html = html_escape(code)
        html += [
            "<div class=\"program\">",
            f"<h2>程序 {pid}</h2>",
            f"<p style=\"color:#666\">路径: {html_escape(path)}</p>",
            f"<pre><code>{code_html}</code></pre>",
            "</div>",
        ]

    html += ["</body>", "</html>"]
    with open(os.path.join(output_dir, f"cluster_{cid}.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))


def main():
    parser = argparse.ArgumentParser(description="生成按簇展示的静态可视化页面（包含程序代码）")
    parser.add_argument("--analysis-dir", default="programs_analysis", help="分析输出目录，包含 clusters.json/index.json")
    parser.add_argument("--output-dir", default="programs_analysis/site", help="静态站点输出目录")
    args = parser.parse_args()

    analysis_dir = args.analysis_dir
    output_dir = args.output_dir

    clusters_path = os.path.join(analysis_dir, "clusters.json")
    index_path = os.path.join(analysis_dir, "index.json")
    if not os.path.exists(clusters_path) or not os.path.exists(index_path):
        raise FileNotFoundError(f"缺少分析文件：{clusters_path} 或 {index_path}")

    with open(clusters_path, "r", encoding="utf-8") as f:
        clusters_obj = json.load(f)
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    clusters: Dict[int, List[int]] = {int(k): v for k, v in clusters_obj.get("clusters", {}).items()}

    os.makedirs(output_dir, exist_ok=True)

    # 复制静态资源
    static_src = os.path.join(os.path.dirname(__file__), "static")
    static_dst = os.path.join(output_dir, "static")
    if os.path.exists(static_dst):
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)

    # 清理旧的簇页面，保留单页站点
    for name in os.listdir(output_dir):
        if name.startswith("cluster_") and name.endswith(".html"):
            try:
                os.remove(os.path.join(output_dir, name))
            except Exception:
                pass

    # 生成单页交互站点
    logging.info(f"生成单页交互可视化到 {output_dir}/index.html")
    generate_single_page(output_dir, clusters, index)

    # 写入简要索引 JSON
    site_index = {"clusters": clusters, "count": sum(len(v) for v in clusters.values())}
    with open(os.path.join(output_dir, "site_index.json"), "w", encoding="utf-8") as f:
        json.dump(site_index, f, ensure_ascii=False, indent=2)

    logging.info(f"完成。请在浏览器打开: {output_dir}/index.html （需通过HTTP服务访问）")


if __name__ == "__main__":
    main()