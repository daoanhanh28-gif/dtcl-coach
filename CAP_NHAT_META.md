# ĐTCL Coach · v1.3 · 2026-10-20 — Quy trình “cập nhật meta”

Khi Riot ra bản mới (khoảng 2 tuần / lần), anh Peach chỉ cần nhắn Claude: **“cập nhật meta”**.
Claude làm theo các bước dưới. Mọi dữ liệu nằm trong `data/*.json` — không cần sửa code.

## 0. Giữ bản cũ để xem song song
- Chép toàn bộ `data/*.json` hiện tại vào `data/ban/<bản cũ>/` (ví dụ `data/ban/18.4b/`).
- Thêm dòng vào `BO_DU_LIEU` trong `core/config.py`, sửa `BO_MAC_DINH` thành bản mới. Bộ cũ hơn có thể xoá khỏi danh sách.
- Thêm vào `meta.json` của bộ cũ: `bo`, `ban_moi`, `ngay_ban_moi`, `vn_nguon`, `excel` (xem bộ 18.3b làm mẫu).
- Sao lưu `tools/raw/*` vào `tools/raw/<bản cũ>/`.

## 1. Kiểm tra bản hiện tại
- Tra lịch bản vá (esports.gg / Riot) → bản đang chạy ở VN, bản kế tiếp.
- Ghi vào `tools/build_data.py` (biến `GAME`, `NGAY_LAY`).

## 2. Dữ liệu game bản Việt (tướng, tộc hệ, đồ, lõi)
- Nguồn: `https://raw.communitydragon.org/latest/cdragon/tft/vi_vn.json` (và `en_us.json`).
- Môi trường đám mây của Claude không vào được trang này → mở bằng **trình duyệt tích hợp** trên máy anh,
  dùng JavaScript lọc `setData` của mùa hiện tại, chép kết quả vào `tools/raw/champs.tsv`, `augments_*.tsv`.
- Mùa mới: sửa bảng `TRAITS`, `ITEMS`, `EMBLEMS` trong `tools/build_data.py`.

## 3. Thống kê
- MetaTFT: API `comps_data` + `comps_stats` (Bạch Kim+, 3 ngày) → `tools/raw/comps_metatft.tsv`;
  `augments_tiers` → `tools/raw/augment_tiers_metatft.tsv`; độ hiếm lõi → `augment_rarity_metatft.txt`.
- MetaTFT `comp_details?comp=<id>` (form cấp 4/5/6/7, ô đứng, mốc lên cấp) → `tools/raw/comp_details_metatft.tsv`;
  `unit_items_processed` (đồ hay dùng từng tướng) → `tools/raw/unit_items_metatft.tsv`; chạy `python tools/build_chi_tiet.py`.
- Bản mới: ghi danh sách tăng / giảm vào `data/ban_cap_nhat.json` (trang Phân tích bản cập nhật tự xếp đội theo đó).
- Số liệu máy chủ VN: OP.GG `https://op.gg/tft/meta-trends/comps?region=vn` (mở bằng Chrome, đọc mảng `decks` trong trang)
  → `tools/raw/vn_opgg.tsv`. Ghi `phien_ban`, `moc` (mốc tộc/hệ bị đổi) và `muc` (0,5 = chỉnh nhỏ) trong `data/ban_cap_nhat.json`.
- Thống kê Ấn (ai cầm tốt, tactics.tools) → `tools/raw/tactics_tools_<bản>.txt`; bùa (MetaTFT Wisp Tier List + tên Việt
  Community Dragon) → `tools/raw/tinh_linh_<bản>.txt`; chạy `python tools/build_cam_nang.py` (nội dung tempo / lõi top 1 / cặp lõi
  viết tay trong file đó — xem lại mỗi bản).
- Chạy `python tools/cap_nhat_ban.py` (sửa `BO`, `VN_BAN`, `VN_NGAY`, `VN_SO_VAN` ở đầu file) → bảng VN, xu hướng bản mới
  cho 19 đội, mục “Có gì mới”. Không cần làm lại file Excel nếu chỉ đổi số liệu.
- **Không bịa** tỉ lệ thắng / hạng trung bình. Không lấy được số thì ghi rõ “chưa có số liệu”.

## 4. Nội dung hướng dẫn (file Excel)
- Cập nhật file Excel hướng dẫn (tăng phiên bản v1.9, v2.0…), đặt vào `tools/raw/excel/`.
- Chạy `python tools/import_excel.py <file.xlsx>` → ra `data/hd_*.json`.

## 5. Dựng lại + kiểm thử + phiên bản
```
python tools/build_data.py
python tools/build_chi_tiet.py
python tools/import_excel.py     # chỉ khi có file Excel mới
python tools/cap_nhat_ban.py
python -m pytest -q
```
- Tăng phiên bản web: `core/config.py` (VERSION, VERSION_DATE), file `VERSION`, `README.md`, **dòng đầu mọi file**.
- Đẩy lên GitHub → GitHub tự chạy test (tab Actions) → Streamlit Cloud tự cập nhật.
- Mở web thật, xem số phiên bản ở chân trang. Kẹt “Your app is in the oven” quá vài phút → Manage app → Reboot.
