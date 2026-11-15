"""
AI Content Factory - Google Sheets Database Generator
Creates CSV files and an Excel Workbook representing the complete 8-sheet database schema.
"""

import os
import csv

DB_DIR = os.path.dirname(os.path.abspath(__file__))

SHEETS_SCHEMA = {
    "Ideas": [
        "Idea ID", "Video Title", "Video Summary", "Target Audience", "Hook", 
        "Content Angle", "Video Type", "Estimated Duration", "SEO Keywords", 
        "Competition Level", "Interest Score", "Priority Score", "Research Sources", 
        "Status", "Created Date"
    ],
    "Scripts": [
        "Script ID", "Idea ID", "Video Type", "Language", "Hook (0-3s)", 
        "Full Voiceover (Egyptian Arabic)", "Scene Breakdown JSON", "Suggested CTA", 
        "Word Count", "Estimated Duration", "Status", "Script File Link", "Last Updated"
    ],
    "SEO": [
        "SEO ID", "Idea ID", "Main Title", "Alternative Title 1", "Alternative Title 2", 
        "Alternative Title 3", "Alternative Title 4", "Alternative Title 5", 
        "YouTube Description", "Short Description (Reels/TikTok)", "Tags (Comma-separated)", 
        "Hashtags", "Primary Keywords", "Secondary Keywords", "Pinned Comment", "Related Video Ideas"
    ],
    "Thumbnails": [
        "Thumbnail ID", "Idea ID", "Visual Concept & AI Prompt", "Raw Image URL", 
        "YouTube 16:9 (1280x720) Link", "Vertical 9:16 (1080x1920) Link", 
        "Personal Photo Included", "Arabic Text Overlay", "Storage Path / Cloudinary ID", 
        "Dimensions Verified", "Status", "Created Date"
    ],
    "Publishing": [
        "Publish ID", "Idea ID", "Video Title", "Platform", "Scheduled Date", 
        "Published Date", "Post URL", "Publishing Mode", "User Approval Status", 
        "Execution Log", "Last Status Check"
    ],
    "Analytics": [
        "Record ID", "Idea ID", "Video Title", "Platform", "Views", "Likes", 
        "Comments", "Shares", "Watch Time (Mins)", "Average View Duration (AVD)", 
        "CTR (%)", "Subscribers Growth", "Recorded Date", "AI Performance Score"
    ],
    "Settings": [
        "Key", "Value", "Description", "Allowed Options / Notes"
    ],
    "Sources": [
        "Source ID", "Source Name", "Source URL / RSS", "Category", 
        "Reliability Level", "Fetch Frequency", "Status"
    ]
}

