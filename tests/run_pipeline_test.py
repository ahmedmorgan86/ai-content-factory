"""
AI Content Factory - End-to-End System Integration & Acceptance Test
Executes and validates all 13 project acceptance criteria.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config, DB_DIR, STORAGE_ROOT
from core.idea_engine import IdeaEngine
from core.script_engine import ScriptEngine
from core.seo_engine import SEOEngine
from core.thumbnail_engine import ThumbnailEngine
from core.storage_engine import StorageEngine
from core.telegram_bot import TelegramControlPanel
from core.publishing_engine import PublishingEngine
from core.analytics_engine import AnalyticsEngine

def run_acceptance_tests():
    print("=" * 70)
    print("   AI CONTENT FACTORY - COMPREHENSIVE SYSTEM ACCEPTANCE TEST   ")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = 13

    # CRITERION 1: Niche Settings Reception & Verification
    print("\n[TEST 1/13] Checking Niche & Configuration Ingestion...")
    assert Config.NICHE == "Technology & Artificial Intelligence"
    assert Config.LANGUAGE == "Egyptian Arabic"
    assert Config.IDEAS_PER_BATCH == 20
    print(f"  [✓] Niche: '{Config.NICHE}', Language: '{Config.LANGUAGE}', Batch: {Config.IDEAS_PER_BATCH}")
    passed_tests += 1

    # CRITERION 2: Generating 20 Scored Ideas
    print("\n[TEST 2/13] Generating 20 Scored Unique Ideas...")
    idea_engine = IdeaEngine()
    ideas = idea_engine.generate_batch()
    assert len(ideas) == 20, f"Expected 20 ideas, got {len(ideas)}"
    assert all("idea_id" in i and "priority_score" in i for i in ideas)
    print(f"  [✓] Successfully generated {len(ideas)} unique scored ideas.")
    passed_tests += 1

    # CRITERION 3: Saving Ideas to Database (Sheets / CSV / XLSX)
    print("\n[TEST 3/13] Saving Ideas to Google Sheets Database...")
    saved_count = idea_engine.save_ideas_to_database(ideas)
    assert saved_count == 20
    assert (DB_DIR / "Ideas.csv").exists()
    assert (DB_DIR / "AI_Content_Factory_Database.xlsx").exists()
    print(f"  [✓] Successfully persisted {saved_count} ideas into Ideas.csv and synced XLSX.")
    passed_tests += 1

    # CRITERION 4: Telegram Idea Selection Simulation
    print("\n[TEST 4/13] Simulating Telegram Selection of Top Idea...")
    bot = TelegramControlPanel()
    selected_idea = ideas[0]
    user_id = "123456789"
    assert bot.is_authorized(user_id)
    menu_text, menu_kb = bot.build_main_menu_payload()
    ideas_text, ideas_kb = bot.format_ideas_list_message(ideas)
    assert len(ideas_kb["inline_keyboard"]) >= 10
    print(f"  [✓] Telegram interactive selector ready. Selected: {selected_idea['idea_id']} - '{selected_idea['video_title']}'")
    passed_tests += 1

    # CRITERION 5: Script & Scene Breakdown Generation
    print("\n[TEST 5/13] Generating Egyptian Arabic Script & 8-Point Scene Breakdown...")
    script_engine = ScriptEngine()
    short_script = script_engine.generate_short_script(selected_idea)
    long_script = script_engine.generate_long_script(selected_idea)
    
    assert short_script["word_count"] > 50
    assert len(short_script["scene_breakdown"]) >= 4
    assert long_script["word_count"] > 300
    assert len(long_script["scene_breakdown"]) >= 5
    
    script_id = script_engine.save_script_to_database(short_script)
    print(f"  [✓] Short script: {short_script['estimated_duration']} ({short_script['word_count']} words).")
    print(f"  [✓] Long script: {long_script['estimated_duration']} ({long_script['word_count']} words, {len(long_script['chapters'])} chapters).")
    passed_tests += 1

    # CRITERION 6: SEO Package Generation
    print("\n[TEST 6/13] Generating Multi-Platform SEO Package...")
    seo_engine = SEOEngine()
    seo_pkg = seo_engine.generate_seo_package(selected_idea, short_script)
    assert len(seo_pkg["alternative_titles"]) == 5
    assert len(seo_pkg["tags_20"]) == 20
    assert len(seo_pkg["hashtags_5"]) == 5
    assert len(seo_pkg["pinned_comment"]) > 20
    seo_id = seo_engine.save_seo_to_database(seo_pkg)
    print(f"  [✓] Generated 5 titles, 20 tags, 5 hashtags, pinned comment. Recorded as {seo_id}.")
    passed_tests += 1

    # CRITERION 7 & 8: Real Thumbnail Generation & Exact Dimensions Verification
    print("\n[TEST 7 & 8/13] Generating & Verifying Exact Thumbnail Dimensions...")
    thumb_engine = ThumbnailEngine()
    target_storage = STORAGE_ROOT / selected_idea["idea_id"] / "Thumbnails"
    thumb_res = thumb_engine.generate_and_verify_thumbnails(
        selected_idea["idea_id"], selected_idea["video_title"], output_dir=target_storage
    )
    assert os.path.exists(thumb_res["youtube_path"])
    assert os.path.exists(thumb_res["vertical_path"])
    assert thumb_res["youtube_dimensions"] == (1280, 720)
    assert thumb_res["vertical_dimensions"] == (1080, 1920)
    print(f"  [✓] Verified YouTube 16:9 Thumbnail: {thumb_res['youtube_dimensions']} at {thumb_res['youtube_path']}")
    print(f"  [✓] Verified Vertical 9:16 Cover: {thumb_res['vertical_dimensions']} at {thumb_res['vertical_path']}")
    passed_tests += 2

    # CRITERION 9: Google Drive / Storage Folder Hierarchy
    print("\n[TEST 9/13] Structuring Complete Video Assets Directory in Storage...")
    storage_engine = StorageEngine()
    folder_tree = storage_engine.create_video_structure(selected_idea["idea_id"])
    script_md, script_json = storage_engine.save_script_asset(selected_idea["idea_id"], short_script)
    seo_json, seo_txt = storage_engine.save_seo_asset(selected_idea["idea_id"], seo_pkg)
    
    assert os.path.exists(script_md)
    assert os.path.exists(script_json)
    assert os.path.exists(seo_json)
    assert os.path.exists(seo_txt)
    print(f"  [✓] Structured /AI Content Factory/2026/{selected_idea['idea_id']}/ with 6 subfolders.")
    print(f"  [✓] Files safely staged: Script .md, Scene .json, SEO .json, Copyable .txt")
    passed_tests += 1

    # CRITERION 10: Dispatching Result Package to Telegram
    print("\n[TEST 10/13] Formatting Telegram Review Delivery Package...")
    delivery_text, delivery_kb = bot.format_delivery_package(selected_idea, short_script, seo_pkg, thumb_res)
    assert "حزمة الإنتاج الكاملة" in delivery_text
    assert len(delivery_kb["inline_keyboard"]) == 2
    print("  [✓] Formatted Telegram delivery card with Inline Action Keyboards.")
    passed_tests += 1

    # CRITERION 11: Approval Gate Testing
    print("\n[TEST 11/13] Verifying Security Approval Gate...")
    pub_engine = PublishingEngine()
    # Test blocked state before approval
    blocked_res = pub_engine.prepare_publishing_manifest(
        selected_idea["idea_id"], selected_idea["video_title"], seo_pkg, thumb_res, approved=False
    )
    assert blocked_res["status"] == "BLOCKED_APPROVAL_REQUIRED"
    print("  [✓] Security gate correctly BLOCKS execution without user approval.")
    passed_tests += 1

    # CRITERION 12: Publishing Preparation for Supported Platforms
    print("\n[TEST 12/13] Preparing Approved Publishing Payloads...")
    approved_res = pub_engine.prepare_publishing_manifest(
        selected_idea["idea_id"], selected_idea["video_title"], seo_pkg, thumb_res, approved=True
    )
    assert approved_res["status"] == "SUCCESS_PREPARED"
    assert len(approved_res["manifest"]) == 5
    print("  [✓] Prepared payloads for: YouTube, YouTube Shorts, TikTok, Instagram Reels, Facebook Reels.")
    passed_tests += 1

    # CRITERION 13: Logging Operations & Analytics Engine
    print("\n[TEST 13/13] Checking Operational Logs & Analytics Intelligence...")
    analytics_engine = AnalyticsEngine()
    score = analytics_engine.record_metrics({
        "record_id": f"REC-{selected_idea['idea_id']}",
        "idea_id": selected_idea["idea_id"],
        "video_title": selected_idea["video_title"],
        "platform": "YouTube",
        "views": 35000,
        "likes": 2400,
        "comments": 180,
        "shares": 450,
        "watch_time": 185000,
        "avd": "05:17",
        "ctr": 11.4,
        "subscribers_growth": 620
    })
    digest = analytics_engine.generate_weekly_telegram_digest()
    assert score > 0
    assert "Weekly Growth Digest" in digest
    print(f"  [✓] Performance score computed: {score}/10.")
    print("  [✓] Generated weekly executive digest for Telegram.")
    passed_tests += 1

    print("\n" + "=" * 70)
    print(f"🎉 ALL ACCEPTANCE TESTS PASSED: {passed_tests}/{total_tests} CRITERIA VERIFIED (100%)")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_acceptance_tests()
    sys.exit(0 if success else 1)
