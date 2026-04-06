# LexiMiner

LexiMiner 是一个面向英语词汇与短语分析的 Python MVP 项目。它可以对英文文本进行清洗、分词、词形还原、词频统计、短语提取，并基于本地词表完成词汇分类，最后在 Streamlit 页面中展示结果，并支持导出 CSV 与 Excel。

## 1. 项目整体设计说明

项目按“界面层 -> 服务层 -> 核心算法层 -> 数据模型层 -> 工具层”组织：

- `streamlit_app.py`：Streamlit 应用入口，负责接收文本/文件输入、触发分析、展示结果、导出文件。
- `services/analysis_service.py`：业务编排层，负责把预处理、单词提取、分类、短语提取串联起来。
- `core/`：核心 NLP 逻辑，包括文本清洗、词形还原、单词提取、短语提取、词汇分类。
- `models/`：结构化数据模型，统一词汇结果、短语结果和分析摘要的数据格式。
- `utils/export_utils.py`：导出 CSV/Excel 的辅助函数。
- `utils/file_utils.py`：上传文件读取工具，负责 `.txt` 与 `.pdf` 文本抽取。
- `data/vocab/`：本地词表目录，包含分类词表和本地词典数据。
- `tests/`：基础测试，验证主分析流程可运行。

当前实现遵循 MVP 思路：

- 支持输入英文文本
- 支持上传 `.txt` 与 `.pdf` 文件
- 提取单词并词形还原
- 统计词频
- 按本地词表分类：`academic > cet6 > cet4 > unknown`
- 提取基础 bigram / trigram 短语
- 展示表格结果
- 导出 CSV 与 Excel

## 2. 项目目录结构

```text
hxz-leximiner/
├─ core/
│  ├─ __init__.py
│  ├─ classifier.py
│  ├─ lemmatizer.py
│  ├─ nltk_resources.py
│  ├─ phrase_extractor.py
│  ├─ preprocess.py
│  └─ word_extractor.py
├─ data/
│  └─ vocab/
│     ├─ academic.txt
│     ├─ cet4.txt
│     ├─ cet6.txt
│     └─ phrase_dict.txt
├─ models/
│  ├─ __init__.py
│  └─ schemas.py
├─ output/
│  └─ .gitkeep
├─ services/
│  ├─ __init__.py
│  └─ analysis_service.py
├─ tests/
│  └─ test_analysis_service.py
├─ utils/
│  ├─ __init__.py
│  └─ export_utils.py
├─ README.md
├─ requirements.txt
└─ streamlit_app.py
```

## 3. 核心功能说明

### 文本处理

- `core/preprocess.py` 负责清理空白字符、清除非 ASCII 噪声、切分句子。

### 单词提取

- `core/word_extractor.py` 使用正则提取英文词。
- 通过 `nltk` 的 `WordNetLemmatizer` 对单词做词形还原。
- 保留每个 lemma 的首个来源句子，便于结果展示。

### 短语提取

- `core/phrase_extractor.py` 基于过滤后的 token 生成 bigram 与 trigram。
- 去掉全停用词组合和明显无效组合。

### 分类逻辑

- `core/classifier.py` 从 `data/vocab/` 加载本地词表。
- 词汇分类优先级：`academic > cet6 > cet4 > unknown`。
- 短语若命中 `phrase_dict.txt`，标记为 `phrase_dict`，否则为 `ngram`。

### 本地词典

- `data/vocab/local_dictionary.json`：项目内置本地词典，优先提供中文意思、音标、助记词。
- `data/vocab/word_metadata.json`：你可以继续手动补充或覆盖默认词典内容。
- 查询优先级：`local_dictionary.json` -> `word_metadata.json` -> 缓存 -> 离线回退。

### 结果导出

- `utils/export_utils.py` 支持：
  - 导出 ZIP 压缩包，包含 `words.csv` 与 `phrases.csv`
  - 导出 Excel，多工作表分别保存词汇和短语结果

## 4. 安装方式

建议使用 Python 3.11 或更高版本。

### 4.1 创建虚拟环境

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 4.2 安装依赖

```bash
pip install -r requirements.txt
```

如果本地已安装 NLTK 语料，程序会优先使用更完整的词形还原与停用词能力。

如果这些语料暂时没有安装，项目也可以离线运行，此时会自动切换到内置停用词表和轻量词形还原回退逻辑。

如需更完整的 NLTK 处理能力，可以手动下载：

- `stopwords`
- `wordnet`
- `omw-1.4`
- `averaged_perceptron_tagger_eng`

## 5. 运行方式

### 启动 Streamlit

```bash
streamlit run streamlit_app.py
```

启动后在浏览器打开本地地址即可使用。

### 运行测试

```bash
pytest
```

## 6. 输入与输出说明

### 输入

- 直接粘贴英文文本
- 上传 `.txt` 文本文件
- 上传可提取文本的 `.pdf` 文件

### 单词结果字段

- `word`：原始词形（该 lemma 首次出现时的词形）
- `lemma`：词形还原结果
- `frequency`：词频
- `category`：分类结果
- `chinese_meaning`：中文意思，优先来自本地词典，缺失时自动回退补充
- `phonetic`：音标，优先使用本地元数据和自动音标转换
- `mnemonic`：助记词或词形记忆提示
- `source_sentence`：来源句子
- `remark`：预留字段

### 短语结果字段

- `phrase`：短语内容
- `frequency`：出现频次
- `category`：`phrase_dict` 或 `ngram`

## 7. 后续扩展建议

第二版可以继续扩展：

- DOCX 解析
- SQLite 历史记录
- 用户自定义词表
- 更复杂的短语规则提取
- 背诵清单生成

## 8. 适合初学者理解的说明

这个项目刻意保持了模块化和轻量实现：

- 核心逻辑集中在 `core/`
- 页面逻辑集中在 `streamlit_app.py`
- 数据结构集中在 `models/`
- 业务流程集中在 `services/`

如果你后续要增强功能，建议优先从 `services/analysis_service.py` 和 `core/classifier.py` 入手。