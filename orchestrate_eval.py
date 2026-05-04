from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from metrics.base import MetricResult


load_dotenv()


def _load_class(class_path: str):
    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _load_config(config_ref: str):
    """
    Load pipeline CONFIG from either:
    - module path: config.pipeline_config
    - file path:   D:/.../pipeline_config.py
    """
    if config_ref.endswith(".py"):
        config_path = Path(config_ref).resolve()
        spec = importlib.util.spec_from_file_location("runtime_pipeline_config", config_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Unable to load config file: {config_ref}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(config_ref)

    if not hasattr(module, "CONFIG"):
        raise ValueError(f"Config module {config_ref} must define CONFIG")
    return module.CONFIG


def _ensure_metric_result(payload: Any, metric_name: str) -> Dict[str, Any]:
    if isinstance(payload, MetricResult):
        return payload.to_dict()
    if is_dataclass(payload):
        return asdict(payload)
    if isinstance(payload, dict):
        return {
            "metric_name": payload.get("metric_name", metric_name),
            "score": payload.get("score"),
            "reason": payload.get("reason", ""),
            "metadata": payload.get("metadata", {}),
        }
    return {
        "metric_name": metric_name,
        "score": None,
        "reason": "Metric returned unsupported result type.",
        "metadata": {"raw_type": str(type(payload))},
    }


async def _run_metric_for_row(
    *,
    semaphore: asyncio.Semaphore,
    metric_obj: Any,
    metric_name: str,
    metric_config: Dict[str, Any],
    row_bundle: Dict[str, Any],
    fail_open: bool,
) -> Dict[str, Any]:
    async with semaphore:
        try:
            result = await metric_obj.evaluate(
                row_json=row_bundle["original"],
                transformed_json=row_bundle["transformed"],
                variables=row_bundle["selected_variables"],
                config=metric_config,
            )
            return _ensure_metric_result(result, metric_name)
        except Exception as exc:
            if not fail_open:
                raise
            return {
                "metric_name": metric_name,
                "score": None,
                "reason": "Metric failed; continuing due to fail_open.",
                "metadata": {"error": str(exc)},
            }


async def run_pipeline(CONFIG) -> List[Dict[str, Any]]:
    repo_root = Path(__file__).resolve().parent
    CONFIG.resolve_paths(repo_root)

    input_path = Path(CONFIG.input_path)
    output_path = Path(CONFIG.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f:
        input_rows: List[Dict[str, Any]] = json.load(f)

    if CONFIG.num_samples is not None:
        input_rows = input_rows[: CONFIG.num_samples]

    transform_cls = _load_class(CONFIG.data_transform.transformer_class)
    transformer = transform_cls(**CONFIG.data_transform.transformer_kwargs)

    row_bundles: List[Dict[str, Any]] = []
    for row in input_rows:
        transformed = transformer.transform(row)
        selected_variables = {
            key: transformed.get(key) for key in CONFIG.data_transform.selected_output_keys
        }
        row_bundles.append(
            {
                "original": row,
                "transformed": transformed,
                "selected_variables": selected_variables,
                "metrics": [],
            }
        )

    metric_instances: List[Tuple[str, Any, Dict[str, Any]]] = []
    for metric_class_path in CONFIG.model_evaluation.metric_classes:
        metric_cls = _load_class(metric_class_path)
        metric_obj = metric_cls()
        metric_name = getattr(metric_obj, "metric_name", metric_class_path)
        metric_config = dict(
            CONFIG.model_evaluation.metric_configs.get(metric_class_path)
            or CONFIG.model_evaluation.metric_configs.get(metric_name)
            or {}
        )
        if "llm" not in metric_config:
            metric_config["llm"] = CONFIG.model_evaluation.llm
        metric_instances.append((metric_name, metric_obj, metric_config))

    semaphore = asyncio.Semaphore(CONFIG.max_concurrent)
    batch_size = max(1, int(getattr(CONFIG, "batch_size", len(row_bundles) or 1)))

    for batch_start in range(0, len(row_bundles), batch_size):
        batch_rows = row_bundles[batch_start : batch_start + batch_size]
        batch_num = (batch_start // batch_size) + 1

        for metric_name, metric_obj, metric_config in metric_instances:
            tasks = [
                _run_metric_for_row(
                    semaphore=semaphore,
                    metric_obj=metric_obj,
                    metric_name=metric_name,
                    metric_config=metric_config,
                    row_bundle=row_bundle,
                    fail_open=CONFIG.fail_open,
                )
                for row_bundle in batch_rows
            ]
            results = await tqdm.gather(
                *tasks,
                desc=f"Batch {batch_num} metric: {metric_name}",
            )

            for row_bundle, metric_result in zip(batch_rows, results):
                row_bundle["metrics"].append(metric_result)
                eval_payload = metric_result.get("metadata", {}).get("evaluation")
                if eval_payload:
                    row_bundle["evaluation"] = eval_payload

    with output_path.open("w", encoding="utf-8") as f:
        final_rows: List[Dict[str, Any]] = []
        for row_bundle in row_bundles:
            out_row = {
                "original": row_bundle["original"],
                "metrics": row_bundle["metrics"],
            }
            if "evaluation" in row_bundle:
                out_row["evaluation"] = row_bundle["evaluation"]
            final_rows.append(out_row)

        json.dump(final_rows, f, ensure_ascii=False, indent=2)

    return final_rows


async def main(config_ref: str) -> List[Dict[str, Any]]:
    CONFIG = _load_config(config_ref)
    return await run_pipeline(CONFIG)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Config-driven evaluation orchestrator")
    parser.add_argument(
        "--config",
        type=str,
        default="config.pipeline_config",
        help="Config module path or python file path that exposes CONFIG",
    )
    args = parser.parse_args()

    asyncio.run(main(args.config))

