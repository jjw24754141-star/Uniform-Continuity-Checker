import streamlit as st
import numpy as np
import sympy
from sympy.parsing.sympy_parser import parse_expr
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import glob

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="평등연속성 판별 앱",
    page_icon="📈",
    layout="centered"
)

# --- 한글 폰트 설정 (이전과 동일) ---
@st.cache_data
def load_korean_font():
    font_dir = 'font'
    if not os.path.exists(font_dir): return
    font_files = glob.glob(os.path.join(font_dir, '*.[tT][tT][fF]')) + glob.glob(os.path.join(font_dir, '*.[oO][tT][fF]'))
    if not font_files: return
    font_path = font_files[0]
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False

load_korean_font()

# --- 수학적 판별 로직 (SymPy 객체를 직접 받도록 수정) ---
def check_uniform_continuity(func_str, interval_type, a_sym, b_sym):
    x = sympy.symbols('x')
    try:
        f = parse_expr(func_str, local_dict={'x': x}, transformations='all')
    except Exception as e:
        return "오류", f"함수식을 파싱할 수 없습니다: {e}", None

    try:
        discontinuities = sympy.singularities(f, x)
    except Exception:
        discontinuities = []

    if interval_type == '[a, b]':
        if a_sym.is_infinite or b_sym.is_infinite:
            reason = "닫힌구간 [a, b]는 유한해야 합니다. 무한대 구간은 닫힌구간으로 설정할 수 없습니다."
            return "판별 불가", reason, f
        
        interval_sympy = sympy.Interval(a_sym, b_sym)
        for p in discontinuities:
            if p in interval_sympy:
                reason = f"함수가 닫힌구간 $[{sympy.latex(a_sym)}, {sympy.latex(b_sym)}]$ 내의 점 $x = {sympy.latex(p)}$ 에서 불연속이므로 평등연속이 아닙니다."
                return "평등연속 아님", reason, f
        reason = f"함수가 닫힌구간 $[{sympy.latex(a_sym)}, {sympy.latex(b_sym)}]$ 에서 연속입니다. 따라서 **하이네-칸토어 정리**에 의해 이 구간에서 평등연속입니다."
        return "평등연속", reason, f
    else:
        # 구간의 열린 끝점에서 극한값 확인
        is_uc = True
        reason = ""
        
        # 왼쪽 끝점
        if interval_type in ['(a, b)', '(a, b]']:
            try:
                limit_a = sympy.limit(f, x, a_sym, dir='+')
                if limit_a.is_infinite:
                    is_uc = False
                    reason = f"구간의 왼쪽 끝점 $x \\to {sympy.latex(a_sym)}^+$ 에서 함수의 극한이 무한대로 발산하므로 평등연속이 아닙니다."
            except Exception: pass
        
        # 오른쪽 끝점
        if is_uc and interval_type in ['(a, b)', '[a, b)']:
            try:
                limit_b = sympy.limit(f, x, b_sym, dir='-')
                if limit_b.is_infinite:
                    is_uc = False
                    reason = f"구간의 오른쪽 끝점 $x \\to {sympy.latex(b_sym)}^-$ 에서 함수의 극한이 무한대로 발산하므로 평등연속이 아닙니다."
            except Exception: pass
        
        if not is_uc:
            return "평등연속 아님", reason, f
        
        reason = f"구간의 열린 끝점에서 함수의 극한이 모두 유한한 값으로 수렴하므로 평등연속입니다."
        return "평등연속", reason, f
        
    return "판단 불가", "제공된 판별 로직으로는 평등연속성을 명확히 판단하기 어렵습니다.", f


# --- Streamlit UI 부분 ---
st.title("📈 평등연속성 판별 앱 (π, e, ∞ 지원)")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("함수 입력")
    func_input = st.text_input("f(x) =", value="sin(x)", label_visibility="collapsed")
with col2:
    st.subheader("구간 입력")
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        # st.number_input -> st.text_input 으로 변경
        a_str = st.text_input("구간 시작 (a)", value="-inf", help="숫자, pi, e, inf, -inf 등을 입력하세요. (예: pi/2)")
    with sub_col2:
        b_str = st.text_input("구간 끝 (b)", value="inf", help="숫자, pi, e, inf, -inf 등을 입력하세요. (예: 2*pi)")

col1_btn, col2_radio = st.columns([1, 1])
with col1_btn:
    submitted = st.button("평등연속성 판별", type="primary", use_container_width=True)
