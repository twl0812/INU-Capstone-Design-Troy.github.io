from transformers import RobertaTokenizer, RobertaModel
import torch
import numpy as np
import faiss
import pickle
import os

# 1. CodeBERT 로딩
MODEL_NAME = "microsoft/codebert-base"
tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
model = RobertaModel.from_pretrained(MODEL_NAME)

# 2. 임베딩 추출 함수
def get_code_embedding(code: str) -> np.ndarray:
    inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    cls_embedding = outputs.last_hidden_state[:, 0, :]  # [CLS]
    return cls_embedding.squeeze().numpy()

# 3. FAISS 인덱스 초기화 (768차원, L2 거리 기준)
def index_init(index_name):
    index = faiss.IndexFlatL2(768)
    faiss.write_index(index, index_name +".faiss")

# 4. 기존 코드 저장 및 인덱싱
def add_to_index(code: str, index):
    vec = get_code_embedding(code).astype('float32')
    index.add(np.array([vec]))  # FAISS에 추가

# 5. 유사도 비교 함수
def is_similar(code: str, index, threshold=0.95) -> bool:
    vec = get_code_embedding(code).astype('float32').reshape(1, -1)
    if index.ntotal == 0:
        return False
    D, I = index.search(vec, k=1)  # 가장 가까운 코드와의 거리 검색
    similarity = 1 - D[0][0] / 2  # L2 거리 → cosine 유사도 근사
    return similarity > threshold

def check_similarity(index_name, code):

    # 새로운 log 파일이라면 index 파일 새로 생성
    if not os.path.exists(index_name+".faiss"):
        index_init(index_name)
        print("새로운 index 생성: ", index_name)

    # index load
    index = faiss.read_index(index_name+".faiss")
    print("인덱스 로드 완료: ", index_name)

    # 기존에 있는 코드끼리 유사도 판정
    if is_similar(code, index):
        return 1 # 유사한 코드가 있음음
    else:
        # 인덱스 추가
        add_to_index(code, index)

        if not os.path.exists(index_name+".pkl"):
            with open(index_name + ".pkl", "wb") as f:
                pickle.dump([], f)

        # code list 배열에 저장 (파일)
        with open(index_name + ".pkl", "r+b") as f:
            loaded_array = pickle.load(f)
            new_array = loaded_array.append(code)

            f.seek(0)  # 파일 포인터를 처음으로 이동
            pickle.dump(loaded_array, f)
            f.truncate()

        return 0 # 유사한 코드가 없음음
