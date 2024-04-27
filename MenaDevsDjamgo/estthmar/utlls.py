import re

def parse_questions(response_text):
    response_text = re.sub(r'\s+', ' ', response_text).replace('[', '(').replace(']', ')').replace('{', '(').replace('}', ')')

    questions_list = []

    pattern = r'(?i)\bQ(\d+)[.:!]\s*([^?!.]+[?!.])\s*(?:\(([^)]+)\)|- Example: ([^,]+),|Example: ([^,]+),)?'
    matches = re.findall(pattern, response_text)

    for match in matches:
        question_number, question, hint1, hint2, hint3 = match
        hints = [hint1, hint2, hint3]
        hint = next((h.strip() for h in hints if h), 'No hint provided')

        question_dict = {
            'id': int(question_number),
            'question': question.strip(),
            'hint': hint
        }

        questions_list.append(question_dict)

    return questions_list

if __name__ == "__main__":
    questions_list = parse_questions('response')
    print(questions_list)
