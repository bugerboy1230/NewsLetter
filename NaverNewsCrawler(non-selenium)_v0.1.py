import requests
import time
import random
import urllib.parse
import datetime
import pandas as pd
from bs4 import BeautifulSoup


def get_naver_news_api(keyword):
    """
    네이버 뉴스 검색 결과를 API 요청 방식으로 크롤링하는 함수

    Parameters:
    - keyword: 검색 키워드

    기본 설정:
    - max_articles: 100개 (최대 크롤링할 기사 수)
    - days: 1일 (몇 일 전 기사까지 검색할지)
    - sort: 0 (관련도순)
    - photo: 3 (포토)
    - field: 0 (분야: 전체)
    - office_type: 0 (언론사 분류: PC메인언론사)

    Returns:
    - news_list: 뉴스 기사 정보가 담긴 리스트
    """
    # 기본 설정값
    max_articles = 100  # 최대 기사 수
    days = 1  # 검색 기간 (일)
    sort = 0  # 정렬 방식 (0: 관련도순)
    photo = 3  # 이미지 옵션 (3: 포토)
    field = 0  # 분야 (0: 전체)
    office_type = 0  # 언론사 분류 (0: PC메인언론사)

    news_list = []

    # 현재 날짜 및 시간
    now = datetime.datetime.now()

    # 시작일, 종료일 설정
    end_date = now.strftime("%Y.%m.%d.%H.%M")
    start_date = (now - datetime.timedelta(days=days)).strftime("%Y.%m.%d.%H.%M")

    # URL 인코딩된 키워드
    encoded_keyword = urllib.parse.quote(keyword)

    # 네이버 뉴스 검색 기본 URL
    base_url = "https://search.naver.com/search.naver"

    # 검색 파라미터
    params = {
        "where": "news",
        "query": keyword,
        "sm": "tab_opt",
        "sort": sort,  # 0: 관련도순
        "photo": photo,  # 3: 포토
        "field": field,  # 0: 전체
        "pd": 4,  # 기간 직접 설정
        "ds": start_date.replace('.', '-')[:10],  # YYYY-MM-DD 형식
        "de": end_date.replace('.', '-')[:10],  # YYYY-MM-DD 형식
        "docid": "",
        "related": 0,
        "mynews": 0,
        "office_type": office_type,  # 0: PC메인언론사
        "office_section_code": 0,
        "news_office_checked": "",
        "nso": f"so:r,p:{days}d",
        "is_sug_officeid": 0,
        "office_category": 0,
        "service_area": 2,
    }

    # User-Agent 설정 (차단 방지)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://search.naver.com/search.naver",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
    }

    # 이미 처리한 기사의 URL을 저장하는 집합
    processed_urls = set()

    # 시작 인덱스
    start = 1

    print(f"네이버 뉴스 검색 시작: 키워드 '{keyword}'")
    print(f"기본 설정: 1일 이내, 관련도순, PC메인언론사, 최대 100개 기사")

    while len(news_list) < max_articles:
        # 페이지 파라미터 업데이트
        params["start"] = start

        try:
            # 요청 보내기
            response = requests.get(base_url, params=params, headers=headers)

            # 응답이 성공적이면 파싱 시작
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # 뉴스 아이템 찾기
                news_items = soup.select("div.news_area")

                # 뉴스 아이템이 없으면 종료
                if not news_items:
                    print("더 이상 뉴스 항목이 없습니다.")
                    break

                # 각 뉴스 아이템에서 정보 추출
                for item in news_items:
                    if len(news_list) >= max_articles:
                        break

                    try:
                        # 제목과 링크
                        title_tag = item.select_one("a.news_tit")
                        if not title_tag:
                            continue

                        title = title_tag.get_text(strip=True)
                        link = title_tag.get("href")

                        # 이미 처리한 URL이면 건너뛰기
                        if link in processed_urls:
                            continue

                        processed_urls.add(link)

                        # 언론사
                        press_tag = item.select_one("a.press")
                        press = press_tag.get_text(strip=True) if press_tag else "언론사 정보 없음"

                        # 요약 내용
                        summary_tag = item.select_one("div.news_dsc")
                        summary = summary_tag.get_text(strip=True) if summary_tag else "요약 내용 없음"

                        # 날짜
                        date_tag = item.select_one("span.info")
                        date = date_tag.get_text(strip=True) if date_tag else "날짜 정보 없음"

                        # 뉴스 정보 저장
                        news_info = {
                            "제목": title,
                            "언론사": press,
                            "날짜": date,
                            "요약": summary,
                            "링크": link
                        }

                        news_list.append(news_info)

                        # 진행 상황 출력 (10개 단위)
                        if len(news_list) % 10 == 0:
                            print(f"현재 {len(news_list)}개 기사 수집 완료...")

                    except Exception as e:
                        print(f"기사 정보 추출 중 오류 발생: {e}")

                # 다음 페이지로 이동
                start += len(news_items)

                # 서버 부하 방지를 위한 대기
                time.sleep(random.uniform(0.5, 1.5))

            else:
                print(f"페이지 요청 실패: {response.status_code}")
                break

        except Exception as e:
            print(f"크롤링 중 오류 발생: {e}")
            break

    # 정확히 max_articles개만 반환 (초과한 경우 자르기)
    return news_list[:max_articles]


def save_to_excel(news_list, keyword):
    """
    뉴스 정보를 엑셀 파일로 저장하는 함수

    Parameters:
    - news_list: 뉴스 기사 정보가 담긴 리스트
    - keyword: 검색 키워드 (파일명에 사용)
    """
    if not news_list:
        print("저장할 뉴스 정보가 없습니다.")
        return

    # 데이터프레임 생성
    df = pd.DataFrame(news_list)

    # 현재 날짜 및 시간
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 파일명 설정
    filename = f"네이버뉴스_{keyword}_{now}.xlsx"

    # 엑셀 파일로 저장
    df.to_excel(filename, index=False, engine="openpyxl")

    print(f"총 {len(news_list)}개의 뉴스 기사가 '{filename}' 파일로 저장되었습니다.")


def main():
    """
    메인 함수
    """
    print("=" * 50)
    print("네이버 뉴스 크롤링 프로그램")
    print("=" * 50)
    print("기본 설정:")
    print("- 검색 기간: 1일")
    print("- 정렬 방식: 관련도순")
    print("- 언론사 분류: PC메인언론사")
    print("- 최대 기사 수: 100개")
    print("=" * 50)

    # 사용자 입력 받기
    keyword = input("검색할 키워드를 입력하세요: ")

    print("\n크롤링을 시작합니다. 잠시만 기다려주세요...")

    # 뉴스 크롤링
    news_list = get_naver_news_api(keyword)

    # 엑셀로 저장
    save_to_excel(news_list, keyword)


if __name__ == "__main__":
    main()
