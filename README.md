# ĐTCL Coach · v1.4 · 2026-10-22

Web trợ lý Đấu Trường Chân Lý (Teamfight Tactics) cho máy chủ Việt Nam — Mùa 18 *Đại Ngàn Kỳ Bí*.
Ba bộ dữ liệu chọn ở thanh bên: **18.5 (đang chạy, mặc định)**, **18.4b (bản trước)** và **18.3b (cũ)**.
Mở thêm tab với link `?ban=18.4b` hoặc `?ban=18.3b` để xem song song.
Chạy trên Streamlit Community Cloud (miễn phí), nhật ký lưu Google Sheets, AI giải thích bằng Gemini (gói miễn phí).

> Hướng dẫn giúp vào top đều hơn, **không đảm bảo** top 1 mọi ván. Không liên kết chính thức với Riot Games.

## Các trang

| Trang | Làm gì |
|---|---|
| Cẩm nang Thách Đấu | Top đội mạnh / mạnh ít người chơi / dễ vào top ít điều kiện (OP.GG VN), đánh tempo như Thách Đấu (mốc lên cấp thật từ MetaTFT), lõi top 1 & cách xử lý, cặp lõi mạnh, bùa (Tinh Linh) theo giai đoạn |
| Đội hình meta | 19 đội S/A/B/C (file Excel v1.8), số liệu VN (OP.GG 18.4b) · Trung · Hàn, **form theo vòng** (cấp 4 → hoàn chỉnh, vị trí đứng thật), thống kê MetaTFT |
| Trợ lý ván đấu | 3 bước: tình hình → **bấm hình** tướng / mảnh đồ / Ấn → **4 dòng kết luận** (đội nên đi, lên cấp hay đổi tướng, ghép gì, lõi nào) + thẻ “vì sao”, form theo vòng; thẻ **Ấn → đội hình** (ai đeo Ấn, mốc tộc/hệ ở cấp 8 & 9, thay tướng nào để lên mốc cao hơn, ai cầm Ấn đầu trận) và **Lõi → cách đánh** |
| Phân tích bản cập nhật | Tăng / giảm bản mới có hình; đội nên chơi, được lợi, mạnh nhất, dễ top 1, dễ top 4, mạnh mà ít người chơi (spam), dễ chơi, nên tránh |
| Lõi nâng cấp | Tra 254 lõi theo bậc / hạng / nhóm / đội hình, lõi ăn top 1, quy tắc theo mốc, lõi tộc hệ |
| Trang bị & Ấn | Bấm hình ghép 2 mảnh, **đồ theo từng tướng** (MetaTFT + file hướng dẫn), bảng ghép 10×10, đồ khởi đầu → đội hình, 21 Ấn, Tạo Tác có hình |
| Bàn cờ & xếp vị trí | Bàn 4×7 bấm để đặt tướng, tải mẫu theo đội, 5 kiểu xếp theo tình huống, 10 nguyên tắc |
| Kinh tế & nhịp ván | Tính vàng / lãi / chuỗi, tỉ lệ ra tướng, máy tính đổi tướng, lộ trình theo lối chơi, Tinh Linh |
| Luyện tập | 10 câu tình huống ngẫu nhiên mỗi lượt, chấm điểm + giải thích |
| Nhật ký ván đấu | Ghi ván → hạng TB, top 4 / top 1 theo đội và lõi, đội hợp tay nhất, biểu đồ |
| Kiến thức & tra cứu | Tộc hệ & 65 tướng, nguyên tắc vàng, 20 thói quen Thách Đấu, từ điển, nguồn |

## Cấu trúc

