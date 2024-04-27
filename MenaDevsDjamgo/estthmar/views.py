from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser

from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate

from estthmar.utlls import parse_questions


folder_path = "chroma_db"

cached_llm = Ollama(model="llama3")

embedding = FastEmbedEmbeddings()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=80, length_function=len, is_separator_regex=False
)


questions_prompt = PromptTemplate.from_template(
""" 
### Request a feasibility study for the financial assistant
**[introduction]**
You are considered an expert financial assistant with specialized skills in conducting feasibility studies for various projects. I am currently exploring a new venture initiative and need your expertise to evaluate its potential for success.

### Example of the initial questions required
Below is an outline of the type of questions that would guide our feasibility study. These questions are designed to delve into various important aspects of the project:
- **Q1:** Who are the target customer segments?
- **Q2:** What is the target market?
- **Q3:** What is the specific problem that the project aims to solve?
- **Q4:** What is the proposed solution to this problem?
- **Q5:** What is the evidence that supports the compatibility of the problem with the solution?

**[Ask initial questions]**
Based on these questions and to ensure a comprehensive and accurate feasibility study is conducted, please provide a list of preliminary questions based on the project details that I will provide. These questions should serve as a guide to our discussions and help gather all the necessary information needed to conduct a comprehensive assessment.

**[Input instructions]**
- **[INST] Query project: {context}**
- **Answer:**
1. Based on the submitted project,
2. We state in bullet points the main questions that must be addressed to develop the feasibility study.
3. No side conversations or assertions, just give me questions in the format mentioned.
**[End of instructions]**"""
)

raw_prompt = PromptTemplate.from_template(

"""
### Financial Assistant Feasibility Study Prompt
**[Introduction]**
You are regarded as an expert financial assistant with specialized skills in conducting feasibility studies for various projects. I am currently exploring a new project initiative and need your expertise to assess its potential for success. Please carry out a detailed feasibility study to evaluate the viability of this proposed project. Your analysis should provide in-depth suggestions and consultations aimed at optimizing the project’s success.

**[objective]**
Conduct a comprehensive feasibility study that explores all relevant aspects of the proposed project. Your findings should help us make informed decisions regarding the project's potential and strategies moving forward.
"""
)


# Create your views here.
def home(request):
    return render(request,'home.html',{})

def pdf_upload(request):
    return render(request, 'pdf_upload.html')

class AIView(APIView):
    def post(self, request):
        print("query")
        data = request.data
        query = data.get("query")
        
        chain = questions_prompt | cached_llm
        print("LOGGING...\nReady to Go.")
        result = chain.invoke({"context": query})
        print("LOGGING...\end Go.")

        questions_dictionary = parse_questions(result)
        print("LOGGING...\end Go.")
        print(questions_dictionary)
        return Response(questions_dictionary)

class AskPDFView(APIView):
    def post(self, request):
        data = request.data
        query = data.get("query")
        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
        retriever = vector_store.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": 20, "score_threshold": 0.1})
        document_chain = create_stuff_documents_chain(cached_llm, questions_prompt)
        chain = create_retrieval_chain(retriever, document_chain)
        result = chain.invoke({"input": query})
        sources = [{"source": doc.metadata["source"], "page_content": doc.page_content} for doc in result["context"]]
        return Response({"answer": result["answer"], "sources": sources})


from django.core.files.storage import default_storage
import os

class PDFUploadAPI(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file = request.FILES['file']
        file_name = file.name
        save_path = "Documents/" + file_name

        # Ensure the directory exists
        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))

        # Save file to disk
        with default_storage.open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        print("LOGGING...\n\tSTARTING")
        loader = PDFPlumberLoader(save_path)
        docs = loader.load_and_split()
        chunks = text_splitter.split_documents(docs)
        print("LOGGING...\n\tREADY TO SAVE IN CHROMA")

        vector_store = Chroma.from_documents(documents=chunks, embedding=embedding, persist_directory=folder_path)
        vector_store.persist()
        return Response({
            "status": "Successfully Uploaded",
            "filename": file_name,
            "doc_len": len(docs),
            "chunks": len(chunks),
        })
