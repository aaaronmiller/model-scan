# Model Scan Report

## Current Settings Overview

**Default Model (Canonical):** nvidia/nemotron-3-ultra-550b-a55b:free  
**Default Provider:** openrouter  
**Default Thinking Level:** medium  
**Transport:** auto  
**HTTP Idle Timeout:** 30000ms  

**Enabled Models:**
- openrouter/openrouter/free
- openrouter/nvidia/nemotron-3-ultra-550b-a55b:free
- opencode/nemotron-3-ultra-free

## Model Providers and Available Models

### OpenRouter Provider
- **API:** openai-completions
- **Base URL:** https://openrouter.ai/api/v1
- **Enabled Models:**
  1. openrouter/owl-alpha (context: 1M, text only)
  2. qwen/qwen3-coder:free (context: 1M, text only)
  3. nvidia/nemotron-3-ultra-550b-a55b:free (context: 1M, text+reasoning)
  4. nvidia/nemotron-3-super-120b-a12b:free (context: 1M, text+reasoning)
  5. nex-agi/nex-n2-pro:free (context: 262K, text+image)
  6. nousresearch/hermes-3-llama-3.1-405b:free (context: 131K, text only)
  7. openai/gpt-oss-120b:free (context: 131K, text+reasoning)
  8. poolside/laguna-m.1:free (context: 262K, text+reasoning)
  9. google/gemma-4-31b-it:free (context: 262K, text+image+video)
  10. meta-llama/llama-3.3-70b-instruct:free (context: 131K, text only)
  11. (13 more models, 10 disabled)

### Opencode Provider
- **API:** openai-completions
- **Base URL:** https://opencode.ai/zen/go/v1
- **Enabled Models:**
  1. deepseek-v4-flash (context: 1M, text+reasoning)
  2. qwen3.6-plus (context: 262K, text+image+video)
  3. kimi-k2.5 (context: 262K, text+reasoning)
  4. kimi-k2.6 (context: 262K, text+reasoning)
  5. minimax-m2.5 (context: 205K, text+image+video)
  6. (7 more models, 5 disabled)

### NVIDIA NIM Provider
- **API:** openai-completions
- **Base URL:** https://integrate.api.nvidia.com/v1
- **Enabled Models:**
  1. deepseek-ai/deepseek-r1 (context: 64K, text+reasoning)
  2. deepseek-ai/deepseek-v3 (context: 128K, text)
  3. qwen/qwen3-235b-a22b (context: 128K, text+reasoning)
  4. qwen/qwen3-coder-480b-a35b-instruct (context: 128K, text)
  5. qwen/qwen3.5-397b-a17b (context: 128K, text)
  6. minimaxai/minimax-m2.5 (context: 1M, text)
  7. minimaxai/minimax-m2.7 (context: 1M, text)
  8. moonshotai/kimi-k2 (context: 128K, text+reasoning)
  9. moonshotai/kimi-k2.5 (context: 128K, text+reasoning)
  10. nvidia/nemotron-3-super-120b-a12b (context: 128K, text)
  11. nvidia/llama-3.3-nemotron-super-49b-v1 (context: 128K, text)
  12. openai/gpt-oss-120b (context: 1M, text+reasoning)
  13. zhipuai/glm-5 (context: 1M, text)
  14. (8 more models, 10 disabled)

### Ollama Cloud Provider
- **API:** openai-completions
- **Base URL:** https://ollama.com/v1
- **Enabled Models:**
  1. gemma4:31b-cloud (context: 262K, text+image+audio)
  2. gpt-oss:20b-cloud (context: 131K, text+reasoning)
  3. nemotron-3-nano:30b-cloud (context: 1M, text+reasoning)
  4. minimax-m2.5:cloud (context: 205K, text+reasoning)
  5. (4 more models, 3 disabled)

## Authentication Configuration
- opencode: $OPENCODE_API_KEY
- opencode-go: $OPENCODE_GO_API_KEY

## Summary
The system supports multiple AI model providers with various models of different sizes and capabilities. The current default model is nvidia/nemotron-3-ultra-550b-a55b:free from OpenRouter, with a context window of 1M tokens and text+reasoning capability.