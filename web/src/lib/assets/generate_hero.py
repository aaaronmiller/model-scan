import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFilter as ImageFilter
import random
import math
import numpy as np

def generate_hero():
    width = 1920
    height = 1080
    
    # Background: Dark indigo navy gradient
    base_color = (10, 15, 45)  # Very dark navy
    accent_color = (20, 30, 80) # Slightly lighter indigo
    
    img = Image.new('RGB', (width, height), base_color)
    draw = ImageDraw.Draw(img)
    
    # Create a subtle radial gradient
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - width/2)**2 + (y - height/2)**2)
            ratio = min(1.0, dist / (width * 0.7))
            r = int(base_color[0] * ratio + accent_color[0] * (1 - ratio))
            g = int(base_color[1] * ratio + accent_color[1] * (1 - ratio))
            b = int(base_color[2] * ratio + accent_color[2] * (1 - ratio))
            img.putpixel((x, y), (r, g, b))

    # Re-draw object to use on the gradient image
    draw = ImageDraw.Draw(img, 'RGBA')

    # Draw Neural Network Nodes and Connections
    nodes = []
    for _ in range(40):
        nodes.append({
            'x': random.randint(0, width),
            'y': random.randint(0, height),
            'size': random.randint(2, 5),
            'color': random.choice([(0, 255, 255, 150), (100, 150, 255, 150)]) # Cyan/Electric Blue
        })

    # Draw connections (light streams)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            d = math.sqrt((nodes[i]['x'] - nodes[j]['x'])**2 + (nodes[i]['y'] - nodes[j]['y'])**2)
            if d < 300:
                opacity = int(255 * (1 - d/300) * 0.3)
                color = (0, 200, 255, opacity)
                draw.line([(nodes[i]['x'], nodes[i]['y']), (nodes[j]['x'], nodes[j]['y'])], fill=color, width=1)

    # Draw nodes
    for node in nodes:
        x, y, s = node['x'], node['y'], node['size']
        draw.ellipse([x-s, y-s, x+s, y+s], fill=node['color'])
        # Glow effect for nodes
        for r in range(1, 4):
            opacity = int(100 / (r * 2))
            draw.ellipse([x-s-r*2, y-s-r*2, x+s+r*2, y+s+r*2], outline=(node['color'][0], node['color'][1], node['color'][2], opacity))

    # Draw Radar Charts (Spider charts)
    def draw_radar(center_x, center_y, size, num_axes, color):
        points = []
        # Draw axes
        for i in range(num_axes):
            angle = i * (2 * math.pi / num_axes)
            x = center_x + size * math.cos(angle)
            y = center_y + size * math.sin(angle)
            draw.line([(center_x, center_y), (x, y)], fill=(255, 255, 255, 30), width=1)
            
            # Data point
            val = random.uniform(0.4, 0.9) * size
            points.append((center_x + val * math.cos(angle), center_y + val * math.sin(angle)))
        
        # Draw radar polygon
        draw.polygon(points, fill=(color[0], color[1], color[2], 60), outline=(color[0], color[1], color[2], 200))
        
        # Draw concentric hexagons/circles for grid
        for r in [0.25, 0.5, 0.75, 1.0]:
            grid_points = []
            for i in range(num_axes):
                angle = i * (2 * math.pi / num_axes)
                grid_points.append((center_x + size * r * math.cos(angle), center_y + size * r * math.sin(angle)))
            draw.polygon(grid_points, outline=(255, 255, 255, 20))

    # Place a few radar charts
    draw_radar(width * 0.2, height * 0.4, 150, 6, (0, 255, 255))
    draw_radar(width * 0.8, height * 0.6, 120, 5, (100, 100, 255))
    draw_radar(width * 0.5, height * 0.8, 100, 8, (0, 180, 255))

    # Apply a slight blur and then sharpen to get that "cinematic" look
    # (Optional, might slow down generation)
    # img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    output_path = '/home/cheta/code/model-scan/web/src/lib/assets/2026-05-20/001-hero-banner-wide.png'
    img.save(output_path)
    print(f"Banner saved to {output_path}")

if __name__ == "__main__":
    generate_hero()
