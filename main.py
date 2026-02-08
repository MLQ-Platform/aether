import asyncio
from aether.pipeline.runner import run_full_pipeline


if __name__ == "__main__":
    result, metrics = asyncio.run(run_full_pipeline())
    print(f"Factor code generated: {len(result.code)} chars")
