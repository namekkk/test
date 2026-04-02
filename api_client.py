# api_client.py
import requests
import csv
import json
import logging
import time
from requests.exceptions import RequestException

# 从配置文件导入接口地址
from config import (
    LOGIN_URL, ADD_USER_URL, DETAIL_URL, PAGE_URL, UPDATE_URL, DELETE_URL
)
# 日志配置由调用方（如 conftest.py）调用 logging_config.setup_logging() 完成

# ==================== 登录 ====================
def login(username, password):
    """登录获取 token（假设返回格式为 {"data": {"token": "xxx"}}）"""
    print("执行到登陆函数了")
    try:
        resp = requests.post(LOGIN_URL, json={"username": username, "password": password}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        token = data.get("data", {}).get("token")
        if not token:
            raise ValueError("登录响应中未找到 token")
        logging.info("登录成功")
        return token
    except Exception as e:
        logging.error(f"登录失败: {e}")
        raise

# ==================== 新增用户 ====================
def add_user(token, user_info):
    """新增用户，使用自定义 Token 头"""
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(ADD_USER_URL, json=user_info, headers=headers, timeout=5)
        assert resp.status_code in [200, 201], f"状态码异常: {resp.status_code}"
        logging.info(f"新增用户成功: {user_info.get('username')}")
        return resp
    except AssertionError as e:
        logging.error(f"断言失败: {e}, 响应: {resp.text}")
        raise
    except RequestException as e:
        logging.error(f"请求异常: {e}")
        raise

# ==================== 从 CSV 读取用户 ====================
def read_users_from_csv(file_path):
    """读取 CSV 并转换为接口需要的 JSON 格式"""
    users = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user = {
                    "username": row["username"],
                    "displayName": row["displayName"],
                    "email": row["email"],
                    "mobile": row["mobile"],
                    "orgId": int(row["orgId"]),
                    "roleIds": json.loads(row["roleIds"]),
                    "status": int(row["status"])
                }
                users.append(user)
        logging.info(f"从 {file_path} 读取到 {len(users)} 个用户")
    except Exception as e:
        logging.error(f"读取 CSV 失败: {e}")
        raise
    return users

# ==================== 用户详情 ====================
def user_detail(token, user_id):
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(DETAIL_URL, json={"id": user_id}, headers=headers, timeout=5)
        assert resp.status_code in [200, 201], f'获取用户信息失败，状态码为{resp.status_code}'
        data = resp.json()
        assert data.get("success") is True, f"业务失败：{data.get('errorMessage')}"
        user_info = data.get("data", {})
        logging.info(f"获取{user_id}用户成功")
        return user_info
    except AssertionError as e:
        logging.error(f"断言失败：{e}，参数为：{resp.text}")
        raise
    except RequestException as e:
        logging.error(f"请求异常：{e}")
        raise

# ==================== 分页查询用户列表 ====================
def get_user_page(token, page_number=1):
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    payload = {
        "displayName": "",
        "email": "",
        "mobile": "",
        "orgId": "",
        "pageNum": page_number,
        "pageSize": 10,
        "status": "",
        "username": ""
    }
    try:
        resp = requests.post(PAGE_URL, json=payload, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        users = data.get("data", {}).get("records", [])
        logging.info(f"成功获取到第{page_number}页的数据,共{len(users)}条")
        return users
    except Exception as e:
        logging.error(f"获取第{page_number}页数据失败：{e}")
        raise

# ==================== 根据用户名查找用户ID ====================
def find_user_id_by_username(token, username, max_pages=5):
    page = 1
    while page <= max_pages:
        users = get_user_page(token, page)
        if users is None:
            users = []
        # 打印本页所有用户名
        names = [u.get("username") for u in users]
        logging.info(f"第{page}页用户名: {names}")
        for u in users:
            if u.get("username") == username:
                return u.get("id")
        page += 1
    return None

# ==================== 修改用户 ====================
def update_user(token, user_id, update_data):
    # 1. 获取当前用户完整信息
    current = user_detail(token, user_id)
    # 2. 用 update_data 覆盖需要修改的字段
    current.update(update_data)
    # 3. 确保 id 正确
    current["id"] = user_id
    # 4. 移除只读字段（根据实际返回调整）
    current.pop("createTime", None)
    current.pop("createUser", None)
    current.pop("createUserName", None)
    # 5. 发送全量更新请求
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    resp = requests.post(UPDATE_URL, json=current, headers=headers, timeout=5)
    assert resp.status_code in [200, 201], f"修改失败，HTTP状态码{resp.status_code}"
    resp_data = resp.json()
    assert resp_data.get("success") is True, f"修改失败，业务错误：{resp_data.get('errorMessage')}"
    logging.info(f"用户 {user_id} 修改成功，修改内容：{update_data}")
    return resp

# ==================== 删除用户 ====================
def delete_user(token, user_id):
    """使用 POST 方法删除用户，参数 id 放在 JSON body 中"""
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    payload = {"id": user_id}
    try:
        resp = requests.post(DELETE_URL, json=payload, headers=headers, timeout=5)
        assert resp.status_code in [200, 204], f"删除失败，状态码{resp.status_code}"
        logging.info(f"用户 {user_id} 删除成功")
        return resp
    except AssertionError as e:
        logging.error(f"删除断言失败：{e}，响应：{resp.text}")
        raise
    except RequestException as e:
        logging.error(f"删除请求异常：{e}")
        raise