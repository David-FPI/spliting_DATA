import streamlit as st
import pandas as pd
import math
import io
import streamlit.components.v1 as components

st.set_page_config(page_title="Phân chia DATA thông minh", layout="wide")
st.title("📊 Chia Đều DATA Cho TV và CS")

# ============ CONFIG ============ #
with st.sidebar:
    st.header("⚙️ Cấu hình")
    total_data = st.number_input("Tổng số lượng DATA:", min_value=1, step=1)

    chia_kieu = st.radio(
        "🔧 Cách chia cho nhóm 'chia ít':",
        ["Số dòng mỗi người", "% tổng DATA của cả nhóm"],
        index=0
    )

    if chia_kieu == "Số dòng mỗi người":
        low_default = st.number_input("🔢 Số dòng chia cho mỗi người 'chia ít':", min_value=1, value=10)
        low_percent = None
    else:
        low_percent = st.slider("📊 % tổng DATA chia cho nhóm chia ít:", 1, 100, 40)
        low_default = None

# ============ INPUT TÊN ============ #
col1, col2 = st.columns(2)
with col1:
    tv_names_raw = st.text_area("📥 Danh sách Tư Vấn (TV):")
    tv_low_raw = st.text_area("🔽 Tên TV chia ít DATA (tùy chọn):")

with col2:
    cs_names_raw = st.text_area("📥 Danh sách Chăm Sóc (CS):")
    cs_low_raw = st.text_area("🔽 Tên CS chia ít DATA (tùy chọn):")

# ============ XỬ LÝ INPUT ============ #
def parse_names(raw):
    return [name.strip() for name in raw.replace(",", "\n").splitlines() if name.strip()]

tv_names = parse_names(tv_names_raw)
cs_names = parse_names(cs_names_raw)
tv_low = set(parse_names(tv_low_raw))
cs_low = set(parse_names(cs_low_raw))

# ============ PHÂN CHIA ============ #
def assign_data(names, low_names, total, low_default=None, low_percent=None):
    low_list = [name for name in names if name in low_names]
    normal_list = [name for name in names if name not in low_names]

    if not names:
        return [], {}

    if low_default is not None:
        low_value = low_default
        total_low = low_value * len(low_list)
    elif low_percent is not None:
        total_low = math.floor((low_percent / 100) * total)
        if len(low_list) == 0:
            low_value = 0
        else:
            low_value = total_low // len(low_list)
        total_low = low_value * len(low_list)
    else:
        raise ValueError("Thiếu thông số chia ít")

    remaining = total - total_low

    if remaining < 0:
        raise ValueError("❗ Tổng số DATA quá nhỏ để chia cho nhóm 'chia ít'")
    if remaining > 0 and len(normal_list) == 0:
        raise ValueError("❗ Không có ai trong nhóm thường để chia phần còn lại")

    per_person = remaining // len(normal_list) if normal_list else 0
    extra = remaining % len(normal_list) if normal_list else 0

    result = []
    stats = {}

    for i, name in enumerate(normal_list):
        count = per_person + (1 if i < extra else 0)
        result.extend([name] * count)
        stats[name] = count

    for name in low_list:
        result.extend([name] * low_value)
        stats[name] = low_value

    return result, stats

# ============ XỬ LÝ KHI ẤN NÚT ============ #
if st.button("🚀 Phân chia DATA"):
    if not tv_names or not cs_names:
        st.error("❗ Vui lòng nhập đầy đủ danh sách TV và CS")
    else:
        try:
            tv_invalid = tv_low - set(tv_names)
            cs_invalid = cs_low - set(cs_names)
            if tv_invalid:
                st.warning(f"⚠️ TV chia ít không có trong danh sách: {', '.join(tv_invalid)}")
            if cs_invalid:
                st.warning(f"⚠️ CS chia ít không có trong danh sách: {', '.join(cs_invalid)}")

            # Phân chia
            assigned_tv, tv_stats = assign_data(tv_names, tv_low, total_data, low_default, low_percent)
            assigned_cs, cs_stats = assign_data(cs_names, cs_low, total_data, low_default, low_percent)

            # Merge TV & CS cùng hàng
            max_len = max(len(assigned_tv), len(assigned_cs))
            assigned_tv += [''] * (max_len - len(assigned_tv))
            assigned_cs += [''] * (max_len - len(assigned_cs))

            df = pd.DataFrame({"Tên TV": assigned_tv, "Tên CS": assigned_cs})

            # Hiển thị kết quả
            st.subheader("📊 Kết quả phân chia")
            st.dataframe(df, use_container_width=True)

            # Copy nhanh
            st.subheader("📋 Copy nhanh sang Excel / Google Sheets")
            csv_str = df.to_csv(sep="\t", index=False, header=False)
            escaped_csv_str = csv_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            html_code = f"""
                <textarea id="dataArea" rows="15" style="width:100%">{escaped_csv_str}</textarea>
                <button id="copyBtn" onclick="copyToClipboard()"
                        style="margin-top:10px;padding:6px 16px;font-weight:bold;background-color:#4CAF50;color:white;border:none;border-radius:4px;cursor:pointer">
                    📋 Copy vào Clipboard
                </button>
                <p id="copyMsg" style="font-size: 0.9rem; color: grey; margin-top:5px;"></p>
                <script>
                function copyToClipboard() {{
                    const text = document.getElementById("dataArea").value;
                    navigator.clipboard.writeText(text).then(function() {{
                        var btn = document.getElementById("copyBtn");
                        btn.innerHTML = "✅ Đã copy!";
                        btn.style.backgroundColor = "#2E7D32";
                        document.getElementById("copyMsg").innerText = "➡️ Dán vào Excel hoặc Google Sheets";
                        setTimeout(function() {{
                            btn.innerHTML = "📋 Copy vào Clipboard";
                            btn.style.backgroundColor = "#4CAF50";
                        }}, 2000);
                    }});
                }}
                </script>
            """
            components.html(html_code, height=420)

            # Thống kê
            st.subheader("📈 Thống kê")
            col3, col4 = st.columns(2)
            with col3:
                st.markdown("### 📌 TV")
                st.dataframe(pd.DataFrame(tv_stats.items(), columns=["Tên TV", "Số lượng"]))
            with col4:
                st.markdown("### 📌 CS")
                st.dataframe(pd.DataFrame(cs_stats.items(), columns=["Tên CS", "Số lượng"]))

            # Xuất Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="PhanCong")
            st.download_button("📥 Tải file Excel kết quả", output.getvalue(), "phan_cong.xlsx")

        except ValueError as e:
            st.error(str(e))