SAMPLE_DATA = {
    "Settings": [
        ["niche", "Technology & Artificial Intelligence", "مجال القناة الأساسي", "Tech, AI"],
        ["target_audience", "Arab Youth, Tech Enthusiasts, AI Creators, Business Owners", "الجمهور المستهدف", "General Tech"],
        ["country", "Egypt / Arab World", "الدولة والمنطقة المستهدفة", "MENA"],
        ["language", "Egyptian Arabic", "اللغة الأساسية للمحتوى والسكريبت", "Egyptian Arabic"],
        ["main_platforms", "YouTube, YouTube Shorts, TikTok, Instagram Reels, Facebook Reels", "المنصات المستهدفة للنشر", "Multi-platform"],
        ["ideas_per_batch", "20", "عدد الأفكار لكل دفعة بحث", "10-50"],
        ["content_style", "Educational, Engaging, Professional, Conversational", "طبيعة ونبرة المحتوى", "Engaging/Educational"],
        ["brand_colors", "#0F172A, #38BDF8, #818CF8", "ألوان الهوية البصرية (Dark Slate, Light Blue, Indigo)", "HEX Codes"],
        ["brand_identity", "Future Tech Navigator - موجه التكنولوجيا المستقبلي", "شخصية وهوية البراند", "Text"],
        ["telegram_authorized_users", "123456789", "معرفات تليجرام المسموح لها بإدارة النظام", "Comma-separated user IDs"]
    ],
    "Sources": [
        ["SRC-01", "OpenAI Official Blog & Changelog", "https://openai.com/news/rss.xml", "AI Research & Releases", "High (Primary Source)", "Daily", "Active"],
        ["SRC-02", "Google DeepMind Research", "https://deepmind.google/discover/blog/rss.xml", "Core AI Breakthroughs", "High (Primary Source)", "Daily", "Active"],
        ["SRC-03", "Hugging Face Daily Papers", "https://huggingface.co/papers", "Open Source & New Models", "High (Technical)", "Daily", "Active"],
        ["SRC-04", "TechCrunch AI Section", "https://techcrunch.com/category/artificial-intelligence/feed/", "Industry & Funding News", "Medium-High", "Daily", "Active"],
        ["SRC-05", "Product Hunt AI Leaderboard", "https://www.producthunt.com/topics/artificial-intelligence", "New Consumer Tools", "Medium (Trends)", "Daily", "Active"],
        ["SRC-06", "Reddit r/ArtificialIntelligence & r/LocalLlama", "https://www.reddit.com/r/ArtificialIntelligence/.rss", "Community Questions & Sentiment", "Medium (Audience Pulse)", "Daily", "Active"]
    ],
    "Ideas": [
        [
            "IDEA-2026-001",
            "إزاي تستخدم وكلاء الذكاء الاصطناعي (AI Agents) في أتمتة شغلك اليومي في 2026؟",
            "دليل عملي وتطبيقي لشرح ثورة وكلاء الذكاء الاصطناعي الفردية والمستقلة، مع تجربة عملية لبناء وكيل شخصي ينجز المهام الروتينية.",
            "الشباب العربي، المستقلون، ورواد الأعمال",
            "تخيل لو عندك موظف شاطر جداً بيشتغل 24 ساعة ببلاش ومابيشتكيش.. ده مش خيال، ده AI Agent!",
            "دليل عملي خطوة بخطوة بعيداً عن التعقيد الأكاديمي",
            "Long-form",
            "8-10 دقائق",
            "ذكاء اصطناعي, وكلاء الذكاء الاصطناعي, AI Agents 2026, أتمتة الأعمال, تطبيقات عملية",
            "Medium",
            "9.5",
            "9.8",
            "Hugging Face Papers, Google DeepMind Releases",
            "New",
            "2026-11-15"
        ],
        [
            "IDEA-2026-002",
            "أقوى 3 أدوات ذكاء اصطناعي نزلت الأسبوع ده لازم تجربها فوراً!",
            "استعراض سريع ومبهر لثلاث أدوات جديدة تماماً توفر ساعات من العمل اليومي.",
            "صناع المحتوى والمصممون",
            "الأداة التانية بالذات هتوفر عليك اشتراك برامج بآلاف الجنيهات!",
            "أدوات سرية سريعة ومجانية",
            "Short-form",
            "60 ثانية",
            "أدوات ذكاء اصطناعي, أدوات مجانية, AI Tools, شورتس تكنولوجيا",
            "Low",
            "9.0",
            "9.2",
            "Product Hunt, TechCrunch",
            "New",
            "2026-11-15"
        ]
    ]
}

def create_csv_files():
    for sheet_name, headers in SHEETS_SCHEMA.items():
        csv_path = os.path.join(DB_DIR, f"{sheet_name}.csv")
        with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            if sheet_name in SAMPLE_DATA:
                for row in SAMPLE_DATA[sheet_name]:
                    writer.writerow(row)
        print(f"[✓] Created CSV schema: {sheet_name}.csv")

def create_excel_workbook():
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        cell_font = Font(name="Segoe UI", size=10)
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        for sheet_name, headers in SHEETS_SCHEMA.items():
            ws = wb.create_sheet(title=sheet_name)
            ws.views.sheetView[0].rightToLeft = True  # RTL for Arabic readability

            # Write header
            ws.append(headers)
            for col_num in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws.row_dimensions[1].height = 28

            # Write actual data from CSV if exists, otherwise fallback to SAMPLE_DATA
            csv_path = os.path.join(DB_DIR, f"{sheet_name}.csv")
            if os.path.exists(csv_path):
                with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)  # Skip header row since ws.append(headers) already did it
                    for row_data in reader:
                        if row_data:
                            ws.append(row_data)
            elif sheet_name in SAMPLE_DATA:
                for row_data in SAMPLE_DATA[sheet_name]:
                    ws.append(row_data)

            # Style data cells & auto-adjust column width
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(headers)):
                for cell in row:
                    cell.font = cell_font
                    cell.border = thin_border
                    cell.alignment = Alignment(vertical="center", wrap_text=False)

            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 45)

        excel_path = os.path.join(DB_DIR, "AI_Content_Factory_Database.xlsx")
        wb.save(excel_path)
        print(f"[✓] Created Excel Master Workbook: {excel_path}")
    except ImportError:
        print("[!] openpyxl not installed yet. Skipping XLSX creation.")

if __name__ == "__main__":
    create_csv_files()
    create_excel_workbook()
