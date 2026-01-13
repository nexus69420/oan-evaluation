## mistralai/Mistral-Small-3.2-24B-Instruct-2506

```
CUDA_VISIBLE_DEVICES=0,1,2,3 nohup vllm serve mistralai/Mistral-Small-3.2-24B-Instruct-2506   --tokenizer-mode mistral   --config-format mistral   --load-format mistral   --tool-call-parser mistral   --enable-auto-tool-choice   --tensor-parallel-size 4   --gpu-memory-utilization 0.9   --max-model-len 128000   --port 8080   --enforce-eager   > vllm_mistral_small.out 2>&1 &
```


## openai/gpt-oss-20b

```
CUDA_VISIBLE_DEVICES=0,1,2,3 nohup vllm serve openai/gpt-oss-20b   --tool-call-parser openai   --enable-auto-tool-choice   --tensor-parallel-size 4 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager > vllm_gpt_oss_20b.out 2>&1 &
```

## openai/gpt-oss-120b

```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 nohup vllm serve openai/gpt-oss-120b   --tool-call-parser openai   --enable-auto-tool-choice   --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager > vllm_gpt_oss_120b.out 2>&1 &
```


## Qwen

Let's not use thinking for these models - so they can be compared with fine-tuned models.

To do that, we need to pass this to the model settings:
```
"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
```

## Qwen/Qwen3-14b

```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 nohup vllm serve Qwen/Qwen3-14b --enable-auto-tool-choice --reasoning-parser deepseek_r1 --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager > vllm_qwen3.out 2>&1 &
```

## Qwen/Qwen3-30B-A3B


```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 nohup vllm serve Qwen/Qwen3-30B-A3B --enable-auto-tool-choice --tool-call-parser hermes --reasoning-parser deepseek_r1 --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager > vllm_qwen3.out 2>&1 &
```

## Qwen/Qwen3-32B
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 nohup vllm serve Qwen/Qwen3-32B --enable-auto-tool-choice --tool-call-parser hermes --reasoning-parser deepseek_r1 --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager > vllm_qwen3.out 2>&1 &
```


---

### Finetuned Qwen3 14b
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 nohup vllm serve kenpath/mhv_vistaar_qwen3-14b_v0.1 --enable-auto-tool-choice --tool-call-parser hermes --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager > vllm_qwen3.out 2>&1 &
```