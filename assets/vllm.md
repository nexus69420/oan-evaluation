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