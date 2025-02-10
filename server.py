from fastapi import FastAPI, HTTPException
from typing import Optional, Dict, Any
import json
from datetime import datetime
import os

app = FastAPI()

# 确保数据文件目录存在
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

MESSAGE_FILE = os.path.join(DATA_DIR, "message.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
OFFICIAL_FILE = os.path.join(DATA_DIR, "official.json")

# 初始化文件结构
def init_message_file():
    if not os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, 'w', encoding='utf8') as f:
            json.dump({
                "messages": [],
                "tags": [],
                "stats": {"total": 0, "today": 0, "week": 0}
            }, f, ensure_ascii=False, indent=2)

def init_accounts_file():
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'w', encoding='utf8') as f:
            json.dump({"users": []}, f, ensure_ascii=False, indent=2)

# 初始化文件
init_message_file()
init_accounts_file()

@app.get("/token_official_message")
async def get_message_data():
    with open(MESSAGE_FILE, 'r', encoding='utf8') as f:
        return json.load(f)


@app.post("/token_get_user")
async def get_user_info(data: Dict[str, Any]):
    with open(ACCOUNTS_FILE, 'r', encoding='utf8') as f:
        accounts = json.load(f)

    user = next((u for u in accounts.get("users", [])
                 if u["platform"] == data["platform"] and u["openid"] == data["openid"]), None)

    # 如果用户不存在，则创建新用户
    if not user:
        accounts["users"].append(data)

        # 保存到文件
        with open(ACCOUNTS_FILE, 'w', encoding='utf8') as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
        return user

    return data

@app.post("/add_user")
async def add_user(user_data: Dict[str, Any]):
    with open(ACCOUNTS_FILE, 'r', encoding='utf8') as f:
        accounts = json.load(f)
    
    if "users" not in accounts:
        accounts["users"] = []
    
    new_user = {
        **user_data,
        "messageId": None,
        "lastMessageTime": None
    }
    accounts["users"].append(new_user)
    
    with open(ACCOUNTS_FILE, 'w', encoding='utf8') as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)
    return new_user

@app.put("/update_user/{platform}/{openid}")
async def update_user(platform: str, openid: str, updates: Dict[str, Any]):
    with open(ACCOUNTS_FILE, 'r', encoding='utf8') as f:
        accounts = json.load(f)
    
    user_index = next((i for i, u in enumerate(accounts.get("users", []))
                      if u["platform"] == platform and u["openid"] == openid), -1)
    
    if user_index == -1:
        raise HTTPException(status_code=404, detail="User not found")
    
    accounts["users"][user_index].update(updates)
    
    with open(ACCOUNTS_FILE, 'w', encoding='utf8') as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)
    return accounts["users"][user_index]

@app.post("/add_message")
async def add_message(message_data: Dict[str, Any], user_id: str):
    with open(MESSAGE_FILE, 'r', encoding='utf8') as f:
        data = json.load(f)
    
    print(f"Before processing - Stats: {data['stats']}")  # 添加日志
    
    # 删除已存在的留言，并更新相关统计
    old_message = next((m for m in data["messages"] if m["userId"] == user_id), None)
    if old_message:
        print(f"Found old message: {old_message}")  # 添加日志
        # 更新标签计数
        if old_message.get("tag"):
            tag_index = next((i for i, t in enumerate(data["tags"]) 
                            if t["name"] == old_message["tag"]), -1)
            if tag_index != -1 and data["tags"][tag_index]["count"] > 0:
                data["tags"][tag_index]["count"] -= 1
                print(f"Updated tag count for {old_message['tag']}")  # 添加日志
        
        # 更新统计信息
        data["stats"]["total"] -= 1
        data["stats"]["today"] -= 1
        data["stats"]["week"] -= 1
        print(f"After removing old message - Stats: {data['stats']}")  # 添加日志
        
        # 删除旧留言
        data["messages"] = [m for m in data["messages"] if m["userId"] != user_id]
    
    # 添加新留言
    new_message = {
        **message_data,
        "id": int(datetime.now().timestamp() * 1000),
        "userId": user_id
    }
    data["messages"].append(new_message)
    
    # 更新标签计数
    if message_data.get("tag"):
        tag_index = next((i for i, t in enumerate(data["tags"]) 
                         if t["name"] == message_data["tag"]), -1)
        if tag_index != -1:
            data["tags"][tag_index]["count"] += 1
    
    # 更新统计信息
    data["stats"]["total"] += 1
    data["stats"]["today"] += 1
    data["stats"]["week"] += 1
    
    print(f"Final stats: {data['stats']}")  # 添加日志
    with open(MESSAGE_FILE, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return new_message

@app.delete("/delete_message/{message_id}")
async def delete_message(message_id: int):
    with open(MESSAGE_FILE, 'r', encoding='utf8') as f:
        data = json.load(f)
    
    message_index = next((i for i, m in enumerate(data["messages"]) 
                         if m["id"] == message_id), -1)
    
    if message_index != -1:
        message = data["messages"].pop(message_index)
        
        # 更新标签计数
        if message.get("tag"):
            tag_index = next((i for i, t in enumerate(data["tags"]) 
                            if t["name"] == message["tag"]), -1)
            if tag_index != -1 and data["tags"][tag_index]["count"] > 0:
                data["tags"][tag_index]["count"] -= 1
        
        # 更新统计信息
        data["stats"]["total"] -= 1
        data["stats"]["today"] -= 1
        data["stats"]["week"] -= 1
        
        with open(MESSAGE_FILE, 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"success": True}
    return {"success": False}

@app.get("/token_get_official")
async def verify_official_account(username: str, password: str):
    with open(OFFICIAL_FILE, 'r', encoding='utf8') as f:
        official = json.load(f)
    
    if official["username"] == username and official["password"] == password:
        return {
            "name": official["name"],
            "avatar": official["avatar"],
            "id": official["id"],
            "isOfficial": True
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/user_message/{user_id}")
async def get_user_message(user_id: str):
    with open(MESSAGE_FILE, 'r', encoding='utf8') as f:
        data = json.load(f)
    message = next((m for m in data["messages"] if m["userId"] == user_id), None)
    return message

@app.put("/like_message/{message_id}")
async def like_message(message_id: int):
    with open(MESSAGE_FILE, 'r', encoding='utf8') as f:
        data = json.load(f)
    
    message = next((m for m in data["messages"] if m["id"] == message_id), None)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message["likes"] = message.get("likes", 0) + 1
    
    with open(MESSAGE_FILE, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return message

@app.get("/hot_tags")
async def get_hot_tags():
    with open(MESSAGE_FILE, 'r', encoding='utf8') as f:
        data = json.load(f)
    return data["tags"]

@app.get("/message_stats")
async def get_message_stats():
    with open(MESSAGE_FILE, 'r', encoding='utf8') as f:
        data = json.load(f)
    return data["stats"]

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8088)
