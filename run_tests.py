import pytest
import asyncio
from tests.test_e2e import main as run_test

def test_execution_wrapper():
    asyncio.run(run_test())

if __name__ == "__main__":
    pytest.main([__file__, "--html=outputs/report.html", "--self-contained-html"])