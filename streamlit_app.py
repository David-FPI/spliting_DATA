# test.py
import streamlit as st
import pandas as pd
import json
import os
import streamlit.components.v1 as components
# ======== CẤU HÌNH FILE LƯU NHÓM ======== #
GROUPS_FILE = "groups.json"

# ===== Hàm lưu và tải nhóm ===== #
def save_groups(group_a, group_b, group_c):
    data = {"A": group_a, "B": group_b, "C": group_c}
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"A": [], "B": [], "C": []}

# ===== Hàm chính chia data theo dây chuyền bánh xe ===== #
def chia_data_day_chuyen(danh_sach_nhan_su, groups, total_data, last_person=None):
    # Sắp xếp lại danh sách nhân sự theo đúng thứ tự nhóm A → B → C
    group_a = [name for name in groups.get("A", []) if name in danh_sach_nhan_su]
    group_b = [name for name in groups.get("B", []) if name in danh_sach_nhan_su]
    group_c = [name for name in groups.get("C", []) if name in danh_sach_nhan_su]


    def make_sole_queue(names, count):
        if not names:
            return []
        queue = []
        i = 0
        while len(queue) < count * len(names):
            queue.append(names[i % len(names)])
            i += 1
        return queue

    base_unit = len(group_a) * 3 + len(group_b) * 2 + len(group_c) * 1
    if base_unit == 0:
        raise ValueError("⚠️ Không xác định được nhóm cho bất kỳ ai trong danh sách!")

    rounds = (total_data + base_unit - 1) // base_unit

    queue = []
    for _ in range(rounds):
        queue += make_sole_queue(group_a, 3)
        queue += make_sole_queue(group_b, 2)
        queue += make_sole_queue(group_c, 1)

    if last_person and last_person in queue:
        idx = len(queue) - 1 - queue[::-1].index(last_person)
        queue = queue[idx+1:] + queue[:idx+1]

    return queue[:total_data]

# ===== Giao diện Streamlit ===== #
st.set_page_config(page_title="Bánh Xe DATA", layout="wide")
st.title("🔄 Chia DATA theo dây chuyền nhóm A-B-C")

tabs = st.tabs(["📥 Thiết lập nhóm", "🚀 Chạy chia DATA"])

# ===== TAB 1: Thiết lập nhóm ===== #
with tabs[0]:
    st.subheader("📌 Thiết lập nhóm cố định")
    group_a_raw = st.text_area("👑 Nhóm A (3 data/người)", placeholder="Nhập tên cách nhau bởi dấu xuống dòng hoặc dấu phẩy")
    group_b_raw = st.text_area("🧑‍💼 Nhóm B (2 data/người)")
    group_c_raw = st.text_area("👤 Nhóm C (1 data/người)")

    def parse_names(raw):
        return [x.strip() for x in raw.replace(",", "\n").splitlines() if x.strip()]

    if st.button("💾 Lưu nhóm"):
        save_groups(parse_names(group_a_raw), parse_names(group_b_raw), parse_names(group_c_raw))
        st.success("✅ Đã lưu nhóm thành công!")

    if os.path.exists(GROUPS_FILE):
        st.info("📂 Nhóm hiện tại:")
        groups = load_groups()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 👑 Nhóm A")
            st.write(groups.get("A", []))
        with col2:
            st.markdown("### 🧑‍💼 Nhóm B")
            st.write(groups.get("B", []))
        with col3:
            st.markdown("### 👤 Nhóm C")
            st.write(groups.get("C", []))

# ===== TAB 2: Chạy chia ===== #
with tabs[1]:
    st.sidebar.header("⚙️ Cấu hình chia")
    total_data = st.sidebar.number_input("📦 Tổng số DATA cần chia", min_value=1, step=1)
    last_person = st.sidebar.text_input("🔁 Tên người cuối cùng đã nhận (để tiếp tục)", placeholder="Ví dụ: Nhân")

    st.subheader("📥 Danh sách nhân sự cần chia (lộn xộn)")
    raw_names = st.text_area("✍️ Dán danh sách nhân sự (tự động dò nhóm từ danh sách đã lưu)")
    danh_sach_nhan_su = parse_names(raw_names)

    if st.button("🚀 Bắt đầu chia"):
        try:
            groups = load_groups()
            result = chia_data_day_chuyen(danh_sach_nhan_su, groups, total_data, last_person)

            # 🚀 Thêm xử lý Mã Team
            team_map = {
                "1": "1Hưng",
                "2": "2Kiệt",
                "3": "3Ruby",
                "4": "4Sơn"
            }

            team_labels = []
            for name in result:
                if name and name[0] in team_map and name[1:].isalpha():
                    team_labels.append(team_map[name[0]])
                else:
                    team_labels.append("")

            df = pd.DataFrame({
                "Mã Team": team_labels,
                "Nhân sự nhận DATA": result
            })
            # 📈 Thống kê tổng số DATA mỗi người nhận
            thong_ke = pd.Series(result).value_counts().reset_index()
            thong_ke.columns = ["Nhân sự", "Số DATA nhận"]

            st.subheader("📈 Thống kê số DATA mỗi nhân sự")
            st.dataframe(thong_ke, use_container_width=True)

            # Cho phép tải file thống kê
            st.download_button("📥 Tải file thống kê", thong_ke.to_csv(index=False).encode(), "thong_ke_data.csv")

            st.subheader("📊 Kết quả phân chia")
            st.dataframe(df, use_container_width=True)

            # ✅ COPY CLIPBOARD
            tsv_str = df.to_csv(sep="\t", index=False, header=False)
            escaped_tsv_str = tsv_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            html_code = f"""
                <textarea id="dataArea" rows="10" style="width:100%;font-size:14px;">{escaped_tsv_str}</textarea>
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
                            document.getElementById("copyMsg").innerText = "";
                        }}, 2000);
                    }});
                }}
                </script>
            """
            components.html(html_code, height=300)

            # ✅ Tải file
            st.download_button("📥 Tải file Excel", df.to_csv(index=False).encode(), "day_chuyen_data.csv")

            st.success(f"✅ Chia xong, người cuối cùng là: **{result[-1]}** — dùng để tiếp vòng sau.")

        except ValueError as e:
            st.error(str(e))
