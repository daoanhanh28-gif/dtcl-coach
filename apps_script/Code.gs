// ĐTCL Coach v1.0 (2026-10-06) — Database Google Sheets cho nhật ký ván đấu
/**
 * Database miễn phí trên Google Sheets
 *
 * CÁCH DÙNG: tạo 1 Google Sheet trống → Tiện ích mở rộng → Apps Script →
 * dán toàn bộ file này → chọn hàm caiDat → Chạy (cấp quyền) → xem Nhật ký thực thi
 * để lấy TOKEN (tự copy, không gửi cho ai) → Triển khai → Tùy chọn triển khai mới → Ứng dụng web
 * (Thực thi với tư cách: Tôi · Ai có quyền truy cập: Bất kỳ ai) → copy URL kết thúc bằng /exec.
 * TOKEN không nằm trong code: được tạo ngẫu nhiên và cất trong Script Properties.
 *
 * Web app nhận:
 *   POST {token, action:"append", sheet, row:{...}}  → ghi 1 dòng (tự tạo sheet/cột)
 *   GET  ?token=...&action=read&sheet=...             → trả toàn bộ dòng dạng JSON
 */

function token_() {
  return PropertiesService.getScriptProperties().getProperty('TOKEN');
}
const ALLOWED_SHEETS = ['NhatKy', 'LuyenTap'];

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (!token_() || body.token !== token_()) return json_({ ok: false, error: 'sai token' });
    if (body.action !== 'append') return json_({ ok: false, error: 'action không hợp lệ' });
    if (ALLOWED_SHEETS.indexOf(body.sheet) === -1) return json_({ ok: false, error: 'sheet không hợp lệ' });
    const lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      appendRow_(body.sheet, body.row || {});
    } finally {
      lock.releaseLock();
    }
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function doGet(e) {
  const p = e.parameter || {};
  if (!token_() || p.token !== token_()) return json_({ ok: false, error: 'sai token' });
  if (p.action !== 'read' || ALLOWED_SHEETS.indexOf(p.sheet) === -1) {
    return json_({ ok: false, error: 'yêu cầu không hợp lệ' });
  }
  const sh = SpreadsheetApp.getActive().getSheetByName(p.sheet);
  if (!sh || sh.getLastRow() < 2) return json_({ ok: true, rows: [] });
  const values = sh.getDataRange().getValues();
  const headers = values.shift();
  const rows = values.map(function (r) {
    const o = {};
    headers.forEach(function (h, i) {
      o[h] = r[i] instanceof Date
        ? Utilities.formatDate(r[i], 'Asia/Ho_Chi_Minh', 'yyyy-MM-dd HH:mm:ss')
        : r[i];
    });
    return o;
  });
  return json_({ ok: true, rows: rows });
}

function appendRow_(sheetName, row) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(sheetName);
  if (!sh) sh = ss.insertSheet(sheetName);
  let headers = sh.getLastColumn() > 0
    ? sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0]
    : [];
  Object.keys(row).forEach(function (k) {
    if (headers.indexOf(k) === -1) headers.push(k);
  });
  sh.getRange(1, 1, 1, headers.length).setValues([headers])
    .setFontWeight('bold').setBackground('#14110B').setFontColor('#C8A24A');
  sh.setFrozenRows(1);
  const line = headers.map(function (h) {
    const v = row[h];
    return v === undefined || v === null ? '' : v;
  });
  sh.appendRow(line);
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * CHẠY 1 LẦN: tạo TOKEN ngẫu nhiên (nếu chưa có), tạo sẵn các sheet,
 * rồi in TOKEN ra Nhật ký thực thi để chủ web tự copy vào Secrets của Streamlit (SHEETS_TOKEN).
 */
function caiDat() {
  const props = PropertiesService.getScriptProperties();
  let t = props.getProperty('TOKEN');
  if (!t) {
    t = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '').slice(0, 8);
    props.setProperty('TOKEN', t);
  }
  const ss = SpreadsheetApp.getActive();
  ALLOWED_SHEETS.forEach(function (n) { if (!ss.getSheetByName(n)) ss.insertSheet(n); });
  const first = ss.getSheets()[0];
  if (ss.getSheets().length > ALLOWED_SHEETS.length && first.getLastRow() === 0 &&
      ALLOWED_SHEETS.indexOf(first.getName()) === -1) ss.deleteSheet(first);
  Logger.log('SHEETS_TOKEN = ' + t);
}

/** Đổi TOKEN mới (khi nghi bị lộ) — nhớ cập nhật lại Secrets của Streamlit. */
function doiToken() {
  PropertiesService.getScriptProperties().deleteProperty('TOKEN');
  caiDat();
}
