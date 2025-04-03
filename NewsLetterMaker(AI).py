import pandas as pd
import datetime
import os
import openai
import time
import json
from dotenv import load_dotenv
import re

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 뉴스레터 설정
NEWSLETTER_NAME = "데일리 뉴스 브리핑"
COMPANY_NAME = "AI 뉴스 서비스"
LOGO_URL = "https://your-logo-url.com/logo.png"  # 로고 URL 설정
WEBSITE_URL = "https://your-website.com"
SUBSCRIPTION_URL = "https://your-website.com/subscribe"
SOCIAL_MEDIA = {
    "Twitter": "https://twitter.com/your-handle",
    "Facebook": "https://facebook.com/your-page",
    "LinkedIn": "https://linkedin.com/company/your-company"
}


def get_newsletter_header(topic, date):
    """
    뉴스레터 헤더를 생성하는 함수

    Parameters:
    - topic: 뉴스레터 주제
    - date: 날짜

    Returns:
    - header: 뉴스레터 헤더
    """
    header = f"""
# {NEWSLETTER_NAME}

![로고]({LOGO_URL})

**{date} | {topic} 특집호**

---

안녕하세요, {NEWSLETTER_NAME} 구독자 여러분!

오늘의 주요 이슈인 **{topic}**에 대한 핵심 뉴스와 분석을 정리했습니다.
가장 중요한 기사들을 AI가 선별하고 요약했으니, 바쁜 일상 속에서도 꼭 필요한 정보만 빠르게 확인하세요.

---

"""
    return header


def get_newsletter_footer():
    """
    뉴스레터 푸터를 생성하는 함수

    Returns:
    - footer: 뉴스레터 푸터
    """
    current_year = datetime.datetime.now().year

    footer = f"""
---

## 📱 소셜 미디어에서 만나요

"""

    for platform, url in SOCIAL_MEDIA.items():
        footer += f"- [{platform}]({url})\n"

    footer += f"""
## 📝 구독 관리

- [구독 설정 변경]({SUBSCRIPTION_URL})
- [지난 뉴스레터 보기]({WEBSITE_URL}/archives)
- [피드백 남기기]({WEBSITE_URL}/feedback)

이 뉴스레터는 네이버 뉴스 크롤링 데이터를 기반으로 AI의 도움을 받아 자동 생성되었습니다.
뉴스의 정확성과 다양한 관점을 제공하기 위해 노력하고 있으나, 모든 정보의 사실 여부는 원문을 통해 확인하시기 바랍니다.

© {current_year} {COMPANY_NAME}. All rights reserved.
"""
    return footer


