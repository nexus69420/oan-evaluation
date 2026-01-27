## mistralai/Mistral-Small-3.2-24B-Instruct-2506

```
CUDA_VISIBLE_DEVICES=0,1,2,3 nohup vllm serve mistralai/Mistral-Small-3.2-24B-Instruct-2506   --tokenizer-mode mistral   --config-format mistral   --load-format mistral   --tool-call-parser mistral   --enable-auto-tool-choice   --tensor-parallel-size 4   --gpu-memory-utilization 0.9   --max-model-len 128000   --port 8080   --enforce-eager   > vllm_mistral_small.out 2>&1 &
```


## openai/gpt-oss-20b

```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve openai/gpt-oss-20b --tool-call-parser openai --enable-auto-tool-choice  --tensor-parallel-size 4 --gpu-memory-utilization 0.8  --port 8080 --enforce-eager
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
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 nohup vllm serve Qwen/Qwen3-14b --enable-auto-tool-choice --reasoning-parser qwen3 --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager > vllm_qwen3.out 2>&1 &
```


## Qwen/Qwen3-30B-A3B


```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve Qwen/Qwen3-30B-A3B-Instruct-2507 --enable-auto-tool-choice --tool-call-parser hermes --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager --enable-expert-parallel
```

Finetuned Qwen3-30B-A3B-Instruct-2507
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve kenpath/mhv_vistaar_all_qwen3-30b-a3b-instruct-2507_v0.1 --enable-auto-tool-choice --tool-call-parser hermes --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager --enable-expert-parallel --max-model-len 128000
```

## Qwen/Qwen3-32B
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve Qwen/Qwen3-32B --enable-auto-tool-choice --tool-call-parser hermes --reasoning-parser qwen3 --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager
```

## Kenpath Qwen3-32B
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve kenpath/mhv_vistaar_all_mhv_vistaar_last_qwen3-30b-a3b-instruct-2507_v0.2_v0.2.1 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --tensor-parallel-size 8 \
  --gpu-memory-utilization 0.9 \
  --port 8080 \
  --enforce-eager \
  --max-model-len 128000
```

---

### Finetuned Qwen3 14b
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 nohup vllm serve kenpath/mhv_vistaar_qwen3-14b_v0.2 --enable-auto-tool-choice --tool-call-parser hermes --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager > vllm_qwen3.out 2>&1 &
```


### Llama 4
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve meta-llama/Llama-4-Scout-17B-16E-Instruct --enable-auto-tool-choice --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager --max-model-len 128000   --tool-call-parser llama4_json
```


### Llama 3.3 70b

```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve meta-llama/Llama-3.3-70B-Instruct --enable-auto-tool-choice --tensor-parallel-size 8 --gpu-memory-utilization 0.9  --port 8080 --enforce-eager --max-model-len 128000 --tool-call-parser llama3_json
```

### Finetuned GPT OSS 20b
```
# Force FlashInfer for the EXPERTS ONLY, while letting Attention use FlashAttention
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve kenpath/mhv_fsdp-vistaar_gpt-oss-120b_v0.5 \
    --tensor-parallel-size 8 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 128000 \
    --trust-remote-code \
    --enable-auto-tool-choice \
    --tool-call-parser openai \
    --reasoning-parser openai_gptoss \
    --port 8080 \
    --compilation-config '{"cudagraph_mode": "PIECEWISE"}' \
    --disable-custom-all-reduce \
    --chat-template /home/jovyan/chat_templates/gptoss_unsloth_chat_template.jinja

```

### Run from locally saved merged model

```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve /home/jovyan/oan-finetuning/fine-tuning/models/merged_16bit --served-model-name kenpath/mhv_vistaar_gpt-oss-20b_v0.1 --enable-auto-tool-choice --tensor-parallel-size 8 --gpu-memory-utilization 0.9 --port 8080 --enforce-eager --max-model-len 128000 --tool-call-parser openai
```


### Nemotron
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 \
  --tensor-parallel-size 8 \
  --max-model-len 128000 \
  --port 8080 \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser-plugin nano_v3_reasoning_parser.py \
  --reasoning-parser nano_v3
  --gpu-memory-utilization 0.9
```


### GPT OSS 20b without thinking

```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve openai/gpt-oss-20b --tool-call-parser openai --enable-auto-tool-choice  --tensor-parallel-size 4 --gpu-memory-utilization 0.8  --port 8080 --enforce-eager --chat-template oan-finetuning/assets/chat_templates/openai_non_thinking.jinja --served-model-name openai/gpt-oss-20b_non_thinking
```




