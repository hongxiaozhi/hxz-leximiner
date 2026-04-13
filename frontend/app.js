const API_BASE = window.location.protocol === "file:"
  ? "http://127.0.0.1:5000"
  : window.location.origin;

async function loadVocabPreview() {
  const grid = document.getElementById("vocab-stats-grid");
  const note = document.getElementById("vocab-stats-note");
  if (!grid || !note) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/leximiner/vocab-preview`);
    const data = await response.json();
    const stats = data.stats || {};
    const cards = [
      ["高频/基础", stats.high_school || 0],
      ["四级", stats.cet4 || 0],
      ["六级", stats.cet6 || 0],
      ["雅思", stats.ielts || 0],
      ["托福", stats.toefl || 0],
      ["学术词表", stats.academic || 0],
    ];
    grid.innerHTML = cards.map(([label, value]) => `
      <article class="stat-card">
        <span>${label}</span>
        <strong>${value}</strong>
      </article>
    `).join("");
    note.textContent = `短语词表 ${data.phrase_count || 0} 条，短语释义 ${data.phrase_meaning_count || 0} 条。`;
  } catch (error) {
    grid.innerHTML = "";
    note.textContent = `词库概览加载失败：${error.message}`;
  }
}

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
  const fileInput = document.getElementById("file-input");
  const uploadedFile = fileInput.files[0];
  const useOnlineTranslation = document.getElementById("online-translation").checked;
  const statusBox = document.getElementById("status-box");
  const summaryBox = document.getElementById("summary-box");
  const wordsBox = document.getElementById("words-box");
  const phrasesBox = document.getElementById("phrases-box");

  if (!text && !uploadedFile) {
    statusBox.textContent = "请输入英文文本或上传文件";
    return;
  }

  statusBox.textContent = "分析中...";

  try {
    const isFileUpload = Boolean(uploadedFile);
    const response = await fetch(`${API_BASE}/api/leximiner/analyze`, {
      method: "POST",
      headers: isFileUpload ? {} : { "Content-Type": "application/json" },
      body: isFileUpload
        ? (() => {
            const formData = new FormData();
            formData.append("file", uploadedFile);
            formData.append("text", text);
            formData.append("use_online_translation", String(useOnlineTranslation));
            return formData;
          })()
        : JSON.stringify({ text, use_online_translation: useOnlineTranslation }),
    });

    const contentType = response.headers.get("content-type") || "";
    const responseText = await response.text();
    let data;
    if (contentType.includes("application/json")) {
      data = JSON.parse(responseText);
    } else {
      data = {
        status: "error",
        message: responseText.slice(0, 200) || `请求失败：HTTP ${response.status}`,
      };
    }

    if (!response.ok) {
      throw new Error(data.message || "请求失败");
    }

    statusBox.textContent = data.message;
    summaryBox.textContent = JSON.stringify(data.summary, null, 2);
    renderTable(wordsBox, data.words || [], [
      { key: "word", label: "原形" },
      { key: "lemma", label: "Lemma" },
      { key: "frequency", label: "频次" },
      { key: "category", label: "分类" },
      { key: "frequency_band", label: "高低频" },
      { key: "chinese_meaning", label: "中文释义" },
      { key: "phonetic", label: "音标" },
      { key: "mnemonic", label: "助记" },
      { key: "source_sentence", label: "例句" },
    ]);
    renderTable(phrasesBox, data.phrases || [], [
      { key: "phrase", label: "短语" },
      { key: "frequency", label: "频次" },
      { key: "category", label: "分类" },
      { key: "chinese_meaning", label: "短语释义" },
      { key: "source_sentence", label: "例句" },
    ]);
  } catch (error) {
    statusBox.textContent = `分析失败：${error.message}`;
  }
}

document.getElementById("analyze-btn").addEventListener("click", analyze);
document.getElementById("refresh-vocab-btn").addEventListener("click", loadVocabPreview);

loadVocabPreview();