with col2_radio:
    interval_type = st.radio("구간 종류", ['[a, b]', '(a, b)', '[a, b)', '(a, b]'], index=1, horizontal=True, label_visibility="collapsed")

st.markdown("---")

if submitted:
    try:
        # 사용자가 입력한 문자열을 SymPy 표현식으로 변환
        # 사용 편의를 위해 'inf'는 'oo'로, 'e'는 대문자 'E'로 치환
        a_str_parsed = a_str.lower().replace('inf', 'oo').replace('e', 'E')
        b_str_parsed = b_str.lower().replace('inf', 'oo').replace('e', 'E')

        a_sym = parse_expr(a_str_parsed, local_dict={"oo": sympy.oo, "E": sympy.E, "pi": sympy.pi})
        b_sym = parse_expr(b_str_parsed, local_dict={"oo": sympy.oo, "E": sympy.E, "pi": sympy.pi})
        
        if not (a_sym.is_real or a_sym.is_infinite) or not (b_sym.is_real or b_sym.is_infinite):
            raise ValueError("유효한 실수 또는 기호가 아닙니다.")
        
        # 무한대가 아닐 경우에만 대소 비교
        if not a_sym.is_infinite and not b_sym.is_infinite:
            if a_sym.evalf() >= b_sym.evalf():
                st.error("구간의 시작점(a)은 끝점(b)보다 작아야 합니다.")
                st.stop()

    except Exception as e:
        st.error(f"구간 값을 해석하는 데 실패했습니다: '{a_str}' 또는 '{b_str}'. 올바른 형식을 입력해주세요. (오류: {e})")
        st.stop()

    with st.spinner('판별 중...'):
        result, reason, func_sympy = check_uniform_continuity(func_input, interval_type, a_sym, b_sym)

        if result == "평등연속": st.success(f"**판별 결과: {result}**")
        elif result == "평등연속 아님": st.error(f"**판별 결과: {result}**")
        else: st.warning(f"**판별 결과: {result}**")

        st.markdown("### 판별 근거")
        st.info(reason)

        if func_sympy:
            st.markdown("### 함수 그래프")
            try:
                # --- 그래프 범위 설정을 위한 로직 ---
                plot_a_num, plot_b_num = -10.0, 10.0 # 기본값
                
                if a_sym.is_infinite and b_sym.is_infinite:
                    plot_a_num, plot_b_num = -10.0, 10.0 # (-inf, inf)
                elif a_sym.is_infinite: # (-inf, b]
                    plot_b_num = float(b_sym.evalf())
                    plot_a_num = plot_b_num - 20.0
                elif b_sym.is_infinite: # [a, inf)
                    plot_a_num = float(a_sym.evalf())
                    plot_b_num = plot_a_num + 20.0
                else: # [a, b]
                    plot_a_num = float(a_sym.evalf())
                    plot_b_num = float(b_sym.evalf())

                f_lambda = sympy.lambdify(sympy.symbols('x'), func_sympy, 'numpy')
                x_vals = np.linspace(plot_a_num, plot_b_num, 500)
                y_vals = f_lambda(x_vals)
                y_vals[np.isinf(y_vals) | np.isneginf(y_vals)] = np.nan

                # --- 그래프 그리기 ---
                plt.style.use('dark_background')
                fig, ax = plt.subplots()
                ax.plot(x_vals, y_vals, label=f'$f(x) = {sympy.latex(func_sympy)}$', color='#3498db')
                
                if not a_sym.is_infinite: ax.axvline(x=plot_a_num, color='gray', linestyle='--', linewidth=1)
                if not b_sym.is_infinite: ax.axvline(x=plot_b_num, color='gray', linestyle='--', linewidth=1)
                
                ax.set_xlabel("x축")
                ax.set_ylabel("y축")
                ax.set_title("함수 구간 그래프", color='white')
                ax.grid(True, linestyle=':', alpha=0.5)
                ax.legend()
                
                # y축 범위 자동 조절
                valid_y = y_vals[~np.isnan(y_vals)]
                if len(valid_y) > 0:
                    q1, q3 = np.percentile(valid_y, [5, 95])
                    iqr = q3 - q1
                    y_min = q1 - 0.5 * iqr
                    y_max = q3 + 0.5 * iqr
                    ax.set_ylim([y_min, y_max])
                
                st.pyplot(fig)
            except Exception as e:
                st.error(f"그래프를 그리는 중 오류가 발생했습니다: {e}")