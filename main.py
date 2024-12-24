import io
from fastapi import FastAPI, File, UploadFile, Response
from elasticsearch import Elasticsearch
from typing import Annotated
import requests
from PIL import Image
import torch
from transformers import AutoProcessor, LlavaOnevisionForConditionalGeneration
import re
import time
import datetime
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

model_path = "models/llava-onevision-qwen2-7b-ov-hf"
model = LlavaOnevisionForConditionalGeneration.from_pretrained(
    model_path, 
    torch_dtype=torch.float16, 
    low_cpu_mem_usage=True, 
    load_in_4bit=True
).to(0)
processor = AutoProcessor.from_pretrained(model_path)

es = Elasticsearch("http://100.107.92.46:9200")

try:
    mapping = {
        "mappings": {
            "properties": {
                "image_path": {"type": "text"},
                "taken_date": {"type": "date"},
                "description": {"type": "text"}
            }
        }
    }

    es.indices.create(index="images", body=mapping)
except:
    pass


def ImageToText(image):
    """
    Receive bytes(file)
    bytes to BytesIO to PIL.Image
    """

    conversation = [
    {

      "role": "user",
      "content": [
          {"type": "text", "text": "What are these?"},
          {"type": "image"},
        ],
        },
    ]
    prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)

    raw_image = Image.open(io.BytesIO(image))
    inputs = processor(images=raw_image, text=prompt, return_tensors='pt').to(0, torch.float16)

    output = model.generate(**inputs, max_new_tokens=200, do_sample=False)
    decoded_output = processor.decode(output[0][2:], skip_special_tokens=True)

    pattern = re.compile(r"(?<=assistant).*", flags=re.M | re.S)
    answer = pattern.search(decoded_output)
    
    return answer.group()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/lifelog/save_image/")
async def read_item(file: UploadFile):
    body = await file.read()

    filename = file.filename
    nowTime = datetime.datetime.fromtimestamp(int((file.filename).split(".")[0]) / 1000)

    with open(f"./images/{filename}", "wb") as f: # 脆弱すぎる(filenameが複雑だった場合....)
        f.write(body)
        
    rt = ImageToText(body)

    doc = {
        "image_path": filename,
        "taken_date": nowTime.isoformat(),
        "description": rt
    }

    try:
        es.index(index="images", document=doc)
    except Exception as e:
        return {"error": f"Failed to save to Elasticsearch: {e}"}

    return {"filename": filename, "datetime": nowTime, "description": rt}


@app.get("/lifelog/images/",
    responses = {
        200: {
            "content": {"image/jpeg": {}}
        }
    },
    response_class=Response)
async def get_image(query: str = ""):
    with open(f"images/{query}", "rb") as f:
        img_byte = f.read()
    return Response(content=img_byte, media_type="image/jpeg")


@app.get("/lifelog/search_image")
async def search_image(query: str = ""):
    result = es.search(index="images", body={
        "query": {
            "match": {
                "description": query
            }
        }
    })

    qfound = [x["_source"] for x in result["hits"]["hits"]]
    
    return qfound


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)