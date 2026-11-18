import glob
import os
import shutil
import sys

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import API_KEY, BASE_URL

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "kb")
STORE_DIR = os.path.join(BASE_DIR, "vector_store")

embeddings = OpenAIEmbeddings(
    model="text-embedding-v3",
    api_key=API_KEY,
    base_url=BASE_URL,
    check_embedding_ctx_length=False,
    chunk_size=10,
)

# 【原创】知识库构建逻辑：读取 kb 文档 -> 切片 -> 向量化入库
docs = []
for path in sorted(glob.glob(os.path.join(KB_DIR, "*.md"))):
    with open(path, encoding="utf-8") as f:
        docs.append(Document(page_content=f.read(), metadata={"source": path}))
if not docs:
    sys.exit(f"kb/ 目录里没有找到 .md 文件：{KB_DIR}")
print(f"加载知识文件：{len(docs)} 个")

splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
chunks = splitter.split_documents(docs)
print(f"切片后知识片段：{len(chunks)} 个")

if os.path.isdir(STORE_DIR):
    shutil.rmtree(STORE_DIR, ignore_errors=True)
    print("已清空旧的向量库，开始重建")
vector_store = Chroma.from_documents(chunks, embeddings, persist_directory=STORE_DIR)
print(f"向量库已保存到：{STORE_DIR}（共 {vector_store._collection.count()} 条）")

print("\n自检：检索「做一个小程序需要什么技术」")
for d in vector_store.similarity_search("做一个小程序需要什么技术", k=3):
    source = os.path.basename(d.metadata.get("source", ""))
    preview = d.page_content[:40].replace("\n", " ")
    print(f"  - [{source}] {preview}...")