```
app.py                  điểm vào: đăng nhập (ghi nhớ 90 ngày), thanh bên có phiên bản
core/config.py          VERSION, đọc Secrets, đọc data/, BO_DU_LIEU (bộ dữ liệu theo bản vá)
core/engine.py          phép tính chính (luật trong code) — có test
core/plan.py            form theo vòng, tối ưu mốc tộc/hệ với Ấn, phân tích bản cập nhật — có test
core/coach.py           AI chỉ diễn giải kết quả của engine
core/auth.py, db.py, llm.py, ui.py
views/*.py              10 trang
data/*.json             dữ liệu game bản mới (sửa dữ liệu không cần sửa code)
data/ban/18.3b/*.json   bộ dữ liệu bản cũ, giữ nguyên để xem song song
apps_script/Code.gs     database Google Sheets
tools/build_data.py     dựng tướng / tộc hệ / đồ / lõi / thống kê MetaTFT từ tools/raw
tools/import_excel.py   chuyển file Excel hướng dẫn → data/hd_*.json
tools/build_chi_tiet.py form theo cấp, vị trí đứng, đồ từng tướng (MetaTFT) → data/metatft_chi_tiet.json
tools/cap_nhat_ban.py   bảng VN (OP.GG) + xu hướng bản mới → data/hd_*.json (không cần làm lại file Excel)
tests/                  pytest + Streamlit AppTest
```

## Chạy thử trên máy

```
pip install -r requirements.txt pytest
python -m pytest -q
streamlit run app.py          # mã đăng nhập mặc định: dtcl2026
```

## Lịch sử phiên bản

- **v1.4 · 2026-10-22** — Bản 18.5 chính thức làm mặc định: ghi chú Riot 18.5 (khác bản xem trước: Sivir, Bụi Gai Đỏ, Alune, Taric
  tăng thêm; Draven không đổi), thống kê MetaTFT 18.5, OP.GG VN 18.5 (7 đội đủ mẫu). Cẩm nang thêm thẻ “được lợi & spam”:
  so hạng TB từng đội 18.5 với 18.4b, đội mạnh ít người chơi, top quốc tế. 18.4b giữ làm bản trước.

- **v1.3 · 2026-10-20** — Bộ dữ liệu **18.4b** (bản đang chạy, mặc định): thay đổi 18.4 + 18.4b, OP.GG VN 32 đội (196.456 ván),
  thống kê Ấn tactics.tools. Trang mới **Cẩm nang Thách Đấu**. Trợ lý → Ấn: tối ưu lại, xếp đội quanh chủ lực meta
  (đội đủ mẫu MetaTFT, mốc tộc của chủ lực nặng gấp 3, người cầm Ấn theo thống kê), mỗi chủ lực 1 đội, có gợi ý đổi tướng.

- **v1.2 · 2026-10-20** — Cập nhật lên bản 18.5: thống kê MetaTFT 18.4b (60 cụm đội, form theo vòng, đồ từng tướng, bảng lõi),
  số liệu máy chủ VN OP.GG 18.4b (28 đội, 171.120 ván), danh sách tăng/giảm 18.5 (tướng, tộc hệ, lõi, trang bị, Tinh Linh,
  luật giới hạn lõi), xu hướng 18.5 tự tính cho 19 đội, lõi mới / đổi số 18.4–18.4b. Giữ bộ 18.3b cũ: chọn ở thanh bên
  hoặc mở `?ban=18.3b` ở tab khác.

- **v1.1 · 2026-10-06** — Trợ lý ván đấu bấm hình + kết luận 4 dòng; hình ở mọi tên tướng / đồ / Ấn / Tạo Tác / lõi / tộc hệ / Tinh Linh;
  Ấn → đội hình tối ưu mốc tộc/hệ (cấp 8 & 9), người cầm Ấn đầu trận; form theo vòng cho mọi đội; trang Phân tích bản cập nhật;
  đồ theo từng tướng; bàn cờ có hình và tải vị trí đứng thật.
- **v1.0 · 2026-10-06** — bản đầu: 9 trang, dữ liệu Excel v1.8 + Community Dragon + MetaTFT.

## Cập nhật khi Riot ra bản mới

Nhắn Claude: **“cập nhật meta”** — xem quy trình trong `CAP_NHAT_META.md`.
