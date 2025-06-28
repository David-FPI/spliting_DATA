import streamlit as st
import pandas as pd
import math
import io

st.set_page_config(page_title="Phân chia DATA thông minh", layout="wide")
st.title("📊 Chia Đều DATA Cho TV và CS (Có hỗ trợ nhân sự chia ít)")

# Input từ người dùng
with st.sidebar:
    st.header("⚙️ Cấu hình")
    total_data = st.number_input("Tổng số lượng DATA:", min_value=1, step=1, help="Tổng lượng data bạn muốn chia đều")
    low_default = st.number_input("Số dòng chia ít (default):", min_value=1, value=9, step=1, help="Những người được đánh dấu 'chia ít' sẽ nhận số dòng này")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    tv_names_raw = st.text_area("📥 Danh sách Tư Vấn (TV):", placeholder="Nhập tên, cách nhau bởi dấu phẩy hoặc xuống dòng", help="Những người cần chia DATA bên nhóm TV")
    tv_low_raw = st.text_area("🔽 Tên TV chia ít DATA:", placeholder="Không bắt buộc", help="Nhập tên người TV cần chia ít DATA")

with col2:
    cs_names_raw = st.text_area("📥 Danh sách Chăm Sóc (CS):", placeholder="Nhập tên, cách nhau bởi dấu phẩy hoặc xuống dòng", help="Những người cần chia DATA bên nhóm CS")
    cs_low_raw = st.text_area("🔽 Tên CS chia ít DATA:", placeholder="Không bắt buộc", help="Nhập tên người CS cần chia ít DATA")

# Xử lý input
def parse_names(raw):
    return [name.strip() for name in raw.replace(",", "\n").splitlines() if name.strip()]

tv_names = parse_names(tv_names_raw)
cs_names = parse_names(cs_names_raw)
tv_low = set(parse_names(tv_low_raw))
cs_low = set(parse_names(cs_low_raw))

# Hàm phân bổ data

def assign_data(names, low_names, total, low_default=9):
    low_list = [name for name in names if name in low_names]
    normal_list = [name for name in names if name not in low_names]

    total_low = low_default * len(low_list)
    remaining = total - total_low

    if remaining < 0:
        raise ValueError("Tổng số DATA quá nhỏ để chia cho nhóm 'chia ít'")
    if remaining > 0 and len(normal_list) == 0:
        raise ValueError("Không có ai để chia phần DATA còn lại")

    per_person = remaining // len(normal_list) if normal_list else 0
    extra = remaining % len(normal_list) if normal_list else 0

    result = []
    stats = {}

    for i, name in enumerate(normal_list):
        count = per_person + (1 if i < extra else 0)
        result.extend([name] * count)
        stats[name] = count

    for name in low_list:
        result.extend([name] * low_default)
        stats[name] = low_default

    return result, stats

if st.button("🚀 Phân chia DATA"):
    if not tv_names or not cs_names:
        st.error("❗ Vui lòng nhập đầy đủ danh sách TV và CS")
    else:
        try:
            # Cảnh báo nếu có tên chia ít không nằm trong danh sách
            tv_invalid = tv_low - set(tv_names)
            cs_invalid = cs_low - set(cs_names)
            if tv_invalid:
                st.warning(f"⚠️ Các tên TV chia ít không nằm trong danh sách TV: {', '.join(tv_invalid)}")
            if cs_invalid:
                st.warning(f"⚠️ Các tên CS chia ít không nằm trong danh sách CS: {', '.join(cs_invalid)}")

            assigned_tv, tv_stats = assign_data(tv_names, tv_low, total_data, low_default)
            assigned_cs, cs_stats = assign_data(cs_names, cs_low, total_data, low_default)

            max_len = max(len(assigned_tv), len(assigned_cs))
            assigned_tv += [''] * (max_len - len(assigned_tv))
            assigned_cs += [''] * (max_len - len(assigned_cs))

            df = pd.DataFrame({"Tên TV": assigned_tv, "Tên CS": assigned_cs})

            st.subheader("📊 Kết quả phân chia")
            st.dataframe(df, use_container_width=True)

            st.subheader("📈 Thống kê")
            col3, col4 = st.columns(2)
            with col3:
                st.markdown("### 📌 TV")
                st.dataframe(pd.DataFrame(tv_stats.items(), columns=["Tên TV", "Số lượng"]))
            with col4:
                st.markdown("### 📌 CS")
                st.dataframe(pd.DataFrame(cs_stats.items(), columns=["Tên CS", "Số lượng"]))

            # Xuất file Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="PhanCong")
                workbook = writer.book
                worksheet = writer.sheets["PhanCong"]
                for col_idx, name_list in enumerate([tv_names, cs_names]):
                    for i, name in enumerate(name_list):
                        color = "#D9E1F2" if i % 2 == 0 else "#FCE4D6"
                        cell_format = workbook.add_format({'bg_color': color})
                        for row_num, val in enumerate(df.iloc[:, col_idx]):
                            if val == name:
                                worksheet.write(row_num + 1, col_idx, val, cell_format)

            st.download_button(
                label="📥 Tải file Excel kết quả",
                data=output.getvalue(),
                file_name="phan_cong_data_TV_CS.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except ValueError as e:
            st.error(f"🚫 Lỗi: {str(e)}")
