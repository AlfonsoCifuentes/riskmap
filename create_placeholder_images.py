#!/usr/bin/env python3
"""
Create placeholder satellite images to fix 404 errors
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_satellite_images():
    """Create placeholder satellite images for the gallery"""
    
    static_dir = "./static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    images_to_create = [
        {
            'filename': 'placeholder_satellite_1.jpg',
            'title': 'Base Aérea Torrejón',
            'subtitle': 'Spain - Military Aircraft Detected',
            'color': (34, 102, 51)  # Military green
        },
        {
            'filename': 'placeholder_satellite_2.jpg', 
            'title': 'Kubinka Airfield',
            'subtitle': 'Russia - Military Vehicles Detected',
            'color': (51, 51, 102)  # Dark blue
        },
        {
            'filename': 'alert_1.jpg',
            'title': 'CRITICAL ALERT',
            'subtitle': 'Military Activity Detected',
            'color': (139, 0, 0)  # Dark red
        },
        {
            'filename': 'alert_2.jpg',
            'title': 'HIGH ALERT',
            'subtitle': 'Fire Detection - Industrial Area',
            'color': (255, 140, 0)  # Dark orange
        }
    ]
    
    for img_info in images_to_create:
        try:
            # Create 512x512 image
            img = Image.new('RGB', (512, 512), color=img_info['color'])
            draw = ImageDraw.Draw(img)
            
            # Add grid pattern (satellite-like)
            grid_size = 32
            for x in range(0, 512, grid_size):
                draw.line([(x, 0), (x, 512)], fill=(255, 255, 255, 50), width=1)
            for y in range(0, 512, grid_size):
                draw.line([(0, y), (512, y)], fill=(255, 255, 255, 50), width=1)
            
            # Add some "satellite objects" (rectangles)
            for i in range(5):
                x = 50 + i * 80
                y = 200 + (i % 2) * 100
                draw.rectangle([x, y, x+30, y+20], fill=(200, 200, 200))
            
            # Add title text
            try:
                font_large = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Title
            title_bbox = draw.textbbox((0, 0), img_info['title'], font=font_large)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (512 - title_width) // 2
            draw.text((title_x, 30), img_info['title'], fill='white', font=font_large)
            
            # Subtitle
            subtitle_bbox = draw.textbbox((0, 0), img_info['subtitle'], font=font_small)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (512 - subtitle_width) // 2
            draw.text((subtitle_x, 60), img_info['subtitle'], fill='yellow', font=font_small)
            
            # Add timestamp
            timestamp = "2025-10-03 14:30:00 UTC"
            draw.text((10, 480), timestamp, fill='white', font=font_small)
            
            # Add coordinates
            coords = "40.497°N, 3.435°W" if "Torrejón" in img_info['title'] else "55.566°N, 36.718°E"
            draw.text((10, 460), coords, fill='white', font=font_small)
            
            # Save image
            file_path = os.path.join(static_dir, img_info['filename'])
            img.save(file_path, 'JPEG', quality=85)
            print(f"✅ Created: {file_path}")
            
        except Exception as e:
            print(f"❌ Error creating {img_info['filename']}: {e}")

if __name__ == "__main__":
    create_placeholder_satellite_images()
    print("\n✅ Placeholder satellite images created successfully!")