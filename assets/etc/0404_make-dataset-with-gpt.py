# -*- coding: utf-8 -*-

from openai import OpenAI
import code_similarity_check as csc
import json
import os
import re
from tqdm import tqdm

client = OpenAI(api_key="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")

prompt = """
C 언어 코드를 분석하여 한 줄씩 설명하고, 특정 형식의 태그를 적용해줘.

설명 및 요구사항  
1. C 언어 코드를 제공하면, 코드의 흐름을 한 줄씩 분석하여 각 단계별 설명을 작성해줘.  
2. 코드 블록(함수, 조건문, 반복문 등)의 시작과 끝을 특정 태그로 감싸서 표현해줘.  
3. 태그 규칙:  
   - 함수: [func_def_start(중첩 레벨)] ~ [func_def_end(중첩 레벨)]  
   - 조건문: [cond_start(중첩 레벨)] ~ [cond_end(중첩 레벨)]  
   - 반복문: [rep_start(중첩 레벨)] ~ [rep_end(중첩 레벨)]  
   - 구조체: [struct_start(중첩 레벨)] ~ [struct_end(중첩 레벨)]  
4. 태그 안의 숫자(중첩 레벨)는 현재 중첩된 깊이를 의미함.  
   - 예를 들어, for문 안에 또 다른 for문이 있다면,  
     - 바깥 for문 → [rep_start(1)]  
     - 안쪽 for문 → [rep_start(2)]  
     - 안쪽 for문 종료 → [rep_end(2)]  
     - 바깥 for문 종료 → [rep_end(1)]  

예제 코드 & 원하는 출력 예시  

입력 코드:
c
#include <stdio.h>

int is_prime(int num) {
    if (num < 2) return 0;
    for (int j = 2; j < num; j++) {
        if (num % j == 0) {
            return 0;
        }
    }
    return 1;
}

int main(void) {
    int M, N;
    scanf("%d\n%d", &M, &N);

    int sum = 0, min = 0;
    for (int i = M; i <= N; i++) {
        if (is_prime(i)) {
            sum += i;
            if (min == 0) {
                min = i;
            }
        }
    }
    if (min != 0)
        printf("%d\n%d", sum, min);
    else
        printf("-1");

    return 0;
}
출력 예시:

1. [func_def_start(1)] int 반환형 함수 is_prime을 정의하세요. (매개변수: int num)
2. [cond_start(1)] num이 2보다 작은지 확인하는 조건문을 작성하세요.
3. num이 2보다 작다면 0을 반환하세요.
4. [cond_end(1)]
5. [rep_start(1)] j를 선언해 2부터 num-1까지 반복하는 for 루프를 작성하세요.
6. [cond_start(2)] num이 j로 나누어지는지 확인하는 조건문을 작성하세요.
7. num이 j로 나누어지면 0을 반환하세요.
8. [cond_end(2)]
9. [rep_end(1)]
10. 위의 과정을 통과한 num은 소수이므로 1을 반환하세요.
11. [func_def_end(1)]
12. [func_def_start(1)] int 반환형 main 함수를 정의하세요. (매개변수 없음)
13. 정수형 변수 M과 N을 선언하세요.
14. M과 N에 입력을 받으세요.
15. 소수의 합을 저장할 int형 변수 sum을 0으로 초기화하세요.
16. 첫 번째 소수를 저장할 int형 변수 min을 0으로 초기화하세요.
17. [rep_start(1)] i를 선언해 M부터 N까지 반복하는 for 루프를 작성하세요.
18. [cond_start(2)] is_prime 함수를 이용하여 i가 소수인지 판별하는 조건문을 작성하세요.
19. i가 소수라면 sum에 i를 더하세요.
20. [cond_start(3)] 이전에 소수가 나왔는지 확인하는 조건문을 작성하세요.
21. 이전에 소수가 나오지 않았다면 첫 번째 소수의 값을 i로 설정하세요.
22. [cond_end(3)]
23. [cond_end(2)]
24. [rep_end(1)]
25. [cond_start(1)] 소수가 존재하는지 확인하는 조건문을 작성하세요.
26. 소수가 존재하면 sum과 min을 출력하세요.
27. [cond_end(1)]
28. [cond_start(1)] 소수가 존재하지 않는 경우를 처리하는 조건문을 작성하세요.
29. 소수가 없으면 -1을 출력하세요.
30. [cond_end(1)]
31. return 0;으로 프로그램을 종료하세요.
32. [func_def_end(1)]
이제 제공하는 C 코드도 이 형식으로 변환해서 설명해줘.
"""

def remove_c_comments(code: str) -> str:
    # 여러 줄 주석 제거: /* ... */
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    # 한 줄 주석 제거: // ...
    code = re.sub(r'//.*', '', code)

    return code

def parse_log_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        log_text = file.read()

    # 로그를 줄 단위로 구분
    log_entries = log_text.strip().split("------------------------------------------------------")

    parsed_data = []
    
    for entry in log_entries:
        lines = entry.strip().split("\n")
        if lines and len(lines) > 1:
            # 헤더 파싱
            header = lines[0].strip()
            id_, problem, result = header.split(":", 2)
            problem_number_str = ''.join(filter(str.isdigit, problem))
            # 코드 부분 파싱
            code = "\n".join(lines[1:]).strip()
            code = remove_c_comments(code)
            # code_lines = code.splitlines()
            # filtered_lines = [line for line in code_lines if "#define _CRT_SECURE_NO_WARNINGS" not in line]
            # code = '\n'.join(filtered_lines)  
            # 파싱된 데이터를 리스트에 저장
            parsed_data.append({
                'id': id_,
                'problem': int(problem_number_str),
                'result': result,
                'code': code
            })
    
    return parsed_data

cnt = 0

for i in tqdm(range(1000, 1025)):

    log_filename =  "logs-" + str(i)

    # 로그 파일 파싱
    parsed_data_list = parse_log_file('./log/'+log_filename + '.txt')

    for i in tqdm(range(len(parsed_data_list))):
        parsed_data = parsed_data_list[i]

        cnt = cnt + 1
        if cnt > 100:
            break
        if parsed_data['result'] == 'ACCEPTED':
            # print(parsed_data['result'])
            # tap = input()  
            # print(parsed_data['code'])
            # print("------------------------------------------------------")
            code = parsed_data['code']

            if csc.check_similarity(log_filename, code):
                continue
            
            response = client.responses.create(
              model="gpt-4o-mini-2024-07-18",
              input = prompt + "\n"+ code 
            )

            print(response.output_text)

            # 새로 추가할 항목 정의
            new_entry = {
                "conversations": [
                    {"role": "user", "content": code},
                    {"role": "assistant", "content": response.output_text}
                ],
                "source": "custom-dataset",
                "score": 4.8
            }

            # 파일 경로
            file_path = "dataset.json"

            # 기존 데이터 불러오기
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []

            # 새 항목 추가
            data.append(new_entry)

            # JSON으로 저장 (줄바꿈은 \n으로 저장됨)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print("dataset.json에 저장되었습니다.")

