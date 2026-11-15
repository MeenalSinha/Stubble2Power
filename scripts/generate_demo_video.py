import os
import sys
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def ease_in_out(t):
    """Smooth cubic ease-in-out curve."""
    return 3 * (t ** 2) - 2 * (t ** 3)

def interpolate_pos(p1, p2, t):
    e = ease_in_out(max(0.0, min(1.0, t)))
    return (p1[0] + (p2[0] - p1[0]) * e, p1[1] + (p2[1] - p1[1]) * e)

def create_cursor():
    size = 48
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Shadow
    so = 2
    sp = [(4+so, 2+so), (34+so, 26+so), (22+so, 28+so), (16+so, 42+so), (11+so, 40+so), (17+so, 27+so), (4+so, 21+so)]
    draw.polygon(sp, fill=(0, 0, 0, 80))
    # Border
    bp = [(4, 2), (34, 26), (22, 28), (16, 42), (11, 40), (17, 27), (4, 21)]
    draw.polygon(bp, fill=(15, 23, 42, 255))
    # Body
    ip = [(6, 6), (30, 25), (20, 27), (15, 39), (13, 38), (18, 26), (6, 20)]
    draw.polygon(ip, fill=(255, 255, 255, 255))
    return img

def main():
    print("Starting Stubble2Power Professional Demo Video Generation...")
    output_filename = "stubble2power_demo_1080p.mp4"
    fps = 30.0
    total_frames = 900 # exactly 30.00 seconds
    W, H = 1920, 1080

    cursor_sprite = create_cursor()

    # Load Windows fonts
    font_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 15)
    font_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 23)
    font_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 17)
    font_timer = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 14)
    font_outro_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 52)
    font_outro_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 26)
    font_outro_tag = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 20)

    # Assets cache
    asset_paths = {
        "s1_a": "final_assets/s1_home_a.png",
        "s1_b": "final_assets/s1_home_b.png",
        "s2_a": "final_assets/s2_map_a.png",
        "s2_b": "final_assets/s2_map_b.png",
        "s3_a": "final_assets/s3_harm_a.png",
        "s3_b": "final_assets/s3_harm_b.png",
        "s4_a": "final_assets/s4_cal_a.png",
        "s4_b": "final_assets/s4_cal_b.png",
        "s5_a": "final_assets/s5_anom_a.png",
        "s5_b": "final_assets/s5_anom_b.png",
        "s6_a": "final_assets/s6_agri_a.png",
        "s6_b": "final_assets/s6_agri_b.png",
        "s7_a": "final_assets/s7_farm_a.png",
        "s7_b": "final_assets/s7_farm_b.png",
        "s7_c": "final_assets/s7_biomass_c.png",
        "s8_a": "final_assets/s8_refinery_a.png",
        "s8_b": "final_assets/s8_refinery_b.png",
        "s9_a": "final_assets/s9_financial_a.png",
        "s9_b": "final_assets/s9_lca_b.png",
        "s9_c": "final_assets/s9_lca_c.png"
    }

    images = {}
    for k, v in asset_paths.items():
        if os.path.exists(v):
            img = Image.open(v).convert("RGBA")
            if img.size != (W, H):
                img = img.resize((W, H), Image.Resampling.LANCZOS)
            images[k] = img
        else:
            print(f"Warning: asset {v} not found!")

    # Setup VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_filename, fourcc, fps, (W, H))

    if not writer.isOpened():
        print("Error: Could not open VideoWriter!")
        sys.exit(1)

    # 9-scene configuration
    # scene: (start_frame, end_frame, img_a, img_b, badge, title, subtitle, cursor_waypoints, click_frames)
    scenes = [
        # Scene 1: Home Dashboard & Overview (0 - 95: 96 frames = 3.20s)
        {
            "start": 0, "end": 95,
            "img_a": "s1_a", "img_b": "s1_b",
            "badge": "FEATURE 01 / 09  •  PLATFORM OVERVIEW",
            "title": "Stubble2Power - Satellite Fire Intelligence & Mobile Bio-Refineries",
            "sub": "Harmonizes NASA MODIS & VIIRS Earth observations with decentralized mobile bio-refineries.",
            "cursor": [(1100, 580), (680, 440), (920, 440), (1180, 440)],
            "clicks": [35, 65]
        },
        # Scene 2: NASA Fire Intelligence & Hotspot Map (96 - 195: 100 frames = 3.33s)
        {
            "start": 96, "end": 195,
            "img_a": "s2_a", "img_b": "s2_b",
            "badge": "FEATURE 02 / 09  •  SATELLITE INTELLIGENCE",
            "title": "NASA FIRMS Real-Time Active Fire Hotspot Mapping",
            "sub": "MODIS (1km) & VIIRS (375m) cross-satellite detection with DPDP Act 2023 geospatial privacy obfuscation.",
            "cursor": [(850, 380), (920, 460), (1050, 480), (960, 720)],
            "clicks": [135, 175]
        },
        # Scene 3: MODIS–VIIRS Harmonization (196 - 295: 100 frames = 3.33s)
        {
            "start": 196, "end": 295,
            "img_a": "s3_a", "img_b": "s3_b",
            "badge": "FEATURE 03 / 09  •  SENSOR HARMONIZATION",
            "title": "Geodesic MODIS–VIIRS Harmonization Engine",
            "sub": "Cross-sensor spatial clustering eliminates observation double-counting and merges Fire Radiative Power (MW).",
            "cursor": [(480, 280), (480, 320), (850, 420), (1120, 460)],
            "clicks": [230, 270]
        },
        # Scene 4: Historical Burning Activity Calendar (296 - 395: 100 frames = 3.33s)
        {
            "start": 296, "end": 395,
            "img_a": "s4_a", "img_b": "s4_b",
            "badge": "FEATURE 04 / 09  •  HISTORICAL CALENDAR",
            "title": "Multi-Year Stubble Burning Activity Heatmaps",
            "sub": "Quantifies empirical day-of-year burning frequencies and harvest burning windows across Indo-Gangetic plains.",
            "cursor": [(550, 420), (820, 460), (1120, 480), (1350, 490)],
            "clicks": [335, 375]
        },
        # Scene 5: Seasonal & Anomaly Intelligence (396 - 495: 100 frames = 3.33s)
        {
            "start": 396, "end": 495,
            "img_a": "s5_a", "img_b": "s5_b",
            "badge": "FEATURE 05 / 09  •  ANOMALY INTELLIGENCE",
            "title": "Statistical Anomaly Detection & Baseline Forecasting",
            "sub": "Z-score and Interquartile Range (IQR) models identifying unprecedented fire outbreaks in high-risk zones.",
            "cursor": [(620, 380), (750, 420), (1050, 480), (1220, 520)],
            "clicks": [435, 470]
        },
        # Scene 6: Agricultural Fire Context (496 - 595: 100 frames = 3.33s)
        {
            "start": 496, "end": 595,
            "img_a": "s6_a", "img_b": "s6_b",
            "badge": "FEATURE 06 / 09  •  AGRICULTURAL CONTEXT",
            "title": "Cropland Masking & Phenological Calendar Correlation",
            "sub": "Verifies agricultural crop residue origin against land-use classification and seasonal paddy harvest timelines.",
            "cursor": [(720, 360), (880, 420), (1150, 520), (950, 680)],
            "clicks": [535, 570]
        },
        # Scene 7: Farmer & Biomass Management (596 - 695: 100 frames = 3.33s)
        {
            "start": 596, "end": 695,
            "img_a": "s7_a", "img_b": "s7_b",
            "badge": "FEATURE 07 / 09  •  BIOMASS MANAGEMENT",
            "title": "Farmer Parcels & Empirical Residue Inventory Modeling",
            "sub": "Spatial farm boundaries, empirical straw generation metrics, and moisture-adjusted cooperative storage.",
            "cursor": [(580, 420), (720, 460), (1050, 480), (1280, 620)],
            "clicks": [630, 675]
        },
        # Scene 8: Mobile Bio-Refinery Deployment (696 - 795: 100 frames = 3.33s)
        {
            "start": 696, "end": 795,
            "img_a": "s8_a", "img_b": "s8_b",
            "badge": "FEATURE 08 / 09  •  FLEET LOGISTICS",
            "title": "Mobile Bio-Refinery Fleet Routing & Decentralized Dispatch",
            "sub": "Point-of-harvest mobile pyrolysis processing, slashing long-haul biomass transport costs by 70%.",
            "cursor": [(520, 380), (760, 440), (1020, 480), (1220, 420)],
            "clicks": [730, 770]
        },
        # Scene 9: Financial and Environmental Impact Dashboard (796 - 899: 104 frames = 3.47s)
        {
            "start": 796, "end": 899,
            "img_a": "s9_a", "img_b": "s9_b",
            "badge": "FEATURE 09 / 09  •  IMPACT DASHBOARD",
            "title": "Techno-Economic Viability & Carbon-Negative LCA Impact",
            "sub": "Quantified CO2e emissions avoided, PM2.5 reduction, attractive farmer dividends, and bio-energy revenue.",
            "cursor": [(600, 380), (820, 430), (1050, 460), (1180, 520)],
            "clicks": [830, 865]
        }
    ]

    print(f"Synthesizing {total_frames} frames ({total_frames / fps:.2f} seconds) at 1080p...")

    for f_idx in range(total_frames):
        # Determine current scene
        cur_sc = None
        for sc in scenes:
            if sc["start"] <= f_idx <= sc["end"]:
                cur_sc = sc
                break

        if cur_sc is None:
            cur_sc = scenes[-1]

        sc_start = cur_sc["start"]
        sc_len = cur_sc["end"] - sc_start + 1
        sc_progress = (f_idx - sc_start) / max(1, sc_len - 1)

        # Base image interpolation (smooth vertical scrolling simulation)
        # We blend smoothly between img_a and img_b
        img_a = images[cur_sc["img_a"]]
        img_b = images[cur_sc["img_b"]]

        # Smooth scroll curve: holds slightly at start, scrolls smoothly, holds at end
        scroll_t = ease_in_out(sc_progress)
        base_frame = Image.blend(img_a, img_b, scroll_t)

        # Cross-fade transition between scenes (first 5 frames of a scene blend from previous scene)
        if f_idx - sc_start < 5 and sc_start > 0:
            prev_sc = scenes[scenes.index(cur_sc) - 1]
            prev_end_img = images[prev_sc["img_b"]]
            fade_t = (f_idx - sc_start) / 5.0
            base_frame = Image.blend(prev_end_img, base_frame, fade_t)

        # Fade in from black at the very beginning (first 10 frames)
        if f_idx < 10:
            black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            base_frame = Image.blend(black, base_frame, f_idx / 10.0)

        # Outro handling (frames 884 to 899: 15 frames)
        if f_idx >= 884:
            outro_t = (f_idx - 884) / 15.0
            outro_img = Image.new("RGBA", (W, H), (15, 23, 42, 255))
            o_draw = ImageDraw.Draw(outro_img)
            
            # Draw decorative backdrop rings
            for r in [200, 320, 440]:
                o_draw.ellipse([W//2 - r, H//2 - r - 20, W//2 + r, H//2 + r - 20], outline=(16, 185, 129, 30), width=2)
            
            # Outro card
            title_text = "Stubble2Power"
            t_box = font_outro_title.getbbox(title_text)
            t_w = t_box[2] - t_box[0]
            o_draw.text(((W - t_w)//2, H//2 - 90), title_text, font=font_outro_title, fill=(240, 253, 244, 255))
            
            sub_text = "NASA Satellite Fire Intelligence & Mobile Bio-Refineries"
            s_box = font_outro_sub.getbbox(sub_text)
            s_w = s_box[2] - s_box[0]
            o_draw.text(((W - s_w)//2, H//2 - 15), sub_text, font=font_outro_sub, fill=(16, 185, 129, 255))

            tag_text = "NASA Space Apps Challenge 09 | Clean Energy. Sustainable Agriculture."
            tg_box = font_outro_tag.getbbox(tag_text)
            tg_w = tg_box[2] - tg_box[0]
            o_draw.text(((W - tg_w)//2, H//2 + 45), tag_text, font=font_outro_tag, fill=(148, 163, 184, 255))

            base_frame = Image.blend(base_frame, outro_img, ease_in_out(outro_t))

        # Create overlay layer for UI, Lower Third, Cursor, and Progress Bar
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # -----------------------------------------------------------------
        # 1. Top Watermark Badge
        # -----------------------------------------------------------------
        draw.rounded_rectangle([W - 470, 20, W - 25, 60], radius=8, fill=(15, 23, 42, 220), outline=(16, 185, 129, 180), width=1)
        draw.text((W - 450, 29), "STUBBLE2POWER  |  NASA SATELLITE INTELLIGENCE", font=font_timer, fill=(240, 253, 244, 255))

        # -----------------------------------------------------------------
        # 2. Lower-Third Feature Information Card
        # -----------------------------------------------------------------
        # Don't show lower-third during final outro
        if f_idx < 880:
            card_w, card_h = 1380, 118
            card_x = (W - card_w) // 2
            card_y = H - card_h - 22

            # Frosted glass container with emerald accent glow
            draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=14, fill=(15, 23, 42, 238), outline=(16, 185, 129, 220), width=2)

            # Badge pill
            badge_txt = cur_sc["badge"]
            badge_bbox = font_badge.getbbox(badge_txt)
            badge_w = badge_bbox[2] - badge_bbox[0] + 24
            draw.rounded_rectangle([card_x + 25, card_y + 16, card_x + 25 + badge_w, card_y + 40], radius=6, fill=(16, 185, 129, 255))
            draw.text((card_x + 37, card_y + 19), badge_txt, font=font_badge, fill=(255, 255, 255, 255))

            # Headline Title
            draw.text((card_x + 25, card_y + 49), cur_sc["title"], font=font_title, fill=(255, 255, 255, 255))

            # Subtitle Explanation
            draw.text((card_x + 25, card_y + 84), cur_sc["sub"], font=font_sub, fill=(203, 213, 225, 255))

            # Live Timer inside card
            elapsed_sec = int(f_idx / fps)
            timer_str = f"00:{elapsed_sec:02d} / 00:30"
            draw.text((card_x + card_w - 130, card_y + 19), timer_str, font=font_timer, fill=(148, 163, 184, 255))

        # -----------------------------------------------------------------
        # 3. Animated Cursor with Smooth Path & Click Ripple
        # -----------------------------------------------------------------
        if f_idx < 880:
            waypoints = cur_sc["cursor"]
            num_seg = len(waypoints) - 1
            cur_seg_float = sc_progress * num_seg
            seg_idx = min(int(cur_seg_float), num_seg - 1)
            seg_t = cur_seg_float - seg_idx
            
            p1 = waypoints[seg_idx]
            p2 = waypoints[seg_idx + 1]
            cx, cy = interpolate_pos(p1, p2, seg_t)

            # Check for click ripples
            for cf in cur_sc["clicks"]:
                if 0 <= (f_idx - cf) <= 12:
                    ripple_age = (f_idx - cf) / 12.0
                    r_rad = int(8 + ripple_age * 28)
                    r_alpha = int(220 * (1.0 - ripple_age))
                    draw.ellipse([cx - r_rad, cy - r_rad, cx + r_rad, cy + r_rad], outline=(16, 185, 129, r_alpha), width=3)

            # Stamp cursor sprite
            overlay.paste(cursor_sprite, (int(cx), int(cy)), cursor_sprite)

        # -----------------------------------------------------------------
        # 4. Global Progress Bar at Bottom Edge
        # -----------------------------------------------------------------
        bar_h = 6
        progress_ratio = f_idx / (total_frames - 1)
        draw.rectangle([0, H - bar_h, W, H], fill=(30, 41, 59, 255))
        draw.rectangle([0, H - bar_h, int(W * progress_ratio), H], fill=(16, 185, 129, 255))

        # Composite frame
        composed = Image.alpha_composite(base_frame, overlay).convert("RGB")

        # Convert to BGR numpy array for OpenCV VideoWriter
        frame_bgr = cv2.cvtColor(np.array(composed), cv2.COLOR_RGB2BGR)
        writer.write(frame_bgr)

        if (f_idx + 1) % 150 == 0 or f_idx == total_frames - 1:
            print(f"Rendered {f_idx + 1}/{total_frames} frames ({(f_idx + 1)/fps:.1f}s)...")

    writer.release()
    print("Video encoding complete!")
    print(f"Output video: {output_filename}")
    print(f"File size: {os.path.getsize(output_filename):,} bytes")

if __name__ == "__main__":
    main()
