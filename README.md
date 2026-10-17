# Tín hiệu chứng khoán Việt Nam

Trang web tĩnh hiển thị đồ thị và tín hiệu mua/bán cho khoảng 80 mã, chạy hoàn toàn trên GitHub, không cần máy chủ.

## Cách hoạt động
1. GitHub Actions (`.github/workflows/update.yml`) chạy mỗi ngày giao dịch lúc 16:30, gọi `scripts/update_data.py`.
2. Script tải giá bằng `vnstock`, tính điểm, ghi `data/data.json` rồi tự commit.
3. `index.html` đọc `data/data.json` và vẽ đồ thị. Triển khai bằng GitHub Pages.

## Cài đặt
1. Tạo repository trên GitHub, tải toàn bộ file trong thư mục này lên.
2. Settings, Pages, Source: chọn nhánh `main`, thư mục `/ (root)`.
3. Tab Actions, chọn "Cập nhật dữ liệu", bấm Run workflow (lần đầu chạy tay, mất vài phút).
4. Mở địa chỉ GitHub Pages của repository.

## Tùy chỉnh
- `symbols.csv`: danh sách mã và ngành. Thêm hoặc bớt dòng tùy ý.
- `watchlist.txt`: mã theo dõi riêng, mỗi dòng một mã (tự thêm vào dù không có trong symbols.csv).
- Điểm số: hàm `score` trong `scripts/update_data.py`.

## Chạy thử trên máy
`pip install vnstock pandas`, `python scripts/update_data.py`, rồi `python -m http.server` và mở http://localhost:8000.

## Lưu ý
- Dữ liệu lấy từ nguồn công khai qua vnstock, không phải nguồn chính thức của sở giao dịch, và có thể đổi hoặc bị chặn.
- Quy tắc tính điểm là bản đầu, chưa backtest. Chỉ để tham khảo, không phải khuyến nghị đầu tư.
- GitHub có thể tạm dừng workflow theo lịch nếu repository không có hoạt động trong 60 ngày.
