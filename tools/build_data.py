# ĐTCL Coach v1.0 (2026-10-06) — dựng data/*.json từ dữ liệu thô (Community Dragon + MetaTFT)
"""
Chạy:  python tools/build_data.py
Đọc tools/raw/*.tsv|txt  →  ghi data/tuong.json, toc_he.json, trang_bi.json, loi.json, doi_hinh.json, meta.json
Các file kinh_te.json, cau_hoi.json, meo.json được viết tay (không do script này tạo).
Khi Riot ra bản mới: lấy lại dữ liệu thô (xem CAP_NHAT_META.md) rồi chạy lại script.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "tools" / "raw"
DATA = ROOT / "data"

GAME = {"mua": 18, "ten_mua": "Enchanted Wilds", "ten_mua_vi": "Đại Ngàn Kỳ Bí", "phien_ban": "18.3b"}
NGAY_LAY = "2026-10-06"
CDN = "https://raw.communitydragon.org/latest/game/"

# --------------------------------------------------------------------------- tộc / hệ
# khoá ngắn (dùng chung với MetaTFT) → tên VN, loại, mô tả ngắn do ĐTCL Coach viết lại
TRAITS = {
    "Blackthorn": ("Gai Đen", "Tộc", "Hiến tế đồng minh đặt trên ô Gai Đen trước giao tranh để tăng Máu cho cả đội; tướng Gai Đen nhận thêm chỉ số theo vai trò, sao và giá của vật tế."),
    "Blossom": ("Hoa Linh", "Tộc", "Mua Tinh Linh trong cửa hàng; sau mỗi giao tranh Tinh Linh mạnh lên. Tướng Hoa Linh nhận thêm SMCK, SMPT và Máu. Mốc cao: Tinh Linh xuất hiện mọi lượt, hoàn vàng, mua 2 Tinh Linh/vòng."),
    "Coven": ("Tiên Hắc Ám", "Tộc", "Tích Tinh Hoa khi hạ gục và khi thua. Từ một mốc Tinh Hoa có thể đổi lấy phần thưởng hoặc tiếp tục tích — đội chơi thua chuỗi để lấy thưởng lớn."),
    "Elderwood": ("Thần Rừng", "Tộc", "Nhận cây Thần Rừng đặt trên bàn: Cây Vỏ Đá (đỡ đòn), Hoa Sinh Mệnh, Hộ Vệ Rừng. Mốc 7/9/11 cây lên 2–3 sao."),
    "Fae": ("Tiên Linh", "Tộc", "Sát thương, hồi máu, lá chắn của đội hút Pix. Mỗi Pix tăng SMCK/SMPT cho tướng Tiên Linh và hồi máu khi thấp máu; đủ 7 Pix sẽ ra Pix Hoàng Kim cho vàng."),
    "Inferno": ("Hỏa Ngục", "Tộc", "Tướng Hỏa Ngục gây Thiêu Đốt + Vết Thương Sâu. Mốc 3: sau giao tranh vài ô cửa hàng bốc cháy, hiện tướng cao hơn 1 bậc."),
    "Lunar": ("Mặt Trăng", "Tộc", "Tướng Mặt Trăng và đồng minh đứng cạnh nhận Tốc Độ Đánh và SMPT; tướng Mặt Trăng nhận nhiều hơn."),
    "Primal": ("Nguyên Sinh", "Tộc", "Chọn 1 trong 4 Phước Lành Nguyên Sinh; mốc 4 mạnh hơn."),
    "Riftbeast": ("Quái Rừng", "Tộc", "Chọn Quái Rừng Đầu Đàn nhận bùa độc nhất. Cửa hàng định kỳ tràn Quái Rừng; Quái Rừng lớn dần trong giao tranh. Mốc 10: +1 số tướng."),
    "Solar": ("Mặt Trời", "Tộc", "Cả đội nhận lá chắn và sát thương phép cộng thêm; mạnh dần theo số tướng 3 sao khác nhau trên sân."),
    "Sprykin": ("Tinh Nghịch", "Tộc", "Nhận Lông Xù Khổng Lồ (LXKL); thả 1 tướng Tinh Nghịch lên làm Kỵ Sĩ. Mốc cao: kỹ năng LXKL áp dụng lên các tướng Tinh Nghịch."),
    "Adaptor": ("Thích Ứng", "Hệ", "Kỹ năng đổi theo SMCK hay SMPT cao hơn; nhận thêm chỉ số đó."),
    "Brawler": ("Đấu Sĩ", "Hệ", "Cả đội thêm Máu tối đa, tướng Đấu Sĩ nhận nhiều hơn."),
    "Defender": ("Vệ Quân", "Hệ", "Cả đội thêm Giáp và Kháng Phép, tướng Vệ Quân nhận nhiều hơn."),
    "Executioner": ("Đao Phủ", "Hệ", "Tướng Đao Phủ nhận Chuẩn Xác (kỹ năng chí mạng được) và Tỉ Lệ Chí Mạng; mốc cao gây chảy máu sát thương chuẩn."),
    "Hunter": ("Thợ Săn", "Hệ", "Tướng Thợ Săn nhận SMCK; giữ một mục tiêu đủ lâu thì nhận thêm Khuếch Đại Sát Thương."),
    "Invoker": ("Thuật Sĩ", "Hệ", "Cả đội tăng Hồi Năng Lượng, tướng Thuật Sĩ nhận nhiều hơn."),
    "Juggernaut": ("Dũng Sĩ", "Hệ", "Cả đội nhận Chống Chịu (giảm sát thương), tướng Dũng Sĩ nhận nhiều hơn."),
    "Rapidfire": ("Liên Kích", "Hệ", "Cả đội nhận Tốc Độ Đánh; tướng Liên Kích cộng dồn thêm Tốc Độ Đánh mỗi đòn đánh."),
    "Slayer": ("Tàn Phá", "Hệ", "Tướng Tàn Phá nhận Hút Máu Toàn Phần và sát thương cộng thêm, gấp đôi lên kẻ địch thấp máu."),
    "Spellweaver": ("Thuật Sư", "Hệ", "Cả đội nhận SMPT; tướng Thuật Sư nhận nhiều hơn và cộng dồn SMPT mỗi lần tung chiêu."),
    "Summoner": ("Triệu Hồi", "Hệ", "Cường hóa đơn vị triệu hồi: Yorick (Máu), Azir (Sát thương), Chim Mẹ (Sát thương), Zyra (cây đánh thêm)."),
    "Vanguard": ("Tiên Phong", "Hệ", "Đầu giao tranh và khi xuống thấp máu, tướng Tiên Phong nhận Lá Chắn theo Máu tối đa."),
    "Caustic": ("Ăn Mòn", "Độc nhất", "Sát thương của Kog'Maw giảm Giáp và Kháng Phép kẻ địch."),
    "FloraFatalis": ("Thực Vật", "Tộc", "Tướng Thực Vật thu hoạch khi tham gia hạ gục: nhận Năng Lượng và hồi máu cho đồng minh yếu nhất."),
    "Rival": ("Khắc Tinh", "Độc nhất", "Kha'Zix và Rengar: chỉ kích hoạt khi ra sân 1 trong 2. Tích điểm hạ gục để tiến hóa Kha'Zix / cường hóa Rengar."),
    "Battlemage": ("Cự Thạch", "Độc nhất", "Malphite tăng Giáp và Kháng Phép theo số kẻ địch đang nhắm vào mình."),
    "Maokai_UniqueTrait": ("Cổ Thụ", "Độc nhất", "Mỗi kẻ địch chết gần Maokai, Maokai nhận Máu tối đa vĩnh viễn."),
    "Greenfather": ("Thụ Thần", "Độc nhất", "Ivern gieo hạt để nuôi ô trên bàn, ô đó tăng hiệu ứng cho tướng đứng trên."),
    "AluneUniqueTrait": ("Hòa Hợp", "Độc nhất", "Alune đổi pha trăng mỗi lần tung chiêu: lúc cho cả đội Chống Chịu, lúc cho Khuếch Đại Sát Thương."),
    "ZyraUniqueTrait": ("Vườn Gai", "Độc nhất", "Cả đội nhận Chống Chịu, tăng thêm khi đủ cây của Zyra còn sống."),
    "Emerald": ("Lục Bảo", "Độc nhất", "Kéo 1 đồng minh vào Taric để ghép đôi, đồng minh nhận hiệu ứng từ kỹ năng Taric."),
    "DravenUniqueTrait": ("Săn Thưởng", "Độc nhất", "Chọn nhiệm vụ; Draven hoàn thành nhiệm vụ để nhận thưởng rồi chọn nhiệm vụ mới."),
    "ApexPredator": ("Bá Chủ", "Độc nhất", "Rồng Ngàn Tuổi chiếm 2 ô đội hình và cộng 2 mốc Quái Rừng."),
    "Avatar": ("Thế Thần", "Độc nhất", "Lux mang theo một tộc/hệ được chọn; tộc/hệ đó tính gấp đôi."),
    "Eclipse": ("Thiên Thực", "Đặc biệt", "Sau vài giây, tướng Thiên Thực hạ gục kẻ địch thấp máu nhất, lặp lại định kỳ (kết hợp Mặt Trời + Mặt Trăng)."),
}
TRAIT_ICON = {
    "Blackthorn": "oldgod", "Slayer": "ravager", "Battlemage": "monolith", "Maokai_UniqueTrait": "oldgrowth",
    "AluneUniqueTrait": "attuned", "ZyraUniqueTrait": "zyraorigin", "Emerald": "emeraldaspect",
    "DravenUniqueTrait": "bountyseeker", "Avatar": "avatar", "FloraFatalis": "florafatalis",
}
TRAIT_MINS = {  # mốc kích hoạt (Community Dragon)
    "Elderwood": [3, 5, 7, 9, 11], "Avatar": [1], "Slayer": [2, 4, 6], "DravenUniqueTrait": [1], "Solar": [3],
    "Sprykin": [3, 5, 7], "Adaptor": [2, 3, 4], "Coven": [3, 4, 5, 7], "Eclipse": [1], "Hunter": [2, 3, 4, 5],
    "Maokai_UniqueTrait": [1], "Battlemage": [1], "Primal": [2, 4], "Greenfather": [1], "Invoker": [2, 3, 4, 5],
    "Rapidfire": [2, 3, 4, 5], "Juggernaut": [2, 4, 6], "Inferno": [2, 3, 5, 7], "AluneUniqueTrait": [1],
    "Rival": [1], "Vanguard": [2, 4, 6], "Brawler": [2, 4, 6], "Blackthorn": [2, 4, 6], "Executioner": [2, 3, 4],
    "ApexPredator": [1], "Riftbeast": [3, 5, 7, 10], "Caustic": [1], "Fae": [2, 4], "Lunar": [2, 3, 4, 5],
    "Defender": [2, 4, 6], "Spellweaver": [2, 4, 6], "ZyraUniqueTrait": [1], "FloraFatalis": [1, 2],
    "Summoner": [2, 3], "Blossom": [3, 5, 7, 9, 11], "Emerald": [1],
}
VI2KEY = {v[0]: k for k, v in TRAITS.items()}

# --------------------------------------------------------------------------- trang bị
# khoá MetaTFT → (tên VN, tên EN, công thức, chỉ số, tác dụng, nhóm, file icon cdragon)
COMP = {  # thành phần
    "BFSword": ("Kiếm B.F.", "B.F. Sword", "+10% SMCK", "tft_item_bfsword"),
    "RecurveBow": ("Cung Gỗ", "Recurve Bow", "+10% Tốc Độ Đánh", "tft_item_recurvebow"),
    "NeedlesslyLargeRod": ("Gậy Quá Khổ", "Needlessly Large Rod", "+10 SMPT", "tft_item_needlesslylargerod"),
    "TearOfTheGoddess": ("Nước Mắt Nữ Thần", "Tear of the Goddess", "+1 Hồi Năng Lượng", "tft_item_tearofthegoddess"),
    "ChainVest": ("Giáp Lưới", "Chain Vest", "+20 Giáp", "tft_item_chainvest"),
    "NegatronCloak": ("Áo Choàng Bạc", "Negatron Cloak", "+20 Kháng Phép", "tft_item_negatroncloak"),
    "GiantsBelt": ("Đai Khổng Lồ", "Giant's Belt", "+150 Máu", "tft_item_giantsbelt"),
    "SparringGloves": ("Găng Đấu Tập", "Sparring Gloves", "+20% Tỉ Lệ Chí Mạng", "tft_item_sparringgloves"),
    "Spatula": ("Siêu Xẻng", "Spatula", "Ghép ra Ấn tộc", "tft_item_spatula"),
    "FryingPan": ("Chảo Vàng", "Frying Pan", "Ghép ra Ấn hệ", "tft_item_fryingpan"),
}
ITEMS = {  # hoàn chỉnh
    "Deathblade": ("Kiếm Tử Thần", "Deathblade", "BFSword+BFSword", "+55% SMCK, +10% sát thương", "Đồ SMCK thuần mạnh nhất.", "AD", "tft_item_deathblade"),
    "GiantSlayer": ("Diệt Khổng Lồ", "Giant Slayer", "BFSword+RecurveBow", "+15% SMCK, +15 SMPT, +15% TĐĐ", "+15% Khuếch Đại Sát Thương lên tướng Đỡ Đòn.", "AD", "tft_item_madredsbloodrazor"),
    "HextechGunblade": ("Kiếm Súng Hextech", "Hextech Gunblade", "BFSword+NeedlesslyLargeRod", "+20% SMCK, +20 SMPT, +1 Hồi NL, 18% Hút Máu", "Hồi máu cho đồng minh yếu nhất bằng 20% sát thương gây ra.", "AP", "tft_item_hextechgunblade"),
    "SpearOfShojin": ("Ngọn Giáo Shojin", "Spear of Shojin", "BFSword+TearOfTheGoddess", "+15% SMCK, +15 SMPT, +1 Hồi NL", "Mỗi đòn đánh hồi 5 Năng Lượng.", "AP", "tft_item_spearofshojin"),
    "EdgeOfNight": ("Áo Choàng Bóng Tối", "Edge of Night", "BFSword+ChainVest", "+10% SMCK, +10 SMPT, +15% TĐĐ, +20 Giáp", "Ở 60% Máu: tàng hình chốc lát, xoá hiệu ứng xấu, hồi 20% Máu đã mất.", "AD", "tft_item_guardianangel"),
    "Bloodthirster": ("Huyết Kiếm", "Bloodthirster", "BFSword+NegatronCloak", "+15% SMCK, +15 SMPT, +20 Kháng Phép, 20% Hút Máu", "Ở 40% Máu: lá chắn 25% Máu tối đa trong 5 giây.", "AD", "tft_item_bloodthirster"),
    "SteraksGage": ("Móng Vuốt Sterak", "Sterak's Gage", "BFSword+GiantsBelt", "+45% SMCK, +300 Máu", "Ở 60% Máu: lá chắn 40% Máu tối đa, giảm dần trong 4 giây.", "AD", "tft_item_steraksgage"),
    "InfinityEdge": ("Vô Cực Kiếm", "Infinity Edge", "BFSword+SparringGloves", "+35% SMCK, +35% Chí Mạng", "Nhận Chuẩn Xác (kỹ năng có thể chí mạng).", "AD", "tft_item_infinityedge"),
    "RedBuff": ("Bùa Đỏ", "Red Buff", "RecurveBow+RecurveBow", "+45% TĐĐ, +6% sát thương", "Đòn đánh và kỹ năng gây Thiêu Đốt 1% + Vết Thương Sâu 33% trong 5 giây.", "AD", "tft_item_rapidfirecannon"),
    "GuinsoosRageblade": ("Cuồng Đao Guinsoo", "Guinsoo's Rageblade", "RecurveBow+NeedlesslyLargeRod", "+10 SMPT, +10% TĐĐ", "+7% Tốc Độ Đánh cộng dồn mỗi giây.", "AD/AP", "tft_item_guinsoosrageblade"),
    "VoidStaff": ("Trượng Hư Vô", "Void Staff", "RecurveBow+TearOfTheGoddess", "+35 SMPT, +15% TĐĐ, +1 Hồi NL", "Đòn đánh và kỹ năng giảm 30% Kháng Phép mục tiêu (Cào Xé).", "AP", "tft_item_voidstaff"),
    "TitansResolve": ("Quyền Năng Khổng Lồ", "Titan's Resolve", "RecurveBow+ChainVest", "+10% TĐĐ, +20 Giáp", "Đánh/bị đánh cộng dồn 2% SMCK & SMPT (tối đa 25); đủ cộng dồn: +10% sát thương, miễn khống chế.", "AD", "tft_item_titansresolve"),
    "KrakensFury": ("Thịnh Nộ Thủy Quái", "Kraken's Fury", "RecurveBow+NegatronCloak", "+10% SMCK, +10% TĐĐ, +20 Kháng Phép", "Mỗi đòn đánh +3.5% SMCK (tối đa 15 lần), đủ 15 lần +15% TĐĐ.", "AD", "tft_item_krakenslayer"),
    "NashorsTooth": ("Nanh Nashor", "Nashor's Tooth", "RecurveBow+GiantsBelt", "+15 SMPT, +10% TĐĐ, +150 Máu, +20% Chí Mạng", "Mỗi đòn đánh hồi 2 Năng Lượng (4 nếu chí mạng).", "AP", "tft_item_leviathan"),
    "LastWhisper": ("Cung Xanh", "Last Whisper", "RecurveBow+SparringGloves", "+15% SMCK, +20% TĐĐ, +20% Chí Mạng", "Giảm 30% Giáp mục tiêu trong 3 giây (Phân Tách).", "AD", "tft_item_lastwhisper"),
    "RabadonsDeathcap": ("Mũ Phù Thủy Rabadon", "Rabadon's Deathcap", "NeedlesslyLargeRod+NeedlesslyLargeRod", "+55 SMPT, +15% sát thương", "Đồ SMPT thuần mạnh nhất.", "AP", "tft_item_rabadonsdeathcap"),
    "ArchangelsStaff": ("Quyền Trượng Thiên Thần", "Archangel's Staff", "NeedlesslyLargeRod+TearOfTheGoddess", "+30 SMPT, +1 Hồi NL", "+20 SMPT mỗi 5 giây giao tranh.", "AP", "tft_item_archangelsstaff"),
    "Crownguard": ("Vương Miện Hoàng Gia", "Crownguard", "NeedlesslyLargeRod+ChainVest", "+20 SMPT, +20 Giáp, +100 Máu", "Đầu giao tranh: lá chắn 25% Máu trong 8 giây; hết lá chắn +25 SMPT.", "AP/Tank", "tft_item_crownguard"),
    "IonicSpark": ("Nỏ Sét", "Ionic Spark", "NeedlesslyLargeRod+NegatronCloak", "+15 SMPT, +250 Máu, +35 Kháng Phép", "Giảm 30% Kháng Phép địch trong 2 ô; địch tung chiêu thì bị giật sét.", "Tank", "tft_item_ionicspark"),
    "Morellonomicon": ("Quỷ Thư Morello", "Morellonomicon", "NeedlesslyLargeRod+GiantsBelt", "+20 SMPT, +150 Máu, +1 Hồi NL", "Thiêu Đốt 1% + Vết Thương Sâu 33% trong 10 giây.", "AP", "tft_item_morellonomicon"),
    "JeweledGauntlet": ("Găng Bảo Thạch", "Jeweled Gauntlet", "NeedlesslyLargeRod+SparringGloves", "+35 SMPT, +35% Chí Mạng", "Nhận Chuẩn Xác (kỹ năng có thể chí mạng).", "AP", "tft_item_jeweledgauntlet"),
    "BlueBuff": ("Bùa Xanh", "Blue Buff", "TearOfTheGoddess+TearOfTheGoddess", "+15% SMCK, +15 SMPT, +5 Hồi NL", "+10% SMCK và SMPT từ mọi nguồn.", "AP", "tft_item_bluebuff"),
    "ProtectorsVow": ("Lời Thề Hộ Vệ", "Protector's Vow", "TearOfTheGoddess+ChainVest", "+25 Giáp, +25 Kháng Phép, +1 Hồi NL", "Đầu giao tranh +20 Năng Lượng; ở 40% Máu: +15 Năng Lượng và lá chắn 20% Máu.", "Tank", "tft_item_frozenheart"),
    "AdaptiveHelm": ("Mũ Thích Nghi", "Adaptive Helm", "TearOfTheGoddess+NegatronCloak", "+20 Kháng Phép, +3 Hồi NL", "+15% Năng Lượng nhận được. Đỡ đòn: +30 Giáp/Kháng Phép; vai trò khác: +10% SMCK/SMPT.", "Tank/AP", "tft_item_adaptivehelm"),
    "SpiritVisage": ("Giáp Tâm Linh", "Spirit Visage", "TearOfTheGoddess+GiantsBelt", "+300 Máu, +2 Hồi NL", "Hồi 2% Máu đã mất mỗi giây.", "Tank", "tft_item_spiritvisagerr"),
    "HandOfJustice": ("Bàn Tay Công Lý", "Hand Of Justice", "TearOfTheGoddess+SparringGloves", "+15% SMCK, +15 SMPT, +20% Chí Mạng, 12% Hút Máu", "Trên 50% Máu: gấp đôi SMCK/SMPT; dưới 50%: gấp đôi Hút Máu.", "AD/AP", "tft_item_unstableconcoction"),
    "BrambleVest": ("Áo Choàng Gai", "Bramble Vest", "ChainVest+ChainVest", "+50 Giáp, +6% Máu", "Giảm 5% sát thương đòn đánh; bị đánh thì gây 100 sát thương phép xung quanh.", "Tank", "tft_item_bramblevest"),
    "GargoyleStoneplate": ("Thú Tượng Thạch Giáp", "Gargoyle Stoneplate", "ChainVest+NegatronCloak", "+25 Giáp, +25 Kháng Phép, +100 Máu", "+10 Giáp và Kháng Phép cho mỗi kẻ địch đang nhắm vào.", "Tank", "tft_item_gargoylestoneplate"),
    "SunfireCape": ("Áo Choàng Lửa", "Sunfire Cape", "ChainVest+GiantsBelt", "+20 Giáp, +150 Máu, +8% Máu", "Mỗi 2 giây Thiêu Đốt + Vết Thương Sâu 1 kẻ địch trong 2 ô.", "Tank", "tft_item_redbuff"),
    "SteadfastHeart": ("Trái Tim Kiên Định", "Steadfast Heart", "ChainVest+SparringGloves", "+20 Giáp, +250 Máu, +20% Chí Mạng", "15% Chống Chịu khi trên 50% Máu (5% khi dưới).", "Tank", "tft_item_nightharvester"),
    "DragonsClaw": ("Vuốt Rồng", "Dragon's Claw", "NegatronCloak+NegatronCloak", "+60 Kháng Phép, +6% Máu", "Mỗi 2 giây hồi 2.5% Máu tối đa.", "Tank", "tft_item_dragonsclaw"),
    "Evenshroud": ("Giáp Vai Nguyệt Thần", "Evenshroud", "NegatronCloak+GiantsBelt", "+20 Kháng Phép, +250 Máu", "Giảm 30% Giáp địch trong 2 ô; +15 Giáp/Kháng Phép 15 giây đầu.", "Tank", "tft_item_spectralgauntlet"),
    "Quicksilver": ("Áo Choàng Thủy Ngân", "Quicksilver", "SparringGloves+NegatronCloak", "+15% TĐĐ, +20% Chí Mạng, +20 Kháng Phép", "Miễn khống chế 18 giây đầu; +3% TĐĐ mỗi giây.", "AD", "tft_item_quicksilver"),
    "WarmogsArmor": ("Giáp Máu Warmog", "Warmog's Armor", "GiantsBelt+GiantsBelt", "+500 Máu, +18% Máu", "Đồ Máu thuần.", "Tank", "tft_item_warmogsarmor"),
    "StrikersFlail": ("Chùy Đoản Côn", "Striker's Flail", "GiantsBelt+SparringGloves", "+10% TĐĐ, +150 Máu, +20% Chí Mạng", "Chí mạng cho +5% sát thương trong 5 giây (cộng dồn 4).", "AD/AP", "tft_item_powergauntlet"),
    "ThiefsGloves": ("Găng Đạo Tặc", "Thief's Gloves", "SparringGloves+SparringGloves", "+20% Chí Mạng, +150 Máu", "Mỗi vòng mang 2 trang bị ngẫu nhiên (chiếm 3 ô đồ).", "Đặc biệt", "tft_item_thiefsgloves"),
    "TacticiansCrown": ("Vương Miện Chiến Thuật", "Tactician's Crown", "Spatula+Spatula", "+1 số tướng tối đa", "10% cơ hội rơi 1 vàng khi thắng giao tranh.", "Đặc biệt", "tft_item_forceofnature"),
    "TacticiansCape": ("Áo Choàng Chiến Thuật", "Tactician's Cape", "Spatula+FryingPan", "+1 số tướng tối đa", "10% cơ hội rơi 1 vàng sau 10 giây giao tranh.", "Đặc biệt", "tft_item_tacticiansring"),
    "TacticiansShield": ("Lá Chắn Chiến Thuật", "Tactician's Shield", "FryingPan+FryingPan", "+1 số tướng tối đa", "10% cơ hội rơi 1 vàng khi người mang tử trận.", "Đặc biệt", "tft_item_tacticiansscepter"),
}
# Ấn: khoá trait → công thức ("" = không ghép được, chỉ có từ lõi / phần thưởng)
EMBLEMS = {
    "Fae": "Spatula+BFSword", "Inferno": "Spatula+RecurveBow", "Blossom": "Spatula+NeedlesslyLargeRod",
    "Lunar": "Spatula+TearOfTheGoddess", "Elderwood": "Spatula+ChainVest", "Sprykin": "Spatula+NegatronCloak",
    "Blackthorn": "Spatula+GiantsBelt", "Primal": "Spatula+SparringGloves",
    "Hunter": "FryingPan+BFSword", "Rapidfire": "FryingPan+RecurveBow", "Spellweaver": "FryingPan+NeedlesslyLargeRod",
    "Invoker": "FryingPan+TearOfTheGoddess", "Vanguard": "FryingPan+ChainVest", "Slayer": "FryingPan+NegatronCloak",
    "Brawler": "FryingPan+GiantsBelt", "Executioner": "FryingPan+SparringGloves",
    "Coven": "", "Defender": "", "FloraFatalis": "", "Juggernaut": "",
}
EMBLEM_ICON = {"Slayer": "ravager"}

# --------------------------------------------------------------------------- tướng
CHAMP_KEY_FIX = {"GnarSmall": "Gnar", "Lux_Base": "Lux"}


def ckey(api: str) -> str:
    k = re.sub(r"^DA_18_|^DA_|18|_AD$|_AP$", "", api)
    k = re.sub(r"_AD$|_AP$", "", k)
    return CHAMP_KEY_FIX.get(k, k)


def cdn(path: str) -> str:
    return CDN + path.lower().replace(".tex", ".png")


def build_champs():
    out = []
    for line in (RAW / "champs.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        api, vi, en, cost, tvi, ten, skill, rng, icon = line.split("\t")
        traits = [VI2KEY[t] for t in tvi.split(",")]
        r = int(rng)
        out.append({
            "id": ckey(api), "api": api, "ten": vi, "ten_en": en, "gia": int(cost), "toc_he": traits,
            "ky_nang": skill, "tam_danh": r,
            "vi_tri": "Tiền tuyến" if r <= 1 else ("Hậu tuyến" if r >= 4 else "Giữa"),
            "anh": cdn(icon),
        })
    return out


def build_traits(champs):
    out = []
    for k, (vi, loai, mota) in TRAITS.items():
        members = [c["id"] for c in champs if k in c["toc_he"]]
        icon = TRAIT_ICON.get(k, k.lower())
        out.append({"id": k, "ten": vi, "loai": loai, "moc": TRAIT_MINS.get(k, [1]), "mo_ta": mota,
                    "tuong": members, "anh": cdn(f"assets/ux/traiticons/trait_icon_18_{icon}.tex")})
    return out


def build_items():
    comps = [{"id": k, "ten": v[0], "ten_en": v[1], "chi_so": v[2],
              "anh": cdn(f"assets/maps/tft/icons/items/hexcore/{v[3]}.tex")} for k, v in COMP.items()]
    full = [{"id": k, "ten": v[0], "ten_en": v[1], "cong_thuc": v[2].split("+"), "chi_so": v[3], "tac_dung": v[4],
             "nhom": v[5], "anh": cdn(f"assets/maps/tft/icons/items/hexcore/{v[6]}.tex")} for k, v in ITEMS.items()]
    emb = []
    for t, rec in EMBLEMS.items():
        vi = TRAITS[t][0]
        icon = EMBLEM_ICON.get(t, t.lower().replace("florafatalis", "florafatalis"))
        emb.append({"id": f"Emblem_{t}", "ten": f"Ấn {vi}", "toc_he": t, "cong_thuc": rec.split("+") if rec else [],
                    "tac_dung": f"Người mang tính là tướng {vi}." + ("" if rec else " Không ghép được — chỉ có từ lõi hoặc phần thưởng."),
                    "anh": cdn(f"assets/maps/particles/tft/item_icons/traits/spatula/set18/tft18_emblem_{icon}.tex")})
    return {"thanh_phan": comps, "hoan_chinh": full, "an": emb}


# --------------------------------------------------------------------------- lõi
AUG_VI_EXTRA = {  # lõi có trong danh sách MetaTFT nhưng Community Dragon thiếu tên Việt → tên tạm dịch
    "DA_CalculatedLoss": ("Thua Có Tính Toán", "Calculated Loss", "Sau khi thua, nhận 2 vàng và 1 lượt đổi miễn phí."),
    "DA_StarringUp": ("Lên Sao Thăng Cấp", "Starring Up", "Sau khi nâng đủ số tướng lên 3 sao, cấp người chơi được đặt lên mốc cao. Nhận lượt đổi ngay và mỗi vòng."),
    "DA_18_FloraFatalisAugmentPlus": ("Thực Vật Hấp Thụ+", "Consuming Flora+", "Nhận 1 Ấn Thực Vật, tướng mang ấn tăng hiệu ứng Thực Vật. Nhận thêm vàng."),
    "DA_18_PrimalAugment_Sivir": ("Quái Thú Bên Trong (Sivir)", "Beast Within", "Nguyên Sinh cho thêm một Phước Lành. Nhận 1 Vi ngay và 1 Sivir sau vài vòng."),
    "DA_18_PrimalAugmentPlus_Sivir": ("Quái Thú Bên Trong+ (Sivir)", "Beast Within+", "Nguyên Sinh cho thêm một Phước Lành. Nhận 1 Vi và 1 Sivir."),
    "DA_TonsOfStatsII": ("Cộng Mệt Nghỉ! II", "TONS of Stats!", "Cả đội nhận thêm Máu, SMCK, SMPT, Giáp, Kháng Phép, Tốc Độ Đánh và Năng Lượng (nhiều hơn bản I)."),
    "DA_DoubleTrouble": ("Cặp Đôi Hoàn Cảnh", "Double Trouble", "Ra sân đúng 2 bản sao của 1 tướng: cả hai nhận thêm SMCK, SMPT, Giáp, Kháng Phép."),
    "DA_18_RivalsAugmentPlus": ("Không Đối Thủ+", "Unrivaled+", "Ra sân Rengar và Kha'Zix cùng lúc không bị phạt, cường hóa lẫn nhau. Nhận 1 Rengar và 1 Kha'Zix."),
    "DA_NestingDolls": ("Búp Bê Xây Tổ", "Nesting Dolls", "Tướng bị hạ tạo bản sao thấp hơn 1 sao. Nhận lượt đổi miễn phí."),
    "DA_NestingDollsPlusPlus": ("Búp Bê Xây Tổ++", "Nesting Dolls++", "Tướng bị hạ tạo bản sao thấp hơn 1 sao. Nhận nhiều lượt đổi miễn phí."),
    "DA_GainGold": ("Nhận 21 Vàng", "Gain 21 Gold", "Nhận 21 vàng."),
}
# nhóm lõi (để lọc và để trợ lý chấm điểm)
AUG_GROUP_RULES = [
    ("Tộc/Hệ", r"TraitAugment|PrimalAugment|RivalsAugment|SprykinAugment|FloraFatalisAugment|LuxAugment|Blackthorn"),
    ("Ấn", r"BranchingOut|SpreadingRoots|TraitTree|TacticiansKitchen|TraitLadder|Flexible|HardCommit|WeStickTogether|LegionOfThrees|BacklineBlueprint|FrontlineFoundation"),
    ("Trang bị", r"GrabBag|Forge|Anvil|Thieves|Gloves|Smith|Overflow|Buckles|Bows|CarveAPath|FlowingTears|Component|Replication|Salvage|Pandoras?Items|Buried|IronAssets|BigGrabBag|DuoQueue|Caps|Blades|Staff|Protection|HeartOfSteel|Retribution|OneBuffTwoBuff|Radiant|Shimmerscale|URF|Urfs|Coronation|Min_Max|Exclusive|CryMeARiver|Cybernetic|PromisedProtection|SpiritOfRedemption|SoloPlate|TheGoldenDragon|BaronsLair|CookingPot|SweetTreats|WovenMagic|BonusGift"),
    ("Kinh tế", r"Gold|Loan|Hustler|Invested|Money|HedgeFund|Capital|Investment|Kingslayer|CalledShot|QuickStreaks|GoingLong|Egg|Gamble|LoadedDice|FeelingLucky|LateGameSpecialist|CalculatedLoss|HardBargain|Malicious|YoungAndWild|GoodForSomething|Expedition|FutureFocused|WispRebate"),
    ("Cấp & Đổi tướng", r"Growth|LevelUp|Epoch|Rolldown|Rolling|Patience|PatientStudy|ShoppingSpree|CommerceCore|TradeSector|PrismaticTicket|MaxBuild|SilverSpoon|CognitiveTax|ClearMind|Cluttered|TimeSkip|Upward|LateGameScaling|Starring"),
    ("Tướng", r"Booster|ChampDelivery|Caretakers|KickStart|Missed|SliceOfLife|WorththeWait|Birthday|BuildABud|Heroic|Subscription|Luxury|OneTwoFive|OnesTwos|TeamBuilding|PandorasBench|Pilfer|Recombobulator|Dummify|ConstructACompanion|ForgeAFriend|GildedSteel|FOURcing|WeightTheWorth|Warpath|CognitiveOverload|NestingDolls|TheTower"),
]


def aug_group(api: str) -> str:
    for g, pat in AUG_GROUP_RULES:
        if re.search(pat, api):
            return g
    return "Chiến đấu"


def build_augments():
    vi = {}
    for f in ("augments_1.tsv", "augments_2.tsv"):
        for line in (RAW / f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                api, name, en, tier, desc = line.split("\t")[:5]
                vi[api] = (name, en, desc)
    vi.update(AUG_VI_EXTRA)
    tiers = {}
    for line in (RAW / "augment_tiers_metatft.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            lab, ids = line.split("\t")
            for i in ids.split(","):
                tiers[i] = lab
    rar = {}
    for part in (RAW / "augment_rarity_metatft.txt").read_text(encoding="utf-8").strip().split(","):
        k, r, rounds = part.split(":")
        rar["DA_" + k] = (int(r), [x for x in rounds.split("/") if x])
    icons = {}
    for part in (RAW / "augment_icons.txt").read_text(encoding="utf-8").strip().split(","):
        k, v = part.split("=")
        icons["DA_" + k] = cdn(f"assets/maps/tft/icons/augments/{v}.tex")
    BAC = {1: "Bạc", 2: "Vàng", 3: "Kim cương"}
    out = []
    for api, lab in tiers.items():
        if api not in vi:
            continue
        r, rounds = rar.get(api, (2, []))
        name, en, desc = vi[api]
        out.append({"id": api, "ten": name, "ten_en": en, "bac": BAC[r], "bac_so": r, "xep_hang": lab,
                    "vong": rounds, "nhom": aug_group(api), "mo_ta": desc, "anh": icons.get(api, "")})
    order = {"S": 0, "A": 1, "B": 2, "C": 3}
    out.sort(key=lambda a: (a["bac_so"], order[a["xep_hang"]], a["ten"]))
    return out


# --------------------------------------------------------------------------- đội hình
LEVEL_TEXT = {
    "lvl 5": ("Reroll cấp 5", "reroll", 5),
    "lvl 6": ("Reroll cấp 6", "reroll", 6),
    "lvl 7": ("Reroll cấp 7", "reroll", 7),
    "Fast 8": ("Lên nhanh cấp 8", "fast8", 8),
    "Fast 9": ("Lên nhanh cấp 9", "fast9", 9),
    "Standard": ("Chuẩn (cấp 8 ở 4-2)", "standard", 8),
}
TANK_ITEMS = {k for k, v in ITEMS.items() if v[5].startswith("Tank")}


def tier_of(avg: float) -> str:
    if avg <= 4.32:
        return "S"
    if avg <= 4.50:
        return "A"
    if avg <= 4.75:
        return "B"
    return "C"


def plan_text(kieu: str, cap: int, carries: list[str], tanks: list[str]) -> dict:
    c = " và ".join(carries[:2]) if carries else "chủ lực"
    t = " và ".join(tanks[:2]) if tanks else "tướng đỡ đòn"
    if kieu == "reroll":
        tien = {5: "1 vàng", 6: "2 vàng", 7: "3 vàng"}[cap]
        return {
            "dau": f"Giữ máu bằng tướng mạnh nhất đang có, ưu tiên mua {c}. Ghép sớm đồ cho {c}.",
            "giua": f"Lên cấp {cap} rồi roll chậm (giữ trên 50 vàng, chỉ tiêu phần lãi) tới khi {c} lên 3 sao — đây là tướng {tien}.",
            "cuoi": f"Xong 3 sao thì lên cấp {cap + 1}–8, thêm tướng 4 vàng hợp tộc/hệ, nâng {t} lên 2 sao.",
            "moc": [f"2-1: cấp 4", f"2-5 hoặc 3-1: cấp {min(cap, 5)}" if cap > 5 else "2-1 → 3-2: roll chậm ở cấp 5",
                    f"3-2: cấp {cap}, bắt đầu roll chậm" if cap > 5 else "3-2: tiếp tục roll, chưa lên cấp",
                    f"Khi {carries[0] if carries else 'chủ lực'} 3 sao: lên cấp {cap + 1}", "4-2 → 5-1: cấp 8"],
        }
    if kieu == "fast9":
        return {
            "dau": f"Chơi đội mạnh nhất đang có để giữ máu, tích vàng lên mốc 50. Gom đồ cho {c}.",
            "giua": "Lên cấp 7 ở 3-2, cấp 8 ở 4-1 hoặc 4-2, chỉ roll vừa đủ để giữ máu.",
            "cuoi": f"Lên cấp 9 ở 5-1/5-2 rồi roll tìm tướng 5 vàng ({c}). {t} đứng trước chịu đòn.",
            "moc": ["2-1: cấp 4", "2-5: cấp 5", "3-2: cấp 6–7", "4-1: cấp 8", "5-1 hoặc 5-2: cấp 9, roll tìm tướng 5 vàng"],
        }
    if kieu == "standard":
        return {
            "dau": f"Đánh chuỗi thắng hoặc chuỗi thua rõ ràng; gom đồ cho {c}.",
            "giua": "Cấp 6 ở 3-2, cấp 7 ở 4-1, roll vừa đủ giữ máu.",
            "cuoi": f"Cấp 8 ở 4-2 rồi roll tìm {c} 2 sao và tướng 4 vàng.",
            "moc": ["2-1: cấp 4", "2-5: cấp 5", "3-2: cấp 6", "4-1: cấp 7", "4-2: cấp 8, roll mạnh"],
        }
    # fast8
    return {
        "dau": f"Chơi đội mạnh nhất đang có, gom đồ cho {c} ngay từ đầu.",
        "giua": "Cấp 6 ở 3-2, cấp 7 ở 3-5 hoặc 4-1, giữ vàng gần 50.",
        "cuoi": f"Lên cấp 8 ở 4-1/4-2 rồi roll mạnh tìm {c} 2 sao. Đủ mạnh thì lên 9 ở 5-1 thêm tướng 5 vàng.",
        "moc": ["2-1: cấp 4", "2-5: cấp 5", "3-2: cấp 6", "4-1: cấp 7–8", "4-2: cấp 8, all-in roll tìm chủ lực 2 sao"],
    }


def build_comps(champs):
    cmap = {c["id"]: c for c in champs}
    cmap["Gnar"] = cmap.get("Gnar")
    rows = (RAW / "comps_metatft.tsv").read_text(encoding="utf-8").splitlines()[1:]
    aug_ids = set()
    comps = []
    for line in rows:
        if not line.strip():
            continue
        cl, name, lvl, count, avg, t4, win, units, traits, builds = line.split("\t")
        units = [CHAMP_KEY_FIX.get(u, u) for u in units.split(",")]
        units = [u for u in units if u in cmap]
        tr = []
        for t in traits.split(","):
            k, _, n = t.rpartition("_")
            if k in TRAITS:
                tr.append({"id": k, "ten": TRAITS[k][0], "cap_do": int(n)})
        carries, tanks, emblems = [], [], []
        for b in builds.split(" | "):
            u, items = b.split(":")
            u = CHAMP_KEY_FIX.get(u, u)
            its = items.split("+")
            emb = [i.replace("18_Emblem", "Emblem_") for i in its if i.startswith("18_Emblem")]
            emblems += emb
            its = [i.replace("18_Emblem", "Emblem_") for i in its]
            role = "do_don" if sum(i in TANK_ITEMS for i in its) >= 2 else "chu_luc"
            if u not in cmap:
                continue
            (tanks if role == "do_don" else carries).append({"tuong": u, "do": its})
            if u not in units:
                units.append(u)
        kieu_ten, kieu, cap = LEVEL_TEXT.get(lvl, ("Lên nhanh cấp 8", "fast8", 8))
        parts = name.split("/")
        trait_key = parts[0]
        carry_names = [cmap[c["tuong"]]["ten"] for c in carries]
        tank_names = [cmap[c["tuong"]]["ten"] for c in tanks]
        named = [cmap[CHAMP_KEY_FIX.get(p, p)]["ten"] for p in parts[1:] if CHAMP_KEY_FIX.get(p, p) in cmap]
        head = " & ".join(named[:2] or carry_names[:2])
        ten = f"{head} {TRAITS.get(trait_key, (trait_key,))[0]}"
        a = float(avg)
        comps.append({
            "id": f"c{cl}", "ten": ten, "hang": tier_of(a), "kieu": kieu, "kieu_ten": kieu_ten, "cap_muc_tieu": cap,
            "tuong": units, "chu_luc": carries, "do_don": tanks, "toc_he": tr,
            "an_nen_ghep": sorted(set(emblems)),
            "so_lieu": {"so_tran": int(count), "hang_tb": a, "top4": float(t4), "top1": float(win),
                        "nguon": "MetaTFT", "pham_vi": "Bạch Kim trở lên · 3 ngày gần nhất · bản 18.3b"},
            "cach_choi": plan_text(kieu, cap, carry_names, tank_names),
        })
    comps.sort(key=lambda c: c["so_lieu"]["hang_tb"])
    return comps


def suggest_augments(comps, augs):
    """Lõi hợp theo LUẬT (không phải thống kê): lõi tộc/hệ khớp + lõi theo kiểu chơi + lõi đồ theo chủ lực."""
    by_id = {a["id"]: a for a in augs}
    trait_aug = {
        "Blackthorn": ["DA_BlackthornTraitAugment"], "Blossom": ["DA_18_BlossomTraitAugment", "DA_18_ResidualMagicPlus"],
        "Coven": ["DA_18_CovenTraitAugment_LootToAP", "DA_18_CovenTraitAugment"], "Elderwood": ["DA_18_ElderwoodTraitAugment"],
        "Fae": ["DA_18_FaeTraitAugment"], "Lunar": ["DA_18_LunarTraitAugment"], "Riftbeast": ["DA_18_RiftbeastTraitAugment"],
        "Solar": ["DA_18_SolarTraitAugment"], "Sprykin": ["DA_18_SprykinAugment"], "Rival": ["DA_18_RivalsAugment"],
        "FloraFatalis": ["DA_18_FloraFatalisAugmentPlus", "DA_18_FloraFatalisAugment"],
    }
    kieu_aug = {
        "reroll": ["DA_PandorasBench", "DA_RollingForDays", "DA_ChampDeliveryPlus", "DA_PatienceIsAVirtue", "DA_WorththeWait", "DA_CalculatedLoss"],
        "fast8": ["DA_ExplosiveGrowth", "DA_EpicRolldown", "DA_LevelUp", "DA_MaxBuild", "DA_TradeSector"],
        "fast9": ["DA_ExplosiveGrowth", "DA_LateGameSpecialist", "DA_LateGameScaling", "DA_LevelUp", "DA_GildedSteel"],
        "standard": ["DA_EpicRolldown", "DA_ExplosiveGrowth", "DA_TradeSector"],
    }
    for c in comps:
        picks = []
        for t in c["toc_he"]:
            if t["id"] == "Primal":
                picks += [f"DA_18_PrimalAugment_{u}" for u in ("Nidalee", "Sivir") if u in c["tuong"]]
            picks += trait_aug.get(t["id"], [])
        if c["an_nen_ghep"]:
            picks += ["DA_SpreadingRoots", "DA_18_BranchingOut"]
        picks += kieu_aug[c["kieu"]]
        carry_items = [i for cc in c["chu_luc"] for i in cc["do"]]
        if sum(ITEMS.get(i, ("",) * 6)[5].startswith("AP") for i in carry_items) >= 2:
            picks += ["DA_Staffsmith", "DA_SeraphimsStaff", "DA_DeadlierCaps"]
        else:
            picks += ["DA_Swordsmith", "DA_SwordOverflow"]
        picks += ["DA_PortableForge", "DA_BaronsLair"]
        seen, res = set(), []
        for p in picks:
            if p in by_id and p not in seen:
                seen.add(p)
                res.append(p)
        c["loi_hop"] = res[:8]


def main():
    DATA.mkdir(exist_ok=True)
    champs = build_champs()
    traits = build_traits(champs)
    items = build_items()
    augs = build_augments()
    comps = build_comps(champs)
    suggest_augments(comps, augs)
    meta = {
        **GAME, "ngay_cap_nhat": NGAY_LAY,
        "nguon": [
            {"ten": "Community Dragon (dữ liệu game Riot, bản tiếng Việt)", "url": "https://raw.communitydragon.org/latest/cdragon/tft/vi_vn.json"},
            {"ten": "MetaTFT – thống kê đội hình (Bạch Kim+, 3 ngày, bản 18.3b)", "url": "https://www.metatft.com/comps"},
            {"ten": "MetaTFT – bảng xếp hạng lõi", "url": "https://www.metatft.com/augments"},
            {"ten": "SeeMeta – tỉ lệ cửa hàng Mùa 18", "url": "https://seemeta.com/en/tft/set-18/odds"},
        ],
        "ghi_chu": "Số liệu đội hình là thống kê thật từ MetaTFT. Xếp hạng lõi là bảng chấm của chuyên gia MetaTFT (không phải tỉ lệ thắng). Lõi hợp đội do luật của ĐTCL Coach gợi ý.",
    }
    files = {"tuong.json": champs, "toc_he.json": traits, "trang_bi.json": items, "loi.json": augs,
             "metatft_doi_hinh.json": comps, "meta.json": meta}
    for name, obj in files.items():
        (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print({k: (len(v) if isinstance(v, list) else "ok") for k, v in files.items()})


if __name__ == "__main__":
    main()
