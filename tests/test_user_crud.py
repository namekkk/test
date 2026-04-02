# tests/test_user_crud.py
import time
import os
import allure
import pytest
from api_client import add_user, find_user_id_by_username, user_detail, update_user, delete_user, read_users_from_csv

def load_users():
    """加载测试数据，返回用户列表"""
    csv_path = os.path.join("data", "users.csv")
    return read_users_from_csv(csv_path)

@allure.feature("用户管理")
@pytest.mark.parametrize("user", load_users())
def test_user_full_lifecycle(token, user):
    with allure.step("新增用户"):
        add_user(token, user)

    with allure.step("等待数据同步"):
        time.sleep(3)

    with allure.step("根据用户名查找用户ID"):
        user_id = find_user_id_by_username(token, user["username"], max_pages=2)
        assert user_id is not None
        allure.attach(str(user_id), name="用户ID", attachment_type=allure.attachment_type.TEXT)

    with allure.step("查询用户详情"):
        detail = user_detail(token, user_id)
        assert detail["username"] == user["username"]

    with allure.step("修改用户信息"):
        update_data = {"displayName": "修改后的名字", "email": "modified@example.com"}
        update_user(token, user_id, update_data)

    with allure.step("验证修改结果"):
        new_detail = user_detail(token, user_id)
        assert new_detail["displayName"] == "修改后的名字"

    with allure.step("删除用户"):
        delete_user(token, user_id)

    with allure.step("验证用户已被删除"):
        with pytest.raises(AssertionError):
            user_detail(token, user_id)