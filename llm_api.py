
# LOGGING
import openai
import base64
import sys
import os
from PIL import Image, ImageEnhance
import io

# Set your OpenRouter API key here
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

OPENAI_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"


def analyse_image_with_llm(image_path: str, prompt: str) -> str:
    try:
        print("[OpenRouter] Connecting to OpenRouter API...", file=sys.stderr)
        client = openai.OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )
        print(f"[OpenRouter] Model: {OPENAI_MODEL}", file=sys.stderr)
        print(f"[OpenRouter] Prompt: {prompt}", file=sys.stderr)
        
        # Preprocessing: Resize and Enhance contrast
        with Image.open(image_path) as img:
            # Resize if too large (max dimension 1024)
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                print(f"[OpenRouter] Image resized to {img.size}", file=sys.stderr)

            enhancer = ImageEnhance.Contrast(img)
            img_enhanced = enhancer.enhance(0.5)
            
            # Save processed image to disk for debugging
            try:
                base, ext = os.path.splitext(image_path)
                processed_path = f"{base}_processed{ext}"
                img_enhanced.save(processed_path)
                print(f"[OpenRouter] Processed image saved to: {processed_path}", file=sys.stderr)
            except Exception as e:
                print(f"[OpenRouter] Warning: Could not save processed image: {e}", file=sys.stderr)

            # Save to buffer
            buffered = io.BytesIO()
            # Use 'PNG' if original format is not available/compatible, but try to preserve format
            save_format = img.format if img.format else 'PNG'
            img_enhanced.save(buffered, format=save_format)
            image_bytes = buffered.getvalue()
            
        image_b64 = base64.b64encode(image_bytes).decode()
        print(f"[OpenRouter] Image loaded, resized(max 1024px), contrast enhanced (0.7x), and encoded (length: {len(image_b64)})", file=sys.stderr)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]}
            ],
            max_tokens=32000
        )
        print(f"[OpenRouter] API response: {response}", file=sys.stderr)

        print('FINISHED')
        print('This was the prompt')
        print(prompt)
        print('This was the response')
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        print(f"[OpenRouter] Error: {str(e)}", file=sys.stderr)
        return f"Error: {str(e)}"
