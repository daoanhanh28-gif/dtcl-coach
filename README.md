# ĐTCL Coach · v1.0 · 2026-10-06

Web trợ lý Đấu Trường Chân Lý (Teamfight Tactics) cho máy chủ Việt Nam — Mùa 18 *Đại Ngàn Kỳ Bí*, bản 18.3b.
Chạy trên Streamlit Community Cloud (miễn phí), nhật ký lưu Google Sheets, AI giải thích bằng Gemini (gói miễn phí).

> Hướng dẫn giúp vào top đều hơn, **không đảm bảo** top 1 mọi ván. Không liên kết chính thức với Riot Games.

## Các trang

| Trang | Làm gì |
|---|---|
| Đội hình meta | 19 đội S/A/B/C (file Excel v1.8), số liệu VN · Trung · Hàn, cách build từng bước, thống kê MetaTFT |
| Trợ lý ván đấu | Nhập tướng / mảnh đồ / lõi / máu / vàng / cấp / vòng → đội nên đi + 2 dự phòng, lên cấp hay đổi tướng, chọn lõi nào, ghép gì trước; thẻ **Ấn → đội hình** và **Lõi → cách đánh** (đúng công thức Excel) |
| Lõi nâng cấp | Tra 254 lõi theo bậc / hạng / nhóm / đội hình, lõi ăn top 1, quy tắc theo mốc, lõi tộc hệ |
| Trang bị & Ấn | Ghép 2 mảnh, bảng ghép 10×10, đồ khởi đầu → đội hình, 21 Ấn, Tạo Tác |
| Bàn cờ & xếp vị trí | Bàn 4×7 bấm để đặt tướng, tải mẫu theo đội, 5 kiểu xếp theo tình huống, 10 nguyên tắc |
| Kinh tế & nhịp ván | Tính vàng / lãi / chuỗi, tỉ lệ ra tướng, máy tính đổi tướng, lộ trình theo lối chơi, Tinh Linh |
| Luyện tập | 10 câu tình huống ngẫu nhiên mỗi lượt, chấm điểm + giải thích |
| Nhật ký ván đấu | Ghi ván → hạng TB, top 4 / top 1 theo đội và lõi, đội hợp tay nhất, biểu đồ |
| Kiến thức & tra cứu | Tộc hệ & 65 tướng, nguyên tắc vàng, 20 thói quen Thách Đấu, từ điển, nguồn |

## Cấu trúc

```
app.py                  điểm vào: đăng nhập (ghi nhớ 90 ngày), thanh bên có phiên bản
core/config.py          VERSION, đọc Secrets, đọc data/
core/engine.py          TOÀN BỘ phép tính (luật trong code) — có test
core/coach.py           AI chỉ diễn giải kết quả của engine
core/auth.py, db.py, llm.py, ui.py
views/*.py              9 trang
data/*.json             dữ liệu game (sửa dữ liệu không cần sửa code)
apps_script/Code.gs     database Google Sheets
tools/build_data.py     dựng tướng / tộc hệ / đồ / lõi / thống kê MetaTFT từ tools/raw
tools/import_excel.py   chuyển file Excel hướng dẫn → data/hd_*.json
tests/                  pytest + Streamlit AppTest
```

## Chạy thử trên máy

```
pip install -r requirements.txt pytest
python -m pytest -q
streamlit run app.py          # mã đăng nhập mặc định: dtcl2026
```

## Cập nhật khi Riot ra bản mới

Nhắn Claude: **“cập nhật meta”** — xem quy trình trong `CAP_NHAT_META.md`.