def summarize_with_chatgpt(news_data, topic):
    """
    ChatGPT를 사용하여 뉴스 데이터를 요약하고 분석하는 함수

    Parameters:
    - news_data: 뉴스 데이터프레임
    - topic: 뉴스 주제

    Returns:
    - analysis: ChatGPT의 분석 결과
    """
    # 뉴스 데이터를 텍스트로 변환
    news_text = f"다음은 '{topic}' 관련 오늘의 주요 뉴스 목록입니다:\n\n"

    for i, (_, news) in enumerate(news_data.iterrows(), 1):
        news_text += f"{i}. 제목: {news['제목']}\n"
        news_text += f"   언론사: {news['언론사']}\n"
        news_text += f"   요약: {news['요약']}\n\n"

    # ChatGPT에게 요청할 프롬프트 작성
    prompt = f"""
    {news_text}

    위 뉴스 기사들을 분석하여 다음 작업을 수행해주세요:

    1. 주요 이슈 요약: 전체 뉴스의 핵심 주제와 중요 사항을 3-4문장으로 요약해주세요.
    2. 주요 키워드: 뉴스에서 자주 등장하는 중요 키워드 5-7개를 추출해주세요.
    3. 추천 기사: 가장 중요하다고 생각되는 상위 5개 기사를 선정하고, 각 기사별로 2-3문장으로 핵심 내용을 요약해주세요.
    4. 다양한 관점: 동일 이슈에 대한 다양한 시각이나 의견이 있다면 간략히 정리해주세요.
    5. 오늘의 한 줄 요약: 전체 이슈를 한 문장으로 요약해주세요.

    JSON 형식으로 응답해주세요:
    {{
        "main_summary": "전체 요약...",
        "one_line_summary": "한 줄 요약...",
        "keywords": ["키워드1", "키워드2", ...],
        "recommended_articles": [
            {{"index": 1, "title": "기사 제목", "summary": "기사 요약..."}},
            ...
        ],
        "perspectives": "다양한 관점 정리..."
    }}

    반드시 위 JSON 형식을 정확히 지켜주세요. 모든 필드를 반드시 포함해야 합니다.
    """

    try:
        # ChatGPT API 호출
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # 또는 사용 가능한 최신 모델
            messages=[
                {"role": "system",
                 "content": "당신은 뉴스 분석 전문가입니다. 뉴스 기사를 분석하여 핵심 내용을 요약하고 중요한 기사를 추천해주세요. 항상 지정된 JSON 형식으로 응답해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1500
        )

        # 응답에서 JSON 추출
        result = response.choices[0].message.content

        # JSON 부분만 추출
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                analysis = json.loads(json_str)
            except json.JSONDecodeError:
                print("JSON 파싱 오류, 텍스트 응답으로 처리합니다.")
                analysis = {
                    "main_summary": "API 응답을 파싱할 수 없습니다.",
                    "one_line_summary": f"{topic}에 관한 주요 뉴스입니다.",
                    "keywords": [topic, "뉴스", "이슈", "분석", "요약"],
                    "recommended_articles": [],
                    "perspectives": "다양한 관점이 존재합니다."
                }
        else:
            print("JSON 형식 응답을 찾을 수 없습니다.")
            analysis = {
                "main_summary": "API 응답에서 JSON을 찾을 수 없습니다.",
                "one_line_summary": f"{topic}에 관한 주요 뉴스입니다.",
                "keywords": [topic, "뉴스", "이슈", "분석", "요약"],
                "recommended_articles": [],
                "perspectives": "다양한 관점이 존재합니다."
            }

        return analysis

    except Exception as e:
        print(f"ChatGPT API 호출 중 오류 발생: {str(e)}")
        return {
            "main_summary": f"API 오류: {str(e)}",
            "one_line_summary": f"{topic}에 관한 주요 뉴스입니다.",
            "keywords": [topic, "뉴스", "이슈", "분석", "요약"],
            "recommended_articles": [],
            "perspectives": "다양한 관점이 존재합니다."
        }


def create_newsletter(excel_file):
    """
    엑셀 파일에서 뉴스 데이터를 읽어 뉴스레터를 생성하는 함수

    Parameters:
    - excel_file: 뉴스 데이터가 담긴 엑셀 파일 경로

    Returns:
    - newsletter_content: 생성된 뉴스레터 내용
    """
    # 현재 날짜 가져오기
    today = datetime.datetime.now().strftime("%Y년 %m월 %d일")

    # 엑셀 파일 읽기
    try:
        df = pd.read_excel(excel_file)
        print(f"엑셀 파일을 성공적으로 읽었습니다. 총 {len(df)}개의 뉴스 기사가 있습니다.")
    except Exception as e:
        return f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}"

    # 데이터 전처리
    df = df.fillna("정보 없음")  # 결측치 처리

    # 파일명에서 주제 추출 (예: 네이버뉴스_탄핵_20250403_222536.xlsx -> 탄핵)
    file_name = os.path.basename(excel_file)
    file_parts = file_name.split('_')
    topic = file_parts[1] if len(file_parts) > 1 else "이슈"

    # ChatGPT를 통한 뉴스 분석
    print(f"ChatGPT를 통해 '{topic}' 관련 뉴스를 분석 중입니다...")
    analysis = summarize_with_chatgpt(df, topic)

    # 헤더 추가
    newsletter_content = get_newsletter_header(topic, today)

    # 한 줄 요약 추가
    one_line_summary = analysis.get("one_line_summary", f"{topic}에 관한 주요 뉴스입니다.")
    newsletter_content += f"## ⚡ 오늘의 한 줄 요약\n\n**{one_line_summary}**\n\n"

    # 주요 이슈 요약 추가
    main_summary = analysis.get("main_summary", "요약 정보가 없습니다.")
    newsletter_content += f"## 📋 오늘의 핵심 요약\n\n{main_summary}\n\n"

    # 키워드 추가
    keywords = analysis.get("keywords", [topic, "뉴스", "이슈", "분석", "요약"])
    newsletter_content += "## 📊 주요 키워드\n\n"
    for keyword in keywords:
        newsletter_content += f"- **{keyword}**\n"

    # 추천 기사 추가
    newsletter_content += "\n## 🔥 주요 뉴스\n\n"

    recommended_articles = analysis.get("recommended_articles", [])

    # 추천 기사가 있는 경우
    if recommended_articles:
        for article in recommended_articles:
            idx = article.get("index", 0) - 1
            if 0 <= idx < len(df):
                news = df.iloc[idx]
                title = news['제목']
                press = news['언론사']
                link = news['링크']
                summary = article.get("summary", "요약 정보가 없습니다.")

                newsletter_content += f"### {title}\n\n"
                newsletter_content += f"**출처**: {press}\n\n"
                newsletter_content += f"{summary}\n\n"
                newsletter_content += f"[기사 원문 보기]({link})\n\n"
                newsletter_content += "---\n\n"
    # 추천 기사가 없는 경우 상위 5개 기사 표시
    else:
        for i in range(min(5, len(df))):
            news = df.iloc[i]
            title = news['제목']
            press = news['언론사']
            summary = news['요약']
            link = news['링크']

            # 요약이 너무 길면 자르기
            if len(summary) > 200:
                summary = summary[:197] + "..."

            newsletter_content += f"### {title}\n\n"
            newsletter_content += f"**출처**: {press}\n\n"
            newsletter_content += f"{summary}\n\n"
            newsletter_content += f"[기사 원문 보기]({link})\n\n"

            if i < min(4, len(df) - 1):  # 마지막 기사 후에는 구분선 없음
                newsletter_content += "---\n\n"

    # 다양한 관점 추가
    perspectives = analysis.get("perspectives", "다양한 관점 정보가 없습니다.")
    newsletter_content += "\n## 🔍 다양한 관점\n\n"
    newsletter_content += f"{perspectives}\n\n"

    # 추가 뉴스 목록 추가
    newsletter_content += "\n## 📰 추가 뉴스 목록\n\n"

    # 이미 추천된 기사를 제외한 나머지 기사 중에서 5개 선택
    recommended_indices = [article.get("index", 0) - 1 for article in recommended_articles]
    other_news_indices = [i for i in range(len(df)) if i not in recommended_indices][:5]

    for i, idx in enumerate(other_news_indices, 1):
        if idx < len(df):
            news = df.iloc[idx]
            title = news['제목']
            press = news['언론사']
            link = news['링크']

            newsletter_content += f"{i}. [{title}]({link}) - {press}\n\n"

    # 푸터 추가
    newsletter_content += get_newsletter_footer()

    return newsletter_content


def main():
    # 현재 디렉토리에서 엑셀 파일 찾기
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and '네이버뉴스' in f]

    if not excel_files:
        print("현재 디렉토리에 '네이버뉴스' 엑셀 파일이 없습니다.")
        return

    # 가장 최근 파일 선택 (파일명에 날짜가 포함되어 있다고 가정)
    latest_file = sorted(excel_files)[-1]
    print(f"처리할 파일: {latest_file}")

    # OpenAI API 키 확인
    if not openai.api_key:
        print("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정하세요.")
        return

    # 뉴스레터 생성
    newsletter = create_newsletter(latest_file)

    # 마크다운 파일로 저장
    file_name = os.path.basename(latest_file)
    topic = file_name.split('_')[1] if len(file_name.split('_')) > 1 else "이슈"
    output_file = f"뉴스레터_{topic}_{datetime.datetime.now().strftime('%Y%m%d')}.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(newsletter)

    print(f"\n뉴스레터가 '{output_file}' 파일로 저장되었습니다.")

    # 결과 미리보기 출력
    print("\n" + "=" * 50)
    print("뉴스레터 미리보기 (처음 500자):")
    print("=" * 50)
    print(newsletter[:500] + "...\n")


if __name__ == "__main__":
    main()
