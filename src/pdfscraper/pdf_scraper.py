from pdf2image import convert_from_path
from io import BytesIO
import base64
from openai import OpenAI
import dotenv
import os


dotenv.load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)
messages = list()



def get_img_uri(img):
    png_buffer = BytesIO()
    img.save(png_buffer, format="PNG")
    png_buffer.seek(0)

    base64_png = base64.b64encode(png_buffer.read()).decode('utf-8')

    data_uri = f"data:image/png;base64,{base64_png}"
    return data_uri


def generate_uris(path: str):
    images = convert_from_path(path)
    image_uris = []
    for img in images:
        image_uris.append(get_img_uri(img))
    return image_uris


def chat(messages: list = []):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        # max_tokens=5000,
        temperature=0,
        top_p=0.1
    )
    return response.choices[0].message.content


def initialize_scraper(initial_instruction: str, example_prompt: str, path: str):

    example_uris = generate_uris(path)

    global messages
    messages = [
        {"role": "system", "content": initial_instruction},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": example_prompt}
            ] + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"{data_uri}"
                    }
                } for data_uri in example_uris
            ]
        },
    ]

    ret = chat(messages)
    messages.append({"role": "assistant", "content": ret})

    return ret


def parse_file(prompt: str, path: str):

    uris = generate_uris(path)
    global messages
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": prompt}
        ] + [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"{data_uri}"
                }
            } for data_uri in uris
        ]
    })

    ret = chat(messages).strip("json").strip("`").strip("\n")
    messages.append({"role": "assistant", "content": ret})

    return ret