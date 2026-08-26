import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from api import PipelineAPI


@pytest.fixture
def api(tmp_path):
    return PipelineAPI(str(tmp_path / "app.db"))
