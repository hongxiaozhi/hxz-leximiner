const API_BASE = window.location.protocol === "file:"
  ? "http://127.0.0.1:5000"
  : window.location.origin;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function trimText(value, limit = 120) {
  const text = String(value ?? "").trim();
  if (!text) {
    return "";
  }
  return text.length > limit ? `${text.slice(0, limit)}...` : text;
}

function buildSentenceSnippet(sentence, needle, limit = 120) {
  const text = String(sentence ?? "").trim();
  if (!text) {
    return "暂无例句";
  }

  const normalizedSentence = text.replace(/\s+/g, " ");
  const normalizedNeedle = String(needle ?? "").trim();
  if (!normalizedNeedle) {
    return trimText(normalizedSentence, limit);
  }

  const lowerSentence = normalizedSentence.toLowerCase();
  const lowerNeedle = normalizedNeedle.toLowerCase();
  const index = lowerSentence.indexOf(lowerNeedle);
  if (index < 0) {
    return trimText(normalizedSentence, limit);
  }

  const half = Math.max(20, Math.floor(limit / 2));
  const start = Math.max(0, index - half);
  const end = Math.min(normalizedSentence.length, index + normalizedNeedle.length + half);
  const prefix = start > 0 ? "..." : "";
  const suffix = end < normalizedSentence.length ? "..." : "";
  return `${prefix}${normalizedSentence.slice(start, end).trim()}${suffix}`;
}

function renderSummary(summary) {
  const totalWords = Number(summary?.total_words || 0);
  const uniqueWords = Number(summary?.unique_words || 0);
  const totalPhrases = Number(summary?.total_phrases || 0);
  const totalSentences = Number(summary?.total_sentences || 0);
  return `
    <div class="summary-grid">
      <article><span>总词数</span><strong>${totalWords}</strong></article>
      <article><span>不同词数</span><strong>${uniqueWords}</strong></article>
      <article><span>短语数</span><strong>${totalPhrases}</strong></article>
      <article><span>句子数</span><strong>${totalSentences}</strong></article>
    </div>
  `;
}

function renderCards(container, rows, type) {
  if (!rows.length) {
    container.innerHTML = '<p class="empty">暂无结果</p>';
    return;
  }

  if (type === "word") {
    container.innerHTML = rows.map((row) => `
      <article class="result-card word-card">
        <header class="result-card__header result-card__header--stack">
          <div class="title-block">
            <p class="result-meta">${escapeHtml(row.category || "unknown")} · ${escapeHtml(row.frequency_band || "unknown")}</p>
            <h3>${escapeHtml(row.lemma || row.word || "")}</h3>
            <p class="meaning-inline">${escapeHtml(row.chinese_meaning || "暂无释义")}</p>
          </div>
          <div class="badge-stack">
            <span class="badge">${escapeHtml(row.frequency ?? "")}</span>
            <span class="hint-badge ${row.remark === "simple_word" ? "hint-badge--active" : ""}">${row.remark === "simple_word" ? "简单词" : "常规"}</span>
          </div>
        </header>
        <div class="result-grid word-grid">
          <div><span class="label">原形</span><strong>${escapeHtml(row.word || "")}</strong></div>
          <div><span class="label">音标</span><strong>${escapeHtml(row.phonetic || "-")}</strong></div>
          <div><span class="label">助记</span><strong>${escapeHtml(row.mnemonic || "-")}</strong></div>
          <div><span class="label">状态</span><strong>${escapeHtml(row.remark === "simple_word" ? "基础词，已跳过联网补充" : "已完成分析")}</strong></div>
        </div>
        <p class="sentence">${escapeHtml(buildSentenceSnippet(row.source_sentence || "暂无例句", row.word || row.lemma || "", 120))}</p>
      </article>
    `).join("");
    return;
  }

  container.innerHTML = rows.map((row) => `
    <article class="result-card phrase-card">
      <header class="result-card__header result-card__header--stack">
        <div class="title-block">
          <p class="result-meta">${escapeHtml(row.category || "ngram")}</p>
          <h3>${escapeHtml(row.phrase || "")}</h3>
          <p class="meaning-inline">${escapeHtml(row.chinese_meaning || "暂无释义")}</p>
        </div>
        <div class="badge-stack">
          <span class="badge">${escapeHtml(row.frequency ?? "")}</span>
        </div>
      </header>
      <p class="sentence">${escapeHtml(buildSentenceSnippet(row.source_sentence || "暂无例句", row.phrase || "", 120))}</p>
    </article>
  `).join("");
}

async function analyze() {
  const text = document.getElementById("text-input").value.trim();
  const fileInput = document.getElementById("file-input");
  const uploadedFile = fileInput.files[0];
  const useOnlineTranslation = document.getElementById("online-translation").checked;
  const summaryBox = document.getElementById("summary-box");
  const wordsBox = document.getElementById("words-box");
  const phrasesBox = document.getElementById("phrases-box");

  if (!text && !uploadedFile) {
    summaryBox.innerHTML = '<p class="empty">请输入英文文本或上传文件</p>';
    return;
  }

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

    summaryBox.innerHTML = renderSummary(data.summary);
    renderCards(wordsBox, data.words || [], "word");
    renderCards(phrasesBox, data.phrases || [], "phrase");
  } catch (error) {
    summaryBox.innerHTML = `<p class="empty">分析失败：${escapeHtml(error.message)}</p>`;
  }
}

document.getElementById("analyze-btn").addEventListener("click", analyze);
