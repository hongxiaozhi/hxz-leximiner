const API_BASE = "";

function renderTable(container, rows, columns) {
  if (!rows.length) {
    container.innerHTML = '<p class="empty">暂无结果</p>';
    return;
  }

  const header = `<tr>${columns.map((column) => `<th>${column.label}</th>`).join("")}</tr>`;
  const body = rows
    .map((row) => `<tr>${columns.map((column) => `<td>${row[column.key] ?? ""}</td>`).join("")}</tr>`)
    .join("");

  container.innerHTML = `<table><thead>${header}</thead><tbody>${body}</tbody></table>`;
}

async function analyze() {
  const text = document.getElementById("text-input").value.trim();
  const useOnlineTranslation = document.getElementById("online-translation").checked;
  const statusBox = document.getElementById("status-box");
  const summaryBox = document.getElementById("summary-box");
  const wordsBox = document.getElementById("words-box");
  const phrasesBox = document.getElementById("phrases-box");

  if (!text) {
    statusBox.textContent = "请输入英文文本";
    return;
  }

  statusBox.textContent = "分析中...";

  try {
    const response = await fetch(`${API_BASE}/api/leximiner/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, use_online_translation: useOnlineTranslation }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || "请求失败");
    }

    statusBox.textContent = data.message;
    summaryBox.textContent = JSON.stringify(data.summary, null, 2);
    renderTable(wordsBox, data.words || [], [
      { key: "lemma", label: "Lemma" },
      { key: "frequency", label: "频次" },
      { key: "category", label: "分类" },
      { key: "chinese_meaning", label: "中文释义" },
    ]);
    renderTable(phrasesBox, data.phrases || [], [
      { key: "phrase", label: "短语" },
      { key: "frequency", label: "频次" },
      { key: "category", label: "分类" },
    ]);
  } catch (error) {
    statusBox.textContent = `分析失败：${error.message}`;
  }
}

document.getElementById("analyze-btn").addEventListener("click", analyze);