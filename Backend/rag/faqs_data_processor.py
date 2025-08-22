from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings


# def parse_faq_file(file_path):
#     with open(file_path, "r", encoding="utf-8") as f:
#         text = f.read()

#     faqs = []
#     blocks = text.strip().split("Question ")
#     for block in blocks:
#         if not block.strip():
#             continue
#         # split into question and answer
#         parts = block.split("Answer:")
#         question = parts[0].strip()
#         if ":" in question:  # remove "1: " etc.
#             question = question.split(":", 1)[1].strip()
#         answer = parts[1].strip()
#         faqs.append({"question": question, "answer": answer})
#     return faqs


# faqs = parse_faq_file("FAQs.txt")

# faq_docs = [
#     Document(
#         page_content=f["question"],  # embed the question
#         metadata={"answer": f["answer"]}
#     )
#     for f in faqs
# ]

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# faq_index = FAISS.from_documents(faq_docs, embedding_model)
# faq_index.save_local("faiss_faq_index")


# Load later if needed
faq_index = FAISS.load_local("faiss_faq_index", embedding_model, allow_dangerous_deserialization=True)

def query_faq(user_query, top_k=1):
    results = faq_index.similarity_search(user_query, k=top_k)
    if results:
        return {"question": results[0].page_content, "answer": results[0].metadata["answer"]}
    return None

print(query_faq("Is it free to sign up?"))


