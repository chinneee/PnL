# 📊 P&L Dashboard — Streamlit

Dashboard xem P&L theo ASIN từ Google Sheets, deploy trên Streamlit Cloud.

---

## 🚀 Hướng dẫn Deploy (5 bước)

### Bước 1 — Chuẩn bị Google Service Account

1. Vào [console.cloud.google.com](https://console.cloud.google.com)
2. Tạo project mới (hoặc dùng project có sẵn)
3. Bật 2 API:
   - **Google Sheets API**
   - **Google Drive API**
4. Vào **IAM & Admin → Service Accounts → Create Service Account**
5. Tạo xong, vào service account → **Keys → Add Key → JSON**
6. Tải file JSON về

### Bước 2 — Share Google Sheet cho Service Account

1. Mở file JSON vừa tải, copy giá trị `client_email`  
   (dạng: `xxx@xxx.iam.gserviceaccount.com`)
2. Mở Google Sheet → Share → paste email đó → **Viewer**

### Bước 3 — Chỉnh `app.py`

Mở `app.py`, tìm dòng đầu và sửa:
```python
SHEET_URL  = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"
SHEET_NAME = "Raw"   # tên sheet tab của bạn
```

### Bước 4 — Push lên GitHub

```bash
git init
git add .
git commit -m "P&L dashboard"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Bước 5 — Deploy trên Streamlit Cloud

1. Vào [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Chọn repo GitHub vừa push
3. Main file path: `app.py`
4. Vào **Advanced settings → Secrets**, paste nội dung từ `secrets_template.toml`  
   (thay bằng thông tin thật từ file JSON service account)
5. Click **Deploy** ✅

---

## 📁 Cấu trúc file

```
pnl_dashboard/
├── app.py                  # Main app
├── requirements.txt        # Dependencies
└── secrets_template.toml   # Mẫu secrets (KHÔNG push lên GitHub)
```

> ⚠️ **Không bao giờ push `secrets_template.toml` lên GitHub**.  
> Thêm vào `.gitignore`: `secrets_template.toml`

---

## 🔧 Cột dữ liệu cần có trong Sheet

| Cột | Mô tả |
|-----|-------|
| `Date` | Ngày (dd/mm/yyyy hoặc yyyy-mm-dd) |
| `ASIN` | Mã ASIN sản phẩm |
| `Name` | Tên sản phẩm |
| `SalesOrganic`, `SalesPPC`, `SalesSponsoredProducts`, `SalesSponsoredDisplay` | Doanh thu |
| `UnitsOrganic`, `UnitsPPC`, `UnitsSponsoredProducts`, `UnitsSponsoredDisplay` | Số lượng |
| `Refunds` | Số lượng hoàn hàng |
| `PromoValue` | Giá trị khuyến mãi |
| `SponsoredProducts`, `SponsoredDisplay`, `SponsoredВrands`, `SponsoredBrandsVideo` | Chi phí quảng cáo |
| `RefundCost` | Chi phí hoàn hàng |
| `AmazonFees` | Phí Amazon |
| `ProductCost` / `Cost of Goods` | Giá vốn |
| `GrossProfit` | Lợi nhuận gộp |
| `NetProfit` | Lợi nhuận ròng |
| `EstimatedPayout` | Thanh toán ước tính |
| `Sessions` | Lượt truy cập |
