import json
import pytest
from pydantic import BaseModel
from aether.utils import add_uuid
from aether.utils import generate_task_id
from aether.utils import generate_uuid
from aether.utils import load_json
from aether.utils import save_json


class DummyModel(BaseModel):
    uuid: int = None
    name: str = "test"


class TestGenerateUuid:
    def test_returns_int(self):
        uid = generate_uuid()
        assert isinstance(uid, int)

    def test_uniqueness(self):
        uids = {generate_uuid() for _ in range(100)}
        assert len(uids) == 100


class TestGenerateTaskId:
    def test_returns_string(self):
        tid = generate_task_id()
        assert isinstance(tid, str)
        assert len(tid) == 3


class TestAddUuid:
    def test_adds_uuid_to_models(self):
        models = [DummyModel(), DummyModel()]
        result = add_uuid(models)
        assert len(result) == 2
        assert all(m.uuid is not None for m in result)

    def test_filters_none_and_exceptions(self):
        models = [DummyModel(), None, ValueError("err"), DummyModel()]
        result = add_uuid(models)
        assert len(result) == 2

    def test_empty_list(self):
        result = add_uuid([])
        assert result == []


class TestJsonIO:
    def test_save_and_load(self, tmp_path):
        data = {"key": "value", "nested": {"a": 1}}
        filepath = str(tmp_path / "test.json")

        save_json(data, filepath)
        loaded = load_json(filepath)

        assert loaded == data

    def test_unicode_support(self, tmp_path):
        data = {"korean": "한글 테스트", "emoji": "🚀"}
        filepath = str(tmp_path / "unicode.json")

        save_json(data, filepath)
        loaded = load_json(filepath)

        assert loaded["korean"] == "한글 테스트"
