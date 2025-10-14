// Interactive single-page clusters viewer with side-by-side compare
document.addEventListener("DOMContentLoaded", () => {
  const clusterCards = document.querySelectorAll(".cluster-card");
  const compareGrid = document.getElementById("compareGrid");
  const clearBtn = document.getElementById("clearSelection");

  // Inject lightweight styles for diff highlighting
  const style = document.createElement("style");
  style.textContent = `.line-diff{background:#fff3cd}`;
  document.head.appendChild(style);

  // Maintain selected programs (limit 3)
  const selected = new Map(); // pid -> {title, path, code}

  function toggleCluster(cid) {
    // Hide others
    document.querySelectorAll(".cluster-section").forEach(sec => {
      if (sec.id !== `cluster-${cid}`) sec.style.display = "none";
    });
    // Toggle current
    const sec = document.getElementById(`cluster-${cid}`);
    if (!sec) return;
    const show = sec.style.display === "none" || sec.style.display === "";
    sec.style.display = show ? "block" : "none";
    if (show) sec.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Attach cluster card handlers
  clusterCards.forEach(card => {
    card.addEventListener("click", () => {
      const cid = card.getAttribute("data-cid");
      if (cid) toggleCluster(cid);
    });
  });

  function readProgramFromCheckbox(cb) {
    const programEl = cb.closest(".program");
    const titleEl = programEl.querySelector("h4");
    const pathEl = programEl.querySelector("p");
    const codeEl = programEl.querySelector("pre code");
    const pid = cb.getAttribute("data-pid") || (titleEl?.textContent || "").replace(/^程序\s+/, "");
    const path = cb.getAttribute("data-path") || (pathEl?.textContent || "").replace(/^路径:\s*/, "");
    const code = cb.getAttribute("data-code") || (codeEl?.innerText || "");
    return { pid, title: titleEl?.textContent || `程序 ${pid}`, path, code };
  }

  function renderCompare() {
    compareGrid.innerHTML = "";
    const items = Array.from(selected.values());
    items.forEach(item => {
      const div = document.createElement("div");
      div.className = "compare-item";
      div.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
          <div>
            <div style="font-weight:600;">${escapeHtml(item.title)}</div>
            <div style="color:#666;font-size:0.9em;">${escapeHtml(item.path)}</div>
          </div>
          <button data-remove="${escapeHtml(item.pid)}" title="移除">移除</button>
        </div>
        <pre><code>${escapeHtml(item.code)}</code></pre>
      `;
      compareGrid.appendChild(div);
    });
    attachRemoveHandlers();
    if (items.length === 2) highlightLineDiff(items[0].code, items[1].code);
    syncScrollInit();
  }

  function attachRemoveHandlers() {
    compareGrid.querySelectorAll("button[data-remove]").forEach(btn => {
      btn.addEventListener("click", () => {
        const pid = btn.getAttribute("data-remove");
        selected.delete(pid);
        // Uncheck original checkbox
        document.querySelectorAll(`.compare-toggle[data-pid='${cssEscape(pid)}']`).forEach(cb => cb.checked = false);
        renderCompare();
      });
    });
  }

  function highlightLineDiff(a, b) {
    const linesA = a.split(/\r?\n/);
    const linesB = b.split(/\r?\n/);
    const preBlocks = compareGrid.querySelectorAll("pre code");
    if (preBlocks.length < 2) return;
    const markDiff = (el, lines, other) => {
      const container = document.createElement("div");
      container.style.whiteSpace = "pre-wrap";
      container.style.wordBreak = "break-word";
      lines.forEach((ln, i) => {
        const span = document.createElement("span");
        span.textContent = ln + (i < lines.length - 1 ? "\n" : "");
        if (ln !== (other[i] ?? "")) span.className = "line-diff";
        container.appendChild(span);
      });
      el.parentElement.replaceChild(container, el);
    };
    markDiff(preBlocks[0], linesA, linesB);
    markDiff(preBlocks[1], linesB, linesA);
  }

  function syncScrollInit() {
    const scrollers = Array.from(compareGrid.querySelectorAll("pre, .compare-item div"));
    const pres = Array.from(compareGrid.querySelectorAll("pre"));
    pres.forEach(pre => {
      pre.addEventListener("scroll", () => {
        const ratio = pre.scrollTop / (pre.scrollHeight - pre.clientHeight || 1);
        pres.forEach(other => {
          if (other === pre) return;
          other.scrollTop = ratio * (other.scrollHeight - other.clientHeight);
        });
      }, { passive: true });
    });
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function cssEscape(s) {
    return String(s).replace(/'/g, "\\'");
  }

  // Handle compare toggles
  document.querySelectorAll(".compare-toggle").forEach(cb => {
    cb.addEventListener("change", () => {
      const { pid } = readProgramFromCheckbox(cb);
      if (cb.checked) {
        if (selected.size >= 3) {
          alert("最多选择 3 个程序进行对比");
          cb.checked = false;
          return;
        }
        selected.set(pid, readProgramFromCheckbox(cb));
      } else {
        selected.delete(pid);
      }
      renderCompare();
    });
  });

  clearBtn?.addEventListener("click", () => {
    selected.clear();
    document.querySelectorAll(".compare-toggle").forEach(cb => cb.checked = false);
    renderCompare();
  });
});