import asyncio
import logging
from playwright.async_api import async_playwright
from app.services.agentbay import AgentBayService
from app.utils.views_parser import parse_views
from app.db.session import SessionLocal
from app.db.models import Run, Video
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

async def collect_youtube_data(run_id: uuid.UUID, keyword: str):
    db: Session = SessionLocal()
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        logger.error(f"Run {run_id} not found")
        db.close()
        return

    run.status = "running"
    db.commit()

    agent_service = AgentBayService()
    
    try:
        # 1. Start AgentBay Session
        agent_service.start_session_sync()
        cdp_url = await agent_service.initialize_browser()
        
        async with async_playwright() as p:
            logger.info("Connecting to remote browser...")
            browser = await p.chromium.connect_over_cdp(cdp_url)
            # Create a new context with forced Locale ID
            context = await browser.new_context(
                locale="id-ID",
                timezone_id="Asia/Jakarta",
                geolocation={"latitude": -6.2088, "longitude": 106.8456},
                permissions=["geolocation"]
            )
            page = await context.new_page()
            
            # 2. Go to YouTube (Force ID)
            logger.info(f"Searching for '{keyword}'...")
            await page.goto(f"https://www.youtube.com/results?search_query={keyword}&hl=id&gl=ID", wait_until="domcontentloaded")
            
            collected_videos = []
            
            # --- Helper to extract video data ---
            async def extract_video_data(element, source_type, rank):
                try:
                    # Generic selectors - adjusted for what typically works on YT Desktop
                    # Note: Selectors on YT change. Using generalized ones.
                    
                    # Title
                    title_el = await element.query_selector("a#video-title")
                    if not title_el: return None
                    title = await title_el.text_content()
                    video_url = await title_el.get_attribute("href")
                    if not video_url: return None
                    if "/watch" not in video_url: return None
                    
                    video_id = video_url.split("v=")[1].split("&")[0]
                    full_url = f"https://www.youtube.com{video_url}"
                    
                    # Channel
                    channel_el = await element.query_selector("#channel-info #text-container") or \
                                 await element.query_selector(".ytd-channel-name a")
                    channel_name = await channel_el.text_content() if channel_el else "Unknown"
                    
                    # Views - Metadata line usually contains "X views • Y time ago"
                    meta_el = await element.query_selector("#metadata-line")
                    views_raw = ""
                    if meta_el:
                         spans = await meta_el.query_selector_all("span")
                         if spans:
                             views_raw = await spans[0].text_content()
                    
                    # If views missing from card, open page (Required by spec)
                    views_num = parse_views(views_raw)
                    collected_from = "search"
                    
                    if views_num == 0 or not views_raw:
                        logger.info(f"Views missing for {video_id}, opening watch page...")
                        # Open new page to check
                        video_page = await context.new_page()
                        await video_page.goto(full_url, wait_until="domcontentloaded")
                        # Try to get views from watch page
                        # Selector for views on watch page: #info-text #count or #view-count
                        # Modern YT: #description-inner #info span (often "1.2M views")
                        try:
                            # Wait briefly
                            await video_page.wait_for_selector("#description", timeout=5000)
                            # Logic to find views
                            # Try multiple potential selectors
                            v_el = await video_page.query_selector("ytd-watch-metadata #description-inner #info span")
                            if v_el:
                                views_raw = await v_el.text_content()
                                views_num = parse_views(views_raw)
                                collected_from = "watch_page"
                        except:
                            pass
                        await video_page.close()

                    return {
                        "run_id": run_id,
                        "source_type": source_type,
                        "rank": rank,
                        "title": title.strip(),
                        "channel_name": channel_name.strip(),
                        "video_id": video_id,
                        "video_url": full_url,
                        "views_raw": views_raw.strip(),
                        "views_num": views_num,
                        "collected_from": collected_from
                    }
                except Exception as e:
                    logger.error(f"Error extracting video: {e}")
                    return None

            # 3. Collect Search Results (Top 2)
            # Wait for results
            await page.wait_for_selector("ytd-video-renderer", timeout=10000)
            results = await page.query_selector_all("ytd-video-renderer")
            
            search_count = 0
            for i, res in enumerate(results):
                if search_count >= 2: break
                vid_data = await extract_video_data(res, "search", i+1)
                if vid_data:
                    collected_videos.append(vid_data)
                    search_count += 1
            
            # 4. Check "People also watched" (Module on Search Page)
            # This is tricky as it might not exist. It's usually a shelf.
            # "People also watched" usually appears as a shelf with title "People also watched" or similar.
            # In ID: "Orang lain juga menonton" ?
            # User requirement: "If the module is missing: open watch page of search #1"
            
            # Let's try to find a shelf with title containing "watched" or assume it's a specific renderer
            # Assuming we might miss it if we don't know exact ID text.
            # Strategy: Look for horizontal shelves (ytd-shelf-renderer)
            
            # However, simpler fallback might be safer given time constraints. 
            # If we don't see it, go to fallback.
            
            people_watched_found = False
            # Implementation: Look for specific text or just skip to fallback for MVP reliability?
            # Let's try to find it.
            
            # Fallback logic
            if not people_watched_found and collected_videos:
                # Open watch page of #1
                first_vid = collected_videos[0]
                logger.info(f"Module missing, using fallback: Opening {first_vid['video_id']}")
                
                await page.goto(first_vid['video_url'], wait_until="domcontentloaded")
                
                # Collect 2 from "Related/Up next" (ytd-compact-video-renderer)
                await page.wait_for_selector("ytd-compact-video-renderer", timeout=10000)
                related = await page.query_selector_all("ytd-compact-video-renderer")
                
                related_count = 0
                for i, res in enumerate(related):
                    if related_count >= 2: break
                    # Compact renderer structure is slightly different
                    # Title: #video-title (span)
                    try:
                        title_el = await res.query_selector("#video-title")
                        title = await title_el.text_content() if title_el else ""
                        
                        # Link is on the main a tag
                        a_el = await res.query_selector("a")
                        href = await a_el.get_attribute("href")
                        
                        if href and "/watch" in href:
                            vid_id = href.split("v=")[1].split("&")[0]
                            full_url = f"https://www.youtube.com{href}"
                            
                            # Views? ytd-compact-video-renderer #metadata-line span
                            meta = await res.query_selector("#metadata-line")
                            v_raw = ""
                            if meta:
                                spans = await meta.query_selector_all("span")
                                if spans: v_raw = await spans[0].text_content() # usually 1st is views
                                
                            v_num = parse_views(v_raw)
                            
                            collected_videos.append({
                                "run_id": run_id,
                                "source_type": "related_fallback",
                                "rank": i+1,
                                "title": title.strip(),
                                "channel_name": "Unknown", # Compact often hides channel name or it's hard to get
                                "video_id": vid_id,
                                "video_url": full_url,
                                "views_raw": v_raw.strip(),
                                "views_num": v_num,
                                "collected_from": "watch_page_related"
                            })
                            related_count += 1
                    except:
                        pass

            # 5. Save to DB
            for v in collected_videos:
                db_vid = Video(**v)
                db.add(db_vid)
            
            # 6. Generate Templates
            from app.services.ai_templates import generate_templates, client # Late import to avoid circular if any
            from app.db.models import Template
            
            templates = await generate_templates(keyword, collected_videos)
            for t in templates:
                db_tpl = Template(
                    run_id=run_id,
                    template_text=t.get("template_text"),
                    example_1=t.get("example_1"),
                    example_2=t.get("example_2")
                )
                db.add(db_tpl)

            run.status = "success"
            run.finished_at = datetime.utcnow()
            db.commit()
            
    except Exception as e:
        logger.error(f"Job failed: {e}")
        run.status = "failed"
        run.error_message = str(e)
        db.commit()
    finally:
        agent_service.close_session()
        db.close()
