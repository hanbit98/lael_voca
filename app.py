import streamlit as st
import pandas as pd
import random # 순서 섞기용

# ---------------------------------------------------------
# 1. 초기 설정 및 데이터 로드
# ---------------------------------------------------------
st.set_page_config(page_title="아빠표 단어 시험", page_icon="📝", layout="centered")

# --- UI 커스텀 CSS (폰트 크기 조절 및 넓은 괄호) ---
st.markdown("""
    <style>
    div[data-baseweb="input"] input {
        font-size: 28px !important;
        font-weight: bold !important;
        padding: 15px !important;
    }
    div[data-testid="stNotification"] div[data-testid="stMarkdownContainer"] p {
        font-size: 24px !important;
        font-weight: bold !important;
        line-height: 1.4 !important;
    }
    .exam-sentence {
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
        white-space: pre-wrap; /* 넓은 공백 유지 */
    }
    .english-def {
        font-size: 22px;
        font-weight: bold;
        color: #d9534f;
        margin-bottom: 10px;
        padding: 15px;
        background-color: #f9f2f4;
        border-radius: 10px;
    }
    .korean-translation {
        font-size: 18px;
        color: #0066cc;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


# 세션 상태 초기화
if 'quiz_state' not in st.session_state:
    st.session_state['quiz_state'] = 'SETUP' 
if 'current_index' not in st.session_state:
    st.session_state['current_index'] = 0
if 'score' not in st.session_state:
    st.session_state['score'] = 0
if 'wrong_answers' not in st.session_state:
    st.session_state['wrong_answers'] = []
if 'quiz_data' not in st.session_state:
    st.session_state['quiz_data'] = []
if 'last_feedback' not in st.session_state:
    st.session_state['last_feedback'] = None

# 데이터 로드
@st.cache_data
def load_data():
    try:
        # utf-8-sig로 읽어서 한글 깨짐 방지
        df = pd.read_csv('vocab.csv', encoding='utf-8-sig')
        
        # 첫 줄이 데이터로 들어갔을 경우를 대비한 처리
        if 'Day' not in df.columns:
            df = pd.read_csv('vocab.csv', header=None, names=['Day', '순서', '유형', '정답 단어', '예문', '한글 해석', '영영 뜻'], encoding='utf-8-sig')
        else:
            # 안전하게 컬럼명 고정
            df.columns = ['Day', '순서', '유형', '정답 단어', '예문', '한글 해석', '영영 뜻']
            
        # 빈칸(NaN)을 빈 문자열로 처리
        df = df.fillna('')
        
        # 정답 입력 시 띄어쓰기 오류 방지를 위해 공백 제거
        df['정답 단어'] = df['정답 단어'].astype(str).str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

df = load_data()

# ---------------------------------------------------------
# 2. 기능 함수
# ---------------------------------------------------------
def check_answer():
    current_idx = st.session_state['current_index']
    data = st.session_state['quiz_data']
    
    if current_idx >= len(data):
        return

    current_word = data[current_idx]
    user_input = st.session_state.user_input
    correct_answer = str(current_word['정답 단어'])

    # 정답 체크 (대소문자 무시, 양끝 공백 무시)
    if user_input.strip().lower() == correct_answer.strip().lower():
        st.session_state['score'] += 1
        st.session_state['last_feedback'] = (f"⭕ 정답! '{correct_answer}'", True)
    else:
        # 틀린 문제 기록 시 유형별로 텍스트 다르게 저장
        question_text = current_word.get('예문', '') if current_word.get('유형', '') == '예문빈칸' else current_word.get('영영 뜻', '')
        
        st.session_state['wrong_answers'].append({
            '정답 단어': correct_answer,
            '나의 답': user_input,
            '문제(예문/영영)': question_text,
            '한글 해석': current_word.get('한글 해석', '')
        })
        st.session_state['last_feedback'] = (f"❌ 땡! 정답은 '{correct_answer}' (입력: {user_input})", False)

    st.session_state['current_index'] += 1
    st.session_state.user_input = ""

# ---------------------------------------------------------
# 3. 화면 구성
# ---------------------------------------------------------
# 타이틀
st.markdown("<h2 style='font-size: 30px;'>❤️보석같은 라엘❤️ 단어시험 뽀개기😁</h2>", unsafe_allow_html=True)

# (A) 설정 화면
if st.session_state['quiz_state'] == 'SETUP':
    if not df.empty:
        st.info("엔터키를 치면 바로 채점하고 다음 문제로 넘어갑니다!")
        if 'Day' in df.columns:
            days = df['Day'].unique()
            selected_day = st.selectbox("Day 선택", days)
        else:
            st.error("CSV 파일 구조에 문제가 있습니다. 파일 형식을 확인해주세요.")
            st.stop()
        
        if st.button("시험 시작하기!"):
            day_data = df[df['Day'] == selected_day]
            # 전체 데이터 셔플
            st.session_state['quiz_data'] = day_data.sample(frac=1).reset_index(drop=True).to_dict('records')
            
            # 상태 초기화
            st.session_state['quiz_state'] = 'TESTING'
            st.session_state['current_index'] = 0
            st.session_state['score'] = 0
            st.session_state['wrong_answers'] = []
            st.session_state['last_feedback'] = None
            st.rerun()
    else:
        st.error("'vocab.csv' 파일을 넣어주세요. (컬럼: Day, 순서, 유형, 정답 단어, 예문, 한글 해석, 영영 뜻)")

# (B) 시험 화면
elif st.session_state['quiz_state'] == 'TESTING':
    total_q = len(st.session_state['quiz_data'])
    current_idx = st.session_state['current_index']

    if current_idx >= total_q:
        st.session_state['quiz_state'] = 'FINISHED'
        st.rerun()

    current_word = st.session_state['quiz_data'][current_idx]
    
    st.progress(current_idx / total_q)
    
    # 상단 피드백 영역
    if st.session_state['last_feedback']:
        msg, is_correct = st.session_state['last_feedback']
        if is_correct:
            st.success(msg)
        else:
            st.error(msg)
    else:
        st.write("시작해볼까요? 화이팅!")

    st.markdown("---")
    st.markdown(f"#### 문제 {current_idx + 1}/{total_q}")
    
    # 🌟 핵심: 유형에 따라 문제를 다르게 보여줌
    quiz_type = current_word.get('유형', '예문빈칸')
    
    if quiz_type == '영영사전':
        # 영영 풀이 모드
        st.markdown(f"<div class='english-def'>📖 English Definition:<br>{current_word.get('영영 뜻', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='korean-translation'>💡 뜻: {current_word.get('한글 해석', '')}</div>", unsafe_allow_html=True)
    else:
        # 예문 빈칸 모드 (짧은 괄호를 넓게 자동 치환)
        exam_text = str(current_word.get('예문', '')).replace('( )', '( &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; )').replace('()', '( &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; )')
        st.markdown(f"<div class='exam-sentence'>{exam_text}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='korean-translation'>💡 힌트: {current_word.get('한글 해석', '')}</div>", unsafe_allow_html=True)

    st.text_input(
        label="정답 영어 단어를 입력하고 Enter를 치세요",
        key="user_input",
        on_change=check_answer
    )

# (C) 결과 화면
elif st.session_state['quiz_state'] == 'FINISHED':
    score = st.session_state['score']
    total = len(st.session_state['quiz_data'])
    
    st.balloons()
    st.header(f"끝! 점수: {score} / {total}")

    # 마지막 문제 피드백
    if st.session_state['last_feedback']:
        msg, is_correct = st.session_state['last_feedback']
        if is_correct:
            st.success(f"마지막 문제: {msg}")
        else:
            st.error(f"마지막 문제: {msg}")

    # 틀린 문제가 있을 경우
    if st.session_state['wrong_answers']:
        st.markdown("### 🚨 틀린 단어 확인하기")
        
        # 틀린 문제 표 출력
        wrong_df = pd.DataFrame(st.session_state['wrong_answers'])
        wrong_df.index = wrong_df.index + 1 # 0,1,2...를 1,2,3...으로 변경
        st.table(wrong_df)
        
        st.warning("👇 틀린 문제만 모아서 다시 시험 볼 수 있어요!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔥 틀린 문제만 다시 풀기"):
                retry_data = st.session_state['wrong_answers'].copy()
                # 재시험용 데이터로 변환 (기존 포맷 복구)
                formatted_retry_data = []
                for item in retry_data:
                    # 문제 텍스트에 따라 유형 유추
                    is_english_def = "a " in str(item['문제(예문/영영)']) or "to " in str(item['문제(예문/영영)']) and " " not in str(item['정답 단어'])
                    
                    formatted_retry_data.append({
                        '정답 단어': item['정답 단어'],
                        '유형': '영영사전' if is_english_def else '예문빈칸',
                        '예문': item['문제(예문/영영)'] if not is_english_def else '',
                        '영영 뜻': item['문제(예문/영영)'] if is_english_def else '',
                        '한글 해석': item['한글 해석']
                    })
                
                random.shuffle(formatted_retry_data)
                st.session_state['quiz_data'] = formatted_retry_data
                
                st.session_state['quiz_state'] = 'TESTING'
                st.session_state['current_index'] = 0
                st.session_state['score'] = 0
                st.session_state['wrong_answers'] = [] 
                st.session_state['last_feedback'] = None
                st.rerun()
        
        with col2:
            if st.button("🏠 처음으로 돌아가기"):
                st.session_state['quiz_state'] = 'SETUP'
                st.session_state['last_feedback'] = None
                st.rerun()
                
    else:
        st.success("완벽합니다! 틀린 문제가 하나도 없네요! 🎉")
        if st.button("🏠 처음으로 돌아가기"):
            st.session_state['quiz_state'] = 'SETUP'
            st.session_state['last_feedback'] = None
            st.rerun()