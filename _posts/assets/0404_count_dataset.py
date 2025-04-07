import json

# JSON 파일 열기
with open('dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 배열의 길이 출력 (최상위 배열의 개수)
print("배열의 개수:", len(data))
