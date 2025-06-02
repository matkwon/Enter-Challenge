from fastapi import FastAPI
from pydantic import BaseModel
import datetime

from PIL import Image, ImageDraw, ImageFont


app = FastAPI()

class Report(BaseModel):
    message: str


@app.post("/report/")
async def report(rep: Report):
    create_png_report(rep.message, "../img/portfolio_graph.png")
    return {"message": datetime.datetime.now()}


import textwrap 


def create_png_report(text_content, original_chart_path, output_filename="../img/report.png"):
    try:
        # --- Configuration ---
        report_canvas_width = 800
        horizontal_padding = 40
        vertical_padding = 30
        spacing_between_elements = 25
        inter_line_spacing_factor = 0.3 # Multiplier for spacing_between_elements for inter-text-line space

        title_font_size = 40 # Keep this as it was, or adjust if needed
        body_font_size = 22  # Keep this as it was, or adjust if needed
        
        max_chart_width_in_report = report_canvas_width - (2 * horizontal_padding)

        # --- Font Setup ---
        try:
            font_path = "arial.ttf"
            title_font = ImageFont.truetype(font_path, title_font_size)
            body_font = ImageFont.truetype(font_path, body_font_size)
        except IOError:
            print("Arial font not found. Using default font. Text might not look as good.")
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            # Note: Default font sizing is tricky. These are placeholders.
            if hasattr(title_font, 'path') and title_font.path == '': # Pillow 10 check for default
                 title_font_size = int(title_font_size / 5) # Drastic reduction for typical default font appearance
                 body_font_size = int(body_font_size / 5)


        # --- Text Processing & Height Calculation ---
        temp_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        
        title_actual_line_height = temp_draw.textbbox((0,0), "Tg", font=title_font)[3] - temp_draw.textbbox((0,0), "Tg", font=title_font)[1]
        body_actual_line_height = temp_draw.textbbox((0,0), "Tg", font=body_font)[3] - temp_draw.textbbox((0,0), "Tg", font=body_font)[1]

        text_block_width = report_canvas_width - (2 * horizontal_padding)
        
        # *** THIS IS THE KEY CHANGE FOR WIDER TEXT ***
        # We reduce the multiplier (e.g., from 0.55 to 0.45 or 0.42).
        # A smaller multiplier means we estimate each character is narrower,
        # so more characters fit per line for textwrap.
        char_width_heuristic_factor_title = 0.45  # TRY ADJUSTING THIS (e.g., 0.40 to 0.50)
        char_width_heuristic_factor_body = 0.42   # TRY ADJUSTING THIS (e.g., 0.40 to 0.50)

        # If font size is very small (e.g. after default font adjustment), heuristic might need to be larger
        if title_font_size < 10: char_width_heuristic_factor_title = 0.6
        if body_font_size < 10: char_width_heuristic_factor_body = 0.6

        chars_per_line_title = int(text_block_width / (title_font_size * char_width_heuristic_factor_title)) if title_font_size > 0 else 50
        chars_per_line_body = int(text_block_width / (body_font_size * char_width_heuristic_factor_body)) if body_font_size > 0 else 80


        all_display_lines = []
        original_text_lines = text_content.strip().split('\n')

        for i, original_line in enumerate(original_text_lines):
            is_current_line_title = (i == 0 and original_line.strip() != "")

            if not original_line.strip():
                all_display_lines.append(("", body_font, body_actual_line_height // 2)) # Reduced space for empty lines
                continue

            font_to_use = title_font if is_current_line_title else body_font
            wrap_char_count = chars_per_line_title if is_current_line_title else chars_per_line_body
            line_height = title_actual_line_height if is_current_line_title else body_actual_line_height
            
            # Ensure wrap_char_count is at least 1
            wrap_char_count = max(1, wrap_char_count)

            wrapped_lines = textwrap.wrap(original_line, width=wrap_char_count, break_long_words=True, replace_whitespace=False, drop_whitespace=False)
            if not wrapped_lines and original_line: # If textwrap returns empty but original had content
                wrapped_lines = [original_line]
            
            for line_idx, line_segment in enumerate(wrapped_lines):
                all_display_lines.append((line_segment, font_to_use, line_height))
            
            if is_current_line_title and len(wrapped_lines) > 0 and i < len(original_text_lines) - 1:
                 all_display_lines.append(("", body_font, body_actual_line_height // 3)) # Space after title block

        total_text_height = 0
        small_line_spacing = int(spacing_between_elements * inter_line_spacing_factor)
        for idx, (_, _, line_h) in enumerate(all_display_lines):
            total_text_height += line_h
            if idx < len(all_display_lines) - 1: # Add spacing for all but the last line
                 # Add less space if current or next line is effectively an empty spacing line
                if all_display_lines[idx][0].strip() == "" or (idx + 1 < len(all_display_lines) and all_display_lines[idx+1][0].strip() == ""):
                    total_text_height += small_line_spacing // 2
                else:
                    total_text_height += small_line_spacing
        

        # --- Image Processing ---
        try:
            original_chart_image = Image.open(original_chart_path)
        except FileNotFoundError:
            print(f"Error: The original chart image '{original_chart_path}' was not found.")
            return
        
        img_orig_w, img_orig_h = original_chart_image.size
        if img_orig_w == 0 or img_orig_h == 0: # prevent division by zero
            print(f"Error: Original chart image '{original_chart_path}' has zero dimension.")
            return
        aspect_ratio = img_orig_h / img_orig_w
        
        new_chart_width = min(img_orig_w, max_chart_width_in_report)
        new_chart_height = int(new_chart_width * aspect_ratio)
        if new_chart_height == 0 and img_orig_h > 0: # Ensure min height if aspect ratio calculation leads to 0
            new_chart_height = 1

        resized_chart_image = original_chart_image.resize((new_chart_width, new_chart_height), Image.Resampling.LANCZOS)

        # --- Canvas Creation ---
        final_canvas_height = (vertical_padding + 
                               total_text_height + 
                               (spacing_between_elements if total_text_height > 0 else 0) + # only add if there's text
                               new_chart_height + 
                               vertical_padding)
        
        report_final_image = Image.new('RGB', (report_canvas_width, int(final_canvas_height)), color='white')
        draw = ImageDraw.Draw(report_final_image)

        # --- Drawing Text ---
        current_y = vertical_padding
        for idx, (text_segment, font_obj, line_h) in enumerate(all_display_lines):
            is_empty_spacer_line = (text_segment.strip() == "")

            if is_empty_spacer_line:
                current_y += line_h # Add pre-calculated spacing effect
            else:
                segment_bbox = draw.textbbox((0,0), text_segment, font=font_obj)
                segment_width = segment_bbox[2] - segment_bbox[0]
                
                current_x = (report_canvas_width - segment_width) / 2
                if current_x < horizontal_padding:
                    current_x = horizontal_padding
                
                draw.text((current_x, current_y), text_segment, font=font_obj, fill='black')
                current_y += line_h

            if idx < len(all_display_lines) - 1:
                if is_empty_spacer_line or (idx + 1 < len(all_display_lines) and all_display_lines[idx+1][0].strip() == ""):
                    current_y += small_line_spacing // 2
                else:
                    current_y += small_line_spacing
        
        # Adjust Y before placing image (current_y is now at the baseline of the last text line + its trailing space)
        current_y += (spacing_between_elements - small_line_spacing if all_display_lines else spacing_between_elements)


        # --- Drawing Image ---
        image_pos_x = (report_canvas_width - new_chart_width) // 2
        report_final_image.paste(resized_chart_image, (image_pos_x, int(current_y)))

        # --- Save Final Report ---
        report_final_image.save(output_filename)
        print(f"Updated PNG report with wider text saved as '{output_filename}'")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
